## DESCRIPTION

**t.rast.aggregate.seasons** aggregates an input space time raster dataset
astronomical or meteorological seasons using a statistical method
selected by the user. It uses
[t.rast.aggregate.ds](https://grass.osgeo.org/grass-stable/manuals/t.rast.aggregate.ds.html)
to detect and copy the seasons granularity.

Astronomical seasons are defined as:

* *Spring* 20 March - 21 June
* *Summer* 21 June - 20 September
* *Autumn* 20 September - 21 December
* *Winter* 21 December - 20 March (following year)

Meteorological seasons are defined as:

* *Spring* 1 March - 31 May
* *Summer* 1 June - 30 August
* *Autumn* 1 September - 30 November
* *Winter* 1 December - 28/29 Februay (following year)

Using the *output* option, the tool will create a single unified space time
raster dataset with the name provided, otherwise it will create a space time
raster dataset for each year in the input space time raster dataset.

## EXAMPLES

Aggregate the input space-time raster dataset into astronomical seasons and
create a unified output space-time raster dataset

```bash
t.rast.aggregate.seasons input=mystrds basename=mystrds_seasons output=outstrds
```

Aggregate the input space-time raster dataset into meteorological seasons and
create an output space-time raster dataset for a selected year

```bash
t.rast.aggregate.seasons -m input=mystrds basename=mystrds_seasons_meteo \
    output=outstrds_meteo year=2014
```

## NOTES

If one of the seasons is not fully covered by the input space time raster
dataset, that season will not be created by the tool. For example if you have
a daily space time raster dataset for just one year it will create only raster
maps for 3 seasons (Spring, Summer, Autumn), the Winter will be avoided
since your input dataset has data only until the end of the
year but it misses the data from January to March.

## SEE ALSO

*[t.rast.aggregate.ds](t.rast.aggregate.ds.md)*, *[r.null](r.series.md)*

## AUTHOR

Luca Delucchi, Fondazione Edmund Mach
