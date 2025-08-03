## DESCRIPTION

*i.sentinel.preproc* allows to import Sentinel-2 images and perform
atmospheric and topographic correction.

*i.sentinel.preproc* is a module for the preprocessing of Sentinel-2
images (Level-1C Single Tile product) which wraps the import, the
atmospheric and the topographic correction using respectively
[i.sentinel.import](i.sentinel.import.md),
[i.atcorr](https://grass.osgeo.org/grass-stable/manuals/i.atcorr.html)
and
[i.topo.corr](https://grass.osgeo.org/grass-stable/manuals/i.topo.corr.html).  
It works both with Sentinel-2A and 2B images.  
The aim is to provide a simplified module which allows importing images,
which area downloaded using
[i.sentinel.download](i.sentinel.download.md) or any other sources, and
performing the atmospheric correction avoiding users to provide all the
required input parameters manually. In fact, regarding the atmospheric
correction performed with *i.atcorr* one of the most challenging steps,
especially for unexperienced users, is the compiling of the control file
with all the required parameters to parametrize the 6S (*Second
Simulation of Satellite Signal in the Solar Spectrum*) model on which
*i.atcorr* is based.

To run *i.atcorr*, users have to provide the so-called control file in
which all the parameters (geometrical conditions, date, time, longitude
and latitude of the center of the scene, atmospheric model, aerosol
model, visibility or Aerosol Optical Depth -AOD- value, mean elevation
target and bands number) have to be specified with precise syntax rules
and codes.  
*i.sentinel.preproc* retrieves as many parameters as possible from the
metadata file (e.g. Geometrical conditions, data and time and bands
number), longitude and latitude are automatically computed from the
computational region while others like the mean target elevation above
sea level from the input digital elevation model (DEM). Only a few
parameters have to be provided by users who can choose the proper option
from a drop-down menu thus avoiding to enter the corresponding code. In
any case, *i.sentinel.preproc* writes a temporary control file, changing
it according to the band number, following the syntax rules and codes of
*i.atcorr* and then it runs *i.atcorr* for all bands. Using the *c* flag
*i.sentinel.preproc* is able to perform also the topographic correction
using
[i.topo.corr](https://grass.osgeo.org/grass-stable/manuals/i.topo.corr.html)
creating the needed information as the illumination model based on the
elevation model provided by the user.

![image-alt](i_sentinel_preproc_GWF.png)  
*Fig: Module General WorkFlow*

When all bands have been processed by the integrated version of
*i.atcorr*, an histogram equalization grayscale color scheme is applied.

If the **-t** flag is set, a text file ready to be used as input for
[i.sentinel.mask](i.sentinel.mask) will be created. In this case a name
for the output text file has to be specified.

NOTE: as for *i.atcorr*, current region settings are ignored. The region
is temporary set to maximum image extent and restored at the end of the
process.

***Important***: *i.sentinel.preproc* requires all the bands of a
Sentinel-2 images. If the module is used only for the atmospheric
correction, all bands from \*\_B01 to \*\_B12 must be imported.  
Moreover, the original bands name has to be kept unchanged (e.g if the
original name is *T17SPV\_20180315T160021\_B02* the imported raster map
in the GIS DATABSE must be named *T17SPV\_20180315T160021\_B02*).

### Import

*i.sentinel.preproc* allows the import of all the bands of a Sentinel-2
image. The required input is the **.SAFE folder** downloaded using
*i.sentinel.download* or any other source (e.g. Copernicus Open Access
Hub). Note that in the case that spatial reference system of input data
differs from GRASS location, the input data are reprojected.  
The number of imported bands **can not** be reduced, all bands are
automatically imported by default.

***Important***: *i.sentinel.preproc* allows the import of one image at
a time because the input **.SAFE folder** is also used to automatically
identify the corresponding metadata file that is used during the
atmospheric correction.

The import can be skipped using the **-i** flag. Note that even if the
import is skipped the input **.SAFE folder** must be specified to
automatically retrieve the metadata file.

### Atmospheric correction

*i.sentinel.preproc* allows performing atmospheric correction of all
bands of a Sentinel-2 scene with a single process using *i.atcorr*.
Unlike *i.atcorr*, it writes the control file changing it according to
the band number. The only required inputs are:

- **input\_dir** = the \*.SAFE directory where the image and metadata
    file (MTD\_MSIL1C.xml or S2A\_OPER\_MTD\_SAFL1C\_PDMC\_\*.xml
    depending on naming convention) are stored,
- **elevation** = raster of a digital elevation model,
- **visibility or AOD value** = raster of a visibility map or an AOD
    value (*see AOD section*),
- **Atmospheric model** = to be choosen from the drop-down menu,
- **Aerosol model** = to be choosen from the drop-down menu,
- **suffix** = a suffix for the output maps name
- **rescale** = the output range of values for the corrected bands,
    for example: 0-255, 0-1, 1-10000 (default value 0-1).

The module writes the control file automatically starting from the input
above.

#### Control file

*i.atcorr* requires a control file to parametrize the 6S algorithm on
which it is based.

Below an example of the control file, taken from the *i.atcorr* manual
page, of a Sentinel-2A image:

```text
25                            - geometrical conditions = Sentinel-2A
5 4 19.737 -78.727 35.748     - month day hh.ddd longitude latitude ("hh.ddd" is in decimal hours GMT)
2                             - atmospheric model = midlatitude summer
1                             - aerosols model = continental
0                             - visibility [km] (aerosol model concentration)
0.07                          - AOD at 550nm
-0.124                        - mean target elevation above sea level [km]
-1000                         - sensor height (here, sensor on board a satellite)
167                           - sensor band = Sentinel2A Blue band B2
```

Using *i.sentinel.preproc* the only parameters from the list above that
users have to provide are: atmospheric model, aerosol model, visibility
or AOD value. The others are automatically retrieved from the metadata
file, input elevation map and bands.

1. **Geometrical conditions**

    The geometrical condition of the satellite are read from the
    metadata file and converted to the corresponding *i.atcorr* code, 25
    for Sentinel-2A mission and 26 for Sentinel-2B.

2. **Date, time, longitude and latitude**

    Date (month and day) and time are read from the metadata file. The
    date (with the format YYYY-MM-DDTHH:MM:SSZ) is converted in a
    standard format and only the month and the day are selected and
    added to the control file.

    Time is already in Greenwich Mean Time (GMT), as *i.atcorr*
    requires, and it's automatically converted to decimal hours.  
    Longitude and latitude are computed from the computational region
    and converted to WGS84 decimal coordinates.

3. **Atmospheric model**

    Only some options are available:

      - Automatic
      - No gaseous absorption
      - Tropical
      - Midlatitude summer
      - Midlatitude winter
      - Subarctic summer
      - Subarctic winter
      - Us standard 62

    Users can choose the proper option from a drop-down menu. The
    desired model is automatically converted to the corresponding code
    and added to the control file.

    ***Automatic** option*  
    The default option is *Automatic* which consists in the automatic
    identification of the proper atmospheric model for the input image.
    The *Automatic* option reads the latitude of the center of the
    computational region and uses it to choose between Midlatitude
    (15.00 \> lat \<= 45.00), Tropical (-15.00 \> lat \<= 15.00) and
    Subarctic (45.00 \> lat \<= 60.00) for Northern Hemisphere
    (obviously it also works for the Southern Hemisphere). Then, the
    month from the acquisition date is used to distinguish summer or
    winter in case of Midlatitude or Subarctic model. Once the proper
    atmospheric model is identified, it is converted to the
    corresponding code and added to the control file.  
    Note that this is a simplified and standardized method to identify
    the atmospheric model. Obviously, it is possible to choose other
    options from those available.

4. **Aerosol model**

    Also in this case, only some options are available and users have to
    select the desired one from the drop-down menu, then it is converted
    to the corresponding code and added to the control file.

      - no aerosols
      - continental model
      - maritime model
      - urban model
      - shettle model for background desert aerosol
      - biomass burning
      - stratospheric model

    No automatic procedure has been implemented in this case.

5. **Visibility or AOD**

    By default, *i.sentinel.preproc* uses the input visibility map to
    estimate a visibility value to be added in the control file. If no
    visibility map is available for the processed scene, it is possible
    to use an estimated Aerosol Optical Depth (AOD) value checking the
    **-a** flag.  
    If the **-a** flag is checked and a visibility map is provided, the
    visibility will be ignored and no mean visibility value will be
    computed and added to the control file. Whereas, if the **-a** flag
    isn't checked and an AOD value is provided it will be ignored and
    not added to the control file.

    In the same way, if the **-a** flag is checked and a visibility map
    is provided it will be excluded from atmospheric correction process.

    **AOD**

    The AOD value can be specified by users (e.g. `aod_value=0.07`) or
    automatically retrieved from an AERONET file to be given as input
    instead of the AOD value.  
    *i.sentinel.preproc* reads the AERONET file, identify the closest
    available date to the scene date and compute AOD at 550nm using the
    closest upper and lower wavelength to 550 (e.g. 500nm and 675nm) and
    applying the Angstrom coefficient.

    The type of AERONET file is a Combined file for All Points (Level
    1.5 or 2.0)  
    To download this kind of file:  

    1. Go to
        <https://aeronet.gsfc.nasa.gov/cgi-bin/webtool_opera_v2_inv>
    2. Choose the site you want to get data from
    3. Choose the data you want to get data for
    4. Tick the box near the bottom labelled as 'Combined file (all
        products without phase functions)'
    5. Choose either Level 1.5 or Level 2.0 data. Level 1.5 data is
        unscreened, so contains far more data meaning it is more likely
        for users to find data near your specified time
    6. Choose 'All Points' under Data Format
    7. Download the file
    8. Unzip (the file has a .dubovik extension)

    Then, giving this file as input (e.g.
    `aeronet_file=your_path/*.dubovik`), the AOD at 550nm will be
    automatically computed and added to the control file.

    NOTE: as in *i.atcorr* manual explained, if an AOD value is provided
    a value 0 for the visibility has to be entered with the AOD value in
    the following line. Obviously, *i.sentinel.preproc* takes into
    account this syntax rule and automatically adds a 0 value for
    visibility (or -1 if AOD=0) if an AOD value is provided (through
    both `aod_value` and `aeronet_file`).

6. **Mean target elevation above sea level**

    Mean target elevation above sea level is automatically estimated
    from the input digital elevation model. According to the rules for
    writing the contol file of *i.atcorr*, the mean elevation value is
    added as a negative value and converted in kilometers (e.g. if
    mean=121 in the control file it will be written in \[-km\], i.e.,
    -0.121).

7. **Sensor height**

    Since the sensor is on board a satellite, the sensor height is
    automatically set to -1000.

8. **Sensor band**

    The number of the band changes automatically according to the band
    that is processed at that moment. The module reads the name of the
    band and converts it into the corresponding code.

### Topographic correction

*i.sentinel.preproc* allows performing the topographic correction of all
bands of a Sentinel-2 scene with a single process using
[i.topo.corr](https://grass.osgeo.org/grass-stable/manuals/i.topo.corr.html).
*i.sentinel.preproc* calculate the zenit and azimuth angles using
[r.sunmask](https://grass.osgeo.org/grass-stable/manuals/r.sunmask.html),
after that it create the illumination model based on the elevation model
and apply it to all the bands of a Sentinel-2 scene

## EXAMPLE

The example illustrates how to run *i.sentinel.preproc* for a
Sentinel-2A image
(S2A\_MSIL1C\_20180315T160021\_N0206\_R097\_T17SPV\_20180315T194425.SAFE)
in the North Carolina location.  
The AERONET file has been downloaded from the *EPA-Res\_Triangle\_Pk*
station.

```sh
i.sentinel.preproc -a -t input_dir=/path/S2A_MSIL1C_20180315T160021_N0206_R097_T17SPV_20180315T194425.SAFE \
  elevation=elevation atmospheric_model=Automatic aerosol_model="Continental model" \
  aeronet_file=path/180301_180331_EPA-Res_Triangle_Pk.dubovik suffix=cor text_file=/path/input_cloud_mask.txt
```

Here is the control file automatically written for Band 02 of the input
scene

```text
25
5 4 19.74 -78.728 35.749
3                           -The Automatic option identified the Midlatitude Winter as the proper model for the scene
1
0                           -The visibility is set to 0 with AOD in the following line
0.18867992317               -AOD computed from the input AERONET file
-0.122
-1000
167
```

Here is the output text file ready to be used as input for
*i.sentinel.mask* (**-t** flag)

```text
blue=T17SPV_20180315T160021_B02_cor
green=T17SPV_20180315T160021_B03_cor
red=T17SPV_20180315T160021_B04_cor
swir11=T17SPV_20180315T160021_B11_cor
nir=T17SPV_20180315T160021_B08_cor
swir12=T17SPV_20180315T160021_B12_cor
nir8a=T17SPV_20180315T160021_B8A_cor
```

[![image-alt](i_sentinel_preproc_ES.png)](i_sentinel_preproc_ES.png)  
*Figure: Sentinel-2A Band 02*

## REQUIREMENTS

- [i.sentinel.import](i.sentinel.import.md)

## IMPORTANT NOTES

- *i.sentinel.preproc* integrates a simplyfied version of both modules
    (i.sentinel.import and i.atcorr), only some options are available.
    For instance, if it's necessary a strong customization (e.g.
    definition of your own atmospheric or aerosol model), please refer
    to i.atcorr.
- *i.sentinel.preproc* works with Sentinel-2 images whose names follow
    both the New Compact Naming Convention (e.g.
    S2A\_MSIL1C\_20170527T102031\_N0205\_R065\_T32TMQ\_20170527T102301.SAFE)
    and the Old Format Naming Convention (e.g.
    S2A\_OPER\_PRD\_MSIL1C\_PDMC\_20160930T155112\_R079\_V20160930T095022\_20160930T095944.SAFE).
    For further information about the naming convention see [ESA
    Sentinel User
    Guide](https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi/naming-convention).

## FOLLOW UP

- Implement download functionality avoiding dependencies
- Integrate topographic correction

## SEE ALSO

*[Overview of i.sentinel toolset](i.sentinel.md)*

*[i.sentinel.download](i.sentinel.download.md),
[i.sentinel.import](i.sentinel.import.md),
[i.sentinel.mask](i.sentinel.mask.md),
[i.atcorr](https://grass.osgeo.org/grass-stable/manuals/i.atcorr.html),
[r.import](https://grass.osgeo.org/grass-stable/manuals/r.import.html),
[r.external](https://grass.osgeo.org/grass-stable/manuals/r.external.html)*

## AUTHORS

Roberta Fagandini, GSoC 2018 student  
[Moritz Lennert](https://wiki.osgeo.org/wiki/User:Mlennert)  
[Roberto Marzocchi](https://wiki.osgeo.org/wiki/User:Robertomarzocchi)
