## DESCRIPTION

*r.euro.ecosystem* defines colors and raster category labels for
[Ecosystem types of
Europe](https://www.eea.europa.eu/en/datahub/datahubitem-view/573ff9d5-6889-407f-b3fc-cfe3f9e23941).

The data can be downloaded at
[EEA](https://www.eea.europa.eu/en/datahub/datahubitem-view/573ff9d5-6889-407f-b3fc-cfe3f9e23941)
for level 1 (based on
[EUNIS](https://www.eea.europa.eu/en/datahub/datahubitem-view/ce3e4bf4-e929-404a-88c7-37f2c614fd1d%22)
habitat classification level 1) and level 2 (based on EUNIS habitat
classification level 2).

The dataset combines the Corine based MAES ecosystem classes with the
non-spatial EUNIS habitat classification for a better biological
characterization of ecosystems across Europe. As such it represents
probabilities of EUNIS habitat presence for each MAES ecosystem type.

Data definition rules have to be defined by flags **-1** or **-2**.

Raster data definition rules are donated by EEA.

## EXAMPLE

```sh
  # link to ecosystem raster data level 1
  r.external input="es_l1_100m.tif" output=es_l1_100m
  # define colors and raster category labels
  r.euro.ecosystem -1 input=es_l1_100m

  # link to ecosystem raster data level 2
  r.external input="es_l2_100m.tif" output=es_l2_100m
  # define colors and raster category labels
  r.euro.ecosystem -2 input=es_l2_100m
 
```

## SEE ALSO

*[r.colors](https://grass.osgeo.org/grass-stable/manuals/r.colors.html)
[r.category](https://grass.osgeo.org/grass-stable/manuals/r.category.html)*

## AUTHOR

Helmut Kudrnovsky
