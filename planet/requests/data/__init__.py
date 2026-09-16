import httpx
from ..request import Simple
from dataclasses import dataclass

@dataclass
class Search:
    """
    Documentation specific to the response (partial for POC)
    """

    name: str
    search_type: str

class GetSearch(Simple[Search]):
    """
    Documentation specific to GetSearch operation
    """

    _response_class = Search
    _url_format = 'https://api.planet.com/data/v1/searches/{id}'

    def __init__(self, id):
        """
        Documentation specific to operation parameters
        """
        self._url_args = {"id": id}

    def _response(self, response: httpx.Response):
        json = response.json()
        # because the model is not complete, need to manually call keywords
        # ideally the Search dataclass would have all the fields declared
        # and this override wouldn't be needed (see Simple._response)
        return Search(name=json["name"], search_type=json["search_type"])