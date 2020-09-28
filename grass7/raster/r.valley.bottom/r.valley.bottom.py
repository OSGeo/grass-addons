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

#%Module
#% description: Calculation of Multi-resolution Valley Bottom Flatness (MrVBF) index
#% keyword: raster
#% keyword: terrain
#%end

#%option G_OPT_R_ELEV
#% key: elevation
#% description: Name of elevation raster map
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#% key: mrvbf
#% description: Name of output MRVBF raster map
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#% key: mrrtf
#% description: Name of output MRRTF raster map
#% required: no
#%end

#%option
#% key: t_slope
#% type: double
#% description: Initial Threshold for Slope
#% required: no
#% answer: 16
#% end

#%option
#% key: t_pctl_v
#% type: double
#% description: Threshold (t) for transformation of Elevation Percentile (Lowness)
#% required: no
#% answer: 0.4
#% end

#%option
#% key: t_pctl_r
#% type: double
#% description: Threshold (t) for transformation of Elevation Percentile (Upness)
#% required: no
#% answer: 0.3
#% end

#%option
#% key: t_vf
#% type: double
#% description: Threshold (t) for transformation of Valley Bottom Flatness
#% required: no
#% answer: 0.3
#% end

#%option
#% key: t_rf
#% type: double
#% description: Threshold (t) for transformation of Ridge Top Flatness
#% required: no
#% answer: 0.35
#% end

#%option
#% key: p_slope
#% type: double
#% description: Shape Parameter (p) for Slope
#% required: no
#% answer: 4
#% end

#%option
#% key: p_pctl
#% type: double
#% description: Shape Parameter (p) for Elevation Percentile
#% required: no
#% answer: 3
#% end

#%option
#% key: min_cells
#% type: integer
#% description: Number of cells in the DEM at the coarsest generalization level
#% required: no
#% answer: 1
#% end

#%option
#% key: n_jobs
#% type: integer
#% description: Number of processes cores for computation
#% required: no
#% answer: 1
#% end

#%flag
#% key: s
#% description: Use square moving window instead of circular moving window
#%end


import sys
import os
import math
import atexit
import random
import string
import multiprocessing as mp

import grass.script as gs
from grass.pygrass.gis.region import Region
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.grid import GridModule


if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def cleanup():
    """Clean-up procedure upon module exit
    """
    gs.message("Deleting intermediate files...")

    for k, v in TMP_RAST.items():
        for f in v:
            if len(gs.find_file(f)["fullname"]) > 0:
                gs.run_command("g.remove", type="raster", name=f, flags="f", quiet=True)

    Region.write(current_region)


def rand_id(prefix):
    unique = [random.choice(string.ascii_letters + string.digits) for n in range(4)]
    unique = "".join(unique)
    id = "_".join([prefix, unique])

    return id


def tile_shape(region, n_jobs):
    """Calculates the number of tiles required for one tile per cpu

    Parameters
    ----------
    region : pygrass.gis.region.Region
        The computational region object.
    
    n_jobs : int
        The number of processing cores.
    
    Returns
    -------
    width, height : tuple
        The width and height of each tile.
    """
    n = math.sqrt(n_jobs)
    width = math.ceil(region.cols / n)
    height = math.ceil(region.rows / n)

    if width < 250 or height < 250:
        width = region.cols
        height = region.rows

    return width, height


