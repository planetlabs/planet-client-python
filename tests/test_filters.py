import pytest
from pytz import timezone
from datetime import datetime
from planet.api import filters


@pytest.mark.parametrize('dt, expected', [
    (datetime(1900, 1, 1, tzinfo=timezone("US/Central")),
     {'field_name': 'acquired',
      'type': 'DateRangeFilter',
      'config': {'gte': '1900-01-01T00:00:00-05:51'}}),

    (datetime(1999, 12, 31),
     {'field_name': 'acquired',
      'type': 'DateRangeFilter',
      'config': {'gte': '1999-12-31T00:00:00Z'}}),

    ("2018-01-01",
     {'field_name': 'acquired',
      'type': 'DateRangeFilter',
      'config': {'gte': '2018-01-01T00:00:00Z'}}),
])
def test_date_range(dt, expected):
    fieldname = "acquired"
    arg = "gte"

    assert filters.date_range(fieldname, **{arg: dt}) == expected
