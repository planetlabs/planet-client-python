# Copyright 2021 Planet Labs, PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
import logging
from http import HTTPStatus

import click
from click.testing import CliRunner
import pytest
import respx
import httpx

from planet.cli import cli

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def invoke():

    def _invoke(extra_args, runner=None):
        runner = runner or CliRunner()
        args = ['orders', '--base-url', TEST_URL] + extra_args
        return runner.invoke(cli.main, args=args)

    return _invoke


TEST_URL = 'http://MockNotRealURL/api/path'
TEST_DOWNLOAD_URL = f'{TEST_URL}/download'
TEST_ORDERS_URL = f'{TEST_URL}/orders/v2'


@pytest.fixture
def mock_download_response(oid, order_description):

    def _func():
        # Mock an HTTP response for download
        order_description['state'] = 'success'
        dl_url1 = TEST_DOWNLOAD_URL + '/1?token=IAmAToken'
        dl_url2 = TEST_DOWNLOAD_URL + '/2?token=IAmAnotherToken'
        order_description['_links']['results'] = [{
            'location': dl_url1
        }, {
            'location': dl_url2
        }]

        get_url = f'{TEST_ORDERS_URL}/{oid}'
        mock_resp = httpx.Response(HTTPStatus.OK, json=order_description)
        respx.get(get_url).return_value = mock_resp

        mock_resp1 = httpx.Response(HTTPStatus.OK,
                                    json={'key': 'value'},
                                    headers={
                                        'Content-Type':
                                        'application/json',
                                        'Content-Disposition':
                                        'attachment; filename="m1.json"'
                                    })
        respx.get(dl_url1).return_value = mock_resp1

        mock_resp2 = httpx.Response(HTTPStatus.OK,
                                    json={'key2': 'value2'},
                                    headers={
                                        'Content-Type':
                                        'application/json',
                                        'Content-Disposition':
                                        'attachment; filename="m2.json"'
                                    })
        respx.get(dl_url2).return_value = mock_resp2

    return _func


@respx.mock
def test_cli_orders_download_quiet(invoke, mock_download_response, oid):
    mock_download_response()

    runner = CliRunner()
    result = runner.invoke(cli.main, args=['orders', 'download', '--base-url', TEST_URL])
            # args = ['orders', '--base-url', TEST_URL] + extra_args
    # return runner.invoke(cli.main, args=args)

    # # quiet_inputs = ['-q', ' --quiet ']
    # runner = CliRunner()
    # # runner = runner or CliRunner()
    # result = invoke(['-q', 'orders', 'download', '--base-url', TEST_URL, oid], runner=runner)
    assert not result.exception
    assert result.output == 'success\n'

#     runner = CliRunner()
#     result = invoke(['wait', '--delay', '0', '--quiet', oid], runner=runner)

    # return runner.invoke(cli.main, args=args)

    # with runner.isolated_filesystem():
    #     for quiet_input in quiet_inputs:
    #         result = invoke([quiet_input, 'orders', 'download', oid], runner=runner)
    #         assert not result.exception


# @respx.mock
# def test_cli_orders_download_quiet(invoke, mock_download_response, oid):
#     mock_download_response()

#     runner = CliRunner()
#     with runner.isolated_filesystem():
#         result = invoke(['download', '--quiet', oid], runner=runner)
#         assert not result.exception


# @respx.mock
# def test_cli_orders_wait_quiet(invoke, order_description, oid):
#     get_url = f'{TEST_ORDERS_URL}/{oid}'

#     order_description['state'] = 'success'

#     route = respx.get(get_url)
#     route.side_effect = [httpx.Response(HTTPStatus.OK, json=order_description)]

#     runner = CliRunner()
#     result = invoke(['wait', '--delay', '0', '--quiet', oid], runner=runner)
#     assert not result.exception
#     assert result.output == 'success\n'


# TODO: when testing multiple values for verbosity, use test parameterization
def test_cli_info_verbosity(monkeypatch):
    log_level = None

    # dummy command so we can invoke cli
    @click.command()
    def test():
        pass

    cli.main.add_command(test)

    def configtest(stream, level, format):
        nonlocal log_level
        log_level = level

    monkeypatch.setattr(cli.logging, 'basicConfig', configtest)

    runner = CliRunner()
    result = runner.invoke(cli.main, args=['test'])
    assert result.exit_code == 0
    assert log_level == logging.WARNING
