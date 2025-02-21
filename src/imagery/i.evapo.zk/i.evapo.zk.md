## DESCRIPTION

*i.evapo.zk* Calculates the global diurnal evapotranspiration after
Zhang, Kimball, Nemani and Running (2010).

## NOTES

*Main function* ETa (biome\_type, ndvi, tday, sh, patm, Rn, G)

  - Biome\_type as defined below
  - ndvi NDVI value \[-\]
  - tday day temperature \[C\]
  - sh specific humidity \[-\]
  - patm atmospheric pressure \[Pa\]
  - Rn day net radiation \[MJ/m2/d\]
  - G day soil heat flux \[MJ/m2/d\]

IGBP Biome types with ID used in this model:

  - Code ID Description
  - BENF 0 Boreal Evergreen Needleleaf Forest (less or eq 212 frost-free
    days)
  - TENF 1 Temperate Evergreen Needleleaf Forest (more than 212
    frost-free days)
  - EBF 2 Evergreen Broadleaf Forest
  - DBF 4 Deciduous Broadleaf Forest
  - CSH 6 Closed Shrubland
  - OSH 7 Open Shrubland
  - WSV 8 Woody Savannah
  - SV 9 Savannah
  - GRS 10 Grassland
  - CRP 12 Cropland

IGBP Classification:

  - 01 Evergreen Needleleaf Forest
  - 02 Evergreen Broadleaf Forest
  - 03\* Deciduous Needleleaf Forest
  - 04 Deciduous Broadleaf Forest
  - 05\* Mixed Forest (stats of other classes areas used in article)
  - 06 Closed Shrublands
  - 07 Open Shrublands
  - 08 Woody Savannas
  - 09 Savannas
  - 10 Grasslands
  - 11\* Permanent Wetlands
  - 12 Croplands
  - 13\* Urban and Built-Up
  - 14\* Cropland/Natural Vegetation Mosaic
  - 15\* Snow and Ice
  - 16\* Barren or Sparsely Vegetated
  - 17\* Water Bodies (Evaporation Priestley-Taylor used in article)

\* Not used in this model *IGBP Biome types and configuration of
internal parameters of the model*

  - Code Description TcloseMinC TopenMaxC VPDClosePa VPDOpenPa ToptC
    BetaC kPa GaMs-1 GtotMs-1 GchMs-1 B1Sm-1 B2Sm-1 B3 b1\* b2\* b3\*
    b4\*
  - BENF Boreal Evergreen Needleleaf Forest -8 40 2800 500 12 25 150
    0.03 0.002 0.08 208.3 8333.3 10
  - TENF Temperate Evergreen Needleleaf Forest -8 40 2800 500 25 25 200
    0.03 0.004 0.08 133.3 888.9 6
  - EBF Evergreen Broadleaf Forest -8 50 4000 500 40 40 300 0.03 0.006
    0.01 57.7 769.2 4.5
  - DBF Deciduous Broadleaf Forest -6 45 2800 650 28 25 200 0.04 0.002
    0.01 85.8 694.7 4
  - MF Mixed Forest
  - CSH Closed Shrubland -8 45 3300 500 19 20 400 0.01 0.001 0.04 202
    4040.4 6.5
  - OSH Open Shrubland -8 40 3700 500 10 30 50 0.005 0.012 0.04 178.6
    178.6 8
  - WSV Woody Savannah -8 50 3200 500 32 28 900 0.002 0.0018 0.04 0.2
    24000 6.5 57.1\* 3333.3\* 8\* -0.01035\*
  - SV Savannah -8 40 5000 650 32 30 800 0.001 0.001 0.04 790.9 8181.8
    10
  - GRS Grassland -8 40 3800 650 20 30 500 0.001 0.001 0.04 175 2000 6
  - CRP Cropland -8 45 3800 650 20 30 450 0.005 0.003 0.04 105 3000 3

\* For WSV when NDVI superior to 0.64"

## SEE ALSO

*[i.evapo.pm](https://grass.osgeo.org/grass-stable/manuals/i.evapo.pm.html)  
[i.evapo.mh](https://grass.osgeo.org/grass-stable/manuals/i.evapo.mh.html)  
[i.evapo.senay](i.evapo.senay.md)  
[i.eb.netrad](https://grass.osgeo.org/grass-stable/manuals/i.eb.netrad.html)  
[i.eb.soilheatflux](i.eb.soilheatflux.md)  
*

## REFERENCES

Zhang, K., Kimball, J.S., Nemani, R.R., Running, S.W. (2010). A
continuous satellite-derived global record of land surface
evapotranspiration from 1983 to 2006. WRR 46, W09522

Chemin, Y., 2012. A Distributed Benchmarking Framework for Actual ET
Models, in: Irmak, A. (Ed.), Evapotranspiration - Remote Sensing and
Modeling. InTech.
([PDF](https://www.intechopen.com/books/evapotranspiration-remote-sensing-and-modeling/a-distributed-benchmarking-framework-for-actual-et-models),
[DOI: 10.5772/23571](https://doi.org/10.5772/23571))

## AUTHOR

Yann Chemin, GRASS Development Team, 2011
