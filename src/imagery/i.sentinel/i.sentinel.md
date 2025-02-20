## DESCRIPTION

The *i.sentinel* toolset consists of currently six modules:

  - [i.sentinel.coverage](i.sentinel.coverage.md)  
    checks the area coverage of Sentinel-1 or Sentinel-2 scenes selected
    by filters
  - [i.sentinel.download](i.sentinel.download.md)  
    downloads Copernicus Sentinel products from [Copernicus Open Access
    Hub](https://scihub.copernicus.eu/)
  - [i.sentinel.parallel.download](i.sentinel.parallel.download.md)  
    downloads parellelized (using i.sentinel.download) Copernicus
    Sentinel products from [Copernicus Open Access
    Hub](https://scihub.copernicus.eu/)
  - [i.sentinel.import](i.sentinel.import.md)  
    imports already downloaded Sentinel products into GRASS GIS mapset
  - [i.sentinel.preproc](i.sentinel.preproc.md)  
    imports and performs atmospheric correction on Sentinel-2 images
  - [i.sentinel.mask](i.sentinel.mask.md)  
    creates clouds and shadows masks for Sentinel-2 images

## REQUIREMENTS

  - [Sentinelsat library](https://pypi.org/project/sentinelsat/)
  - [Pandas library](https://pypi.org/project/pandas/)

## AUTHORS

Martin Landa, [GeoForAll
Lab](https://geomatics.fsv.cvut.cz/research/geoforall/), CTU in Prague,
Czech Republic with support of
[OpenGeoLabs](https://opengeolabs.cz/en/home/) company

Roberta Fagandini, GSoC 2018 student, Italy

Anika Weinmann, Guido Riembauer, Markus Neteler,
[mundialis](https://www.mundialis.de/), Germany
