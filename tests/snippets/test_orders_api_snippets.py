# Copyright 2023 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""Example of creating and downloading multiple orders.

This is an example of submitting two orders, waiting for them to complete, and
downloading them. The orders each clip a set of images to a specific area of
interest (AOI), so they cannot be combined into one order.

[Planet Explorer](https://www.planet.com/explorer/) was used to define
the AOIs and get the image ids.
"""
import shutil
import os
from pathlib import Path
import planet
import pytest


@pytest.fixture
def create_request():
    '''Create an order request.'''

    # The Orders API will be asked to mask, or clip, results to
    # this area of interest.
    aoi = {
        "type":
        "Polygon",
        "coordinates": [[[-91.198465, 42.893071], [-91.121931, 42.893071],
                         [-91.121931, 42.946205], [-91.198465, 42.946205],
                         [-91.198465, 42.893071]]]
    }

    # In practice, you will use a Data API search to find items, but
    # for this example take them as given.
    items = ['20200925_161029_69_2223', '20200925_161027_48_2223']

    order = planet.order_request.build_request(
        name='iowa_order',
        products=[
            planet.order_request.product(item_ids=items,
                                         product_bundle='analytic_udm2',
                                         item_type='PSScene')
        ],
        tools=[planet.order_request.clip_tool(aoi=aoi)])

    return order


@pytest.mark.anyio
def create_succesful_order():
    '''Code snippet for create_order.'''
    order_details = {
        "_links": {
            "_self":
            "https://api.planet.com/compute/ops/orders/v2/785185e1-8d02-469d-840e-475ec9888a17",
            "results":
            [{
                "delivery": "success",
                "expires_at": "2023-07-12T22:58:47.877Z",
                "location":
                "https://api.planet.com/compute/ops/download/?token=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODkyMDI3MjcsInN1YiI6IkdIWSszZHZhQ2VnUWYza2grVzZjbDllQmkzOG85VWdQMjhXL2lNY0tTYUxjblk1ZGR5d2phS05Jb0V1SFpUL2dOd1ErMFBDUlRtVWpRNTRCcWo2Wld3PT0iLCJ0b2tlbl90eXBlIjoiZG93bmxvYWQtYXNzZXQtc3RhY2siLCJhb2kiOiIiLCJhc3NldHMiOlt7Iml0ZW1fdHlwZSI6IiIsImFzc2V0X3R5cGUiOiIiLCJpdGVtX2lkIjoiIn1dLCJ1cmwiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vY29tcHV0ZS1vcmRlcnMtbGl2ZS83ODUxODVlMS04ZDAyLTQ2OWQtODQwZS00NzVlYzk4ODhhMTcvY29tcG9zaXRlLnRpZj9YLUdvb2ctQWxnb3JpdGhtPUdPT0c0LVJTQS1TSEEyNTZcdTAwMjZYLUdvb2ctQ3JlZGVudGlhbD1jb21wdXRlLWdjcy1zdmNhY2MlNDBwbGFuZXQtY29tcHV0ZS1wcm9kLmlhbS5nc2VydmljZWFjY291bnQuY29tJTJGMjAyMzA3MTElMkZhdXRvJTJGc3RvcmFnZSUyRmdvb2c0X3JlcXVlc3RcdTAwMjZYLUdvb2ctRGF0ZT0yMDIzMDcxMVQyMjU4NDdaXHUwMDI2WC1Hb29nLUV4cGlyZXM9ODYzOTlcdTAwMjZYLUdvb2ctU2lnbmF0dXJlPTA1NmI0MzAxYWI3MzUxNjU3MDU2NDQ0NTllYmU4OTJjZjRkNWM3YzE1ODAzNWQ0NmQwYzM0ODIyNjk0NjIyNDE3NmUwYTI2NWI3MGM1NTFkNzI1ZGM3MDI4NTk2MmI1NDY2MzljZGFjYzFiZWFlNDU5NTdlNzBmNzgwZmI5ODM4NGYyODE1NWQ2ZjhlMjQyZmNjZTNhOWRjMTA5MTQ2NmI0YmI3MDJmMGUyMjM5NzdiMmYxMDI0MDEzMzI2MDJlY2FkZTM5OThmMzZhYjZiYWNkYmI0ZmMyMTkxZjBkYmNhMTJkNmEyYmFiMTE2ZGQwMmI1YzdkYjQ3YWRjY2YwOWU3Y2FhNmI2MzNmY2M4MDExZDg1ZTI5YzA1NzI5OWI3MjA4YzdhZjQ5YjU0YThkYjkzMTk2MDA0MDkzMzM2NGUzZTRhOGUyODIwMGMxODVhNzlkZjU4NjQ2NGMxMTJjYWZmYmZmMDk5MThiY2E0ZTgxNTllYjk2Y2Y1MTQ2M2YyOTdmM2FhMjQ4NGY3ZDIyNjE0YzBmMjU5MWI5OTM4YjAwNzRjNmI3NWRmZDg2MDVlODliNjM2Njg5YmVlYWE0ZjBiYTcwOGI5OTdhYmU1MWI2NGYzM2QzMTRhMzlmM2E2ZjlhZjNlMzgwZGU4YmVjYzRiMzIwZTNiOTI5YTVlYzgzXHUwMDI2WC1Hb29nLVNpZ25lZEhlYWRlcnM9aG9zdCIsInNvdXJjZSI6Ik9yZGVycyBTZXJ2aWNlIn0.YJ2N1KwRg8YmiW2E3HRlSEyVlVMRK8LIsbdQfCeXWP32e9sYQKOshGCGNRMblmyYqARAq5YWfWyk99h7igT38w",
                "name": "785185e1-8d02-469d-840e-475ec9888a17/composite.tif"
            },
             {
                 "delivery":
                 "success",
                 "expires_at":
                 "2023-07-12T22:58:47.880Z",
                 "location":
                 "https://api.planet.com/compute/ops/download/?token=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODkyMDI3MjcsInN1YiI6InNwdmpvY3NTd3Fsd2dMYTZUSndHdWlaM2NFNS9lbThta3pDNzdHRmNQamZkdDhSZHdOdEJFUU9YcjdUcDFMQWZKOFBvUTdQL2NkZVF4bXZpOW81TE1RPT0iLCJ0b2tlbl90eXBlIjoiZG93bmxvYWQtYXNzZXQtc3RhY2siLCJhb2kiOiIiLCJhc3NldHMiOlt7Iml0ZW1fdHlwZSI6IiIsImFzc2V0X3R5cGUiOiIiLCJpdGVtX2lkIjoiIn1dLCJ1cmwiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vY29tcHV0ZS1vcmRlcnMtbGl2ZS83ODUxODVlMS04ZDAyLTQ2OWQtODQwZS00NzVlYzk4ODhhMTcvY29tcG9zaXRlX21ldGFkYXRhLmpzb24_WC1Hb29nLUFsZ29yaXRobT1HT09HNC1SU0EtU0hBMjU2XHUwMDI2WC1Hb29nLUNyZWRlbnRpYWw9Y29tcHV0ZS1nY3Mtc3ZjYWNjJTQwcGxhbmV0LWNvbXB1dGUtcHJvZC5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSUyRjIwMjMwNzExJTJGYXV0byUyRnN0b3JhZ2UlMkZnb29nNF9yZXF1ZXN0XHUwMDI2WC1Hb29nLURhdGU9MjAyMzA3MTFUMjI1ODQ3Wlx1MDAyNlgtR29vZy1FeHBpcmVzPTg2Mzk5XHUwMDI2WC1Hb29nLVNpZ25hdHVyZT00YmFiMGZiZjlmMTFjYzlhMjZiNDc4MDJkMzE2NzI2YTcyMjEwYWNhYzQ5OGY5NTE2YjU2NmY0MjMxZTllNTMxN2NjODY0OWY1Mzc3ODhkMzQwMThjMDlhNDc3MWUzMjczYTQyM2NlMGUwYzE2MTAxNTU0Zjg2ZDJiMTE0ZWNlMGQ3Nzk4YzVlZjA3YjY5ZjQ0ZGIxZjY5NTU5ZGEzMmJjM2Q4MDg3MDFlZjRkNmY0ZTVmYTE2M2UyNmJiODMxYjgwMGJiMTE4ZDI1ZjYzZTVmNTQxM2ZkZTBkMjU1ZDFhMGNhMjI4YzI1N2MwZmU3MDEzMTdkNTNlZjdmYWE5NmU0ZGIwZjkwMjQyNjc5M2ZkOWFmNzMyYjNkM2Q1ZWU1YzMzYWUwYjAyM2U0NDhlNDE4ZDhmZjA1YTdmNmFiZGE0Mjc3YzE0OWFjMmY3ZmNkYzZkMzZhMDNjNTJkNmU5NWE4MTA5MjlmYjFiYzBkMmNmYmIyMjc4OTM2YTQ3MWRkMmEyM2U4YjczZmE2ZmVkNTc3ZWUyNDE5OGE5YWUwNTMxZGY4MmE0ZDMzMjU0YWI5NDRmNjcxMTNjMmZkMzNlYzE4MzNlNjRmZTRhMmJjZTc1N2RiMzVhOTE5NTU2NWIzMGQ4MjYxZGYyN2VmMWVmZTVjYTYzYzlhYzU1ODRiY2QzYVx1MDAyNlgtR29vZy1TaWduZWRIZWFkZXJzPWhvc3QiLCJzb3VyY2UiOiJPcmRlcnMgU2VydmljZSJ9.66549P4DkJOlQ1SjTljrZMQQyeANoPNdVQRF4OMOiq0atiU9RX7iL7p-Ji2m6AWy7EKfZQm4Hn5F-Mn4-gL19Q",
                 "name":
                 "785185e1-8d02-469d-840e-475ec9888a17/composite_metadata.json"
             },
             {
                 "delivery":
                 "success",
                 "expires_at":
                 "2023-07-12T22:58:47.883Z",
                 "location":
                 "https://api.planet.com/compute/ops/download/?token=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODkyMDI3MjcsInN1YiI6IkhvejBKZTZDWm5jd1FFcVFpMWpadzdGREV3UzNoeE94Q1AyT0syUGxsZUV1cGZ3RXNmMFZwWjNobHV2R3ZWdkdsOXc1T2RpR25jRWNRN1NnZ29jWDZBPT0iLCJ0b2tlbl90eXBlIjoiZG93bmxvYWQtYXNzZXQtc3RhY2siLCJhb2kiOiIiLCJhc3NldHMiOlt7Iml0ZW1fdHlwZSI6IiIsImFzc2V0X3R5cGUiOiIiLCJpdGVtX2lkIjoiIn1dLCJ1cmwiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vY29tcHV0ZS1vcmRlcnMtbGl2ZS83ODUxODVlMS04ZDAyLTQ2OWQtODQwZS00NzVlYzk4ODhhMTcvMjAyMzA2MDNfMTgwMzI2XzU4XzI0YzVfbWV0YWRhdGEuanNvbj9YLUdvb2ctQWxnb3JpdGhtPUdPT0c0LVJTQS1TSEEyNTZcdTAwMjZYLUdvb2ctQ3JlZGVudGlhbD1jb21wdXRlLWdjcy1zdmNhY2MlNDBwbGFuZXQtY29tcHV0ZS1wcm9kLmlhbS5nc2VydmljZWFjY291bnQuY29tJTJGMjAyMzA3MTElMkZhdXRvJTJGc3RvcmFnZSUyRmdvb2c0X3JlcXVlc3RcdTAwMjZYLUdvb2ctRGF0ZT0yMDIzMDcxMVQyMjU4NDdaXHUwMDI2WC1Hb29nLUV4cGlyZXM9ODYzOTlcdTAwMjZYLUdvb2ctU2lnbmF0dXJlPTg0M2Q0NzlmNjc4OGMyYTJhZjM4ODYyZDc3MzE2NDhhNGIzODliNjI3YWQzZWU0ZGQxM2I5YzlmZjhmMzI0N2UwYmIyNmEzMDYwMzdkNzk0MDBjNzdlOGYxZGVmMzgzOTkzYjQ1ZGQwNzU0OTU0ZmYxMTg3ZTdkOWFhOTRhYzczY2YyZjZlZTk4YTZiMzc1YTk0MDU4NGE3YzdmNDY2YzE3MDhmMmQ5ZGY1YjgyY2ZiNmYyYzQ5N2ZhNDUyNzVmYmFlYmE0OWU0NjNhNWQ0ODRhZjYyYzZhMjJjNjE1YTQ4OTA3YTI4NjliMDdiYjE4NWY5NzUxODZhZThiMzBkMDg4ZjNmMjkxODViNjI0YzFiYzFiNDBhZWQxZDE0NmMwYmVlYWZiY2MyYWZjMzNlZDE3ZGRlNTJiNWVhYzMyZGRlYzcxNmIwY2IyYWY3OGRjZDRhYjNjZDM4YWIzYjU5ODM2MTcyYTVkZTcxNTExYjVlMGJkYTBiNjA4MTU3OTgzYmRjNGU1M2E1ODM4ODg0ZDM1MTZlYThlZWVjZWY4NDUzNjkzMWVmODZhMWU4NjYzZDU2NmM3OWYzZGNkN2FlYTQ5NmQ0OGY4YjFmZGZhNjFkNGViZGJmYTQ0NDU3NWRkZDlmOTQ1YmIyMzNlZjk1NDkxMDhiZTA3MWZkZmRjMDI1XHUwMDI2WC1Hb29nLVNpZ25lZEhlYWRlcnM9aG9zdCIsInNvdXJjZSI6Ik9yZGVycyBTZXJ2aWNlIn0.xhUXOMazIqybHKfI-Fyx6PshfwpzZGGheVuwyc38NmM8yKMVIOwF0vQ1_iCH920sBYuhWmF-_wlsfL5AnqJ-dA",
                 "name":
                 "785185e1-8d02-469d-840e-475ec9888a17/20230603_180326_58_24c5_metadata.json"
             },
             {
                 "delivery":
                 "success",
                 "expires_at":
                 "2023-07-12T22:58:47.871Z",
                 "location":
                 "https://api.planet.com/compute/ops/download/?token=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODkyMDI3MjcsInN1YiI6IkJTNTZOcCt4Z3JHek12U2FoU0N0Q0QrWnQ1Q2VySUVTVnY2YXFoQm1PNmRucFpPRlcrNWVvMEFZZldVQmlHVzI1OUdBV3U3SEp5Znhtb05yRWVVUW9nPT0iLCJ0b2tlbl90eXBlIjoiZG93bmxvYWQtYXNzZXQtc3RhY2siLCJhb2kiOiIiLCJhc3NldHMiOlt7Iml0ZW1fdHlwZSI6IiIsImFzc2V0X3R5cGUiOiIiLCJpdGVtX2lkIjoiIn1dLCJ1cmwiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vY29tcHV0ZS1vcmRlcnMtbGl2ZS83ODUxODVlMS04ZDAyLTQ2OWQtODQwZS00NzVlYzk4ODhhMTcvMjAyMzA2MDNfMTgwMzI4XzkxXzI0YzVfbWV0YWRhdGEuanNvbj9YLUdvb2ctQWxnb3JpdGhtPUdPT0c0LVJTQS1TSEEyNTZcdTAwMjZYLUdvb2ctQ3JlZGVudGlhbD1jb21wdXRlLWdjcy1zdmNhY2MlNDBwbGFuZXQtY29tcHV0ZS1wcm9kLmlhbS5nc2VydmljZWFjY291bnQuY29tJTJGMjAyMzA3MTElMkZhdXRvJTJGc3RvcmFnZSUyRmdvb2c0X3JlcXVlc3RcdTAwMjZYLUdvb2ctRGF0ZT0yMDIzMDcxMVQyMjU4NDdaXHUwMDI2WC1Hb29nLUV4cGlyZXM9ODYzOTlcdTAwMjZYLUdvb2ctU2lnbmF0dXJlPTJiYzI2ODZkYjVmY2ZkZTUxNzRkNzVlY2M2N2RhOTExMmRmMzkzNDI5NmVjNTM4ODg3YTUwZDRjZWNmNGQ5NDJkMWE2MTIxMzllNGU1ZWZmMTRjYzk4NWNmZDk0MzczZjhiY2YyYTRmM2RhMzdkYzBmNzdkY2M5MjQ2MTZlZmIyMDc2ZGUxNjVlM2JhZDE1MTUxMDNkNjM1OGRhZDY4M2M5MDBiMmM4NzRjYmNhYTAyN2Y2MmMzOWQ0Y2Y0ZTBlOTZjNTdhOGY4M2RhN2JmMjhiZTNmNzc2ZWNhMzcxZWYwYjQyMTYyOGJhNDIxMGExZTg5Zjk2YTI3ZTUxNWNkNzJiMmYxM2MyMGU3NWE5MWRjZjlkNDVhMjM0NjhjNzAzY2Q1NzdjZjJiZTc3ZTNmOWVlMDkyY2RiY2FjOTMxYzRmZjlhODFmMDczOWYwNDQ2YzMyMWNjMDBiYzY2NDc4MzE5Zjg5YWJhNTg0ZDI2NjMwZWVlMGFjYTA4YmY2NzA1MmQ0MDFhYzdlMzA5Njc3ZjE0YWYzYzk3YTA1NjMzMDdlYjhjOGIxZGM3Njc3NTFjMWQ5M2MwOGQ5NzFmNWFlZjFkMDZiNjNkZjIxOTc3MmQ3NWQ2ZGZkNmRiNjJlYTMxZjA5MjQ4YzEwNWRlNWVhODhiNzExYThmM2U4NWRkMGM0XHUwMDI2WC1Hb29nLVNpZ25lZEhlYWRlcnM9aG9zdCIsInNvdXJjZSI6Ik9yZGVycyBTZXJ2aWNlIn0.rAjq4q87lEfqp0qzMdW668yYRqrqI8bNRLkKMsDr851-c9xWdcB0BQ89M8ythVIpxJKAlhjnseRo_C1bK6tfnA",
                 "name":
                 "785185e1-8d02-469d-840e-475ec9888a17/20230603_180328_91_24c5_metadata.json"
             },
             {
                 "delivery": "success",
                 "expires_at": "2023-07-12T22:58:47.874Z",
                 "location":
                 "https://api.planet.com/compute/ops/download/?token=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODkyMDI3MjcsInN1YiI6IisvMktSQXBuM0tiWjY4dDh1cEx5c2hvTzB1VlhPZ2UwamNNZFA0Mnc4V3JEaUN0azZjaDBXakIrTkVwdUZGdzAxWFpKZnNqQ1BjcUtudGF2YnFZc0R3PT0iLCJ0b2tlbl90eXBlIjoiZG93bmxvYWQtYXNzZXQtc3RhY2siLCJhb2kiOiIiLCJhc3NldHMiOlt7Iml0ZW1fdHlwZSI6IiIsImFzc2V0X3R5cGUiOiIiLCJpdGVtX2lkIjoiIn1dLCJ1cmwiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vY29tcHV0ZS1vcmRlcnMtbGl2ZS83ODUxODVlMS04ZDAyLTQ2OWQtODQwZS00NzVlYzk4ODhhMTcvbWFuaWZlc3QuanNvbj9YLUdvb2ctQWxnb3JpdGhtPUdPT0c0LVJTQS1TSEEyNTZcdTAwMjZYLUdvb2ctQ3JlZGVudGlhbD1jb21wdXRlLWdjcy1zdmNhY2MlNDBwbGFuZXQtY29tcHV0ZS1wcm9kLmlhbS5nc2VydmljZWFjY291bnQuY29tJTJGMjAyMzA3MTElMkZhdXRvJTJGc3RvcmFnZSUyRmdvb2c0X3JlcXVlc3RcdTAwMjZYLUdvb2ctRGF0ZT0yMDIzMDcxMVQyMjU4NDdaXHUwMDI2WC1Hb29nLUV4cGlyZXM9ODYzOTlcdTAwMjZYLUdvb2ctU2lnbmF0dXJlPTc3NDUzYjFlYzAxMTVhMWQyODEzNWM0ZGRjZGVjOWE3ZmJjMDM0N2YwZTAzMDFkMWM4ZTgyNmVlMzA1YzUxMmRkNjBiMTMyMmZiOTE2ZmI2MzM3ZWJjZjFiYTBiNzkzNzY5MTRkNjI1ODEyYjE3YmYwNzljOTM4NTcxOTQ1YmRkNmVkMzZiMDVkOGMzMzk1NDgxZTliNDY1MDg3NmJjMzQwM2Y0Y2EwZDgxYTkxYjQwYjQxZDI1ODBmYmRjZDgyNmEyZTU2Y2ZiNWQ0ZGU4NDg0MmE3N2FjMzI4MThkYzA5MjQ3ZDc3YjU4MDg5ZjU2Y2MxNmNjMDQxOTc5NzYzZjQ5ZDU0YTY5MDgwZTEzZTM3ZWY5ZWU5NmU5NTIzMThmMDI2YjIwOWY2YTI5M2UyOGIxNDAyYTk4YmJmMzZiZDQxZmM1NjI0OWI1ODFjZjVkM2ZlZjJlMzYxOGMxYjY0NTVhOTJlZmJlODMyOWYyMGI4OGFmNmU3Y2YyYmM5NTRhNmQyZmNiNzg1NDY3ZGFlM2QwNDM4ZjQ0YTQzYzg3MmRiOWU0NWIzM2ZhMWUzZGZjMWVlNWNmZTE5ODk0ODJiYjNmNzQxMDhkNzlhZmFlMGZiNDIyNDVkYWM0MjJjNWRhZDg1MGVmODkxYmFiNGNjZTk3YTEzOTZkNDM3M2RiZDY0XHUwMDI2WC1Hb29nLVNpZ25lZEhlYWRlcnM9aG9zdCIsInNvdXJjZSI6Ik9yZGVycyBTZXJ2aWNlIn0.yc1ZrJeMuaqmsCJiSOhe14h1DJi5eB6SKPnMcN_kFTEPVg2lJCaMZE0cX9I8aL9LrWAcPgO_1Ui6aEAROPUl3A",
                 "name": "785185e1-8d02-469d-840e-475ec9888a17/manifest.json"
             }]
        },
        "created_on":
        "2023-06-15T19:32:42.945Z",
        "error_hints": [],
        "id":
        "785185e1-8d02-469d-840e-475ec9888a17",
        "last_message":
        "Manifest delivery completed",
        "last_modified":
        "2023-06-15T19:38:13.677Z",
        "name":
        "Composite CA Strip Visual Short",
        "products": [{
            "item_ids": ["20230603_180326_58_24c5", "20230603_180328_91_24c5"],
            "item_type":
            "PSScene",
            "product_bundle":
            "visual"
        }],
        "state":
        "success",
        "tools": [{
            "composite": {}
        }]
    }
    return order_details


@pytest.mark.anyio
async def test_snippet_orders_create_order():
    '''Code snippet for create_order.'''
    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": ['20230508_155304_44_2480'],
            "item_type": "PSScene",
            "product_bundle": "analytic_udm2"
        }],
    }
    # --8<-- [start:create_order]
    async with planet.Session() as sess:
        client = sess.client('orders')
        order = await client.create_order(request=order_request)
    # --8<-- [end:create_order]
    assert len(order['id']) > 0
    return order


@pytest.mark.anyio
async def test_snippet_orders_get_order():
    '''Code snippet for get_order.'''
    order = await test_snippet_orders_create_order()
    order_id = order['id']
    # --8<-- [start:get_order]
    async with planet.Session() as sess:
        client = sess.client('orders')
        order = await client.get_order(order_id=order_id)
    # --8<-- [end:get_order]
    assert len(order['id']) > 0
    # TO DO: get order ID some other way


@pytest.mark.anyio
async def test_snippet_orders_cancel_order():
    '''Code snippet for cancel_order.'''
    order = await test_snippet_orders_create_order()
    order_id = order['id']
    # --8<-- [start:cancel_order]
    async with planet.Session() as sess:
        client = sess.client('orders')
        order = await client.cancel_order(order_id=order_id)
    # --8<-- [end:cancel_order]
    # TO DO: get order ID some other way
    assert order['state'] == 'cancelled'


@pytest.mark.anyio
async def test_snippets_cancel_multiple_orders():
    '''Code snippet for cancel_order.'''
    order1 = await test_snippet_orders_create_order()
    order2 = await test_snippet_orders_create_order()
    order_id1 = order1['id']
    order_id2 = order2['id']
    # --8<-- [start:cancel_orders]
    async with planet.Session() as sess:
        client = sess.client('orders')
        orders = await client.cancel_orders(order_ids=[order_id1, order_id2])
    # --8<-- [end:cancel_orders]
    assert orders['result']['succeeded']['count'] == 2


@pytest.mark.anyio
async def test_snippet_orders_aggregated_order_stats():
    '''Code snippet for aggregated_order_stats.'''
    # --8<-- [start:aggregated_order_stats]
    async with planet.Session() as sess:
        client = sess.client('orders')
        json_resp = await client.aggregated_order_stats()
    # --8<-- [start:aggregated_order_stats]
    assert 'organization' and 'user' in [key for key in json_resp.keys()]


@pytest.mark.anyio
async def test_snippet_orders_download_asset():
    '''Code snippet for download_asset.'''
    order = create_succesful_order()
    order_id = order['id']
    # --8<-- [start:download_asset]
    async with planet.Session() as sess:
        client = sess.client('orders')
        order = await client.get_order(order_id=order_id)
        info = order['_links']['results']
        # Find and download the data
        for i in info:
            # This works to download spesifically a composite.tif
            if 'composite.tif' in i['name']:
                location = i['location']
                filename = await client.download_asset(location=location)
                # --8<-- [end:download_asset]
                assert filename.exists()
                os.remove(filename)
            else:
                pass


@pytest.mark.anyio
async def test_snippet_orders_download_order_without_checksum():
    '''Code snippet for download_order without checksum.'''
    order = create_succesful_order()
    order_id = order['id']
    # --8<-- [start:download_order_without_checksum]
    async with planet.Session() as sess:
        client = sess.client('orders')
        filenames = await client.download_order(order_id=order_id)
    # --8<-- [end:download_order_without_checksum]
    assert all([filename.exists() for filename in filenames])
    shutil.rmtree(filenames[0].parent)


@pytest.mark.anyio
async def test_snippet_orders_download_order_with_checksum():
    '''Code snippet for download_order with checksum.'''
    order = create_succesful_order()
    order_id = order['id']
    # --8<-- [start:download_order_without_checksum]
    async with planet.Session() as sess:
        client = sess.client('orders')
        filenames = await client.download_order(order_id=order_id)
        client.validate_checksum(directory=Path(order_id), checksum="MD5")
    # --8<-- [end:download_order_without_checksum]
    assert all([filename.exists() for filename in filenames])
    shutil.rmtree(filenames[0].parent)


@pytest.mark.anyio
async def test_snippet_orders_wait():
    '''Code snippet for wait.'''
    order = create_succesful_order()
    order_id = order['id']
    # --8<-- [start:wait]
    async with planet.Session() as sess:
        client = sess.client('orders')
        state = await client.wait(order_id=order_id)

        # --8<-- [end:wait]
    assert state == 'success'


@pytest.mark.anyio
async def test_snippet_orders_list_orders():
    '''Code snippet for list_orders.'''
    # --8<-- [start:list_orders]
    async with planet.Session() as sess:
        client = sess.client('orders')
        order_descriptions = [order async for order in client.list_orders()]
    # --8<-- [start:list_orders]
    assert order_descriptions[0].keys() == {
        '_links',
        'created_on',
        'error_hints',
        'id',
        'last_message',
        'last_modified',
        'name',
        'products',
        'state'
    }
