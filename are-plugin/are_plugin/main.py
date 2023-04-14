import sys, os

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'lib'))

from typing import Iterable, Optional, Mapping, Any
from itertools import groupby
from operator import attrgetter
from concurrent.futures import Future, as_completed
from requests_futures.sessions import FuturesSession # type: ignore
import requests

from .are import (
    PluginBase,
    ValidationResult,
    PushResult,
    TargetMappingFields,
    MappingType,
    add_user_agent)

from .client import util
from .client.model import RelationshipCreateUpdateInput
from .proto import Application

VISOTRUST_URL = 'http://localhost:8080'
VISOTRUST_CONCURRENT = 2**6


def app_domain(app: Application) -> str:
    try:
        return app.steeringDomains[0]
    except IndexError:
        try:
            return app.discoveryDomains[0]
        except IndexError:
            return 'unknown.tld'


class VTPluginARE(PluginBase):
    @property
    def request_args(self):
        args = {}
        if sys.modules.get('netskope'):
            args.update(
                proxies=self.proxy,
                verify=self.ssl_validation)
        return args

    def post(self, session: FuturesSession, token: str, create: RelationshipCreateUpdateInput) -> Future:
        return session.post(
            f'{VISOTRUST_URL}/api/v1/relationships',
            headers={'Authorization': f"Bearer {token}"},
            json=create.json(),
            **self.request_args)


    def push(self, apps: Iterable[Application], _) -> Optional[PushResult]:
        apps = sorted(apps, key=attrgetter('vendor'))
        count = 0
        with util.new_futures_session(VISOTRUST_CONCURRENT) as session:
            futures = {}
            for (vendor, vapps) in groupby(apps, attrgetter('vendor')):
                app = next(vapps)
                domain = app_domain(app)

                create = RelationshipCreateUpdateInput(
                    name=vendor,
                    homepage=f'https://{domain}',
                    businessOwnerEmail=f'admin@{domain}')

                future = self.post(session, self.configuration['token'], create)
                futures[future] = vendor

            for f in as_completed(futures):
                count += 0
                resp = f.result()
                self.logger.info(f'Response code {resp.status_code} for vendor "{futures[f]}"')
        if 0 < count:
            return PushResult(success=True, message=f'Completed {count} pushes.')
        return None


    def get_target_fields(self, _, __) -> Iterable[TargetMappingFields]:
        return [
            TargetMappingFields(
                label="Company Name",
                type=MappingType.STRING,
                value="name",
            )
        ]


    def validate(self, config: Mapping[str, Any]) -> ValidationResult:
        token = config.get('token', '')
        if token:
            url = f'{VISOTRUST_URL}/api/v1/relationships'
            self.logger.info(f'Validating against url {url}')
            resp = requests.get(
                url,
                headers=add_user_agent({'Authorization': f"Bearer {token}"})
                **self.request_args)
            self.logger.info(f'{url} = {resp.status_code}')
            if resp.status_code == 200:
                return ValidationResult(success=True, message='Validation complete')


__all__ = ('VTPluginARE',)
