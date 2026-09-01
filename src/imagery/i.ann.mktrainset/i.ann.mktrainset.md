## NAME

i.ann.mktrainset - Export moving window samples from an imagery group
and two rasters. This is designed to be used by i.ann.\* training
modules.

## KEYWORDS

imagery, ann, export

## DESCRIPTION

The *i.ann.mktrainset* module exports samples from a moving window
across the current computational region. For each window position, it
extracts all bands from a specified imagery group and two additional
rasters. For each unique clump (region) in the first raster, it creates
a set of masked GeoTIFF files:

-   A multiband GeoTIFF containing all group bands, masked by the unique
    clump.
-   A single-band GeoTIFF for the each unique clump with a unique class.

The output is organized into subdirectories for each window position and
clump.

## OPTIONS

-   **group** --- Imagery group name (required)
-   **raster1** --- First raster input (clump, required)
-   **raster2** --- Second raster input (value, required)
-   **out_dir** --- Output directory (required)
-   **win_width** --- Window width in cells (required)
-   **win_height** --- Window height in cells (required)

## NOTES

-   All output files are written in GeoTIFF format using the current
    region\'s projection and resolution.
-   Each clump within a window is masked and exported separately.
-   This module requires `rasterio` and `numpy` Python packages.

## EXAMPLES

    # Create the raster datasets for polygons ids and associated classes
    g.region vector=LanduseMap_Steinbeissen_2009_07@PERMANENT format=plain

    # Raster1 unique polygon ID
    v.to.rast --overwrite input=LanduseMap_Steinbeissen_2009_07@PERMANENT output=polyg_id use=attr attribute_column=OBJECTID memory=8000

    # Raster2 LULC class value
    v.to.rast --overwrite input=LanduseMap_Steinbeissen_2009_07@PERMANENT output=polyg_class use=attr attribute_column=landuse__1 memory=8000

    # Generate the training set
    i.ann.mktrainset --verbose group=090727_Steinbeissen_rad_geo_atm@PERMANENT raster1=polyg_id raster2=polyg_class output_directory=/home/user/RSDATA/Steinbeissen_lulc window_width=128 window_height=128

## SEE ALSO

-   [i.group](i.group.html)
-   [r.out.bin](r.out.bin.html)
-   [r.out.gdal](r.out.gdal.html)

## AUTHOR

The GRASS Development team, 2025
