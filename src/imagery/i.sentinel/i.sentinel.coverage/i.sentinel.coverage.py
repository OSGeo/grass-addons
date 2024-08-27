#!/usr/bin/env python3

############################################################################
#
# MODULE:       i.sentinel.coverage
#
# AUTHOR(S):    Anika Weinmann <weinmann at mundialis.de>
#
# PURPOSE:      Checks the area coverage of the by filters selected
#               Sentinel-1 or Sentinel-2 scenes
#
# COPYRIGHT:	(C) 2020 by mundialis and the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

# %Module
# % description: Checks the area coverage of Sentinel-1 or Sentinel-2 scenes selected by filters.
# % keyword: imagery
# % keyword: satellite
# % keyword: Sentinel
# % keyword: geometry
# % keyword: spatial query
# % keyword: area
# %end

# %option G_OPT_F_INPUT
# % key: settings
# % label: Full path to settings file (user, password)
# %end

# %option G_OPT_V_INPUT
# % key: area
# % description: Area input vector maps
# %end

# %option
# % key: start
# % type: string
# % description: Start date ('YYYY-MM-DD')
# % guisection: Filter
# %end

# %option
# % key: end
# % type: string
# % description: End date ('YYYY-MM-DD')
# % guisection: Filter
# %end

# %option
# % key: producttype
# % type: string
# % description: Sentinel product type to filter
# % required: no
# % options: SLC,GRD,OCN,S2MSI1C,S2MSI2A,S2MSI2Ap
# % answer: S2MSI2A
# % guisection: Filter
# %end

# %option
# % key: clouds
# % type: integer
# % required: no
# % multiple: no
# % description: Maximum cloud cover percentage for Sentinel scene
# % guisection: Filter
# %end

# %option
# % key: minpercent
# % type: integer
# % required: no
# % multiple: no
# % description: Minimal percentage of coverage for Sentinel scene; error otherwise
# % guisection: Filter
# %end

# %option
# % key: names
# % type: string
# % description: Sentinel-1 or Sentinel-2 names
# % guisection: Filter
# % required: no
# % multiple: yes
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % label: Output file with a list of Sentinel-1 or Sentinel-2 scene names
# % required: no
# %end

# %rules
# % collective: start,end
# % excludes: names,start,end,clouds,producttype
# %end


import atexit
import os
import subprocess
from datetime import datetime, timedelta

import grass.script as grass


# initialize global vars
rm_regions = []
rm_vectors = []
rm_rasters = []


def cleanup():
    nuldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nuldev}
    for rmr in rm_regions:
        if rmr in [x for x in grass.parse_command("g.list", type="region")]:
            grass.run_command("g.remove", type="region", name=rmr, **kwargs)
    for rmv in rm_vectors:
        if grass.find_file(name=rmv, element="vector")["file"]:
            grass.run_command("g.remove", type="vector", name=rmv, **kwargs)
    for rmrast in rm_rasters:
        if grass.find_file(name=rmrast, element="raster")["file"]:
            grass.run_command("g.remove", type="raster", name=rmrast, **kwargs)


def scenename_split(scenename):
    """
    When using the query option in i.sentinel.coverage and defining
    specific filenames, the parameters Producttype, Start-Date, and End-Date
    have to be definied as well. This function extracts these parameters from a
    Sentinel-2 filename and returns the proper string to be passed to the query
    option.
    Args:
        scenename(string): Name of the scene in the format
                           S2A_MSIL1C_20180822T155901_N0206_R097_T17SPV_20180822T212023
    Returns:
        producttype(string): Sentinel-2 producttype in the required parameter
                             format for i.sentinel.download, e.g. S2MSI2A
        start_day(string): Date in the format YYYY-MM-DD, it is the acquisition
                           date -1 day
        end_day(string): Date in the format YYYY-MM-DD, it is the acquisition
                           date +1 day

    """
    try:
        # get producttype
        name_split = scenename.split("_")

        if name_split[0].startswith("S2"):
            type_string = name_split[1]
            level_string = type_string.split("L")[1]
            producttype = "S2MSI" + level_string
            date_string = name_split[2].split("T")[0]
        elif name_split[0].startswith("S1"):
            producttype = name_split[2][:3]
            if producttype == "SLC":
                date_string = name_split[5].split("T")[0]
            else:
                date_string = name_split[4].split("T")[0]

        else:
            grass.fatal(_("Sensor {} is not supported yet").format(name_split[0]))
        dt_obj = datetime.strptime(date_string, "%Y%m%d")
        start_day_dt = dt_obj - timedelta(days=1)
        end_day_dt = dt_obj + timedelta(days=1)
        start_day = start_day_dt.strftime("%Y-%m-%d")
        end_day = end_day_dt.strftime("%Y-%m-%d")
    except Exception as e:
        grass.fatal(
            _(
                "The name of the scene must have a format of e.g."
                + " S2A_MSIL1C_YYYYMMDDT155901_N0206_R097_T17SPV_20180822T212023"
            )
        )
    return producttype, start_day, end_day


