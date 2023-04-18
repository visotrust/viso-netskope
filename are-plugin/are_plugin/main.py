import sys, os

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'lib'))

from typing import Iterable, Optional, Mapping, Any
from itertools import groupby, tee
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


    @staticmethod
    def filter_app(config, app):
        return (app.cci or 0) <= config['max_cci']


    def push(self, apps: Iterable[Application], _) -> PushResult:
        apps = sorted(apps, key=attrgetter('vendor'))
        vendors = 0
        pushes = 0
        with util.new_futures_session(VISOTRUST_CONCURRENT) as session:
            futures = {}
            for (vendor, vapps) in groupby(apps, attrgetter('vendor')):
                (vapps, fapps) = tee(vapps)
                if not any(self.filter_app(self.configuration, app) for app in fapps):
                    continue
                vendors += 1
                app = next(vapps)
                domain = app_domain(app)

                create = RelationshipCreateUpdateInput(
                    name=vendor,
                    homepage=f'https://{domain}',
                    dataTypes=[],
                    contextTypes=[],
                    businessOwnerEmail=self.configuration["email"])

                self.logger.info(f'Request JSON: {create.json()}')
                future = self.post(session, self.configuration['token'], create)
                futures[future] = vendor

            for f in as_completed(futures):
                resp = f.result()
                if 200 <= resp.status_code <= 299:
                    pushes += 1
                else:
                    self.logger.info(f'Response code {resp.status_code} for vendor "{futures[f]}"')
                    self.logger.info(f'Response: {resp.json()}')
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
            token = config.get('token', '')
            email = config.get('email', '')
            url   = config.get('url',   '')
            if not (token and email and url):
                raise ValueError('Missing keys')
            url = f'{url}/api/v1/relationships'
            self.logger.info(f'Validating against url {url}')
            resp = requests.get(
                url,
                headers={'Authorization': f"Bearer {token}"},
                **self.request_args(config))
            self.logger.info(f'{url} = {resp.status_code}')
            if 200 <= resp.status_code <= 299:
                return ValidationResult(success=True, message='Validation complete')
            return ValidationResult(success=False, message=f'Response code {resp.status_code}')
        except Exception as e:
            self.logger.info(f"Validation error: {e}")
            return ValidationResult(success=False, message=str(e))


__all__ = ('VTPluginARE',)
