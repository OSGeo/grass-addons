#!/usr/bin/env python

#
########################################################################
#
# MODULE:       r.out.legend
# AUTHOR(S):    Paulo van Breugel
# DESCRIPTION:  Export the legend of a raster as image, which can be used
#               in e.g., the map composer in QGIS.
#
# COPYRIGHT: (C) 2014-2017 by Paulo van Breugel and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
# %Module
# % description: Create an image file showing the legend of a raster map
# % keyword: raster
# % keyword: color
# % keyword: color table
# % keyword: image
# %End

# %option G_OPT_R_MAP
# % key: raster
# %end

# %option G_OPT_F_OUTPUT
# % key:file
# % description: Name of the output file (including file extension)
# % key_desc: name
# %end

# %option
# % key: filetype
# % type: string
# % description: File type
# % key_desc: extension
# % options: png,ps,cairo
# % answer: cairo
# % required: yes
# % multiple: no
# %end

# ------------------------------------------------------------------------------

# %option
# % key: dimensions
# % type: string
# % description: width and height of the color legend
# % key_desc: width,height
# % required: yes
# % guisection: Image settings
# %end

# %option
# % key: unit
# % type: string
# % description: unit of the image dimensions
# % key_desc: unit
# % required: no
# % options: cm,mm,inch,px
# % answer: cm
# % guisection: Image settings
# %end

# %option
# % key: resolution
# % type: integer
# % description: resolution (dots/inch)
# % key_desc: value
# % required: no
# % guisection: Image settings
# %end

# %option G_OPT_CN
# % guisection: Image settings
# % answer: white
# %end

# ------------------------------------------------------------------------------

# %option
# % key: labelnum
# % type: integer
# % description: Number of text labels
# % key_desc: integer
# % required: no
# % answer: 5
# % guisection: Extra options
# %end

# %option
# % key: range
# % type: string
# % description: Use a subset of the map range for the legend
# % key_desc: min,max
# % required: no
# % guisection: Extra options
# %end

# %option
# % key: label_values
# % type: string
# % key_desc: float
# % description: Specific values to draw ticks
# % required: no
# % multiple: yes
# % guisection: Extra options
# %end

# %option
# % key: label_step
# % type: string
# % key_desc: float
# % description: Display label every step
# % required: no
# % multiple: no
# % guisection: Extra options
# %end

# %option
# % key: digits
# % type: integer
# % description: Maximum number of digits for raster value display
# % key_desc: integer
# % required: no
# % answer: 1
# %end

# %flag:
# % key: f
# % description: Flip legend
# % guisection: Extra options
# %end

# %flag:
# % key: d
# % description: Add histogram to legend
# % guisection: Extra options
# %end

# %flag:
# % key: t
# % description: Draw legend ticks for labels
# % guisection: Extra options
# %end

# ------------------------------------------------------------------------------

# %option
# % key: font
# % type: string
# % description: Font name
# % key_desc: string
# % required: no
# % answer: Arial
# % guisection: Font settings
# %end

# %option
# % key: fontsize
# % type: integer
# % description: Font size
# % key_desc: integer
# % required: no
# % answer: 10
# % guisection: Font settings
# %end

# =======================================================================
# General
# =======================================================================

# import libraries
import os
import sys
import math
import grass.script as grass
from grass.pygrass.modules import Module
from grass.script.utils import parse_key_val
import imp

try:
    imp.find_module("PIL")
    found = True
    from PIL import Image
except ImportError:
    found = False


