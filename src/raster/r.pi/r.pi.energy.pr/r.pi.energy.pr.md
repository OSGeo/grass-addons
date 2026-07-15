## DESCRIPTION

This function is based on *r.pi.energy* but adds the functionality of
iterative patch removal for testing of patch relevance to maintain the
landscape connectivity integrity. Isolation or connectivity of singular
patches of a defined landcover class are analysed using individual-based
dispersal models. This functions uses a maximum amount of energy for
each individuals dispersing through the landscape which is deminished by
a fricition or cost map. Unlike the related function *r.pi.energy* does
this function allows individuals to stay or move within a patch until
the energy is depleted.

## NOTES

Amount of successful immigrants or emigrants are not taken individual
into account which emigrated from and immigrated into the same patch
(pseudo immigration).

The suitability matrix impacts the step direction, while the costmap
relates to the depletion of assigned energy.

## EXAMPLE

An example for the North Carolina sample dataset: The amount (average)
and variance with or without the respective patch of successful
emigrants (\*\_emi), immigrants (\*\_imi), the percentage of immigrants
per patch (\*\_imi\_percent), the amount of lost indivuals (\*\_lost),
the amount of migrants (\*\_mig), successful (\*\_mig\_succ) and
unsuccessful migrants (\_mig\_unsucc) can be retrieved using this
command:

```sh
r.pi.energy.pr input=landclass96 output=energyiter1 keyval=5 n=1000 step_length=5 energy=10 percent=80 stats=average,variance
```

introducing costs for movement results in different immigration counts:

```sh
r.mapcalc "cost_raster = if(landclass96==5,1,if(landclass96 == 1, 10, if (landclass96==3,2, if(landclass96==4,1,if(landclass96==6,100)))))"
r.pi.energy.pr input=landclass96 output=energy1 keyval=5 n=1000 step_length=5 energy=10 percent=80 stats=average costmap=cost_raster
```

introducing a suitability for the movement:

```sh
# the suitability for the next step selection is defined as:
# class 5 and 3 (forest and grassland) have a high suitability,
# while shrubland (class 4) only a moderate and water and developed
# areas (class 6 and 1) have a very low suitability:

r.mapcalc "suit_raster = if(landclass96==5,100,if(landclass96 == 3, 100, if (landclass96==1,1, if(landclass96==6,1,if(landclass96==4,50)))))"
r.pi.energy.pr input=landclass96 output=energyiter3 keyval=5 n=1000 step_length=5 energy=10 percent=80 suitability=suit_raster stats=average,variance
```

further settings can be changed and information retrieved: setting the
perception range to 10 pixel:

```sh
r.pi.energy.pr input=landclass96 output=energyiter keyval=5 n=1000 step_length=5 energy=10 percent=80 perception=10 stats=average
```

increasing the attraction to move towards patches to 10:

```sh
r.pi.energy input=landclass96 output=energyiter keyval=5 n=1000 step_length=5 energy=10 percent=80 stats=average multiplicator=10
```

output of each movement location for a defined step frequency. Here
every 10th step is provided as output raster:

```sh
r.pi.energy input=landclass96 output=energyiter keyval=5 n=1000 step_length=5 energy=10 percent=80 stats=average out_freq=10
```

## SEE ALSO

*[r.pi.energy](r.pi.energy.md), [r.pi.searchtime](r.pi.searchtime.md),
[r.pi](r.pi.md)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
