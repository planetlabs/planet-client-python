"""Fast, isolated tests of functions in planet.cli.data."""

import json

# from planet.cli.data import parse_item_types, parse_filter
#
#
# def test_filter_callback():
#     """Filter callback converts JSON to a dict."""
#     result = parse_filter(None, None, json.dumps(dict(filter="yes")))
#     assert result == {"filter": "yes"}
#
#
# def test_item_types_callback():
#     """Item types callback converts string to a list."""
#     result = parse_item_types(None, None, "oh,yeah")
#     assert result == ["oh", "yeah"]
