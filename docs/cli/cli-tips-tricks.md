---
title: More CLI Tips & Tricks
---

## About

This document shows off a range of more advanced command-line workflows, making use of a wider range
of tools in the command-line & geospatial ecosystem. Some of them can be a pain to install, like
GDAL/OGR, and several pop in and out of web tools, so these are kept out of the main tutorial
section.

**WORK IN PROGRESS**: This document is still under construction, with a number of TODO’s remaining,
but we are publishing as there’s a lot of good information here.

## Tools used

* **[GDAL/OGR](https://gdal.org)** - We’ll mostly use OGR, the vector tooling.
Great for things like format conversion and basic simplification.
* **[Keplergl_cli](https://github.com/kylebarron/keplergl_cli#usage)** - Nice tool to call the
awesome kepler.gl library from the commandline. Useful for visualization of large amounts of
geojson.
* **[GeoJSON.io](https://geojson.io/)** - Simple tool to do editing of geojson, useful for creating
AOI’s. It integrates with github, but the ability to save a GeoJSON to github doesn't seem to work so well.
* **[Placemark.io](https://placemark.io)** - More advanced tool from the creator of GeoJSON.io, very
nice for creating AOI’s and piping them in, with lots of rich geometry editing features.
* **[MapShaper](https://github.com/mbloch/mapshaper)** - Tool to do interactive simplification of
GeoJSON, has a nice CLI.
* **[STACTools](https://github.com/stac-utils/stactools)** - CLI for working with STAC data. There
is also a [planet plugin](https://github.com/stactools-packages/planet) that may be useful in the
future.
* **[Github commandline](https://cli.github.com/)** - Nice CLI for quickly posting things to gists.

## Workflows

### Geometry Inputs

While the command-line can often be quicker than using a UI, one place that can be slower is
getting the geometry input for searching or clipping. Hand-editing GeoJSON is a huge pain, so most
people will open up a desktop tool like QGIS or ArcGIS Pro and save the file. But there are a few
tools that can get you back into the CLI workflow more quickly.

#### Use the Features API
Rather than using GeoJSON in the SDK, upload your GeoJSON to the [Features API](https://developers.planet.com/docs/apis/features/) and use references
across the system with the sdk.
References are used in the geometry block of our services in a GeoJSON blob like:
```json
"geometry":
    {
        "content": "pl:features/my/[collection-id]/[feature-id]",
        "type": "ref"
    }
```
Or as a string in a geometry option like `"pl:features/my/[collection-id]/[feature-id]"`


#### Draw with GeoJSON.io

One great tool for quickly drawing on a map and getting GeoJSON output is
[GeoJSON.io](https://geojson.io). You can draw and save the file, but an even faster workflow
is to use your operating system’s clipboard to command-line tools.

Just draw with the tools, then copy (with right click and 'copy' from the menu or 'ctrl c') the
JSON from the text box:

![Select on GeoJSON.io](https://user-images.githubusercontent.com/407017/179411184-fe3061aa-32ad-4bf7-bf6a-18c59bfdfff7.png)

On a mac you can use `pbpaste` to grab whatever is currently in your clipboard:

```console
pbpaste | planet data filter --geom -  | planet data search SkySatCollect --filter -
```

(TODO: Find alternatives for windows and linux)

#### Draw with Placemark

A really fantastic tool for working with GeoJSON is [Placemark](https://placemark.io). It is a
commercial tool that you’ll have to pay for, but it’s got a really nice feature that makes it very
compatible with command-line workflows. You can easily grab the URL of any individual GeoJSON
feature and stream it in as your geometry using `curl`:

![Stream from Placemark](https://user-images.githubusercontent.com/407017/179412209-2365d79a-9260-47e5-9b08-9bc5b84b6ddc.gif)

```console
curl -s https://api.placemark.io/api/v1/map/a0BWUEErqU9A1EDHZWHez/feature/278cd610-05ee-11ed-8fdd-15633e4f8f01 | \
planet data filter --geom - | jq
```

### Geometry Visualization

Looking at a big list of GeoJSON is a lot less useful then actually being able to see the footprints. This is often
done by saving the output files and opening with a desktop GIS program, but there are some nice alternatives that
let you pipe (`|`) the output more directly.

#### Copy GeoJSON to clipboard

One of the quicker routes to visualizing search output is to copy the output to your clipboard and paste into a
tool that will take GeoJSON and visualize it.

You can do this on GeoJSON.io:

(TODO: record example)

Or also on Placemark, which tends to perform a bit better (especially when you get above 1000 features).

(TODO: record example)

For both it’s recommended to pass the output through `planet collect` to get properly formatted GeoJSON:

```console
planet data filter --string-in strip_id 5743669 | planet data search PSScene --filter - | planet collect - | pbcopy
```

(TODO: Get pbcopy equivalents for windows and linux)

#### Post to Github as gist

Another easy option that is a bit more persistent is to post to Github using the
[`gh` cli tool](https://github.com/cli/cli). Specifically using the `gist create` command.

The following command will get the latest SkySat image captured, upload to github, and open
your browser to see it:

```console
planet data search SkySatCollect --sort 'acquired desc' --limit 1 \
| planet collect - | jq | gh gist create -f latest-skysat.geojson -w
```

Or you can show all ps-scenes in a strip on github gist.
(You may need to reload the page, for some reason it doesn't always showing up immediately after open)

```console
planet data filter --string-in strip_id 5743640 | planet data search PSScene --filter - \
| planet collect - | gh gist create -f ps-search.geojson -w
```


TODO: get a command that gets the latest strip id and uses that as input in one line. May need to update filter commands to take stdin?
This current command doesn't quite work.

```console
strip-id=`planet data search PSScene --limit 1 \
| jq -r '.properties.strip_id' | sed 's/\\[tn]//g'`
planet data filter --string-in strip_id $stripid | planet data search PSScene --filter -
```


#### Kepler.gl

One of the best tools to visualize large numbers of imagery footprints is a tool called [kepler.gl](https://kepler.gl/),
which has a really awesome command-line version which is perfect for working with Planet’s CLI. To get the CLI go to
[keplergl_cli](https://github.com/kylebarron/keplergl_cli) and follow the
[installation instructions](https://github.com/kylebarron/keplergl_cli#install). Be sure to get a Mapbox API key (from
the [access tokens](https://account.mapbox.com/access-tokens/) page) - just sign up for a free account if you don't have
one already. The kepler CLI won't work at all without getting one and setting it as the `MAPBOX_API_KEY` environment
variable.

Once it’s set up you can just pipe any search command directly to `kepler` (it usually does fine even without
`planet collect` to go from ndgeojson to geojson). For example:

```console
curl -s https://storage.googleapis.com/open-geodata/ch/vermont.json \
| planet data filter --geom -  \
| planet data search PSScene --filter - \
| kepler
```

(TODO: Add animated gif, showing some options)

Kepler really excels at larger amounts of data, so try it out with larger limits:

```console
curl -s https://storage.googleapis.com/open-geodata/ch/vermont.json \
| planet data filter --geom - \
| planet data search PSScene,Sentinel2L1C,Landsat8L1G,SkySatCollect,Sentinel1 \
--sort 'acquired desc' --limit 1500 --filter - \
| kepler
```

(show animated gif with 600 - lower amount so it takes less time to load).

And you can bring it all together using Placemark for input and Kepler for output:

(TODO: Figure out why this link isn't working... Maybe needs to be smaller?)

![Placemark and Kepler with Planet CLI](https://storage.googleapis.com/open-geodata/ch/planet-cli-pm-kepler.gif)

```console
curl -s https://api.placemark.io/api/v1/map/a0BWUEErqU9A1EDHZWHez/feature/91a07390-0652-11ed-8fdd-15633e4f8f01 \
| planet data filter --geom - \
| planet data search PSScene,Landsat8L1G,SkySatCollect,Sentinel1 --filter - | kepler
```

#### Large Dataset Visualization

Oftentimes it can be useful to visualize a large amount of data, to really get a sense of the
coverage and then do some filtering of the output. For this we recommend downloading the output
to disk. Getting 20,000 skysat collects will take at least a couple of minutes, and will be over
100 megabytes of GeoJSON on disk.

```console
planet data search SkySatCollect --limit 20000 > skysat-large.geojsons
```

Kepler can fairly easily handle 20,000 skysat footprints, try:

```console
kepler skysat-large.geojsons
```

Many GIS programs will open that geojson file by default. But if you have any trouble it can be useful to run it
through `planet collect`:

```console
planet data collect skysat-large.geojsons > skysat-large-clean.geojson
```
This turns it into a real GeoJSON, instead of a newline-delimited one, which more programs understand.

If you want to visualize even larger sets of footprints there’s a few things we recommend:

##### Convert to GeoPackage

GeoJSON is an amazing format for communicating online, but is less good with
really large amounts of data, so we recommend converting it to a format that
has a spatial index and isn't so large on disk. We recommend
[geopackage](https://www.geopackage.org/), but shapefile can work as well.

The `ogr2ogr` of [GDAL/OGR](https://gdal.org/) is a great tool for this. We
recommend using the [binaries](https://gdal.org/download.html#binaries), or if
you’re on a Mac then use [homebrew](https://brew.sh/) (run `brew install gdal`
after you get it set up). If you’re having trouble getting GDAL working well a
good backup can be to use docker and the
[osgeo/gdal](https://hub.docker.com/r/osgeo/gdal) package.

To convert to a geopackage run:

```console
ogr2ogr skysat-large.gpkg skysat-large.geojsons
```

The Python program `fio` from
[Fiona](https://fiona.readthedocs.io/en/stable/cli.html) and plugin commands
from the [fio-planet](https://fio-planet.readthedocs.io/en/latest/) package are
another option for converting and manipulating GeoJSON. Fiona and fio-planet
are easy to install alongside the Planet SDK and CLI. The Fiona way to convert
a sequence of GeoJSON features from a search to Geopackage is this:

```console
cat skysat-large.geojsons | fio load -f GPKG skysat-large.gpkg
```

##### Simplification with Fiona and fio-planet

There are a number of ways to [simplify areas of
interest](https://fio-planet.readthedocs.io/en/latest/topics/simplification/).
The one that best balances effectiveness with ease of use is the union, or
merger, of concave hulls.

```console
cat skysat-large.geojsons \
| fio map 'concave_hull g :ratio 0.4' --dump-parts \
| fio reduce 'unary_union c' \
| fio load -f GPKG skysat-large-simplified.gpkg
```

The `ratio` parameter describes the desired distance from the `convex_hull`
algorithm. A ratio of 1.0 produces hulls that are the same as convex hulls.
Smaller ratios preserve the character of concave features better.

##### Simplification with OGR

The other thing you’ll likely want to do to visualize large amounts of data is to simplify it
some. Many simplification tools call for a 'tolerance', often set in degrees. For SkySat some useful values are:

| tolerance | result                                                                                                          |
|-----------|-----------------------------------------------------------------------------------------------------------------|
| 0.001     | Mostly removes unnecessary points, visually looks pretty much the same, but much easier for programs to render. |
| 0.01      | Messes with the shape a bit, but the footprint generally looks the same, with a couple vertices off.            |
| 0.1       | Mashes the shape, often into a triangle, but still useful for understanding broad coverage.                     |

It’s worth experimenting with options between these as well. The more simplification the easier it is for programs to
render the results. `ogr2ogr` includes the ability to simplify any output:

```console
ogr2ogr skysat-large.gpkg skysat-large.json -simplify .008
```

Alternative - use convex hull. TODO: test this, write it up

```console
ogr2ogr skysat-convex.gpkg skysat.geojson ogr2ogr -sql "select st_convexhull(geometry) from skysat" -dialect sqlite
```

Other alternative for really big ones, centroid. GDAL should be able to do this, need to figure out the similar
sql.

#### Simplification with Mapshaper

Another great tool is [Mapshaper](https://github.com/mbloch/mapshaper), which excels at simplification. It offers a
web-based user interface to see the results of simplification, and also a command-line tool you can use if you
find a simplification percentage you’re happy with. After you get it
[installed](https://github.com/mbloch/mapshaper#installation) you can fire up the UI with:

```console
mapshaper-gui skysat-large.geojson
```

(TODO: Show animated gif of recording)

It’s easy to get a sense of how much simplification affects the shape. You can download the output from the web
interface, or you can also run the command-line program:

```console
mapshaper -i footprints.geojson -simplify 15% -o simplified.geojson
```

Once you find a simplification amount you’re happy with you can use it as a piped output.

```console
planet data search --limit 20 SkySatCollect - | planet collect - | mapshaper -i - -simplify 15% -o skysat-ms2.geojson
```

Mapshaper also has more simplification algorithms to try out, so we recommend diving into the
[CLI options](https://github.com/mbloch/mapshaper/wiki/Command-Reference).

#### Simplification with QGIS

Another good tool for simplification is QGIS.

TODO: Flesh out this section, add in command-line qgis_processing option.

Other simplification options for large datasets:

* Use QGIS, run 'convex hull' (Vector -> Geoprocessing -> Convex Hull). Good idea to convert to gpkg or shapefile before you open in qgis if large.

### Advanced jq

- do a limit 0 (unlimited) on a constrained search (geom and time range) with jq count to see how many scenes are in the area
 (note you can also do `stats`)

- get id by array number

```console
planet orders list | jq -rs '.[3] | "\(.id) \(.created_on) \(.name) \(.state)"'
```
(limit can get the most recent, but not a second or third)

* Use jq to show just orders that have a given item type, like just skysat.

```console
planet orders list | jq -rs '.[] | "\(.id) \(.created_on) \(.state) \(.products[0].item_type)"'
```

will show the item type https://gist.github.com/ipbastola/2c955d8bf2e96f9b1077b15f995bdae3 has ideas for contains, but haven't got it right yet

* use jq to get the id of the an order by it’s name

* get total number of items, add up each year of `stats`

### Simplify Geometries to 500 vertices

One of the limits of Planet’s API’s is that they demand geometries have less than 500 vertices. This section shows some
tools that can help you to do that simplification.

TODO: flesh these out.

#### Mapshaper

- simplify CLI
- simplify UI, download and use
- count number of resulting vertices
`ogrinfo -al simplify_test.geojson | grep POLYGON | sed 's/$/,/' | tr -d -c "," | wc`
But there should be a JQ way to do the same...

#### Placemark

- see count of vertices
- union together
- buffer and union
- simplify

