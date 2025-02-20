## DESCRIPTION

The *i.modis* suite is a toolset to import MODIS (Moderate Resolution
Imaging Spectroradiometer, flown on the two NASA spacecrafts Terra and
Aqua) satellite data into GRASS GIS. It uses the
[pyModis](http://www.pymodis.org) library and additionally either the
[GDAL library](https://gdal.org/) or the [MODIS Reprojection
Tool](https://web.archive.org/web/20170711122121/https://lpdaac.usgs.gov/tools/modis_reprojection_tool)
(MRT) software to convert, mosaic and process MODIS data.

The *i.modis* suite requires the pyModis library and either the GDAL or
MRT software to be installed.

The *i.modis* suite offers two modules as interface to MODIS data. Each
module is dedicated to a specific operation. The module
*i.modis.download* is used to download MODIS HDF products from NASA
servers. These files can then be imported with *i.modis.import* which
supports import of Level 3 MODIS products as a single image or as a
mosaic into GRASS GIS.

Subsequently, the user can create a temporal dataset using *t.create*
and, register the maps with *t.register*. NOTE: In order to work with
the temporal framework of GRASS GIS the flag *w* must be set during the
import with *i.modis.import*.

The user can choose from several MODIS products, distributed as single
or multiple tiles and also ranges of observation days retrieving data
from the related NASA servers. The suite imports Level 3 (georeferenced)
products either as single images or as mosaics for each date.

## Supported MODIS products

These products are currently supported:

### MODIS Surface Reflectance

  - **Surface spectral reflectance daily 1 km and 500 m (Terra/Aqua)**:
    Bands 1 through 7 corrected for atmospheric conditions such as
    gasses, aerosols, and Rayleigh scattering in Sinusoidal projection
    daily. Provided along with the 500 meter (m) surface reflectance,
    observation, and quality bands are a set of ten 1 kilometer
    observation bands and geolocation flags. The reflectance layers from
    MOD09GA and MYD09GA are used as the source data for many of the
    MODIS land products (related
    [MOD09GA](https://lpdaac.usgs.gov/products/mod09gav061/) and
    [MYD09GA](https://lpdaac.usgs.gov/products/myd09gav061/) product
    pages).
  - **Surface spectral reflectance eight day 500 m (Terra/Aqua)**: Bands
    1 through 7 corrected for atmospheric conditions such as gasses,
    aerosols, and Rayleigh scattering in Sinusoidal projection during an
    8-day period. Along with the seven 500 meter (m) reflectance bands
    are two quality layers and four observation bands. For each pixel, a
    value is selected from all the acquisitions within the 8-day
    composite period. The criteria for the pixel choice include cloud
    and solar zenith. When several acquisitions meet the criteria, the
    pixel with the minimum channel 3 (blue) value is used (related
    [MOD09A1](https://lpdaac.usgs.gov/products/mod09a1v061/) and
    [MYD09A1](https://lpdaac.usgs.gov/products/myd09a1v061/) product
    pages).

### MODIS LST - Land Surface Temperature

  - **Land Surface Temperature daily 1 km (Terra/Aqua)**: product
    provides per-pixel temperature and emissivity values in a sequence
    of swath-based to grid-based global products in Sinusoidal
    projection. The MODIS/Terra-Aqua LST/E Daily L3 Global 1 km Grid
    product (MOD11A1/MYD11A1), is tile-based and gridded in the
    Sinusoidal projection, and produced daily at 1 km spatial resolution
    (related [MOD11A1](https://lpdaac.usgs.gov/products/mod11a1v061/)
    and [MYD11A1](https://lpdaac.usgs.gov/products/myd11a1v061/) product
    pages).
  - **Land Surface Temperature eight day 1 km (Terra/Aqua)**: data are
    composed from the daily 1-kilometer LST product (MOD11A1/MYD11A1)
    and stored on a 1-km Sinusoidal grid as the average values of
    clear-sky LSTs during an 8-day period.  
    MOD11A2/MYD11A2 is comprised of daytime and nighttime LSTs, quality
    assessment, observation times, view angles, bits of clear sky days
    and nights, and emissivities estimated in Bands 31 and 32 from land
    cover types (related
    [MOD11A2](https://lpdaac.usgs.gov/products/mod11a2v061/) and
    [MYD11A2](https://lpdaac.usgs.gov/products/myd11a2v061/) product
    pages).
  - **Land Surface Temperature eight day \~6 km (Terra/Aqua)**: products
    provide per-pixel temperature and emissivity values in a sequence of
    swath-based to grid-based global products. The MODIS/Terra-Aqua
    LST/E Daily L3 Global 6 km Grid (Short name: MOD11B1/MYD11B1), is
    tile-based and gridded in the Sinusoidal projection, and produced
    daily at 5600m spatial resolution (related
    [MOD11B1](https://lpdaac.usgs.gov/products/mod11b1v061/) and
    [MYD11B1](https://lpdaac.usgs.gov/products/myd11b1v061/) product
    pages).
  - **Land Surface Temperature monthly \~6 km (Terra/Aqua)**: products
    provide per-pixel temperature and emissivity values in a sequence of
    swath-based to grid-based global products with a pixel size of 5,600
    meters. Each LST\&E pixel value in the MOD11B3 is a simple average
    of all the corresponding values from the MOD11B1 collected during
    the month period. Each MOD11B3 granule consists of 19 layers
    including daytime and nighttime layers for LSTs, quality control
    assessments, observation times, view zenith angles, and number of
    clear sky observations along with percentage of land in the tile and
    emissivities from bands 20, 22, 23, 29, 31, and 32. Unique to the
    MOD11B products are additional day and night LST layers generated
    from band 31 of the corresponding 1 km [MOD11\_L2 swath
    product](https://lpdaac.usgs.gov/products/mod11_l2v061/) aggregated
    to the 6 km grid (related
    [MOD11B3](https://lpdaac.usgs.gov/products/mod11b3v061/) and
    [MYD11B3](https://lpdaac.usgs.gov/products/myd11b3v061/) product
    pages).

### MODIS VI - Vegetation Indices

  - **VI sixteen days 250 m (Terra/Aqua)**: Global MOD13Q1/MYD13Q1 MODIS
    vegetation indices are designed to provide consistent spatial and
    temporal comparisons of vegetation. conditions. Blue, red, and
    near-infrared reflectances, centered at 469-nanometers,
    645-nanometers, and 858-nanometers, respectively, are used to
    determine the MODIS daily vegetation indices.  
    The MODIS Normalized Difference Vegetation Index (NDVI) complements
    NOAA's Advanced Very High Resolution Radiometer (AVHRR) NDVI
    products and provides continuity for time series historical
    applications. MODIS also includes a new Enhanced Vegetation Index
    (EVI) that minimizes canopy background variations and maintains
    sensitivity over dense vegetation conditions. The EVI also uses the
    blue band to remove residual atmosphere contamination caused by
    smoke and sub-pixel thin cloud clouds. The MODIS NDVI and EVI
    products are computed from atmospherically corrected bi-directional
    surface reflectances that have been masked for water, clouds, heavy
    aerosols, and cloud shadows. Global MOD13Q1/MYD13Q1 data are
    provided every 16 days at 250-meter spatial resolution as a gridded
    level-3 product in the Sinusoidal projection. Lacking a 250m blue
    band, the EVI algorithm uses the 500m blue band to correct for
    residual atmospheric effects, with negligible spatial artifacts
    (related [MOD13Q1](https://lpdaac.usgs.gov/products/mod13q1v061/)
    and [MYD13Q1](https://lpdaac.usgs.gov/products/myd13q1v061/) product
    pages).
  - **VI sixteen days 500 m (Terra/Aqua)**: Global MOD13A1/MYD13A1 MODIS
    vegetation indices are designed to provide consistent spatial and
    temporal comparisons of vegetation conditions. Blue, red, and
    near-infrared reflectances, centered at 469-nanometers,
    645-nanometers, and 858-nanometers, respectively, are used to
    determine the MODIS daily vegetation indices.  
    The MODIS Normalized Difference Vegetation Index (NDVI) complements
    NOAA's Advanced Very High Resolution Radiometer (AVHRR) NDVI
    products provide continuity for time series historical applications.
    MODIS also includes a new Enhanced Vegetation Index (EVI) that
    minimizes canopy background variations and maintains sensitivity
    over dense vegetation conditions. The EVI also uses the blue band to
    remove residual atmosphere contamination caused by smoke and
    sub-pixel thin cloud clouds. The MODIS NDVI and EVI products are
    computed from atmospherically corrected bi-directional surface
    reflectances that have been masked for water, clouds, heavy
    aerosols, and cloud shadows.  
    Global MOD13A1/MYD13A1 data are provided every 16 days at 500-meter
    spatial resolution as a gridded level-3 product in the Sinusoidal
    projection. Vegetation indices are used for global monitoring of
    vegetation conditions and are used in products displaying land cover
    and land cover changes. These data may be used as input for modeling
    global biogeochemical and hydrologic processes and global and
    regional climate. These data also may be used for characterizing
    land surface biophysical properties and processes, including primary
    production and land cover conversion (related
    [MOD13A1](https://lpdaac.usgs.gov/products/mod13a1v061/) and
    [MYD13A1](https://lpdaac.usgs.gov/products/myd13a1v061/) product
    pages).
  - **VI sixteen days 250 m (Terra/Aqua)**: The MOD13Q1 product provides
    two primary vegetation layers. The first is the Normalized
    Difference Vegetation Index (NDVI) which is referred to as the
    continuity index to the existing National Oceanic and Atmospheric
    Administration-Advanced Very High Resolution Radiometer (NOAA-AVHRR)
    derived NDVI. The second vegetation layer is the Enhanced Vegetation
    Index (EVI), which has improved sensitivity over high biomass
    regions. The algorithm chooses the best available pixel value from
    all the acquisitions from the 16 day period. The criteria used is
    low clouds, low view angle, and the highest NDVI/EVI value. Along
    with the vegetation layers and the two quality layers, the HDF file
    will have MODIS reflectance bands 1 (red), 2 (near-infrared), 3
    (blue), and 7 (mid-infrared), as well as four observation layers
    (related [MOD13Q1](https://lpdaac.usgs.gov/products/mod13q1v061/)
    and [MYD13Q1](https://lpdaac.usgs.gov/products/myd13q1v061/) product
    pages).
  - **VI sixteen days 1 km (Terra/Aqua)**: The MOD13A2 product provides
    a Vegetation Index (VI) value at a per pixel basis. There are 2
    primary vegetation layers. The first is the Normalized Difference
    Vegetation Index (NDVI) which is referred to as the continuity index
    to the existing National Oceanic and Atmospheric
    Administration-Advanced Very High Resolution Radiometer (NOAA-AVHRR)
    derived NDVI. The second vegetation layer is the Enhanced Vegetation
    Index (EVI), which has improved sensitivity over high biomass
    regions. The data are provided at 1000 m resolution as a gridded
    level-3 product in the Sinusoidal projection (related
    [MOD13A2](https://lpdaac.usgs.gov/products/mod13a2v061/) and
    [MYD13A2](https://lpdaac.usgs.gov/products/myd13a2v061/) product
    pages).
  - **VI monthly 1 km (Terra/Aqua)**: The MOD13A3 product provides a
    Vegetation Index (VI) value at a per pixel basis. There are 2
    primary vegetation layers. The first is the Normalized Difference
    Vegetation Index (NDVI) which is referred to as the continuity index
    to the existing National Oceanic and Atmospheric
    Administration-Advanced Very High Resolution Radiometer (NOAA-AVHRR)
    derived NDVI. The second vegetation layer is the Enhanced Vegetation
    Index (EVI), which has improved sensitivity over high biomass
    regions. The data are provided at 1000 m resolution as a gridded
    level-3 product in the Sinusoidal projection. Provided along with
    the vegetation layers and the two quality assurance (QA) layers are
    reflectance bands 1 (red), 2 (near-infrared), 3 (blue), and 7
    (mid-infrared), as well as three observation layers (related
    [MOD13A3](https://lpdaac.usgs.gov/products/mod13a3v061/) and
    [MYD13A3](https://lpdaac.usgs.gov/products/myd13a3v061/) product
    pages).
  - **VI sixteen days Global 0.05Deg CMG (Terra/Aqua)**: The MOD13C1
    product provides a Vegetation Index (VI) value at a per pixel basis.
    There are 2 primary vegetation layers. The first is the Normalized
    Difference Vegetation Index (NDVI) which is referred to as the
    continuity index to the existing National Oceanic and Atmospheric
    Administration-Advanced Very High Resolution Radiometer (NOAA-AVHRR)
    derived NDVI. The second vegetation layer is the Enhanced Vegetation
    Index (EVI), which has improved sensitivity over high biomass
    regions. The Climate Modeling Grid (CMG) consists 3600 rows and 7200
    columns of 5600 m pixels and is provided as a global
    latitude/longitude grid (related
    [MOD13C1](https://lpdaac.usgs.gov/products/mod13c1v061/) and
    [MYD13C1](https://lpdaac.usgs.gov/products/myd13c1v061/) product
    pages).
  - **VI monthly Global 0.05Deg CMG (Terra/Aqua)**: The MOD13C2 product
    provides a Vegetation Index (VI) value at a per pixel basis. There
    are 2 primary vegetation layers. The first is the Normalized
    Difference Vegetation Index (NDVI) which is referred to as the
    continuity index to the existing National Oceanic and Atmospheric
    Administration-Advanced Very High Resolution Radiometer (NOAA-AVHRR)
    derived NDVI. The second vegetation layer is the Enhanced Vegetation
    Index (EVI), which has improved sensitivity over high biomass
    regions. The Climate Modeling Grid (CMG) consists 3600 rows and 7200
    columns of 5600 m pixels and is provided as a global
    latitude/longitude grid (related
    [MOD13C2](https://lpdaac.usgs.gov/products/mod13c2v061/) and
    [MYD13C2](https://lpdaac.usgs.gov/products/myd13c2v061/) product
    pages).

### MODIS AOD - Aerosol Optical Depth

  - **Aerosol optical depth daily 1 km (Terra+Aqua)**: MCD19A2 is the
    short name for the Multi-Angle Implementation of Atmospheric
    Correction (MAIAC) algorithm-based Level-2 gridded (L2G) aerosol
    optical thickness over land surfaces product. This product is
    derived using both Terra and Aqua MODIS inputs, and produced daily
    at 1 km pixel resolution in a Sinusoidal projection. MCD19A2 has
    achieved Stage-3 validation, and each Hierarchical Data Format 4
    (HDF4) file contains two data groups with the following Science Data
    Set parameters: Grid 1km: 1. Aerosol Optical Depth at 047 micron /
    2. Aerosol Optical Depth at 055 micron / 3. AOD Uncertainty at 047
    micron / 4. Fine-Mode Fraction for Ocean / 5. Column Water Vapor in
    cm liquid water / 6. AOD QA / 7. AOD Model (Regional background
    model used) / 8. Injection Height (Smoke injection height over local
    surface height) Grid 5km: 9. Cosine of Solar Zenith Angle / 10.
    Cosine of View Zenith Angle / 11. Relative Azimuth Angle / 12.
    Scattering Angle / 13. Glint Angle. See the validation webpage for
    details on the validation and validation definitions (related
    [MCD19A2](https://lpdaac.usgs.gov/products/mcd19a2v006/) product
    pages).

### MODIS Snow

  - **Snow daily 500 m (Terra/Aqua)**: MOD10A1 and MYD10A1 are tiles of
    daily snow cover at 500 m spatial resolution. The daily observation
    selected from multiple observations in a MOD10A1 (or MYD10A1) cell
    is the observation acquired nearest nadir and having the greatest
    coverage of the grid cell. The daily MOD10A1 and MYD10A1 snow
    products are tiles of data gridded in the sinusoidal projection.
    Tiles are approximately 1200 x 1200 km in area. A single scientific
    data set (SDS) of snow cover and a single SDS of QA data along with
    local and global attributes comprise the data product file. The
    daily level 3 snow product is the result of selecting an observation
    from the multiple observations mapped to a cell of the MOD10\_L2G
    (or MYD10\_L2G) product. See the validation webpage for details on
    the validation and validation definitions (related
    [MOD10A1](https://nsidc.org/data/MOD10A1) and
    [MYD10A1](https://nsidc.org/data/MYD10A1) product pages).
  - **Snow eight days 500 m (Terra/Aqua)**: The MOD10A2 and MYD10A2
    products are composites of eight days of snow maps in the sinusoidal
    grid. An eight-day compositing period was chosen because that is the
    exact ground track repeat period of the Terra and Aqua platforms.
    Snow cover over eight days is mapped as maximum snow extent in one
    SDS and as a chronology of observations in the other SDS. Eight-day
    periods begin on the first day of the year and extend into the next
    year. The product can be produced with two to eight days of input.
    There may not always be eight days of input, because of various
    reasons, so the user should check the attributes to determine on
    what days observations were obtained. See the validation webpage for
    details on the validation and validation definitions (related
    [MOD10A2](https://nsidc.org/data/MOD10A2) and
    [MYD10A2](https://nsidc.org/data/MYD10A2) product pages).

### MODIS Land Water Mask

  - **Land Water Mask 250 m (Terra)**: The Version 6 data product
    provides a global map of surface water at 250 meter (m) spatial
    resolution. The data are available annually from 2000 to 2015.
    MOD44W Version 6 is derived using a decision tree classifier trained
    with MODIS data and validated with the Version 5 MOD44W data
    product. A series of masks are applied to address known issues
    caused by terrain shadow, burn scars, cloudiness, or ice cover in
    oceans. A primary improvement in Version 6 is the generation of time
    series data rather than a simple static representation of water,
    given that water bodies fluctuate in size and location over time due
    to both natural and anthropogenic causes. Provided in each MOD44W
    Version 6 Hierarchical Data Format 4 (HDF4) file are layers for
    land, water, no data, and an associated per pixel quality assurance
    (QA) layer that provides users with information on the determination
    of water (related
    [MOD44W](https://lpdaac.usgs.gov/products/mod44wv006/) product
    page).

## NOTES

The *i.modis* modules need the [pyModis](https://www.pymodis.org)
library. Please install it beforehand.

## SEE ALSO

*[i.modis.download](i.modis.download.md),
[i.modis.import](i.modis.import.md),
[i.modis.qc](https://grass.osgeo.org/grass-stable/manuals/i.modis.qc.html)*

  - [MODIS Reprojection
    Tool](https://web.archive.org/web/20170711122121/https://lpdaac.usgs.gov/tools/modis_reprojection_tool)
  - [MODIS Land homepage](https://modis-land.gsfc.nasa.gov/)
  - [MODIS Snow homepage](https://modis-snow-ice.gsfc.nasa.gov/)
  - [MODIS Land products table](https://lpdaac.usgs.gov/product_search/)

## AUTHORS

Luca Delucchi, Initial version: Google Summer of Code 2011; subsequently
updated by further authors
