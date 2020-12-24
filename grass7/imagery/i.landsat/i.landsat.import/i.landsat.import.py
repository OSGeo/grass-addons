#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:      i.landsat.import
# AUTHOR(S):   Veronica Andreo
# PURPOSE:     Imports Landsat data downloaded from EarthExplorer using
#              i.landsat.download.
# COPYRIGHT:   (C) 2020-2021 by Veronica Andreo, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%module
#% description: Imports Landsat satellite data downloaded using i.landsat.download.
#% keyword: imagery
#% keyword: satellite
#% keyword: Landsat
#% keyword: import
#%end
#%option G_OPT_M_DIR
#% key: input
#% description: Name of input directory with downloaded Landsat data
#% required: yes
#%end
#%option G_OPT_M_DIR
#% key: unzip_dir
#% description: Name of directory into which Landsat zip-files are extracted (default=input)
#% required: no
#%end
#%option
#% key: pattern
#% description: Band name pattern to import
#% guisection: Filter
#%end
#%option
#% key: pattern_file
#% description: File name pattern to import
#% guisection: Filter
#%end
#%option
#% key: extent
#% type: string
#% required: no
#% multiple: no
#% options: input,region
#% answer: input
#% description: Output raster map extent
#% descriptions: region;extent of current region;input;extent of input map
#% guisection: Filter
#%end
#%option
#% key: memory
#% type: integer
#% required: no
#% multiple: no
#% label: Maximum memory to be used (in MB)
#% description: Cache size for raster rows
#% answer: 300
#%end
#%flag
#% key: r
#% description: Reproject raster data using r.import if needed
#% guisection: Settings
#%end
#%flag
#% key: l
#% description: Link raster data instead of importing
#% guisection: Settings
#%end
#%flag
#% key: o
#% description: Override projection check (use current location's projection)
#% guisection: Settings
#%end
#%flag
#% key: p
#% description: Print raster data to be imported and exit
#% guisection: Print
#%end
#%rules
#% exclusive: -l,-r,-p
#% exclusive: -o,-r
#% exclusive: extent,-l
#%end

import os
import sys
import glob
import re
import shutil
import grass.script as gs
from grass.exceptions import CalledModuleError


def _untar(inputdir, untardir):

    if not os.path.exists(inputdir):
        gs.fatal(_("Input directory <{}> does not exist").format(inputdir))

    if untardir is None or untardir == "":
        untardir = inputdir

    if not os.path.exists(untardir):
        gs.fatal(_("Directory <{}> does not exist").format(untardir))

    if options["pattern_file"]:
        filter_f = "*" + options["pattern_file"] + "*.tar.gz"
    else:
        filter_f = "*.tar.gz"

    scenes_to_untar = glob.glob(os.path.join(inputdir, filter_f))
    for scene in scenes_to_untar:
        shutil.unpack_archive(scene, untardir)

    untared_tifs = glob.glob(os.path.join(untardir, "*.TIF"))
    return untared_tifs


def _check_projection(filename):
    try:
        with open(os.devnull) as null:
            gs.run_command(
                "r.in.gdal", flags="j", input=filename, quiet=True, stderr=null
            )
    except CalledModuleError as e:
        return False

    return True


def _raster_resolution(filename):
    try:
        from osgeo import gdal
    except ImportError as e:
        gs.fatal(_("Flag -r requires GDAL library: {}").format(e))
    dsn = gdal.Open(filename)
    trans = dsn.GetGeoTransform()

    ret = int(trans[1])
    dsn = None

    return ret


def _raster_epsg(filename):
    try:
        from osgeo import gdal, osr
    except ImportError as e:
        gs.fatal(_("Flag -r requires GDAL library: {}").format(e))
    dsn = gdal.Open(filename)

    srs = osr.SpatialReference()
    srs.ImportFromWkt(dsn.GetProjectionRef())

    ret = srs.GetAuthorityCode(None)
    dsn = None

    return ret


def _map_name(filename):
    return os.path.splitext(os.path.basename(filename))[0]


def import_raster(filename, module, args):
    mapname = _map_name(filename)
    gs.message(_("Processing <{}>...").format(mapname))
    if module == "r.import":
        kv = gs.parse_command("g.proj", flags="j")
        if kv["+proj"] == "longlat":
            args["resolution"] = "estimated"
        else:
            args["resolution"] = "value"
            args["resolution_value"] = _raster_resolution(filename)
    try:
        gs.run_command(module, input=filename, output=mapname, **args)
        if gs.raster_info(mapname)["datatype"] in ("FCELL", "DCELL"):
            gs.message("Rounding to integer after reprojection")
            gs.use_temp_region()
            gs.run_command("g.region", raster=mapname)
            gs.run_command(
                "r.mapcalc",
                quiet=True,
                expression="tmp_%s = round(%s)" % (mapname, mapname),
            )
            gs.run_command(
                "g.rename",
                quiet=True,
                overwrite=True,
                raster="tmp_%s,%s" % (mapname, mapname),
            )
            gs.del_temp_region()
        gs.raster_history(mapname)
    except CalledModuleError as e:
        pass  # error already printed


def print_products(filenames):
    for f in filenames:
        sys.stdout.write(
            "{} {} (EPSG: {}){}".format(
                f, "1" if _check_projection(f) else "0", _raster_epsg(f), os.linesep
            )
        )


def main():

    inputdir = options["input"]
    untardir = options["unzip_dir"]

    files = _untar(inputdir, untardir)

    if options["pattern"]:
        filter_p = r".*{}.*.TIF$".format(options["pattern"])
    else:
        filter_p = r".*_B.*.TIF$"

    pattern = re.compile(filter_p)

    files_to_import = []
    for f in files:
        if pattern.match(f):
            files_to_import.append(f)

    if len(files_to_import) < 1:
        gs.fatal(
            _("Nothing found to import. Please check the input and pattern options.")
        )

    if flags["p"]:
        print_products(files_to_import)
    else:
        # which module to use for the import?
        args = {}
        module = ""
        if flags["l"]:
            module = "r.external"
            args["flags"] = "o" if flags["o"] else None
        else:
            args["memory"] = options["memory"]
            if flags["r"]:
                module = "r.import"
                args["resample"] = "bilinear"
                args["extent"] = options["extent"]
            else:
                module = "r.in.gdal"
                args["flags"] = "o" if flags["o"] else None
                if options["extent"] == "region":
                    if args["flags"]:
                        args["flags"] += "r"
                    else:
                        args["flags"] = "r"
        for f in files_to_import:
            if not flags["o"] and (flags["l"] or (not flags["l"] and not flags["r"])):
                if not _check_projection(f):
                    gs.fatal(
                        _(
                            "Projection of dataset does not match current location. "
                            "Force reprojection using -r flag."
                        )
                    )
            import_raster(f, module, args)

    # remove all tif files after import
    for f in files:
        os.remove(f)


if __name__ == "__main__":
    options, flags = gs.parser()
    main()
