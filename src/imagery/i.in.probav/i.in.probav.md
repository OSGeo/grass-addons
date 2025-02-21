## DESCRIPTION

*i.in.probav* imports Proba-V NDVI data sets. After the import the
digital numbers (DN) are remapped to VEGETATION NDVI values and the NDVI
color table is applied. The imported DN map is removed after remapping.
It is also possible to change the scale and offset factor (default is
scale: 0.004, offset: -0.08 for Proba-V) and to improve the memory usage
(default is 300 MB).

Important for the Proba-V Data sets, is a user registration at [the VITO
portal](https://www.vito-eodata.be/PDF/portal/Application.html#Home)
necessary (Register Button in the Upper Right Corner).

## NOTES

The Proba-V files are delivered in NetCDF (Network Common Data Form)
format. It is required to have the GDAL libraries installed with NetCDF
support. Also to check the necessary scale and offset factor with
**gdalinfo**.

### Before Import

When working with Proba-V NDVI, it it necessary to fix the range of the
map because it exceeds the -180°..+180° range with entire world extent.
You can shift the map slightly into the right position using
[gdal\_translate](https://gdal.org/en/latest/programs/gdal_translate.html).
This example in [Global
datasets](https://grasswiki.osgeo.org/wiki/Global_datasets#ESA_Globcover_dataset)
may help you.

## EXAMPLE

```sh
# import of 300m NDVI
i.in.probav input=c_gls_NDVI300_201611010000_GLOBE_PROBAV_V1.0.1.nc \
            output=c_gls_NDVI300_201611010000_GLOBE_PROBAV_V1.0.1 memory=500
```

## SEE ALSO

*[i.in.spotvgt](https://grass.osgeo.org/grass-stable/manuals/i.in.spotvgt.html),
[r.in.gdal](https://grass.osgeo.org/grass-stable/manuals/r.in.gdal.html)*

## REFERENCES

- [VITO Product Distribution
    Portal](https://www.vito-eodata.be/PDF/portal/Application.html#Home)
- [PROBA-V
    FAQ](https://www.vito-eodata.be/PDF/image/faq_help/Faq.html)
- [VITO Collections
    help](https://www.vito-eodata.be/PDF/image/faq_help/Help.html#COLLECTION)

## AUTHOR

Jonas Strobel
