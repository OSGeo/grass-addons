## DESCRIPTION

*i.lmf* calculates the Local maximum fitting of a temporal image series,
intially for vegetation indices, it also works for surface reflectance.

This is a first level port, only a fast fitting is done, see TODO.

The number of bands is potentially several years, **nfiles** and
**ndates** are respectively the number of pixels and the number of
pixels in a year.

## NOTES

Original links are found here SAWADA, 2001:
[http://www.affrc.go.jp/ANDES/sawady/index.html](https://web.archive.org/web/20110523233556/http://www.affrc.go.jp/ANDES/sawady/index.html)
NAGATANI et al., 2002:
[http://www.gisdevelopment.net/aars/acrs/2002/pos2/184.pdf](https://web.archive.org/web/20051222023531/http://www.gisdevelopment.net/aars/acrs/2002/pos2/184.pdf)
Yann Chemin and Kiyoshi Honda repaired it and ported it from SGI/OpenMP
to Linux.
[http://www.rsgis.ait.ac.th/\~honda/lmf/lmf.html](https://web.archive.org/web/20070824132301/http://www.rsgis.ait.ac.th/~honda/lmf/lmf.html)

## TODO

Port the full detailed algorithm from Fortran, and vastly
unemcomber/clean it. It will make the algorithm must slower though,
gaining only a marginal fitting strength, for my actual experience with
VIs curves.

## SEE ALSO

*[r.series](https://grass.osgeo.org/grass-stable/manuals/r.series.html)*

## AUTHOR

Yann Chemin, International Rice Research Institute, The Philippines
