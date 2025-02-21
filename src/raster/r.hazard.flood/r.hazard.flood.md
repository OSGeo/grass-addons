## DESCRIPTION

*r.hazard.flood* is an implementation of a fast procedure to detect
flood prone areas. It is based on a simple procedure that exploits the
correlation between flood exposure and a Modified Topographic Index
(MTI), calculated on the basis of the DTM and strongly influenced by the
resolution of this latter.

### Important

Before running the program, the region should be aligned perfectly with
the input map. The cell size taken in consideration is the one specified
in the region settings. If it doesn't match with the elevation map, the
result is nonsense. Note that this program only supports projected
coordinate systems, LatLong is not supported.

## NOTES

The availability of new technologies for the measurement of surface
elevation has addressed the lack of high resolution elevation data, and
this has led to an increase in the attraction of DEM-based automated
procedures for hydrological applications including the delineation of
floodplains. In particular, the exposure to flooding may be delineated
quite well by adopting a modified topographic index (TIm) computed from
a DEM. The comparison between TIm and flood inundation maps (obtained
from hydraulic simulations) shows that the portion of a basin exposed to
flood inundation is generally characterized by a TIm higher than a given
threshold, tau. This allows the development of a simple procedure for
the identification of flood prone areas that requires only two
parameters for the calibration: the threshold tau and the exponent of
TIm. Because the topographic index is sensitive to the spatial
resolution of the digital elevation model, the threshold is
automatically determinated from the cellsize.

The proposed procedure may help in the delineation of flood prone areas
especially in basins with marked topography. The method is sensitive to
the DEM resolution, but a cell size of \~100m is sufficient to reach
good performances for the catchments investigated here. The procedure is
also tested adopting DEMs from different sources, such as the shuttle
radar topography mission (SRTM) DEM, ASTER GDEM, and national elevation
data. This experiment highlights the reliability with the SRTM DEM for
the delineation of flood prone areas. A useful relationship between
model parameters and the reference scale of the DEM was also obtained
providing a strategy for the application of this method in different
contexts.

The use of the modified topographic index should not be considered as an
alternative to standard hydrological-hydraulic simulations for flood
mapping, but it may represent a useful and rapid tool for a preliminary
delineation of flooding areas in ungauged basins and in areas where
expensive and time consuming hydrological-hydraulic simulations are not
affordable or economically convenient.

## EXAMPLE

```sh
g.region raster=elevation -ap
r.hazard.flood map=elevation flood=flood mti=mti
```

### Dependencies

*[r.area](https://grass.osgeo.org/grass-stable/manuals/r.area.html)*

## CITE AS

*Di Leo M., Manfreda S., Fiorentino M., An automated procedure for the
detection of flood prone areas: r.hazard.flood, Geomatics Workbooks
n.10, 2011.
([PDF](https://geomatica.como.polimi.it/workbooks/n10/GW10-FOSS4Git_2011.pdf))*

## REFERENCES

*Manfreda S., Di Leo M., Sole A., Detection of Flood Prone Areas using
Digital Elevation Models, Journal of Hydrologic Engineering,
(10.1061/(ASCE)HE.1943-5584.0000367), 2011.*

## AUTHOR

Margherita Di Leo (dileomargherita AT gmail DOT com)
