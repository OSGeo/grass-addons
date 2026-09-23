## DESCRIPTION

*v.in.natura2000* imports [Natura 2000 protected
areas](https://www.eea.europa.eu/data-and-maps/data/ds_resolveuid/52E54BF3-ACDB-4959-9165-F3E4469BE610).
The tool is implemented for the sqlite/spatialite version of this data
(size \> 1 GB). Listing und import operations of *v.in.natura2000* may
be slow due to the huge data file size. Listing (already availabe
layers, biogeographic regions, EU member states codes, habitat codes,
species codes, protected area site types) and importing (all data,
protected areas of a defined habitat/species/member states/biogeographic
region) is limited to some small selection of wide range of possible
cases.

### Important notes

Topological correctness of the input data is not guaranteed, overlapping
of (many) polygones may occur. According to GRASS GIS topological model,
imported data may have more layers in case of overlapping polygones .
The sqlite/spatialite data is shipped in EPSG:3035 projection. The
script uses
[pyspatialite](https://pypi.org/project/pyspatialite/3.0.1-alpha-0) for
connecting to the sqlite/spatialite database.

With the database update by end 2015 the column *PERCENTAGE\_COVER* in
the HABITATS table was renamed to *PERCENTAGECOVER*. The addon script
was adapted accordingly; for Natura 2000 database versions \< 2015, the
column has to be renamed back.

Depending on which taxonomy was used to identify species, different
species codes may be used for species across EU member states. Check the
[Reference Portal for
Natura 2000](https://cdr.eionet.europa.eu/help/natura2000) (*Codelist
for species (Annex II,IV,V)*) for species and their synonyms.

## EXAMPLE

```sh
# list spatial layer(s) already availabe in the sqlite/spatialite database
v.in.natura2000 -l input=Natura2000_end2014.sqlite

# import already available spatial layer
v.in.natura2000 input=Natura2000_end2014.sqlite existing_layer=sv1800

# list biogeographic regions
v.in.natura2000 -b input=Natura2000_end2014.sqlite

# list EU member states codes
v.in.natura2000 -m input=Natura2000_end2014.sqlite

# list habitats of community interest
v.in.natura2000 -h input=Natura2000_end2014.sqlite

# list species of community interest
v.in.natura2000 -s input=Natura2000_end2014.sqlite

# list protected area site types
v.in.natura2000 -t input=Natura2000_end2014.sqlite

# import protected areas of type A
v.in.natura2000 input=Natura2000_end2014.sqlite /
output=pa_typeA sitetype=A

# import protected areas with habitat 3230
v.in.natura2000 input=Natura2000_end2014.sqlite /
output=pa_habitat3230 habitat_code=3230

# import protected areas with species 1800
v.in.natura2000 input=Natura2000_end2014.sqlite /
output=pa_species1800 species_code=1800

# import protected areas within the Alpine biogeographical region
v.in.natura2000 input=Natura2000_end2014.sqlite /
output=pa_alpineregion biogeographic_region=Alpine

# import protected areas of member state Austria
v.in.natura2000 input=Natura2000_end2014.sqlite /
output=pa_austria member_state=AT

 
```

## SEE ALSO

*[v.import](https://grass.osgeo.org/grass-stable/manuals/v.import.html),
[v.in.ogr](https://grass.osgeo.org/grass-stable/manuals/v.in.ogr.html),
[v.proj](https://grass.osgeo.org/grass-stable/manuals/v.proj.html)*

## AUTHOR

Helmut Kudrnovsky
