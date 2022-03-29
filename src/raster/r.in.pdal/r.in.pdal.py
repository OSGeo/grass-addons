#!/usr/bin/env python

############################################################################
#
# MODULE:	    r.in.pdal
#
# AUTHOR(S): Anika Bettge <bettge at mundialis.de>
#            Thanks to Markus Neteler <neteler at mundialis.de> for help
#
# PURPOSE:   Creates a raster map from LAS LiDAR points using univariate statistics and r.in.xyz.
#
# COPYRIGHT: (C) 2018-2019 by mundialis and the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

# %Module
# %description:  Creates a raster map from LAS LiDAR points using univariate statistics and r.in.xyz.
# %keyword: raster
# %keyword: import
# %keyword: LIDAR
# %keyword: statistics
# %keyword: conversion
# %overwrite: yes
# %End

# %option G_OPT_R_INPUT
# % key: input
# % description: LAS input file
# % required: yes
# %end

# %option G_OPT_R_OUTPUTS
# % key: output
# % description: Name for output raster map
# % required: yes
# %end

# %option
# % key: resolution
# % type: double
# % description: 2D grid resolution (north-south and east-west)
# % answer: 1.0
# % required: no
# %end

# %option
# % key: raster_reference
# % label: Raster map to be used as pixel geometry reference
# % description: Raster map to align to, e.g. an orthophoto of the same region
# % required: no
# %end

# %option
# % key: raster_file
# % label: External raster map to be used as pixel geometry reference
# % description: External raster map to align to, e.g. an orthophoto of the same region
# % required: no
# %end

# %option
# % key: method
# % type: string
# % description: Statistic to use for raster values
# % options: n, min, max, range, sum, mean, stddev, variance, coeff_var, median, percentile, skewness, trimmean
# % answer: mean
# % descriptions: n;Number of points in cell;min;Minimum value of point values in cell;max;Maximum value of point values in cell;range;Range of point values in cell;sum;Sum of point values in cell;mean;Mean (average) value of point values in cell;stddev;Standard deviation of point values in cell;variance;Variance of point values in cell;coeff_var;Coefficient of variance of point values in cell;median;Median value of point values in cell;percentile;Pth (nth) percentile of point values in cell;skewness;Skewness of point values in cell
# % multiple: yes
# % required: no
# %end

# %option
# % key: zrange
# % type: double
# % key_desc: min,max
# % description: Filter range for z data (min,max)
# % required: no
# %end

# %option
# % key: zscale
# % type: double
# % description: Scale to apply to z data
# % answer: 1.0
# % required: no
# %end

# %option
# % key: type
# % type: string
# % description: Type of raster map to be created / Storage type for resultant raster map
# % options: CELL, FCELL, DCELL
# % answer: FCELL
# % required: no
# % descriptions: CELL;Integer;FCELL;Single precision floating point;DCELL;Double precision floating point
# %end

# %option
# % key: percent
# % type: integer
# % description: Percent of map to keep in memory
# % options: 1-100
# % answer: 100
# % required: no
# %end

# %option
# % key: pth
# % type: integer
# % description: Pth percentile of the values
# % options: 1-100
# % required: no
# %end

# %option
# % key: trim
# % type: double
# % description: Discard <trim> percent of the smallest and <trim> percent of the largest observations
# % options: 1-50
# % required: no
# %end

# %option
# % key: footprint
# % type: string
# % description: Footprint of the data as vector map
# % required: no
# %end

# %option
# % key: pdal_cmd
# % type: string
# % description: Command for PDAL (e.g. if PDAL runs only in a docker)
# % required: no
# % answer: pdal
# %end

# %flag
# % key: s
# % description: Scan data file for extent then exit
# %end

# %flag
# % key: g
# % description: In scan mode, print using shell script style
# %end

# %rules
# % exclusive: raster_file, raster_reference
# % exclusive: resolution, raster_file, raster_reference
# %end

import os
import sys

import grass.script as grass
import json
import time

# i18N
import gettext

gettext.install("grassmods", os.path.join(os.getenv("GISBASE"), "locale"))


