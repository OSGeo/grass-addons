## DESCRIPTION

*i.sentinel.coverage* is a GRASS GIS addon Python script to check the
area coverage by Sentinel scenes selected by a filter.

The coverage test considers only the geometric coverage by Sentinel
scene footprints and does not include the cloud covered pixels.

## EXAMPLES

### Check Sentinel-1 scenes by region, start and end time

Note that only the last 12 months of Sentinel data are online available
ESA Hub, older scenes are stored in the Long Term Archive (LTA) and
cannot be retrieved immediately. The example is based on the North
Carolina dataset:

```sh
# extract Durham (NC) county
v.extract input=boundary_county output=county_durham where="NAME = 'DURHAM'"

# simplify geometry (needed for ESA Hub)
v.generalize input=county_durham output=county_durham_dp1000 method=douglas threshold=1000

# search for SLC scenes in certain period of time
i.sentinel.coverage settings=credentials.txt output=s1names.txt \
  producttype=SLC minpercent=95 area=county_durham_dp1000 start=2020-10-01 end=2021-01-31
```

### Check Sentinel-2 scenes by region, cloud coverage, start and end time

Note that only the last 12 months of Sentinel data are online available
ESA Hub, older scenes are stored in the Long Term Archive (LTA) and
cannot be retrieved immediately. The example is based on the North
Carolina dataset:

```sh
# extract Durham (NC) county
v.extract input=boundary_county output=county_durham where="NAME = 'DURHAM'"

# simplify geometry (needed for ESA Hub)
v.generalize input=county_durham output=county_durham_dp1000 method=douglas threshold=1000

# search for L2A scenes with minimal clouds in certain period of time
i.sentinel.coverage settings=credentials.txt output=s2names.txt \
  producttype=S2MSI2A clouds=10 minpercent=95 area=county_durham_dp1000 start=2020-10-01 end=2021-01-31
```

### Check Sentinel-2 scenes by names

```sh
i.sentinel.coverage settings=credentials.txt output=s2names.txt \
  names=S2A_MSIL2A_20200104T024111_N0213_R089_T49MGU_20200104T061337,S2B_MSIL2A_20200129T023939_N0213_R089_T49MGU_20200201T153252 \
  producttype=S2MSI2A clouds=20 minpercent=95 area=mangkawuk
```

### Use retrieved Sentinel-2 scene names for import

When storing the list of scenes into a file, this resulting file can be
used for a parallelized import, using the
[t.sentinel](https://github.com/mundialis/t.sentinel) set of addons:

```sh
# install t.sentinel.import and related addons
g.extension extension=t.sentinel url=https://github.com/mundialis/t.sentinel

# download and import into space-time cube (STRDS), using 4 CPUs
t.sentinel.import settings=credentials.txt s2names=s2names.txt nprocs=4 \
  pattern='B(02_10|03_10|04_10|08_10)m' strds_output=s2_myarea directory=s2_data/
```

## SEE ALSO

*[i.sentinel.download](i.sentinel.download.md),
[v.dissolve](v.dissolve.md), [v.overlay](v.overlay.md),
[v.to.db](v.to.db.md)*

## AUTHOR

Anika Weinmann, [mundialis](https://www.mundialis.de/)
