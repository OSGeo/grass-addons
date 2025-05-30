## DESCRIPTION

*v.vect.stats.multi* computes attribute statistics of points in vector
map *points* falling into each area in vector map *areas*. The results
are uploaded to the attribute table of the vector map *areas*.

By default, statistics are computed for all integer and floating point
attributes (columns), e.g., DOUBLE PRECISION and INTEGER columns will be
used, but TEXT will not. Specific (multiple) columns can be selected
using **points\_columns**. The type of the selected columns again need
to be some integer and floating point type.

### Statistical methods

Using numeric attribute values of all points falling into a given area,
a new value is determined with the selected method.

*v.vect.stats* can perform the following operations:

- **sum**  
    The sum of values.
- **average**  
    The average value of all point attributes (sum / count).
- **median**  
    The value found half-way through a list of the attribute values,
    when these are ranged in numerical order.
- **mode**  
    The most frequently occurring value.
- **minimum**  
    The minimum observed value.
- **maximum**  
    The maximum observed value.
- **range**  
    The range of the observed values.
- **stddev**  
    The statistical standard deviation of the attribute values.
- **variance**  
    The statistical variance of the attribute values.
- **diversity**  
    The number of different attribute values.

The count (number of points) is always computed and stored in
**count\_column**.

### Column names

The **stats\_columns** can be used to provide custom column names
instead of the generated ones. If provided, the number of columns must
be number of **points\_columns** times number of methods requested (in
**method**). The order of names is that first come all statistics for
one column, then all statistics for another column, etc. If only one
statistical method is requested, then it is simply one column from
**points\_columns** after another. Note that the number of names
**stats\_columns** is checked against the number of columns that will be
created. However, whether the names correspond to what is being computed
for the columns cannot be checked, so, for example, providing names for
one statistic for all columns, followed by another statistic, etc. will
result in a mismatch between column names and what was actually
computed.

## NOTES

This module is using
*[v.vect.stats](https://grass.osgeo.org/grass-stable/manuals/v.vect.stats.html)*
underneath to do the actual statistical computations. See *v.vect.stats*
for details about behavior in special cases.

## EXAMPLES

### ZIP codes and POIs

The following example is using points of interest (POIs) and ZIP code
areas vector from the basic North Carolina sample database: Create a
copy of ZIP code areas in the current mapset to allow for adding
attributes (using a name which expresses what you will add later on):

```sh
g.copy vector=zipcodes@PERMANENT,zipcodes_with_poi_stats
```

Compute minimum and maximum for each numerical colum in the attribute
table of points of interest:

```sh
v.vect.stats.multi points=points_of_interest areas=zipcodes_with_poi_stats method=minimum,maximum count_column=point_count
```

Use *v.info* to see all the newly created columns:

```sh
v.info -c map=zipcodes_with_poi_stats
```

Use *v.db.select* (or GUI) to examine the values (you can see subset of
the data by selecting only specific columns or using the where cause to
get only certain rows):

```sh
v.db.select map=zipcodes_with_poi_stats
```

Each of the new columns separately can be assigned color using
*v.colors*:

```sh
v.colors map=zipcodes_with_poi_stats use=attr column=elev_m_maximum color=viridis rgb_column=elev_m_maximum_color
```

### Specifying columns by name

Assuming a similar setup as in the previous example (*g.copy* used to
create a copy in the current mapset), you can ask for statistics only on
columns PUMPERS, TANKER, and AERIAL and specify the names of new columns
using: (wrapping a long line here using Bash-like syntax):

```sh
v.vect.stats.multi points=firestations areas=zipcodes method=sum \
    count_column=count point_columns=PUMPERS,TANKER,AERIAL \
    stats_columns=all_pumpers,all_tankers,all_aerials
```

## SEE ALSO

- *[v.vect.stats](https://grass.osgeo.org/grass-stable/manuals/v.vect.stats.html)*
    for printing information instead of storing it in the attribute
    table,
- *[v.what.rast.multi](v.what.rast.multi.md)* for querying multiple
    raster maps by one vector points map,
- *[g.copy](g.copy.md)* for creating a copy of vector map to update
    (to preserve the original data given that this module performs a
    large automated operation).

## AUTHOR

Vaclav Petras, [NCSU Center for Geospatial
Analytics](https://cnr.ncsu.edu/geospatial)
