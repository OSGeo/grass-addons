## DESCRIPTION

*i.sentinel.mask* allows to automatically identify clouds and their
shadows in Sentinel-2 images. The algorithm works on reflectance values
(Bottom of Atmosphere Reflectance - BOA). Therefore, the atmospheric
correction has to be applied to all input bands (see
[i.sentinel.preproc](i.sentinel.preproc.md) or
[i.atcorr](i.atcorr.html)) (level 1C and 2A).

The following figures show the difference between the standard cloud
mask as provided in Sentinel-2 SAFE products and the cloud detection
results obtained with *i.sentinel.mask* (shadow detection not activated
in this example; see below for an example with cloud and shadow masks):

![Official cloud mask (yellow borders) as provided in Sentinel-2 SAFE products
 (example: Indonesia)](i_sentinel_mask_indonesia_esa_sen2cor.png)  
*Fig: Official cloud mask (yellow borders) as provided in Sentinel-2 SAFE
 products (example: Indonesia).*

![Cloud (yellow borders) and shadow (green borders) detection with i.sentinel.mask (example: Indonesia)](i_sentinel_mask_indonesia_grass_gis.png)  
*Fig: Cloud (yellow borders) and shadow (green borders) detection with
 i.sentinel.mask(example: Indonesia).*

The implemented procedure consists essentially of an algorithm based on
values thresholds, comparisons and calculations between bands which
leads to two different rough maps of clouds and shadows. These require
further improvements and elaborations (e.g. transformation from raster
to vector, cleaning geometries, removing small areas, checking topology,
etc.) carried out in the different steps of the procedure.

![Module General WorkFlow](i_sentinel_mask_GWF.png)  
*Fig: Module General WorkFlow.*

![Cloud detection procedure](i_sentinel_mask_CD.png)  
*Fig: Cloud detection procedure.*

![Shadow detection procedure](i_sentinel_mask_SD.png)  
*Fig: Shadow detection procedure.*

The algorithm has been developed starting from rules found in literature
(Parmes et. al 2017) and conveniently refined.

Regarding the detection of shadows, the algorithm has been developed to
identify only the shadows of clouds on the ground. Obviously, some
misclassifications can occur. Often shadows and water have in fact,
similar reflectance values which can lead to erroneous classification of
water bodies as shadows. Therefore, in order to increase the accuracy of
the final shadow mask, a control check is implemented. Clouds and
shadows are spatially intersected in order to remove misclassified
areas. This means that all those shadow geometries which do not
intersect a cloud geometry are removed.

!["Cleaning" procedure of the shadow mask](i_sentinel_mask_CS.png)  
*Fig: "Cleaning" procedure of the shadow mask*

All necessary input bands (blue, green, red, nir, nir8a, swir11, swir12)
must be imported in GRASS and specified one by one or using an input
text file. The text file has to be written following the syntax below:
*variable=your\_map*

```text
blue=your_blue_map
green=your_green_map
red=your_red_map
nir=your_nir_map
nir8a=your_nir8a_map
swir11=your_swir11_map
swir12=your_swir12_map
```

Tha variables names (blue, green, red, nir, nir8a, swir11, swir12) have
to be written precisely like in the example above (e.g. not Blue, nor
BLUE but blue), no spaces, empty lines or special characters are
permitted.

The final outputs are two different vector maps, one for clouds and one
for shadows.

The metadata file (MTD\_TL.xml or
S2A\_OPER\_MTD\_L1C\_TL\_MPS\_\_\*.xml) is required only if both masks
(cloud and shadow) are computed. The module retrieves from this file the
sun azimuth and zenith necessary for the shadow mask cleaning phase
*(see the scheme above)*

If flag **-s** is given all selected bands are rescaled using the
specified scale factor \[**scale\_fac**=*integer*\]. By default the
scale factor is set to 10000, the QUANTIFICATION\_VALUE from the
metadata of Sentinel-2 images.

The module takes the current region settings into accout. To ignore the
current region and set it from the whole image, the flag **-r** has to
be given.

The module allows to compute only the cloud mask or both cloud and
shadow masks. If flag **-c** is given, only the cloud procedure will be
performed. The computation of cloud mask is mandatory for shadow mask
creation. In fact cloud map is used during the cleaning phase of the
shadow mask in order to remove misclassifications.

If the **input\_file** is given, the **mtd\_file** or **metadata** can
also be specified in the this file.

## EXAMPLES

### North Carolina example

