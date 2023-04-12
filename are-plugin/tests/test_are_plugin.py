import string, asyncio
from pydantic import BaseModel
from concurrent.futures import Future
from are_plugin.netskope_model import Application

from are_plugin.main import VTPluginARE

class Response(BaseModel):
    code: int = 200

def fut(res):
    future = Future()
    future.set_result(res)
    return future

def test_token():
    token = string.ascii_letters
    tokens = []
    loop = asyncio.get_event_loop()

    class P(VTPluginARE):
        def post(self, session, token, create):
            tokens.append(token)
            return fut(Response())

    P(config={'token': token}).push(
        [Application(
            applicationId=1,
            applicationName='xyz',
            vendor='',
            deepLink='',
            users=(),
            customTags=(),
            discoveryDomains=('xyz.net',),
            steeringDomains=('xyz.com',))], None)
    assert tokens == [token]
