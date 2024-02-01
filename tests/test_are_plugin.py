import json
import string
from unittest.mock import patch

import pytest
from pydantic import BaseModel
from requests import Response

from are_plugin.main import CCLTag, VTPluginARE
from are_plugin.netskope_model import Application
from are_plugin.url import BASE_URL


class Response(BaseModel):
    status_code: int = 200


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
        def post(self, token, create, hosts):
            tokens.append(token)
            return Response()

    P(config=config).push([app], None)
    assert tokens == [config['token']]


@pytest.fixture
def post():
    resp = Response()
    resp.status_code = 200
    with patch('are_plugin.main.VTPluginARE.post') as post_mock:
        post_mock.return_value = resp
        yield post_mock


@pytest.fixture
def req_post():
    resp = Response()
    resp.status_code = 200
    with patch('are_plugin.main.requests.post') as post_mock:
        post_mock.return_value = resp
        yield post_mock


@pytest.fixture
def search_empty():
    class Resp(Response):
        status_code = 200

        def json(self):
            return []

    with patch('are_plugin.main.requests.get') as get_mock:
        get_mock.return_value = Resp()
        yield get_mock


def test_http(search_empty, req_post):
    VTPluginARE(config=config).push([app], None)

    assert req_post.call_args.args[0] == f'{BASE_URL}/api/v1/relationships'
    args = req_post.call_args.kwargs
    assert args['headers']['Authorization'] == f'Bearer {string.ascii_lowercase}'
    j = json.loads(args['data'])
    assert app.vendor == j['name']
    assert config['email'] == j['businessOwnerEmail']
    assert [CCLTag.POOR] == j['tags']


def test_http_avg_cci(search_empty, req_post):
    VTPluginARE(config=config).push(
        [app, Application(**(app_args | {'cci': 100}))], None
    )

    args = req_post.call_args.kwargs
    j = json.loads(args['data'])
    assert [CCLTag.LOW] == j['tags']


def test_http_no_cci(search_empty, req_post):
    VTPluginARE(config=config).push([Application(**(app_args | {'cci': None}))], None)

    args = req_post.call_args.kwargs
    j = json.loads(args['data'])
    assert [CCLTag.UNKNOWN] == j['tags']


def test_http_cci(post):
    VTPluginARE(config=config | {'max_cci': 50}).push(
        [Application(**(app_args | {'cci': 51}))], None
    )

    assert not post.called


ID = 56


@pytest.fixture
def search_result():
    class Resp(Response):
        status_code = 200

        def json(self):
            return [{'id': ID, 'tags': []}]

    with patch('are_plugin.main.requests.get') as search_mock:
        search_mock.return_value = Resp()
        yield search_mock


@pytest.fixture
def req_patch():
    with patch('are_plugin.main.requests.patch') as patch_mock:
        patch_mock.return_value = Response()
        yield patch_mock


def test_update(search_result, req_patch):
    VTPluginARE(config=config).push([app], None)

    assert search_result.call_args.args[0] == f'{BASE_URL}/api/v1/relationships/search'
    assert req_patch.call_args.args[0] == f'{BASE_URL}/api/v1/relationships'
    args = req_patch.call_args.kwargs
    j = json.loads(args['data'])
    assert j['id'] == ID
    assert j['tags'] == [CCLTag.POOR]
