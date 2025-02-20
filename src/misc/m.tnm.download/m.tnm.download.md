## DESCRIPTION

*m.tnm.download* downloads data for specified polygon codes from [The
National Map (TNM)](https://apps.nationalmap.gov/downloader/).

## NOTES

This module uses [the TNM Access REST
APIs](https://apps.nationalmap.gov/tnmaccess/) to download TNM data.

## EXAMPLES

List supported datasets and exit:

```sh
# use indices, IDs, or tags to select datasets, but indices can change between
# sessions
m.tnm.download -d
```

List supported states and exit:

```sh
# use FIPS codes, USPS codes, or names to select states for type=state
m.tnm.download -s
```

Download National Elevation Dataset (NED) 1-arcsecond files for Texas:

```sh
# find the dataset ID
m.tnm.download -d | grep "NED.* 1 arc-second"
m.tnm.download dataset=one-arc-second-dem type=state code=TX
```

Download National Watershed Boundary Dataset (WBD) files for HUC8
01010001:

```sh
# find the dataset ID
m.tnm.download -d | grep WBD
m.tnm.download dataset=watershed-boundary-dataset type=huc8 code=01010001
```

## SEE ALSO

*[m.cdo.download](m.cdo.download.md)*

## AUTHOR

[Huidae Cho](mailto:grass4u@gmail-com), New Mexico State University
