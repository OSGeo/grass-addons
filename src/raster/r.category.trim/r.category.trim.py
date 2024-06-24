#!/usr/bin/env python
#
########################################################################
#
# MODULE:       r.category.trim
# AUTHOR(S):    Paulo van Breugel (paulo AT ecodiv DOT earth)
# DESCRIPTION:  Export the categories, category labels and colour codes (RGB)
#               as csv file or as a QGIS colour map file. It will first remove
#               non-existing categories and their colour definitions.
#               Optionally, map values can be reclassed into consecutive
#               categories values, whereby the category labels and colors are
#               retained.
#
# COPYRIGHT: (C) 2015-2022 Paulo van Breugel and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
# %Module
# % description: Export categories and corresponding colors as QGIS color file or csv file. Non-existing categories and their color definitions will be removed.
# % keyword: raster
# % keyword: color
# % keyword: color table
# % keyword: category
# %End

# %option
# % key: input
# % type: string
# % gisprompt: old,cell,raster
# % description: input map
# % key_desc: name
# % required: yes
# % multiple: no
# % guisection: Raster
# %end

# %option
# % key: output
# % type: string
# % gisprompt: new,cell,raster
# % description: output map
# % key_desc: name
# % required: no
# % multiple: no
# % guisection: Raster
# %end

# %option G_OPT_F_OUTPUT
# % key:csv
# % description: Attribute table (csv format)
# % key_desc: name
# % required: no
# % guisection: Export
# %end

# %option G_OPT_F_OUTPUT
# % key:qgis
# % description: QGIS color file (txt format)
# % key_desc: name
# % required: no
# % guisection: Export
# %end

# %flag:
# % key: n
# % description: Recode layer to get consecutive category values
# %end

# %rules
# % requires_all: -n, output
# %end

# import libraries
import os
import sys
import re
from subprocess import PIPE
from grass.pygrass.modules import Module
import grass.script as gs


