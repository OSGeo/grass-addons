## DESCRIPTION

*r.object.spatialautocor* calculates global spatial autocorrelation of
the raster objects in the *object\_map* based on the values in the
*variable\_map*. The user can choose between Moran's I or Geary's G
indicator using the *method* parameter.

At this stage, neighborhood is simply defined by an adjancy matrix. The
user can choose whether to also accept diagonal neighborhood by setting
the *-d* flag.

## NOTES

The module depends on the addon
[r.neighborhoodmatrix](r.neighborhoodmatrix.md) which needs to be
installed.

## EXAMPLE

Calculate the spatial autocorrelation of altitude in the elevation map
using individual patches in the landclass96 (North Carolina sample
dataset) as objects:

```sh
g.region raster=elevation
r.clump landclass96 output=objects
r.object.spatialautocor ob=objects var=elevation method=moran
r.object.spatialautocor ob=objects var=elevation method=geary
```

## REFERENCES

Moran, P.A.P., 1950. Notes on Continuous Stochastic Phenomena.
Biometrika 37, 17-23. <https://dx.doi.org/10.2307%2F2332142>  
  
Geary, R.C., 1954. The Contiguity Ratio and Statistical Mapping. The
Incorporated Statistician 5, 115. <https://dx.doi.org/10.2307%2F2986645>

## SEE ALSO

[r.neighborhoodmatrix](r.neighborhoodmatrix.md)  

## AUTHOR

Moritz Lennert
