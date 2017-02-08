from planet.api.helpers import downloader


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
        self._got_write = True

    def await(self):
        pass

    def cancel(self):
        pass


def asset(name, type, status):
    return {"_name": name, "type": type, 'status': status}


def assets(*assets):
    res = {}
    for a in assets:
        res[a['type']] = a
    res['_pinged'] = 0
    return res


class HelperClient(object):

    def __init__(self):
        self.assets = {}

    def get_assets(self, item):
        if item['id'] in self.assets:
            a = self.assets[item['id']]
            if a['_pinged'] > 2:
                a['a']['status'] = 'active'
            a['_pinged'] += 1
        else:
            a = assets(asset(item['id'] + '.junk', 'a', 'inactive'))
            self.assets[item['id']] = a
        return Resp(a)

    def activate(self, asset):
        asset['status'] = 'activating'

    def download(self, asset, writer):
        b = Body(asset['_name'])
        writer(b)
        return b


def items_iter(cnt):
    for i in range(cnt):
        yield {'id': str(i)}


def test_pipeline():
    from planet.api.utils import handle_interrupt
    cl = HelperClient()
    items = items_iter(1)
    asset_types = ['a']
    dl = downloader(cl, asset_types, 'whatever', no_sleep=True, astage_size=2)
    handle_interrupt(dl.shutdown, dl.download, items)
