## DESCRIPTION

*i.image.bathymetry* is used to estimate Satellite-Derived Bathymetry
(SDB). Module estimates bathymetry over near-shore region using limited
reference depth points. The maximum depth can be estimated by the module
is depending up on many factors such as quality of the water, suspended
materials etc.,(Lyzenga et al., 2006, Kanno and Tanaka, 2012). Our
experiments with several multispectral optical images indicate that the
depth estimates are reliable for when water column is below 20 meter.  
  
Delineation of land and water area are based on combining the result of
NDVI and band ratio. NDVI has used to delineate water from land, band
ratio between green band and infrared band used to separate the
delineated water from clouds, ice, etc. Atmospheric and water
corrections applied according to the Lyzenga et al., 2006. Corrected
spectral bands will be used for weighted multiple regression to estimate
depth. R library *GWmodel* has been used to compute the Geographically
Weighted Regression used for depth estimation.

## NOTES

The input image must include deep water pixels (far away from the coast)
which are used to assist water surface and water column correction.if
there is no deep water pixels included in the satellite imagery,
atmospheric and water corrections are carried without using deep water
pixels. Sparse depth points extracted from hydrographic charts or depth
pints derived from LiDAR survey or derived from Sonar survey can be used
as reference depth for calibration. The calibration depth points
provided by the user are used to ditermine the Area of Interest,
therefore it is suggested to provide calibration depth points in order
to cover user's estimation region boundary. In addition, an optional
parameter is also available to provide a polygon vector file for user's
to ditermine the area to be estimated (see first example).  
  
The tide height at the time of reference depth collection and satellite
imagery capture should be normalized if it is not. An option is
available in the module to provide tide hieght at the tide of image
captured and the module will correct the reference depth accordingly.
This option asuumes that the reference depth given is corrected zero
tide height. The tide lower than zero can be added as negative value.  
  
The *GWmodel* adaptive GWR model is memory intensive and may not be used
to process large images. For large images, the estimation is carried out
by using non-adaptive GWR implemented in *r.gwr* module in GRASS GIS. R
\> 3.1 should be installed to run *GWmodel* in order to proccess
adaptive GWR model for better depth estimation. Default gaussian kernel
will be used to estimate geographically weighted regression
coefficients.The flag 'b' can be used to change the kernel function
gaussian to bi-square.  
  
## EXAMPLES

In *i.image.bathymetry* green band, red band, near-infrared band, band
for correction and calibration depth points are mandatory input.
Additional bands available in the visible wavelength can be used for
better depth estimation as optional input. Short Wave Infrared (SWIR)
band is suggested to use as "band\_for\_correction" if it is available
(for e.g. satellite images like Landsat-7, Landsat-8 and Sentinel-2).An
example of depth estimation using Sentinel-2 (MSI) image is shown below,
where depth value is stored in column named 'Z'  

```sh
i.image.bathymetry blue_band='B2' green_band='B3' red_band='B4'
nir_band='B8' band_for_correction='B11'
calibration_points='Calibration_points' calibration_column='Z'
depth_estimate='output' area_of_interest='AOI'
```

If SWIR band is not available near-infrared band can be used as
"band\_for\_correction" (for e.g. satellite images like RapidEye and
ALOS AVINIR-2). An example of depth estimation using RapidEye image is
shown below image is shown below, where depth value is stored in column
named 'value'.  

```sh
i.image.bathymetry blue_band='B1' green_band='B2' red_band='B3'
Additional_band1='B4' nir_band='B5' band_for_correction='B5'
calibration_points='Calibration_points'  calibration_column='value'
depth_estimate='output'
```

## REFERENCES

- Vinayaraj, P., Raghavan, V. and Masumoto, S. (2016) Satellite
    derived bathymetry using adaptive-geographically weighted regression
    model, Marine Geodesy, 39(6), pp.458-478
- Su, H., Liu, H., Lei, W., Philipi, M., Heyman, W., and Beck, A.,
    2013, Geographically Adaptive Inversion Model for Improving
    Bathymetric Retrieval from Multispectral satellite Imagery. IEEE
    Transaction on Geosciences and Remote Sensing, 52(1) : 465-476,
    Accessed January 2013, doi:10.1109/TGRS.2013.2241772.

## SEE ALSO

*[r.gwr](r.gwr.md),
[r.regression.multi](https://grass.osgeo.org/grass-stable/manuals/r.regression.multi.html)*

## AUTHORS

Vinayaraj Poliyapram (email:*vinay223333@gmail.com*), Luca Delucchi and
Venkatesh Raghavan
