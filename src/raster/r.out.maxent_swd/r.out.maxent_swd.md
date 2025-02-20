## DESCRIPTION

The script is intended to produce a set of SWD files as input to MaxEnt
\>= 3.3.3e using **r.stats**.  
  
The SWD file format is a simple CSV-like file file format as described
in Elith et al. 2011. Generally it looks like:  
*specie\_name,X,Y,parameter\_1,parameter\_2,...  
your\_specie,1.1,1.1,2,4.7,...  
* The first column always contains the name of the species, followed by
two columns for the X- and Y-coordinates. Then each column represents
one environmental parameter. In contrast to **r.stats** only integer
values are accepted to represent NO DATA.  
  
A background SWD file is always produced while species output can be
omitted.  
  
Multiple species can be processed, but each has to be in an individual
raster map. Map names of the maps containing the environmental
parameters can be replaced by short names, which should be used in
MaxEnt \>= 3.3.3.e.  
  
Results from MaxEnt can either be imported using **r.in.xyz** or
calculated from MaxEnt lambdas file using the **r.maxent.lambdas**.

## SEE ALSO

*[r.stats](https://grass.osgeo.org/grass-stable/manuals/r.stats.html),
[r.what](https://grass.osgeo.org/grass-stable/manuals/r.what.html),
[r.in.xyz](https://grass.osgeo.org/grass-stable/manuals/r.in.xyz.html),,
[r.maxent.lambdas](https://grass.osgeo.org/grass-stable/manuals/addons/r.maxent.lambdas.html)*

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

## AUTHOR

Stefan Blumentrath, Norwegian Institute for Nature Research (NINA),
<https://www.nina.no>
