from requests_futures.sessions import FuturesSession

def new_futures_session(max_workers):
    return FuturesSession(max_workers=max_workers)
