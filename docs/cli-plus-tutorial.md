## About

This document shows off a range of more advanced command-line workflows, making use of a wider range
of tools in the geospatial ecosystem. Some of them can be a pain to install,like GDAL/OGR, and 
several pop in and out of web tools, so these are kept out of the main tutorial section. 

## Tools used

* **[GDAL/OGR](https://gdal.org)** - We'll mostly use OGR, the vector tooling. 
Great for things like format conversion and basic simplification.
* **[Keplergl_cli](https://github.com/kylebarron/keplergl_cli#usage)** - Nice tool to call the
awesome kepler.gl library from the commandline. Useful for visualization of large amounts of 
geojson.
* **[GeoJSON.io](https://geojson.io/)** - Simple tool to do editing of geojson, useful for creating
AOI's. Integrates with github, but doesn't seem to work so well.
* **[Placemark.io](https://placemark.io)** - More advanced tool from the creator of GeoJSON, very
nice for creating AOI's and piping them in. 
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

Draw on geojson.io, copy the geojson as input to search
(pbpaste on mac. other options for windows and linux TODO: figure these out)

```console
pbpaste | planet data filter --geom -  | planet data search-quick SkySatCollect -
```

placemark

```console
curl -s https://api.placemark.io/api/v1/map/Dse5hjAzfrLyXDU9WiFn7/feature/11b80520-f672-11ec-98c0-5b51b58d2b56 | planet data filter --geom - | planet data search-quick SkySatCollect -
```

### Geometry Visualization


Copy output to clipboard.
 - paste to geojson.io
 - paste to placemark (not quite working at the moment)

```console
planet data filter --string-in strip_id 5743669 | planet data search-quick PSScene - | planet collect - | pbcopy
```

Show the latest 2500 collects for the state, across assets.
  - filter by provider, and instrument, gsd
  - show customizing the pop-up of properties

```console
curl -s https://raw.githubusercontent.com/ropensci/geojsonio/master/inst/examples/california.geojson | planet data filter --geom -  | planet data search-quick PSScene,Sentinel2L1C,Landsat8L1G,SkySatCollect,Sentinel1 --limit 2500 - | kepler
```

Draw in placemark and run a search in area you made, visualize output in Kepler.
 - filter by acquistion, show animation of time.

```console
curl -s https://api.placemark.io/api/v1/map/Dse5hjAzfrLyXDU9WiFn7/feature/11b80520-f672-11ec-98c0-5b51b58d2b56 | planet data filter --geom - | planet data search-quick SkySatCollect - | kepler
```



#### Large Dataset Visualization

Download lots of scenes (current version of CLI may crap out before it gets there, will take like 10 minutes)

```console
planet data filter | planet data search-quick SkySatCollect --limit 200000 > skysat-large.json
```

Put into a feature collection - often this will clean things up if other programs can't open it (but not always):

```console
planet data collect skysat-large.json > skysat-large-clean.json
```

Turn into geopackage (or shapefile) for a spatial index, and simplify (don't need so many points to visualize)
 - simplify .001 matches fidelity very close, mostly just removes points from lines. .008 drops a bit of info but generally good. .1 
   messes with things a lot, but still good for visualization.

```console
ogr2ogr skysat-large.gpkg skysat-large-clean.json -simplify .008
```

Can open `skysat-large.gpkg` with kepler, or other tools. 

Other simplification options for large datasets:
 
* Use QGIS, run 'convex hull' (Vector -> Geoprocessing -> Convex Hull). Good idea to convert to gpkg or shapefile before you open in qgis if large.

Draw on geojson.io, copy the geojson as input to search
(pbpaste on mac. other options for windows and linux TODO: figure these out)

```console
pbpaste | planet data filter --geom -  | planet data search-quick SkySatCollect -
```


Show the latest skysat image on github as a gist.

```console
planet data filter | planet data search-quick SkySatCollect - --sort 'acquired desc' --limit 1 \
| planet collect - | jq | gh gist create -f latest-skysat.geojson -w
```

Show all ps-scenes in a strip on github gist.
(may need to reload the page, for some reason it wasn't showing up immediately after open)

```console
planet data filter --string-in strip_id 5743640 | planet data search-quick PSScene - | gh gist create -f ps-search.geojson -w
```

TODO: get command that gets the latest strip id and uses that as input in one line. May need to update filter commands to take stdin?

```console
strip-id=`planet data filter | planet data search-quick PSScene - --limit 1 | jq -r '.properties.strip_id' | sed 's/\\[tn]//g'`
planet data filter --string-in strip_id $stripid | planet data search-quick PSScene -
```



```console

```

```console

```
```console

```

```console

```

