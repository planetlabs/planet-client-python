---
title: CLI for Async Processing API Tutorial
---

## Introduction
The `planet async-processing` command submits and tracks requests to the [Async Processing API](https://docs.planet.com/develop/apis/async-processing/). The API runs large Process API requests in the background. Outputs may be up to 10000 pixels in each dimension. Results go to your S3 or GCS bucket, not back to the CLI.

The API is served from `services.sentinel-hub.com`. It needs an OAuth2 login. Planet API keys do not work.

```sh
planet auth login
```

For automated jobs, log in with an M2M client:

```sh
planet auth login --auth-client-id <client-id> --auth-client-secret <client-secret>
```

## Core Workflow

### Write an Evalscript
An evalscript tells the service how to turn input bands into output pixels. Save this NDVI script as `ndvi.js`:

```js
//VERSION=3
function setup() {
  return {
    input: ["B04", "B08"],
    output: { bands: 1, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(s) {
  return [(s.B08 - s.B04) / (s.B08 + s.B04)];
}
```

### Generate a Request
`planet async-processing request` builds the request JSON. It sends nothing.

```sh
planet async-processing request \
    --collection sentinel-2-l2a \
    --bbox 12.44,41.87,12.54,41.93 \
    --time-from 2024-06-01T00:00:00Z \
    --time-to 2024-06-30T23:59:59Z \
    --max-cloud-coverage 20 \
    --evalscript ndvi.js \
    --width 2500 --height 2500 \
    --delivery s3://my-bucket/ndvi \
    --iam-role-arn arn:aws:iam::123456789012:role/planet \
    > request.json
```

Give the area as `--bbox`, `--geometry` or both. Coordinates are WGS84 longitude/latitude unless `--crs` says otherwise. Give the size as `--width`/`--height` in pixels, or `--resx`/`--resy` in CRS units.

`--geometry` accepts a GeoJSON geometry, Feature or FeatureCollection. It may be a string, a file, or `-` for stdin.

Each `--response IDENTIFIER:FORMAT` adds an output file. The identifier must match an output `id` in the evalscript's `setup()`, or be `userdata`. The default is `default:image/tiff`.

### Delivery
Results are written to `<prefix>/<REQUEST_ID>/`. To choose a different layout, use `<REQUEST_ID>` and `<OUTPUT>` placeholders in the URL:

```sh
--delivery 's3://my-bucket/ndvi/<REQUEST_ID>/<OUTPUT>'
```

S3 accepts an IAM role (recommended) or an access key pair:

```sh
--delivery s3://my-bucket/ndvi --iam-role-arn arn:aws:iam::123456789012:role/planet
--delivery s3://my-bucket/ndvi --aws-access-key-id AKIA... --aws-secret-access-key ...
```

Add `--aws-region` if the bucket is in a different region from the deployment.

GCS needs a service account key file. The CLI base64-encodes it for you:

```sh
--delivery gs://my-bucket/ndvi --gcs-credentials key.json
```

See the [API documentation](https://docs.planet.com/develop/apis/async-processing/) for the bucket permissions the service needs.

### Stored Evalscripts
To use an evalscript kept in your bucket, pass `--evalscript-url` instead of `--evalscript`. It uses the same credential options as `--delivery`:

```sh
--evalscript-url s3://my-bucket/scripts/ndvi.js
```

### Submit
```sh
planet async-processing create request.json
```

```json
{"id": "7d9a1c2e-0000-4000-8000-000000000000", "status": "RUNNING"}
```

`create` also reads a JSON string, or `-` for stdin. Generate and submit in one step:

```sh
planet async-processing request ... | planet async-processing create -
```

The API rejects invalid requests here. It also rejects a request when you have reached your concurrent request limit.

### Track
`get` shows the status of a running request:

```sh
planet async-processing get 7d9a1c2e-0000-4000-8000-000000000000
```

`wait` polls until the request stops running:

```sh
planet async-processing wait 7d9a1c2e-0000-4000-8000-000000000000
```

The API reports only running requests. When a request finishes, successfully or not, it disappears. `get` then fails with a not-running message and `wait` exits 0. An unknown ID behaves the same way.

A finished request does not always mean success. Check the delivery bucket. Results are in `<prefix>/<REQUEST_ID>/`. Failures write `error.json`. The service also stores a copy of the request there, with processing cost added after the run.

Submit, wait, and list the results:

```sh
id=$(planet async-processing create request.json | jq -r .id)
planet async-processing wait "$id"
aws s3 ls "s3://my-bucket/ndvi/$id/"
```

## Deployments
Input data must be hosted on the deployment the request goes to. The default is `aws-eu-central-1`. Use `--deployment` for others:

```sh
planet async-processing --deployment aws-us-west-2 create request.json
```

## Python
The same operations are available in the SDK:

```python
from planet import Planet, async_processing_request as apr

pl = Planet()
request = apr.build_request(
    input=apr.process_input(
        data=[apr.data_source('sentinel-2-l2a',
                              time_from='2024-06-01T00:00:00Z',
                              time_to='2024-06-30T23:59:59Z')],
        bbox=[12.44, 41.87, 12.54, 41.93]),
    output=apr.process_output(
        delivery=apr.s3_bucket('s3://my-bucket/ndvi',
                               iam_role_arn='arn:aws:iam::123456789012:role/planet'),
        width=2500,
        height=2500,
        responses=[apr.response('default', 'image/tiff')]),
    evalscript=open('ndvi.js').read())

req = pl.async_processing.create_request(request)
pl.async_processing.wait(req['id'])
```

Use `planet.AsyncProcessingClient` for the async interface, and pass `base_url` to select a deployment.
