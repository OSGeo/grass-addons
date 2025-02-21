## DESCRIPTION

*r.surf.nnbathy* is an interface between the external *nnbathy* utility
and *GRASS*. *nnbathy* is a surface interpolation program provided with
[nn](https://github.com/sakov/nn-c) - a natural neighbor interpolation
library, written by Pavel Sakov.

*r.surf.nnbathy* provides 3 interpolation algorithms. According to *nn*
library documentation these are: Delaunay interpolation (**alg=l**),
Watson's algortithm for Sibson natural neighbor interpolation
(**alg=nn**) and Belikov and Semenov's algorithm for non-Sibsonian
natural neighbor interpolation (**alg=ns**). For performing the
underlaying Delaunay triangulation in all cases *nnbathy* uses
*triangle* software by [Jonathan Richard
Shewchuk](http://www.cs.berkeley.edu/~jrs/).

The **output** raster map is a continous surface interpolated from the
**input** data.

## NOTES

*nnbathy*, if built with '-DNN\_SERIAL' (default as of nn 1.85), is able
to create a grid of virtually any size. It interpolates and writes one
output point at a time only. This eliminates the necessity to hold the
whole output array in memory. However, even then all the input points
are still held in the memory.

1. Requires *GRASS* 7 and *nnbathy* 1.76 or greater.
2. Build *nnbathy* according to instructions provided with its source
    code and put it somewhere in your $PATH.
3. The output raster map extent and resolution match the region
    settings at which the script was started.
4. The output raster map non-NULL area is limited to the convex hull
    encompassing all the non-NULL input cells.
5. The output is double precision floating point raster map (DCELL).
6. Natural neighbor is a an *exact* interpolation algorithm, so all
    non-NULL input points have their value exactly preserved in the
    output.
7. There is circa 0.2 KB memory overhead per each *input* cell.
    However, the *output* grid can be of any size, if *nnbathy* is built
    with -DNN\_SERIAL switch.
8. *r.surf.nnbathy* creates 3 temporary files: ASCII x,y,z lists of the
    input points and output cells, and the output list converted into
    GRASS ASCII format. Then it makes a GRASS raster map from the latter
    - and only then it removes the 3 temp files, when the script
    terminates. Thus, at the script run time several times more disk
    space might be required, than the final GRASS raster map would
    actually occupy.

## EXAMPLE

```sh
g.region raster=elevation@PERMANENT -p
r.random input=elevation@PERMANENT n=100000 raster_output=random_points
r.surf.nnbathy input=random_points output=raster_map
d.rast map=raster_map
```

## REQUIREMENTS

- [nnbathy](https://github.com/sakov/nn-c) library by Pavel Sakov
- *[v.surf.nnbathy](v.surf.nnbathy.md)*

## SEE ALSO

*[v.surf.nnbathy](v.surf.nnbathy.md)*

## AUTHOR

Adam Laza, OSGeoREL, Czech Technical University in Prague (mentor:
Martin Landa)

based on v.surf.nnbathy from GRASS 6 by  
Hamish Bowman, Otago University, New Zealand  
Based on *r.surf.nnbathy* by Maciej Sieczka
