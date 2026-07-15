## DESCRIPTION

The module *r.colors.out\_sld* exports the colors of a raster map into
the Styled Layer Description (SLD) format according to OGC standard.

For raster maps of type CELL also labels are exported. The export of
labels requires that the input map is entirely read and may thus take a
bit longer than the export of continuous color rules (ramp).

Only if the flag **n** is given, the NaN values are written into the
generated SLD file which leads e.g. in GeoServer to an error when using
such SLD.

Currently only SLD v1.0.0 is implemented.

## EXAMPLES

```sh
# Exporting a color ramp
r.colors.out_sld map=testmap style_name=Celsius
```

## SEE ALSO

[r.colors.out](https://grass.osgeo.org/grass-stable/manuals/r.colors.out.html)

## REFERENCES

<https://www.ogc.org/standard/sld>

## AUTHORS

Hamish Bowman  
Stefan Blumentrath, Norwegian Institute for Nature Research, Oslo,
Norway
