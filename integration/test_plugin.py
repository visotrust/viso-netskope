import hashlib
import os
from datetime import datetime

import requests

from are_plugin.main import CCLTag, VTPluginARE
from are_plugin.netskope_model import Application
from are_plugin.url import BASE_URL

EMAIL = os.environ.get('VISOTRUST_EMAIL', 'orgadmin@visotrust.com')

NAME = hashlib.new('sha1', datetime.now().isoformat().encode('utf-8')).hexdigest()
DISC_DOMAINS = [f'{NAME}.net']
STEER_DOMAINS = [f'{NAME}.com', f'{NAME}.backup']

VENDOR = f'v{NAME}'
TAGS = [f't{NAME}']


app_args = {
    'applicationId': 1,
    'applicationName': NAME,
    'vendor': VENDOR,
    'customTags': TAGS,
    'deepLink': '',
    'users': (),
    'cci': 0,
    'discoveryDomains': DISC_DOMAINS,
    'steeringDomains': STEER_DOMAINS,
}

TOKEN = os.environ['VISOTRUST_TOKEN']


def check_vendor_matches(app, expected_ccl):
    resp = requests.get(
        f'{BASE_URL}/api/v1/relationships', headers={'Authorization': f'Bearer {TOKEN}'}
    )
    resp.raise_for_status()
    matches = 0
    for v in resp.json():
        if v['name'] == app.vendor:
            matches += 1
            assert v['tags'] == [expected_ccl]
    assert matches == 1


plugin = VTPluginARE(config={'token': TOKEN, 'email': EMAIL})


def test_plugin():
    app = Application(**app_args)
    assert plugin.push([app, app, app], None).success
    check_vendor_matches(app, CCLTag.POOR)


def test_dedup_same_tag():
    app = Application(**(app_args | {'vendor': NAME + 'a'}))
    assert plugin.push([app], None).success
    assert plugin.push([app], None).success
    check_vendor_matches(app, CCLTag.POOR)


def test_dedup_same_name():
    app1 = Application(**app_args)
    app2 = Application(**(app_args | {'cci': 95}))
    assert plugin.push([app1], None).success
    check_vendor_matches(app1, CCLTag.POOR)
    assert plugin.push([app2], None).success
    check_vendor_matches(app2, CCLTag.EXCELLENT)
