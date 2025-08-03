## DESCRIPTION

The *v.maxent.swd* takes one or more point vector layers with the
location of species presence locations (parameter: **species**), and a
set of raster layers representing relevant environmental variables
(parameter: **evp\_maps**). For all point locations, it reads in the
values of the environmental raster layers. The resulting point layers(s)
are combined in one layer and this is exported as a SWD file that can be
used as input for MaxEnd 3.4 or higher.

The user can also provide a point layer with background points
(parameter: **bgp**). Alternatively, a user-defined number of background
points can be generated automatically, respecting the computational
region and MASK. In either case, for all point locations, the function
reads in the values of the environmental raster layers. The resulting
point layer is exported as a SWD file.

If alias names are used, a CSV file (alias\_file) can be created with
alias names in the first column and map names in the second column,
separated by comma, without a header.

## NOTES

The map names of both the species point layers and the environmental
parameters can be replaced by alias names, which will be used by MaxEnt.

The SWD file format is a simple comma-delimited text files. The first
three fields provide the species name, x-coordinate and y-coordinate,
while subsequent fields contain the values of the user-selected
environmental parameters. The files can be easily read in for example, R
and subsequently used in other models / functions.

Maxent expects the n-s and e-w resolution to be the same. Following the
grass gis convention, the resolution of an exported raster is determined
by the region settings. So make sure to set the resolution of the region
so that the n-s and e-w resolution match. To accomplish this, you can
use (replaced the \*\*\* for the desired resolution):

```sh
g.region -a res=***
```

Alternatively, you can set the **-e flag**. This will run g.region for
you, adjusting the resolution so both the ns and ew resolutionn match
the smallest of the two, using nearest neighbor resampling.

This addon is a vector-based alternative to *r.out.maxent\_swd*. It can
be more efficient with sparse data points. The main difference is that
with this addon you can have more than one sample point per raster cell.
But note that you can use the **-t** flag to thin the point layer so
that there is never more than 1 point per raster cell. Another
difference is the option to export the predictor raster layers to a
user-defined folder. This can be used in Maxent, Maxnet addon for R or
other software.

## EXAMPLES

The examples below use a dataset that you can download [from
here](https://ecodiv.earth/share/reader_SDM/grassmaxent_sampledata.zip).
It includes vector point layer with observation locations of the
pale-throated sloth (*Bradypus tridactylus*) from
[GBIF](https://doi.org/10.15468/dl.br8b4a), a number of bioclim raster
layers from
[WorldClim](https://www.worldclim.org/data/worldclim21.html), the [IUCN
RedList range map](https://www.iucnredlist.org/species/3037/210442660)
of the species, and a boundary layer of the South American countries
from
[NaturalEarth](https://www.naturalearthdata.com/downloads/50m-cultural-vectors/).

The zip file contains a [GRASS
location](https://grass.osgeo.org/grass-stable/manuals/grass_database.html#grass-locations).
Unzip it and put it in a GRASS GIS database. Next, open GRASS GIS and go
to the mapset *southamerica*. Download the zip file, and unzip it in a
GRASS GIS database.

```sh
v.maxent.swd -t species=Bradypus_tridactylus \
 evp_maps=bio02,bio03@southamerica,bio08,bio09,bio13,bio15,bio17 \
 evp_cat=sa_eco_l2 alias_cat=landuse nbgp=10000 \
 bgr_output=maxentinput/bgrd_swd.csv \
 species_output=maxentinput/spec_swd.csv \
 export_rasters=maxentinput/envlayers
```

The output is a folder *maxentinput* with the SWD files bgrd\_swd.csv
and spec\_swd.csv and the accompanying proj files. The latter provide
information about the CRS, which might be useful if you want to import
the point layers in another software tools. In addition, the example
code creates the raster layers of the environmental layes in ascii
format in the folder *envlayers*.

The created data layers can be used as input for
[Maxent](https://biodiversityinformatics.amnh.org/open_source/maxent/).
Alternatively, you can use it as input for the *r.maxent.train* addon,
which provides a convenient wrapper for the *Maxent* software.

## SEE ALSO

- [r.maxent.train](r.maxent.train.md) addon to create/train a Maxent
    model. The addon provides a wrapper to the Maxent software.
- [r.out.maxent\_swd](r.out.maxent_swd.md), an alternative
    implementation of this addon, using species distribution data in
    raster format.
- [r.maxent.lambdas](r.maxent.lambdas.md) addon to compute raw or
    logistic prediction maps from MaxEnt lambdas files.

## REFERENCES

- MaxEnt 3.4.1 (
    [https://biodiversityinformatics.amnh.org/open\_source/maxent](https://biodiversityinformatics.amnh.org/open_source/maxent/))
- Steven J. Phillips, Miroslav Dudík, Robert E. Schapire. A maximum
    entropy approach to species distribution modeling. In Proceedings of
    the Twenty-First International Conference on Machine Learning, pages
    655-662, 2004.
- Steven J. Phillips, Robert P. Anderson, Robert E. Schapire. Maximum
    entropy modeling of species geographic distributions. Ecological
    Modelling, 190:231-259, 2006.
- Jane Elith, Steven J. Phillips, Trevor Hastie, Miroslav Dudík, Yung
    En Chee, Colin J. Yates. A statistical explanation of MaxEnt for
    ecologists. Diversity and Distributions, 17:43-57, 2011.
- GBIF.org (12 November 2023) GBIF Occurrence Download
    <https://doi.org/10.15468/dl.br8b4a>

## AUTHOR

[Paulo van Breugel](https:ecodiv.earth), [HAS green
academy](https://has.nl), [Innovative Biomonitoring research
group](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/),
[Climate-robust Landscapes research
group](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)
