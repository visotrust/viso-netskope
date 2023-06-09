import enum
import os
import sys

if sys.modules.get('netskope'):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib'))

from concurrent.futures import Future, as_completed
from itertools import chain, groupby
from operator import attrgetter
from typing import Any, Iterable, Mapping, Optional

import requests
from requests_futures.sessions import FuturesSession  # type: ignore

from .are import (
    MappingType,
    PluginBase,
    PushResult,
    TargetMappingFields,
    ValidationResult,
)
from .client import util
from .client.model import RelationshipCreateUpdateInput, TagsCreateInput
from .proto import Application
from .url import BASE_URL

VISOTRUST_CONCURRENT = 1


class CCLTag(str, enum.Enum):
    UNKNOWN = 'CCI Unknown'
    POOR = 'CCI Poor'
    LOW = 'CCI Low'
    MEDIUM = 'CCI Medium'
    HIGH = 'CCI High'
    EXCELLENT = 'CCI Excellent'


def app_domain(app: Application) -> str:
    try:
        return app.steeringDomains[0]
    except IndexError:
        try:
            return app.discoveryDomains[0]
        except IndexError:
            return 'unknown.tld'


def vendor_cci(apps: Iterable[Application]) -> tuple[int, Optional[float]]:
    has_one = False
    count = 0.0
    total = 0
    for app in apps:
        count += 1
        total += app.cci or 0
        has_one = has_one or app.cci is not None
    return (int(count), total / count if has_one else None)


CCL_THRESHOLDS = (
    (49, CCLTag.POOR),
    (59, CCLTag.LOW),
    (74, CCLTag.MEDIUM),
    (89, CCLTag.HIGH),
)


def cci_to_ccl(cci: Optional[float]) -> CCLTag:
    if cci is None:
        return CCLTag.UNKNOWN
    for (n, tag) in CCL_THRESHOLDS:
        if cci <= n:
            return tag
    return CCLTag.EXCELLENT


class VTPluginARE(PluginBase):
    def request_args(self, config):
        args = {}
        if sys.modules.get('netskope'):
            args.update(
                proxies=self.proxy,
                verify=self.ssl_validation and BASE_URL.startswith('https'),
            )
        return args

    def post(
        self, session: FuturesSession, token: str, create: RelationshipCreateUpdateInput
    ) -> Future:
        return session.post(
            f"{BASE_URL}/api/v1/relationships",
            headers={
                'Authorization': f"Bearer {token}",
                'Content-Type': 'application/json',
            },
            data=create.json(),
            **self.request_args(self.configuration),
        )

    def push(self, apps: Iterable[Application], _) -> PushResult:
        apps = sorted((x for x in apps if x.vendor), key=attrgetter('vendor'))
        vendors = count = pushes = 0

        with util.new_futures_session(VISOTRUST_CONCURRENT) as session:
            futures = {}
            for (vendor, apps) in groupby(apps, attrgetter('vendor')):
                app = next(apps)
                (count, cci) = vendor_cci(chain([app], apps))

                if count == 0 or self.configuration.get('max_cci', 100) < (cci or 0):
                    continue

                vendors += 1
                ccl = cci_to_ccl(cci)
                domain = app_domain(app)

                create = RelationshipCreateUpdateInput(
                    name=vendor,
                    homepage=f'https://{domain}',
                    tags=[ccl],
                    businessOwnerEmail=self.configuration["email"],
                )

                self.logger.info(f'Request JSON: {create.json()}')
                future = self.post(session, self.configuration['token'], create)
                futures[future] = vendor

            for f in as_completed(futures):
                resp = f.result()
                if 200 <= resp.status_code <= 299:
                    pushes += 1
                else:
                    self.logger.info(
                        f'Response code {resp.status_code} for vendor "{futures[f]}".'
                    )
                    self.logger.info(f'Response: {resp.json()}.')

        return PushResult(
            success=vendors == pushes, message=f'Completed {pushes}/{vendors} pushes.'
        )

    def get_target_fields(self, _, __) -> Iterable[TargetMappingFields]:
        return [
            TargetMappingFields(
                label="Company Name",
                type=MappingType.STRING,
                value="name",
            )
        ]

    def validate(self, config: Mapping[str, Any]) -> ValidationResult:
        try:
            token = config.get('token', '')
            email = config.get('email', '')
            if not (token and email):
                raise ValueError('Missing keys.')

            url = f'{BASE_URL}/api/v1/tags'
            self.logger.info(f'Validating against url {BASE_URL}.')
            resp = requests.post(
                url,
                data=TagsCreateInput(
                    tags=[
                        CCLTag.UNKNOWN,
                        CCLTag.POOR,
                        CCLTag.LOW,
                        CCLTag.MEDIUM,
                        CCLTag.HIGH,
                        CCLTag.EXCELLENT,
                    ]
                ).json(),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                **self.request_args(config),
            )
            self.logger.info(f'{url} = {resp.status_code}.')
            if 200 <= resp.status_code <= 299:
                return ValidationResult(success=True, message='Validation complete.')
            self.logger.info(f'Response code {resp.status_code}')
            return ValidationResult(
                success=False, message=f'Response code {resp.status_code}.'
            )
        except Exception as e:
            self.logger.info(f"Validation error: {e}.")
            return ValidationResult(success=False, message=str(e))


__all__ = ('VTPluginARE',)
