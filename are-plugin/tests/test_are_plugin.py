import string, json
from unittest.mock import patch
from pydantic import BaseModel
from concurrent.futures import Future
from requests import Response
from are_plugin.netskope_model import Application

from are_plugin.main import VTPluginARE, CCLTag

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
    'steeringDomains': ('xyz.com',)}

app = Application(**app_args)

config = {'token':   string.ascii_lowercase,
          'email':   'admin@visotrust.com',
          'url':     'http://localhost',
          'max_cci': 100}

def test_token():
    tokens = []

    class P(VTPluginARE):
        def post(self, session, token, create):
            tokens.append(token)
            return fut(Response())

    P(config=config).push([app], None)
    assert tokens == [config['token']]


def mock_resp(fs_mock):
    resp = Response()
    resp.status_code = 200
    post = fs_mock.return_value.__enter__.return_value.post
    post.return_value = fut(resp)
    return post


@patch('are_plugin.client.util.new_futures_session')
def test_http(fs_mock):
    post = mock_resp(fs_mock)

    VTPluginARE(config=config).push([app], None)

    assert post.call_args.args[0] == f'{config["url"]}/api/v1/relationships'
    args = post.call_args.kwargs
    assert args['headers']['Authorization'] == f'Bearer {string.ascii_lowercase}'
    j = json.loads(args['data'])
    assert app.vendor == j['name']
    assert config['email'] == j['businessOwnerEmail']
    assert [CCLTag.POOR] == j['tags']


@patch('are_plugin.client.util.new_futures_session')
def test_http_avg_cci(fs_mock):
    post = mock_resp(fs_mock)

    VTPluginARE(config=config).push(
        [app, Application(**(app_args | {'cci': 100}))], None)

    args = post.call_args.kwargs
    j = json.loads(args['data'])
    assert [CCLTag.LOW] == j['tags']


@patch('are_plugin.client.util.new_futures_session')
def test_http_no_cci(fs_mock):
    post = mock_resp(fs_mock)

    VTPluginARE(config=config).push(
        [Application(**(app_args | {'cci': None}))], None)

    args = post.call_args.kwargs
    j = json.loads(args['data'])
    assert [CCLTag.UNKNOWN] == j['tags']


@patch('are_plugin.client.util.new_futures_session')
def test_http_cci(fs_mock):
    post = fs_mock.return_value.__enter__.return_value.post

    VTPluginARE(config=config | {'max_cci': 50}).push(
        [Application(**(app_args | {'cci': 51}))], None)

    assert not post.called
