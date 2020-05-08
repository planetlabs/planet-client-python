import os
import json

import pytest
import requests_mock
from planet.api.experimental.basemaps_client import BasemapsClientV1
from planet.api import APIException


@pytest.fixture()
def basemaps_client():
    return BasemapsClientV1('fakekey')


def test_list_basemap_series(basemaps_client):
    with requests_mock.Mocker() as m:
        path = 'basemaps/v1/series/'
        page1_url = os.path.join(basemaps_client.base_url, path)
        page2_url = page1_url + "?_page=2&_page_size=4"
        # page1 has 4 results and a _next link
        page1 = {
            "_links": {
                "_next": page2_url,
                "_self": page1_url
            },
            "series": [{"id": i,
                        "name": "test {}".format(i)}
                       for i in range(1, 5)]
        }
        # page2 has 2 results and no _next link
        page2 = {
            "_links": {
                "_self": page1_url
            },
            "series": [{"id": i,
                        "name": "test {}".format(i)}
                       for i in range(5, 7)]
        }
        m.get(page1_url, text=json.dumps(page1))
        m.get(page2_url, text=json.dumps(page2))
        # series is a generator
        series = basemaps_client.list_basemap_series()
        # check the first series value
        first_result = next(series)
        assert first_result.get("id") == 1
        assert first_result.get("name") == "test 1"
        # only requested page 1 so far
        assert m.call_count == 1
        series_list = list(basemaps_client.list_basemap_series())
        assert len(series_list) == 6
        # made 2 more requests for pages 1 and 2
        assert m.call_count == 3


def test_list_basemap_series_api_error(basemaps_client):
    with requests_mock.Mocker() as m:
        path = 'basemaps/v1/series/'
        url = os.path.join(basemaps_client.base_url, path)
        m.get(url, text='{"message":"oops"}', status_code=401)
        with pytest.raises(APIException):
            series = basemaps_client.list_basemap_series()
            next(series)


def test_get_basemap_series(basemaps_client):
    with requests_mock.Mocker() as m:
        test_id = "aaaa-bbb-ccc"
        path = 'basemaps/v1/series/{}'.format(test_id)
        url = os.path.join(basemaps_client.base_url, path)
        test_series = {
            "_links": {"_self": url},
            "id": test_id,
            "name": "test mosaic series",
        }
        m.get(url, text=json.dumps(test_series))
        retrieved_series = basemaps_client.get_basemap_series(test_id)
        assert retrieved_series == test_series
