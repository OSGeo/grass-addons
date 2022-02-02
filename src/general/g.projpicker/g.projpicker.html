<h2>DESCRIPTION</h2>

<em>g.projpicker</em> queries projections spatially. It is a wrapper that invokes
<a href="https://pypi.org/project/projpicker/">the ProjPicker module</a>
internally. Check <a href="https://projpicker.readthedocs.io/">its documentation</a>
for more details including
<a href="https://projpicker.readthedocs.io/en/latest/getting_started/installation.html">installation</a>
and <a href="https://projpicker.readthedocs.io/en/latest/getting_started/query_syntax.html">the query syntax</a>.

<h2>NOTES</h2>

A query string can be read from one of the <b>coordinates</b> (with
<b>operator</b>), <b>query</b>, and <b>input</b> options, but not from more
than one source. When an <b>input</b> file is used, one keyword or one geometry
must be defined per line. Otherwise, invalid lines will be ignored. The
<em>-p</em> flag can be used to validate the query syntax.

<h3>Coordinate systems</h3>

The projection of the current GRASS location is not used for queries. Instead,
non-latitude/longitude coordinates are considered x and y in an unknown unit
that needs to be queried. The <b>coordinates</b> option takes
longitude,latitude (without the <b>-l</b> flag) or latitude,longitude pairs
(with the <b>-l</b> flag) in degrees. To use x-y coordinates, either the
<b>query</b> or <b>input</b> option must be used. Two keywords (<em>latlon</em>
and <em>xy</em>) can be used to switch between coordinate systems. By default,
<em>latlon</em> is assumed and longitude,latitude as in the <b>coordinates</b>
options is not supported in the <b>query</b> and <b>input</b> options. The
query syntax is case-sensitive.

<h3>Coordinate formats</h3>

Various coordinate formats are supported. For the <em>latlon</em> coordinate
system, the following points are all identical:
<div class="code"><pre>
################################
# decimal degrees and separators
################################
34.2348,-83.8677   # comma
34.2348 -83.8677   # whitespace

####################################################
# degree, minute, and second symbols
# degree: &deg; (U+00B0, &amp;deg;, alt+0 in xterm), o, d
# minute: ' (U+0027, &apos;), &prime; (U+2032, &amp;prime;), m
# second: " (U+0022, &quot;), &Prime; (U+2033, &amp;Prime;),
#         '' (U+0027 U+0027, &apos; &apos;), s
####################################################
34.2348&deg;      -83.8677&deg;       # without minutes, seconds, and [SNWE]
34&deg;14.088'    -83&deg;52.062'     # without seconds and [SNWE]
34&deg;14'5.28"   -83&deg;52'3.72"    # without [SNWE]
34.2348&deg;N     83.8677&deg;W       # without minutes and seconds
34&deg;14.088'N   83&deg;52.062'W     # without seconds
34&deg;14'5.28"N  83&deg;52'3.72"W    # full
34&deg;14&prime;5.28&Prime;N  83&deg;52&prime;3.72&Prime;W    # full using U+2032 and U+2033
34o14'5.28''N 83o52'3.72''W   # full using o' and ''
34d14m5.28sN  83d52m3.72sW    # full using dms
34:14:5.28N   83:52:3.72W     # full using :
34:14:5.28    -83:52:3.72     # without [SNWE]
34:14.088     -83:52.062      # without seconds and [SNWE]
</pre></div>

Any geometries following the <em>xy</em> keyword are in the <em>xy</em>
coordinate system in an unknown unit. For example,
<div class="code"><pre>
xy
396255,1374239
396255 1374239
</pre></div>

<h3>Units</h3>

