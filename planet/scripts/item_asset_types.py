import requests
from planet.api.dispatch import _get_user_agent
from planet.api.auth import find_api_key

ITEM_TYPE_URL = 'https://api.planet.com/data/v1/item-types/'
ASSET_TYPE_URL = 'https://api.planet.com/data/v1/asset-types/'

_item_types = None
_asset_types = None
_bundles = None

# Default values here are used as a fallback
# In case the API fails to respond or takes too long.
DEFAULT_ITEM_TYPES = [
    'Landsat8L1G',
    'MOD09GA',
    'MOD09GQ',
    'MYD09GA',
    'MYD09GQ',
    'PSOrthoTile',
    'PSScene3Band',
    'PSScene4Band',
    'REOrthoTile',
    'REScene',
    'Sentinel1',
    'Sentinel2L1C',
    'SkySatCollect',
    'SkySatScene',
    'SkySatVideo'
]

DEFAULT_ASSET_TYPES = [
    'analytic', 'analytic_b1', 'analytic_b10', 'analytic_b11', 'analytic_b12',
    'analytic_b2', 'analytic_b3', 'analytic_b4', 'analytic_b5', 'analytic_b6',
    'analytic_b7', 'analytic_b8', 'analytic_b8a', 'analytic_b9',
    'analytic_bqa', 'analytic_dn', 'analytic_dn_xml', 'analytic_gflags',
    'analytic_granule_pnt', 'analytic_iobs_res', 'analytic_ms',
    'analytic_num_observations', 'analytic_num_observations_1km',
    'analytic_num_observations_500m', 'analytic_obscov',
    'analytic_obscov_500m', 'analytic_orbit_pnt', 'analytic_q_scan',
    'analytic_qc_250m', 'analytic_qc_500m', 'analytic_range',
    'analytic_sensor_azimuth', 'analytic_sensor_zenith',
    'analytic_solar_azimuth', 'analytic_solar_zenith', 'analytic_sr',
    'analytic_state_1km', 'analytic_sur_refl_b01', 'analytic_sur_refl_b02',
    'analytic_sur_refl_b03', 'analytic_sur_refl_b04', 'analytic_sur_refl_b05',
    'analytic_sur_refl_b06', 'analytic_sur_refl_b07', 'analytic_xml',
    'basic_analytic', 'basic_analytic_b1', 'basic_analytic_b1_nitf',
    'basic_analytic_b2', 'basic_analytic_b2_nitf', 'basic_analytic_b3',
    'basic_analytic_b3_nitf', 'basic_analytic_b4', 'basic_analytic_b4_nitf',
    'basic_analytic_b5', 'basic_analytic_b5_nitf', 'basic_analytic_dn',
    'basic_analytic_dn_nitf', 'basic_analytic_dn_rpc',
    'basic_analytic_dn_rpc_nitf', 'basic_analytic_dn_xml',
    'basic_analytic_dn_xml_nitf', 'basic_analytic_nitf', 'basic_analytic_rpc',
    'basic_analytic_rpc_nitf', 'basic_analytic_sci', 'basic_anlytic_udm',
    'basic_analytic_udm2', 'basic_analytic_xml', 'basic_analytic_xml_nitf',
    'basic_l1a_panchromatic_dn', 'basic_l1a_panchromatic_dn_rpc',
    'basic_panchromatic', 'basic_panchromatic_dn', 'basic_panchromatic_dn_rpc',
    'basic_panchromatic_rpc', 'basic_panchromatic_udm2', 'basic_udm',
    'basic_udm2', 'browse', 'metadata_aux', 'metadata_txt', 'ortho_analytic',
    'ortho_analytic_dn', 'ortho_analytic_hh', 'ortho_analytic_hv',
    'ortho_analytic_udm', 'ortho_analytic_udm2', 'ortho_analytic_vh',
    'ortho_analytic_vv', 'ortho_panchromatic', 'ortho_panchromatic_dn',
    'ortho_panchromatic_udm', 'ortho_panchromatic_udm2', 'ortho_pansharpened',
    'ortho_pansharpened_udm', 'ortho_pansharpened_udm2', 'ortho_visual', 'udm',
    'udm2', 'video_file', 'video_frames', 'video_metadata', 'visual',
    'visual_xml'
]

DEFAULT_BUNDLES = [u'all', u'all_udm2', u'analytic', u'analytic_sr',
                   u'analytic_sr_udm2', u'analytic_udm2', u'basic_analytic',
                   u'basic_analytic_nitf', u'basic_analytic_nitf_udm2',
                   u'basic_analytic_udm2', u'basic_panchromatic',
                   u'basic_panchromatic_dn', u'basic_uncalibrated_dn',
                   u'basic_uncalibrated_dn_nitf',
                   u'basic_uncalibrated_dn_nitf_udm2',
                   u'basic_uncalibrated_dn_udm2', u'panchromatic',
                   u'panchromatic_dn', u'panchromatic_dn_udm2',
                   u'pansharpened', u'pansharpened_udm2', u'skysatvideo',
                   u'uncalibrated_dn', u'uncalibrated_dn_udm2', u'visual']


def _get_json_or_raise(url, timeout=11):
    api_key = find_api_key()
    headers = {'User-Agent': _get_user_agent(),
               'Authorization': 'api-key %s' % api_key}
    resp = requests.get(url, timeout=timeout, headers=headers)
    resp.raise_for_status()
    return resp.json()


def get_item_types():
    global _item_types
    if _item_types is None:
        _item_types = DEFAULT_ITEM_TYPES
        data = _get_json_or_raise(ITEM_TYPE_URL)
        _item_types = [it['id'] for it in data['item_types']]
    return _item_types


def get_asset_types():
    global _asset_types
    if _asset_types is None:
        _asset_types = DEFAULT_ASSET_TYPES
        data = _get_json_or_raise(ASSET_TYPE_URL)
        _asset_types = [a['id'] for a in data['asset_types']]
    return _asset_types


def get_bundles():
    global _bundles
    if _bundles is None:
        _bundles = DEFAULT_BUNDLES
        # TODO if/when bundles defs are served by API we can grab them here
    return _bundles