def get_size(vector):
    tmpvector = "tmp_getsize_%s" % str(os.getpid())
    rm_vectors.append(tmpvector)
    grass.run_command(
        "g.copy", vector="%s,%s" % (vector, tmpvector), overwrite=True, quiet=True
    )
    if len(grass.vector_db(tmpvector)) == 0:
        grass.run_command("v.db.addtable", map=tmpvector, quiet=True)
    grass.run_command(
        "v.db.addcolumn", map=tmpvector, columns="tmparea DOUBLE PRECISION", quiet=True
    )
    grass.run_command(
        "v.to.db",
        map=tmpvector,
        columns="tmparea",
        option="area",
        units="meters",
        quiet=True,
        overwrite=True,
    )
    sizeselected = grass.parse_command("v.db.select", map=tmpvector, format="vertical")
    sizesstr = [x.split("|")[1:] for x in sizeselected if x.startswith("tmparea|")][0]
    sizes = [float(x) for x in sizesstr]
    return sum(sizes)


def main():

    global rm_regions, rm_rasters, rm_vectors

    # parameters
    settings = options["settings"]
    output = options["output"]
    area = options["area"]
    if not grass.find_file(area, element="vector")["file"]:
        grass.fatal(_("Vector map <{}> not found").format(area))
    producttype = options["producttype"]

    grass.message(_("Retrieving Sentinel footprints from ESA hub ..."))
    fps = "tmp_fps_%s" % str(os.getpid())
    rm_vectors.append(fps)

    if not options["names"]:
        i_sentinel_download_params = {
            "settings": settings,
            "map": area,
            "clouds": options["clouds"],
            "producttype": producttype,
            "start": options["start"],
            "end": options["end"],
            "flags": "lb",
            "quiet": True,
        }
        i_sentinel_download_cmd = "i.sentinel.download {}".format(
            " ".join(
                [
                    "{!s}={!r}".format(k, v)
                    for (k, v) in i_sentinel_download_params.items()
                    if k not in ["flags", "quiet"]
                ]
            )
        )
        if "quiet" in i_sentinel_download_params:
            i_sentinel_download_cmd += " --q"
        if "flags" in i_sentinel_download_params:
            i_sentinel_download_cmd += " -{}".format(
                i_sentinel_download_params["flags"]
            )
        cmd = grass.Popen(
            i_sentinel_download_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        resp = cmd.communicate()
        if resp[0] != b"":
            s_list = resp[0].decode("utf-8").strip().splitlines()
        else:
            # Experimental version warning needs to be removed from i.eodag
            if set(resp) == {b""}:
                grass.fatal(_("No products found"))
            else:
                error_msg = ""
                for i in range(0, len(resp)):
                    error_msg += resp[i].decode("utf-8")
                grass.fatal(_("Error using i.sentinel.download: {}").format(error_msg))
        name_list_tmp = [x.split(" ")[0] for x in s_list]
    else:
        name_list_tmp = options["names"].split(",")
    name_list = []
    fp_list = []
    for name in name_list_tmp:
        real_producttype, start_day, end_day = scenename_split(name)
        if real_producttype != producttype:
            grass.fatal(_("Producttype of {} not supported").format(real_producttype))
        fpi = "tmp_fps_%s_%s" % (name, str(os.getpid()))
        try:
            grass.run_command(
                "i.sentinel.download",
                settings=settings,
                footprints=fpi,
                producttype=producttype,
                id=name,
                flags="l",
                quiet=True,
            )
            name_list.append(name)
            fp_list.append(fpi)
            rm_vectors.append(fpi)
        except Exception as e:
            grass.warning(_("{} was not found in {}").format(name, area))

    if len(fp_list) > 1:
        start_fp = fp_list[0]
        for idx, fp in enumerate(fp_list[1:]):
            temp_overlay = "tmp_fp_overlay_%d" % idx
            rm_vectors.append(temp_overlay)
            grass.run_command(
                "v.overlay",
                ainput=start_fp,
                binput=fp,
                operator="or",
                output=temp_overlay,
                quiet=True,
            )
            grass.run_command(
                "v.db.update",
                map=temp_overlay,
                column="a_title",
                query_column='a_title || "+" ' + "|| b_title",
                where="a_title NOT NULL AND " + "b_title NOT NULL",
                quiet=True,
            )
            grass.run_command(
                "v.db.update",
                map=temp_overlay,
                column="a_title",
                query_column="b_title",
                where="a_title IS NULL",
                quiet=True,
            )
            grass.run_command(
                "v.db.renamecolumn",
                map=temp_overlay,
                column="a_title,title",
                quiet=True,
            )
            columns_dict = grass.parse_command("v.info", map=temp_overlay, flags="c")
            drop_columns = [
                col.split("|")[1]
                for col in columns_dict
                if col.split("|")[1]
                not in ["cat", "title"]  # What does cat refer to here?
            ]
            grass.run_command(
                "v.db.dropcolumn", map=temp_overlay, columns=drop_columns, quiet=True
            )

            start_fp = temp_overlay
    else:
        temp_overlay = fp_list[0]
    grass.run_command("g.rename", vector="%s,%s" % (temp_overlay, fps))

    grass.message(_("Getting size of <{}> area ...").format(area))
    areasize = get_size(area)

    grass.message(_("Getting size of footprints in area <{}> ...").format(area))
    fps_in_area = "tmp_fps_in_area_%s" % str(os.getpid())
    rm_vectors.append(fps_in_area)
    grass.run_command(
        "v.overlay",
        ainput=fps,
        atype="area",
        binput=area,
        operator="and",
        output=fps_in_area,
        quiet=True,
    )
    grass.run_command(
        "v.db.addcolumn", map=fps_in_area, columns="tmp INTEGER", quiet=True
    )
    grass.run_command("v.db.update", map=fps_in_area, column="tmp", value=1, quiet=True)
    # list of scenes that actually intersect with bbox
    name_list_updated_tmp = list(
        grass.parse_command(
            "v.db.select", map=fps_in_area, column="a_title", flags="c"
        ).keys()
    )

    # split along '+' and remove duplicates
    name_list_updated = list(
        set([item2 for item in name_list_updated_tmp for item2 in item.split("+")])
    )
    fps_in_area_dis = "tmp_fps_in_area_dis_%s" % str(os.getpid())
    rm_vectors.append(fps_in_area_dis)
    grass.run_command(
        "v.dissolve",
        input=fps_in_area,
        output=fps_in_area_dis,
        column="tmp",
        quiet=True,
    )
    grass.run_command("v.db.addtable", map=fps_in_area_dis, quiet=True)
    fpsize = get_size(fps_in_area_dis)

    percent = fpsize / areasize * 100.0
    percent_rounded = round(percent, 2)
    grass.message(
        _("{} percent of the area <{}> is covered").format(str(percent_rounded), area)
    )
    if options["minpercent"]:
        if percent < int(options["minpercent"]):
            grass.fatal(
                _("The percentage of coverage is too low (expected: {})").format(
                    str(options["minpercent"])
                )
            )
    # save list of Sentinel names
    if output:
        with open(output, "w") as f:
            f.write(",".join(name_list_updated))
        grass.message(
            _("Name of Sentinel scenes are written to file <{}>").format(output)
        )
    else:
        grass.message(_("The following scenes were found:"))
        grass.message(_("\n".join(name_list_updated)))

    # TODO Sentinel-1 select only "one" scene (no overlap)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
