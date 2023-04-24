import sys, os, enum

if sys.modules.get('netskope'):
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'lib'))

from typing import Iterable, Optional, Mapping, Callable, Any
from itertools import groupby, chain
from operator import attrgetter
from concurrent.futures import Future, as_completed
from requests_futures.sessions import FuturesSession # type: ignore
import requests

from .are import (
    PluginBase,
    ValidationResult,
    PushResult,
    TargetMappingFields,
    MappingType)

from .client import util
from .client.model import RelationshipCreateUpdateInput
from .proto import Application

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
    (89, CCLTag.HIGH))


def cci_to_ccl(cci: Optional[float]) -> CCLTag:
    if cci is None:
        return CCLTag.UNKNOWN
    for (n, tag) in CCL_THRESHOLDS:
        if cci <= n:
            return tag
    return CCLTag.EXCELLENT


def cats_to_set(s: Optional[str]) -> Optional[set[str]]:
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    return {c.strip() for c in s.split(',')}


def build_keepfn(config: Mapping[str, Any]) -> Callable[[Application], bool]:
    incl = cats_to_set(config.get('include_cats'))
    excl = cats_to_set(config.get('exclude_cats'))
    if incl:
        def _(app):
            return app.categoryName in incl
    elif excl:
        def _(app):
            return app.categoryName not in excl
    else:
        def _(_):
            return True
    return _


class VTPluginARE(PluginBase):
    def request_args(self, config):
        args = {}
        if sys.modules.get('netskope'):
            args.update(
                proxies=self.proxy,
                verify=self.ssl_validation and config['url'].startswith('https'))
        return args


    def post(self, session: FuturesSession, token: str, create: RelationshipCreateUpdateInput) -> Future:
        return session.post(
            f"{self.configuration['url']}/api/v1/relationships",
            headers={'Authorization': f"Bearer {token}",
                     'Content-Type': 'application/json'},
            data=create.json(),
            **self.request_args(self.configuration))


    def push(self, apps: Iterable[Application], _) -> PushResult:
        apps = sorted((x for x in apps if x.vendor), key=attrgetter('vendor'))
        keepfn = build_keepfn(self.configuration)
        vendors = count = pushes = 0

        with util.new_futures_session(VISOTRUST_CONCURRENT) as session:
            futures = {}
            for (vendor, apps) in groupby(apps, attrgetter('vendor')):
                app = next(apps)
                (count, cci) = vendor_cci(a for a in chain([app], apps) if keepfn(a))

                if count == 0 or self.configuration['max_cci'] < (cci or 0):
                    continue

                vendors += 1
                ccl = cci_to_ccl(cci)
                domain = app_domain(app)

                create = RelationshipCreateUpdateInput(
                    name=vendor,
                    homepage=f'https://{domain}',
                    tags=[ccl],
                    businessOwnerEmail=self.configuration["email"])

                self.logger.info(f'Request JSON: {create.json()}')
                future = self.post(session, self.configuration['token'], create)
                futures[future] = vendor

            for f in as_completed(futures):
                resp = f.result()
                if 200 <= resp.status_code <= 299:
                    pushes += 1
                else:
                    self.logger.info(f'Response code {resp.status_code} for vendor "{futures[f]}".')
                    self.logger.info(f'Response: {resp.json()}.')

        return PushResult(success=vendors == pushes, message=f'Completed {pushes}/{vendors} pushes.')


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
            incl = config.get('include_cats')
            excl = config.get('exclude_cats')
            if incl and excl:
                return ValidationResult(
                    success=False,
                    message="Can't specify categories to include AND exclude.")
            token = config.get('token', '')
            email = config.get('email', '')
            url   = config.get('url',   '')
            if not (token and email and url):
                raise ValueError('Missing keys.')

            url = f'{url}/api/v1/relationships'
            self.logger.info(f'Validating against url {url}.')
            resp = requests.options(
                url,
                headers={'Authorization': f"Bearer {token}"},
                **self.request_args(config))
            self.logger.info(f'{url} = {resp.status_code}.')
            if 200 <= resp.status_code <= 299:
                return ValidationResult(success=True, message='Validation complete.')
            return ValidationResult(success=False, message=f'Response code {resp.status_code}.')
        except Exception as e:
            self.logger.info(f"Validation error: {e}.")
            return ValidationResult(success=False, message=str(e))


__all__ = ('VTPluginARE',)
