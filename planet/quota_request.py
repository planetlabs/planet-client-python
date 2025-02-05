from typing import List, Dict, Any, Optional


def build_estimate_quota_reservations_request(
        aoi_refs: List[str], product_id: int) -> Dict[str, Any]:
    return {
        "estimated_costs": [{
            "aoi_ref": aoi_refs[0], "cost": 2000
        }],
        "quota_remaining": 8000,
        "total_cost": 2000
    }


def build_create_bulk_quota_reservations_request(
        aoi_refs: List[str], product_id: int) -> Dict[str, Any]:
    return {"job_id": "1", "status": "pending"}


def get_my_products_request(organization_id: int,
                            quota_style: Optional[str] = None,
                            limit: Optional[int] = None,
                            offset: Optional[int] = None) -> Dict[str, Any]:
    return {
        "organization_id": organization_id,
        "quota_style": quota_style,
        "limit": limit,
        "offset": offset
    }


def get_quota_reservations_request(
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort: Optional[str] = None,
        fields: Optional[str] = None,
        filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    return {
        "limit": limit,
        "offset": offset,
        "sort": sort,
        "fields": fields,
        "filters": filters
    }
