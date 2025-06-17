from dataclasses import dataclass
from pathlib import Path
import json
from typing import Optional
import httpx
import pytest

import respx
from click.testing import CliRunner

from planet.cli import cli

baseurl = "http://basemaps.com/v1/"

uuid = "09462e5a-2af0-4de3-a710-e9010d8d4e58"


def url(path: str) -> str:
    return baseurl + path


def request(path: str,
            json,
            method="GET",
            status=200,
            headers=None,
            stream=None):

    def go():
        respx.request(method,
                      url(path)).return_value = httpx.Response(status,
                                                               json=json,
                                                               headers=headers,
                                                               stream=stream)

    return go


def quad_item_downloads(cnt):
    return [{
        "_links": {
            "download": url(f"mosaics/download-a-quad/{i}")
        },
        "id": f"456-789{i}"
    } for i in range(cnt)]


def quad_item_download_requests(cnt):
    return [
        request(f"mosaics/download-a-quad/{i}",
                None,
                stream=stream(),
                headers={
                    "Content-Length": "100",
                }) for i in range(cnt)
    ]


async def stream():
    yield bytes("data" * 25, encoding="ascii")


@dataclass
class CLITestCase:
    id: str
    command: list[str]
    args: list[str]
    requests: list
    exit_code: int = 0
    output: Optional[dict] = None
    expect_files: Optional[list[str]] = None
    exception: Optional[str] = None


info_cases = [
    CLITestCase(id="info",
                command=["info"],
                args=[uuid],
                output={"name": "a mosaic"},
                requests=[
                    request(f"mosaics/{uuid}", {"name": "a mosaic"}),
                ]),
    CLITestCase(id="info not exist by uuid",
                command=["info"],
                args=[uuid],
                output='Error: {"message":"Mosaic Not Found: fff"}\n',
                exit_code=1,
                requests=[
                    request(f"mosaics/{uuid}",
                            {"message": "Mosaic Not Found: fff"},
                            status=404),
                ]),
    CLITestCase(id="info not exist by name",
                command=["info"],
                args=["fff"],
                output='Error: {"message":"Mosaic Not Found: fff"}\n',
                exit_code=1,
                requests=[request("mosaics?name__is=fff", {"mosaics": []})]),
]

list_mosaic_cases = [
    CLITestCase(id="list",
                command=["list"],
                args=[],
                output=[{
                    "name": "a mosaic"
                }],
                requests=[
                    request("mosaics", {"mosaics": [{
                        "name": "a mosaic"
                    }]}),
                ]),
    CLITestCase(
        id="list with filters",
        command=["list"],
        args=[
            "--name-contains",
            "name",
            "--interval",
            "1 day",
            "--acquired_lt",
            "2025-05-19",
            "--acquired_gt",
            "2024-05-19"
        ],
        output=[{
            "name": "a mosaic"
        }],
        requests=[
            request(
                "mosaics?name__contains=name&interval=1+day&acquired__gt=2024-05-19+00%3A00%3A00&acquired__lt=2025-05-19+00%3A00%3A00",
                {"mosaics": [{
                    "name": "a mosaic"
                }]}),
        ]),
]

series_info_cases = [
    CLITestCase(
        id="series info",
        command=["series", "info"],
        args=["Global Monthly"],
        output={"id": "123"},
        requests=[
            request("series?name__is=Global+Monthly",
                    {"series": [{
                        "id": "123"
                    }]})
        ],
    ),
    CLITestCase(
        id="series info by name does not exist",
        command=["series", "info"],
        args=["non-existing-series"],
        output='Error: {"message":"Series Not Found: non-existing-series"}\n',
        exit_code=1,
        requests=[
            request("series?name__is=non-existing-series", {"series": []})
        ],
    ),
    CLITestCase(
        id="series info by uuid does not exist",
        command=["series", "info"],
        args=[uuid],
        output='Error: {"message":"Series Not Found: fff"}\n',
        exit_code=1,
        requests=[
            request(f"series/{uuid}", {"message": "Series Not Found: fff"},
                    status=404),
        ],
    ),
]

list_series_cases = [
    CLITestCase(id="series list",
                command=["series", "list"],
                args=[],
                output=[{
                    "name": "a series"
                }],
                requests=[
                    request("series", {"series": [{
                        "name": "a series"
                    }]}),
                ]),
    CLITestCase(
        id="series list filters",
        command=["series", "list"],
        args=[
            "--name-contains",
            "name",
            "--interval",
            "1 day",
            "--acquired_lt",
            "2025-05-19",
            "--acquired_gt",
            "2024-05-19"
        ],
        output=[{
            "name": "a series"
        }],
        requests=[
            request(
                "series?name__contains=name&interval=1+day&acquired__gt=2024-05-19+00%3A00%3A00&acquired__lt=2025-05-19+00%3A00%3A00",
                {"series": [{
                    "name": "a series"
                }]}),
        ]),
    CLITestCase(id="series list-mosaics",
                command=["series", "list-mosaics"],
                args=[uuid],
                output=[{
                    "name": "a mosaic"
                }],
                requests=[
                    request(
                        "series/09462e5a-2af0-4de3-a710-e9010d8d4e58/mosaics",
                        {"mosaics": [{
                            "name": "a mosaic"
                        }]}),
                ]),
    CLITestCase(
        id="series list-mosaics filters",
        command=["series", "list-mosaics"],
        args=[
            "Some Series",
            "--acquired_lt",
            "2025-05-19",
            "--acquired_gt",
            "2024-05-19",
            "--latest"
        ],
        output=[{
            "name": "a mosaic"
        }],
        requests=[
            request("series?name__is=Some+Series", {"series": [{
                "id": "123"
            }]}),
            request(
                "series/123/mosaics?acquired__gt=2024-05-19+00%3A00%3A00&acquired__lt=2025-05-19+00%3A00%3A00&latest=yes",
                {"mosaics": [{
                    "name": "a mosaic"
                }]}),
        ]),
]

