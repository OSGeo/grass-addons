#!/usr/bin/env python

############################################################################
#
# MODULE:       g.proj.all
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#               Vaclav Petras (wenzeslaus gmail.com)
#
# PURPOSE:      Reproject the entire mapset
# COPYRIGHT:    (C) 2013 by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Reprojects raster and vector maps from given location and mapset to current mapset.
# % keyword: general
# % keyword: projection
# % keyword: transformation
# %end
# %option
# % key: location
# % key_desc: name
# % type: string
# % required: yes
# % description: Location containing input raster map
# % gisprompt: old,location,location
# % guisection: Source
# %end
# % option G_OPT_M_MAPSET
# % description: Mapset containing input raster map
# % required: yes
# % guisection: Source
# %end
# %option
# % key: dbase
# % key_desc: path
# % type: string
# % required: no
# % description: Path to GRASS database of input location
# % gisprompt: old,dbase,dbase
# %end
# %option
# % key: method
# % type: string
# % required: no
# % description: Interpolation method to use
# % guisection: Raster
# % answer: nearest
# % options: nearest,linear,cubic,lanczos,linear_f,cubic_f,lanczos_f
# % descriptions: nearest;nearest neighbor;linear;linear interpolation;cubic;cubic convolution;lanczos;lanczos filter;linear_f;linear interpolation with fallback;cubic_f;cubic convolution with fallback;lanczos_f;lanczos filter with fallback
# %end
# %option
# % key: resolution
# % type: double
# % required: no
# % description: Resolution of output raster map
# % guisection: Raster
# %end
# %flag
# % key: r
# % description: Use current region instead of maps bounds
# % guisection: Raster
# %end
# %flag
# % key: z
# % label: Assume z coordinate is ellipsoidal height and transform if possible
# % description: 3D vector maps only
# % guisection: Vector
# %end
# %flag
# % key: o
# % description: Allow output files to overwrite existing files
# %end


## location, mapset, dbase should be moved to one tab (Source)
## if we override Required (which is not possible now)


import sys
import atexit

from grass.script.utils import parse_key_val
from grass.script import core as gcore
from grass.exceptions import CalledModuleError


def main():
    options, flags = gcore.parser()

    location = options["location"]
    mapset = options["mapset"]
    dbase = options["dbase"]

    resolution = options["resolution"]
    if resolution:
        resolution = float(resolution)
    method = options["method"]
    curr_region = flags["r"]

    transform_z = flags["z"]
    overwrite = flags["o"]

    if not curr_region:
        gcore.use_temp_region()
        atexit.register(gcore.del_temp_region)
    if overwrite or gcore.overwrite():
        overwrite = True
    else:
        overwrite = False
    #
    # r.proj
    #
    parameters = dict(location=location, mapset=mapset, flags="l", overwrite=overwrite)
    if dbase:
        parameters.update(dict(dbase=dbase))
    # first run r.proj to see if it works
    try:
        gcore.run_command("r.proj", quiet=True, **parameters)
    except CalledModuleError:
        gcore.fatal(_("Module r.proj failed. Please check the error messages above."))
    # run again to get the raster maps
    rasters = gcore.read_command("r.proj", **parameters)
    rasters = rasters.strip().split()
    gcore.info(
        _(
            "{num} raster maps will be reprojected from mapset <{mapsetS}> "
            "to mapset <{mapsetT}>."
        ).format(num=len(rasters), mapsetS=mapset, mapsetT=gcore.gisenv()["MAPSET"])
    )

    parameters = dict(
        location=location, mapset=mapset, method=method, overwrite=overwrite
    )
    if resolution:
        parameters.update(dict(resolution=resolution))
    if dbase:
        parameters.update(dict(dbase=dbase))
    for raster in rasters:
        if not curr_region:
            bounds = gcore.read_command("r.proj", input=raster, flags="g", **parameters)
            bounds = parse_key_val(bounds, vsep=" ")
            gcore.run_command("g.region", **bounds)

        gcore.run_command("r.proj", input=raster, **parameters)

    #
    # v.proj
    #
    parameters = dict(location=location, mapset=mapset, flags="l", overwrite=overwrite)
    if dbase:
        parameters.update(dict(dbase=dbase))
    # first run v.proj to see if it works
    try:
        gcore.run_command("v.proj", quiet=True, **parameters)
    except CalledModuleError:
        gcore.fatal(_("Module v.proj failed. Please check the error messages above."))
    # run again to get the vector maps
    vectors = gcore.read_command("v.proj", **parameters)
    vectors = vectors.strip().split()
    gcore.info(
        _(
            "{num} vectors maps will be reprojected from mapset <{mapsetS}> "
            "to mapset <{mapsetT}>."
        ).format(num=len(vectors), mapsetS=mapset, mapsetT=gcore.gisenv()["MAPSET"])
    )

    parameters = dict(location=location, mapset=mapset, overwrite=overwrite)
    if transform_z:
        parameters.update(dict(flags="z"))
    for vector in vectors:
        gcore.run_command("v.proj", input=vector, **parameters)


if __name__ == "__main__":
    sys.exit(main())