def footprint_to_vectormap(infile, footprint):
    """The function generates a footprint as vectormap of the input las-file.
    It uses pdal info --boundary.

    Args:
        infile(string): Name of LAS input file
        footprint(string): Footprint of the data as vector map
    """
    if not grass.find_program(
        options["pdal_cmd"].split(" ")[0],
        " ".join(options["pdal_cmd"].split(" ")[1:]) + " info --boundary",
    ):
        grass.fatal(
            _(
                "The pdal executable is not available."
                " Install PDAL or put the pdal executable on path."
            )
        )
    command_fp = options["pdal_cmd"].split(" ")
    command_fp.extend(["info", "--boundary", infile])
    tmp_fp = grass.tempfile()
    if tmp_fp is None:
        grass.fatal("Unable to create temporary files")
    fh = open(tmp_fp, "wb")
    if grass.call(command_fp, stdout=fh) != 0:
        fh.close()
        # check to see if pdal info executed properly
        os.remove(tmp_fp)
        grass.fatal(_("pdal info broken..."))
    else:
        fh.close()
    data = json.load(open(tmp_fp))
    xy_in = ""
    str1 = "boundary"
    try:
        str2 = "boundary_json"
        str3 = "coordinates"
        coord = data[str1][str2][str3][0][0]
        for xy in coord:
            xy_in += str(xy[0]) + "," + str(xy[1]) + "\n"
    except Exception:
        coord_str = str(data[str1][str1])
        coord = coord_str[coord_str.find("((") + 2 : coord_str.find("))")]
        x_y = coord.split(",")
        for xy in x_y:
            xy_in += xy.rstrip().replace(" ", ",") + "\n"
    tmp_xy = grass.tempfile()
    if tmp_xy is None:
        grass.fatal("Unable to create temporary files")
    f = open(tmp_xy, "w")
    f.write(xy_in[:-1])
    f.close()
    grass.run_command(
        "v.in.lines", input=tmp_xy, output="footprint_line", separator="comma"
    )
    grass.run_command("g.region", vector="footprint_line")
    grass.run_command(
        "v.type",
        input="footprint_line",
        out="footprint_boundary",
        from_type="line",
        to_type="boundary",
    )
    grass.run_command("v.centroids", input="footprint_boundary", out=footprint)
    grass.run_command("v.db.addtable", map=footprint, columns="name varchar(50)")
    grass.run_command("v.db.update", map=footprint, column="name", value=infile)

    # Cleaning up
    grass.message(_("Cleaning up..."))
    os.remove(tmp_fp)
    os.remove(tmp_xy)
    grass.run_command(
        "g.remove", flags="f", type="vector", name="footprint_line", quiet=True
    )
    grass.run_command(
        "g.remove", flags="f", type="vector", name="footprint_boundary", quiet=True
    )

    # metadata
    grass.run_command("v.support", map=footprint, comment="in " + os.environ["CMDLINE"])

    grass.message(_("Generating output vector map <%s>...") % footprint)