The <em>unit=</em> keyword can be used to restrict queries to a specific unit.
By default, it is set to <em>unit=any</em> and the full list of supported units
is as follows:
<ul>
<li>degree</li>
<li>degree minute second hemisphere</li>
<li>grad</li>
<li>meter</li>
<li>kilometer</li>
<li>50 kilometers</li>
<li>150 kilometers</li>
<li>link</li>
<li>foot</li>
<li>US foot</li>
<li>British foot (1936)</li>
<li>British foot (Sears 1922)</li>
<li>British yard (Sears 1922)</li>
<li>British chain (Benoit 1895 B)</li>
<li>British chain (Sears 1922 truncated)</li>
<li>British chain (Sears 1922)</li>
<li>Clarke's link</li>
<li>Clarke's foot</li>
<li>Clarke's yard</li>
<li>German legal meter</li>
<li>Gold Coast foot</li>
<li>Indian yard (1937)</li>
<li>Indian yard</li>
</ul>

Most commonly used units include <em>degree</em>, <em>meter</em>, and <em>US
foot</em>.

<h3>Geometry types</h3>

Three geometry types including <em>point</em>, <em>poly</em>, and <em>bbox</em>
are supported. Both lines and boundaries are supported by the same
<em>poly</em> geometry type. Regardless of the coordinate system, <em>bbox</em>
geometries always take the south, north, west, and east coordinates in that
order of a bounding box.

<p>See the following example:
<div class="code"><pre>
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
</pre></div>

The above <b>input</b> file is parsed to:
<div class="code"><pre>
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
</pre></div>

<h3>Logical operators</h3>

The <b>operator</b> option sets a global logical operator that will be
performed on all geometries in the <b>coordinates</b> option. It includes
set-theoretic <em>and</em>, <em>or</em>, and <em>xor</em>.

<p>The <b>query</b> and <b>input</b> options support
<a href="https://projpicker.readthedocs.io/en/latest/query_syntax.html">the full query syntax</a>
including <em>and</em>, <em>or</em>, <em>xor</em>, and <em>not</em> in the
<em>postfix</em> query mode. Unless the query mode is <em>postfix</em>, only
one of <em>and</em>, <em>or</em>, or <em>xor</em> must be given as the first
word.

<p>This query string performs the AND of all geometries A, B, C, and D, and
returns projections that completely contain all of them:
<div class="code"><pre>
and
# A, B, C, or D can be point, poly, or bbox individually
A
B
C
D
</pre></div>

<p>This query string performs the OR of all geometries and returns projections
that completely contain any of them:
<div class="code"><pre>
or
# A, B, C, or D can be point, poly, or bbox individually
A
B
C
D
</pre></div>

<p>This query string performs the XOR of two geometries and returns projections
that completely contain only one of them:
<div class="code"><pre>
xor
# A or B can be point, poly, or bbox individually
A
B
</pre></div>

<p>Since the XOR operator is performed on two geometries at a time, feeding
more than two geometries does not return mutually exclusive projections. For
example, this query string returns projections that contain only A, B, or C
exclusively, and additionally all three geometries:
<div class="code"><pre>
xor
# A, B, or C can be point, poly, or bbox individually
A
B
C
</pre></div>

<h3>Postfix logical operations</h3>

If the first word is <em>prefix</em> in the query string, <em>and</em>,
<em>or</em>, <em>xor</em>, <em>not</em>, and <em>match</em> operations can be
performed in a postfix notation.

<p>This query string returns all projections that completely contain geometry
A, but not B:
<div class="code"><pre>
postfix
A       # find A
B       # find B
not     # complement of B
and     # A and not B
</pre></div>

<p>This query string returns all projections that contain A or B, but not C:
A, but not B:
<div class="code"><pre>
postfix
A       # find A
B       # find B
or      # A or B
C       # find C
not     # complement of C
and     # (A or B) and not C
</pre></div>

<p>This query string returns all projections that contain both A and B, but not
C; or those that contain C, but neither A nor B:
<div class="code"><pre>
postfix
A       # find A
B       # find B
and     # A and B
C       # find C
xor     # (A and B) xor C
</pre></div>

<p>This query string returns all projections that contain only one of A, B, or
C exclusively:
<div class="code"><pre>
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
</pre></div>

<h3>Special geometries for logical operations</h3>

A <em>none</em> is an empty geometry and an <em>all</em> is everything. These
special geometries are useful to manipulate existing projection sets.

<p>This query string ignores all results above <em>none</em> and returns those
projections that only contain X:
<div class="code"><pre>
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
</pre></div>

