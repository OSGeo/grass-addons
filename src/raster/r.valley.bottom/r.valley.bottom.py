#!/usr/bin/env python
# -*- coding: utf-8

"""
MODULE:    r.valley.bottom

AUTHOR(S): Helmut Kudrnovsky <alectoria AT gmx at>
           Steven Pawley <dr.stevenpawley@gmail.com>

PURPOSE:   Calculates Multi-resolution Valley Bottom Flatness (MrVBF) index
           Index is inspired by
           John C. Gallant and Trevor I. Dowling 2003.
           A multiresolution index of valley bottom flatness for mapping depositional areas.
           WATER RESOURCES RESEARCH, VOL. 39, NO. 12, 1347, doi:10.1029/2002WR001426, 2003

COPYRIGHT: (C) 2018 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

# %module
# % description: Calculation of Multi-resolution Valley Bottom Flatness (MrVBF) index
# % keyword: raster
# % keyword: terrain
# %end

# %option G_OPT_R_ELEV
# % key: elevation
# % description: Name of elevation raster map
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: mrvbf
# % description: Name of output MRVBF raster map
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: mrrtf
# % description: Name of output MRRTF raster map
# % required: no
# %end

# %option
# % key: t_slope
# % description: Initial Threshold for Slope
# % required: no
# % answer: 16
# % end

# %option
# % key: t_pctl_v
# % description: Threshold (t) for transformation of Elevation Percentile (Lowness)
# % required: no
# % answer: 0.4
# % end

# %option
# % key: t_pctl_r
# % description: Threshold (t) for transformation of Elevation Percentile (Upness)
# % required: no
# % answer: 0.3
# % end

# %option
# % key: t_vf
# % description: Threshold (t) for transformation of Valley Bottom Flatness
# % required: no
# % answer: 0.3
# % end

# %option
# % key: t_rf
# % description: Threshold (t) for transformation of Ridge Top Flatness
# % required: no
# % answer: 0.35
# % end

# %option
# % key: p_slope
# % description: Shape Parameter (p) for Slope
# % required: no
# % answer: 4
# % end

# %option
# % key: p_pctl
# % description: Shape Parameter (p) for Elevation Percentile
# % required: no
# % answer: 3
# % end

# %option
# % key: min_cells
# % description: Minimum number of cells in generalized DEM
# % required: no
# % answer: 2
# % end

# %flag
# % key: s
# % description: Use square moving window instead of circular moving window
# %end


import atexit
import math
import os
import random
import string
import sys

import grass.script as gs
from grass.pygrass.gis.region import Region
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.exceptions import ParameterError


if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def cleanup():
    """Clean-up procedure for module"""
    gs.message("Deleting intermediate files...")
    for k, v in TMP_RAST.items():
        for f in v:
            if len(gs.find_file(f)["fullname"]) > 0:
                g.remove(type="raster", name=f, flags="f", quiet=True)

    current_region.write()


def rand_id(prefix):
    """Generates a unique temporary mapname with a prefix for intermediate processing
    outputs.

    Parameters
    ----------
    prefix : str
        Prefix for the temporary mapname.

    Returns
    -------
    mapname : str
        A unique temporary mapname.
    """
    id = [random.choice(string.ascii_letters + string.digits) for n in range(4)]
    id = "".join(id)
    prefix = "_".join(["tmp", prefix])
    return "_".join([prefix, id])


def cell_padding(input, output, radius=3):
    """Mitigates edge effect by growing an input raster map by radius cells

    Parameters
    ----------
    input, output : str
        Names of GRASS raster map for input, and padded output.

    radius : int
        Radius in which to expand region and grow raster.

    Returns
    -------
    input_grown : str
        GRASS raster map which has been expanded by radius cells
    """

    g.region(grow=radius)
    r.grow(input=input, output=output, radius=radius, quiet=True)
    region = Region()

    return region


def focal_expr(radius, window_square=False):
    """Returns array offsets relative to centre pixel (0,0) for a matrix of
    size radius

    Parameters
    ----------
    radius : int
        Radius of the focal function.

    window_square : bool. Optional (default is False)
        Boolean to use a circular or square window.

    Returns
    -------
    offsets : list
        List of pixel positions (row, col) relative to the center pixel
        ( 1, -1)  ( 1, 0)  ( 1, 1)
        ( 0, -1)  ( 0, 0)  ( 0, 1)
        (-1, -1)  (-1, 0)  (-1, 1)
    """
    offsets = []

    # generate a list of spatial neighbourhood offsets for the chosen radius
    # ignoring the centre cell
    if window_square:
        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                if (i, j) != (0, 0):
                    offsets.append((i, j))
    else:
        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                row = i + radius
                col = j + radius
                row_start = row - radius
                col_start = col - radius

                if (
                    pow(row_start, 2) + pow(col_start, 2) <= pow(radius, 2)
                    and (
                        i,
                        j,
                    )
                    != (0, 0)
                ):
                    offsets.append((j, i))

    return offsets


def elevation_percentile(input, radius=3, window_square=False):
    """Calculates the percentile whichj is the ratio of the number of points of
    lower elevation to the total number of points in the surrounding region
    Args
    ----
    L : int
        Processing step (level)
    input : str
        GRASS raster map (elevation) to perform calculation on
    radius : int
        Neighborhood radius (in pixels)
    window_square : bool. Optional (default is False)
        Boolean to use square or circular neighborhood
    Returns
    -------
    PCTL : str
        Name of GRASS cell-padded raster map with elevation percentile for
        processing step L"""
    # get offsets for given neighborhood radius
    offsets = focal_expr(radius=radius, window_square=window_square)

    # generate grass mapcalc terms and execute
    n_pixels = float(len(offsets))

    # create mapcalc expr focal function and fill null neighbors with centre cell
    PCTL = rand_id("PCTL{}".format(L + 1))
    TMP_RAST[L].append(PCTL)

    terms = []
    for d in offsets:
        valid = ",".join(map(str, d))
        terms.append(
            "if( isnull({input}[{d}]), 1, {input}[{d}]<={input})".format(
                input=input, d=valid
            )
        )

    terms = "+".join(terms)
    expr = "{x} = ({s}) / {n}".format(x=PCTL, s=terms, n=n_pixels)
    gs.mapcalc(expr)

    return PCTL


def calc_slope(elevation):
    """Calculates slope angle in percent using r.slope.aspect

    Parameters
    ----------
    elevation : str
        Name of the GRASS raster map with the elevation data.

    Returns
    -------
    slope : str
        Name of the output slope map.
    """
    slope = rand_id("slope{}".format(L + 1))
    TMP_RAST[L].append(slope)
    r.slope_aspect(
        elevation=elevation, slope=slope, flags="e", format="percent", quiet=True
    )

    return slope


def flatness(slope, t, p):
    """Calculates the flatness index (equation 2 of Gallant and Dowling, 2003)

    Flatness F1 = 1 / (1 + pow ((slope / t), p)

    Parameters
    ----------
    slope : str
        Name of the GRASS raster map with slope in percent.

    t : float
        The threshold parameter for the logistic transformation. This defines the mid-point
        value of the logistic function, which represents the threshold for when a pixel is
        considered flat.

    p : float
        The shape parameter for the flatness transformation. This is the smoothness of
        the logistic function, i.e. large values cause a rapid transition from 0 -> 1
        resulting in a rapid transition from non-flat to flat terrain.

    Returns
    -------
    F : str
        Name of the transformed flatness GRASS raster map.
    """
    F = rand_id("F{}".format(L + 1))
    TMP_RAST[L].append(F)
    gs.mapcalc("$g = 1.0 / (1.0 + pow(($x / $t), $p))", g=F, x=slope, t=t, p=p)

    return F


def prelim_flatness_valleys(F, PCTL, t, p):
    """Transform elevation percentile to a local lowness value and multiply by
    flatness.

    Equation 3 (Gallant and Dowling, 2003):
    PVF = F * (1 / (1 + (PCTL / t)^p)

    Equation (1) multiplied by flatness (F) to produce the preliminary
    valley flatness index (PVF).

    Parameters
    ----------
    F : str
        Name of GRASS raster map representing the flatness index.

    PCTL : str
        Name of the GRASS raster map representing the elevation percentile
        metric.

    t : float
        The threshold parameter for the logistic transformation. This defines the mid-point
        value of the logistic function, which represents the threshold for when a pixel is
        considered low or high.

    p : float
        The shape parameter for the flatness transformation. This is the smoothness of
        the logistic function, i.e. large values cause a rapid transition from 0 -> 1
        resulting in a rapid transition from low to high terrain.

    Returns
    -------
    PVF : str
        The name of the GRASS raster map containing the preliminary flatness index.
    """

    PVF = rand_id("PVF{}".format(L + 1))
    TMP_RAST[L].append(PVF)
    gs.mapcalc(
        "$g = $a * (1.0 / (1.0 + pow(($x / $t), $p)))", g=PVF, a=F, x=PCTL, t=t, p=p
    )

    return PVF


def prelim_flatness_ridges(F, PCTL, t, p):
    """The same calculation as the prelim flatness index, except elevation is transformed
    to 'lowness', i.e. 1-PCTL.
    """

    PVF = rand_id("PVR{}".format(L + 1))
    TMP_RAST[L].append(PVF)
    gs.mapcalc(
        "$g = $a * (1.0 / (1.0 + pow(((1-$x) / $t), $p)))", g=PVF, a=F, x=PCTL, t=t, p=p
    )

    return PVF


def valley_flatness(PVF, t, p):
    """Calculation of the valley flatness VF (equation 4, Gallant and Dowling, 2003)

    Larger values of VF1 indicate increasing valley bottom character with values less
    than 0.5 considered not to be in valley bottoms.

    Parameters
    ----------
    PVF : str
        Name of the GRASS raster map with the preliminary flatness index.

    t : float
        The threshold parameter for the logistic transformation. This defines the mid-point
        value of the logistic function, which represents the threshold for when a pixel is
        considered to be in a valley bottom, or not.

    p : float
        The shape parameter for the flatness transformation. This is the smoothness of
        the logistic function, i.e. large values cause a rapid transition from 0 -> 1
        resulting in a rapid transition from valley bottom to non-valley bottom terrain.

    Returns
    -------
    VF : str
        Name of the GRASS raster map containing the valley flatness index.
    """
    VF = rand_id("VF{}".format(L + 1))
    TMP_RAST[L].append(VF)
    gs.mapcalc("$g = 1 - (1.0 / (1.0 + pow(($x / $t), $p)))", g=VF, x=PVF, t=t, p=p)

    return VF


def calc_mrvbf(VF1, VF2, t):
    """Calculation of the MRVBF index.

    Parameters
    ----------
    VF1 : str
        Name of the GRASS raster map representing the valley flatness index from the
        previous step (L-1).

    VF2 : str
        Name of the GRASS raster map representing the valley flatness index from the
        current step.

    t : float
        The threshold parameter for the logistic transformation. This defines the mid-point
        value of the logistic function.

    Returns
    -------
    MRVBF : str
        Name of the GRASS raster map with the MrVBF index for the current processing
        step.
    """

    # Calculation of weight W2 (Equation 9)
    W = rand_id("W{}".format(L + 1))
    TMP_RAST[L].append(W)
    p = (math.log10(((L + 1) - 0.5) / 0.1)) / math.log10(1.5)
    gs.mapcalc("$g = 1 - (1.0 / (1.0 + pow(($x / $t), $p)))", g=W, x=VF2, t=t, p=p)

    # Calculation of MRVBF2	(Equation 8)
    MRVBF = rand_id("MRVBF{}".format(L + 1))
    TMP_RAST[L].append(MRVBF)
    gs.mapcalc(
        "$MBF = ($W * ($L + $VF2)) + ((1 - $W) * $VF1)",
        MBF=MRVBF,
        L=L,
        W=W,
        VF2=VF2,
        VF1=VF1,
    )

    return MRVBF


def combined_flatness(F1, F2):
    """Calculates the combined flatness index (equation 13, Gallanet and Dowling, 2003)

    CF = F1 * F2

    Parameters
    ----------
    F1 : str
        Name of the GRASS raster map with the flatness index from the previous step (L-1)

    F2 : str
        Name of the GRASS raster map with the flatness index from the current step (L)

    Returns
    -------
    CF : str
        Name of hte GRASS raster map with the combined flatness index.
    """
    CF = rand_id("CF{}".format(L + 1))
    TMP_RAST[L].append(CF)
    gs.mapcalc("$CF = $F1 * $F2", CF=CF, F1=F1, F2=F2)

    return CF


def smooth_dem(DEM):
    """Smooth the DEM using an 11 cell averaging filter with gauss weighting of 3 radius"""

    smoothed = rand_id("smoothed{}".format(L + 1))
    TMP_RAST[L].append(smoothed)

    r.neighbors(
        input=DEM,
        output=smoothed,
        size=11,
        weighting_function="gaussian",
        weighting_factor=3,
    )

    return smoothed


def refine(input, region, method="bilinear"):
    """change resolution back to base resolution and resample a raster"""

    # grow input
    input_padded = rand_id("padded{}".format(L + 1))
    cell_padding(input=input, output=input_padded, radius=2)

    # resample
    refined = rand_id("refined{}".format(L + 1))
    TMP_RAST[L].append(refined)

    region.write()

    if method == "bilinear":
        r.resamp_interp(input=input_padded, output=refined, method="bilinear")

    if method == "average":
        r.resamp_stats(input=input_padded, output=refined, method="average", flags="w")

    # remove padded raster
    g.remove(type="raster", name=input_padded, flags="f", quiet=True)

    return refined


def step_message(L, xres, yres, ncells, t_slope):
    gs.message(
        "step {L}, ew_res {ewres}, ns_res {nsres}, remaining cells {ncells}, threshold slope {t}".format(
            L=L + 1,
            ewres=round(xres, 2),
            nsres=round(yres, 2),
            ncells=ncells,
            t=t_slope,
        )
    )


def main():
    r_elevation = options["elevation"]
    mrvbf = options["mrvbf"].split("@")[0]
    mrrtf = options["mrrtf"].split("@")[0]
    t_slope = float(options["t_slope"])
    t_pctl_v = float(options["t_pctl_v"])
    t_pctl_r = float(options["t_pctl_r"])
    t_vf = float(options["t_rf"])
    t_rf = float(options["t_rf"])
    p_slope = float(options["p_slope"])
    p_pctl = float(options["p_pctl"])
    moving_window_square = flags["s"]
    min_cells = int(options["min_cells"])

    global current_region, TMP_RAST, L
    TMP_RAST = {}
    current_region = Region()

    # some checks
    if (
        t_slope <= 0
        or t_pctl_v <= 0
        or t_pctl_r <= 0
        or t_vf <= 0
        or t_rf <= 0
        or p_slope <= 0
        or p_pctl <= 0
    ):
        gs.fatal("Parameter values cannot be <= 0")

    if min_cells < 2:
        gs.fatal("Minimum number of cells in generalized DEM cannot be less than 2")

    if min_cells > current_region.cells:
        gs.fatal(
            "Minimum number of cells in the generalized DEM cannot exceed the ungeneralized number of cells"
        )

    # calculate the number of levels
    levels = 2
    remaining_cells = current_region.cells
    while remaining_cells >= min_cells:
        levels += 1
        g.region(nsres=Region().nsres * 3, ewres=Region().ewres * 3)
        remaining_cells = Region().cells
    current_region.write()

    if levels < 3:
        gs.fatal(
            "MRVBF algorithm requires a greater level of generalization. Reduce number of min_cells or use a larger computational region."
        )

    gs.message("Parameter Settings")
    gs.message("------------------")
    gs.message(
        "min_cells = %d will result in %d generalization steps" % (min_cells, levels)
    )

    # intermediate outputs
    Xres_step = list()
    Yres_step = list()

    DEM = list()
    SLOPE = list()
    F = list()
    PCTL = list()
    PVF = list()
    PVF_RF = list()
    VF = list()
    VF_RF = list()
    MRVBF = list()
    MRRTF = list()

    # step 1 at base resolution -------------------------------------------------------
    L = 0
    TMP_RAST[L] = list()
    Xres_step.append(current_region.ewres)
    Yres_step.append(current_region.nsres)
    DEM.append(r_elevation)
    radius = 3

    step_message(L, Xres_step[L], Yres_step[L], current_region.cells, t_slope)

    # calculation of slope (S1) and calculation of flatness (F1) (equation 2)
    SLOPE.append(calc_slope(DEM[L]))
    F.append(flatness(SLOPE[L], t_slope, p_slope))

    # calculation of elevation percentile PCTL for step 1
    PCTL.append(elevation_percentile(DEM[L], radius, moving_window_square))

    # transform elevation percentile to local lowness for step 1 (equation 3)
    PVF.append(prelim_flatness_valleys(F[L], PCTL[L], t_pctl_v, p_pctl))

    if mrrtf != "":
        PVF_RF.append(prelim_flatness_ridges(F[L], PCTL[L], t_pctl_r, p_pctl))

    # calculation of the valley flatness step 1 VF1 (equation 4)
    VF.append(valley_flatness(PVF[L], t_vf, p_slope))
    MRVBF.append(None)

    if mrrtf != "":
        VF_RF.append(valley_flatness(PVF_RF[L], t_rf, p_slope))
        MRRTF.append(None)

    # step 2 at base scale resolution -------------------------------------------------
    L = 1
    TMP_RAST[L] = list()
    Xres_step.append(current_region.ewres)
    Yres_step.append(current_region.nsres)
    DEM.append(r_elevation)
    t_slope /= 2.0
    radius = 6

    step_message(L, Xres_step[L], Yres_step[L], current_region.cells, t_slope)

    # calculation of flatness for step 2 (equation 5)
    SLOPE.append(SLOPE[L - 1])
    F.append(flatness(SLOPE[L], t_slope, p_slope))

    # calculation of elevation percentile PCTL for step 2 (radius of 6 cells)
    PCTL.append(elevation_percentile(r_elevation, radius, moving_window_square))

    # PVF for step 2 (equation 6)
    PVF.append(prelim_flatness_valleys(F[L], PCTL[L], t_pctl_v, p_pctl))
    if mrrtf != "":
        PVF_RF.append(prelim_flatness_ridges(F[L], PCTL[L], t_pctl_r, p_pctl))

    # calculation of the valley flatness VF for step 2 (equation 7)
    VF.append(valley_flatness(PVF[L], t_vf, p_slope))
    if mrrtf != "":
        VF_RF.append(valley_flatness(PVF_RF[L], t_rf, p_slope))

    # calculation of MRVBF for step 2
    MRVBF.append(calc_mrvbf(VF1=VF[L - 1], VF2=VF[L], t=t_pctl_v))
    if mrrtf != "":
        MRRTF.append(calc_mrvbf(VF1=VF_RF[L - 1], VF2=VF_RF[L], t=t_pctl_r))

    # update flatness for step 2 with combined flatness from F1 and F2 (equation 10)
    F[L] = combined_flatness(F[L - 1], F[L])

    # remaining steps -----------------------------------------------------------------
    # for steps >= 2, each step uses the smoothing radius of the current step
    # but at the dem resolution of the previous step
    remaining_cells = current_region.cells

    while remaining_cells >= min_cells:
        L += 1
        TMP_RAST[L] = list()
        t_slope /= 2.0
        Xres_step.append(Xres_step[L - 1] * 3)
        Yres_step.append(Yres_step[L - 1] * 3)
        radius = 6

        # delete temporary maps from L-2
        for tmap in TMP_RAST[L - 2]:
            if len(gs.find_file(tmap)["fullname"]) > 0:
                g.remove(type="raster", name=tmap, flags="f", quiet=True)

        # coarsen resolution to resolution of previous step (step L-1) and smooth DEM
        if L > 2:
            g.region(ewres=Xres_step[L - 1], nsres=Yres_step[L - 1])

        step_message(L, Xres_step[L], Yres_step[L], remaining_cells, t_slope)
        DEM.append(smooth_dem(DEM[L - 1]))

        # calculate slope at coarser resolution
        SLOPE.append(calc_slope(DEM[L]))

        # refine slope back to base resolution
        if L > 2:
            SLOPE[L] = refine(SLOPE[L], current_region, method="bilinear")

        # coarsen resolution to current step L and calculate PCTL
        g.region(ewres=Xres_step[L], nsres=Yres_step[L])
        remaining_cells = Region().cells
        DEM[L] = refine(DEM[L], Region(), method="average")
        PCTL.append(elevation_percentile(DEM[L], radius, moving_window_square))

        # refine PCTL to base resolution
        PCTL[L] = refine(PCTL[L], current_region, method="bilinear")

        # calculate flatness F at the base resolution
        F.append(flatness(SLOPE[L], t_slope, p_slope))

        # update flatness with combined flatness CF from the previous step
        F[L] = combined_flatness(F1=F[L - 1], F2=F[L])

        # calculate preliminary valley flatness index PVF at the base resolution
        PVF.append(prelim_flatness_valleys(F[L], PCTL[L], t_pctl_v, p_pctl))
        if mrrtf != "":
            PVF_RF.append(prelim_flatness_ridges(F[L], PCTL[L], t_pctl_r, p_pctl))

        # calculate valley flatness index VF
        VF.append(valley_flatness(PVF[L], t_vf, p_slope))
        if mrrtf != "":
            VF_RF.append(valley_flatness(PVF_RF[L], t_rf, p_slope))

        # calculation of MRVBF
        MRVBF.append(calc_mrvbf(VF1=MRVBF[L - 1], VF2=VF[L], t=t_pctl_v))
        if mrrtf != "":
            MRRTF.append(calc_mrvbf(VF1=MRRTF[L - 1], VF2=VF_RF[L], t=t_pctl_r))

    # output final MRVBF --------------------------------------------------------------
    current_region.write()
    gs.mapcalc("$x = $y", x=mrvbf, y=MRVBF[L])

    if mrrtf != "":
        gs.mapcalc("$x = $y", x=mrrtf, y=MRRTF[L])


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