def scan_extent(infile):
    if not grass.find_program(
        options["pdal_cmd"].split(" ")[0],
        " ".join(options["pdal_cmd"].split(" ")[1:]) + " info --summary",
    ):
        grass.fatal(
            _(
                "The pdal program is not in the path "
                + "and executable. Please install first"
            )
        )
    command_scan = options["pdal_cmd"].split(" ")
    command_scan.extend(["info", "--summary", infile])

    tmp_scan = grass.tempfile()
    if tmp_scan is None:
        grass.fatal("Unable to create temporary files")
    fh = open(tmp_scan, "wb")
    summary = True
    if grass.call(command_scan, stdout=fh) != 0:
        fh.close()
        command_scan = options["pdal_cmd"].split(" ")
        command_scan.extend(["info", infile])
        fh2 = open(tmp_scan, "wb")
        if grass.call(command_scan, stdout=fh2) != 0:
            os.remove(tmp_scan)
            grass.fatal(
                _("pdal cannot determine metadata " + "for unsupported format of <%s>")
                % infile
            )
            fh2.close()
        else:
            fh2.close()
        summary = False
    else:
        fh.close()

    data = json.load(open(tmp_scan))
    if summary:
        str1 = "summary"
        str2 = "bounds"
        y_str = "Y"
        x_str = "X"
        z_str = "Z"
        min_str = "min"
        max_str = "max"
        try:
            n = str(data[str1][str2][y_str][max_str])
            s = str(data[str1][str2][y_str][min_str])
            w = str(data[str1][str2][x_str][min_str])
            e = str(data[str1][str2][x_str][max_str])
            t = str(data[str1][str2][z_str][max_str])
            b = str(data[str1][str2][z_str][min_str])
        except:
            ymin_str = "miny"
            xmin_str = "minx"
            zmin_str = "minz"
            ymax_str = "maxy"
            xmax_str = "maxx"
            zmax_str = "maxz"
            n = str(data[str1][str2][ymax_str])
            s = str(data[str1][str2][ymin_str])
            w = str(data[str1][str2][xmin_str])
            e = str(data[str1][str2][xmax_str])
            t = str(data[str1][str2][zmax_str])
            b = str(data[str1][str2][zmin_str])
    else:
        str1 = "stats"
        str2 = "bbox"
        str3 = "native"
        str4 = "bbox"
        n = str(data[str1][str2][str3][str4]["maxy"])
        s = str(data[str1][str2][str3][str4]["miny"])
        w = str(data[str1][str2][str3][str4]["minx"])
        e = str(data[str1][str2][str3][str4]["maxx"])
        t = str(data[str1][str2][str3][str4]["maxz"])
        b = str(data[str1][str2][str3][str4]["minz"])

    return n, s, w, e, t, b


