from typing import Optional, cast, Any
import httpx
from abc import ABC

from planet.http import Session
from .request import Request


class _Base(ABC):
    def __init__(self, session: Optional[Session] = None):
        self._session = session or Session()
        acl = self._session._client
        # @todo use real client/session
        self.client = httpx.Client(
            auth=acl.auth,
            headers=acl.headers,
            base_url="https://api.planet.com",
            transport=httpx.HTTPTransport(retries=3)
        )


class Sync(_Base):

    def response(self, r: Request) -> httpx.Response:
        req = r._request()
        resp = self.client.send(req)
        return resp.raise_for_status()

    def json(self, r: Request) -> Any:
        return self.response(r).json()

    def data[T](self, r: Request[T]) -> T:
        return cast(T, r._response(self.response(r)))


class Async(_Base):

    async def response(self, r: Request) -> httpx.Response:
        req = r._request()
        resp = self.client.send(req)
        return resp.raise_for_status()

    async def json(self, r: Request) -> Any:
        resp = await self.response(r)
        return resp.json()

    async def data[T](self, r: Request[T]) -> T:
        resp = await self.response(r)
        return cast(T, r._response(resp))