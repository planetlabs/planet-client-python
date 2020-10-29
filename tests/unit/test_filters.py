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


@pytest.mark.parametrize('predicate, expected', [
    (
        filters.string_filter('id', '20190625_070754_20_105c',
                              '20190324_150924_104b'),
        {
            'type': 'NotFilter',
            'config': {
                'field_name': 'id',
                'type': 'StringInFilter',
                'config': (
                    '20190625_070754_20_105c',
                    '20190324_150924_104b'
                )
            }
        }
    ),
    (
        filters.string_filter('ground_control', 'false'),
        {
            'type': 'NotFilter',
            'config': {
                'type': 'StringInFilter',
                'field_name': 'ground_control',
                'config': ('false',)
            }
        }
    )
])
def test_not_filter(predicate, expected):
    assert expected == filters.not_filter(predicate)


@pytest.mark.parametrize('filt, expected', [
    (
        filters.and_filter(
            filters.date_range('published',
                               lt='2019-08-29T13:20:37.776031Z'),
            filters.not_filter(
                filters.string_filter('id', '20190625_070754_20_105c',
                                      '20190324_150924_104b')
            )
        ),
        {
            'type': 'AndFilter',
            'config': (
                {
                    'field_name': 'published',
                    'type': 'DateRangeFilter',
                    'config': {
                        'lt': '2019-08-29T13:20:37.776031Z'
                    }
                },
                {
                    'type': 'NotFilter',
                    'config': {
                        'field_name': 'id',
                        'type': 'StringInFilter',
                        'config': (
                            '20190625_070754_20_105c',
                            '20190324_150924_104b'
                        )
                    }
                }
            )
        }
    )
])
def test_complex(filt, expected):
    assert expected == filt
