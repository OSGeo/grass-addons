## DESCRIPTION

*v.net.curvedarcs* is a frontend to
*[v.net](https://grass.osgeo.org/grass-stable/manuals/v.net.html)* and
*[v.segment](https://grass.osgeo.org/grass-stable/manuals/v.segment.html)*
that creates curved arcs between given start and end points. The user
provides a point vector map and a text file (see Notes section) with
start and end point categories as well as a flow volume for this link
which will be transferred to the attribute table of the curved arcs.

The user can determine the nature of the curve with the
*minimum\_offset* and *maximum\_offset* parameters. The longest curve's
maximum offset from a straight line is equal to the value of
*maximum\_offset* in map units. The other curves maximum offset from a
straight line is calulated as length(x)/max\_length \* max\_offset. In
other words, shorter lines are less curved than longer lines. However,
any line's maximum offset is always at least *minimum\_offset* from the
straight line.

## NOTES

## EXAMPLE

TODO

```sh
v.extract census_wake2000 cat=1,52,70,99,101 type=centroid out=tmp
v.type tmp from=centroid to=point out=points
echo >> flows.txt << EOF
> from,to,volume
> 52,1,100
> 1,52,50
> 70,1,50
> 1,70,50
> 99,1,66
> 1,99,100
> 101,1,25
> 1,101,75
> EOF
v.net.curvedarcs in=points flow=flows.txt sep=comma out=flows minoff=0 maxoff=2000
d.vect map=flows display=shape,dir width_column=volume width_scale=0.05 size=10
d.vect map=points display=shape,cat fill_color=red icon=basic/circle label_bcolor=black label_size=12 yref=bottom
```

![image-alt](v_net_curvedarcs.png)  
The curved arcs with minimum offset = 150 and maximum offset = 2000

Using different amount of curvature:

```sh
v.net.curvedarcs in=points flow=flows.txt sep=comma out=flows minoff=150 maxoff=5000 --o
d.vect map=flows display=shape,dir width_column=volume width_scale=0.05 size=10
d.vect map=points display=shape,cat fill_color=red icon=basic/circle label_bcolor=black label_size=12 yref=bottom
```

![image-alt](v_net_curvedarcs2.png)  
The curved arcs with minimum offset = 0 and maximum offset = 5000

## SEE ALSO

*[v.net](https://grass.osgeo.org/grass-stable/manuals/v.net.html),
[v.segment](https://grass.osgeo.org/grass-stable/manuals/v.segment.html)*

## AUTHOR

Moritz Lennert, DGES-ULB
