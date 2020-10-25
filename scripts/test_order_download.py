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

Because download is spotty, this runs download multiple times and ensures that
each time all files were downloaded.
'''
import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
import time

# from click.testing import CliRunner
import requests
from requests.auth import HTTPBasicAuth


# logging.basicConfig(filename='example.log', level=logging.DEBUG)
# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logging.basicConfig(
    stream=sys.stderr, level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
# logging.getLogger('planet.api.dispatch').setLevel(logging.WARNING)
# logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
# API Key stored as an env variable
PLANET_API_KEY = os.getenv('PL_API_KEY')

ORDERS_URL = 'https://api.planet.com/compute/ops/orders/v2'

# equivalent to:
# planet orders create --item-type SkySatScene --bundle analytic \
#   --id 20200505_193841_ssc4d1_0018 --name 20200505_193841_ssc4d1_0018
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
    "delivery": {
        "archive_filename": "{{name}}_{{order_id}}.zip",
        "archive_type": "zip",
        "single_archive": True
        },
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
    return order_id


def poll_for_success(order_url, auth, num_loops=50):
    count = 0
    while(count < num_loops):
        count += 1
        r = requests.get(order_url, auth=auth)
        response = r.json()
        state = response['state']
        logger.info(state)
        end_states = ['success', 'failed', 'partial']
        if state in end_states:
            break
        time.sleep(10)
    if state != 'success':
        raise Exception('order did not succeed')


def test_download_order(order_id, num_runs):
    # # these are the files inside the zip
    # expected_files = [
    #     '20200505_193841_ssc4d1_0018_analytic_reproject.tif',
    #     '20200505_193841_ssc4d1_0018_analytic_udm_reproject.tif',
    #     '20200505_193841_ssc4d1_0018_metadata.json',
    #     'manifest.json'
    # ]

    expected_files = [
        '20200505_193841_ssc4d1_0018_53d1209a-af58-40ce-974f-3570f4e20326.zip',
        'manifest.json'
    ]

    messages = []
    for i in range(num_runs):
        logging.debug('TEST {}'.format(i))
        files = download_order_cli(order_id)
        if not len(files) == len(expected_files):
            messages.append('TEST {}'.format(i))
            messages.append('{} != {}'.format(len(files), len(expected_files)))
            for f in expected_files:
                if f not in files:
                    messages.append('{} not found'.format(f))

    if len(messages):
        for m in messages:
            logger.info(m)
    else:
        logger.info('Success!')


def download_order_cli(order_id):
    with tempfile.TemporaryDirectory() as tmpdirname:
        cmd = ['planet', '-vv', 'orders', 'download', '--dest', tmpdirname,
               order_id]

        logging.debug(cmd)
        _run_command_line(cmd)

        files = os.listdir(tmpdirname)
        logger.debug(files)
    return files


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
    aparser.add_argument('-r', '--runs', type=int, default=5,
                         help='number of runs')
    return aparser


if __name__ == '__main__':
    args = get_parser().parse_args(sys.argv[1:])
    logger.debug(args)

    auth = HTTPBasicAuth(PLANET_API_KEY, '')

    if args.oid:
        order_id = args.oid
    else:
        logging.debug('submitting order')
        order_id = submit_order(ORDER_REQUEST, auth)

    order_url = ORDERS_URL + '/' + order_id
    poll_for_success(order_url, auth)

    test_download_order(order_id, args.runs)
    logger.info('order id: {}'.format(order_id))
