from planet.quota_request import (build_estimate_quota_reservations_request,
                                  build_create_bulk_quota_reservations_request,
                                  get_my_products_request,
                                  get_quota_reservations_request)


def test_build_estimate_quota_reservations_request():
    payload = {"aoi_refs": ["aoi_1"], "product_id": 123}
    aoi_refs = payload["aoi_refs"]
    product_id = payload["product_id"]
    request = build_estimate_quota_reservations_request(aoi_refs, product_id)
    expected = {
        "estimated_costs": [{
            "aoi_ref": aoi_refs[0], "cost": 2000
        }],
        "quota_remaining": 8000,
        "total_cost": 2000
    }
    assert request == expected


def test_build_create_bulk_quota_reservations_request():
    payload = {"aoi_refs": ["aoi_1"], "product_id": 123}
    aoi_refs = payload["aoi_refs"]
    product_id = payload["product_id"]
    request = build_create_bulk_quota_reservations_request(
        aoi_refs, product_id)
    expected = {"job_id": "1", "status": "pending"}
    assert request == expected


def test_get_my_products_request():
    organization_id = 1
    quota_style = "style"
    limit = 10
    offset = 0
    request = get_my_products_request(organization_id,
                                      quota_style,
                                      limit,
                                      offset)
    expected = {
        "organization_id": organization_id,
        "quota_style": quota_style,
        "limit": limit,
        "offset": offset
    }
    assert request == expected


def test_get_quota_reservations_request():
    limit = 10
    offset = 0
    sort = "created_at"
    fields = "id,name"
    filters = {"status": "active"}
    request = get_quota_reservations_request(limit,
                                             offset,
                                             sort,
                                             fields,
                                             filters)
    expected = {
        "limit": limit,
        "offset": offset,
        "sort": sort,
        "fields": fields,
        "filters": filters
    }
    assert request == expected