search_cases = [
    CLITestCase(
        id="mosaics search bbox",
        command=["search"],
        args=[uuid, "--bbox", "-100,40,-100,40"],
        output=[{
            "id": "455-1272"
        }],
        requests=[
            request(
                f"mosaics/{uuid}",
                {
                    "_links": {
                        "quads": url(
                            "mosaics/09462e5a-2af0-4de3-a710-e9010d8d4e58/quads?bbox={lx},{ly},{ux},{uy}"
                        )
                    }
                }),
            request(
                "mosaics/09462e5a-2af0-4de3-a710-e9010d8d4e58/quads?bbox=-100.0,40.0,-100.0,40.0",
                {"items": [{
                    "id": "455-1272"
                }]}),
        ]),
    CLITestCase(
        id="mosaics search bbox summary",
        command=["search"],
        args=[uuid, "--bbox", "-100,40,-100,40", "--summary"],
        output={"total_quads": 1234},
        requests=[
            request(
                f"mosaics/{uuid}",
                {
                    "_links": {
                        "quads": url(
                            "mosaics/09462e5a-2af0-4de3-a710-e9010d8d4e58/quads?bbox={lx},{ly},{ux},{uy}"
                        )
                    }
                }),
            request(
                "mosaics/09462e5a-2af0-4de3-a710-e9010d8d4e58/quads?bbox=-100.0,40.0,-100.0,40.0&minimal=true&summary=true",
                {
                    # note this gets stripped from expected output
                    "items": [{
                        "id": "455-1272"
                    }],
                    "summary": {
                        "total_quads": 1234
                    }
                }),
        ]),
]

download_cases = [
    CLITestCase(
        id="mosaics download bbox",
        command=["download"],
        args=[uuid, "--bbox", '-100,40,-100,40'],
        requests=[
            request(
                f"mosaics/{uuid}",
                {
                    "id": "123",
                    "name": "a mosaic",
                    "_links": {
                        "quads": url(
                            "mosaics/123/quads?bbox={lx},{ly},{ux},{uy}")
                    }
                }),
            request(
                "mosaics/123/quads?bbox=-100.0,40.0,-100.0,40.0&minimal=true",
                {"items": quad_item_downloads(1)}),
            *quad_item_download_requests(1),
        ],
        expect_files=[
            "a mosaic/456-7890.tif",
        ]),
    CLITestCase(
        id="mosaics download geometry",
        command=["download"],
        args=[uuid, "--geometry", '{"type": "Point", "coordinates": [0,0]}'],
        requests=[
            request(f"mosaics/{uuid}", {
                "id": "123", "name": "a mosaic"
            }),
            request("mosaics/123/quads/search?minimal=true", {},
                    status=302,
                    method="POST",
                    headers={"Location": url("mosaics/search-link")}),
            request("mosaics/search-link", {"items": quad_item_downloads(5)}),
            *quad_item_download_requests(5),
        ],
        expect_files=[
            "a mosaic/456-7890.tif",
            "a mosaic/456-7891.tif",
            "a mosaic/456-7892.tif",
            "a mosaic/456-7893.tif",
            "a mosaic/456-7894.tif",
        ])
]

other_cases = [
    CLITestCase(
        id="quad contributions",
        command=["contributions"],
        args=["mosaic-name", "quad-id"],
        output=[{
            "link": "https://api.planet.com/some/item"
        }],
        requests=[
            request("mosaics?name__is=mosaic-name",
                    {"mosaics": [{
                        "id": "123"
                    }]}),
            request(
                "mosaics/123/quads/quad-id",
                {"_links": {
                    "items": url("mosaics/123/quads/quad-id/items")
                }}),
            request("mosaics/123/quads/quad-id/items",
                    {"items": [{
                        "link": "https://api.planet.com/some/item"
                    }]})
        ]),
]

test_cases = info_cases + series_info_cases + list_mosaic_cases + list_series_cases + search_cases + download_cases + other_cases


@pytest.mark.parametrize("tc",
                         [pytest.param(tc, id=tc.id) for tc in test_cases])
def test_cli(tc: CLITestCase):
    run_test(tc)


@respx.mock
def run_test(tc: CLITestCase):
    runner = CliRunner()
    with runner.isolated_filesystem() as folder:
        for r in tc.requests:
            r()

        args = ["mosaics", "-u", baseurl] + tc.command + tc.args
        result = runner.invoke(cli.main, args=args)
        # result.exception may be SystemExit which we want to ignore
        # but if we don't raise a "true error" exception, there's no
        # stack trace, making it difficult to diagnose
        if result.exception and tc.exit_code == 0:
            raise result.exception
        assert result.exit_code == tc.exit_code, result.output
        if tc.output:
            try:
                # error output (always?) not JSON
                output = json.loads(result.output)
            except json.JSONDecodeError:
                output = result.output
            assert output == tc.output
        if tc.expect_files:
            for f in tc.expect_files:
                assert Path(folder, f).exists(), f