def main(options, flags):

    # Check if running in GRASS
    gisbase = os.getenv("GISBASE")
    if not gisbase:
        gs.fatal(
            _(
                "$GISBASE not defined. You must be in GRASS GIS to run \
        this program"
            )
        )
        return 0

    # Input
    input_raster = options["input"]
    output_raster = options["output"]
    output_csv = options["csv"]
    output_colorfile = options["qgis"]
    flag_recode = flags["n"]

    # Check if raster is integer
    iscell = gs.raster.raster_info(input_raster)["datatype"]
    if iscell != "CELL":
        gs.error(_("Input should be an integer raster layer"))

    # Get map category values and their labels
    rcategory_output = Module(
        "r.category", map=input_raster, stdout_=PIPE
    ).outputs.stdout
    raster_cats = rcategory_output.split("\n")
    raster_cats = [_f for _f in raster_cats if _f]
    raster_id = [z.split("\t")[0] for z in raster_cats]
    raster_id_list = list(map(int, raster_id))

    # Get full color table
    raster_color = gs.read_command("r.colors.out", map=input_raster).split("\n")
    raster_color = [x for x in raster_color if "nv" not in x and "default" not in x]
    raster_color = [_f for _f in raster_color if _f]
    raster_color_cat = [z.split(" ")[0] for z in raster_color]
    idx = [i for i, item in enumerate(raster_color_cat) if not re.search(r"\.", item)]
    raster_color_cat = [raster_color_cat[i] for i in idx]
    raster_color = [raster_color[i] for i in idx]
    raster_color_cat = list(map(int, raster_color_cat))

    # Set strings / list to be used in loop
    color_rules = ""
    recode_rules = ""
    category_string = ""
    cv_string = []

    # recode to consecutive category values
    if flag_recode:
        raster_id_new = list(range(1, len(raster_id) + 1))
        raster_lab = [z.split("\t")[1] for z in raster_cats]
        for j in range(len(raster_id)):
            recode_rules = "{0}{1}:{1}:{2}\n".format(
                recode_rules, raster_id[j], raster_id_new[j]
            )
            select_color = list(
                map(
                    int,
                    [
                        i
                        for i, x in enumerate(raster_color_cat)
                        if x == raster_id_list[j]
                    ],
                )
            )
            if select_color:
                add_color = raster_color[select_color[0]].split(" ")[1]
                color_rules = "{}{} {}\n".format(
                    color_rules, raster_id_new[j], add_color
                )
                category_string = "{}{}|{}\n".format(
                    category_string, raster_id_new[j], raster_lab[j]
                )
                cv_string.append(add_color)

        color_rules = "{}nv 255:255:255\ndefault 255:255:255\n".format(color_rules)
        Module(
            "r.recode",
            flags="a",
            input=input_raster,
            output=output_raster,
            rules="-",
            stdin_=recode_rules,
            quiet=True,
        )
        Module("r.colors", map=output_raster, rules="-", stdin_=color_rules, quiet=True)
        Module(
            "r.category",
            map=output_raster,
            rules="-",
            stdin_=category_string,
            quiet=True,
            separator="pipe",
        )
    else:
        # Check if new layer should be created
        if len(output_raster) > 0:
            k = "{},{}".format(input_raster, output_raster)
            gs.run_command("g.copy", raster=k)
        else:
            output_raster = input_raster

        # Remove redundant categories
        Module(
            "r.category",
            map=output_raster,
            rules="-",
            stdin_=rcategory_output,
            quiet=True,
        )

        # Write color rules and assign colors
        for j in range(len(raster_id_list)):
            select_color = list(
                map(
                    int,
                    [
                        i
                        for i, x in enumerate(raster_color_cat)
                        if x == raster_id_list[j]
                    ],
                )
            )
            if select_color:
                add_color = raster_color[select_color[0]].split(" ")[1]
                color_rules = (
                    color_rules + str(raster_id_list[j]) + " " + add_color + "\n"
                )
                cv_string.append(add_color)
        color_rules = "{}nv 255:255:255\ndefault 255:255:255\n".format(color_rules)
        Module("r.colors", map=output_raster, rules="-", stdin_=color_rules, quiet=True)

    # If attribute table (csv format) should be written
    if len(output_csv) > 0:
        if flag_recode:
            raster_cat1 = [
                w.replace("|", ",'")
                for w in [_f for _f in category_string.split("\n") if _f]
            ]
        else:
            raster_cat1 = [w.replace("\t", ",'") for w in raster_cats]
        raster_cat1 = ["{}'".format(w) for w in raster_cat1]
        raster_cat1.insert(0, "CATEGORY,CATEGORY LABEL")
        cv_string1 = list(cv_string)
        cv_string1.insert(0, "RGB")
        with open(output_csv, "w") as text_file:
            for k in range(len(raster_cat1)):
                text_file.write("{},{}\n".format(raster_cat1[k], cv_string1[k]))

    # If QGIS Color Map text files should be written
    if len(output_colorfile) > 0:
        rgb_string = [w.replace(":", ",") for w in cv_string]
        if flag_recode:
            raster_cats = [_f for _f in category_string.split("\n") if _f]
        else:
            raster_cats = [w.replace("\t", "|") for w in raster_cats]
        with open(output_colorfile, "w") as text_file:
            text_file.write("# QGIS color map for {}\n".format(output_raster))
            text_file.write("INTERPOLATION:EXACT\n")
            for k in range(len(raster_cats)):
                raster_cats2 = raster_cats[k].split("|")
                if raster_cats2[1]:
                    text_file.write(
                        "{},{},255,{}\n".format(
                            raster_cats2[0], rgb_string[k], raster_cats2[1]
                        )
                    )
                else:
                    text_file.write(
                        "{},{},255,{}\n".format(raster_cats2[0], rgb_string[k], "-")
                    )


if __name__ == "__main__":
    sys.exit(main(*gs.parser()))
