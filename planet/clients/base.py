from typing import Any, AsyncIterator, Coroutine, Iterator, TypeVar
from planet.http import Session

T = TypeVar("T")


class _BaseClient:

    def __init__(self, session: Session, base_url: str):
        """
        Parameters:
            session: Open session connected to server.
            base_url: The base URL to use. Defaults to production data API
                base url.
        """
        self._session = session

        self._base_url = base_url
        if self._base_url.endswith('/'):
            self._base_url = self._base_url[:-1]

    def _call_sync(self, f: Coroutine[Any, Any, T]) -> T:
        """block on an async function call, using the call_sync method of the session"""
        return self._session._call_sync(f)

    def _aiter_to_iter(self, aiter: AsyncIterator[T]) -> Iterator[T]:
        return self._session._aiter_to_iter(aiter)
