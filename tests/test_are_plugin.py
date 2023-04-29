import json
import string
from concurrent.futures import Future
from unittest.mock import patch

import pytest
from pydantic import BaseModel
from requests import Response

from are_plugin.main import CCLTag, VTPluginARE
from are_plugin.netskope_model import Application
from are_plugin.url import BASE_URL


class Response(BaseModel):
    status_code: int = 200


def fut(res):
    future = Future()
    future.set_result(res)
    return future


app_args = {
    'applicationId': 1,
    'applicationName': 'xyz',
    'vendor': 'Vendor!',
    'deepLink': '',
    'users': (),
    'cci': 0,
    'customTags': (),
    'discoveryDomains': ('xyz.net',),
    'steeringDomains': ('xyz.com',),
}

app = Application(**app_args)

config = {
    'token': string.ascii_lowercase,
    'email': 'admin@visotrust.com',
    'max_cci': 100,
}


def test_token():
    tokens = []

    class P(VTPluginARE):
        def post(self, session, token, create):
            tokens.append(token)
            return fut(Response())

    P(config=config).push([app], None)
    assert tokens == [config['token']]


@pytest.fixture
def post():
    resp = Response()
    resp.status_code = 200
    with patch('are_plugin.client.util.new_futures_session') as fs_mock:
        post = fs_mock.return_value.__enter__.return_value.post
        post.return_value = fut(resp)
        yield post


def test_http(post):
    VTPluginARE(config=config).push([app], None)

    assert post.call_args.args[0] == f'{BASE_URL}/api/v1/relationships'
    args = post.call_args.kwargs
    assert args['headers']['Authorization'] == f'Bearer {string.ascii_lowercase}'
    j = json.loads(args['data'])
    assert app.vendor == j['name']
    assert config['email'] == j['businessOwnerEmail']
    assert [CCLTag.POOR] == j['tags']


def test_http_avg_cci(post):
    VTPluginARE(config=config).push(
        [app, Application(**(app_args | {'cci': 100}))], None
    )

    args = post.call_args.kwargs
    j = json.loads(args['data'])
    assert [CCLTag.LOW] == j['tags']


def test_http_no_cci(post):
    VTPluginARE(config=config).push([Application(**(app_args | {'cci': None}))], None)

    args = post.call_args.kwargs
    j = json.loads(args['data'])
    assert [CCLTag.UNKNOWN] == j['tags']


def test_http_cci(post):
    VTPluginARE(config=config | {'max_cci': 50}).push(
        [Application(**(app_args | {'cci': 51}))], None
    )

    assert not post.called


def test_http_include(post):
    VTPluginARE(config=config | {'include_cats': 'Homeopathy'}).push(
        [Application(**app_args)], None
    )

    assert not post.called


def test_http_include_pos(post):
    VTPluginARE(config=config | {'include_cats': 'Homeopathy'}).push(
        [Application(**(app_args | {'categoryName': 'Homeopathy'}))], None
    )

    assert post.called


def test_http_exclude(post):
    VTPluginARE(config=config | {'exclude_cats': 'Homeopathy'}).push(
        [Application(**(app_args | {'categoryName': 'Homeopathy'}))], None
    )

    assert not post.called


def test_http_exclude_pos(post):
    VTPluginARE(config=config | {'exclude_cats': 'Homeopathy'}).push(
        [Application(**app_args)], None
    )

    assert post.called
