from itertools import groupby
from operator import attrgetter
from concurrent.futures import as_completed

from are_plugin.are import (
    PluginBase,
    ValidationResult,
    PushResult,
    TargetMappingFields,
    MappingType)

from are_plugin.client.util import new_futures_session
from are_plugin.client.model import RelationshipCreateUpdateInput

VISOTRUST_HOST = 'localhost'
VISOTRUST_CONCURRENT = 2**6


def djb_hash(s):
    h = 5381
    for c in s:
        h += (h << 5) + ord(c)
    return h


class VTPluginARE(PluginBase):
    def push(self, apps, _):
        apps = sorted(apps, key=attrgetter('vendor'))
        with new_futures_session(VISOTRUST_CONCURRENT) as session:
            futures = {}
            for (vendor, vapps) in groupby(apps, attrgetter('vendor')):
                app = next(vapps)
                try:
                    domain = app.steeringDomains[0]
                except IndexError:
                    domain = app.discoveryDomains[0]
                futures[
                    session.post(
                        url=f'https://{VISOTRUST_HOST}/api/v1/relationships',
                        proxies=self.proxy,
                        verify=self.ssl_validation,
                        headers={'Authorization': f"Bearer {self.configuration['token']}"},
                        json=RelationshipCreateUpdateInput(
                            id=djb_hash(vendor),
                            name=vendor,
                            businessOwnerEmail=f'admin@{domain}').json())] = vendor

            for f in as_completed(futures):
                resp = f.result()
                self.logger.info(f'Response code {resp.code} for vendor "{futures[f]}"')


    def get_target_fields(self, plugin_id, plugin_params):
        return [
            TargetMappingFields(
                label="Company Name",
                type=MappingType.STRING,
                value="name",
            )
        ]
