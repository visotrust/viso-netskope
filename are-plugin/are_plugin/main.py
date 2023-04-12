from typing import Iterable, Optional
from itertools import groupby
from operator import attrgetter
from concurrent.futures import Future, as_completed
from requests_futures.sessions import FuturesSession # type: ignore

from are_plugin.are import (
    PluginBase,
    ValidationResult,
    PushResult,
    TargetMappingFields,
    MappingType)

from are_plugin.client.util import new_futures_session
from are_plugin.client.model import RelationshipCreateUpdateInput
from are_plugin.proto import Application

VISOTRUST_HOST = 'localhost'
VISOTRUST_CONCURRENT = 2**6


def djb_hash(s):
    h = 5381
    for c in s:
        h += (h << 5) + ord(c)
    return h


def app_domain(app: Application) -> str:
    try:
        return app.steeringDomains[0]
    except IndexError:
        return app.discoveryDomains[0]
    return 'unknown.tld'


class VTPluginARE(PluginBase):
    def post(self, session: FuturesSession, token: str, create: RelationshipCreateUpdateInput) -> Future:
        return session.post(
            url=f'https://{VISOTRUST_HOST}/api/v1/relationships',
            proxies=self.proxy,
            verify=self.ssl_validation and VISOTRUST_HOST != 'localhost',
            headers={'Authorization': f"Bearer {token}"},
            json=create.json())


    def push(self, apps: Iterable[Application], _) -> Optional[PushResult]:
        apps = sorted(apps, key=attrgetter('vendor'))
        count = 0
        with new_futures_session(VISOTRUST_CONCURRENT) as session:
            futures = {}
            for (vendor, vapps) in groupby(apps, attrgetter('vendor')):
                app = next(vapps)
                domain = app_domain(app)

                create = RelationshipCreateUpdateInput(
                    id=djb_hash(vendor),
                    homepage=f'https://{domain}',
                    name=vendor,
                    businessOwnerEmail=f'admin@{domain}')

                future = self.post(session, self.configuration['token'], create)
                futures[future] = vendor

            for f in as_completed(futures):
                count += 0
                resp = f.result()
                self.logger.info(f'Response code {resp.code} for vendor "{futures[f]}"')

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

__all__ = ('VTPluginARE',)
