

## Commands

### Auth

Initialize with user name and password

```console
$ planet auth init
```

See API key that is being used for requests

```console
$ planet auth value
```

*NOTE: Right now you must init before you get help, until https://github.com/planetlabs/planet-client-python/issues/463 is resolved*

### Get Help

Most commands are pretty self-documenting, can use `--help` after any command to get usage info. And many will give you help
if you don't form a complete command.

```console
$ planet --help
$ planet
$ planet orders
$ planet orders list --help
```

### Orders

See recent orders you've made

```console
$ planet orders list
```

Print them more nicely
(both are options, jq is a bit more advanced, but prints a bit nicer and is more powerful)

```console
$ planet orders list | jq
$ planet orders list --pretty
```

Get the number of your recent orders. (-s collects objects into a single array)

```console
$ planet orders list | jq -s length
```

Get more info on a single order

```console
$ planet orders get 782b414e-4e34-4f31-86f4-5b757bd062d7
```

Download the order

```console
$ planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7
```

Download it to a different directory (relative to where the command is run)


```console
$ mkdir psscene
$ planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7 --directory psscene
```

Download to a directory specified absolutely (in this case to my desktop)

```console
$ planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7 --directory /Users/cholmes/Desktop/
```

Verify the checksum to make sure the file I got wasn't corrupted along the way (during download, etc)

```console
$ planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7 --checksum MD5
```

Create a new order request from a scene ID found in Explorer

```console
$ planet orders request --name "My First Order" --bundle analytic_sr_udm2 --id 20220605_124027_64_242b --item-type PSScene
```

Save to a file in the directory where the command was run

```console
$ planet orders request --name "My First Order" --bundle analytic_sr_udm2 --id 20220605_124027_64_242b --item-type PSScene > request-1.json
```

Make a new order with that request

```console
$ planet orders create request-1.json
```

Create the request and make a new order with it all in one call

```console
$ planet orders request --name "My First Order" --bundle analytic_sr_udm2 --id 20220605_124027_64_242b --item-type PSScene | planet orders create
```

Download - only works when the order is ready:

```console
$ planet orders download 65df4eb0-e416-4243-a4d2-38afcf382c30
```

Wait until the order is ready for download, then order it:
(Note that \ just tells the console to treat the next line as the same one - used here to be a bit easier to read)

```console
$ planet orders wait 65df4eb0-e416-4243-a4d2-38afcf382c30 \
&& planet orders download 65df4eb0-e416-4243-a4d2-38afcf382c30 
```

Create an order from a request, wait for it and download when ready 
(TODO: don't quite have this working yet)

```console
$ planet orders create request-1.json | jq -r '.id' | planet orders wait - | jq -r '.id' | planet orders download -
```


planet orders list

` --pretty or | jq`

```

Order and download a scene id found from explorer

```console
20220605_124027_64_242b
```

```console
$ 
```

```console
$ 
```

```console
$ 
```

As surface reflectance
Order and download the results of 3-4 of the first set of searches above
Order and download the above as STAC to:
Add to an existing STAC catalog with stactools
Browse resulting catalog with STAC Browser
Visualize results in Unfolded Studio
Do this with both surface reflectance data as well as clipped, composite, harmonized data.
Run search of geojson of 7 moderate-sized fields, download clipped, cloud-free imagery of each.
Do clip & composite of them
Clip, composite & harmonize
Clip, composite and NDVI
COG’s for each of the outputs


Run a search for planetscope data on a bounding box in Iowa
Run search for planetscope with cloud cover less than 20
Run search with permission filter to just be data that can be downloaded
Run search with just good sun angles
Run search for sentinel 2 images
Run search for landsat8 images
Run search for sentinel 1 images
Run search for all data from Planet & public satellites for the last 5 grow seasons in Iowa (April 15 - October 15th)
Get it into a shapefile for use by naive GIS people
Get stats of number of images captured by satellite, show in chart
Get stats of number of cloud free images by satellite
Run search with a geojson of 7 small to moderate sized fields, try out a few filters
Run search and turn results into STAC output, to:
Understand results with stac-terminal
Add to an existing stac catalog with stactools



Download 3 months of imagery over a small field stored in a shapefile, but only download the imagery that is 90% cloud free over the field.
https://hello.planet.com/code/benjamin/cloud_free_order can help us
Set up a subscription of planetscope data over a bound box in iowa
With cloud cover less than 25%
Set up a subscription clipped to the 7 small to moderate-sized fields
And then do it with harmonization & composites
Only use those that are 90% cloud-free over the actual AOI
Backfill a subscription for the previous 6 months
