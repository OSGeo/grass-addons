## DESCRIPTION

*r.hypso* produces the hypsometric and hypsographic curve related to a
digital elevation model and prints the percentiles.

## NOTES

The *hypsographic curve* gives the distribution of surfaces in different
altitude ranges. Each point on the function reports on the y-axis the
elevation and on the x-axis the portion of the basin surface placed
above such elevation value. The *hypsometric curve* uses adimensional
axes.

## Flags:

\-a: generates hypsometric curve

\-b: generates hyposographic curve

## EXAMPLE

```sh
r.hypso -b map=elevation image=/tmp/hypso
```

generates hypsographic curve, and

```sh
r.hypso -a map=elevation image=/tmp/hypso
```

generates hypsometric curve.

### Dependencies

  - Matplotlib

## SEE ALSO

*[r.basin](https://grass.osgeo.org/grass-stable/manuals/r.basin.html),*

## REFERENCES

*Rodriguez-Iturbe I., Rinaldo A. — Fractal River Basins, Chance and
Self-Organization. Cambridge Press (2001)*

*In Italian: Di Leo M., Di Stefano M., Claps P., Sole A. —
Caratterizzazione morfometrica del bacino idrografico in GRASS GIS
(Morphometric characterization of the catchment in GRASS GIS
environment), [Geomatics
Workbooks](https://www.geolab.polimi.it/volume-9/), n. 9 (2010)*

## AUTHORS

Margherita Di Leo (grass-dev AT lists DOT osgeo DOT org), Massimo Di
Stefano, Francesco Di Stefano
