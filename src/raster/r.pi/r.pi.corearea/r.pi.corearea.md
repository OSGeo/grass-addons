## DESCRIPTION

Edge effects and core area analysis of landcover fragments. This module
can compute static edge effects (defined edge depth) and dynamic edge
effects (based on surrounding landscape). The impact of the surrounding
landscape can be accounted for and the resulting core area is provided.

## NOTES

This module is generating core areas based on defined edge depths. The
edge depths can be increased by the values of a *costmap* (e.g. urban
areas could have a more severe impact than secondary forest on forest
fragments). Moreover a friction map ( *propmap* within the fragments can
lower the impact of surrounding landcover types and hence an increased
edge depth (e.g. a river or escarpment which might lower the edge
effects). Moreover a *dist\_weight* can be assigned in order to increase
the weight of closer pixel values.

### Distance weight

The assigned distance weight is computed as:  
w(d) = 1 - (d / d\_max)^(tan(dist\_weight \* 0.5 \* pi))  
where:  

  - d = Distance of the respective cell
  - d\_max - the defined maximum distance
  - dist\_weight - the parameter how to weight the pixel values in the
    landscape depending on the distance  

the *dist\_weight* has a range between 0 and 1 and results in:

  - 0 \< dist\_weight \< 0.5: the weighting curve decreases at low
    distances to the fragment and lowers to a weight of 0 at d=d\_max
  - dist\_weight = 0.5: linear decrease of weight until weight of 0 at d
    = d\_max
  - 0.5 \< dist\_weight \< 1: the weighting curve decreases slowly at
    low distances and approaches weight value of 0 at higher distances
    from the fragment, the weight value 0 is reached at d = d\_max
  - dist\_weight = 1: no distance weight applied, common static edge
    depth used

### propmap

The *propmap* minimizes the effect of the edge depth and the surrounding
matrix. This has an ecological application if certain landscape features
inside a e.g. forest fragment hamper the human impact (edge effects).  
two methods exist:  

  - propmethod=linear: propagated value = actual value - (propmap value
    at this position)  
  - propmethod=exponential: propagated value = actual value / (propmap
    value at this position)  

If 0 is chosen using the linear method, then propagated value=actual
value which results in a buffering of the whole region. In order to
minimize the impact the value must be larger than 1. For the exponential
method a value of below 1 should not be chosen, otherwise it will be
propagated infinitely.

## EXAMPLE

An example for the North Carolina sample dataset using class 5 (forest):
For the computation of variable edge effects a costmap is necessary
which need to be defined by the user. Higher costs are resulting in
higher edge depths:

```sh
# class - type - costs
#   1   - developed - 3
#   2   - agriculture - 2
#   3   - herbaceous - 1
#   4   - shrubland - 1
#   5   - forest - 0
#   6   - water - 0
#   7   - sediment - 0

r.mapcalc "costmap_for_corearea = if(landclass96==1,3,if(landclass96==2,2,if(landclass96==3,1,if(landclass96==4,1,if(landclass96==5,0,if(landclass96==6,0,if(landclass96==7,0)))))))"

```

now the edge depth and the resulting core area can be computed:

```sh
r.pi.corearea input=landclass96 costmap=costmap_for_corearea  output=landcover96_corearea keyval=5 buffer=5 distance=5 angle=90 stats=average propmethod=linear
```

the results consist of 2 files:  
landclass96\_corearea: the actual resulting core areas  
landclass96\_corearea\_map: a map showing the edge depths

## SEE ALSO

*[r.pi.grow](r.pi.grow.md), [r.pi.import](r.pi.import.md),
[r.pi.index](r.pi.index.md), [r.pi](r.pi.md)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
