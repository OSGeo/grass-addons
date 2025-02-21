## DESCRIPTION

Inverse cost weighting is like inverse distance weighted (IDW)
interpolation, but uses *cost* instead of shortest Euclidean distance.
In this way solid barriers and molasses zones may be correctly taken
into account.

Input data points do not need to have direct line of sight to each
other. This is interpolation "as the fish swims", not "as the crow
flies", and can see around headlands or across land-bridges without
polluting over barriers which the natural value (or flightless bird) can
not cross.

It was initially written to interpolate water chemistry in two parallel
arms of a fjord, but may just as well be used for population abundance
constrained by topography, or in studies of archeologic technology
transfer.

## NOTES

In the simplest case, the cost map will just be a mask raster with
values of 1 in areas to interpolate, and NULL in impenetrable areas.
Fancier cost maps can be used, for example, to make it more expensive
for a measured pollutant to diffuse upstream in an estuary, or to make
it more expensive for a stone tool technology to cross waterways.

Since generating cost maps can take a long time, it is recommended to
keep the raster region relatively small and limit the number of starting
points to less than 500.

Higher values of **friction** will help limit unconstrained boundary
effects at the edges of your coverage, but will incur more of a stepped
transition between sites.

The **post\_mask**, if given, is applied after the interpolation is
complete. A common use for that might be to only present data within a
certain distance (thus confidence) of an actual sampling station. In
that case the *r.cost* module can be used to create the mask.

This module writes lots of temporary files and so can be rather disk I/O
intensive. If you are running it many times in a big loop you may want
to try setting up a RAM-disk to put the mapset in (on UNIX symlinking
back into the location is ok), or adjust the disk-cache flushing timer
to be slightly longer than one iteration of the script.  
To do this on Linux you can tune the
`/proc/sys/vm/dirty_expire_centisecs` kernel control. The default is to
keep files in memory a maximum of 30 seconds before writing them to
disk, although if you are short on free RAM the kernel may write to disk
long before that timeout is reached.

By default the module will run serially. To run in parallel set the
**workers** parameter to the desired value (typically the number of
cores in your CPU). Alternatively, if the `WORKERS` environment variable
is set, the number of concurrent processes will be set at that number of
jobs.

## EXAMPLE

In this example we'll generate some fake island barriers from the
standard North Carolina GRASS dataset, then interpolate a continuous
variable between given point stations. We'll use rainfall, but for the
purposes of the exercise pretend it is a nutrient concentration in our
fake wayerway. Point data stations outside of the current region or in
NULL areas of the *cost\_map* will be ignored.

```sh
# set up a fake sea with islands:
g.region n=276000 s=144500 w=122000 e=338500 res=500
r.mapcalc "pseudo_elev = elev_state_500m - 1100"
r.colors pseudo_elev color=etopo2
r.mapcalc "navigable_mask = if(pseudo_elev < 0, 1, null())"

# pick a data column from the points vector:
v.info -c precip_30ynormals

# run the interpolation:
v.surf.icw input=precip_30ynormals column=annual output=annual_interp.3 \
   cost_map=navigable_mask friction=3 --verbose

# equalize colors to show maximum detail:
r.colors -e annual_interp.3 color=bcyr

# display results in a GRASS monitor:
d.mon wx0
d.erase black
d.rast annual_interp.3
d.vect precip_30ynormals fcolor=red icon=basic/circle
d.legend annual_interp.3 at=48.4,94.8,3.4,6.0
```

## REFERENCES

The method was first described in Wing et. al 2004, with further
comments and examples in report 3 of that series, 2005. Ducke and
Rassmann 2010 (in German) describe a novel use of the approach to study
prehistoric movement corridors of early Bronze Age technology through
Europe.

- Wing, S.R., M.H.E. Bowman, F. Smith and S.M. Rutger (2004),
    *Analysis of biodiversity patterns and management decision making
    processes to support stewardship of marine resources and
    biodiversity in Fiordland - a case study*, report 2 of 3, Technical
    report, Report to the Ministry for the Environment, New Zealand.
- Ducke, B. and K. Rassmann (2010), *Modelling and Interpretation of
    the Communication Spaces of the 3rd and Early 2nd Millennium BC in
    Europe Using Diversity Gradients*   (*Modellierung und
    Interpretation der Kommunikationsräume des 3. und frühen 2.
    Jahrtausends v. Chr.*), in Europa mittels Diversitätsgradienten;
    Archäologischer Anzeiger 2010/1, pp.239-261

## SEE ALSO

*[v.surf.idw](https://grass.osgeo.org/grass-stable/manuals/v.surf.idw.html).
[v.surf.rst](https://grass.osgeo.org/grass-stable/manuals/v.surf.rst.html).
[v.surf.bspline](https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html).
[r.cost](https://grass.osgeo.org/grass-stable/manuals/r.cost.html).
[r.surf.idw](https://grass.osgeo.org/grass-stable/manuals/r.surf.idw.html),
[r.surf.idw2](https://grass.osgeo.org/grass-stable/manuals/r.surf.idw2.html)*

## AUTHOR

Hamish Bowman  
*Department of Marine Science,  
Dunedin, New Zealand*
