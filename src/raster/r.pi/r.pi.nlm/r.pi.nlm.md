## DESCRIPTION

Creates a random generated map with values 0 or 1" "by given landcover
and agglomeration value.

## NOTES

Related to r.pi.nlm.circ but using fractal landscapes instead of
circular growth. Per default the size of the whole region is used for
generating a random landscape, this can be constraint by assigning a
class in a raster map with acts as mask for the generation of the random
landscape (*nullval*). The landcover can be set manually, randomly or be
taken from the input class coverage. The agglomeration level
(*sharpness*) can be set manually or randomly. If similar random
landscape with differing e.g. percentage coverage should be generated,
then the *seed* can be set using any number and reused for any
subsequent analysis.

## EXAMPLE

An example for the North Carolina sample dataset: A random landscape
with random percentage coverage and agglomeration factor:  

```sh
r.pi.nlm output=nlm.1 landcover=50
```

A random landscape is generated using the percentage coverage of class
5. The agglomeration factor is set randomly:  

```sh
r.pi.nlm input=landclass96 output=nlm.2 keyval=5
```

## SEE ALSO

*[r.pi.nlm.circ](r.pi.nlm.circ.md), [r.pi.nlm.stats](r.pi.nlm.stats.md),
[r.pi](r.pi.md)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
