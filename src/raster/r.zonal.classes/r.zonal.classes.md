## DESCRIPTION

*r.zonal.classes* computes class proportions and majority class (mode)
of a "cover layer" (provided via the **raster** parameter) - e.g. a land
cover map - according to how it intersects with areas/objects in a "base
layer" (provided via the **zone\_map** parameter). Areas are defined by
adjacent pixels with the same value, such as those obtained with
*[r.clump](https://grass.osgeo.org/grass-stable/manuals/r.clump.html)*
or
*[i.segment](https://grass.osgeo.org/grass-stable/manuals/i.segment.html)*.

This function is similar to
*[r.stats.zonal](https://grass.osgeo.org/grass-stable/manuals/r.stats.zonal.html)*,
but is intended to be used on a categorical raster with integer values
(CELL type) instead of floating point as in *r.stats.zonal*.

## NOTES

The user can choose between output in the form of a vector map of the
areas contained in the "base layer" with the statistics of the "cover
layer" stored in the attribute table (the name of the vector layer
should be provided via the **vectormap** parameter) and/or in the form
of a CSV text file (the path to the file should be provided via the
**csvfile** parameter).

By default:

- the function compute the majority class as well as class proportions
    for each zone in the "base layer". If only the majority class or
    class proportion is needed, it can be specified by using the
    **statistics** parameter.
- the function provides the ratio of classes (total = 1) but the
    **-p** flag allows providing percentages (total = 100). The number
    of decimals is set to 5 by default and can be changed using the
    **decimals** parameter.
- the name of columns for proportions follows this logic : 'prop\_XX'
    where XX is the class of the "base layer". The user can add a prefix
    to proportion columns using the **prefix** parameter.
- the function works under the current computation region. The **-r**
    flag can be used to define the computational region based on the
    "base layer" for the processing.
- the function ignores NULL values in statistics computation. This
    behaviour can be reverted using the **-n** flag.
- the function provides proportion columns only for classes that
    actually exist in the "base layer" under the current computational
    region. This can create problems when the user run the function on
    different computational region with the aim to merge outputs at the
    end, because some classes could be present under some computational
    regions and absent on others. The **classes\_list** parameter and
    the **-l** flag allow to alleviate this issue. The **-l** flag force
    the output to provide statistics only for classes provided via the
    **classes\_list** parameter. When the **classes\_list** parameter is
    provided **without the -l flag**, the output will contain in
    addition to the classes that actually exist in the "base layer"
    under the current computational region (the default behaviour)
    columns for classes in the provided via the **classes\_list**
    parameter which will be filled with zero value. This is particularly
    useful when the function is used in multiple processing -
    sequentially or in parallel - to ensure all the output will have the
    same number (and order) of columns. Please notice that the
    computation of the mode is not affected by the list of classes
    provided in the **classes\_list** parameter.
- there is no check for the type of input's raster which is intended
    to be "CELL". This behaviour can be reversed using the **-c** flag.

## EXAMPLES

On North Carolina sample dataset:

```sh
# Define region
g.region raster=zipcodes

# Get majority class and class proportion of 'landuse96_28m'
# for each zone/object in 'zipcode' layer
r.zonal.classes zone_map=zipcodes raster=landuse96_28m csvfile=output.csv \
  vectormap=vect_output

# Display attributes table
v.db.select map=vect_output

cat mode    prop_0  prop_1   ...    prop_21
27511   18  0.00009 0.11286  ...    0.00000
27513   15  0.00000 0.06098  ...    0.00000
27518   15  0.00000 0.06455  ...    0.00000
27529   15  0.00000 0.24149  ...    0.00000
... ... ... ...  ...    ...

# Get only class proportion (not the mode), add prefix on columns and
# return proportion as percentages instead of the zone's area ratio
r.zonal.classes zone_map=zipcodes raster=landuse96_28m csvfile=output.csv \
  vectormap=vect_output prefix=lu statistics=proportion -p

# Display attributes table
v.db.select map=vect_output

cat lu_prop_0   lu_prop_1   ... lu_prop_21
27511   0.00851     11.28639    ... 0.00000
27513   0.00000     6.09839     ... 0.00000
27518   0.00000     6.45485     ... 0.00000
27529   0.00000     24.14926    ... 0.00000
... ...     ...     ...  ...

# Ensure that a column is created for class '1234' even if it doesn't exist
# under the current computational region
r.zonal.classes zone_map=zipcodes raster=landuse96_28m csvfile=output.csv \
  vectormap=vect_output prefix=lu classes_list='1234'

# Display attributes table
v.db.select map=vect_output

cat lu_mode lu_prop_0   ... lu_prop_21  lu_prop_1234
27511   18  0.00009     ... 0.00000     0.00000
27513   15  0.00000     ... 0.00000     0.00000
27518   15  0.00000     ... 0.00000     0.00000
... ... ...     ...  ...        ...

# Output only the proportion columns for classes '4,12,1234'
r.zonal.classes zone_map=zipcodes raster=landuse96_28m csvfile=output.csv \
  vectormap=vect_output classes_list='4,12,1234' -l

# Display attributes table
v.db.select map=vect_output

cat mode    prop_4      prop_12 prop_1234
27511   18  0.02310     0.00000 0.00000
27513   15  0.02888     0.00000 0.00000
27518   15  0.06291     0.00000 0.00000
27529   15  0.02579     0.00000 0.00000
... ... ...     ...  ...
```

### Acknowledgement

This work was funded by the Belgian Federal Science Policy Office
(BELSPO) (Research Program for Earth Observation [STEREO
III](https://eo.belspo.be/About/Stereo3.aspx), contract SR/00/304) as
part of the [MAUPP project](https://maupp.ulb.ac.be) and by [the
department of Geomatics of the Walloon
region](https://geoportail.wallonie.be) as part of the WALOUS project.

## SEE ALSO

*[r.stats.zonal](https://grass.osgeo.org/grass-stable/manuals/r.stats.zonal.html),
[r.univar](https://grass.osgeo.org/grass-stable/manuals/r.univar.html),
[v.rast.stats](https://grass.osgeo.org/grass-stable/manuals/v.rast.stats.html),
[i.segment.stats (Addon)](i.segment.stats.md),*

## AUTHOR

Tais GRIPPA - Universite Libre de Bruxelles. ANAGEO Lab.
