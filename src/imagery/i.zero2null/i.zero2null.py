#!/usr/bin/env python
############################################################################
#
# MODULE:       i.zero2null
# AUTHOR(S):    Markus Metz
# PURPOSE:      Replaces zero values with either NULL or appropriate neighboring values.
# COPYRIGHT: (C) 2020 by mundialis and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################

# %module
# % description: Replaces zero values with null at edges, otherwise replaces zero values with appropriate neighboring values.
# % keyword: imagery
# % keyword: satellite
# %end

# %option G_OPT_R_MAPS
# %end


import sys
import os
import shutil
import atexit
import grass.script as gs

# initialize global vars
rm_region = None
rm_rasters = []


def cleanup():
    if (
        rm_region is not None
        and gs.find_file(name=rm_region, element="windows", mapset=".")["name"]
    ):
        gs.run_command("g.region", region=rm_region)
        gs.run_command("g.remove", type="region", name=rm_region, flags="f", quiet=True)
    for rmrast in rm_rasters:
        if gs.find_file(name=rmrast, element="cell", mapset=".")["name"]:
            gs.run_command(
                "g.remove", type="raster", name=rmrast, flags="f", quiet=True
            )


def main():
    inmaps = options["map"].split(",")

    # save current region
    # why is this global needed for rm_region but not for rm_rasters ?
    global rm_region
    rm_region = "i_zero2null_region_" + str(os.getpid())
    gs.run_command("g.region", save=rm_region)

    gisenv = gs.gisenv()

    for inmap in inmaps:
        gs.message("Processing <%s>..." % inmap)
        # check if map is in current mapset
        inmap = inmap.split("@")[0]
        mapname = gs.find_file(name=inmap, element="cell", mapset=".")["name"]
        if mapname is None or len(mapname) == 0:
            gs.warning("Raster map <%s> is not in the current mapset." % mapname)
            continue

        # set current region to map
        gs.run_command("g.region", raster=inmap)

        # check if there are any zero cells
        rinfo = gs.raster_info(inmap)
        if rinfo["datatype"] != "CELL":
            gs.warning(
                "Input map <%s> is not of CELL type but %s."
                % (inmap, rinfo["datatype"])
            )
            continue

        if rinfo["min"] > 0:
            gs.message("No zero cells in input map <%s>, nothing to do." % inmap)
            continue

        gs.run_command("g.region", raster=inmap)

        # create clumps of zero cells
        # reclass rules
        tmpfile = gs.tempfile()
        f = open(tmpfile, "w")
        f.write("0 = 1\n")
        f.write("* = NULL\n")
        f.close()

        gs.run_command("r.reclass", input=inmap, output=inmap + "_rcl", rules=tmpfile)
        gs.try_remove(tmpfile)
        rm_rasters.append(inmap + "_rcl")

        gs.run_command("r.clump", input=inmap + "_rcl", output=inmap + "_rcl_clump")

        map_region = gs.region()

        # get center coordinates of the corner pixels
        nc = map_region["n"] - map_region["nsres"] / 2.0
        sc = map_region["s"] + map_region["nsres"] / 2.0
        ec = map_region["e"] - map_region["ewres"] / 2.0
        wc = map_region["w"] + map_region["ewres"] / 2.0

        # get clump IDs of corner cells
        corner_clumps = []
        # strip line endings from r.what output
        clump = (
            gs.read_command(
                "r.what", map=inmap + "_rcl_clump", coordinates=("%s,%s" % (wc, nc))
            )
            .rstrip()
            .split("|")[3]
        )
        if clump != "*" and clump not in corner_clumps:
            corner_clumps.append(clump)

        clump = (
            gs.read_command(
                "r.what", map=inmap + "_rcl_clump", coordinates=("%s,%s" % (ec, nc))
            )
            .rstrip()
            .split("|")[3]
        )
        if clump != "*" and clump not in corner_clumps:
            corner_clumps.append(clump)

        clump = (
            gs.read_command(
                "r.what", map=inmap + "_rcl_clump", coordinates=("%s,%s" % (ec, sc))
            )
            .rstrip()
            .split("|")[3]
        )
        if clump != "*" and clump not in corner_clumps:
            corner_clumps.append(clump)

        clump = (
            gs.read_command(
                "r.what", map=inmap + "_rcl_clump", coordinates=("%s,%s" % (wc, sc))
            )
            .rstrip()
            .split("|")[3]
        )
        if clump != "*" and clump not in corner_clumps:
            corner_clumps.append(clump)

        # check if any clumps are not covered by corner cells:
        # internal patches of zero cells
        clumpinfo = gs.raster_info(inmap + "_rcl_clump")
        maptomask = None
        n_inner_clumps = int(clumpinfo["max"]) - len(corner_clumps)
        if n_inner_clumps > 0:
            gs.message("Filling %(n)d inner clumps..." % {"n": n_inner_clumps})
            exp = "%(inmap)s_nozero = if(%(inmap)s == 0, null(), %(inmap)s)" % {
                "inmap": inmap
            }
            gs.mapcalc(exp)
            rm_rasters.append(inmap + "_nozero")
            gs.run_command(
                "r.grow.distance", input=inmap + "_nozero", value=inmap + "_nearest_flt"
            )
            rm_rasters.append(inmap + "_nearest_flt")
            exp = "%(inmap)s_nearest = round(%(inmap)s_nearest_flt)" % {"inmap": inmap}
            gs.mapcalc(exp)
            rm_rasters.append(inmap + "_nearest")
            gs.run_command(
                "r.patch",
                input="%(inmap)s_nearest,%(inmap)s_nozero" % {"inmap": inmap},
                output=inmap + "_filled",
            )
            rm_rasters.append(inmap + "_filled")
            maptomask = inmap + "_filled"
        else:
            maptomask = inmap

        # corner clumps of zero cells
        if len(corner_clumps) > 0:
            gs.message("Removing %(n)d corner clumps..." % {"n": len(corner_clumps)})
            corner_clumps = sorted(set(corner_clumps))
            tmpfile = gs.tempfile()
            f = open(tmpfile, "w")
            have_corner_clumps = False
            for clump in corner_clumps:
                f.write("%s = 1\n" % clump)
                have_clump = True

            # create a nodata mask and set masked cells to null
            f.write("* = NULL\n")
            f.close()
            gs.run_command(
                "r.reclass",
                input=inmap + "_rcl_clump",
                output=inmap + "_nodatamask",
                rules=tmpfile,
            )
            gs.try_remove(tmpfile)
            rm_rasters.append(inmap + "_nodatamask")

            exp = (
                "%(inmap)s_null = if(isnull(%(inmap)s_nodatamask), %(maptomask)s, null())"
                % {"inmap": inmap, "maptomask": maptomask}
            )
            gs.mapcalc(exp)
        else:
            if maptomask != inmap:
                gs.run_command(
                    "g.rename",
                    raster="%(maptomask)s,%(inmap)s_null"
                    % {"maptomask": maptomask, "inmap": inmap},
                    quiet=True,
                )

        # *_rcl_clump are base maps for reclassed maps, need to be removed last
        rm_rasters.append(inmap + "_rcl_clump")

        # list of support files to be preserved:
        # cell_misc/<inmap>/timestamp
        # cell_misc/<inmap>/description.json
        # copy hist/<inmap>
        # colr/<inmap>
        # anything missing ?

        # copy cell_misc/<inmap>/timestamp
        path = os.path.join(
            gisenv["GISDBASE"],
            gisenv["LOCATION_NAME"],
            gisenv["MAPSET"],
            "cell_misc",
            inmap,
            "timestamp",
        )

        if os.path.exists(path):
            newpath = os.path.join(
                gisenv["GISDBASE"],
                gisenv["LOCATION_NAME"],
                gisenv["MAPSET"],
                "cell_misc",
                inmap + "_null",
                "timestamp",
            )
            shutil.copyfile(path, newpath)

        # copy cell_misc/<inmap>/description.json
        path = os.path.join(
            gisenv["GISDBASE"],
            gisenv["LOCATION_NAME"],
            gisenv["MAPSET"],
            "cell_misc",
            inmap,
            "description.json",
        )

        if os.path.exists(path):
            newpath = os.path.join(
                gisenv["GISDBASE"],
                gisenv["LOCATION_NAME"],
                gisenv["MAPSET"],
                "cell_misc",
                inmap + "_null",
                "description.json",
            )
            shutil.copyfile(path, newpath)

        # copy hist/<inmap>
        path = os.path.join(
            gisenv["GISDBASE"], gisenv["LOCATION_NAME"], gisenv["MAPSET"], "hist", inmap
        )
        newpath = os.path.join(
            gisenv["GISDBASE"],
            gisenv["LOCATION_NAME"],
            gisenv["MAPSET"],
            "hist",
            inmap + "_null",
        )
        shutil.copyfile(path, newpath)

        # copy colr/<inmap>
        path = os.path.join(
            gisenv["GISDBASE"], gisenv["LOCATION_NAME"], gisenv["MAPSET"], "colr", inmap
        )

        if os.path.exists(path):
            newpath = os.path.join(
                gisenv["GISDBASE"],
                gisenv["LOCATION_NAME"],
                gisenv["MAPSET"],
                "colr",
                inmap + "_null",
            )
            shutil.copyfile(path, newpath)

        # remove <inmap>_rcl first
        gs.run_command(
            "g.remove", type="raster", name=inmap + "_rcl", flags="f", quiet=True
        )
        # remove <inmap>
        gs.run_command("g.remove", type="raster", name=inmap, flags="f", quiet=True)

        # rename <inmap>_null to <inmap>
        gs.run_command(
            "g.rename", raster="%(inmap)s_null,%(inmap)s" % {"inmap": inmap}, quiet=True
        )


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
