# Planet Labs CLI

The Planet Labs command line interface can be used to search and download Planet scenes.

### List Scene Types

    $ planet list-scene-types
    {
      "ortho": "https://api.planet.com/v0/scenes/ortho/"
    }
    

### Search

    $ planet search --where cloud_cover.estimated lt 1 --where image_statistics.snr gt 50
    
    $ cat aoi.geojson | planet search
    
    $ cat aoi.geojson | planet search --where cloud_cover.estimated lt 1 --where image_statistics.snr gt 50
  

### Metadata

    $ planet metadata 20150615_190229_0905
    
### Thumbnails

    $ planet thumbnails 20150615_190229_0905 --size sm --format jpg
    
    $ cat list-of-scene-ids.txt | planet thumbnails --size lg --format png

### Geotiffs

    $ planet download 20150615_190229_0905 --product analytic
    $ planet download 20150615_190229_0905 --product visual


### Chaining commands

    # Using Rasterio's CLI we can search Planet for images in the overlapping region
    $ rio bounds LC80260332015082LGN00_B2.TIF | planet search
    
    # or even within the same timeframe
    $ rio bounds LC80260332015082LGN00_B2.TIF | planet search --where acquired gt 2015-03-20 --where acquired lt 2015-03-25
    
    # or we can chain planet commands with itself
    cat aoi.geojson | planet search | jq -r ".features[].id" | planet thumbnails --size lg
    