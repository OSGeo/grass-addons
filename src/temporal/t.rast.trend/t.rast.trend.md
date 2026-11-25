## DESCRIPTION

*t.rast.trend* included tools for STL decomposition (Seasonal- Trend
decomposition using LOESS) and trend analysis of a space-time raster dataset
(STRDS):

- *[t.rast.stl](t.rast.stl.md)* decomposes and plots the series at a single
  point, or the mean/median series over a zone or raster, optionally with OLS,
  Theil-Sen and/or GAM trend lines.
- *[t.rast.stl2ca](t.rast.stl2ca.md)* decomposes and compares the series of
  every category of a classification (a CELL raster's own cell values, or a
  vector map grouped by an attribute column) on one multi-panel plot.

### Acknowledgement

This tool was developed for the
[Save the tiger! Save the Grasslands! Save the Water!](https://savethetiger.nl/)
project, funded by the Dutch Research Council (NWO) under award
<https://doi.org/10.61686/UYHYF97856>.

## Notes

Installing *t.rast.trend* installs both tools together with the shared
*trendlib* they depend on. Installing *t.rast.stl* or *t.rast.stl2ca* on
its own does not install *trendlib*, so install *t.rast.trend* first (or
alongside) if installing either tool individually.

## SEE ALSO

*[t.rast.stl](t.rast.stl.md)*, *[t.rast.stl2ca](t.rast.stl2ca.md)*

## AUTHOR

[Paulo van Breugel](https://ecodiv.earth),
[Innovative Biomonitoring](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/)
and
[Climate-robust Landscapes](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)
research groups at the [HAS green academy](https://has.nl)
