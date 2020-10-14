# Copyright 2020 Planet Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Test CLI download. This creates an order, waits for it to be ready, then
downloads it, and confirms all files were downloaded.

Because download is spotty, this runs download 5 times and ensures that all
5 times all files were downloaded.
'''
import json
import logging
import os
import subprocess
import tempfile
import time

from click.testing import CliRunner
import pytest
import requests
from requests.auth import HTTPBasicAuth


# API Key stored as an env variable
PLANET_API_KEY = os.getenv('PL_API_KEY')

ORDERS_URL = 'https://api.planet.com/compute/ops/orders/v2'

ORDER_REQUEST = {
    "name": "20200505_193841_ssc4d1_0018",
    "products": [
        {
          "item_ids": [
            "20200505_193841_ssc4d1_0018"
          ],
          "item_type": "SkySatScene",
          "product_bundle": "analytic"
        }
      ],
    "state": "success",
    "tools": [
        {
          "reproject": {
            "kernel": "cubic",
            "projection": "EPSG:4326"
          }
        }
      ]
}

EXPECTED_FILES = [
        '20200505_193841_ssc4d1_0018_analytic_reproject.tif',
        '20200505_193841_ssc4d1_0018_analytic_udm_reproject.tif',
        '20200505_193841_ssc4d1_0018_metadata.json'
    ]


@pytest.fixture
def runner():
    return CliRunner()


def test_download_order(runner, oid):
    logger = logging.getLogger('test_download_order')
    logging.basicConfig()
    if not oid:
        logger.info('creating order')
        oid = _create_order()
        logger.info('oid: {}'.format(oid))
    else:
        logger.info('oid ({}) given, skipping order creation'.format(oid))

    expected_files = EXPECTED_FILES

    num_runs = 5
    for i in range(num_runs):
        files = _download_order(oid)
        logging.info(files)
        assert len(files), 'no files were downloaded'
        for f in expected_files:
            assert f in files, 'run {}: {} not found'.format(i, f)


def _create_order():
    auth = HTTPBasicAuth(PLANET_API_KEY, '')

    order_id = _submit_order(ORDER_REQUEST, auth)

    order_url = ORDERS_URL + '/' + order_id
    _poll_for_success(order_url, auth)

    return order_id


def _submit_order(request, auth):
    auth = HTTPBasicAuth(PLANET_API_KEY, '')

    # set content type to json
    headers = {'content-type': 'application/json'}

    response = requests.post(ORDERS_URL,
                             data=json.dumps(request),
                             auth=auth,
                             headers=headers)
    order_id = response.json()['id']
    print('order id: {}'.format(order_id))
    return order_id


def _poll_for_success(order_url, auth, num_loops=50):
    count = 0
    while(count < num_loops):
        count += 1
        r = requests.get(order_url, auth=auth)
        response = r.json()
        state = response['state']
        print('Poll: {}'.format(state))
        end_states = ['success', 'failed', 'partial']
        if state in end_states:
            break
        time.sleep(10)
    if state != 'success':
        raise Exception('order did not succeed')


def _download_order(order_id):
    # using CliRunner here results in a return when the download
    # process is still happening (so there is a img.tmp file)
    # and therefore an automatic fail on all runs
    with tempfile.TemporaryDirectory() as tmpdirname:
        cmd = ['planet', '-v', 'orders', 'download', '--dest', tmpdirname,
               order_id]
        _run_command_line(cmd)

        files = os.listdir(tmpdirname)
        # logging.debug(files)
    return files


def _run_command_line(cmds, stdout=None, stderr=None):
    try:
        cmds = [str(x) for x in cmds]
        logging.debug(' '.join(cmds))
        subprocess.check_call(cmds, stdout=stdout, stderr=stderr)
    except OSError:
        raise OSError('{} not found.'.format(cmds[0]))


if __name__ == '__main__':
    test_download_order()
