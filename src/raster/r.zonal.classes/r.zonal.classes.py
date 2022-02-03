#!/usr/bin/env python
############################################################################
#
# MODULE:       r.zonal.classes
# AUTHOR:       Tais Grippa
# PURPOSE:      Calculates statistics describing raster areas's (zones) composition in terms of classes (e.g.,land cover map)
#
# COPYRIGHT:    (c) 2019 Tais Grippa, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Calculates zonal classes proportion describing raster areas's composition, e.g., in terms of land-cover classes.
# % keyword: raster
# % keyword: statistics
# % keyword: zonal statistics
# %end
# %option G_OPT_R_INPUT
# % key: zone_map
# % label: Name for input raster map with areas
# % description: Raster map with areas (all pixels of an area have same id), such as the output of r.clump
# % required: yes
# %end
# %option G_OPT_R_INPUT
# % key: raster
# % description: Name of input categorical raster maps for statistics
# % required: yes
# %end
# %option
# % key: statistics
# % type: string
# % label: Statistics to calculate for each input raster map
# % required: yes
# % multiple: yes
# % options: proportion,mode
# % answer: proportion,mode
# % guisection: Statistics
# %end
# %option
# % key: prefix
# % type: string
# % label: Prefix for statistics name
# % required: no
# % guisection: Statistics
# %end
# %option
# % key: decimals
# % type: integer
# % label: Number of decimals for proportion numbers
# % answer: 5
# % required: no
# % guisection: Statistics
# %end
# %option
# % key: classes_list
# % type: string
# % label: List of classes to be considered in the calculation, e.g. '21,34,35,56'
# % required: no
# % guisection: Statistics
# %end
# %option G_OPT_F_OUTPUT
# % key: csvfile
# % description: Name for output CSV file containing statistics
# % required: no
# % guisection: Output
# %end
# %option G_OPT_F_SEP
# % guisection: Output
# %end
# %option G_OPT_V_OUTPUT
# % key: vectormap
# % description: Name for optional vector output map with statistics as attributes
# % required: no
# % guisection: Output
# %end
# %flag
# % key: r
# % description: Adjust region to input map
# %end
# %flag
# % key: c
# % description: Force check of input's layer type
# %end
# %flag
# % key: n
# % description: Consider null values in the calculations
# % guisection: Statistics
# %end
# %flag
# % key: p
# % description: Proportions as percentages instead of zone's area ratio
# % guisection: Statistics
# %end
# %flag
# % key: l
# % description: Compute statistics only for the classes provided in 'classes_list' parameter
# % guisection: Statistics
# %end
# %rules
# % required: csvfile,vectormap
# % required: raster,statistics
# % requires: -l, classes_list
# %END

import os
import csv
import operator
import atexit
import grass.script as gscript


def cleanup():
    if temporary_vect:
        if gscript.find_file(temporary_vect, element="vector")["name"]:
            gscript.run_command(
                "g.remove", flags="f", type_="vector", name=temporary_vect, quiet=True
            )
        if gscript.db_table_exist(temporary_vect):
            gscript.run_command(
                "db.execute", sql="DROP TABLE %s" % temporary_vect, quiet=True
            )