<p>This query string returns all projections not in degree that contain A:
<div class="code"><pre>
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
</pre></div>

<p>This query string returns all projections in <em>xy</em> that contain A that
can be transformed to B in EPSG:4326 within a <em>match_tol</em> distance
tolerance in <em>xy</em> (default 1):
<div class="code"><pre>
postfix
match_tol=200   # error tolerance in an xy unit for distance matching
A               # known coordinates in an unknown projection and unit
latlon
B               # known coordinates in latlon that should match A
match           # find projections in xy that contain A that matches B in latlon
</pre></div>

<p>This operator requires the <a href="https://pypi.org/project/pyproj/">pyproj</a>
module and is slow because it has to transform B to many projections that
contain both A and B. To save time and just return the first match, use
<em>match_max</em> (default 0 for all):
<div class="code"><pre>
postfix
match_tol=200   # error tolerance in an xy unit for distance matching
match_max=1     # return the first match only and quit
A               # known coordinates in an unknown projection and unit
latlon
B               # known coordinates in latlon that should match A
match           # find projections in xy that contain A that matches B in latlon
</pre></div>

<h3>Geometry variables</h3>

Geometry variables can be used to store a geometry. The name of a variable must
consist of lowercase and uppercase letters, numbers, and underscores. If the
variable name starts with one of these characters and ends with a colon, it
stores the following geometry and is not used immediately. If the variable name
starts with a colon followed by these characters, the geometry stored in the
variable is restored. If the variable name starts and ends with a colon, the
following geometry is stored and used immediately.

<p>See the following example:
<div class="code"><pre>
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
</pre></div>

<h3>Multiple items in one line</h3>

Multiple items can be specified in one line separated by whitespaces. When
there are whitespaces in one item, it needs to be enclosed between single or
double quotes. Two numbers in <em>latlon</em> or <em>xy</em>, or four numbers
in <em>bbox</em> are treated as a single item, so they don't need quotes unless
they are separated by whitespaces.

<p>See the following example:
<div class="code"><pre>
point 10,20 xy 3,4
# use a space-comma-space to start a new poly
latlon poly 10,20 "30 40" xy 5,6 7,8 9,10 , 11,12 13,14
latlon bbox 10,20,30,40 xy 5,6,7,8
</pre></div>

<h3>Output schema</h3>

The output schema for the <em>sqlite</em> <b>format</b> is as follows:
<div class="code"><pre>
CREATE TABLE bbox (
    proj_table TEXT NOT NULL CHECK (length(proj_table) &gt;= 1),
    crs_name TEXT NOT NULL CHECK (length(crs_name) &gt;= 2),
    crs_auth_name TEXT NOT NULL CHECK (length(crs_auth_name) &gt;= 1),
    crs_code TEXT NOT NULL CHECK (length(crs_code) &gt;= 1),
    usage_auth_name TEXT NOT NULL CHECK (length(usage_auth_name) &gt;= 1),
    usage_code TEXT NOT NULL CHECK (length(usage_code) &gt;= 1),
    extent_auth_name TEXT NOT NULL CHECK (length(extent_auth_name) &gt;= 1),
    extent_code TEXT NOT NULL CHECK (length(extent_code) &gt;= 1),
    south_lat FLOAT CHECK (south_lat BETWEEN -90 AND 90),
    north_lat FLOAT CHECK (north_lat BETWEEN -90 AND 90),
    west_lon FLOAT CHECK (west_lon BETWEEN -180 AND 180),
    east_lon FLOAT CHECK (east_lon BETWEEN -180 AND 180),
    bottom FLOAT,
    top FLOAT,
    left FLOAT,
    right FLOAT,
    unit TEXT NOT NULL CHECK (length(unit) &gt;= 2),
    area_sqkm FLOAT CHECK (area_sqkm &gt; 0),
    CONSTRAINT pk_bbox PRIMARY KEY (
        crs_auth_name, crs_code,
        usage_auth_name, usage_code
    ),
    CONSTRAINT check_bbox_lat CHECK (south_lat &gt;= north_lat)
)
</pre></div>

