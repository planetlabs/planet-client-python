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
import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
import time

import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

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


def submit_order(request, auth):
    auth = HTTPBasicAuth(PLANET_API_KEY, '')

    # set content type to json
    headers = {'content-type': 'application/json'}

    response = requests.post(ORDERS_URL,
                             data=json.dumps(request),
                             auth=auth,
                             headers=headers)
    order_id = response.json()['id']
    logging.debug(order_id)
    return order_id


def poll_for_success(order_url, auth, num_loops=50):
    count = 0
    while(count < num_loops):
        count += 1
        r = requests.get(order_url, auth=auth)
        response = r.json()
        state = response['state']
        print(state)
        end_states = ['success', 'failed', 'partial']
        if state in end_states:
            break
        time.sleep(10)
    if state != 'success':
        raise Exception('order did not succeed')


def test_download_order_cli(order_id):
    with tempfile.TemporaryDirectory() as tmpdirname:
        cmd = ['planet', 'orders', 'download', '--dest', tmpdirname, order_id]
        _run_command_line(cmd)

        files = os.listdir(tmpdirname)
        logging.info(files)

    # can also use the manifest to look for these
    expected_files = [
        '20200505_193841_ssc4d1_0018_analytic_reproject.tif',
        '20200505_193841_ssc4d1_0018_analytic_udm_reproject.tif',
        '20200505_193841_ssc4d1_0018_metadata.json'
    ]

    for f in expected_files:
        assert f in files, '{} not found'.format(f)


def _run_command_line(cmds, stdout=None, stderr=None):
    try:
        cmds = [str(x) for x in cmds]
        logging.debug(' '.join(cmds))
        subprocess.check_call(cmds, stdout=stdout, stderr=stderr)
    except OSError:
        raise OSError('{} not found.'.format(cmds[0]))


def get_parser():
    aparser = argparse.ArgumentParser(
        description='Submit and download an order')
    aparser.add_argument('-o', '--oid',
                         help='order id')
    return aparser


if __name__ == '__main__':
    args = get_parser().parse_args(sys.argv[1:])
    logging.debug(args)

    auth = HTTPBasicAuth(PLANET_API_KEY, '')

    if 'oid' in args:
        order_id = args.oid
    else:
        logging.debug('submitting order')
        order_id = submit_order(ORDER_REQUEST, auth)

    order_url = ORDERS_URL + '/' + order_id
    poll_for_success(order_url, auth)

    messages = []
    for i in range(5):
        try:
            test_download_order_cli(order_id)
        except AssertionError as err:
            messages.append('Test {} failed: {}'.format(i, err))

    if len(messages):
        for m in messages:
            logging.info(m)
    else:
        logging.info('Success!')
