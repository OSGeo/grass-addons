## DESCRIPTION

The *v.class.mlpy* module is a tool for supervised vector
classification. It is built on top of the Python *mlpy* library
\[Albanese2012\]. The classification is based on attribute values. The
geometry is not taken into account, so the module does not depend on the
feature types used in the map. The classification is supervised, so the
training dataset is always required.

The attribute table of training map (dataset) has to contain a column
with the class. Required type of class column is integer. Expected type
of other columns is double or integer.

## NOTES

This module requires the user to have *mlpy* library installed. However,
this is not an issue because *mlpy* library is free and open source and
can be quickly downloaded and installed. Furthermore, library is
available for all major platforms supported by GRASS GIS. You find
*mlpy* download and installation instructions at the official *mlpy*
website (<https://mlpy.sourceforge.net/>).

## EXAMPLE

This is an example in a North Carolina sample dataset. It uses several
raster maps and generates (spatially) random vector data for
classification from raster maps. The random data used as input to the
classification and represent training dataset and dataset to be
classified in the real use case.

Two sets of random points are generated containing 100 and 1000 points.
Then, an attribute table is created for both maps and attributes are
derived from digital values of raster maps (Landsat images) at points
locations. These attribute table columns are input to the
classification. The smaller dataset is used as training dataset. Classes
are taken from the raster map which is a part of the sample dataset as
an example result of some former classification. The number of classes
in training dataset is 6.

```sh
# the example code uses unix-like syntax for continuation lines, for-loops,
# variables and assigning command outputs to variables

# generate random points to be used as an input
v.random output=points_unknown n=1000
v.db.addtable map=points_unknown

# generate random points to be used as a training dataset
v.random output=points_known n=100
v.db.addtable map=points_known

# fill attribute tables
MAPS=$(g.list type=rast pattern="lsat*" exclude="*87*" mapset=PERMANENT sep=" ")
let NUM=0
for MAP in $MAPS
do
let NUM++
    v.db.addcolumn map=points_unknown layer=1 columns="map_$NUM integer"
    v.db.addcolumn map=points_known layer=1 columns="map_$NUM integer"
    v.what.rast map=points_unknown layer=1 raster=$MAP column=map_$NUM
    v.what.rast map=points_known layer=1 raster=$MAP column=map_$NUM
done

# fill the class (category) column with correct values for training dataset
v.db.addcolumn map=points_known layer=1 columns="landclass integer"
v.what.rast map=points_known layer=1 raster=landclass96 column=landclass

# TODO: syntax in the setting of color tables is strange, fix example
# set color table
r.colors.out map=landclass96 rules=tmp_color_rules_file \
| v.colors map=points_known column=landclass layer=1 rules=tmp_color_rules_file
rm tmp_color_rules_file

# do the classification
v.class.mlpy input=points_unknown training=points_known class_column=landclass

# set color table
r.colors.out map=landclass96 rules=tmp_color_rules_file \
| v.colors map=points_unknown column=landclass layer=1 rules=tmp_color_rules_file
rm tmp_color_rules_file
```

## SEE ALSO

*[v.class](https://grass.osgeo.org/grass-stable/manuals/v.class.html)*
for unsupervised attributes classification,
*[v.to.db](https://grass.osgeo.org/grass-stable/manuals/v.to.db.html)*
for populating attribute values from vector features,
*[v.what.rast](https://grass.osgeo.org/grass-stable/manuals/v.what.rast.html)*
for uploading raster values to attribute columns,
*[v.rast.stats](https://grass.osgeo.org/grass-stable/manuals/v.rast.stats.html)*
for uploading raster statistics to attribute columns,
*[v.class.ml](v.class.ml.md)* for a more powerful vector classification
module which uses *scikit-learn*

## REFERENCES

D. Albanese, R. Visintainer, S. Merler, S. Riccadonna, G. Jurman, C.
Furlanello. *mlpy: Machine Learning Python*, 2012.
[arXiv:1202.6548](http://arxiv.org/abs/1202.6548)

## AUTHOR

Vaclav Petras, [Czech Technical University in
Prague](https://www.cvut.cz), Czech Republic
