#!/usr/bin/env python

############################################################################
#
# MODULE:    r.out.kde
# AUTHOR(S): Anna Petrasova
#
# PURPOSE:
# COPYRIGHT: (C) 2013 - 2019 by the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# %module
# % description: Exports raster with variable transparency into an image file
# % keyword: raster
# % keyword: kernel density
# % keyword: visualization
# % keyword: transparency
# % keyword: heatmap
# %end

# %option G_OPT_R_INPUT
# % description: Raster map to be rendered with semi-transparency
# %end

# %option G_OPT_R_INPUT
# % key: background
# % description: Background raster map
# %end

# %option G_OPT_F_OUTPUT
# % description: Rendered output file
# %end

# %option
# % key: method
# % type: string
# % options: linear,logistic
# % description: Method to scale transparency
# %end


import os
import tempfile
import atexit
import shutil
from math import exp
import grass.script as gscript


TMPRAST = []
TMPDIR = tempfile.mkdtemp()


def cleanup():
    gscript.run_command(
        "g.remove", name=",".join(TMPRAST), flags="f", type="raster", quiet=True
    )
    shutil.rmtree(TMPDIR)


def main(rinput, background, output, method):
    try:
        from PIL import Image
    except ImportError:
        gscript.fatal("Cannot import PIL." " Please install the Python pillow package.")

    if "@" in rinput:
        rinput = rinput.split("@")[0]
    suffix = "_" + os.path.basename(gscript.tempfile(False))
    tmpname = rinput + suffix
    gscript.run_command("g.copy", raster=[rinput, tmpname])
    TMPRAST.append(tmpname)
    gscript.run_command("r.colors", map=tmpname, color="grey")

    reg = gscript.region()
    width = reg["cols"]
    height = reg["rows"]

    fg_out = os.path.join(TMPDIR, "foreground.png")
    bg_out = os.path.join(TMPDIR, "background.png")
    intensity_tmp = os.path.join(TMPDIR, "intensity.png")
    gscript.run_command(
        "d.mon",
        start="cairo",
        output=fg_out,
        width=width,
        height=height,
        bgcolor="black",
    )
    gscript.run_command("d.rast", map=rinput)
    gscript.run_command("d.mon", stop="cairo")

    # background
    gscript.run_command(
        "d.mon", start="cairo", output=bg_out, width=width, height=height
    )
    gscript.run_command("d.rast", map=background)
    gscript.run_command("d.mon", stop="cairo")

    # greyscale
    gscript.run_command(
        "d.mon", start="cairo", output=intensity_tmp, width=width, height=height
    )
    gscript.run_command("d.rast", map=tmpname)
    gscript.run_command("d.mon", stop="cairo")

    # put together with transparency
    foreground = Image.open(fg_out)
    background = Image.open(bg_out)
    intensity = Image.open(intensity_tmp)

    foreground = foreground.convert("RGBA")
    data_f = foreground.getdata()
    data_i = intensity.getdata()
    newData = []
    for i in range(len(data_f)):
        intens = data_i[i][0]
        if intens == 0:
            newData.append((data_f[i][0], data_f[i][1], data_f[i][2], 0))
        else:
            newData.append(
                (
                    data_f[i][0],
                    data_f[i][1],
                    data_f[i][2],
                    scale(0, 255, intens, method),
                )
            )
    foreground.putdata(newData)
    background.paste(foreground, (0, 0), foreground)
    background.save(output)


def scale(cmin, cmax, intens, method):
    # scale to 0 - 1
    val = (intens - cmin) / float((cmax - cmin))
    if method == "logistic":
        val = 1.0 / (1 + exp(-10 * (val - 0.5)))
    val *= 255
    return int(val)


if __name__ == "__main__":
    options, flags = gscript.parser()
    rinput = options["input"]
    bg = options["background"]
    output = options["output"]
    method = options["method"]
    atexit.register(cleanup)
    main(rinput, bg, output, method)
