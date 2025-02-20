## DESCRIPTION

*i.lswt* computes Lake Water Surface Temperature (LSWT) from moderate
resolution polar orbiting satellites with dual thermal channels. Given
the Top Of Atmosphere(TOA) Brightness Temperatures (BT) derived from the
thermal channels of the supported satellites, the module computes
surface temperature. For water surface (lakes/inland water bodies), the
module uses a simplified non-linear split-window algorithm.

## NOTES

The non-linear split window equation used here is:

```sh
LSWT = Ti + c1 * (Ti - Tj) + c2 * (Ti - Tj) ^ 2 + c0
```

Where Ti and Tj are Brightness temperatures derived from dual thermal
channels 10.5 - 11.5 micro m and 11.5 - 12.5 micro m respectively. The
split window equation and the coefficients c0,c1,c2 are taken from
Jimenez-Munoz et.al (2008).

## EXAMPLE

```sh
r.mask vect=watermask cats=1 --o
i.lswt in1=NSS.LHRR.NP.D14177.S1312_b4 in2=NSS.LHRR.NP.D14177.S1312_b5 \
  basename=NSS.LHRR.NP.D14177.S1312 satellite=NOAA19-AVHRR
```

## REFERENCES

The satellite specific split-window coefficients are taken from:

  - Jimenez-Munoz, J.-C., Sobrino, J.A., 2008. Split-Window Coefficients
    for Land Surface Temperature Retrieval From Low-Resolution Thermal
    Infrared Sensors. IEEE Geoscience and Remote Sensing Letters 5,
    806-809. ([DOI](https://doi.org/10.1109/LGRS.2008.2001636))

A new method to develop continuos time series of LSWT from historical
AVHRR is explained below, uses the same split window technique
implemented here:

  - Pareeth, S., Delucchi, L., Metz, M., Rocchini, D., Devasthale, A.,
    Raspaud, M., Adrian, R., Salmaso, N., Neteler, M., 2016. New
    Automated Method to Develop Geometrically Corrected Time Series of
    Brightness Temperatures from Historical AVHRR LAC Data. Remote
    Sensing 8, 169. ([DOI](https://doi.org/10.3390/rs8030169))

## SEE ALSO

*[i.landsat8.swlst](i.landsat8.swlst.md),
[i.emissivity](https://grass.osgeo.org/grass-stable/manuals/i.emissivity.html)*

## AUTHOR

Sajid Pareeth; Fondazione Edmund Mach, Italy
