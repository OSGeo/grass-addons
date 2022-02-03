#!/usr/bin/env python
#
##############################################################################
#
# MODULE:       Minimum Redundancy Maximum Relevance Feature Selection
#
# AUTHOR(S):    Steven Pawley
#
##############################################################################
# %module
# % description: Perform Minimum Redundancy Maximum Relevance Feature Selection on a GRASS Attribute Table
# %end

# %option G_OPT_V_INPUT
# % description: Vector features
# % key: table
# % required : yes
# %end

# %option G_OPT_V_FIELD
# % key: layer
# % required : yes
# %end

# %option
# % description: Discretization threshold
# % key: threshold
# % type: double
# % answer: 1.0
# % required : no
# % guisection: Options
# %end

# %option
# % description: Number of features (attributes)
# % key: nfeatures
# % type: integer
# % answer: 50
# % required : yes
# % guisection: Options
# %end

# %option
# % description: Maximum number of samples
# % key: nsamples
# % type: integer
# % answer: 1000
# % required : yes
# % guisection: Options
# %end

# %option
# % description: Maximum number of variables/attributes
# % key: maxvar
# % type: integer
# % answer: 10000
# % required : yes
# % guisection: Options
# %end

# %option
# % description: Feature selection method
# % key: method
# % type: string
# % options: MID,MIQ
# % answer: MID
# % required : yes
# % guisection: Options
# %end

import sys
import os
import subprocess
import shutil

import grass.script as grass
import tempfile
import atexit
import os.path

# env = grass.gisenv()
# gisdbase = env['GISDBASE']
# location = env['LOCATION_NAME']
# mapset = env['MAPSET']
# path = os.path.join(gisdbase, location, mapset, 'sqlite.db')

tmpdir = tempfile.mkdtemp()
tmptable = "mrmrdat.csv"


def cleanup():
    shutil.rmtree(tmpdir)
    return 0


def main():
    table = options["table"]
    layer = options["layer"]
    threshold = options["threshold"]
    nfeatures = options["nfeatures"]
    maxvar = options["maxvar"]
    nsamples = options["nsamples"]
    method = options["method"]

    os.chdir(tmpdir)

    grass.run_command(
        "v.out.ogr",
        input=table,
        layer=layer,
        type="auto",
        output=tmpdir + "/" + tmptable,
        format="CSV",
        flags="s",
    )

    mrmrcmd = (
        "mrmr -i "
        + tmptable
        + " -m "
        + method
        + " -t "
        + threshold
        + " -n "
        + nfeatures
        + " -s "
        + nsamples
        + " -v "
        + maxvar
    )

    subprocess.call(mrmrcmd, shell=True)

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
