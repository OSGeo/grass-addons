## DESCRIPTION

*v.surf.nnbathy* is an interface between the external *nnbathy* utility
and *GRASS*. *nnbathy* is a surface interpolation program provided with
[nn](https://github.com/sakov/nn-c) - a natural neighbor interpolation
library, written by Pavel Sakov.

*v.surf.nnbathy* provides 3 interpolation algorithms. According to *nn*
library documentation these are: Delaunay interpolation (**alg=l**),
Watson's algortithm for Sibson natural neighbor interpolation
(**alg=nn**) and Belikov and Semenov's algorithm for non-Sibsonian
natural neighbor interpolation (**alg=ns**). For performing the
underlaying Delaunay triangulation in all cases *nnbathy* uses
*triangle* software by [Jonathan Richard
Shewchuk](https://people.eecs.berkeley.edu/~jrs/).

The **output** raster map is a continous surface interpolated from the
**input** or **file** data.

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
8. *v.surf.nnbathy* creates 4 temporary files: ASCII x,y,z lists of the
    input points and output cells, and the output list converted into
    GRASS ASCII format. Then it makes a GRASS raster map from the latter
    - and only then it removes the 3 temp files, when the script
    terminates. Thus, at the script run time several times more disk
    space might be required, than the final GRASS raster map would
    actually occupy.

## EXAMPLE

```sh
g.region raster=elevationelev_lid792_randpts@PERMANENT -p
v.surf.nnbathy input=elevation_lid792_randpts@PERMANENT output=raster_map column=value
d.rast map=raster_map
```

## REQUIREMENTS

- [nnbathy](https://github.com/sakov/nn-c) library by Pavel Sakov

## SEE ALSO

*[r.surf.nnbathy](r.surf.nnbathy.md)*

## AUTHORS

Adam Laza, OSGeoREL, Czech Technical University in Prague (mentor:
Martin Landa) Corrected by Roberto Marzocchi,
<roberto.marzocchi@gter.it>

Based on v.surf.nnbathy from GRASS 6 by:  
Hamish Bowman, Otago University, New Zealand  
Based on *r.surf.nnbathy* by Maciej Sieczka
