#!/usr/bin/env bash

# fail on non-zero return code from a subprocess
set -e

# Install module from addons if not available (in v7).
if ! grass --tmp-project XY --exec g.download.location --help; then
    grass --tmp-project XY --exec \
        g.extension g.download.location
fi
grass --tmp-project XY --exec \
    g.download.location url=https://grass.osgeo.org/sampledata/north_carolina/nc_spm_full_v2alpha2.tar.gz path=$HOME

grass --tmp-project XY --exec \
    python3 -m grass.gunittest.main \
        --grassdata $HOME --location nc_spm_full_v2alpha2 --location-type nc \
        --min-success 60
