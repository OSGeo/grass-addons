## DESCRIPTION

The *i.sentinel.import* module allows importing Copernicus Sentinel
products downloaded by the
*[i.sentinel.download](i.sentinel.download.md)* module.

By default *i.sentinel.import* imports all Sentinel scene files found in
the **input** directory. The number of scene files can be optionally
reduced by the **pattern\_file** option. In this option, a regular
expression for filtering the file names should be given, e.g.
"MSIL2A.\*T32VNR\_2019" for importing only level 2A products for tile
T32VNR from 2019.

By default *i.sentinel.import* imports the full scene. Optionally, the
import can be reduced to the computational region extent with
**extent=region**.

Note that in the case that spatial reference system of input data
differs from GRASS GIS location, the input data need to be reprojected
with
*[r.import](https://grass.osgeo.org/grass-stable/manuals/r.import.html)*.
To speed up this process, a higher than default value can be specified
for the **memory** option.

In order to ignore insignificant mismatch of the spatial reference
systems, the projection check can be suppressed with the **-o** flag.

Optionally input data can be linked by
*[r.external](https://grass.osgeo.org/grass-stable/manuals/r.external.html)*
when **-l** is given. Note that linking data requires that Sentinel
input data and GRASS location have the same spatial reference system
(e.g., the same UTM zone).

The number of imported Sentinel bands can be optionally reduced by the
**pattern** option. Below an overview of the Sentinel-2 MSI band spatial
resolutions:

| Spatial resolution \[m\] | S2 Bands                     |
| ------------------------ | ---------------------------- |
| 10                       | B02, B03, B04, B08           |
| 20                       | B05, B06, B07, B8A, B11, B12 |
| 60                       | B01, B09, B10                |

Level 2A (L2A) products for Sentinel-2 come with a scene classification
(SCL layer) at 20m and 60m resolution, that e.g. can be used for masking
clouds and snow and is also imported by default.

For each imported band both scene and band specific metadata on
geometric conditions as well as quality indicators are written into the
map history
(*[r.support](https://grass.osgeo.org/grass-stable/manuals/r.support.html)*).
In addition, the scene name is stored as *source1* and the imported or
linked file name as *source2*. Also, sensing time is written into the
timestamp of the map. After import, the metadata can be retrieved with
*r.info -e* as shown below.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td>SATELLITE=S2B<br />
CLOUDY_PIXEL_PERCENTAGE=1.250696<br />
DEGRADED_MSI_DATA_PERCENTAGE=0<br />
NODATA_PIXEL_PERCENTAGE=58.089572<br />
SATURATED_DEFECTIVE_PIXEL_PERCENTAGE=0.000000<br />
DARK_FEATURES_PERCENTAGE=4.668012<br />
CLOUD_SHADOW_PERCENTAGE=0.572569<br />
VEGETATION_PERCENTAGE=45.350337<br />
NOT_VEGETATED_PERCENTAGE=1.179313<br />
WATER_PERCENTAGE=44.793952<br />
UNCLASSIFIED_PERCENTAGE=2.184867<br />
MEDIUM_PROBA_CLOUDS_PERCENTAGE=0.620685<br />
HIGH_PROBA_CLOUDS_PERCENTAGE=0.570162<br />
THIN_CIRRUS_PERCENTAGE=0.059849<br />
SNOW_ICE_PERCENTAGE=0.000253<br />
RADIATIVE_TRANSFER_ACCURACY=0.0<br />
WATER_VAPOUR_RETRIEVAL_ACCURACY=0.0<br />
AOT_RETRIEVAL_ACCURACY=0.0<br />
MEAN_SUN_ZENITH_GRID_ANGLE=63.9790718336484<br />
MEAN_SUN_AZIMUTH_GRID_ANGLE=180.4378695652174<br />
MEAN_SUN_ZENITH_ANGLE=63.9790721741866<br />
MEAN_SUN_AZIMUTH_ANGLE=180.437882291128<br />
ZENITH_ANGLE_5=9.9540335513936<br />
AZIMUTH_ANGLE_5=295.354861828927<br />
</td>
</tr>
</tbody>
</table>

## NOTES

By **register\_file** option *i.sentinel.import* allows creating a file
which can be used to register imported imagery data into space-time
raster dateset (STRDS) by
*[t.register](https://grass.osgeo.org/grass-stable/manuals/t.register.html)*.
Note that currently a register file can be created only for Sentinel-2
data. See example below.

### Importing cloud and cloud shadow masks

If **-c** flag is given, a cloud mask with suffix \_MSK\_CLOUDS is
additionally created. For Level2A products this mask is based on the
Level2A inherent cloud probability layer and can be controlled by
specifying the **cloud\_\*** options. The default
**cloud\_probability\_threshold** applied to the probability layer is
set to 65%, which corresponds to the classification of such areas as
most likely cloudy according to the ESA classification scheme used for
the creation of the SCL layer. The SCL Layer itself is used if shadow
masks should be included in the \_MSK\_CLOUDS layer. This requires to
call the **-s** flag, which adds shadows as part of the \_MSK\_CLOUDS
output layer. The **cloud\_area\_threshold** parameter allows to exclude
small areas of cloud and shadow cover, which in case of vector outputs
tend to increase the computational speed. Note that the resolution of
the \_MSK\_CLOUDS layer (20m) is determined by the native resolution of
the cloud probability layer and the SCL layer, respectively. For Level1C
products a simplified cloud mask will be created since cloud probability
and SCL layer are not available. Note that for Level1C products only
clouds and no shadows can be masked and specifying the
**cloud\_probability\_threshold** does not influence the masking
procedure. Only the parameters **cloud\_area\_threshold** and
**cloud\_output** will be applied during the import of cloud masks for
Level1C products.

### Metadata import

By using the **-j** flag the band metadata are additionally stored in
JSON format (in the current mapset under `cell_misc`). These metadata
JSON files are supported by *i.sentinel.mask*.

## EXAMPLES

### List Sentinel bands

At first, print list of raster files to be imported by **-p**. For each
file also projection match with current location is printed including
detected input data EPSG code:

```sh
i.sentinel.import -p input=data

data/S2B_MSIL1C_20180216T102059_N0206_R065_T32UPB_20180216T140508.SAFE/GRANULE/.../T32UPB_20180216T102059_B04.jp2 1 (EPSG: 32632)
data/S2B_MSIL1C_20180216T102059_N0206_R065_T32UPB_20180216T140508.SAFE/GRANULE/.../T32UPB_20180216T102059_B07.jp2 1 (EPSG: 32632)
data/S2B_MSIL1C_20180216T102059_N0206_R065_T32UPB_20180216T140508.SAFE/GRANULE/.../T32UPB_20180216T102059_B11.jp2 1 (EPSG: 32632)
```

### Import Sentinel data

Import all Sentinel bands found in *data* directory and store metadata
as JSON files within the GRASS GIS database directory:

```sh
i.sentinel.import -j input=data
```

Limit import to only to 4th and 8th bands:

```sh
i.sentinel.import -j input=data pattern='B0(4|8)'
```

Limit import to all bands with 10m resolution (excluding AOT, WVP, ...
bands):

```sh
i.sentinel.import -j input=data pattern='B0(2|3|4|8)_10m'
```

Limit import to only selected bands with 10m and 20m resolution
(excluding AOT, WVP, ... bands):

```sh
i.sentinel.import -j input=data pattern='B(02_1|03_1|04_1|08_1|11_2)0m'
```

Limit import to all bands with 10m and 20m resolution (excluding AOT,
WVP, ... bands):

```sh
i.sentinel.import -j input=data pattern='_B((0[2348]_1)|(0[567]|8A|11|12)_2)0m'
```

Import cloud and shadow mask:

```sh
i.sentinel.import input=data
i.sentinel.import input=data -c -s
i.sentinel.import input=data cloud_probability_threshold=25 cloud_area_threshold=10 -c -s
```

<table>
<colgroup>
<col style="width: 33%" />
<col style="width: 33%" />
<col style="width: 33%" />
</colgroup>
<tbody>
<tr class="odd">
<td style="text-align: center;"><a href="i_sentinel_import_without_cloud_mask.png"><img src="i_sentinel_import_without_cloud_mask.png" alt="image-alt" /></a><br />
<br />
<em>Fig: S2 L2-A imagery without cloud mask<br />
(example: T33TVE_20210313T095029, Italy)<br />
</em></td>
<td style="text-align: center;"><a href="i_sentinel_import_with_cloud_shadow_mask_v1.png"><img src="i_sentinel_import_with_cloud_shadow_mask_v1.png" alt="image-alt" /></a><br />
<br />
<em>Fig: Cloud (ligthgrey) and shadow (darkgrey) mask<br />
(default options)<br />
</em></td>
<td style="text-align: center;"><a href="i_sentinel_import_with_cloud_shadow_mask_v2.png"><img src="i_sentinel_import_with_cloud_shadow_mask_v2.png" alt="image-alt" /></a><br />
<br />
<em>Fig: Cloud (ligthgrey) and shadow (darkgrey) mask<br />
(lower probability threshold and higher area threshold)<br />
</em></td>
</tr>
</tbody>
</table>

Link data from specific UTM zone while ignoring projection check

```sh
i.sentinel.import -l -o -j input=data pattern_file="_T32"
```

Limit import to only bands 3 and 4 from level 2A products for tile
T32VNR in 2019

```sh
i.sentinel.import -j input=data pattern_file="MSIL2A.*T32VNR_2019" pattern='B(03|04)'
```

Limit import to only bands 3 and 4 from level 2A products for tile
T32VNR in 2019, unzip to directory "safefiles\_dir":

```sh
i.sentinel.import -j input=data unzip_dir=safefiles_dir pattern_file="MSIL2A.*T32VNR_2019" pattern='B(03|04)'
```

### Register imported Sentinel data into STRDS

```sh
i.sentinel.import -j input=data register_output=t_register.txt

# register imported data into existing STRDS
t.register input=sentinel_ds file=t_register.txt
```

A register file typically contains two columns: imported raster map name
and timestamp separated by `|`. In the case of current development
version of GRASS which supports band references concept (see
*[i.band.library](https://grass.osgeo.org/grass-devel/manuals/i.band.library.html)*
module for details) a register file is extended by a third column
containg band reference information, see the examples below.

```sh
# register file produced by stable GRASS GIS 7.8 version
T33UVR_20181205T101401_B05|2018-12-05 10:16:43.275000
T33UVR_20181205T101401_B03|2018-12-05 10:16:43.275000
T33UVR_20181205T101401_B06|2018-12-05 10:16:43.275000
...
# register file produced by development GRASS GIS 7.9 version
T33UVR_20181205T101401_B05|2018-12-05 10:16:43.275000|S2_5
T33UVR_20181205T101401_B03|2018-12-05 10:16:43.275000|S2_3
T33UVR_20181205T101401_B06|2018-12-05 10:16:43.275000|S2_6
```

## SEE ALSO

*[Overview of i.sentinel toolset](i.sentinel.md)*

*[i.sentinel.download](i.sentinel.download.md),
[i.sentinel.preproc](i.sentinel.preproc.md),
[i.sentinel.mask](i.sentinel.mask.md),
[r.import](https://grass.osgeo.org/grass-stable/manuals/r.import.html),
[r.external](https://grass.osgeo.org/grass-stable/manuals/r.external.html),
[v.import](https://grass.osgeo.org/grass-stable/manuals/v.import.html)*

See also [GRASS GIS Workshop in
Jena](https://training.gismentors.eu/grass-gis-workshop-jena/units/20.html)
for usage examples.

## AUTHORS

Martin Landa, [GeoForAll
Lab](https://geomatics.fsv.cvut.cz/research/geoforall/), CTU in Prague,
Czech Republic with support of
[OpenGeoLabs](https://opengeolabs.cz/en/home/) company
