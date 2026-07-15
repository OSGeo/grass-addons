## DESCRIPTION

**r.cell.area is deprecated.** Use the built-in `area()` function in
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)
instead (available since GRASS 7.4). It provides an ellipsoidal
cell-area calculation and requires no extra module.

*r.cell.area* computes the area of each raster cell in the current
computational region and writes the result to a new raster map. It is
now a thin wrapper around the `area()` function in *r.mapcalc* and emits
a deprecation warning on every run.

## NOTES

The `area()` function in *r.mapcalc* returns cell area in square metres
using an ellipsoidal model. Multiply by a constant to obtain other units:

| r.cell.area units | Equivalent r.mapcalc expression                |
|-------------------|------------------------------------------------|
| `m2`              | `r.mapcalc "output = area()"`                  |
| `km2`             | `r.mapcalc "output = area() * 1e-6"`           |
| `ha`              | `r.mapcalc "output = area() * 1e-4"`           |
| `acres`           | `r.mapcalc "output = area() / 4046.8564224"`   |
| `mi2`             | `r.mapcalc "output = area() / 2589988.110336"` |

## EXAMPLES

Compute cell area in square metres (recommended, no module needed):

```bash
r.mapcalc "cell_area_m2 = area()"
```

Compute cell area in hectares:

```bash
r.mapcalc "cell_area_ha = area() * 1e-4"
```

Using r.cell.area (deprecated, emits a warning):

```bash
r.cell.area output=cell_area units=ha
```

## SEE ALSO

*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)*

## AUTHOR

Andrew D. Wickert
