## DESCRIPTION

*r.threshold* finds optimal threshold for stream extraction.

## NOTES

The module finds a first tentative value of upslope area to be used as
input to extract the river network using *r.stream.extract* or
*r.watershed*. Real streams depend on many factors, such as rainfall,
infiltration rate, geology, climate etc. i.e. the same topography in
different parts of the world yields different real stream networks. This
approach provides a best guess about what makes sense when looking only
at the DEM.

## EXAMPLE

```sh
r.threshold acc=accumulation_map
```

## SEE ALSO

*[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html),
[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*

## AUTHOR

Margherita Di Leo (dileomargherita AT gmail DOT com)
