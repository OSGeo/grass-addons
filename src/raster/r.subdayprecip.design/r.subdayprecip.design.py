#!/usr/bin/env python

############################################################################
#
# MODULE:       r.subdayprecip.design
#
# AUTHOR(S):    Martin Landa
#
# PURPOSE:      Computes subday design precipitation totals.
#
# COPYRIGHT:    (C) 2015 Martin Landa and GRASS development team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Computes subday design precipitation totals.
# % keyword: raster
# % keyword: hydrology
# % keyword: precipitation
# %end

# %option G_OPT_V_MAP
# % label: Vector map of location under analysis
# %end

# %option G_OPT_R_INPUTS
# % key: return_period
# % description: Rainfall raster maps of required return period
# % options: N2,N5,N10,N20,N50,N100
# %end

# %option
# % key: rainlength
# % description: Design rainfall length in minutes
# % type: integer
# % options: 0-1439
# % required: yes
# %end

# %option
# % key: area_size
# % description: Maximum area size to be processed (in km2, -1 for no limit)
# % type: double
# % answer: 20
# %end

import os
import sys

import grass.script as grass
from grass.pygrass.modules import Module
from grass.exceptions import CalledModuleError


def coeff(name, rl):
    a = c = None
    if name == "N2":
        if rl < 40:
            a = 0.166
            c = 0.701
        elif rl < 120:
            a = 0.237
            c = 0.803
        elif rl < 1440:
            a = 0.235
            c = 0.801
    elif name == "N5":
        if rl < 40:
            a = 0.171
            c = 0.688
        elif rl < 120:
            a = 0.265
            c = 0.803
        elif rl < 1440:
            a = 0.324
            c = 0.845
    elif name == "N10":
        if rl < 40:
            a = 0.163
            c = 0.656
        elif rl < 120:
            a = 0.280
            c = 0.803
        elif rl < 1440:
            a = 0.380
            c = 0.867
    elif name == "N20":
        if rl < 40:
            a = 0.169
            c = 0.648
        elif rl > 40 and rl < 120:
            a = 0.300
            c = 0.803
        elif rl < 1440:
            a = 0.463
            c = 0.894
    elif name == "N50":
        if rl < 40:
            a = 0.174
            c = 0.638
        elif rl < 120:
            a = 0.323
            c = 0.803
        elif rl < 1440:
            a = 0.580
            c = 0.925
    elif name == "N100":
        if rl < 40:
            a = 0.173
            c = 0.625
        elif rl < 120:
            a = 0.335
            c = 0.803
        elif rl < 1440:
            a = 0.642
            c = 0.939

    return a, c


def main():
    # check if the map is in the current mapset
    mapset = grass.find_file(opt["map"], element="vector")["mapset"]
    if not mapset or mapset != grass.gisenv()["MAPSET"]:
        grass.fatal(
            _("Vector map <{}> not found in the current mapset").format(opt["map"])
        )

    # get list of existing columns
    try:
        columns = grass.vector_columns(opt["map"]).keys()
    except CalledModuleError as e:
        return 1

    allowed_rasters = ("N2", "N5", "N10", "N20", "N50", "N100")

    # test input feature type
    vinfo = grass.vector_info_topo(opt["map"])
    if vinfo["areas"] < 1 and vinfo["points"] < 1:
        grass.fatal(
            _("No points or areas found in input vector map <{}>").format(opt["map"])
        )

    # check area size limit
    check_area_size = float(opt["area_size"]) > 0
    if check_area_size:
        area_col_name = "area_{}".format(os.getpid())
        Module(
            "v.to.db",
            map=opt["map"],
            option="area",
            units="kilometers",
            columns=area_col_name,
            quiet=True,
        )
        areas = Module(
            "v.db.select",
            flags="c",
            map=opt["map"],
            columns=area_col_name,
            where="{} > {}".format(area_col_name, opt["area_size"]),
            stdout_=grass.PIPE,
        )
        large_areas = len(areas.outputs.stdout.splitlines())
        if large_areas > 0:
            grass.warning(
                "{} areas larger than size limit will be skipped from computation".format(
                    large_areas
                )
            )

    # extract multi values to points
    for rast in opt["return_period"].split(","):
        # check valid rasters
        name = grass.find_file(rast, element="cell")["name"]
        if not name:
            grass.warning("Raster map <{}> not found. " "Skipped.".format(rast))
            continue
        if name not in allowed_rasters:
            grass.warning(
                "Raster map <{}> skipped. " "Allowed: {}".format(rast, allowed_rasters)
            )
            continue

        # perform zonal statistics
        grass.message("Processing <{}>...".format(rast))
        table = "{}_table".format(name)
        if vinfo["areas"] > 0:
            Module(
                "v.rast.stats",
                flags="c",
                map=opt["map"],
                raster=rast,
                column_prefix=name,
                method="average",
                quiet=True,
            )
            # handle NULL values (areas smaller than raster resolution)
            null_values = Module(
                "v.db.select",
                map=opt["map"],
                columns="cat",
                flags="c",
                where="{}_average is NULL".format(name),
                stdout_=grass.PIPE,
            )
            cats = null_values.outputs.stdout.splitlines()
            if len(cats) > 0:
                grass.warning(
                    _(
                        "Input vector map <{}> contains very small areas (smaller than "
                        "raster resolution). These areas will be proceeded by querying "
                        "single raster cell."
                    ).format(opt["map"])
                )
                Module(
                    "v.what.rast",
                    map=opt["map"],
                    raster=rast,
                    type="centroid",
                    column="{}_average".format(name),
                    where="{}_average is NULL".format(name),
                    quiet=True,
                )
        else:  # -> points
            Module(
                "v.what.rast",
                map=opt["map"],
                raster=rast,
                column="{}_average".format(name),
                quiet=True,
            )

        # add column to the attribute table if not exists
        rl = float(opt["rainlength"])
        field_name = "H_{}T{}".format(name, opt["rainlength"])
        if field_name not in columns:
            Module(
                "v.db.addcolumn",
                map=opt["map"],
                columns="{} double precision".format(field_name),
            )

        # determine coefficient for calculation
        a, c = coeff(rast, rl)
        if a is None or c is None:
            grass.fatal("Unable to calculate coefficients")

        # calculate output values, update attribute table
        coef = a * rl ** (1 - c)
        expression = "{}_average * {}".format(name, coef)
        Module(
            "v.db.update", map=opt["map"], column=field_name, query_column=expression
        )

        if check_area_size:
            Module(
                "v.db.update",
                map=opt["map"],
                column=field_name,
                value="-1",
                where="{} > {}".format(area_col_name, opt["area_size"]),
            )

        # remove unused column
        Module("v.db.dropcolumn", map=opt["map"], columns="{}_average".format(name))

    if check_area_size:
        # remove unused column
        Module("v.db.dropcolumn", map=opt["map"], columns=area_col_name)

    return 0


if __name__ == "__main__":
    opt, flg = grass.parser()
    sys.exit(main())
