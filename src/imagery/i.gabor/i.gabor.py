#!/usr/bin/env python

############################################################################
#
# MODULE:       i.gabor
#
# AUTHOR(S):    Owen Smith <ocsmit@protonmail.com>
#
# PURPOSE:      Compute and convolve Gabor filter banks and for spatial
#               imagery.
#
# COPYRIGHT:    (C) 2021 by Owen Smith and the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
############################################################################

# %module
# % description: Creates Gabor filter bank for a 2-dimensional image
# % overwrite: yes
# % keyword: imagery
# % keyword: satellite
# % keyword: raster
# % keyword: filter
# % keyword: Gabor
# %end

# FLAGS
# %flag
# % key: c
# % description: Combine convolved filters into one raster
# %end
# %flag
# % key: i
# % description: Output imaginary component of filter, default is real component
# %end
# %flag
# % key: q
# % description: Create quantified binary output
# %end

# OPTIONS
# %option G_OPT_R_INPUT
# %end
# %option G_OPT_R_BASENAME_OUTPUT
# % description: Basename for filter bank outputs, unless -c flag (single output).
# %end
# %option
# % key: size
# % type: integer
# % required: no
# % description: Window size
# % answer: 11
# %end
# %option
# % key: orientation
# % type: double
# % required: no
# % multiple: yes
# % description: List of orientations in degrees
# % answer: 0,45,90,135
# %end
# %option
# % key: wavelength
# % type: double
# % required: no
# % description: Wavelength of sinusoidal wave in pixels
# % answer: 3
# %end
# %option
# % key: offset
# % type: integer
# % required: no
# % description: Phase offset from the center of the window
# % answer: 0
# %end
# %option
# % key: aspect
# % type: double
# % required: no
# % description: Aspect ratio, specifies ellipticity of kernel
# % answer: 0.5
# %end
# %option
# % key: threshold
# % type: integer
# % required: no
# % description: Percentile threshold to extract
# % answer: 0
# %end

import os
import sys
import numpy as np

if "GISBASE" not in os.environ:
    sys.stderr.write(_("You must be in GRASS GIS to run this program.\n"))
    sys.exit(1)

import grass.script as grass
from grass.script import array as garray


def deg_to_radians(deg):
    return deg * np.pi / 180


def gabor2d(win_size, orientation=0, wavelength=5, aspect=0.5, offset=0, ntype="real"):
    # Get window size +/- around origin
    xy = win_size // 2

    # Check to make sure wave length is not greater than half the window size
    if wavelength >= xy:
        grass.fatal(_("A wavelength smaller than w / 2 is needed"))

    # Convert degrees to radians
    orientation = deg_to_radians(orientation)
    stddev = xy // wavelength
    max = xy
    min = -xy
    (y, x) = np.meshgrid(np.arange(min, max + 1), np.arange(min, max + 1))
    xr = x * np.cos(orientation) + y * np.sin(orientation)
    yr = -x * np.sin(orientation) + y * np.cos(orientation)

    gaussian = np.exp(-((xr**2 + aspect**2 * yr**2) / (2 * stddev**2)))
    if ntype == "imag":
        sf = np.sin(2 * np.pi * xr / wavelength + offset)
    else:
        sf = np.cos(2 * np.pi * xr / wavelength + offset)

    return gaussian * sf


def gabor_convolve(inarr, kern, thresh, quantify=0):
    con = fftconvolve(inarr, kern, mode="same")
    if not thresh:
        return con
    per = np.percentile(con, thresh)
    if quantify > 0:
        return np.where(con >= per, quantify, 0)
    return np.where(con >= per, con, 0)


def main():
    input = options["input"]
    output = options["output"]

    win_size = int(options["size"])
    orientation = [float(o) for o in options["orientation"].split(",")]
    wavelength = [float(f) for f in options["wavelength"].split(",")]
    offset = float(options["offset"])
    aspect = float(options["aspect"])
    threshold = int(options["threshold"])

    if flags["i"]:
        ntype = "imag"
    else:
        ntype = "real"

    if flags["q"]:
        if not threshold:
            grass.fatal(_("A percentile threshold is needed to quantify."))
        q = [2**i for i in range(len(orientation))]
    else:
        q = 0

    filters = {}
    for deg in orientation:
        for freq in wavelength:
            name = f"{win_size}_{deg}_{freq}_{offset}_{aspect}"
            filters[name] = gabor2d(win_size, deg, freq, aspect, offset, ntype)

    inarr = garray.array(input)
    if flags["c"]:
        convolved = []
        if type(q) == list:
            for i in range(len(filters.keys())):
                name = list(filters.keys())[i]
                convolved.append(gabor_convolve(inarr, filters[name], threshold, q[i]))
        else:
            for name in filters.keys():
                convolved.append(gabor_convolve(inarr, filters[name], threshold))
        outarr = garray.array()
        out = np.sum(convolved, axis=0)
        outarr[...] = out
        outarr.write(output)
    else:
        for name in filters.keys():
            outarr = garray.array()
            outarr[...] = gabor_convolve(inarr, filters[name], threshold)
            outarr.write(f"{output}_{name.replace('.', '')}")


if __name__ == "__main__":
    # Lazy import for scipy.signal.fftconvolve
    try:
        from scipy.signal import fftconvolve
    except ImportError:
        grass.fatal(_("Cannot import fftconvolve from scipy"))

    options, flags = grass.parser()
    sys.exit(main())
