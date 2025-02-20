## DESCRIPTION

The *i.landsat* toolset consists of three modules:

  - [i.landsat.download](i.landsat.download.md)  
    downloads Landsat TM, ETM and OLI data from
    [EarthExplorer](https://earthexplorer.usgs.gov/) using
    [landsatxplore](https://github.com/yannforget/landsatxplore) Python
    library
  - [i.landsat.import](i.landsat.import.md)  
    imports Landsat data downloaded from EarthExplorer into GRASS GIS
    mapsets
  - [i.landsat.qa](i.landsat.qa.md)  
    reclassifies Landsat QA band according to acceptable pixel quality
    as defined by the user

## REQUIREMENTS

  - An [EarthExplorer](https://ers.cr.usgs.gov/register) account
  - [landsatxplore library](https://github.com/yannforget/landsatxplore)
    (install with `pip install landsatxplore`)

## AUTHORS

[Veronica Andreo](https://veroandreo.gitlab.io/), CONICET, Argentina.  
Stefan Blumentrath, Norwegian Institute for Nature Research, Oslo
(Norway)
