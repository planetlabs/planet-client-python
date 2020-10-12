from planet.api import downloader
from planet.api.utils import handle_interrupt
import logging
import sys
from concurrent.futures import Future
import threading
import time
import pytest

SPEED_UP = 1000.
WRITE_DELAY = 3 / SPEED_UP
ACTIVATE_DELAY = .5 / SPEED_UP
DOWNLOAD_DELAY = .5 / SPEED_UP
ASSET_DELAY = .5 / SPEED_UP


class Resp(object):

    def __init__(self, resp):
        self.resp = resp

    def get(self):
        return self.resp


class Body(object):
    def __init__(self, name):
        self.name = name
        self._got_write = False

    def write(self, file, callback):
        callback(start=self)
        callback(total=1024, wrote=1024)
        callback(finish=self)
        self._got_write = True

    def wait(self):
        pass

    def cancel(self):
        pass


class Download(object):
    # mirror models.Response kinda, mostly not
    def __init__(self, body, writer):
        self._future = Future()

        def respond():
            self._future.set_result(body)
            writer(body)
        # don't write to the body synchronously
        threading.Timer(WRITE_DELAY, respond).start()

    def wait(self):
        return self._future.result()


def asset(name, type, status):
    return {'_name': name, 'type': type, 'status': status,
            'location': 'http://somewhere/%s/%s' % (type, name)}


def assets(*assets):
    res = {}
    for a in assets:
        res[a['type']] = a
    res['_pinged'] = 0
    return res


class HelperClient(object):

    def __init__(self):
        self.assets = {}
        self._shutdown = False

    def get_assets(self, item):
        if item['id'] in self.assets:
            a = self.assets[item['id']]
            if a['_pinged'] > 2:
                a['a']['status'] = 'active'
                a['b']['status'] = 'active'
            a['_pinged'] += 1
        else:
            a = assets(asset(item['id'] + '.junk', 'a', 'inactive'),
                       asset(item['id'] + '.crud', 'b', 'inactive'))
            self.assets[item['id']] = a
        time.sleep(ASSET_DELAY)
        return Resp(a)

    def activate(self, asset):
        time.sleep(ACTIVATE_DELAY)
        asset['status'] = 'activating'

    def download(self, asset, writer):
        time.sleep(DOWNLOAD_DELAY)
        b = Body(asset['_name'])
        return Download(b, writer)

    def shutdown(self):
        self._shutdown = True


def items_iter(cnt):
    for i in range(cnt):
        yield {'id': str(i)}


def test_pipeline():
    logging.basicConfig(
        stream=sys.stderr, level=logging.INFO,
        format='%(asctime)s %(message)s', datefmt='%M:%S'
    )
    cl = HelperClient()
    items = items_iter(100)
    asset_types = ['a', 'b']
    dl = downloader.create(
        cl, no_sleep=True,
        astage__size=10, pstage__size=10, pstage__min_poll_interval=0,
        dstage__size=2)
    completed = []
    dl.on_complete = lambda *a: completed.append(a)
    stats = handle_interrupt(dl.shutdown, dl.download, items,
                             asset_types, 'dest')
    assert stats == {
        'downloading': 0, 'complete': 200, 'paging': False,
        'downloaded': '0.20MB', 'activating': 0, 'pending': 0
    }
    assert 200 == len(completed)


from planet.scripts import main
from click.testing import CliRunner
import os
from BaseHTTPServer import BaseHTTPRequestHandler
import SocketServer
import random
from multiprocessing import Process
import signal
import json


@pytest.fixture()
def plapi(tmpdir):

    _URI_TO_RESPONSE = {
        '/compute/ops/orders/v2/b0cb3448-0a74-11eb-92a1-a3d779bb08e0': {
            "_links": {
                "_self": "string",
                "results": [
                    {
                        "location": "/foo"
                    }
                ]
            },
            "id": "b0cb3448-0a74-11eb-92a1-a3d779bb08e0",
            "name": "string",
            "subscription_id": 0,
            "tools": [{}],
            "products": [{}],
            "created_on": "2019-08-24T14:15:22Z",
            "last_modified": "2019-08-24T14:15:22Z",
            "state": "queued",
            "last_message": "string",
            "error_hints": [
                "string"
            ],
            "delivery": {
                "single_archive": True,
                "archive_type": "string",
                "archive_filename": "string",
                "layout": {},
                "amazon_s3": {},
                "azure_blob_storage": {},
                "google_cloud_storage": {},
                "google_earth_engine": {}
            },
            "notifications": {
                "webhook": {},
                "email": True
            },
            "order_type": "full"
        },
        
    }
    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

        def do_GET(self):
            if self.path not in _URI_TO_RESPONSE:
                self.send_response(404)
                self.end_headers()
                return

            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(_URI_TO_RESPONSE[self.path]).encode('utf-8'))

    SocketServer.TCPServer.allow_reuse_address = True
    port = random.randint(10000, 20000)
    handler = SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", port), handler)
    path = os.path.join(str(tmpdir))

    def cwd_and_serve():
        os.chdir(path)
        httpd.serve_forever()

    p = Process(target=cwd_and_serve)
    p.daemon = True
    p.start()
    yield 'http://localhost:{}'.format(port)

    os.kill(p.pid, signal.SIGTERM)


def test_all_files_downloaded(tmpdir, monkeypatch, plapi):

    monkeypatch.setenv('PL_API_BASE_URL', plapi)
    monkeypatch.setenv('PL_API_KEY', '1234')
    runner = CliRunner()

    fd = os.open('/dev/null', os.O_RDONLY)
    fd = os.fdopen(fd)

    order_id = 'b0cb3448-0a74-11eb-92a1-a3d779bb08e0'
    args = ['-v', 'orders', 'download', '--dest', str(tmpdir), order_id]
    result = runner.invoke(main, args, catch_exceptions=False, input=fd)
    print result.output
    assert result.exit_code == 0, result.output


if __name__ == '__main__':
    test_pipeline()
