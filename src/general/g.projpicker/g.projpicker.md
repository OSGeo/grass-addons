## DESCRIPTION

*g.projpicker* queries projections spatially. It is a wrapper that
invokes [the ProjPicker module](https://pypi.org/project/projpicker/)
internally. Check [its
documentation](https://projpicker.readthedocs.io/) for more details
including
[installation](https://projpicker.readthedocs.io/en/latest/getting_started/installation.html)
and [the query
syntax](https://projpicker.readthedocs.io/en/latest/getting_started/query_syntax.html).

## NOTES

A query string can be read from one of the **coordinates** (with
**operator**), **query**, and **input** options, but not from more than
one source. When an **input** file is used, one keyword or one geometry
must be defined per line. Otherwise, invalid lines will be ignored. The
*-p* flag can be used to validate the query syntax.

### Coordinate systems

The projection of the current GRASS location is not used for queries.
Instead, non-latitude/longitude coordinates are considered x and y in an
unknown unit that needs to be queried. The **coordinates** option takes
longitude,latitude (without the **-l** flag) or latitude,longitude pairs
(with the **-l** flag) in degrees. To use x-y coordinates, either the
**query** or **input** option must be used. Two keywords (*latlon* and
*xy*) can be used to switch between coordinate systems. By default,
*latlon* is assumed and longitude,latitude as in the **coordinates**
options is not supported in the **query** and **input** options. The
query syntax is case-sensitive.

### Coordinate formats

Various coordinate formats are supported. For the *latlon* coordinate
system, the following points are all identical:

```sh
################################
# decimal degrees and separators
################################
34.2348,-83.8677   # comma
34.2348 -83.8677   # whitespace

####################################################
# degree, minute, and second symbols
# degree: ° (U+00B0, &deg;, alt+0 in xterm), o, d
# minute: ' (U+0027, '), ′ (U+2032, &prime;), m
# second: " (U+0022, "), ″ (U+2033, &Prime;),
#         '' (U+0027 U+0027, ' '), s
####################################################
34.2348°      -83.8677°       # without minutes, seconds, and [SNWE]
34°14.088'    -83°52.062'     # without seconds and [SNWE]
34°14'5.28"   -83°52'3.72"    # without [SNWE]
34.2348°N     83.8677°W       # without minutes and seconds
34°14.088'N   83°52.062'W     # without seconds
34°14'5.28"N  83°52'3.72"W    # full
34°14′5.28″N  83°52′3.72″W    # full using U+2032 and U+2033
34o14'5.28''N 83o52'3.72''W   # full using o' and ''
34d14m5.28sN  83d52m3.72sW    # full using dms
34:14:5.28N   83:52:3.72W     # full using :
34:14:5.28    -83:52:3.72     # without [SNWE]
34:14.088     -83:52.062      # without seconds and [SNWE]
```

Any geometries following the *xy* keyword are in the *xy* coordinate
system in an unknown unit. For example,

```sh
xy
396255,1374239
396255 1374239
```

### Units

The *unit=* keyword can be used to restrict queries to a specific unit.
By default, it is set to *unit=any* and the full list of supported units
is as follows:

  - degree
  - degree minute second hemisphere
  - grad
  - meter
  - kilometer
  - 50 kilometers
  - 150 kilometers
  - link
  - foot
  - US foot
  - British foot (1936)
  - British foot (Sears 1922)
  - British yard (Sears 1922)
  - British chain (Benoit 1895 B)
  - British chain (Sears 1922 truncated)
  - British chain (Sears 1922)
  - Clarke's link
  - Clarke's foot
  - Clarke's yard
  - German legal meter
  - Gold Coast foot
  - Indian yard (1937)
  - Indian yard

Most commonly used units include *degree*, *meter*, and *US foot*.

### Geometry types

Three geometry types including *point*, *poly*, and *bbox* are
supported. Both lines and boundaries are supported by the same *poly*
geometry type. Regardless of the coordinate system, *bbox* geometries
always take the south, north, west, and east coordinates in that order
of a bounding box.

See the following example:

```sh
# point geometry
# starts in latlon
point
10,20
xy
3,4

# poly 1
latlon
poly
10,20
30,40
# poly 2 in xy
# new coordinate system always starts a new geometry
xy
5,6
7,8
# comment ignored and poly 2 continues
9,10

# but not this one because there is a blank line above
# start poly 3
11,12
13,14

# bbox
latlon
bbox
10,20,30,40
xy
5,6,7,8
```

The above **input** file is parsed to:

```sh
['point',
 [10.0, 20.0],
 'xy',
 [3.0, 4.0],
 'latlon',
 'poly',
 [[10.0, 20.0], [30.0, 40.0]],
 'xy',
 [[5.0, 6.0], [7.0, 8.0], [9.0, 10.0]],
 [[11.0, 12.0], [13.0, 14.0]],
 'latlon',
 'bbox',
 [10.0, 20.0, 30.0, 40.0],
 'xy',
 [5.0, 6.0, 7.0, 8.0]]
```

### Logical operators

The **operator** option sets a global logical operator that will be
performed on all geometries in the **coordinates** option. It includes
set-theoretic *and*, *or*, and *xor*.

The **query** and **input** options support [the full query
syntax](https://projpicker.readthedocs.io/en/latest/query_syntax.html)
including *and*, *or*, *xor*, and *not* in the *postfix* query mode.
Unless the query mode is *postfix*, only one of *and*, *or*, or *xor*
must be given as the first word.

This query string performs the AND of all geometries A, B, C, and D, and
returns projections that completely contain all of them:

```sh
and
# A, B, C, or D can be point, poly, or bbox individually
A
B
C
D
```

This query string performs the OR of all geometries and returns
projections that completely contain any of them:

```sh
or
# A, B, C, or D can be point, poly, or bbox individually
A
B
C
D
```

This query string performs the XOR of two geometries and returns
projections that completely contain only one of them:

```sh
xor
# A or B can be point, poly, or bbox individually
A
B
```

Since the XOR operator is performed on two geometries at a time, feeding
more than two geometries does not return mutually exclusive projections.
For example, this query string returns projections that contain only A,
B, or C exclusively, and additionally all three geometries:

```sh
xor
# A, B, or C can be point, poly, or bbox individually
A
B
C
```

### Postfix logical operations

If the first word is *prefix* in the query string, *and*, *or*, *xor*,
*not*, and *match* operations can be performed in a postfix notation.

This query string returns all projections that completely contain
geometry A, but not B:

```sh
postfix
A       # find A
B       # find B
not     # complement of B
and     # A and not B
```

This query string returns all projections that contain A or B, but not
C: A, but not B:

```sh
postfix
A       # find A
B       # find B
or      # A or B
C       # find C
not     # complement of C
and     # (A or B) and not C
```

This query string returns all projections that contain both A and B, but
not C; or those that contain C, but neither A nor B:

```sh
postfix
A       # find A
B       # find B
and     # A and B
C       # find C
xor     # (A and B) xor C
```

This query string returns all projections that contain only one of A, B,
or C exclusively:

```sh
postfix
A       # find A
B       # find B
xor     # A xor B
C       # find C
xor     # A xor B xor C
A       # find A again
B       # find B again
and     # A and B
C       # find C again
and     # A and B and C
not     # not (A and B and C)
and     # (A xor B xor C) and not (A and B and C)
```

### Special geometries for logical operations

A *none* is an empty geometry and an *all* is everything. These special
geometries are useful to manipulate existing projection sets.

This query string ignores all results above *none* and returns those
projections that only contain X:

```sh
postfix
A       # find A
B       # find B
or      # A or B
C       # find C
not     # complement of C
and     # (A or B) and not C
none    # empty
and     # ((A or B) and not C) and empty = empty
X       # find X
or      # empty or X = X
```

This query string returns all projections not in degree that contain A:

```sh
postfix
A               # find A
unit=degree     # restrict queries to degree unit
all             # find all projections in degree

unit=any        # back to all units; without this, the following NOT operation
                # would be performed in the degree-unit universe and return
                # nothing because the NOT of all in the same universe is none

not             # complement of (all projections in degree) in the any-unit
                # universe; that is, all projections not in degree

and             # A and (all projections not in degree);
                # all projections not in degree that contain A
```

This query string returns all projections in *xy* that contain A that
can be transformed to B in EPSG:4326 within a *match\_tol* distance
tolerance in *xy* (default 1):

```sh
postfix
match_tol=200   # error tolerance in an xy unit for distance matching
A               # known coordinates in an unknown projection and unit
latlon
B               # known coordinates in latlon that should match A
match           # find projections in xy that contain A that matches B in latlon
```

This operator requires the [pyproj](https://pypi.org/project/pyproj/)
module and is slow because it has to transform B to many projections
that contain both A and B. To save time and just return the first match,
use *match\_max* (default 0 for all):

```sh
postfix
match_tol=200   # error tolerance in an xy unit for distance matching
match_max=1     # return the first match only and quit
A               # known coordinates in an unknown projection and unit
latlon
B               # known coordinates in latlon that should match A
match           # find projections in xy that contain A that matches B in latlon
```

### Geometry variables

Geometry variables can be used to store a geometry. The name of a
variable must consist of lowercase and uppercase letters, numbers, and
underscores. If the variable name starts with one of these characters
and ends with a colon, it stores the following geometry and is not used
immediately. If the variable name starts with a colon followed by these
characters, the geometry stored in the variable is restored. If the
variable name starts and ends with a colon, the following geometry is
stored and used immediately.

See the following example:

```sh
postfix
# define city geometries, but not used immediately
city_A:
A
city_A:
B
city_C:
C
city_X:
X

# start query
:city_A
:city_B
or
:city_C
not
and
:no_where: # saved and used immediately
and
:city_X
or
```

### Multiple items in one line

Multiple items can be specified in one line separated by whitespaces.
When there are whitespaces in one item, it needs to be enclosed between
single or double quotes. Two numbers in *latlon* or *xy*, or four
numbers in *bbox* are treated as a single item, so they don't need
quotes unless they are separated by whitespaces.

See the following example:

```sh
point 10,20 xy 3,4
# use a space-comma-space to start a new poly
latlon poly 10,20 "30 40" xy 5,6 7,8 9,10 , 11,12 13,14
latlon bbox 10,20,30,40 xy 5,6,7,8
```

### Output schema

The output schema for the *sqlite* **format** is as follows:

```sh
CREATE TABLE bbox (
    proj_table TEXT NOT NULL CHECK (length(proj_table) >= 1),
    crs_name TEXT NOT NULL CHECK (length(crs_name) >= 2),
    crs_auth_name TEXT NOT NULL CHECK (length(crs_auth_name) >= 1),
    crs_code TEXT NOT NULL CHECK (length(crs_code) >= 1),
    usage_auth_name TEXT NOT NULL CHECK (length(usage_auth_name) >= 1),
    usage_code TEXT NOT NULL CHECK (length(usage_code) >= 1),
    extent_auth_name TEXT NOT NULL CHECK (length(extent_auth_name) >= 1),
    extent_code TEXT NOT NULL CHECK (length(extent_code) >= 1),
    south_lat FLOAT CHECK (south_lat BETWEEN -90 AND 90),
    north_lat FLOAT CHECK (north_lat BETWEEN -90 AND 90),
    west_lon FLOAT CHECK (west_lon BETWEEN -180 AND 180),
    east_lon FLOAT CHECK (east_lon BETWEEN -180 AND 180),
    bottom FLOAT,
    top FLOAT,
    left FLOAT,
    right FLOAT,
    unit TEXT NOT NULL CHECK (length(unit) >= 2),
    area_sqkm FLOAT CHECK (area_sqkm > 0),
    CONSTRAINT pk_bbox PRIMARY KEY (
        crs_auth_name, crs_code,
        usage_auth_name, usage_code
    ),
    CONSTRAINT check_bbox_lat CHECK (south_lat >= north_lat)
)
```

For the other output **format**s, the column names are used as keys.

## EXAMPLES

### Simple queries

This command finds projections that completely contain both points at
34.2348,-83.8677 and 33.7490,-84.3880 in *latlon*:

```sh
g.projpicker -l 34.2348,-83.8677,33.7490,-84.3880
```

This command finds projections that completely contain two poly
geometries separated by a comma:

```sh
g.projpicker query="poly -10,0 10,0 10,10 10,0 , 10,20 30,40"
```

This command finds projections that completely contain two bounding
boxes in bottom, top, left, and right:

```sh
g.projpicker query="bbox 0,0,10,10 20,20,50,50"
```

### Finding missing projection

Some GIS data is missing projection information. In this example, we
have a shapefile without its .PRJ file, so we don't have the correct
projection. We just know the general location of this data (Atlanta, GA
or 33.7490°N,84.3880°W). We can still check the *xy* extent of the data
in an unknown projection and unit (1323252,1374239,396255,434290 in
SNWE). Let's figure out what the projections of the data can be:

```sh
g.projpicker query="33.7490°N,84.3880°W xy bbox 1323252,1374239,396255,434290"
```

### Matching coordinates

In this example, we know the *xy* coordinates of a location
(432697.24,1363705.31) in an unknown projection and its name (Georgia
State Governor's Office). We can search for its approximate longitude
and latitude by name (33.7490, -84.3880). Let's find out the correct
projection of the *xy* data with an error tolerance of 200 unknown *xy*
units for distance matching:

```sh
g.projpicker query="postfix match_tol=200 33.7490,-84.3880 xy 432697.24,1363705.31 match"
```

This process is slow because it has to transform the geometry in
*latlon* to many different projections. Just to return the first match
to save time:

```sh
g.projpicker query="postfix match_max=1 match_tol=200 33.7490,-84.3880 xy 432697.24,1363705.31 match"
```

### Set-theoretic logical queries using postfix

These equivalent commands find projections in US foot that contains
34.2348,-83.8677, but not 33.7490,-84.3880 in *latlon*:

```sh
# since the unit name "US foot" contains a space and statements are separated
# by whitespaces, it needs to be surrounded by single or double quotes when
# it's passed from the command line
g.projpicker query="postfix unit='US foot' 34.2348,-83.8677 33.7490,-84.3880 not and"

g.projpicker query="postfix unit='US foot' '34.2348 -83.8677' '33.7490 -84.3880' not and"

g.projpicker input=- <<EOT
postfix
unit=US foot    # in this case, quotes are optional because this statement is
                # not followed by other items
34.2348,-83.8677
33.7490,-84.3880
not
and
EOT

g.projpicker input=- <<EOT
postfix
unit=US foot
34.2348 -83.8677
33.7490 -84.3880
not
and
EOT

g.projpicker input=- <<EOT
postfix unit="US foot" 34.2348,-83.8677 33.7490,-84.3880 not and
EOT

g.projpicker input=- <<EOT
postfix
unit=US foot
A: 34.2348,-83.8677
B: 33.7490,-84.3880

:A :B not and
EOT
```

### GUI

Start the GUI for selecting projections using the **-g** flag:

```sh
g.projpicker -g query="postfix 34.2348,-83.8677 33.749,-84.388 not and"
```

![image-alt](g_projpicker_gui.png)

## AUTHOR

[Huidae Cho](mailto:grass4u@gmail-com)
