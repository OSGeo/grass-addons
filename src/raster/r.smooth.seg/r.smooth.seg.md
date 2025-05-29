## DESCRIPTION

***r.smooth.seg*** generates a piece-wise smooth approximation of the
input raster map and a raster map of the discontinuities of the output
approximation.  
The discontinuities of the output approximation are preserved from being
smoothed. The values of the discontinuity map are close to one where the
output approximation is "homogeneous", where the output approximation
has discontinuities (edges) the values are close to zero.  
The module makes use of the *varseg* library which implements the
Mumford-Shah \[1\] variational model for image segmentation. The
Mumford-Shah variational model with curvature term \[2\] is also
implemented in the library. The curvature term prevents the
discontinuities from being shortened too much when the parameter alpha
is set to very high values, (this happens very rarely).  
An overview of the underlying theory with some applications can be found
in [\[3\]](https://doi.org/10.1016/j.isprsjprs.2012.02.005).  

For details on the numerical implementation see \[4\].

## NOTES

Remove any MASK before the execution of the module.  
  
Replace any NULL data (using *r.null*) with the map average value
(calculate it with *r.univar*).  
  
The segmentation depends on the parameters alpha and lambda:

- alpha controls how many discontinuities are allowed to exist.
- lambda controls the smoothness of the solution.
- It is not possible to select the values of the parameters in an
    automatic way. Test some different values to understand their
    influence on the results.  
    Try the following procedure:
  - run the module with both alpha and lambda set to 1.0
  - run the module with alpha set to 1.0 and different values for
        lambda  
        e.g., 0.01, 0.1, 1, 10, 100
  - run the module with lambda set to 1.0 and different values for
        alpha  
        e.g., 0.01, 0.1, 1, 10, 100
  - see how the segmentations change and select the values that
        produce the result that best fits your requirements.

The module computes the segmentation by means of an iterative
procedure.  
The module stops either when the number of iterations reaches the
maximum number of iterations \[mxi\] or when the maximum difference
between the solutions of two successive iterations is less than the
convergence tolerance \[tol\].  
To stop the iteration procedure, it is easier to act on the maximum
number of iterations parameter \[mxi\] than on the convergence tolerance
parameter \[tol\].  
The number of iterations needed to reach the convergence tolerance
increases for high values of the parameter lambda. The larger the total
number of pixels of the input raster map the larger the number of
iterations will be.  
  
The data type of the output raster maps is DOUBLE PRECISION.  
  
The module works on one raster map at a time, imagery groups are not
supported.  
  
To avoid to inappropriately re-sampled the input raster map, the
settings for the current region should be set so that:

- the resolution of the region matches the resolution of the input
    raster map;
- the boundaries of the region are lined up along the edges of the
    nearest cells in the input raster map.

The discontinuity thickness should be changed for test purposes only.  
  
The actual need to use the MSK model should be very rare, see \[4\]. Due
to a different implementation of the MSK model with respect to MS one,
the values of the parameters lambda and alpha in MSK have to be set
independently from the values used in MS.

## EXAMPLE

This example is based on the [North Carolina GRASS sample data
set](https://grass.osgeo.org/download/sample-data):

```code
# set the region to match the ortho_2001_t792_1m raster map:
g.region raster=ortho_2001_t792_1m -p

# select a smaller region:
g.region n=221725 s=220225 w=638350 e=639550 -p

# run r.smooth.seg:
r.smooth.seg in_g=ortho_2001_t792_1m out_u=u_OF out_z=z_OF lambda=10 alpha=200 mxi=250

# for a better visualization of the output raster map u_OF, set its color table to:
r.colors u_OF raster=ortho_2001_t792_1m

# compute the difference between the input raster map and the output raster map u_OF:
r.mapcalc "diff = abs(ortho_2001_t792_1m@PERMANENT - u_OF)"

# for a better visualization of the differences, compute the natural logarithm of the diff map:
r.mapcalc "log_diff = log(1 + diff)"

# and set its color table to the "differences" style:
r.colors log_diff color=differences

# for a better visualization of the output raster map u_OF, set its color table to:
r.colors z_OF color=bgyr

# run r.smooth.seg with different parameter values:
r.smooth.seg in_g=ortho_2001_t792_1m out_u=u1_OF out_z=z1_OF lambda=10 alpha=65 mxi=250
r.smooth.seg in_g=ortho_2001_t792_1m out_u=u2_OF out_z=z2_OF lambda=10 alpha=600 mxi=250
r.smooth.seg in_g=ortho_2001_t792_1m out_u=u3_OF out_z=z3_OF lambda=0.1 alpha=200 mxi=250
r.smooth.seg in_g=ortho_2001_t792_1m out_u=u4_OF out_z=z4_OF lambda=1 alpha=200 mxi=250

# visualize and compare the different results
```

## REFERENCES

- **\[1\]** D. Mumford and J. Shah. *Optimal Approximation by
    Piecewise Smooth Functions and Associated Variational Problems*.  
    Communications on Pure Applied Mathematics, 42(5):577-685, 1989.  
    DOI: 10.1002/cpa.3160420503
- **\[2\]** R. March and M. Dozio. *A variational method for the
    recovery of smooth boundaries*.  
    Image and Vision Computing, 15(9):705-712, 1997.  
    DOI: 10.1016/S0262-8856(97)00002-4
- **\[3\]** A. Vitti. *The Mumford-Shah variational model for image
    segmentation: An overview of the theory, implementation and use*.  
    ISPRS Journal of Photogrammetry and Remote Sensing, 69:50-64,
    2012.  
    DOI: 10.1016/j.isprsjprs.2012.02.005
- **\[4\]** A. Vitti. *Free discontinuity problems in image and signal
    segmentatiion*.  
    Ph.D. Thesis - University of Trento (Italy), 2008.  
    <https://www.ing.unitn.it/~vittia/misc/vitti_phd.pdf>

## SEE ALSO

*[i.smap](https://grass.osgeo.org/grass-stable/manuals/i.smap.html),
[i.zc](https://grass.osgeo.org/grass-stable/manuals/i.zc.html),
[r.clump](https://grass.osgeo.org/grass-stable/manuals/r.clump.html),
[r.mfilter](https://grass.osgeo.org/grass-stable/manuals/r.mfilter.html)*

## AUTHOR

Alfonso Vitti  
  Dept. Civil, Environmental and Mechanical Engineering  
  University of Trento - Italy  
  alfonso.vitti \[at\] unitn.it
