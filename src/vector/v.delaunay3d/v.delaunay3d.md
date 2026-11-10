## DESCRIPTION

*v.delaunay3d* performs 3D Delaunay triangulation on input 3D vector
point map. Resultant facets (ie. triangles) of tetrahedral network (TEN)
are written as faces to the output vector map. If **-l** flag is given,
the module writes edges of the network as lines instead of faces. By
**-p** flag the user can perform plain 3D triangulation instead of
Delaunay triangulation. In the plain triangulation the facets depends on
the insertion order of the vertices.

## NOTES

3D triangulation is performed by the [CGAL](https://www.cgal.org)
library.

Centroids are treated as points when reading data from the input vector
map. Note that input vector map must be 3D, the output is always 3D.

## EXAMPLE

```sh
# generate random 3D points
v.random out=rp n=100 zmax=100 -z
# perform 3D triangulation
v.delaunay3d input=rp output=rp_ten
...
Number of vertices: 100
Number of edges: 626
Number of triangles: 1019
Number of tetrahedrons: 492
```

## REFERENCES

- [CGAL 4.2 - 3D
    Triangulations](https://doc.cgal.org/4.2/CGAL.CGAL.3D-Triangulations/html/index.html)

## SEE ALSO

*[v.delaunay](https://grass.osgeo.org/grass-stable/manuals/v.delaunay.html)*

## AUTHOR

Martin Landa, Czech Technical University in Prague, Czech Republic
