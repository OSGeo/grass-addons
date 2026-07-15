## DESCRIPTION

*v.label.sa* makes a label-file from a GRASS vector map with labels
created from attributes in the attached table. The labels are placed in
as optimal place as possible. The label file has the same syntax as the
one created by
[v.label](https://grass.osgeo.org/grass-stable/manuals/v.label.html)

## EXAMPLE

North Carolina example:

```sh
# get font names:
d.font -L

v.label.sa roadsmajor labels=roads_labels column=ROAD_NAME color=red \
           background=white size=250 font=Vera

# set region:
g.region raster=lsat7_2002_10 -p

# display:
d.rgb b=lsat7_2002_10 g=lsat7_2002_20 r=lsat7_2002_30
d.vect roadsmajor col=yellow
d.labels roads_labels
```

![image-alt](v_label_sa.jpg)  
*Road labeling with v.label.sa (Raleigh, North Carolina, USA, area)*

## REFERENCES

Edmondson, Christensen, Marks and Shieber: A General Cartographic
Labeling Algorithm, Cartographica, Vol. 33, No. 4, Winter 1996, pp.
13-23 The algorithm works by the principle of Simulated Annealing.

## SEE ALSO

*[d.labels](https://grass.osgeo.org/grass-stable/manuals/d.labels.html),
[v.label](https://grass.osgeo.org/grass-stable/manuals/v.label.html),
[ps.map](https://grass.osgeo.org/grass-stable/manuals/ps.map.html)  
[Wikipedia article on simulated
annealing](https://en.wikipedia.org/wiki/Simulated_Annealing)*  

## AUTHOR

Wolf Bergenheim
