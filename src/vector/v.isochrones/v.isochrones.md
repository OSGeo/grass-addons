## DESCRIPTION

*v.isochrones* creates a vector polygon map of isochrones
(**isochrones**) based on a roads map (**map**) with speed or cost
attribute (**cost\_column**), one or several starting points
(**start\_points**) and time steps (in minutes) for the isochrones
(**time\_steps**). The module is actually a front-end to different GRASS
GIS modules, and the user can chose the approach with the **method**
option (see the notes section for details).

The spatial precision of the analysis is defined by the current
computational region. The user can define this with
*[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)*.
Care should be taken to not define a too high resolution for the spatial
extent covered. Otherwise the user might be confronted with memory
issues.

## NOTES

Two approaches are currently implemented in the module:

The first (default) approach is based on
*[v.net.iso](https://grass.osgeo.org/grass-stable/manuals/v.net.iso.html)*.
The output of that module is then used to assign isochrone values to all
pixels based on the nearest road segment that is within a given distance
(**max\_distance**). The **-i** flag allows to calculate a separate
isochrone map for each starting point. For this approach, the input road
map currently has to be prepared by adding all nodes (using
*[v.net](https://grass.osgeo.org/grass-stable/manuals/v.net.html)* with
'operation=nodes' and the '-c' flag. For each starting point, the
algorithm then finds the closest node on the network and calculates the
isochrones from there. This allows to use the same network for many
analyses without having to go through the time of adding the starting
points at each run. In addition, a **cost\_column** has to be present in
the attribute table containing for each line segment the time of
traversal in minutes (i.e. length/speed).

The second approach is based on
*[r.cost](https://grass.osgeo.org/grass-stable/manuals/r.cost.html)*. It
transforms the roads to raster (here **cost\_column** has to point to an
attribute column containing speed in km/h), assigning a user chosen
**offroad\_speed** to all offroad pixels, calculates time cost from the
starting points and then transforms the result into discrete vector
polygons based on the time steps chosen. Optionally, the user can chose
to keep the a raster output of
*[r.cost](https://grass.osgeo.org/grass-stable/manuals/r.cost.html)*
(**timemap**). Current region settings are used to define the maximal
extension and the resolution at which the cost map is calculated. The
**memory** option allows to decide how much memory the
*[r.cost](https://grass.osgeo.org/grass-stable/manuals/r.cost.html)*
module can use (see the r.cost man page for more details). One big
advantage of the this second approach is that the road network does not
have to be topologically clean in order to get meaningful results.

## EXAMPLE

```sh
v.net -c input=roadsmajor operation=nodes output=myroads
v.db.addcolumn myroads col="speed int"
v.db.addcolumn myroads col="length double precision"
v.db.addcolumn myroads col="cost double precision"
v.db.update myroads col=speed value=120 where="ROAD_NAME='US-1'"
v.db.update myroads col=speed value=90 where="(ROAD_NAME like 'US%' AND ROAD_NAME <> 'US-1') OR ROAD_NAME like 'I-%'"
v.db.update myroads col=speed value=50 where="speed is null"
v.to.db myroads op=length col=length
v.db.update myroads col=cost qcol="(length/(speed*1000))*60"

g.region vector=myroads res=50 -a -p

echo "634637|224663" | v.in.ascii input=- output=start x=1 y=2

v.isochrones map=myroads cost_column=cost start_points=start isochrones=isochrones_vnetiso time_steps=15,30,60 \
    max_distance=1000 method=v.net.iso
```

![image-alt](v_isochrones_net.png)  
15, 30 and 60 minute isochrones from the start point using method
v.net.iso

```sh
v.isochrones map=myroads cost_column=speed start_points=start isochrones=isochrones_rcost time_steps=15,30,60 \
    method=r.cost memory=1000
```

![image-alt](v_isochrones_cost.png)  
15, 30 and 60 minute isochrones from the start point using method r.cost

## SEE ALSO

*[r.cost](https://grass.osgeo.org/grass-stable/manuals/r.cost.html),
[v.net.iso](https://grass.osgeo.org/grass-stable/manuals/v.net.iso.html)*

## AUTHOR

Moritz Lennert