def main():
    global insert_sql
    insert_sql = None
    global temporary_vect
    temporary_vect = None
    global stats_temp_file
    stats_temp_file = None
    global content
    content = None
    global raster
    raster = options["raster"]
    global decimals
    decimals = int(options["decimals"])
    global zone_map
    zone_map = options["zone_map"]

    csvfile = options["csvfile"] if options["csvfile"] else []
    separator = gscript.separator(options["separator"])
    prefix = options["prefix"] if options["prefix"] else []
    classes_list = options["classes_list"].split(",") if options["classes_list"] else []
    vectormap = options["vectormap"] if options["vectormap"] else []
    prop = False if "proportion" not in options["statistics"].split(",") else True
    mode = False if "mode" not in options["statistics"].split(",") else True

    if flags[
        "c"
    ]:  # Check only if flag activated - Can be bottleneck in case of very large raster.
        # Check if input layer is CELL
        if gscript.parse_command("r.info", flags="g", map=raster)["datatype"] != "CELL":
            gscript.fatal(
                _(
                    "The type of the input map 'raster' is not CELL. Please use raster with integer values"
                )
            )
        if (
            gscript.parse_command("r.info", flags="g", map=zone_map)["datatype"]
            != "CELL"
        ):
            gscript.fatal(
                _(
                    "The type of the input map 'zone_map' is not CELL. Please use raster with integer values"
                )
            )

    # Check if 'decimals' is + and with credible value
    if decimals <= 0:
        gscript.fatal(_("The number of decimals should be positive"))
    if decimals > 100:
        gscript.fatal(_("The number of decimals should not be more than 100"))

    # Adjust region to input map is flag active
    if flags["r"]:
        gscript.use_temp_region()
        gscript.run_command("g.region", raster=zone_map)

    # R.STATS
    tmpfile = gscript.tempfile()
    try:
        if flags["n"]:
            gscript.run_command(
                "r.stats",
                overwrite=True,
                flags="c",
                input="%s,%s" % (zone_map, raster),
                output=tmpfile,
                separator=separator,
            )  # Consider null values in R.STATS
        else:
            gscript.run_command(
                "r.stats",
                overwrite=True,
                flags="cn",
                input="%s,%s" % (zone_map, raster),
                output=tmpfile,
                separator=separator,
            )  # Do not consider null values in R.STATS
        gscript.message(_("r.stats command finished..."))
    except:
        gscript.fatal(_("The execution of r.stats failed"))

    # COMPUTE STATISTICS
    # Open csv file and create a csv reader
    rstatsfile = open(tmpfile, "r")
    reader = csv.reader(rstatsfile, delimiter=separator)
    # Total pixels per category per zone
    totals_dict = {}
    for row in reader:
        if (
            row[0] not in totals_dict
        ):  # Will pass the condition only if the current zone ID does not exists yet in the dictionary
            totals_dict[
                row[0]
            ] = {}  # Declare a new embedded dictionnary for the current zone ID
        if (
            flags["l"] and row[1] in classes_list
        ):  # Will pass only if flag -l is active and if the current class is in the 'classes_list'
            totals_dict[row[0]][row[1]] = int(row[2])
        else:
            totals_dict[row[0]][row[1]] = int(row[2])
    # Delete key '*' in 'totals_dict' that could append if there are null values on the zone raster
    if "*" in totals_dict:
        del totals_dict["*"]
    # Close file
    rstatsfile.close()
    # Get list of ID
    id_list = [ID for ID in totals_dict]
    # Mode
    if mode:
        modalclass_dict = {}
        for ID in id_list:
            # The trick was found here : https://stackoverflow.com/a/268285/8013239
            mode = max(iter(totals_dict[ID].items()), key=operator.itemgetter(1))[0]
            if mode == "*":  # If the mode is NULL values
                modalclass_dict[ID] = "NULL"
            else:
                modalclass_dict[ID] = mode
    # Class proportions
    if prop:
        # Get list of categories to output
        if classes_list:  # If list of classes provided by user
            class_dict = {
                str(int(a)): "" for a in classes_list
            }  # To be sure it's string format
        else:
            class_dict = {}
        # Proportion of each category per zone
        proportion_dict = {}
        for ID in id_list:
            proportion_dict[ID] = {}
            for cl in totals_dict[ID]:
                if (
                    flags["l"] and cl not in classes_list
                ):  # with flag -l, output will contain only classes from 'classes_list'
                    continue
                if flags["p"]:
                    prop_value = (
                        float(totals_dict[ID][cl]) / sum(totals_dict[ID].values()) * 100
                    )
                else:
                    prop_value = float(totals_dict[ID][cl]) / sum(
                        totals_dict[ID].values()
                    )
                proportion_dict[ID][cl] = "{:.{}f}".format(prop_value, decimals)
                if cl == "*":
                    class_dict["NULL"] = ""
                else:
                    class_dict[cl] = ""
        # Fill class not met in the raster with zero
        for ID in proportion_dict:
            for cl in class_dict:
                if cl not in proportion_dict[ID].keys():
                    proportion_dict[ID][cl] = "{:.{}f}".format(0, decimals)
        # Get list of class sorted by value (arithmetic ordering)
        if "NULL" in class_dict.keys():
            class_list = sorted([int(k) for k in class_dict.keys() if k != "NULL"])
            class_list.append("NULL")
        else:
            class_list = sorted([int(k) for k in class_dict.keys()])
    gscript.verbose(_("Statistics computed..."))
    # Set 'totals_dict' to None to try RAM release
    totals_dict = None
    # OUTPUT CONTENT
    # Header
    header = [
        "cat",
    ]
    if mode:
        if prefix:
            header.append("%s_mode" % prefix)
        else:
            header.append("mode")
    if prop:
        if prefix:
            [header.append("%s_prop_%s" % (prefix, cl)) for cl in class_list]
        else:
            [header.append("prop_%s" % cl) for cl in class_list]
    # Values
    value_dict = {}
    for ID in id_list:
        value_dict[ID] = []
        value_dict[ID].append(ID)
        if mode:
            value_dict[ID].append(modalclass_dict[ID])
        if prop:
            for cl in class_list:
                value_dict[ID].append(proportion_dict[ID]["%s" % cl])
    # WRITE OUTPUT
    if csvfile:
        with open(csvfile, "w", newline="") as outfile:
            writer = csv.writer(outfile, delimiter=separator)
            writer.writerow(header)
            writer.writerows(value_dict.values())
    if vectormap:
        gscript.message(_("Creating output vector map..."))
        temporary_vect = "rzonalclasses_tmp_vect_%d" % os.getpid()
        gscript.run_command(
            "r.to.vect",
            input_=zone_map,
            output=temporary_vect,
            type_="area",
            flags="vt",
            overwrite=True,
            quiet=True,
        )
        insert_sql = gscript.tempfile()
        with open(insert_sql, "w", newline="") as fsql:
            fsql.write("BEGIN TRANSACTION;\n")
            if gscript.db_table_exist(temporary_vect):
                if gscript.overwrite():
                    fsql.write("DROP TABLE %s;" % temporary_vect)
                else:
                    gscript.fatal(
                        _("Table %s already exists. Use --o to overwrite")
                        % temporary_vect
                    )
            create_statement = (
                "CREATE TABLE %s (cat int PRIMARY KEY);\n" % temporary_vect
            )
            fsql.write(create_statement)
            for col in header[1:]:
                if col.split("_")[-1] == "mode":  # Mode column should be integer
                    addcol_statement = "ALTER TABLE %s ADD COLUMN %s integer;\n" % (
                        temporary_vect,
                        col,
                    )
                else:  # Proportions column should be double precision
                    addcol_statement = (
                        "ALTER TABLE %s ADD COLUMN %s double precision;\n"
                        % (temporary_vect, col)
                    )
                fsql.write(addcol_statement)
            for key in value_dict:
                insert_statement = "INSERT INTO %s VALUES (%s);\n" % (
                    temporary_vect,
                    ",".join(value_dict[key]),
                )
                fsql.write(insert_statement)
            fsql.write("END TRANSACTION;")
        gscript.run_command("db.execute", input=insert_sql, quiet=True)
        gscript.run_command(
            "v.db.connect", map_=temporary_vect, table=temporary_vect, quiet=True
        )
        gscript.run_command(
            "g.copy", vector="%s,%s" % (temporary_vect, vectormap), quiet=True
        )


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
