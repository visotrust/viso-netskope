import string
from unittest.mock import patch
from pydantic import BaseModel
from concurrent.futures import Future
from requests import Response
from are_plugin.netskope_model import Application

from are_plugin.main import VTPluginARE

class Response(BaseModel):
    status_code: int = 200

def fut(res):
    future = Future()
    future.set_result(res)
    return future

app = Application(
    applicationId=1,
    applicationName='xyz',
    vendor='Vendor!',
    deepLink='',
    users=(),
    customTags=(),
    discoveryDomains=('xyz.net',),
    steeringDomains=('xyz.com',))

def test_token():
    token = string.ascii_letters
    tokens = []

    class P(VTPluginARE):
        def post(self, session, token, create):
            tokens.append(token)
            return fut(Response())

    P(config={'token': token}).push([app], None)
    assert tokens == [token]


@patch('are_plugin.client.util.new_futures_session')
def test_http(fs_mock):
    resp = Response()
    resp.status_code = 200
    post = fs_mock.return_value.__enter__.return_value.post
    post.return_value = fut(resp)

    VTPluginARE(config={'token': string.ascii_lowercase}).push(
        [app], None)


    assert post.call_args.args[0].endswith('/api/v1/relationships')
    args = post.call_args.kwargs
    assert args['headers']['Authorization'] == f'Bearer {string.ascii_lowercase}'
    assert app.vendor in args['json']