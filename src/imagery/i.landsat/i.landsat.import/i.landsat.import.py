#!/usr/bin/env python

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

# %module
# % description: Imports Landsat satellite data downloaded using i.landsat.download.
# % keyword: imagery
# % keyword: satellite
# % keyword: Landsat
# % keyword: import
# %end

# %option G_OPT_M_DIR
# % key: input
# % description: Name of input directory with downloaded Landsat data
# % required: yes
# %end

# %option G_OPT_M_DIR
# % key: unzip_dir
# % description: Name of directory into which Landsat zip-files are extracted (default=input)
# % required: no
# %end

# %option
# % key: pattern
# % description: Band name pattern to import
# % guisection: Filter
# %end

# %option
# % key: pattern_file
# % description: File name pattern to import
# % guisection: Filter
# %end

# %option
# % key: extent
# % type: string
# % required: no
# % multiple: no
# % options: input,region
# % answer: input
# % description: Output raster map extent
# % descriptions: region;extent of current region;input;extent of input map
# % guisection: Output
# %end

# %option
# % key: resample
# % type: string
# % required: no
# % multiple: no
# % options: nearest,bilinear,bicubic,lanczos,bilinear_f,bicubic_f,lanczos_f
# % description: Resampling method to use for reprojection
# % descriptions: nearest;nearest neighbor;bilinear;bilinear interpolation;bicubic;bicubic interpolation;lanczos;lanczos filter;bilinear_f;bilinear interpolation with fallback;bicubic_f;bicubic interpolation with fallback;lanczos_f;lanczos filter with fallback
# % answer: nearest
# % guisection: Output
# %end

# %option
# % key: memory
# % type: integer
# % required: no
# % multiple: no
# % label: Maximum memory to be used (in MB)
# % description: Cache size for raster rows
# % answer: 300
# % guisection: Settings
# %end

# %option G_OPT_F_OUTPUT
# % key: register_output
# % description: Name for output file to use with t.register
# % required: no
# % guisection: Output
# %end

# %flag
# % key: r
# % description: Reproject raster data using r.import if needed
# % guisection: Settings
# %end

# %flag
# % key: l
# % description: Link raster data instead of importing
# % guisection: Settings
# %end

# %flag
# % key: o
# % description: Override projection check (use current location's projection)
# % guisection: Settings
# %end

# %flag
# % key: p
# % description: Print raster data to be imported and exit
# % guisection: Print
# %end

# %rules
# % exclusive: -l,-r,-p
# % exclusive: -o,-r
# % exclusive: extent,-l
# %end

import os
import sys
import glob
import re
import tarfile
from datetime import *
import grass.script as gs
from grass.exceptions import CalledModuleError


def _untar(inputdir, untardir):

    if not os.path.exists(inputdir):
        gs.fatal(_("Directory <{}> does not exist").format(inputdir))
    if not os.path.isdir(inputdir):
        gs.fatal(_("<{}> is not a directory").format(inputdir))
    elif not os.access(inputdir, os.W_OK):
        gs.fatal(_("Directory <{}> is not writable.").format(inputdir))

    if untardir is None or untardir == "":
        untardir = inputdir
    else:
        if not os.path.exists(untardir):
            gs.fatal(_("Directory <{}> does not exist").format(untardir))
        if not os.path.isdir(untardir):
            gs.fatal(_("<{}> is not a directory").format(untardir))
        elif not os.access(untardir, os.W_OK):
            gs.fatal(_("Directory <{}> is not writable.").format(untardir))

    if options["pattern_file"]:
        filter_f = "*" + options["pattern_file"] + "*.tar.gz"
    else:
        filter_f = "*.tar.gz"

    scenes_to_untar = glob.glob(os.path.join(inputdir, filter_f))

    for scene in scenes_to_untar:
        with tarfile.open(name=scene, mode="r") as tar:

            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")

                tar.extractall(path, members, numeric_owner=numeric_owner)

            safe_extract(tar, untardir)

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


def write_register_file(filenames, register_output):
    gs.message(_("Creating register file <{}>...").format(register_output))
    has_band_ref = float(gs.version()["version"][0:3]) >= 7.9
    sep = "|"

    with open(register_output, "w") as fd:
        for img_file in filenames:
            map_name = _map_name(img_file)
            satellite = map_name.strip()[3]
            timestamp_str = map_name.split("_")[3]
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d").strftime("%Y-%m-%d")
            fd.write("{img}{sep}{ts}".format(img=map_name, sep=sep, ts=timestamp))
            if has_band_ref:
                try:
                    band_ref = re.match(r".*_B([1-9]+).*", map_name).groups()
                    band_ref = band_ref[0] if band_ref[0] else band_ref[1]
                except AttributeError:
                    gs.warning(
                        _("Unable to determine band reference for <{}>").format(
                            map_name
                        )
                    )
                    continue
                fd.write(
                    "{sep}{br}".format(sep=sep, br="L{}_{}".format(satellite, band_ref))
                )
            fd.write(os.linesep)


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
                args["resample"] = options["resample"]
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

    if options["register_output"]:
        write_register_file(files_to_import, options["register_output"])

    # remove all tif files after import
    for f in files:
        os.remove(f)


if __name__ == "__main__":
    options, flags = gs.parser()
    main()