def focal_expr(radius, window_square=False):
    """Returns array offsets relative to centre pixel (0,0) for a matrix of
    size radius

    Parameters
    ----------
    radius : int
        The radius of the focal function.

    window_square : bool (opt). Default is False
        Whether to use a circular or square focal window.

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

                if pow(row - radius, 2) + pow(col - radius, 2) <= pow(radius, 2) and (
                    i,
                    j,
                ) != (0, 0):
                    offsets.append((j, i))

    return offsets


def elevation_percentile(L, input, radius=3, window_square=False, n_jobs=1):
    """Calculates the percentile which is the ratio of the number of points of lower
    elevation to the total number of points in the surrounding region

    Notes
    -----
    Note this function is currently a bottle-neck of the module because r.mapcalc
    becomes slow with large statements. Ideally, a C module that calculates
    elevation percentile is required.

    Parameters
    ----------
    L : int
        The processing step (level).

    input : str
        The GRASS raster map (elevation) to perform calculation on.

    radius : int
        The neighborhood radius (in pixels).

    window_square : bool (opt). Default is False
        Whether to use a square or circular neighborhood.

    n_jobs : int
        The number of processing cores for parallel computation.

    Returns
    -------
    PCTL : str
        Name of the raster map with elevation percentile for processing step L
    """
    PCTL = rand_id(prefix="PCTL{L}".format(L=L + 1))
    TMP_RAST[L].append(PCTL)
    input_grown = input

    # get offsets for given neighborhood radius
    offsets = focal_expr(radius=radius, window_square=window_square)

    # generate grass mapcalc terms and execute
    n_pixels = float(len(offsets))

    # create mapcalc expr
    # if pixel in neighborhood contains nodata, attempt to use opposite neighbor
    # if opposite neighbor is also nodata, then use center pixel
    terms = []
    for d in offsets:
        valid = ",".join(map(str, d))
        invalid = ",".join([str(-d[0]), str(-d[1])])
        terms.append(
            "if(isnull({input}[{d}]), if(isnull({input}[{e}]), 1, {input}[{e}]<={input}), {input}[{d}]<={input})".format(
                input=input_grown, d=valid, e=invalid
            )
        )

    expr = "{x} = ({terms}) / {n}".format(x=PCTL, terms=" + ".join(terms), n=n_pixels)

    region = Region()
    width, height = tile_shape(region, n_jobs)

    if width < region.cols and height < region.rows and n_jobs > 1:
        grd = GridModule(
            cmd="r.mapcalc.simple",
            width=width,
            height=height,
            processes=n_jobs,
            overlap=radius,
            mapset_prefix="PCTL",
            expression=expr,
            output=PCTL,
        )
        grd.run()
    else:
        gs.mapcalc(expr)

    return PCTL


def calc_slope(L, elevation):
    """Calculate terrain slope

    Parameters
    ----------
    L : int
        The processing step (level).

    elevation : str
        The GRASS raster map (elevation) to perform calculation on.

    Returns
    -------
    slope : str
        The name of the slope map.
    """
    slope = rand_id("slope_step{L}".format(L=L + 1))
    TMP_RAST[L].append(slope)
    r.slope_aspect(
        elevation=elevation, 
        slope=slope, 
        flags="e", 
        format="percent", 
        quiet=True
    )

    return slope


def flatness(L, slope, t, p):
    """Calculates the flatness index

    Flatness F1 = 1 / (1 + pow ((slope / t), p)
    Equation 2 (Gallant and Dowling, 2003)

    Parameters
    ----------
    L : int
        The processing step (level).

    slope : str
        The name of the slope map upon which to apply a logistic transform to calculate
        flatness.

    t : float
        The threshold parameters for the flatness transformation. This defines the mid-point
        value of the logistic function, which represents the threshold for when a pixel is
        considered flat.

    p : float
        The shape parameter for the flatness transformation. This is the smoothness of 
        the logistic function, i.e. large values cause a rapid transition from 0 -> 1
        resulting in a rapid transition from non-flat to flat terrain.

    Returns
    -------
    F : str
        The name of the flatness raster.
    """
    F = rand_id("F{L}".format(L=L + 1))
    TMP_RAST[L].append(F)

    expr = "{g} = 1.0 / (1.0 + pow(({x} / {t}), {p}))".format(g=F, x=slope, t=t, p=p)
    gs.mapcalc(expr)

    return F


def prelim_flatness_valleys(L, F, PCTL, t, p):
    """Transform elevation percentile to a local lowness value using equation (1) and
    combined with flatness F to produce the preliminary valley flatness index (PVF) for
    the first step.

    Equation 3 (Gallant and Dowling, 2003)

    Parameters
    ----------
    L : int
        The processing step (level).

    F : str
        The name of the relative flatness raster map.
    
    PCTL : str
        The name of the relative lowness raster map.
    
    t : float
        The threshold parameter for the logistic transform. This defines the mid-point
        of the logistic function, which represents the threshold for when a pixel is
        considered 'low'. The flatness is then multiplied by the lowness value so that 
        pixels that are either flat (F ≥ 0.5) or low (PCTL ≥ 0.5) will have values of 
        PVF ≥ 0.25.
    
    p : float
        The smoothness parameter for the logistic transform, i.e. how rapid the 
        transition from high to low terrain os.
    
    Returns
    -------
    PVF : str
        The name of the preliminary valley flatness index.
    """

    PVF = rand_id("PVF{L}".format(L=L + 1))
    TMP_RAST[L].append(PVF)

    expr = "{g} = {a} * (1.0 / (1.0 + pow(({x} / {t}), {p})))".format(
        g=PVF, a=F, x=PCTL, t=t, p=p
    )

    gs.mapcalc(expr)

    return PVF


def prelim_flatness_ridges(L, F, PCTL, t, p):
    """Transform elevation percentile to a local upness value using equation (1) and
    combined with flatness to produce the preliminary ridge top flatness index (PVF) for
    the first step

    Equation 3 (Gallant and Dowling, 2003)

    Parameters
    ----------
    L : int
        The processing step (level).

    F : str
        The name of the flatness raster map.
    
    PCTL : str
        The name of the elevation percentile raster map.
    
    t : float
        The threshold parameter.
    
    p : float
        The shape parameter.
    
    Returns
    -------
    PVF : str
        The name of the preliminary ridge top index raster.
    """

    PVF = rand_id("PVF_RF{L}".format(L=L + 1))
    TMP_RAST[L].append(PVF)

    expr = "{g} = {a} * (1.0 / (1.0 + pow(((1-{x}) / {t}), {p})))".format(
        g=PVF, a=F, x=PCTL, t=t, p=p
    )
    gs.mapcalc(expr)

    return PVF


def valley_flatness(L, PVF, t, p):
    """Calculation of the valley flatness step VF
    
    Larger values of VF1 indicate increasing valley bottom character with values less
    than 0.5 considered not to be in valley bottoms

    Equation 4 (Gallant and Dowling, 2003)
    
    Parameters
    ----------
    L : int
        The processing step (level).

    PVF : str
        The name of the preliminary flatness index raster map.
    
    t : float
        The threshold value.
    
    p : float
        The shape value.
    
    Returns
    -------
    VF : str
        The name of the valley flatness raster.
    """

    VF = rand_id("VF{L}".format(L=L + 1))
    TMP_RAST[L].append(VF)

    expr = "{g} = 1 - (1.0 / (1.0 + pow(({x} / {t}), {p})))".format(
        g=VF, x=PVF, t=t, p=p
    )
    gs.mapcalc(expr)

    return VF


def calc_mrvbf(L, VF_Lminus1, VF_L, t):
    """Calculation of the MRVBF index (requires that L>1)

    Parameters
    ----------
    L : int
        The processing step (level).

    VF_Lminus1 : str
        The name of the valley flatness index from the previous step.
    
    t : float
        The threshold value.
    
    Returns
    -------
    mrvbf : str
        The name of the Mrvbf raster map.
    """

    # Calculation of weight W2 (Equation 9)
    W = rand_id("W{L}".format(L=L + 1))
    TMP_RAST[L].append(W)

    p = (math.log10(((L + 1) - 0.5) / 0.1)) / math.log10(1.5)

    expr = "{g} = 1 - (1.0 / (1.0 + pow(({x} / {t}), {p})))".format(
        g=W, x=VF_L, t=t, p=p
    )
    gs.mapcalc(expr)

    # Calculation of MRVBF2	(Equation 8)
    mrvbf = rand_id("MRVBF{L}".format(L=L + 1))
    TMP_RAST[L].append(mrvbf)

    expr = "{MBF} = ({W} * ({L} + {VF})) + ((1 - {W}) * {VF1})".format(
        MBF=mrvbf, L=L, W=W, VF=VF_L, VF1=VF_Lminus1
    )
    gs.mapcalc(expr)

    return mrvbf


def combined_flatness(L, F1, F2):
    """Calculates the combined flatness index

    Equation 13 (Gallant and Dowling, 2003)
    
    Parameters
    ----------
    L : int
        The processing step (level).

    F1 : str
        The name of the flatness index 1 raster.
    
    F2 : str
        The name of the flatness index 2 raster.
    
    Returns
    -------
    CF : str
        The name of the combined flatness index raster.
    """

    CF = rand_id("CF{L}".format(L=L + 1))
    TMP_RAST[L].append(CF)

    expr = "{CF} = {F1} * {F2}".format(CF=CF, F1=F1, F2=F2)
    gs.mapcalc(expr)

    return CF


def smooth_dem(L, dem):
    """Smooth the DEM using an 11 cell averaging filter with gauss weighting of 3 radius

    Parameters
    ----------
    L : int
        The processing step (level).
    
    dem : str
        The name of the elevation raster map.
    
    Returns
    -------
    smoothed : str
        The name of the smoothed elevation map.
    """

    smoothed = rand_id("DEM_smoothed_step{L}".format(L=L + 1))
    TMP_RAST[L].append(smoothed)

    # g = 4.3565 * math.exp(-(3 / 3.0))
    r.neighbors(input=dem, output=smoothed, size=11, gauss=3)

    return smoothed


def upsample(L, input, region):
    """Change resolution back to base resolution and upsample (resample to finer
    resolution) a raster

    Parameters
    ----------
    L : int
        The processing step (level).

    input : str
        The name of the raster map to upsample
    
    region : grass.pygrass.gis.region.Region object
        The target computation region settings for upsampling.
    
    Returns
    -------
    refined_map : str
        The name of the refined/upsampled raster.
    """
    # pad input dem by 1 cell to avoid edge shrinkage
    radius = 1.01
    input_padded = rand_id("padded")

    g.region(grow=1)
    r.grow(
        input=input,
        output=input_padded,
        radius=radius+1,
        quiet=True
    )

    # upsample
    refined_map = rand_id("{x}_upsampled".format(x=input))
    TMP_RAST[L].append(refined_map)

    Region.write(region)
    r.resamp_interp(input=input_padded, output=refined_map, method="bilinear")
    g.remove(type="raster", name=input_padded, flags="f", quiet=True)

    return refined_map


def downsample(L, input, region):
    """Resample a raster to a coarser resolution

    Parameters
    ----------
    L : int
        The processing step (level).
    
    input : str
        The name of the raster map to upsample
    
    region : grass.pygrass.gis.region.Region object
        The target computation region settings for downsampling.

    Returns
    -------
    refined_map : str
        The name of the refined/upsampled raster.
    """
    refined_map = rand_id("{x}_coarsened_to_step_L{L}".format(x=input, L=L))
    TMP_RAST[L].append(refined_map)

    Region.write(region)

    r.resamp_stats(input=input, output=refined_map, method="average", flags="w")

    return refined_map


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
    n_jobs = int(options["n_jobs"])

    global current_region
    global TMP_RAST
    TMP_RAST = {}
    current_region = Region()

    # Some checks ---------------------------------------------------------------------
    if n_jobs == 0:
        gs.fatal("Number of processing cores for parallel computation must not equal 0")

    if n_jobs < 0:
        system_cores = mp.cpu_count()
        n_jobs = system_cores + n_jobs + 1

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

    if min_cells < 1:
        gs.fatal("Minimum number of cells in generalized DEM cannot be less than 1")

    if min_cells > current_region.cells:
        gs.fatal(
            "Minimum number of cells in the generalized DEM cannot exceed the ungeneralized number of cells"
        )

    # Calculate number of levels ------------------------------------------------------
    levels = math.ceil(
        -math.log(float(min_cells) / current_region.cells) / math.log(3) - 2
    )
    levels = int(levels)

    if levels < 3:
        gs.fatal(
            "MRVBF algorithm requires a greater level of generalization. Reduce number of min_cells"
        )

    gs.message("Parameter Settings")
    gs.message("------------------")
    gs.message(
        "min_cells = %d will result in %d generalization steps" % (min_cells, levels)
    )

    # Dict to store temporary maps per level
    TMP_RAST = {k: [] for k in range(levels)}

    # Intermediate outputs
    Xres_step = list()
    Yres_step = list()
    DEM = list()
    slope = [0] * levels
    F = [0] * levels
    PCTL = [0] * levels
    PVF = [0] * levels
    PVF_RF = [0] * levels
    VF = [0] * levels
    VF_RF = [0] * levels
    MRVBF = [0] * levels
    MRRTF = [0] * levels

    # Step 1 (L=0) --------------------------------------------------------------------
    # Base scale resolution
    L = 0
    Xres_step.append(current_region.ewres)
    Yres_step.append(current_region.nsres)
    DEM.append(r_elevation)
    radi = 3

    g.message(os.linesep)
    g.message("Step {L}".format(L=L + 1))
    g.message("------")

    # Calculation of slope (S1) and calculation of flatness (F1) (Equation 2)
    gs.message(
        "Calculation of slope and transformation to flatness F{L}...".format(L=L + 1)
    )
    slope[L] = calc_slope(L, DEM[L])
    F[L] = flatness(L, slope[L], t_slope, p_slope)

    # Calculation of elevation percentile PCTL for step 1
    gs.message("Calculation of elevation percentile PCTL{L}...".format(L=L + 1))
    PCTL[L] = elevation_percentile(L, DEM[L], radi, moving_window_square, n_jobs)

    # Transform elevation percentile to local lowness for step 1 (Equation 3)
    gs.message(
        "Calculation of preliminary valley flatness index PVF{L}...".format(L=L + 1)
    )
    PVF[L] = prelim_flatness_valleys(L, F[L], PCTL[L], t_pctl_v, p_pctl)
    if mrrtf != "":
        gs.message(
            "Calculation of preliminary ridge top flatness index PRF{L}...".format(
                L=L + 1
            )
        )
        PVF_RF[L] = prelim_flatness_ridges(L, F[L], PCTL[L], t_pctl_r, p_pctl)

    # Calculation of the valley flatness step 1 VF1 (Equation 4)
    gs.message("Calculation of valley flatness VF{L}...".format(L=L + 1))
    VF[L] = valley_flatness(L, PVF[L], t_vf, p_slope)
    if mrrtf != "":
        gs.message("Calculation of ridge top flatness RF{L}...".format(L=L + 1))
        VF_RF[L] = valley_flatness(L, PVF_RF[L], t_rf, p_slope)

    # Step 2 (L=1) --------------------------------------------------------------------
    # Base scale resolution
    L = 1
    Xres_step.append(current_region.ewres)
    Yres_step.append(current_region.nsres)
    DEM.append(r_elevation)
    t_slope /= 2.0
    radi = 6

    gs.message(os.linesep)
    gs.message("Step {L}".format(L=L + 1))
    gs.message("------")

    # Calculation of flatness for step 2 (Equation 5)
    # The second step commences the same way with the original DEM at its base resolution,
    # using a slope threshold ts,2 half of ts,1:
    gs.message("Calculation of flatness F{L}...".format(L=L + 1))
    F[L] = flatness(L, slope[L - 1], t_slope, p_slope)

    # Calculation of elevation percentile PCTL for step 2 (radius of 6 cells)
    gs.message("Calculation of elevation percentile PCTL{L}...".format(L=L + 1))
    PCTL[L] = elevation_percentile(L, r_elevation, radi, moving_window_square, n_jobs)

    # PVF for step 2 (Equation 6)
    gs.message(
        "Calculation of preliminary valley flatness index PVF{L}...".format(L=L + 1)
    )
    PVF[L] = prelim_flatness_valleys(L, F[L], PCTL[L], t_pctl_v, p_pctl)
    if mrrtf != "":
        gs.message(
            "Calculation of preliminary ridge top flatness index PRF{L}...".format(
                L=L + 1
            )
        )
        PVF_RF[L] = prelim_flatness_ridges(L, F[L], PCTL[L], t_pctl_r, p_pctl)

    g.remove(type="raster", name=PCTL[L], flags="f", quiet=True)
    TMP_RAST[L].remove(PCTL[L])

    # Calculation of the valley flatness VF for step 2 (Equation 7)
    gs.message("Calculation of valley flatness VF{L}...".format(L=L + 1))
    VF[L] = valley_flatness(L, PVF[L], t_vf, p_slope)
    if mrrtf != "":
        gs.message("Calculation of ridge top flatness RF{L}...".format(L=L + 1))
        VF_RF[L] = valley_flatness(L, PVF_RF[L], t_rf, p_slope)

    # Calculation of MRVBF for step 2
    gs.message("Calculation of MRVBF{L}...".format(L=L + 1))
    MRVBF[L] = calc_mrvbf(L, VF_Lminus1=VF[L - 1], VF_L=VF[L], t=t_pctl_v)
    if mrrtf != "":
        gs.message("Calculation of MRRTF{L}...".format(L=L + 1))
        MRRTF[L] = calc_mrvbf(L, VF_Lminus1=VF_RF[L - 1], VF_L=VF_RF[L], t=t_pctl_r)

    # Update flatness for step 2 with combined flatness from F1 and F2 (Equation 10)
    gs.message("Calculation  of combined flatness index CF{L}...".format(L=L + 1))
    F[L] = combined_flatness(L, F[L - 1], F[L])

    # Remaining steps -----------------------------------------------------------------
    # DEM_1_1 refers to scale (smoothing) and resolution (cell size)
    # so that DEM_L1_L-1 refers to smoothing of current step,
    # but resolution of previous step
    for L in range(2, levels):

        t_slope /= 2.0
        Xres_step.append(Xres_step[L - 1] * 3)
        Yres_step.append(Yres_step[L - 1] * 3)
        radi = 6

        # delete temporary maps from L-2
        for tmap in TMP_RAST[L - 2]:
            g.remove(type="raster", name=tmap, flags="f", quiet=True)

        gs.message(os.linesep)
        gs.message("Step {L}".format(L=L + 1))
        gs.message("------")

        # Coarsen resolution to resolution of previous step (step L-1) and smooth DEM
        if L >= 3:
            gs.run_command("g.region", ewres=Xres_step[L - 1], nsres=Yres_step[L - 1])
            gs.message(
                "Coarsening resolution to ew_res={e} and ns_res={n}...".format(
                    e=Xres_step[L - 1], n=Yres_step[L - 1]
                )
            )

        gs.message(
            "DEM smoothing 11 x 11 windows with Gaussian smoothing kernel (sigma) 3..."
        )
        smoothed_dem = smooth_dem(L=L, dem=DEM[L - 1])
        DEM.append(smoothed_dem)

        if L > 2:
            g.remove(type="raster", name=DEM[L - 1], flags="f", quiet=True)
            TMP_RAST[L - 1].remove(DEM[L - 1])

        # Calculate slope
        gs.message("Calculation of slope...")
        slope[L] = calc_slope(L, DEM[L])

        # Refine slope to base resolution
        if L >= 3:
            gs.message("Resampling slope back to base resolution...")
            slope[L] = upsample(L, slope[L], current_region)

        # Coarsen resolution to current step L and calculate PCTL
        gs.run_command("g.region", ewres=Xres_step[L], nsres=Yres_step[L])
        DEM[L] = downsample(L, DEM[L], Region())
        gs.message("Calculation of elevation percentile PCTL{L}...".format(L=L + 1))
        PCTL[L] = elevation_percentile(L, DEM[L], radi, moving_window_square, n_jobs)
        
        # Refine PCTL to base resolution
        gs.message("Resampling PCTL{L} to base resolution...".format(L=L + 1))
        PCTL[L] = upsample(L, PCTL[L], current_region)

        # Calculate flatness F at the base resolution
        gs.message("Calculate F{L} at base resolution...".format(L=L + 1))
        F[L] = flatness(L, slope[L], t_slope, p_slope)
        g.remove(type="raster", name=slope[L], flags="f", quiet=True)
        TMP_RAST[L].remove(slope[L])

        # Update flatness with combined flatness CF from the previous step
        gs.message(
            "Calculate combined flatness CF{L} at base resolution...".format(L=L + 1)
        )
        F[L] = combined_flatness(L, F1=F[L - 1], F2=F[L])

        # Calculate preliminary valley flatness index PVF at the base resolution
        gs.message(
            "Calculate preliminary valley flatness index PVF{L} at base resolution...".format(
                L=L + 1
            )
        )
        PVF[L] = prelim_flatness_valleys(L, F[L], PCTL[L], t_pctl_v, p_pctl)
        if mrrtf != "":
            gs.message(
                "Calculate preliminary ridge top flatness index PRF{L} at base resolution...".format(
                    L=L + 1
                )
            )
            PVF_RF[L] = prelim_flatness_ridges(L, F[L], PCTL[L], t_pctl_r, p_pctl)
        
        g.remove(type="raster", name=PCTL[L], flags="f", quiet=True)
        TMP_RAST[L].remove(PCTL[L])

        # Calculate valley flatness index VF
        gs.message(
            "Calculate valley flatness index VF{L} at base resolution...".format(
                L=L + 1
            )
        )
        VF[L] = valley_flatness(L, PVF[L], t_vf, p_slope)
        g.remove(type="raster", name=PVF[L], flags="f", quiet=True)
        TMP_RAST[L].remove(PVF[L])

        if mrrtf != "":
            gs.message(
                "Calculate ridge top flatness index RF{L} at base resolution...".format(
                    L=L + 1
                )
            )
            VF_RF[L] = valley_flatness(L, PVF_RF[L], t_rf, p_slope)
            g.remove(type="raster", name=PVF_RF[L], flags="f", quiet=True)
            TMP_RAST[L].remove(PVF_RF[L])

        # Calculation of MRVBF
        gs.message("Calculation of MRVBF{L}...".format(L=L + 1))
        MRVBF[L] = calc_mrvbf(L, VF_Lminus1=MRVBF[L - 1], VF_L=VF[L], t=t_pctl_v)

        if mrrtf != "":
            gs.message("Calculation of MRRTF{L}...".format(L=L + 1))
            MRRTF[L] = calc_mrvbf(L, VF_Lminus1=MRRTF[L - 1], VF_L=VF_RF[L], t=t_pctl_r)

    # Output final MRVBF --------------------------------------------------------------
    expr = "{x} = {y}".format(x=mrvbf, y=MRVBF[L])
    gs.mapcalc(expr)

    if mrrtf != "":
        expr = "{x} = {y}".format(x=mrrtf, y=MRRTF[L])
        gs.mapcalc(expr)


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
