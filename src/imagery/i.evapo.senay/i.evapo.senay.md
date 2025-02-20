## DESCRIPTION

*i.evapo.senay* Calculates the diurnal actual evapotranspiration after
Senay (2007). This is converting all Net radiation from the diurnal
period into ET, then uses Senay equation for evaporative fraction.

It takes input maps of Albedo, surface skin temperature, latitude, day
of year, single-way transmissivity and takes input value of the density
of fresh water.

DEM is used for calculating min and max temperature for Senay equation.

The "-s" flag permits output map of evaporative fraction from Senay.

## NOTES

If you are trying to map irrigated crops, and you know there is at least
one crop pixel that is evapotranspiring at maximum (ETa=ETpot), then
read this.

*i.evapo.senay* is highly dependent on the wet pixel being the lowest
temperature in the crop pixels to work for non water stressed crops,
force it that way, even if it breaks non crop areas. I suggest you
reduce your region to the irrigation system boundaries, checking that it
includes a bit of dry area for the hot/dry pixel.

Since it is a direct relationship to LST, evaporative fraction can be
very sensitive to the kind of pixel sample you feed it with.

## TODO

## SEE ALSO

*[r.sun](https://grass.osgeo.org/grass-stable/manuals/r.sun.html),
[i.albedo](https://grass.osgeo.org/grass-stable/manuals/i.albedo.html),
[i.eb.eta](https://grass.osgeo.org/grass-stable/manuals/i.eb.eta.html),
[i.eb.evapfr](https://grass.osgeo.org/grass-stable/manuals/i.eb.evapfr.html),
[i.evapo.potrad](i.evapo.potrad.md)*

## REFERENCES

  - Senay 2007

Chemin, Y., 2012. A Distributed Benchmarking Framework for Actual ET
Models, in: Irmak, A. (Ed.), Evapotranspiration - Remote Sensing and
Modeling. InTech.
([PDF](https://www.intechopen.com/books/evapotranspiration-remote-sensing-and-modeling/a-distributed-benchmarking-framework-for-actual-et-models),
[DOI: 10.5772/23571](https://doi.org/10.5772/23571))

## AUTHOR

Yann Chemin, International Rice Research Institute, The Philippines.