This example illustrates how to run *i.sentinel.mask* for a Sentinel-2A
image
(S2A\_MSIL1C\_20180713T155901\_N0206\_R097\_T17SPV\_20180713T211059.SAFE)
in the North Carolina location.  
Obviously, the image has been imported and atmospheric correction has
been performed before running *i.sentinel.mask* .

```sh
i.sentinel.mask -r input_file=path/input_cloud_mask.txt cloud_mask=cloud \
  shadow_mask=shadow cloud_threshold=25000 shadow_threshold=5000 mtd_file=path/MTD_TL.xml
```

The input text file:

```text
blue=T17SPV_20180315T160021_B02_cor
green=T17SPV_20180315T160021_B03_cor
red=T17SPV_20180315T160021_B04_cor
swir11=T17SPV_20180315T160021_B11_cor
nir=T17SPV_20180315T160021_B08_cor
swir12=T17SPV_20180315T160021_B12_cor
nir8a=T17SPV_20180315T160021_B8A_cor
```

Use **-r** to set the computational region to the maximum image extend.

![image-alt](i_sentinel_mask_ES.png)  
*Figure1 (left): Sentinel-2A Band 02 - Figure2 (right): Sentinel-2A Band
02 with computed cloud and shadow masks*

### Indonesia example

```sh
# EPSG 32749 (UTM 49S)
# Scene: S2A_MSIL2A_20200104T024111_N0213_R089_T49MGU_2020010
i.sentinel.download settings=credentials output=data uuid=f4d51134-c502-488b-8384-9eb0009c7545

# Mangkawuk area
g.region n=9870790 s=9855540 w=763950 e=786410 res=10 -p

# limit import to all bands with 10m and 20m resolution (excluding AOT, WVP, ... bands):
i.sentinel.import input=data -j pattern='_B((0[2348]_1)|(0[567]|8A|11|12)_2)0m'

# prepare input file list
g.list raster pattern="T49*"
g.list raster pattern="T49*" output=input_cloud_shadow_mask.csv

# edit input_cloud_shadow_mask.csv, content:
blue=T49MGU_20200104T024111_B02_10m
green=T49MGU_20200104T024111_B03_10m
red=T49MGU_20200104T024111_B04_10m
nir=T49MGU_20200104T024111_B08_10m
swir11=T49MGU_20200104T024111_B11_20m
swir12=T49MGU_20200104T024111_B12_20m
nir8a=T49MGU_20200104T024111_B8A_20m

# the default metadata json will be used
i.sentinel.mask -s input=input_cloud_shadow_mask.csv cloud_mask=cloud_mask \
  cloud_raster=cloud_raster shadow_mask=shadow_mask \
  cloud_threshold=50000 shadow_threshold=40000
```

The result is seen in the screenshot above.

## IMPORTANT NOTES

*i.sentinel.mask* works for Sentinel-2 images whose names follow both
the New Compact Naming Convention (e.g.
S2A\_MSIL1C\_20170527T102031\_N0205\_R065\_T32TMQ\_20170527T102301.SAFE)
and the Old format Naming Convention (e.g.
S2A\_OPER\_PRD\_MSIL1C\_PDMC\_20160930T155112\_R079\_V20160930T095022\_20160930T095944.SAFE).
Therefore, both the MTD\_TL.xml and
S2A\_OPER\_MTD\_L1C\_TL\_MPS\_\_\*.xml file can be provided as input for
the computation of shadow mask. Both files can be found in the *GRANULE*
folder of the downloaded \*.SAFE product.  
For further information about the naming convention see [ESA Sentinel
User
Guide](https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi/naming-convention).

## REFERENCE

Parmes, E.; Rauste, Y.; Molinier, M.; Andersson, K.; Seitsonen, L. 2017:
Automatic Cloud and Shadow Detection in Optical Satellite Imagery
Without Using Thermal Bands - Application to Suomi NPP VIIRS Images over
Fennoscandia. Remote Sens., 9, 806.
([DOI](https://www.mdpi.com/2072-4292/9/8/806))

## SEE ALSO

*[Overview of i.sentinel toolset](i.sentinel.md)*

*[i.sentinel.download](i.sentinel.download.md),
[i.sentinel.import](i.sentinel.import.md),
[i.sentinel.preproc](i.sentinel.preproc.md),
[r.import](https://grass.osgeo.org/grass-stable/manuals/r.import.html),
[r.external](https://grass.osgeo.org/grass-stable/manuals/r.external.html)*

## AUTHORS

Roberta Fagandini, GSoC 2018 student  
[Moritz Lennert](https://wiki.osgeo.org/wiki/User:Mlennert)  
[Roberto Marzocchi](https://wiki.osgeo.org/wiki/User:Robertomarzocchi)
