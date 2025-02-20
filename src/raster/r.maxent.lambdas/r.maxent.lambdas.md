## DESCRIPTION

The script is intended to compute (**raw**) or (**logistic**) prediction
maps from a lambdas file produced with MaxEnt \>= 3.3.3e.

It will parse the specified **lambdas\_file** from MaxEnt \>= 3.3.3e and
translate it into an r.mapcalc-expression. If alias names had been used
in MaxEnt, these alias names can automatically be replaced according to
a CSV-like file (**alias\_file**) provided by the user, as it can be
produced with
[r.out.maxent\_swd](https://grass.osgeo.org/grass-stable/manuals/addonsr.out.maxent_swd.html).
This file should contain alias names in the first column and map names
in the second column, separated by comma, without header. It should look
e.g. like this:

```sh
alias_1,map_1
alias_2,map_2
...,...
```

If such a CSV-file with alias names used in MaxEnt is provided, the
alias names from MaxEnt are replaced by raster map names.

The logistic map can be produced as an integer map. To do so the user
has to specify the number of decimal places, that should be preserved in
integer output in the **ndigits** option.

Optionally the map calculator expressions can be printed to stdout with
the **p**-flag for inspection or documentation as they likely exceed the
space in the map history.

By default, NoData for each function in the lambdas file is set to zero.
The user can however choose to set pixels to null where a single
variable contains NoData (**n**-flag) or where all variables produce
NoData (**N**-flag).

Extraction of random points in MaxEnt can be a reason why values in
raster maps exceed values seen by the MaxEnt model. To limit raster map
values to the valid range for the model, raster map values can be
clamped to the value range in the model with the **c**-flag.

Complex models (and thus mapcalculator expressions) can become CPU
intensive to process. On multicore computers, processing such large
models can benefit from tiled, parallel processing (**nprocs** larger
than 1). This requires that the
[r.mapcalc.tiled](https://grass.osgeo.org/grass-stable/manuals/addons/r.mapcalc.tiled.html)
addon is installed. The size of tiles can be controlled by the
**height** and **width** options.

## NOTES

This script works only if the maps containing the input data to MaxEnt
are accessible from the current region.

Due to conversion from double to floating-point in exp()-function, a
loss of precision from the 7th decimal place onwards may occur in the
logistic output. Differences to logistic predictions from MaxEnt are
supposed to be below 0.0001. This can be checked by importing sample or
background predictions from the MaxEnt output (e.g. with
[r.in.xyz](https://grass.osgeo.org/grass-stable/manuals/r.in.xyz.html)).

## REFERENCES

  - Wilson, Peter D. 2009: Guidelines for computing MaxEnt model output
    values from a lambdas file. (Available at
    <https://gsp.humboldt.edu/OLM/Courses/GSP_570/Learning-Modules/10-BlueSpray_Maxent_Uncertinaty/MaxEnt-lambda-files.pdf>)
  - Steven J. Phillips, Miroslav Dudík, Robert E. Schapire. 2020: Maxent
    software for modeling species niches and distributions (Version
    3.4.1). Available from url:
    <https://biodiversityinformatics.amnh.org/open_source/maxent> and
    <https://github.com/mrmaxent/Maxent>
  - Steven J. Phillips, Miroslav Dudík, Robert E. Schapire. 2004: A
    maximum entropy approach to species distribution modeling. In
    Proceedings of the Twenty-First International Conference on Machine
    Learning, pages 655-662, 2004.
  - Steven J. Phillips, Robert P. Anderson, Robert E. Schapire. 2006:
    Maximum entropy modeling of species geographic distributions.
    Ecological Modelling, 190:231-259, 2006.
  - Jane Elith, Steven J. Phillips, Trevor Hastie, Miroslav Dudík, Yung
    En Chee, Colin J. Yates. 2011: A statistical explanation of MaxEnt
    for ecologists. Diversity and Distributions, 17:43-57, 2011.

## SEE ALSO

*[r.in.xyz](https://grass.osgeo.org/grass-stable/manuals/r.in.xyz.html),
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.mapcalc.tiled](https://grass.osgeo.org/grass-stable/manuals/addons/r.mapcalc.tiled.html)
(Addon)
[r.out.maxent\_swd](https://grass.osgeo.org/grass-stable/manuals/addons/r.out.maxent_swd.html)
(Addon)*

## AUTHOR

Stefan Blumentrath, Norwegian Institute for Nature Research (NINA),
<https://www.nina.no>
