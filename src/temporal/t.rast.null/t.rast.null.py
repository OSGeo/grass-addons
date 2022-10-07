#!/usr/bin/env python


################################################
#
# MODULE:       t.rast.null
# AUTHOR(S):    Luca Delucchi
# PURPOSE:      Manages NULL-values of a given space time raster dataset.
#
# COPYRIGHT:    (C) 2018 by Luca Delucchi
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
################################################

# %module
# % description: Manages NULL-values of a given space time raster dataset.
# % keyword: temporal
# % keyword: raster
# % keyword: null data
# % keyword: parallel
# %end

# %option G_OPT_STRDS_INPUT
# %end

# %option
# % key: setnull
# % type: string
# % label: List of cell values to be set to NULL
# % multiple: yes
# % required: no
# %end

# %option
# % key: null
# % type: double
# % label: The value to replace the null value by
# % multiple: no
# % required: no
# %end

# %option G_OPT_T_WHERE
# %end

# %option
# % key: nprocs
# % type: integer
# % description: Number of r.null processes to run in parallel
# % required: no
# % multiple: no
# % answer: 1
# %end

import copy
import sys

import grass.temporal as tgis
import grass.script as gscript
import grass.pygrass.modules as pymod


def main():
    strds = options["input"]
    where = options["where"]
    nprocs = int(options["nprocs"])

    nullmod = pymod.Module("r.null")
    nullmod.flags.quiet = True
    if options["null"]:
        nullmod.inputs.null = options["null"]
    elif options["setnull"]:
        nullmod.inputs.setnull = options["setnull"]
    else:
        gscript.fatal(_("Please set 'null' or 'setnull' option"))

    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    sp = tgis.open_old_stds(strds, "strds", dbif)
    maps = sp.get_registered_maps_as_objects(where, "start_time", None)
    if maps is None:
        gscript.fatal(
            _("Space time raster dataset {st} seems to be " "empty".format(st=strds))
        )
        return 1
    # module queue for parallel execution
    process_queue = pymod.ParallelModuleQueue(int(nprocs))

    count = 0
    num_maps = len(maps)

    for mapp in maps:
        count += 1
        mod = copy.deepcopy(nullmod)
        mod.inputs.map = mapp.get_id()
        process_queue.put(mod)

        if count % 10 == 0:
            gscript.percent(count, num_maps, 1)

    # Wait for unfinished processes
    process_queue.wait()


if __name__ == "__main__":
    options, flags = gscript.parser()
    sys.exit(main())
