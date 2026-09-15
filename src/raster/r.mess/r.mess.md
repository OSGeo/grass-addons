## DESCRIPTION

*r.mess* computes the multivariate environmental similarity (MES) \[1\],
which measures how similar environmental conditions in one area are to
those in a reference area. This can also be used to compare
environmental conditions between current and future scenarios. See the
supplementary materials of Elith et al. (2010) \[1\] for more details.

Besides the MES, *r.mess* computes the individual similarity layers (IES

- the user can select to delete these layers) and, optionally, several
other layers that help to further interpret the MES values:

  - The area where for at least one of the variables has a value that
    falls outside the range of values found in the reference set.
  - The most dissimilar variable (MoD).
  - The sum of the IES layers where IES \< 0. This is similar to the NT1
    measure as proposed by Mesgaran et al. 2014 \[2\].
  - The number of layers with negative values.

The user can compare a set of reference (baseline) conditions to
projected (test) conditions. The reference conditions are defined by a
set of environmental raster layers (**ref\_env**). To specify the
reference area, one of the following can be used:

- **ref\_rast** = reference raster layer: A raster with values of 1
    and 0 (or nodata). Reference conditions are derived from the
    locations where the raster value is 1.
- **ref\_vect** = reference vector point layer: Reference conditions
    are taken for the point locations in the vector layer.
- **ref\_region** = reference region: Only areas within the specified
    region's boundaries are considered as the reference area.

If no reference raster map, vector map, or region is provided, the
entire area covered by the input environmental raster layers is used as
the reference area.

The projected (test) conditions are defined by a second set of
environmental variables (**proj\_env**). They can represent future
conditions in the same area (similarity across time), or conditions in
another area (similarity between two different areas). If a projection
region (**proj\_region**) is provided, the MESS (and other layers) will
be limited to that region.

If **proj\_env** is not provided, the MESS value of a raster cell
represents how similar the conditions in that cell are compared to the
medium conditions across the whole area.

## EXAMPLE

The examples below use the bioclimatic variables bio1 (mean annual
temperature), bio12 (annual precipitation), and bio15 (precipitation
seasonality) in Kenya and Uganda. All climate layers (current and
future) are from [Worldclim.org](http://www.worldclim.org). The
protected areas layer includes all nationally designated protected areas
with a IUCN category of II or higher from
[protectedplanet.net](http://www.protectedplanet.net/).

### Example 1

The simplest case is when only a set of reference data layers
(**ref\_env** ) is provided. The multi-variate similarity values of the
resulting map are a measure of how similar conditions in a location are
to the median conditions in the whole region.

```sh
g.region raster=bio1
r.mess ref_env=bio1,bio12,bio15 output=Ex_01
```

Thus, in the following maps, the value in each pixel represents how
similar conditions are in that pixel to the median conditions in the
entire region, in terms of mean annual temperature (bio1), mean annual
precipitation (bio12), precipitation seasonality (bio15) and the three
combined (MES).

![image-alt](r_mess_Ex_01.png)

### Example 2

In the second example, conditions in the whole region are compared to
those in the region's protected areas (ppa), which thus serves as the
reference/sample area. See [van Breugel et
al.(2015)](https://doi.org/10.1371/journal.pone.0121444) \[3\] for an
example of how this can be useful.

```sh
g.region raster=bio1
r.mess -m -n -i ref_env=bio1,bio12,bio15 ref_rast=ppa output=Ex_02
```

In the figure below the map with the protected areas, the MES, the most
dissimilar variables, and the areas with novel conditions are given.
They show that the protected areas cover most of the region's annual
precipitation, mean annual temperature, and precipitation seasonality
gradients. Areas with novel conditions can be found in northern Kenya.

![image-alt](r_mess_Ex_02.png)

### Example 3

Similarity between long-term average conditions based on the period
1950-2000 (**ref\_env**) and projections for climate conditions in 2070
under RCP85 based on the IPSL General Circulation Models (
**proj\_env**). No reference points or areas are defined in this
example, so the whole region is used as a reference.

```sh
g.region raster=bio1
r.mess ref_env=bio1,bio12,bio15 proj_env=IPSL_bio1,IPSL_bio12,IPSL_bio15
output=Ex_03
```

Results (below) shows that there is a fairly large area with novel
conditions. Note that in the *MES* map, the values are based on the
highest negative value across the input variables (here bio1, bio12,
bio15). In the *SumNeg* map, values of all input variables are summed
when negative. The *Count* map shows for each raster cell how many
variables have negative similarity scores. Thus, the values in the *MES*
and *SumNeg* maps only differ where the MES of more than one variable is
negative (dark gray areas in the *Count* map).

![image-alt](r_mess_Ex_03.png)

## REFERENCES

\[1\] Elith, J., Kearney, M., & Phillips, S. 2010. The art of modelling
range-shifting species. Methods in Ecology and Evolution 1:330-342.

\[2\] Mesgaran, M.B., Cousens, R.D. & Webber, B.L. (2014) Here be
dragons: a tool for quantifying novelty due to covariate range and
correlation change when projecting species distribution models.
Diversity & Distributions, 20: 1147-1159, DOI: 10.1111/ddi.12209.

\[3\] van Breugel, P., Kindt, R., Lillesø, J.-P.B., & van Breugel, M.
2015. Environmental Gap Analysis to Prioritize Conservation Efforts in
Eastern Africa. PLoS ONE 10: e0121444.

## SEE ALSO

For an example of using the *r.mess* addon as part of a modeling
workflow, see the tutorial [Species distribution modeling using Maxent
in GRASS GIS](https://ecodiv.earth/TutorialsNotes/sdmingrassgis/).

## AUTHOR

Paulo van Breugel, <https://ecodiv.earth> | HAS green academy University
of Applied Sciences | [Innovative Biomonitoring research
group](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/)
| [Climate-robust Landscapes research
group](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)
