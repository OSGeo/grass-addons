## DESCRIPTION

*i.modis.download* downloads selected MODIS products (Moderate
Resolution Imaging Spectroradiometer, flown on the two NASA spacecrafts
Terra and Aqua). The module can download several tiles at once and also
multiple observation dates for each MODIS product.

## NOTES

The *i.modis* modules need the [pyModis](https://www.pymodis.org)
library. Please install it beforehand.

To be able to download data the user needs to obtain *user* and
*password* for the NASA Earthdata Login:

  - First time user: The user has to register at
    <https://urs.earthdata.nasa.gov/users/new>; then login and change to
    their [profile page](https://urs.earthdata.nasa.gov/profile). Once
    there, under the "Applications" tab \> "Authorized Apps", the user
    needs to approve the following applications (there is a search box
    that makes it easier to find the items):
      - "LP DAAC Data Pool", and
      - "Earthdata Search".
  - If the user is already registered, he/she just needs to login and
    enable the aforementioned applications at
    <https://urs.earthdata.nasa.gov/home> if not already done.

In order to download the desired MODIS product(s), the username and
password must be provided through the *settings* option. There are three
ways:

  - using the
    [.netrc](https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html)
    file as showed below:
    
    ```sh
    machine e4ftl01.cr.usgs.gov
    login your_NASA_username
    password your_NASA_password
    ```
    

  - pass a file in which the first row is the username, and the second
    row is the password, as showed below:
    
    ```sh
    your_NASA_username
    your_NASA_password
    ```
    

  - the user can pass the values from the standard input when prompted.

**Warning**: As per NASA policy no more than ten simultaneous
connections are permitted in parallel with their server. Hence, no more
than ten processes of *i.modis.download* should run at the same time to
avoid that user's actual IP address gets blacklisted.

By default, the downloaded files are stored in the path in which the
settings file was saved. The user can change this directory with the
*folder* option. The *folder* option is required when user and password
are passed through the standard input.

The needed time for the download depends on the number of requested
tiles, days and the type of MODIS product. For example, the NDVI product
ranges from 5 MB to 270 MB and the LST product ranges from 2 MB to 21
MB.

## EXAMPLES

### MODIS NDVI Global with stored credentials

Download of the global MODIS product *MOD13C1 - MODIS/Terra Vegetation
Indices 16-Day L3 Global 0.05Deg CMG V006* by selecting a specific
month, using the credentials conveniently stored in

```sh
$HOME/.netrc
```

file:

```sh
# note: provided in Geographic Lat/Long Grid
i.modis.download product=ndvi_terra_sixteen_5600 startday=2020-05-01 endday=2020-05-31 folder=/path/to/modisdata/
```

### MODIS Land Surface Temperature

Download of the daily MODIS LST product "lst\_terra\_daily\_1000" from
the Terra satellite using the default options (all available tiles from
newest available date) and passing the user and password through
standard input. Note that when settings is read from standard input, the
option folder must be specified:

```sh
i.modis.download settings=- folder=/path/to/modisdata/
```

Reading the user and password options from a file (this will download by
default the "lst\_terra\_daily\_1000" product). MODIS data will be
downloaded to the folder where the SETTING file is:

```sh
i.modis.download settings=$HOME/.grass8/i.modis/SETTING
```

Download of the LST Terra product using the default options and change
of the starting and ending dates to custom values:

```sh
i.modis.download settings=$HOME/.grass8/i.modis/SETTING startday=2011-05-01 endday=2011-05-31 folder=/path/to/modisdata/
```

### MODIS Snow

Download of a different product (here: *Snow eight days 500 m*), default
options (for settings, see example above):

```sh
i.modis.download settings=$HOME/.grass8/i.modis/SETTING product=snow_terra_eight_500 folder=/path/to/modisdata/
```

### MODIS NDVI Global

Download of a global MODIS product (here: *MOD13C1 - MODIS/Terra
Vegetation Indices 16-Day L3 Global 0.05Deg CMG V061*), of a specific
month (for settings, see example above):

```sh
# note: provided in Geographic Lat/Long Grid
i.modis.download settings=$HOME/.grass8/i.modis/SETTING product=ndvi_terra_sixteen_5600 startday=2011-05-01 endday=2011-05-31 folder=/path/to/modisdata/
```

### Download of MODIS data in scripts

To use *i.modis.download* in a script and to concatenate it with another
module, the user needs to set the *-g* flag to return the name of the
file that contains the list of downloaded HDF files:

```sh
i.modis.download -g settings=$HOME/.grass8/i.modis/SETTING startday=2011-05-01 endday=2011-05-31 folder=/path/to/modisdata/
```

## SEE ALSO

*[i.modis](i.modis.md), [i.modis.import](i.modis.import.md)*

[GRASS GIS Wiki: temporal data
processing](https://grasswiki.osgeo.org/wiki/Temporal_data_processing)

[Map of MODIS Land products' Sinusoidal grid tiling
system](https://modis-land.gsfc.nasa.gov/MODLAND_grid.html)

## AUTHOR

Luca Delucchi, Google Summer of Code 2011; subsequently updated.
