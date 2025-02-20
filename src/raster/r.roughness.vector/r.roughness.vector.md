## DESCRIPTION

In this script surface roughness is taken as the dispersion of vectors
normal to surface areas (pixels). Normal vectors are defined by slope
and aspect.

This script will create several temporary maps, for the directional
cosines in each direction (x,y,z), for the sum of these cosines and
vector strength.

The options *compass*, *colatitude*, *xcos*, *ycosm* and *zcos* are
created as temporary files each time the script is run. If the user
wants to create several map (with different window sizes, for instance),
it is recommended to create those maps with *r.mapcalc* and use them as
input:

```sh
  r.mapcalc compass = "if(aspect==0,0,if(aspect < 90, 90-aspect, 360+90-aspect))"
  r.mapcalc colatitude = "90 - slope"
  r.mapcalc xcos = "sin(colatitude)*cos(compass)"
  r.mapcalc ycos = "sin(colatitude)*sin(compass)"
  r.mapcalc zcos = "cos(colatitude)"
 
```

If the user does not specify the output maps names, they will be set to

```sh
INPUT_MAP_vector_strength_NxN
```

and

```sh
  INPUT_MAP_fisher_K_NxN
```

where N is the window size.

## EXAMPLE

```sh
  # calculate roughness factor by search window = 5
  r.roughness.vector elevation=DEM slope=slope aspect=aspect window=5
```

## SEE ALSO

*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.slope.aspect](https://grass.osgeo.org/grass-stable/manuals/r.slope.aspect.html)*

## REFERENCES

Hobson, R.D., 1972. Surface roughness in topography: quantitative
approach. In: Chorley, R.J. (ed). *Spatial analysis in geomorphology*.
Methuer, London, p.225-245.  
  
McKean, J. & Roering, J., 2004. Objective landslide detection and
surface morphology mapping using high-resolution airborne laser
altimetry. *Geomorphology*, 57:331-351.
<https://doi.org/10.1016/S0169-555X(03)00164-8>.  
  
Grohmann, C.H., Smith, M.J. & Riccomini, C., 2011. Multiscale Analysis
of Topographic Surface Roughness in the Midland Valley, Scotland.
*Geoscience and Remote Sensing, IEEE Transactions on*, 49:1200-1213.
<https://doi.org/10.1109/TGRS.2010.2053546>

## AUTHORS

Carlos Henrique Grohmann - Institute of Energy and Environment,
University of São Paulo, Brazil. (<http://carlosgrohmann.com>)  
Helmut Kudrnovsky
