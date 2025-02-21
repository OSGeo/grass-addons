## DESCRIPTION

*v.kriging* constructs 2D / 3D raster from the values located on
discrete points using interpolation method *ordinary kriging*. In order
to let the user decide on the process and necessary parameters, the
module performance is divided into three phases:

- **initial phase** computes experimental variogram.
  - Please set up a name of the **report file**. The file will be
        created automatically in working directory to enable import of
        parameters from current to following phases. If the file has
        been deleted during the module performance, the user is asked to
        start interpolation again from the initial phase.
  - Warning about particular point and "*less than 2 neighbours in
        its closest surrounding. The perimeter of the surrounding will
        be increased...*" indicates that variogram range should be
        shortened.
  - There will appear some temporary files during variogram
        computation. They will be deleted automatically in following
        phase. If missing, the user is asked to repeat initial phase.
  - It is not necessary to save experimental variogram plots. They
        just help to estimate parameters of theoretical variogram that
        will be computed in following step (output contains experimental
        and theoretical variogram plotted together).
- in the **middle phase**, the user estimates theoretical variogram
    setting up the range (if necessary, the sill and the nugget effect
    as well) to fit the experimental variogram from previous phase.
  - Default *sill* is calculated from variogram values, more details
        in (*Stopkova, 2014*).
  - Save horizontal and vertical variogram plots using
        *file=extension*.
  - Experimental anisotropic / bivariate variogram is plotted as a
        base for final theoretical variogram parameters estimation in
        final phase.
- **final phase** performs interpolation based on parameters of
    theoretical variogram.
  - Save anisotropic or bivariate variogram plot using
        *file=extension*.

## EXAMPLES

To get optimal results, it is necessary to test various initial
settings, anisotropic ratios and variogram functions. Input (2D or 3D
point layer) must contain values to be interpolated in the attribute
table.

### 3D kriging

General commands:

```sh
v.kriging phase=initial in=input_layer icol=name report=report_file.txt file=png
```

```sh
v.kriging in=input_layer phase=middle hz_fun=exponential vert_fun=exponential ic=name file=png  \
hz_range=double vert_range=double [hz_sill=double vert_sill=double hz_nugget=double vert_nugget=double] -u
```

```sh
v.kriging in=input_layer phase=final final_fun=exponential final_range=double \
[final_sill=double final_nugget=double] icol=name file=png out=name crossval=crossval_file.txt
```

Commands based on the [dataset](https://grass.osgeo.org/download/data/)
of **Slovakia 3D precipitation** (*Mitasova and Hofierka, 2004*). For
more detailed information check [case studies](v.kriging.pdf). Another
examples of 3D interpolation are available in (*Stopkova, 2014*).

```sh
v.kriging phase=initial in=precip3d@PERMANENT ic=precip report=precip3d.txt file=png --o
```

```sh
v.kriging in=precip3d@PERMANENT phase=middle hz_fun=exponential vert_fun=gaussian ic=precip file=png hz_range=100000. vert_range=1600 --o -u
```

```sh
v.kriging in=precip3d@PERMANENT phase=middle hz_fun=exponential vert_fun=gaussian ic=precip \
file=png hz_range=100000. vert_range=1600 --o -u
```

Note: 3D points in this example are concentrated on the Earth's surface.
Thus the deeper / higher, the less accurate result of interpolation.

### 2D kriging

General commands:

```sh
v.kriging phase=initial in=input_layer icol=name report=report_file.txt file=png -2
```

```sh
v.kriging in=input_layer phase=final final_function=linear icol=name file=png \
  out=name crossval=crossval_file.txt -2
```

Commands based on 500 random points extracted from input points of
Digital Elevation Model (DEM) *elev\_lid792\_randpts* from the **North
Carolina [dataset](https://grass.osgeo.org/download/data/)** (*Neteler
and Mitasova, 2004*). See the [case studies](v.kriging.pdf).

```sh
v.kriging phase=initial in=elev_lid792_selected ic=value azimuth=45. td=45. \
report=lid792_500_linear.txt -2 --o
```

```sh
v.kriging in=elev_lid792_selected phase=final final_function=linear ic=value \
file=png out=lid792_500_linear crossval=lid792_500_xval_linear.txt -2 --o
```

## TODO

- **anisotropy** in horizontal direction missing
- current version is suitable just for **metric coordinate systems**
- enable **mask usage**
- **bivariate variogram** needs to be rebuilt (theory)
- **2D interpolation from 3D input layer** needs to be rebuilt
    (especially in case that there are too many points located on
    identical horizontal coordinates with different elevation)

## Recommendations

- In case of too much *warnings* about input points that have "**less
    than 2 neighbours in its closest surrounding**. The perimeter of the
    surrounding will be increased...", please consider shorter variogram
    range.
- Save just figures with theoretical variogram (using *file=extension*
    in the middle and final phase). Experimental variograms are included
    in the theoretical variogram plot and separate "experimental" plots
    can be just temporal.

## REFERENCES

Mitasova, H. and Hofierka, J. (2004). *Slovakia Precipitation data*.
Available at <https://grass.osgeo.org/download/data/>.

Neteler, M. and Mitasova, H. (2004). *Open Source GIS: A GRASS GIS
Approach*. 2nd Ed. 401 pp, Springer, New York. Online Supplement:
https://grassbook.org

Stopkova, E. (2014). *Development and application of 3D analytical
functions in spatial analyses* (Unpublished doctoral dissertation). The
Department of Theoretical Geodesy, Faculty of Civil Engineering of
Slovak University of Technology in Bratislava, Slovakia.

## SEE ALSO

*[v.vol.rst](https://grass.osgeo.org/grass-stable/manuals/v.vol.rst.html)  
[v.krige](v.krige.md)*

## REQUIREMENTS

- **Gnuplot** graphing utility, [more](http://www.gnuplot.info/)  
- **LAPACK / BLAS** (libraries for numerical computing) for GMATH
    library (GRASS Numerical Library)  
    <https://www.netlib.org/lapack> (usually available on Linux distros)

## AUTHOR

Eva Stopkova  
functions taken from another modules are cited above the function or at
the beginning of the file (e.g. *quantile.cpp* that uses slightly
modified functions taken from the module *r.quantile* (Clements, G.))
