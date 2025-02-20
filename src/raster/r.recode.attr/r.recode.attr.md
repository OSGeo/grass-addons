## DESCRIPTION

The *r.recode.attr* plugin let you reclass/recode a raster layer based
on values specified in a csv table.The module requires the first row of
the CSV file to contain column headers. The table must include at least
two columns: The first column corresponds to the raster values (or a
subset of them). The remaining columns contain the reclassification
values, which can be either integers or floating-point numbers.

For each column in the csv file (except the first one) new raster map
will be created, replacing the raster values corresponding to the first
column with those in the second (3rd, 4th, etc) column.

Users can define custom names for the output map(s). If only one output
name is provided and the CSV file contains more than two columns, the
module will automatically generate output names by appending the column
names to the provided base name.

## EXAMPLES

The example uses the basic North Caroline dataset. You can download it
from ([here](https://grass.osgeo.org/download/data/)). Alternatively,
you can install in directly from within GRASS using the "Download sample
project" option in the Data panel. Inspect the categories of the
*landuse* raster layer.

```sh
r.category map=landuse@PERMANENT
```

Based on the categories of the *landuse* layer, create a CSV file
*reclass.csv*. This table assigns a friction value and a suitability
value to each attribute.

```sh
cat <<EOL > reclass.csv
rasterID,friction,suitability
1,0.9,0
2,0.7,0.2
3,0.6,0.4
4,0.2,0.5
5,0.1,0.9
6,1,0
7,0.8,0
EOL
```

Use the *r.recode.attr* addon to generate two new raster layers, one for
friction and another for suitability. Specify a base name for the output
maps. Ensure that the **separator** matches the delimiter used in your
CSV file.

```sh
r.recode.attr input=landuse output=map rules=reclass.csv separator=comma
```

Note that the names of the two maps are constructed based on the
provided base name 'map' + name of the name of the column. Create for
both layers created above a color table.

```sh
r.colors map=map_friction color=oranges
r.colors map=map_suitability color=greens
```

The original land use map and the derived friction and suitability maps
are shown in the figure below.

[![image-alt](r_recode_attr_01.png)](r_recode_attr_01.png)  
*Figure 1: The A) friction and B) suitability maps, based on scores
assigned to each land use category of the landuse map.*

## SEE ALSO

*[r.reclass](https://grass.osgeo.org/grass-stable/manuals/r.reclass.html),
[r.recode](https://grass.osgeo.org/grass-stable/manuals/r.recode.html)*

## AUTHOR

Paulo van Breugel, <https://ecodiv.earth>, HAS green academy University
of Applied Sciences, [Innovative Biomonitoring research
group](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/),
[Climate-robust Landscapes research
group](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)
