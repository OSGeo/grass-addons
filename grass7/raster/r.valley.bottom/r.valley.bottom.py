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

#%module
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
#% description: Initial Threshold for Slope
#% required: no
#% answer: 16
#% end

#%option
#% key: t_pctl_v
#% description: Threshold (t) for transformation of Elevation Percentile (Lowness)
#% required: no
#% answer: 0.4
#% end

#%option
#% key: t_pctl_r
#% description: Threshold (t) for transformation of Elevation Percentile (Upness)
#% required: no
#% answer: 0.3
#% end

#%option
#% key: t_vf
#% description: Threshold (t) for transformation of Valley Bottom Flatness
#% required: no
#% answer: 0.3
#% end

#%option
#% key: t_rf
#% description: Threshold (t) for transformation of Ridge Top Flatness
#% required: no
#% answer: 0.35
#% end

#%option
#% key: p_slope
#% description: Shape Parameter (p) for Slope
#% required: no
#% answer: 4
#% end

#%option
#% key: p_pctl
#% description: Shape Parameter (p) for Elevation Percentile
#% required: no
#% answer: 3
#% end

#%option
#% key: min_cells
#% description: Minimum number of cells in generalized DEM
#% required: no
#% answer: 1
#% end

#%flag
#% key: s
#% description: Use square moving window instead of circular moving window
#%end


from grass.pygrass.gis.region import Region
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
import sys
import os
import grass.script as grass
import math
import atexit
import random
import string

if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def cleanup():
    grass.message("Deleting intermediate files...")

    for k, v in TMP_RAST.items():
        for f in v:
            if len(grass.find_file(f)['fullname']) > 0:
                grass.run_command(
                    "g.remove", type="raster", name=f, flags="f", quiet=True)
    
    Region.write(current_region)


def cell_padding(input, output, radius=3):
    """Mitigates edge effect by growing an input raster map by radius cells

    Args
    ----
    input, output : str
        Names of GRASS raster map for input, and padded output
    radius : int
        Radius in which to expand region and grow raster
    
    Returns
    -------
    input_grown : str
        GRASS raster map which has been expanded by radius cells"""
    
    region = Region()

    g.region(n=region.north + (region.nsres * radius),
             s=region.south - (region.nsres * radius),
             w=region.west - (region.ewres * radius),
             e=region.east + (region.ewres * radius))

    r.grow(input=input,
           output=output,
           radius=radius+1,
           quiet=True)

    return (region)


def focal_expr(radius, window_square=False):
    """Returns array offsets relative to centre pixel (0,0) for a matrix of
    size radius

    Args
    ----
    radius : int
        Radius of the focal function
    window_square : bool. Optional (default is False)
        Boolean to use a circular or square window

    Returns
    -------
    offsets : list
        List of pixel positions (row, col) relative to the center pixel
        ( 1, -1)  ( 1, 0)  ( 1, 1)
        ( 0, -1)  ( 0, 0)  ( 0, 1)
        (-1, -1)  (-1, 0)  (-1, 1)"""

    offsets = []

    # generate a list of spatial neighbourhood offsets for the chosen radius
    # ignoring the centre cell
    if window_square:
        
        for i in range(-radius, radius+1):
            for j in range(-radius, radius+1):
                if (i,j) != (0,0):
                    offsets.append((i, j))
    
    else:

        for i in range(-radius, radius+1):
            for j in range(-radius, radius+1):
                row = i + radius
                col = j + radius

                if pow(row - radius, 2) + pow(col - radius, 2) <= \
                    pow(radius, 2) and (i, j) != (0,0):
                    offsets.append((j, i))

    return offsets


def get_percentile(L, input, radius=3, window_square=False):
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

    PCTL = "PCTL{L}".format(L=L+1)
    TMP_RAST[L].append(PCTL)
    input_grown=input
    
    # get offsets for given neighborhood radius
    offsets = focal_expr(radius=radius, window_square=window_square)
    
    # generate grass mapcalc terms and execute
    n_pixels = float(len(offsets))

    # create mapcalc expr
    # if pixel in neighborhood contains nodata, attempt to use opposite neighbor
    # if opposite neighbor is also nodata, then use center pixel
    terms = []
    for d in offsets:
        valid = ','.join(map(str, d))        
        invalid = ','.join([str(-d[0]), str(-d[1])])
        terms.append("if(isnull({input}[{d}]), if(isnull({input}[{e}]), 1, {input}[{e}]<={input}), {input}[{d}]<={input})".format(
            input=input_grown, d=valid, e=invalid))

    expr = "{x} = ({s}) / {n}".format(x=PCTL, s=" + ".join(terms), n=n_pixels)
    grass.mapcalc(expr)

    return(PCTL)


