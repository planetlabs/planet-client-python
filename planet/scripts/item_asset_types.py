import requests
from planet.api.dispatch import _get_user_agent

ITEM_TYPE_URL = 'https://api.planet.com/data/v1/item-types/'
ASSET_TYPE_URL = 'https://api.planet.com/data/v1/asset-types/'

_item_types = None
_asset_types = None

# Default values here are used as a fallback
# In case the API fails to respond or takes too long.
DEFAULT_ITEM_TYPES = [
    "PSScene4Band", "PSScene3Band", "REScene", "SkySatScene",
    "REOrthoTile", "Sentinel2L1C", "PSOrthoTile", "Landsat8L1G"]

DEFAULT_ASSET_TYPES = [
    "analytic", "analytic_b1", "analytic_b10", "analytic_b11", "analytic_b12",
    "analytic_b2", "analytic_b3", "analytic_b4", "analytic_b5", "analytic_b6",
    "analytic_b7", "analytic_b8", "analytic_b8a", "analytic_b9",
    "analytic_bqa", "analytic_dn", "analytic_dn_xml", "analytic_ms",
    "analytic_xml", "basic_analytic", "basic_analytic_b1",
    "basic_analytic_b1_nitf", "basic_analytic_b2", "basic_analytic_b2_nitf",
    "basic_analytic_b3", "basic_analytic_b3_nitf", "basic_analytic_b4",
    "basic_analytic_b4_nitf", "basic_analytic_b5", "basic_analytic_b5_nitf",
    "basic_analytic_dn", "basic_analytic_dn_nitf", "basic_analytic_dn_rpc",
    "basic_analytic_dn_rpc_nitf", "basic_analytic_dn_xml",
    "basic_analytic_dn_xml_nitf", "basic_analytic_nitf", "basic_analytic_rpc",
    "basic_analytic_rpc_nitf", "basic_analytic_sci", "basic_analytic_xml",
    "basic_analytic_xml_nitf", "basic_panchromatic_dn",
    "basic_panchromatic_dn_rpc", "basic_udm", "browse", "metadata_aux",
    "metadata_txt", "udm", "visual", "visual_xml"
]


def _get_json_or_raise(url, timeout=0.7):
    headers = {'User-Agent': _get_user_agent()}
    resp = requests.get(url, timeout=timeout, headers=headers)
    resp.raise_for_status()
    return resp.json()


def get_item_types():
    global _item_types
    if _item_types is None:
        try:
            data = _get_json_or_raise(ITEM_TYPE_URL)
            _item_types = [it['id'] for it in data['item_types']]
        except:
            _item_types = DEFAULT_ITEM_TYPES
    return _item_types


def get_asset_types():
    global _asset_types
    if _asset_types is None:
        try:
            data = _get_json_or_raise(ASSET_TYPE_URL)
            _asset_types = [a['id'] for a in data['asset_types']]
        except:
            _asset_types = DEFAULT_ASSET_TYPES
    return _asset_types
