## DESCRIPTION

*m.cdo.download* downloads data from [NCEI's Climate Data Online
(CDO)](https://www.ncei.noaa.gov/cdo-web/webservices/v2) using their v2
API.

## NOTES

This module uses [the CDO Web Services v2
API](https://www.ncei.noaa.gov/cdo-web/api/v2/) to download CDO data.

To access the API services, obtain your CDO API token from the
[NCEI CDO Web Services Token Request page](https://www.ncei.noaa.gov/cdo-web/token)
and set it as the `CDO_API_TOKENS` environment variable. If you have multiple
tokens, separate them with commas. For example:

```sh
export CDO_API_TOKENS=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
```

## EXAMPLES

List available datasets:

```sh
m.cdo.download fetch=datasets
```

List available dataset IDs without column names:

```sh
m.cdo.download -c fetch=datasets fields=id
```

List available stations within (47.5204,-122.2047)-(47.6139,-122.1065):

```sh
m.cdo.download fetch=stations extent=47.5204,-122.2047,47.6139,-122.1065
```

List available "precipitation" and "average temperature" data types:

```sh
m.cdo.download fetch=datatypes field=id,mindate,maxdate,name |
grep -i "|precipitation\||average temperature"
```

List 10 available stations with PRCP and TAVG data starting 2023-01-01:

```sh
m.cdo.download fetch=stations datatypeid=PRCP,TAVG startdate=2023-01-01 limit=10
```

Fetch daily PRCP and TAVG data for a station with mindate ≤ 2023-01-01
and save it into a file:

```sh
# find dataset IDs for data types PRCP and TAVG; let's use GHCND (Daily Summary)
m.cdo.download fetch=datasets datatypeid=PRCP,TAVG

# find the first station ID with mindate ≤ 2023-01-01
stationid=$(m.cdo.download -c fetch=stations datatypeid=PRCP,TAVG \
    startdate=2023-01-01 fields=id limit=1)

# fetch actual data and save it to data.txt
m.cdo.download fetch=data datasetid=GHCND datatypeid=PRCP,TAVG \
    stationid=$stationid startdate=2023-01-01 enddate=2023-10-15 \
    output=data.txt
```

Create a point vector map with all stations:

```sh
# from a latlong location

# download metadata for all stations
m.cdo.download stations output=cdo_stations.txt

# import cdo_stations.txt
xy=$(awk -F'|' '{
    if (NR == 1) {
        for (i = 1; i <= NF; i++)
            if ($i == "latitude")
                latind = i
            else if ($i == "longitude")
                lonind = i
        printf "x=%s y=%s", lonind, latind
        exit
    }
}' cdo_stations.txt)
v.in.ascii input=cdo_stations.txt output=cdo_stations skip=1 $xy

# rename columns
old_cols=$(db.columns table=cdo_stations exclude=cat)
new_cols=$(head -1 cdo_stations.txt | sed 's/|/ /g')

for old_new in $(echo $old_cols $new_cols |
    awk '{
        n = NF / 2
        for (i = 1; i <= n; i++)
            printf "%s,%s\n", $i, $(i + n)
    }'); do
    v.db.renamecolumn map=cdo_stations column=$old_new
done
```

![image-alt](m_cdo_download_cdo_stations.png)

## SEE ALSO

*[m.tnm.download](m.tnm.download.md)*

## AUTHOR

[Huidae Cho](mailto:grass4u@gmail-com), New Mexico State University
