## DESCRIPTION

This module calculates vegetation indices from several space time raster datasets,
using *i.vi* module.

It can apply cloud and shadow masks stored as space time datasets (raster or vector).

The output space time raster dataset can be a new dataset or an existing one,
in this case the new created maps will be added to the existing space time
raster dataset.

## EXAMPLE

Calculate the NDVI for your Red and NIR STDRS bands

```bash
t.rast.vi red=red_monthly nir=nir_monthly output=ndvi_monthly viname=ndvi \
    prefix=ndvimonthly
```

If you have to calculate different indices that require more info, such as EVI
or MSAVI, you need to set the correct parameters.

```bash
t.rast.vi red=red_monthly nir=nir_monthly blue=blue_monthly output=evi_monthly \
    viname=evi prefix=evimonthly
```

```bash
t.rast.vi red=red_monthly nir=nir_monthly output=evi_monthly viname=msavi \
    prefix=msavimonthly soil_line_slope=0.8 soil_line_intercept=0.5 \
    soil_noise_reduction=1
```

## SEE ALSO

*[i.vi.md](i.vi)

## AUTHOR

Luca Delucchi, Fondazione Edmund Mach
