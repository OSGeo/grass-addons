# Test r.mapcalc.tiled with different parameters vs. r.mapcalc


`test.py` is a script for testing `r.mapcalc.tiled` vs `r.mapcalc`. In the
`config.ini` you can set some general parameters like the map on which
the region has to be set, the `r.mapcalc` expression and the number of
processes, as well as the parameters of `r.mapcalc.tiled` to be tested.
These parameters concern the resolutions and the width/height. Also the
name of the output CSV file can be set.

## Usage

The script can be executed in a GRASS GIS session (North Carolina sample
dataset) with:

`python3 test.py config.ini`

`visualization.py` is a script to visualize the result of the `test.py` output CSV file.
It can be executed with

`python3 visualization.py rmapcalctiled_test.csv images`

where the first argument is the resulting CSV file from `test.py` and the
second is a folder where the images are stored as PNG files.
