## DESCRIPTION

*r.width.funct* produces the Width Function of a basin. The Width
Function W(x) gives the number of the cells in a basin at a flow
distance x from the outlet (it is also referred as distance-area
function). It is important to underline the fact that the distance is
not the euclidean one, but it is measured along the flowpath towards the
outlet.

### Input

*Distance to outlet map:* Input map, required. It is obtained by
r.stream.distance (with the option: distance to outlet, flag -o).

*Output plot:* Path and name of the plot.

### Output

It provides the quantiles of the area - distance distribution and the
plot of the Width Function. In x axis is reported the distance and in y
axis is the area.

## EXAMPLE

North Carolina sample dataset example:

```sh
g.region raster=elevation -p

# Calculate flow direction
r.stream.extract elevation=elevation threshold=1000 \
direction=direction

# Create outlet point
echo "637304.924954,218617.100523" | v.in.ascii input=- sep=',' out=outlet

# Convert outlet point to raster
v.to.rast input=outlet type=point output=outlet use=cat

# Calculate distance to outlet map
r.stream.distance -o stream_rast=outlet \
direction=direction distance=dist2out

# Calculate width function
r.width.funct map=dist2out image=/tmp/my_basin
```

### Dependencies

  - Matplotlib

## SEE ALSO

*[r.stream.distance](r.stream.distance.md),
[r.basin](https://grass.osgeo.org/grass-stable/manuals/r.basin.html),*

## REFERENCES

  - *Rodriguez-Iturbe I., Rinaldo A. — Fractal River Basins, Chance and
    Self-Organization. Cambridge Press (2001)*
  - *In Italian: Di Leo M., Di Stefano M., Claps P., Sole A. —
    Caratterizzazione morfometrica del bacino idrografico in GRASS GIS
    (Morphometric characterization of the catchment in GRASS GIS
    environment), [Geomatics
    Workbooks](https://www.geolab.polimi.it/volume-9/), n. 9 (2010)*

## AUTHORS

Margherita Di Leo (grass-dev AT lists DOT osgeo DOT org), Massimo Di
Stefano, Francesco Di Stefano
