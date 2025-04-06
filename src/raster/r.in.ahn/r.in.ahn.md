## DESCRIPTION

*r.in.ahn* imports the Actueel Hoogtebestand Nederland
([AHN](https://www.ahn.nl), version 4) for the current region. The AHN
is a digital elevation model (DEM) of the Netherlands with a resolution
of of 0.5 meter.

There are two different layers available: the digital terrain model
(DTM) and a digital surface model (DSM). The user needs to select which
to download. The selected product will be downloaded for the computation
region. However, note that the region will adjusted to ensure that the
imported raster layer neatly aligns with and has the same resolution
(0.5 meter) as the original AHN data. The resulting will always have the
same or a larger extent than the original computation region. If you
want to store the current computational region, make sure to first save
it using *g.region*.

The AHN can also be downloaded in map sheets (tiles) of 6.5 by 5
kilometer. To download the area covered by one or more of these tiles,
the user can set the **-t** flag. This wil to download the area for the
tiles that overlap with the current computational region.

## NOTE

This location only works in a location with the project 'RD New'
(EPSG:28992). Attempts to run it in a location with another CRS will
result in an error message.

The region will be adjusted to ensure that the imported raster layer
neatly aligns with and has the same resolution (0.5 meter) as the
original AHN data. The user can set the **-g** flag to return the region
to the original computation region after the data is imported.

The addon uses the *r.in.wcs* addon in the background, so the user will
first need to install this addon.

## EXAMPLE

### Example 1

Import the DTM for Fort Crèvecoeur, an fortress where the river *Old
Dieze* flows into the *Maas* river.

```sh
# Set the region for Fort Crèvecoeur
g.region n=416562 s=415957 w=145900 e=147003 res=0.5

# Download the DSM
r.in.ahn product=dsm output=dsm_crevecoeur
```

[![image-alt](r_in_ahn_01.png)](r_in_ahn_01.png)  
*Figure: DSM map of Fort Crèvecoeur*

### Example 2

Import the DTM for the tile that overlaps with the current region. Do
this by setting the **-t flag**.

```sh
# Set the region for Fort Crèvecoeur
g.region n=416562 s=415957 w=145900 e=147003 res=0.5

# Download the DSM
r.in.ahn -t product=dsm output=dsm_crevecoeur2
```

The result will be a raster layer *dsm\_crevecoeur2* and a vector layer
*dsm\_crevecoeur2\_tiles*

[![image-alt](r_in_ahn_02.png)](r_in_ahn_02.png)  
*Figure: DSM map of Fort Crèvecoeur. Left shows the extent (red outline)
after running example 2. The extent equals the extent of the area (tile)
for which the data was downloaded. Right shows the extent (red outline)
after running example 3. In this case, the extent is the same as before
running the example because the **-g** flag was set.*

### Example 3

Set the **-t** flag to import the DTM for the tile that overlaps with
the current region. Set the **-g** flag to keep the current computation
region after importing the requested data. Note, the imported data will
still have the resolution of, and will be aligned to, the original AHN
data.

```sh
# Set the region for Fort Crèvecoeur
g.region n=416562 s=415957 w=145900 e=147003 res=0.5

# Download the DSM
r.in.ahn -t -g product=dsm output=dsm_crevecoeur3
```

The result will be a raster layer *dsm\_crevecoeur3* and a vector layer
*dsm\_crevecoeur3\_tiles*

## REFERENCES

See the [AHN](https://ahn.nl) webpage for more information about the AHN
data (in Dutch).

## AUTHORS

Paulo van Breugel | [HAS green academy](https://has.nl), University of
Applied Sciences | [Climate-robust Landscapes research
group](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)
| [Innovative Bio-Monitoring research
group](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/)
| Contact: [Ecodiv.earth](https://ecodiv.earth)
