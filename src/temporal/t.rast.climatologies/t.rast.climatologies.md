## DESCRIPTION

**t.rast.climatologies** is a module to calculate climatologies, i.e., long term stats, for single days or months in a time series. If the *s* flag is used, the module outputs a new space time raster dataset of relative temporal type with the aggregated maps.

## EXAMPLE

### Daily climatologies

Starting from a space time raster dataset of daily granularity (or granularity lower than one day), the module will create a new space time raster dataset of relative temporal type containing the long term average for each day along years.

```bash
t.rast.climatologies input=myinput output=dailyoutput
```

### 15 days climatologies

Starting from a space time raster dataset of daily granularity (or granularity lower than one day), the module will create a new space time raster dataset of relative temporal type containing the long term average every 15 days starting from 1st January.

```bash
t.rast.climatologies input=myinput output=dailyoutput granularity='15 days'
```

### Monthly climatologies

Starting from a space time raster dataset of monthly granularity (or lower than one month), the module will create two new space time raster datasets containing the long term minimum and maximum for each month along years.

```bash
t.rast.climatologies input=myinput granularity=month method=min,max output=monthlyoutputmin,monthlyoutputmax
```

## SEE ALSO

[r.series](r.series.md), [t.rast.series](t.rast.series.md)

## AUTHOR

Luca Delucchi, *Fondazione Edmund Mach*
