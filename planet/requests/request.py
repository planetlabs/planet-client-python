from typing import TypeVar, ClassVar, Any
import httpx
from abc import ABC, abstractmethod


ResponseType = TypeVar("ResponseType", bound=type)

class Request[ResponseType](ABC):

    _method: str = "GET"
    _url_format: str
    _response_class: ClassVar[type[ResponseType]]

    @abstractmethod
    def _request(self) -> httpx.Request:
        pass

    @abstractmethod
    def _url(self) -> str:
        pass

    @abstractmethod
    def _response(self, response: httpx.Response) -> ResponseType:
        pass


class Simple[ResponseType](Request[ResponseType]):

    _url_args: dict[str, Any]
    _params: dict[str, Any]

    def _url(self):
        return self._url_format.format(**self._url_args)

    def _request(self) -> httpx.Request:
        return httpx.Request(
            method=self._method,
            url=self._url(),
            params=getattr(self, "_params", None),
        )

    def _response(self, response: httpx.Response) -> ResponseType:
        return self._response_class(**response.json())
