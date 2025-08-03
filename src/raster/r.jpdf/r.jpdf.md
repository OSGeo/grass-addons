## DESCRIPTION

*r.jpdf* reads two series of raster maps and calculates for each raster
cell the joint probability density function of the two input series. The
output is set of raster maps, each containing the probability within a
range of values from the first set and a range from the second set. NULL
values are ignored when calculating the JPDF.

The number of output raster maps is determined by the number of "bins"
specified by the user using the parameters *input1* and *input2*. The
users gives the range and density of bins with
*input1=Start1,End1,Nbins1 input2=Start2,End2,Nbins2*. In this case the
data from the first data set will be assigned to *Nbins1* intervals
between *Start1* and *End1* and *Nbins2* intervals between *Start2* and
*End2* for the second data set. In addition, *r.jpdf* will calculate
extra bins for values below or above the start and end values given by
the user. In total, the output will consist of (*Nbins1*+2)×(*Nbins2*+2)
raster maps. The naming of the output rasters is *Prefix\_N1\_N2* where
*Prefix* is given by the parameter *output*. *N1* and *N2* may contain
leading zeros.

## NOTES

### Input series of different lengths

Rasters from the two series of input data will be compared in the order
in which they appear in the two lists. If one list is longer than the
other, the trailing raster maps will be ignored.

### Memory consumption

The (*Nbins1*+2)×(*Nbins2*+2) raster maps are held in memory until the
end of the processing. On the other hand, only one raster from each of
the two series of input rasters will be held in memory.

## EXAMPLES

Using *r.jpdf* with wildcards:  

```sh
r.series input1="`g.list pattern='temperature*' sep=,`" input2="`g.list pattern='pressure*' sep=,`"\
         output=jpdf_temp_pres bins1=-20,40,10 bins2=950,1030,10
```

Note the *g.list* script also supports regular expressions for selecting
map names.

## SEE ALSO

*[g.list](https://grass.osgeo.org/grass-stable/manuals/g.list.html),
[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
[r.quantile](https://grass.osgeo.org/grass-stable/manuals/r.quantile.html),
[r.series.accumulate](https://grass.osgeo.org/grass-stable/manuals/r.series.accumulate.html),
[r.series.interp](https://grass.osgeo.org/grass-stable/manuals/r.series.interp.html),
[r.univar](https://grass.osgeo.org/grass-stable/manuals/r.univar.html)*

[Hints for large raster data
processing](https://grasswiki.osgeo.org/wiki/Large_raster_data_processing)

## AUTHOR

Thomas Huld
