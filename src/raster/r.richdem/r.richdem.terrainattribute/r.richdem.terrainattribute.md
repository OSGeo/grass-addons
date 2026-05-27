## DESCRIPTION

***r.richdem.terrainattribute*** calculates first- and second-order terrain attributes from a digital elevation model. Available attributes are slope (in four unit systems), aspect, and three curvature measures.

### Slope

Slope is the magnitude of the terrain gradient---the rate of elevation change in the steepest downhill direction. It is computed using the Horn (1981) method, which uses a weighted average of finite differences over a 3×3 neighborhood to estimate the east--west and north--south gradient components. Slope is available in four unit systems:

- **slope_riserun** --- dimensionless rise/run ratio (tan of slope angle)
- **slope_percentage** --- rise/run expressed as a percentage
- **slope_degrees** --- angle in degrees from horizontal
- **slope_radians** --- angle in radians from horizontal

### Aspect

**aspect** is the compass direction of the steepest downhill gradient, measured in degrees clockwise from north (0--360°), using the Horn (1981) method.

### Curvature

Curvature describes the rate of change of slope and is useful for identifying ridges, valleys, and areas of flow convergence or divergence. Three curvature attributes are available, following Zevenbergen and Thorne (1987):

- **curvature** --- total (mean) curvature; positive values indicate convex surfaces, negative indicate concave surfaces.
- **planform_curvature** --- curvature of the contour line perpendicular to the slope direction; positive values indicate flow divergence, negative indicate convergence.
- **profile_curvature** --- curvature in the slope direction; positive values indicate slope acceleration (convex profile), negative indicate slope deceleration (concave profile).

### Z-axis scaling

The optional **zscale** parameter multiplies elevation values before computation. This is useful when vertical and horizontal units differ (e.g., elevation in feet, horizontal in meters: use zscale=0.3048). When horizontal units are geographic degrees and elevation is in meters, projecting to a metric coordinate system is preferable to using zscale.

## NOTES

Computations use a 3×3 moving window and assume a planar local coordinate system. For data in geographic (latitude/longitude) coordinates, the horizontal scale varies with latitude and slope results will be approximate. In such cases, project to an equal-area or conformal coordinate system before computing terrain attributes, or apply an appropriate **zscale**.

To compute slope and aspect simultaneously in GRASS, consider *[r.slope.aspect](https://grass.osgeo.org/grass-stable/manuals/r.slope.aspect.html)*. For more morphometric parameters computed over variable window sizes, see *[r.param.scale](https://grass.osgeo.org/grass-stable/manuals/r.param.scale.html)*.

## REQUIREMENTS

This module requires the [RichDEM](https://github.com/r-barnes/richdem) Python package, which is not a standard GRASS GIS dependency and must be installed separately:

```bash
pip install richdem
```

If `pip install richdem` fails (the package requires a C++ compiler), build from source:

```bash
git clone https://github.com/r-barnes/richdem.git
cd richdem/wrappers/pyrichdem
pip install -e .
```

Ensure that RichDEM is installed into the same Python environment used by GRASS GIS.

## EXAMPLES

Calculate slope in degrees:

```bash
r.richdem.terrainattribute input=dem output=slope attribute=slope_degrees
```

Calculate aspect:

```bash
r.richdem.terrainattribute input=dem output=aspect attribute=aspect
```

Calculate planform curvature:

```bash
r.richdem.terrainattribute input=dem output=planform_curv attribute=planform_curvature
```

Scale elevation in feet to match horizontal units in meters (zscale converts feet to meters):

```bash
r.richdem.terrainattribute input=dem_ft output=slope attribute=slope_degrees zscale=0.3048
```

## REFERENCES

- Horn, B.K.P. (1981). Hill shading and the reflectance map. *Proceedings of the IEEE* Vol 69(1), pp 14--47. DOI: [10.1109/PROC.1981.11918](https://doi.org/10.1109/PROC.1981.11918)
- Zevenbergen, L.W., Thorne, C.R. (1987). Quantitative analysis of land surface topography. *Earth Surface Processes and Landforms* Vol 12(1), pp 47--56. DOI: [10.1002/esp.3290120107](https://doi.org/10.1002/esp.3290120107)
- Barnes, R. (2016). RichDEM: Terrain Analysis Software. URL: <http://github.com/r-barnes/richdem>

## SEE ALSO

*[r.slope.aspect](https://grass.osgeo.org/grass-stable/manuals/r.slope.aspect.html), [r.param.scale](https://grass.osgeo.org/grass-stable/manuals/r.param.scale.html), [r.richdem.flowaccumulation](r.richdem.flowaccumulation.md)*

## AUTHORS

Richard Barnes (RichDEM library)

GRASS GIS bindings: Andrew D. Wickert, with assistance from Claude Sonnet 4.6