# main function
def main():

    # parameters - file name and extension
    outputfile = options["file"]
    ext = outputfile.split(".")
    if len(ext) == 1:
        grass.fatal("Please provide the file extension of the output file")
    filetype = options["filetype"]
    if filetype == "cairo":
        allowed = (".png", ".bmp", "ppm", "pdf", "ps", "svg")
        if not outputfile.lower().endswith(allowed):
            grass.fatal("Unknown display driver <{}>".format(ext[1]))
    if filetype == "ps" and not ext[1] == "ps":
        grass.fatal(
            "The file type <{}> does not match the file extension <"
            "{}>".format(filetype, ext[1])
        )
    if filetype == "png" and not ext[1] == "png":
        grass.fatal(
            "The file type <{}> does not match the file extension <"
            "{}>".format(filetype, ext[1])
        )

    # parameters - image settings
    unit = options["unit"]
    resol = options["resolution"]
    if resol == "":
        if unit == "px":
            resol = 96
        else:
            resol = 300
    else:
        resol = int(resol)
    dimensions = options["dimensions"]
    width, height = dimensions.split(",")
    bgcolor = options["color"]
    inmap = options["raster"]
    labelnum = options["labelnum"]
    vr = options["range"]
    font = options["font"]
    fontsize = int(options["fontsize"])
    digits = int(options["digits"])
    labval = options["label_values"]
    labstep = options["label_step"]

    # flag parameters
    flag_f = flags["f"]
    flag_d = flags["d"]
    flag_t = flags["t"]
    if flag_t:
        tagmargin = 9
    else:
        tagmargin = 4

    # Compute output size of legend bar in pixels
    if unit == "cm":
        bw = math.ceil(float(width) / 2.54 * float(resol))
        bh = math.ceil(float(height) / 2.54 * float(resol))
    elif unit == "mm":
        bw = math.ceil(float(width) / 25.4 * float(resol))
        bh = math.ceil(float(height) / 25.4 * float(resol))
    elif unit == "inch":
        bw = math.ceil(float(width) * float(resol))
        bh = math.ceil(float(height) * float(resol))
    elif unit == "px":
        bw = float(width)
        bh = float(height)
    else:
        grass.error("Unit must be inch, cm, mm or px")

    # Add size of legend to w or h, if flag_d is set
    # Add size of tics
    if flag_d:
        histmargin = 2.75
    else:
        histmargin = 1
    if float(height) > float(width):
        w = bw * histmargin + tagmargin
        h = bh + 4
    else:
        h = bh * histmargin + tagmargin
        w = bw + 4

    # Determine image width and height
    if fontsize == 0:
        fz = 1
    else:
        fz = round(float(fontsize) * (float(resol) / 72.272))

    # Determine space at left and right (or top and bottom)
    # based on fontsize (fz) and number of digits
    maprange = grass.raster_info(inmap)
    maxval = round(maprange["max"], digits)
    minval = round(maprange["min"], digits)
    if maxval < 1:
        maxl = len(str(maxval)) - 1
    else:
        maxl = len(str(maxval)) - 2
    if minval < 1:
        minl = len(str(minval)) - 1
    else:
        minl = len(str(minval)) - 2
    margin_left = 0.5 * minl * fz
    margin_right = 0.5 * maxl * fz

    # Page width and height (iw, ih)
    # Position bar in percentage (*margin)
    # Here we take into account the extra space for the numbers and ticks

    if float(height) > float(width):
        iw = w + fz * maxl
        ih = h + margin_left + margin_right
        bmargin = str(margin_left / ih * 100)
        tmargin = str(100 - (margin_right / ih * 100))
        rmargin = str(100 * (w - tagmargin) / iw - 1)
        if flag_d:
            lmargin = str((2 + (bw * 1.75)) / iw * 100)
        else:
            lmargin = str(2 / iw * 100)
    else:
        iw = w + margin_left + margin_right
        ih = h + fz * 1.5
        bmargin = str((2 + tagmargin + fz * 1.5) / ih * 100)
        if flag_d:
            tmargin = str(100 - (2 + (bh * 1.75)) / ih * 100)
        else:
            tmargin = str(100 - 2 / ih * 100)
        lmargin = str(margin_left / iw * 100)
        rmargin = str(100 - margin_right / iw * 100)
    at = (bmargin, tmargin, lmargin, rmargin)

    # Open file connection, set font
    os.environ["GRASS_RENDER_IMMEDIATE"] = filetype
    os.environ["GRASS_RENDER_FILE"] = outputfile
    os.environ["GRASS_RENDER_HEIGHT"] = str(ih)
    os.environ["GRASS_RENDER_WIDTH"] = str(iw)
    if bgcolor == "none":
        os.environ["GRASS_RENDER_TRANSPARENT"] = "TRUE"
    else:
        os.environ["GRASS_RENDER_BACKGROUNDCOLOR"] = bgcolor
    if flag_f and fontsize == 0:
        flag = "cfsv"
    elif flag_f:
        flag = "fsv"
    elif fontsize == 0:
        flag = "csv"
    else:
        flag = "sv"
    if flag_d:
        flag = flag + "d"
    if flag_t:
        flag = flag + "t"

    # Write legend with various options
    d_legend = Module(
        "d.legend",
        flags=flag,
        raster=inmap,
        font=font,
        at=at,
        fontsize=fz,
        labelnum=labelnum,
        run_=False,
    )
    if vr:
        val_range = map(float, vr.split(","))
        d_legend.inputs.range = val_range
    if labval:
        label_values = map(float, labval.split(","))
        d_legend.inputs.label_values = label_values
    if labstep:
        label_step = float(labstep)
        d_legend.inputs.label_step = label_step
    d_legend.run()

    # Set image resolution
    if found and outputfile.lower().endswith((".png", ".bmp")):
        im = Image.open(outputfile)
        im.save(outputfile, dpi=(resol, resol))

    # Provide informatie about image on standard output
    grass.message("----------------------------\n")
    grass.message("File saved as {}".format(outputfile))
    grass.message("The image dimensions are:\n")
    grass.message("{} px wide and {} px heigh\n".format(str(int(iw)), str(int(ih))))
    if unit == "inch":
        wr = round(iw / resol, 3)
        hr = round(ih / resol, 3)
    elif unit == "cm":
        wr = round(iw / resol * 2.54, 3)
        hr = round(ih / resol * 2.54, 3)
    elif unit == "mm":
        wr = round(iw / resol * 2.54 * 10, 3)
        hr = round(ih / resol * 2.54 * 10, 3)
    else:
        wr = "same"
    if wr != "same":
        grass.message("at a resolution of {} ppi this is:".format(str(resol)))
        grass.message("{0} {2} x {1} {2}\n".format(str(wr), str(hr), unit))
    grass.message("----------------------------\n")


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
