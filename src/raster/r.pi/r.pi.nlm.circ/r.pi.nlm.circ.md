## DESCRIPTION

*r.pi.nlm.circ* is a random patch generator. It creates a random
landscape with defined attributes.

## NOTES

The user must specify the names of the raster map layers to be used for
*input* and *output*, the *landcover*, the *size*, the *count* used, the
*keyval* of the class of interest of the input raster map.

  - **Input**  
    The *Input* is potentially used for Landcover, size and count.
  - **keyval**  
    The *keyval* is used to compute landcover and count if not declared.
  - **landcover**  
    The *landcover* defines the amount of cover, if not declared, the
    landcover of keyval of input is used.
  - **count**  
    The *count* defines the amount of patches in the landscape, if not
    defined, the amount of patches in the input is used, if 0 is
    inserted, random amount of patches are created. Values from 1-n can
    be defined for a fixed number of patches.
  - **size**  
    The *size* defines the size of the artificial landscape. If not
    declared the size of the actual region is taken.
  - **seed**  
    The *seed* defiens the seed of random points. If all settings and
    the seed is fixed, then the patches won't be random anymore, but
    fixed. The user will receive everytime the same landscape.
  - **xxx**  
    The *xxx* ....
  - **xxx**  
    The *xxx* ....

## EXAMPLE

An example for the North Carolina sample dataset:

```sh
g.region -d
...
```

## SEE ALSO

*[r.pi.nlm](r.pi.nlm.md), [r.pi.nlm.stats](r.pi.nlm.stats.md),
[r.pi](r.pi.md)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
