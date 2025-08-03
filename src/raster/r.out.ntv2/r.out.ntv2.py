#!/usr/bin/env python
#
############################################################################
#
# MODULE:      r.out.ntv2
# AUTHOR(S):   Maciej Sieczka
# PURPOSE:     Export NTv2 datum transformation grid.
# COPYRIGHT:   (C) 2016 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

# %Module
# % description: Exports NTv2 datum transformation grid
# %End

# %option
# % key: latshift
# % type: string
# % gisprompt: old,cell,raster
# % description: Input raster map of lattitude datum shift values
# % required : yes
# %end

# %option
# % key: lonshift
# % type: string
# % gisprompt: old,cell,raster
# % description: Input raster map of longitude datum shift values
# % required : yes
# %end

# %option
# % key: output
# % type: string
# % description: Output NTv2 datum transformation grid file
# % gisprompt: new_file,file,output
# % required: yes
# %end

# %option
# % key: systemt
# % type: string
# % description: Transformation grid's destination coordinate system name
# % required : no
# % answer: WGS84
# %end

# %option
# % key: majort
# % type: string
# % description: Major ellipsoid axis of the transformation grid's destination coordinate system
# % required : no
# % answer: 6378137
# %end

# %option
# % key: minort
# % type: string
# % description: Minor ellipsoid axis of the transformation grid's destination coordinate system
# % required : no
# % answer: 6356752.314245
# %end

# %option
# % key: systemf
# % type: string
# % description: Transformation grid's input coordinate system name
# % required : no
# % answer: UNKNOWN
# %end

# %option
# % key: majorf
# % type: string
# % description: Major ellipsoid axis of the transformation grid's input coordinate system
# % required : no
# % answer: UNKNOWN
# %end

# %option
# % key: minorf
# % type: string
# % description: Minor ellipsoid axis of the transformation grid's input coordinate system
# % required : no
# % answer: UNKNOWN
# %end

"""
SYSTEM_F, SYSTEM_T, MAJOR_F, MINOR_F, MAJOR_T, MINOR_T are not used for
anything in GDAL or PROJ.4. They will always assume the *_T system is WGS84 and
the *_F system's parameters are simply ignored. It makes sense setting these
for documentation's sake only.

More about NTv2 format on https://github.com/Esri/ntv2-file-routines.
"""

import atexit
import sys
import uuid
import time
from grass.script import core as grass

tmp_group = str(uuid.uuid4())


def cleanup():
    grass.run_command("g.remove", type="group", name=tmp_group, flags="f", quiet=True)


def main():
    grass.run_command(
        "i.group",
        input=(options["latshift"], options["lonshift"]),
        group=tmp_group,
        quiet=True,
    )

    grass.run_command(
        "r.out.gdal",
        input=tmp_group,
        output=options["output"],
        format="NTv2",
        type="Float32",
        quiet=True,
        metaopt=(
            "CREATED=" + time.strftime("%Y%m%d"),
            "GS_TYPE=SECONDS",
            "SYSTEM_T=" + options["systemt"],
            "MAJOR_T=" + options["majort"],
            "MINOR_T=" + options["minort"],
            "SYSTEM_F=" + options["systemf"],
            "MAJOR_F=" + options["majorf"],
            "MINOR_F=" + options["minorf"],
            "PARENT=NONE",
            "SUB_NAME=NONE",
            "UPDATED=" + time.strftime("%H%M%S"),
            "VERSION=NTv2.0",
        ),
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