def main():
    # parameters
    infile = options["input"]
    raster_reference = options["raster_reference"]
    raster_file = options["raster_file"]
    outfiles = options["output"]
    resolution = options["resolution"]
    methods = options["method"]
    zrange = options["zrange"]
    zscale = options["zscale"]
    output_type = options["type"]
    percent = options["percent"]
    pth = options["pth"]
    trim = options["trim"]
    footprint = options["footprint"]
    # flags
    scan = flags["s"]
    shell_script_style = flags["g"]

    if len(outfiles.split(",")) != len(methods.split(",")):
        grass.fatal(
            _(
                "Number of outputs <%s> does not match number of methods <%s>"
                % (outfiles, methods)
            )
        )

    # overwrite auf true setzen
    os.environ["GRASS_OVERWRITE"] = "1"

    # to hide non-error messages from subprocesses
    if grass.verbosity() <= 2:
        outdev = open(os.devnull, "w")
    else:
        outdev = sys.stdout

    # use temporary region
    grass.use_temp_region()

    n, s, w, e, t, b = scan_extent(infile)

    # scan -s or shell_script_style -g:
    if scan:
        if not shell_script_style:
            grass.message(
                _("north: %s\nsouth: %s\nwest: %s\neast: %s\ntop: %s\nbottom: %s")
                % (n, s, w, e, t, b)
            )
        else:
            # shell script style: print to stdout
            print("n=%s s=%s w=%s e=%s t=%s b=%s" % (n, s, w, e, t, b))
    elif footprint:
        footprint_to_vectormap(infile, footprint)
    else:
        # get region with pdal
        # footprint_to_vectormap(infile, 'tiles')

        if raster_file:
            raster_reference = "img" + str(os.getpid())
            grass.run_command(
                "r.external", input=raster_file, flags="o", output=raster_reference
            )
            result = grass.find_file(name=raster_reference, element="raster")
            if result["fullname"] == "":
                raster_reference = raster_reference + ".1"
        # option 1: set region to extent of tiles while precisely aligning pixel
        # geometry to raster_reference (including both raster_reference and raster_file)
        if raster_reference:
            grass.run_command(
                "g.region", n=n, s=s, e=e, w=w, flags="g", align=raster_reference
            )
        else:
            # option 2: change raster resolution to final resolution while best
            # effort aligning to pixel geometry
            grass.run_command(
                "g.region", n=n, s=s, e=e, w=w, flags="ap", res=resolution
            )
        # generate PDAL pipeline
        # . pdal pipline laz2json (STDOUT) | r.in.xyz
        bn = os.path.basename(infile)
        infile_format = bn.split(".")[-1]
        # format_reader from https://pdal.io/stages/readers.html
        format_reader = ""
        if infile_format.lower() == "laz" or infile_format.lower() == "las":
            format_reader = "readers.las"
        # pts: not tested
        elif infile_format.lower() == "pts":
            format_reader = "readers.pts"
        else:
            grass.run_command(
                "g.remove", flags="f", type="vector", name="tiles", quiet=True
            )
            grass.fatal(_("Format .%s is not supported.." % infile_format))

        grass.message(_("Converting input file <%s>...") % infile)
        tmp_file_json = "tmp_file_json_" + str(os.getpid())

        data = {}
        data["pipeline"] = []
        data["pipeline"].append({"type": format_reader, "filename": infile})
        data["pipeline"].append(
            {
                "type": "writers.text",
                "format": "csv",
                "order": "X,Y,Z",
                "keep_unspecified": "false",
                "filename": "STDOUT",
                "quote_header": "false",
            }
        )
        with open(tmp_file_json, "w") as f:
            json.dump(data, f)

        tmp_xyz = grass.tempfile()
        if tmp_xyz is None:
            grass.fatal("Unable to create temporary files")
        command_pdal1 = options["pdal_cmd"].split(" ")
        if options["pdal_cmd"] != "pdal":
            v_index = None
            cmd_entries = options["pdal_cmd"].split(" ")
            for cmd_entry, num in zip(cmd_entries, range(len(cmd_entries))):
                if cmd_entry == "-v":
                    v_index = num
                    break
            mnt_vol = cmd_entries[v_index + 1].split(":")[1]
            tmp_file_json2 = os.path.join(mnt_vol, tmp_file_json)
        else:
            tmp_file_json2 = tmp_file_json
        command_pdal1.extend(["pipeline", "--input", tmp_file_json2])

        fh = open(tmp_xyz, "wb")
        if grass.call(command_pdal1, stdout=fh) != 0:
            fh.close()
            # check to see if pdal pipeline executed properly
            print(command_pdal1)
            grass.fatal(_("pdal pipeline is broken..."))
        else:
            fh.close()

        for i in range(len(methods.split(","))):
            method = methods.split(",")[i]
            outfile = outfiles.split(",")[i]

            grass.message(_("Generating output raster map <%s>...") % outfile)

            command_pdal2 = [
                "r.in.xyz",
                "input=" + tmp_xyz,
                "output=" + outfile,
                "skip=1",
                "separator=comma",
                "method=" + method,
            ]

            if zrange:
                command_pdal2.append("zrange=" + zrange)
            if zscale:
                command_pdal2.append("zscale=" + zscale)
            if output_type:
                command_pdal2.append("type=" + output_type)
            if percent:
                command_pdal2.append("percent=" + percent)
            if pth:
                command_pdal2.append("pth=" + pth)
            if trim:
                command_pdal2.append("trim=" + trim)

            if grass.call(command_pdal2, stdout=outdev) != 0:
                # check to see if r.in.xyz executed properly
                os.remove(tmp_xyz)
                grass.fatal(_("r.in.xyz is broken..."))

            # metadata
            empty_history = grass.tempfile()
            if empty_history is None:
                grass.fatal("Unable to create temporary files")
            f = open(empty_history, "w")
            f.close()
            grass.run_command(
                "r.support",
                map=outfile,
                source1=infile,
                description="generated by r.in.pdal",
                loadhistory=empty_history,
            )
            grass.run_command("r.support", map=outfile, history=os.environ["CMDLINE"])
            os.remove(empty_history)

        # Cleanup
        grass.message(_("Cleaning up..."))
        grass.run_command(
            "g.remove", flags="f", type="vector", name="tiles", quiet=True
        )
        if raster_file:
            grass.run_command(
                "g.remove",
                flags="f",
                type="raster",
                pattern=raster_reference[:-1] + "*",
                quiet=True,
            )
        os.remove(tmp_file_json)
        os.remove(tmp_xyz)
        grass.del_temp_region()


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
