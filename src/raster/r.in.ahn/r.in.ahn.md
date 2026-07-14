## DESCRIPTION

*r.in.ahn* imports elevation data from the Actueel Hoogtebestand Nederland (AHN).
AHN is the national digital elevation model of the Netherlands and provides
both a digital terrain model (DTM) and a digital surface model (DSM) at
resolutions of 0.5 m and 5 m. The dataset is available in multiple versions
(AHN2 through AHN6), each corresponding to a different acquisition period and
processing specification. An overview of these versions is provided on the
[AHN](https://www.ahn.nl) website.

The user specifies the AHN version, the product (*dtm*, *dsm*, *chm*), and the
desired resolution. When chm is selected, the module first downloads and
imports both the DTM and DSM and then computes the canopy height model (CHM) as
the difference between DSM and DTM. In this case, all three layers are retained
and written to the mapset using the user-defined output name with the suffixes
*_dtm*, *_dsm*, and *_chm*.

The module determines which 1 × 1 km tiles intersect the current computational
region, downloads the required tiles, imports them into the GRASS mapset and
combines them in one layer. During this process, the computational region is
(temporarily) adjusted so that the imported raster aligns with the native AHN
grid and uses the selected resolution. The resulting raster always covers the
original region (or the portion overlapping the AHN extent). When the **-g** flag
is used, the original computational region is restored after the import is
completed.

## NOTE

This module can only be used in a location based on the Amersfoort / RD New
coordinate reference system (EPSG:28992). Running it in a location with a
different CRS will result in an error.

The computational region is modified during import to ensure that the resulting
raster aligns with the AHN grid and matches the chosen resolution (0.5 m or 5
m). If the **-g** flag is provided, the region is reset to its original extent
after the import.

All AHN versions are provided as 1 × 1 km tiles. Earlier datasets (AHN2–AHN5),
originally published as larger map sheets (5 × 6.25 km), have been reprocessed
as 1 × 1 km tiles following the AHN6 specification. In the 0.5 m DTM, cell
values represent an unweighted average of ground-level points; in the 0.5 m
DSM, cell values represent the highest point. The earlier versions retain the
original differences related to high-voltage structures: AHN4 DSM excludes
high-voltage power lines but includes pylons, while AHN2 and AHN3 DSM include
both lines and pylons. See the documentation on the [AHN
dataroom](https://www.ahn.nl/dataroom)

The module downloads tiles directly from the AHN object-storage service. The
earlier WCS-based download method and the option to retrieve complete map
sheets are no longer supported.

If a MASK is present, it is preserved, although, consistent with GRASS
behavior, it does not alter the imported DTM or DSM. However, when computing
the CHM, the MASK is applied to the DSM–DTM calculation, and the resulting CHM
will contain NULL values outside the MASKed area.

Versions 5 and 6 do not cover the whole of the Netherlands yet. Check the
[AHN website](https://www.ahn.nl/) for information about which parts are covered.

## EXAMPLES

### Example 1

Import the DTM for Fort Crèvecoeur, an fortress where the river *Old
Dieze* flows into the *Maas* river.

```sh
# Set the region for Fort Crèvecoeur
g.region n=416562 s=415957 w=145900 e=147003 res=0.5

# Download the DSM
r.in.ahn product=dtm output=dtm_crevecoeur resolution=0.5 version=4
```

![image-alt](r.in.ahn example)](r_in_ahn_01.png)
*Figure: DTM map of Fort Crèvecoeur*

### Example 2

Import the DSM version 5 with a resolution of 5 meter. Set the **-g** flag to
keep the current computation region after importing the requested data. Note,
the imported data will still have the resolution of, and will be aligned to,
the original AHN data.

```sh
# Download the DSM
r.in.ahn -g product=dsm output=dsm_crevecoeur resolution=5 version=5
```

[![image-alt](r.in.ahn example)](r_in_ahn_02.png)
*Figure: DSM map of Fort Crèvecoeur*

### Example 3

Import the CHM based on version 4 of DTM and DSM with a resolution of 0.5 meter.

```sh
r.in.ahn product=chm output=chm_crevecoeur resolution=0.5 version=4
```

[![image-alt](r.in.ahn example)](r_in_ahn_03.png)
*Figure: CHM map of Fort Crèvecoeur*

## REFERENCES

See the [AHN](https://www.ahn.nl) webpage for more information about the AHN
data (in Dutch).

## SEE ALSO

*[r.in.srtm](https://grass.osgeo.org/grass-stable/manuals/r.in.srtm.html),
[r.in.nasadem](https://grass.osgeo.org/grass-stable/manuals/r.in.nasadem.html),
[r.in.pdal](https://grass.osgeo.org/grass-stable/manuals/r.in.pdal.html),
[v.in.pdal](https://grass.osgeo.org/grass-stable/manuals/v.in.pdal.html)*

## AUTHOR

Paulo van Breugel | [HAS green academy](https://has.nl), University of
Applied Sciences | [Climate-robust Landscapes research
group](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)
| [Innovative Bio-Monitoring research
group](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/)
| Contact: [Ecodiv.earth](https://ecodiv.earth)