For the other output <b>format</b>s, the column names are used as keys.

<h2>EXAMPLES</h2>

<h3>Simple queries</h3>

This command finds projections that completely contain both points at
34.2348,-83.8677 and 33.7490,-84.3880 in <em>latlon</em>:
<div class="code"><pre>
g.projpicker -l 34.2348,-83.8677,33.7490,-84.3880
</pre></div>

<p>This command finds projections that completely contain two poly geometries
separated by a comma:
<div class="code"><pre>
g.projpicker query="poly -10,0 10,0 10,10 10,0 , 10,20 30,40"
</pre></div>

<p>This command finds projections that completely contain two bounding boxes in
bottom, top, left, and right:
<div class="code"><pre>
g.projpicker query="bbox 0,0,10,10 20,20,50,50"
</pre></div>

<h3>Finding missing projection</h3>

Some GIS data is missing projection information. In this example, we have a
shapefile without its .PRJ file, so we don't have the correct projection. We
just know the general location of this data (Atlanta, GA or
33.7490&deg;N,84.3880&deg;W). We can still check the <em>xy</em> extent of the
data in an unknown projection and unit (1323252,1374239,396255,434290 in SNWE).
Let's figure out what the projections of the data can be:
<div class="code"><pre>
g.projpicker query="33.7490&deg;N,84.3880&deg;W xy bbox 1323252,1374239,396255,434290"
</pre></div>

<h3>Matching coordinates</h3>

In this example, we know the <em>xy</em> coordinates of a location
(432697.24,1363705.31) in an unknown projection and its name (Georgia State
Governor's Office). We can search for its approximate longitude and latitude by
name (33.7490, -84.3880). Let's find out the correct projection of the
<em>xy</em> data with an error tolerance of 200 unknown <em>xy</em> units for
distance matching:
<div class="code"><pre>
g.projpicker query="postfix match_tol=200 33.7490,-84.3880 xy 432697.24,1363705.31 match"
</pre></div>

<p>This process is slow because it has to transform the geometry in
<em>latlon</em> to many different projections. Just to return the first match
to save time:
<div class="code"><pre>
g.projpicker query="postfix match_max=1 match_tol=200 33.7490,-84.3880 xy 432697.24,1363705.31 match"
</pre></div>

<h3>Set-theoretic logical queries using postfix</h3>

These equivalent commands find projections in US foot that contains
34.2348,-83.8677, but not 33.7490,-84.3880 in <em>latlon</em>:
<div class="code"><pre>
# since the unit name "US foot" contains a space and statements are separated
# by whitespaces, it needs to be surrounded by single or double quotes when
# it's passed from the command line
g.projpicker query="postfix unit='US foot' 34.2348,-83.8677 33.7490,-84.3880 not and"

g.projpicker query="postfix unit='US foot' '34.2348 -83.8677' '33.7490 -84.3880' not and"

g.projpicker input=- &lt;&lt;EOT
postfix
unit=US foot    # in this case, quotes are optional because this statement is
                # not followed by other items
34.2348,-83.8677
33.7490,-84.3880
not
and
EOT

g.projpicker input=- &lt;&lt;EOT
postfix
unit=US foot
34.2348 -83.8677
33.7490 -84.3880
not
and
EOT

g.projpicker input=- &lt;&lt;EOT
postfix unit="US foot" 34.2348,-83.8677 33.7490,-84.3880 not and
EOT

g.projpicker input=- &lt;&lt;EOT
postfix
unit=US foot
A: 34.2348,-83.8677
B: 33.7490,-84.3880

:A :B not and
EOT
</pre></div>

<h3>GUI</h3>

Start the GUI for selecting projections using the <b>-g</b> flag:
<div class="code"><pre>
g.projpicker -g query="postfix 34.2348,-83.8677 33.749,-84.388 not and"
</pre></div>

<div align="center">
<img src="g_projpicker_gui.png" alt="GUI">
</div>

<h2>AUTHOR</h2>

<a href="mailto:grass4u@gmail com">Huidae Cho</a>