def get_slope(L, elevation):

    region = Region()

    slope = 'tmp_slope_step{L}'.format(L=L+1) + \
        ''.join([random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST[L].append(slope)

    slope_expr = """{s} = 100 * (sqrt( \
    ((if(isnull({a}[0,-1]), {a}[0,0], {a}[0,-1]) - if(isnull({a}[0, 1]), {a}[0,0], {a}[0, 1])) / (2*{ewres}))^2 + \
     ((if(isnull({a}[-1,0]), {a}[0,0], {a}[-1,0]) - if( isnull({a}[1, 0]), {a}[0,0], {a}[1, 0])) / (2*{nsres}))^2)) \
     """.format(
        s=slope, a=elevation, nsres=region.nsres, ewres=region.ewres)

    grass.mapcalc(slope_expr)

    return (slope)


def get_flatness(L, slope, t, p):
    """Calculates the flatness index
    Flatness F1 = 1 / (1 + pow ((slope / t), p)
    
    Equation 2 (Gallant and Dowling, 2003)"""

    F = "tmp_F{L}".format(L=L+1) + \
        ''.join([random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST[L].append(F)
    grass.mapcalc("$g = 1.0 / (1.0 + pow(($x / $t), $p))", 
                   g=F, x=slope, t=t, p=p)
    
    return F


def get_prelim_flatness(L, F, PCTL, t, p):
    """Transform elevation percentile to a local lowness value using
    equation (1) and combined with flatness F to produce the preliminary
    valley flatness index (PVF) for the first step.
    
    Equation 3 (Gallant and Dowling, 2003)"""
    
    PVF = "tmp_PVF{L}".format(L=L+1) + \
        ''.join([random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST[L].append(PVF)

    grass.mapcalc("$g = $a * (1.0 / (1.0 + pow(($x / $t), $p)))",
                    g=PVF, a=F, x=PCTL, t=t, p=p)
    
    return PVF


def get_prelim_flatness_rf(L, F, PCTL, t, p):
    """Transform elevation percentile to a local upness value using
    equation (1) and combined with flatness to produce the preliminary
    valley flatness index (PVF) for the first step
    
    Equation 3 (Gallant and Dowling, 2003)"""
    
    PVF = "tmp_PVF{L}".format(L=L+1) + \
        ''.join([random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST[L].append(PVF)

    grass.mapcalc("$g = $a * (1.0 / (1.0 + pow(((1-$x) / $t), $p)))",
                    g=PVF, a=F, x=PCTL, t=t, p=p)
    
    return PVF


def get_valley_flatness(L, PVF, t, p):
    """Calculation of the valley flatness step VF
    Larger values of VF1 indicate increasing valley bottom character
    with values less than 0.5 considered not to be in valley bottoms

    Equation 4 (Gallant and Dowling, 2003)"""

    VF = "tmp_VF{L}".format(L=L+1) + \
        ''.join([random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST[L].append(VF)
    grass.mapcalc("$g = 1 - (1.0 / (1.0 + pow(($x / $t), $p)))",
                  g=VF, x=PVF, t=t, p=p)
    
    return VF


def get_mrvbf(L, VF_Lminus1, VF_L, t):
    """Calculation of the MRVBF index
    Requires that L>1"""

    W = "tmp_W{L}".format(L=L+1) + \
        ''.join([random.choice(string.ascii_letters + string.digits) for n in range(4)])
    MRVBF = "MRVBF{L}".format(L=L+1) + \
        ''.join([random.choice(string.ascii_letters + string.digits) for n in range(4)])

    # Calculation of weight W2 (Equation 9)
    TMP_RAST[L].append(W)
    p = (math.log10(((L+1) - 0.5) / 0.1)) / math.log10(1.5)
    grass.mapcalc("$g = 1 - (1.0 / (1.0 + pow(($x / $t), $p)))",
                  g=W, x=VF_L, t=t, p=p)

    # Calculation of MRVBF2	(Equation 8)
    TMP_RAST[L].append(MRVBF)
    grass.mapcalc("$MBF = ($W * ($L + $VF)) + ((1 - $W) * $VF1)",
                  MBF=MRVBF, L=L, W=W, VF=VF_L, VF1=VF_Lminus1)
                
    return MRVBF


def get_combined_flatness(L, F1, F2):
    """Calculates the combined flatness index
    
    Equation 13 (Gallant and Dowling, 2003)"""

    CF = "tmp_CF{L}".format(L=L+1) + \
        ''.join([random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST[L].append(CF)
    grass.mapcalc("$CF = $F1 * $F2", CF=CF, F1=F1, F2=F2)

    return CF


def get_smoothed_dem(L, DEM):
    """Smooth the DEM using an 11 cell averaging filter with gauss weighting of 3 radius"""
    
    smoothed = "tmp_DEM_smoothed_step{L}".format(L=L+1) + \
        ''.join([random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST[L].append(smoothed)

    # g = 4.3565 * math.exp(-(3 / 3.0))
    r.neighbors(input=DEM, output=smoothed, size=11, gauss=3)
    
    return smoothed


def refine(L, input, region, method='bilinear'):
    """change resolution back to base resolution and resample a raster"""
    
    input_padded = '_'.join(['tmp', input, '_padded']) + \
        ''.join([random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST[L].append(input_padded)
    cell_padding(input=input, output=input_padded, radius=2)
    
    Region.write(region)
    input = '_'.join(['tmp', input, 'refined_base_resolution']) + \
        ''.join([random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST[L].append(input)

    if method == 'bilinear':
       r.resamp_interp(input=input_padded, 
                       output=input,
                       method="bilinear")

    if method == 'average':
        r.resamp_stats(input=input_padded,
                       output=input,
                       method='average',
                       flags='w')
    
    return input


def main():
    r_elevation = options['elevation']
    mrvbf = options['mrvbf'].split('@')[0]
    mrrtf = options['mrrtf'].split('@')[0]
    t_slope = float(options['t_slope'])
    t_pctl_v = float(options['t_pctl_v'])
    t_pctl_r = float(options['t_pctl_r'])
    t_vf = float(options['t_rf'])
    t_rf = float(options['t_rf'])
    p_slope = float(options['p_slope'])
    p_pctl = float(options['p_pctl'])
    moving_window_square = flags['s']
    min_cells = int(options['min_cells'])

    global current_region
    global TMP_RAST
    TMP_RAST = {}
    current_region = Region()

    # Some checks
    if t_slope <= 0 or t_pctl_v <= 0 or t_pctl_r <= 0 or t_vf <= 0 or t_rf <= 0 or \
        p_slope <= 0 or p_pctl <= 0:
        grass.fatal('Parameter values cannot be <= 0')

    if min_cells < 1:
        grass.fatal('Minimum number of cells in generalized DEM cannot be less than 1')

    if min_cells > current_region.cells:
        grass.fatal('Minimum number of cells in the generalized DEM cannot exceed the ungeneralized number of cells')

    ###########################################################################
    # Calculate number of levels

    levels = math.ceil(-math.log(float(min_cells)/current_region.cells) / math.log(3) - 2)
    levels = int(levels)

    if levels < 3:
        grass.fatal('MRVBF algorithm requires a greater level of generalization. Reduce number of min_cells')

    grass.message('Parameter Settings')
    grass.message('------------------')
    grass.message('min_cells = %d will result in %d generalization steps' % (min_cells, levels))

    TMP_RAST = {k: [] for k in range(levels)}

    ###########################################################################
    # Intermediate outputs
    Xres_step, Yres_step, DEM = [], [], []
    slope, F, PCTL, PVF, PVF_RF = [0]*levels, [0]*levels, [0]*levels, [0]*levels, [0]*levels
    VF, VF_RF, MRVBF, MRRTF = [0]*levels, [0]*levels, [0]*levels, [0]*levels

    ###########################################################################
    # Step 1 (L=0)
    # Base scale resolution
    L = 0
    Xres_step.append(current_region.ewres)
    Yres_step.append(current_region.nsres)
    DEM.append(r_elevation)
    radi = 3

    g.message(os.linesep)
    g.message("Step {L}".format(L=L+1))
    g.message("------")

    # Calculation of slope (S1) and calculation of flatness (F1) (Equation 2)
    grass.message("Calculation of slope and transformation to flatness F{L}...".format(L=L+1))
    slope[L] = get_slope(L, DEM[L])
    F[L] = get_flatness(L, slope[L], t_slope, p_slope)

    # Calculation of elevation percentile PCTL for step 1
    grass.message("Calculation of elevation percentile PCTL{L}...".format(L=L+1))
    PCTL[L] = get_percentile(L, DEM[L], radi, moving_window_square)

    # Transform elevation percentile to local lowness for step 1 (Equation 3)
    grass.message("Calculation of preliminary valley flatness index PVF{L}...".format(L=L+1))
    PVF[L] = get_prelim_flatness(L, F[L], PCTL[L], t_pctl_v, p_pctl)
    if mrrtf != '':
        grass.message("Calculation of preliminary ridge top flatness index PRF{L}...".format(L=L+1))
        PVF_RF[L] = get_prelim_flatness_rf(L, F[L], PCTL[L], t_pctl_r, p_pctl)

    # Calculation of the valley flatness step 1 VF1 (Equation 4)
    grass.message("Calculation of valley flatness VF{L}...".format(L=L+1))
    VF[L] = get_valley_flatness(L, PVF[L], t_vf, p_slope)
    if mrrtf != '':
        grass.message("Calculation of ridge top flatness RF{L}...".format(L=L+1))
        VF_RF[L] = get_valley_flatness(L, PVF_RF[L], t_rf, p_slope)

    ##################################################################################
    # Step 2 (L=1)
    # Base scale resolution
    L = 1
    Xres_step.append(current_region.ewres)
    Yres_step.append(current_region.nsres)
    DEM.append(r_elevation)
    t_slope /= 2.0
    radi = 6

    grass.message(os.linesep)
    grass.message("Step {L}".format(L=L+1))
    grass.message("------")

    # Calculation of flatness for step 2 (Equation 5)
    # The second step commences the same way with the original DEM at its base resolution,
    # using a slope threshold ts,2 half of ts,1:
    grass.message("Calculation of flatness F{L}...".format(L=L+1))
    F[L] = get_flatness(L, slope[L-1], t_slope, p_slope)

    # Calculation of elevation percentile PCTL for step 2 (radius of 6 cells)
    grass.message("Calculation of elevation percentile PCTL{L}...".format(L=L+1))
    PCTL[L] = get_percentile(L, r_elevation, radi, moving_window_square)

    # PVF for step 2 (Equation 6)
    grass.message("Calculation of preliminary valley flatness index PVF{L}...".format(L=L+1))
    PVF[L] = get_prelim_flatness(L, F[L], PCTL[L], t_pctl_v, p_pctl)
    if mrrtf != '':
        grass.message("Calculation of preliminary ridge top flatness index PRF{L}...".format(L=L+1))
        PVF_RF[L] = get_prelim_flatness_rf(L, F[L], PCTL[L], t_pctl_r, p_pctl)
    
    # Calculation of the valley flatness VF for step 2 (Equation 7)
    grass.message("Calculation of valley flatness VF{L}...".format(L=L+1))
    VF[L] = get_valley_flatness(L, PVF[L], t_vf, p_slope)
    if mrrtf != '':
        grass.message("Calculation of ridge top flatness RF{L}...".format(L=L+1))
        VF_RF[L] = get_valley_flatness(L, PVF_RF[L], t_rf, p_slope)
            
    # Calculation of MRVBF for step 2
    grass.message("Calculation of MRVBF{L}...".format(L=L+1))
    MRVBF[L] = get_mrvbf(L, VF_Lminus1=VF[L-1], VF_L=VF[L], t=t_pctl_v)
    if mrrtf != '':
        grass.message("Calculation of MRRTF{L}...".format(L=L+1))
        MRRTF[L] = get_mrvbf(L, VF_Lminus1=VF_RF[L-1], VF_L=VF_RF[L], t=t_pctl_r)

    # Update flatness for step 2 with combined flatness from F1 and F2 (Equation 10)
    grass.message("Calculation  of combined flatness index CF{L}...".format(L=L+1))
    F[L] = get_combined_flatness(L, F[L-1], F[L])

    ##################################################################################
    # Remaining steps
    # DEM_1_1 refers to scale (smoothing) and resolution (cell size)
    # so that DEM_L1_L-1 refers to smoothing of current step,
    # but resolution of previous step 

    for L in range(2, levels):

        t_slope /= 2.0
        Xres_step.append(Xres_step[L-1] * 3)
        Yres_step.append(Yres_step[L-1] * 3)
        radi = 6

        # delete temporary maps from L-2
        for tmap in TMP_RAST[L-2]:
            g.remove(type='raster', name=tmap, flags='f', quiet=True)

        grass.message(os.linesep)
        grass.message("Step {L}".format(L=L+1))
        grass.message("------")
        
        # Coarsen resolution to resolution of prevous step (step L-1) and smooth DEM
        if L >= 3:
            grass.run_command('g.region', ewres = Xres_step[L-1], nsres = Yres_step[L-1])
            grass.message('Coarsening resolution to ew_res={e} and ns_res={n}...'.format(
                e=Xres_step[L-1], n=Yres_step[L-1]))
        
        grass.message("DEM smoothing 11 x 11 windows with Gaussian smoothing kernel (sigma) 3...")
        DEM.append(get_smoothed_dem(L, DEM[L-1]))

        # Calculate slope
        grass.message("Calculation of slope...")
        slope[L] = get_slope(L, DEM[L])

        # Refine slope to base resolution
        if L >= 3:
            grass.message('Resampling slope back to base resolution...')
            slope[L] = refine(L, slope[L], current_region, method='bilinear')

        # Coarsen resolution to current step L and calculate PCTL
        grass.run_command('g.region', ewres=Xres_step[L], nsres=Yres_step[L])
        DEM[L] = refine(L, DEM[L], Region(), method = 'average')
        grass.message("Calculation of elevation percentile PCTL{L}...".format(L=L+1))
        PCTL[L] = get_percentile(L, DEM[L], radi, moving_window_square)
        
        # Refine PCTL to base resolution
        grass.message("Resampling PCTL{L} to base resolution...".format(L=L+1))
        PCTL[L] = refine(L, PCTL[L], current_region, method='bilinear')

        # Calculate flatness F at the base resolution
        grass.message("Calculate F{L} at base resolution...".format(L=L+1))
        F[L] = get_flatness(L, slope[L], t_slope, p_slope)

        # Update flatness with combined flatness CF from the previous step
        grass.message("Calculate combined flatness CF{L} at base resolution...".format(L=L+1))
        F[L] = get_combined_flatness(L, F1=F[L-1], F2=F[L])

        # Calculate preliminary valley flatness index PVF at the base resolution
        grass.message("Calculate preliminary valley flatness index PVF{L} at base resolution...".format(L=L+1))
        PVF[L] = get_prelim_flatness(L, F[L], PCTL[L], t_pctl_v, p_pctl)
        if mrrtf != '':
            grass.message("Calculate preliminary ridge top flatness index PRF{L} at base resolution...".format(L=L+1))
            PVF_RF[L] = get_prelim_flatness_rf(L, F[L], PCTL[L], t_pctl_r, p_pctl)
        
        # Calculate valley flatness index VF
        grass.message("Calculate valley flatness index VF{L} at base resolution...".format(L=L+1))
        VF[L] = get_valley_flatness(L, PVF[L], t_vf, p_slope)
        if mrrtf != '':
            grass.message("Calculate ridge top flatness index RF{L} at base resolution...".format(L=L+1))
            VF_RF[L] = get_valley_flatness(L, PVF_RF[L], t_rf, p_slope)
            
        # Calculation of MRVBF
        grass.message("Calculation of MRVBF{L}...".format(L=L+1))
        MRVBF[L] = get_mrvbf(L, VF_Lminus1=MRVBF[L-1], VF_L=VF[L], t=t_pctl_v)
        if mrrtf != '':
            grass.message("Calculation of MRRTF{L}...".format(L=L+1))
            MRRTF[L] = get_mrvbf(L, VF_Lminus1=MRRTF[L-1], VF_L=VF_RF[L], t=t_pctl_r)

    # Output final MRVBF
    grass.mapcalc("$x = $y", x = mrvbf, y=MRVBF[L])

    if mrrtf != '':
        grass.mapcalc("$x = $y", x = mrrtf, y=MRRTF[L])

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
