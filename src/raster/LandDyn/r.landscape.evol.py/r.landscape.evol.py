#!/usr/bin/python

############################################################################
#
# MODULE:       r.landscape.evol.py
# AUTHOR(S):    Isaac Ullah and Michael Barton
# COPYRIGHT:    (C) 2012 GRASS Development Team/Isaac Ullah
#
#  description: Simulates the cumulative effect of erosion and deposition on a landscape over time. This module uses appropriate flow on different landforms by default; however, singular flow regimes can be chosen by manipulating the cutoff points. This module requires GRASS 6.4 or greater. THIS SCRIPT WILL PRODUCE MANY TEMPORARY MAPS AND REQUIRES A LOT OF FREE FILE SPACE! 

#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#############################################################################/
#%Module
#% description: Simulates the cumulative effect of erosion and deposition on a landscape over time. This module uses appropriate flow on different landforms by default; however, singular flow regimes can be chosen by manipulating the cutoff points. This module requires GRASS 6.4 or greater. THIS SCRIPT WILL PRODUCE MANY TEMPORARY MAPS AND REQUIRES A LOT OF FREE FILE SPACE! 
#%End
#%option
#% key: elev
#% type: string
#% gisprompt: old,cell,raster
#% description: Input elevation map (DEM of surface)
#% required : yes
#%end
#%option
#% key: initbdrk
#% type: string
#% gisprompt: old,cell,raster
#% description: Bedrock elevations map (DEM of bedrock)
#% answer: 
#% required : yes
#%end
#%option
#% key: K
#% type: string
#% gisprompt: old,cell,raster
#% description: Soil erodability index (K factor) map or constant
#% answer: 0.42
#% required : yes
#%end
#%option
#% key: sdensity
#% type: string
#% gisprompt: old,cell,raster
#% description: Soil density map or constant [T/m3] for conversion from mass to volume
#% answer: 1.2184
#% required : yes
#%end
#%option
#% key: Kt
#% type: double
#% description: Stream transport efficiency variable (0.001 for a soft substrate, 0.0001 for a normal substrate, 0.00001 for a hard substrate, 0.000001 for a very hard substrate)
#% answer: 0.0001
#% options: 0.001,0.0001,0.00001,0.000001
#% required : yes
#%end
#%option
#% key: loadexp
#% type: double
#% description: Stream transport type variable (1.5 for mainly bedload transport, 2.5 for mainly suspended load transport)
#% answer: 1.5
#% options: 1.5,2.5
#% required : yes
#%end
#%option
#% key: kappa
#% type: double
#% description: Hillslope diffusion (Kappa) rate map or constant [m/kyr]
#% answer: 1
#% required : yes
#%end
#%option
#% key: C
#% type: string
#% gisprompt: old,cell,raster
#% description: Landcover index (C factor) map or constant
#% answer: 0.005
#% required : yes
#%end
#%option
#% key: rain
#% type: string
#% gisprompt: old,cell,raster
#% description: Precip totals for the average storm [mm]
#% answer: 20.61
#% required : yes
#%end
#%option
#% key: R
#% type: string
#% description: Rainfall (R factor) constant (AVERAGE FOR WHOLE MAP AREA)
#% answer: 4.54
#% required : yes
#%end
#%option
#% key: storms
#% type: integer
#% description: Number of storms per year (integer)
#% answer: 25
#% required : yes
#%end
#%option
#% key: stormlength
#% type: double
#% description: Average length of the storm [h]
#% answer: 24.0
#% required : yes
#%end
#%option
#% key: speed
#% type: double
#% description: Average velocity of flowing water in the drainage [m/s]
#% answer: 1.4
#% required : yes
#%end
#%option
#% key: cutoff1
#% type: double
#% description: Flow accumulation breakpoint value for shift from diffusion to overland flow
#% answer: 0.65
#% required : yes
#%end
#%option
#% key: cutoff2
#% type: double
#% description: Flow accumulation breakpoint value for shift from overland flow to rill/gully flow (if value is the same as cutoff1, no sheetwash procesess will be modeled)
#% answer: 2.25
#% required : yes
#%end
#%option
#% key: cutoff3
#% type: double
#% description: Flow accumulation breakpoint value for shift from rill/gully flow to stream flow (if value is the same as cutoff2, no rill procesess will be modeled)
#% answer: 7
#% required : yes
#%end
#%option
#% key: smoothing
#% type: string
#% description: Amount of additional smoothing (answer "no" unless you notice large spikes in the erdep rate map)
#% answer: no
#% options: no,low,high
#% required : yes
#%end
#%option
#% key: prefx
#% type: string
#% description: Prefix for all output maps
#% answer: levol_
#% required : yes
#%end
#%option
#% key: outdem
#% type: string
#% description: Name stem for output elevation map(s) (preceded by prefix and followed by numerical suffix if more than one iteration)
#% answer: elevation
#% required: yes
#%end
#%option
#% key: outsoil
#% type: string
#% description: Name stem for the output soil depth map(s) (preceded by prefix and followed by numerical suffix if more than one iteration)
#% answer: soildepth
#% required: yes
#%end
#%option
#% key: number
#% type: integer
#% description: Number of iterations (cycles) to run
#% answer: 1
#% required : yes
#%end


# #%option
# #% key: alpha                 ###This may be added back in if I can find a good equation for mass movement
# #% type: integer
# #% description: Critical slope threshold for mass movement of sediment (in degrees above horizontal)
# #% answer: 40
# #% required : yes
# #%end

#%flag
#% key: p
#% description: -p Output a vector points map with sampled values of flow accumulation and curvatures suitable for determining cutoff values. NOTE: Overrides all other output options, and exits after completion. The output vector points map will be named  "PREFIX_#_randomly_sampled_points".
#% guisection: Optional
#%end
#%flag
#% key: 1
#% description: -1 Calculate streams as 1D difference instead of 2D divergence (forces heavy incision in streams)
#% guisection: Optional
#%end
#%flag
#% key: k
#% description: -k Keep ALL temporary maps (overides flags -drst). This will make A LOT of maps!
#% guisection: Optional
#%end
#%flag
#% key: d
#% description: -d Don't output yearly soil depth maps
#% guisection: Optional
#%end
#%flag
#% key: r
#% description: -r Don't output yearly maps of the erosion/deposition rates ("ED_rate" map, in vertical meters)
#% guisection: Optional
#%end
#%flag
#% key: s
#% description: -s Keep all slope maps 
#% guisection: Optional
#%end
#%flag
#% key: t
#% description: -t Keep yearly maps of the Transport Capacity at each cell ("Qs" maps)
#% guisection: Optional
#%end
#%flag
#% key: e
#% description: -e Keep yearly maps of the Excess Transport Capacity (divergence) at each cell ("DeltaQs" maps)
#% guisection: Optional
#%end
#%Option
#% key: statsout
#% type: string
#% description: Name for the statsout text file (optional, if none provided, a default name will be used)
#% required: no
#% guisection: Optional
#%end

import sys
import os
import subprocess
import math
import random
import tempfile
grass_install_tree = os.getenv('GISBASE')
sys.path.append(grass_install_tree + os.sep + 'etc' + os.sep + 'python')
import grass.script as grass

# First define two useful custom methods that we will need later on
# m is a grass/bash command that will generate some info to stdout. You must invoke this command in the form of "variable to be made" = out2var('command')
def out2var(m):
    pn = subprocess.Popen('%s' % m, stdout=subprocess.PIPE, shell='bash')
    return pn.stdout.read()

# Now define  "main",  our main block of code, here defined because of the way g.parser needs to be called with python codes for grass (see below)        
# m = last iteration number, o = iteration number, p = prefx, q = statsout, r = resolution of input elev map
def main(m, o, p, q, r):
    # Get variables from user input
    years = os.getenv("GIS_OPT_number")
    initbdrk = os.getenv("GIS_OPT_initbdrk")
    outdem = os.getenv("GIS_OPT_outdem")
    outsoil = os.getenv("GIS_OPT_outsoil")
    R = os.getenv("GIS_OPT_R")
    K = os.getenv("GIS_OPT_K")
    sdensity = os.getenv("GIS_OPT_sdensity")
    C = os.getenv("GIS_OPT_C")
    kappa = os.getenv("GIS_OPT_kappa")
    cutoff1 = os.getenv("GIS_OPT_cutoff1")
    cutoff2 = os.getenv("GIS_OPT_cutoff2")
    cutoff3 = os.getenv("GIS_OPT_cutoff3")
    rain = os.getenv("GIS_OPT_rain")
    storms = os.getenv("GIS_OPT_storms")
    stormlengthsecs = float(os.getenv("GIS_OPT_stormlength"))*3600.00                  # number of seconds in the storm
    stormtimet = stormlengthsecs / (float(os.getenv("GIS_OPT_speed")) * float(r))       # number of hydrologic instants in the storm
    timet = stormlengthsecs/stormtimet                                                                      # length of a single hydrologic instant in seconds
    Kt = os.getenv("GIS_OPT_Kt")
    loadexp = os.getenv("GIS_OPT_loadexp")
    # Make some variables for temporary map names
    aspect = '%saspect%04d' % (p, o)
    flowacc = '%sflowacc%04d' % (p, o)
    flacclargenums = flowacc + '_largenums'
    flowdir = '%sflowdir%04d' % (p, o)
    pc = '%spc%04d' % (p, o)
    tc = '%stc%04d' % (p, o)
    meancurv = '%smeancurv%04d' % (p, o)
    rate = '%srate%04d' % (p, o)
    # Make color rules for netchange maps
    nccolors = tempfile.NamedTemporaryFile()
    nccolors.write('100% 0 0 100\n1 blue\n0.5 indigo\n0.01 green\n0 white\n-0.01 yellow\n-0.5 orange\n-1 red\n0% 150 0 50')
    nccolors.flush()
    # Make color rules for soil depth maps
    sdcolors = tempfile.NamedTemporaryFile()
    sdcolors.write('100% 0:249:47\n20% 78:151:211\n6% 194:84:171\n0% 227:174:217')
    sdcolors.flush()
    # If first iteration, use input maps. Otherwise, use maps generated from previous iterations
    if ( o == 1 ):
        old_dem = '%s' % os.getenv("GIS_OPT_elev")
        old_bdrk = '%s' % os.getenv("GIS_OPT_initbdrk")
        old_soil = "%s%s_init" % (prefx, os.getenv("GIS_OPT_outsoil"))
        grass.mapcalc('${old_soil}=${old_dem}-${old_bdrk}', old_soil = old_soil, old_dem = old_dem, old_bdrk = old_bdrk)
    else :
        old_dem = '%s%s%04d' % (p, os.getenv("GIS_OPT_outdem"), m)
        old_bdrk = '%s%s%04d' % (p, os.getenv("GIS_OPT_outbdrk"), m)
        old_soil = '%s%s%04d' % (p, os.getenv("GIS_OPT_outsoil"), m)
    #Checking for special condition of there being only one run, and setting variables accordingly (one year runs have no numbers suffixed to the output map names)
    if ( years == '1' ):
        slope = '%sslope' % p
        qs = '%sQs' % (p)
        netchange = '%sED_rate' % p
        new_dem ='%s%s' % (p, outdem)
        new_soil = '%s%s' % (p, outsoil)
    else:
        slope = '%sslope%04d' % (p, o)
        netchange = '%sED_rate%04d' % (p, o)
        new_dem = '%s%s%04d' % (p, outdem, o)
        new_soil = '%s%s%04d' % (p, outsoil, o)
    if ( os.getenv("GIS_FLAG_p") == "1" ):
        grass.message('1) Calculating slope and curvatures')
        grass.run_command('r.slope.aspect', quiet = True, elevation = old_dem, slope = slope, pcurv = pc, tcurv = tc)
    else:
        grass.message('\n##################################################\n\n*************************\n Year %s -- ' % o + 'step 1: calculating slope\n*************************\n')
        grass.run_command('r.slope.aspect', quiet = True, elevation = old_dem, aspect = aspect, slope = slope)
    if ( os.getenv("GIS_FLAG_p") == "1" ):
        grass.message('2) Calculating map of rainfall excess')
    else:
        grass.message('\n*************************\n Year %s -- ' % o + 'step 2: calculating accumulated flow depths\n*************************\n')       
        grass.message('Calculating runoff excess rates (scaled uplsope accumulated cells)')
    rainexcess = "%s_rainfall_excess_map_%04d"% (p, o)

    #to calculate rainfall excess, we are making a linear regression of C factor and the percentage of water that will leave the cell. A c-factor of 0.005 (mature woodland) will only allow 10% of the water to exit the cell, whereas a c-factor of 0.1 (bareland) will allow 98% of the water to leave the cell. Note that we multiply this by 100 because r.watershed will only allow integer amounts as input in it's 'flow' variable, and we want to maintain the accuracy. The large number flow accumulation will be divided by 100 after it is made, which brings the values back down to what they should be.
    grass.mapcalc('${rainexcess}=int(100 * ((9.26316 * ${C}) + 0.05368))', rainexcess = rainexcess, C = C)
    if ( os.getenv("GIS_FLAG_p") == "1" ):
        grass.message('3) Calculating accumulated flow (in numbers of upslope cells, scaled by runoff contribution')
    grass.message('Calculating overland flow accumulation per cell (total vertical depth of water that passes over each cell in one storm)')
    try:
        grass.run_command('r.watershed', quiet = True, flags = 'fa', elevation = old_dem, flow = rainexcess, accumulation = flacclargenums, drainage = flowdir, convergence = '5')
    except:
        grass.run_command('r.watershed', quiet = True, flags = 'a', elevation = old_dem, flow = rainexcess, accumulation = flacclargenums, drainage = flowdir, convergence = '5')
    grass.mapcalc('${flowacc}=${flacclargenums}/100', flowacc = flowacc, flacclargenums = flacclargenums)
    if ( os.getenv("GIS_FLAG_k") == "1" ):
        pass
    else:
        grass.run_command('g.remove', quiet = True, rast = rainexcess + "," + flacclargenums)
    if ( os.getenv("GIS_FLAG_p") == "1" ):
        grass.message('4) Determining number of sampling points using formula: "ln(#cells_in_input_map)*100"')
        flaccstats = grass.parse_command('r.univar', flags = 'g', map = flowacc)
        numpts = int(math.log(int(flaccstats['n']))*100)
        grass.message('5) Creating random points and sampling values of flow accumulation, curvatures, and slope.')
        vout = '%s%s_randomly_sampled_points' % (p, numpts)
        grass.run_command('r.random', quiet = True, input = flowacc, cover = pc, n = numpts, vector_output = vout)
        grass.run_command('v.db.renamecol', quiet = True, map = vout, column = 'value,Flow_acc')
        grass.run_command('v.db.renamecol', quiet = True, map = vout, column = 'covervalue,Princ_curv')
        grass.run_command('v.db.addcol', quiet = True, map = vout, columns = 'Tang_curv double precision, Slope double precision')
        grass.run_command('v.what.rast', quiet = True, vector = vout, raster = tc, column = "Tang_curv")
        grass.run_command('v.what.rast', quiet = True, vector = vout, raster = slope, column = "Slope")
        if ( os.getenv("GIS_FLAG_k") == "1" ):
            grass.message('--Keeping the created maps (Flow Accumulation, Slope, Principle Curvature, Tangential Curvature)')
        else:
            grass.message('6) Cleaning up...')
            grass.run_command('g.remove', quiet = True, rast = slope + "," + pc + "," + tc + "," + flowacc)
        grass.message('FINISHED. \nRandom sample points map "%s" created successfully.\n' % vout)
        sys.exit(0)
    grass.message('\n*************************\n Year %s -- ' % o + 'step 3: calculating sediment transport rates (units variable depending upon process) \n*************************\n')  
    # This step calculates the force of the flowing water at every cell on the landscape using the proper transport process law for the specific point in the flow regime. For upper hillslopes (below cutoff point 1) this done by multiplying the diffusion coeficient by the accumulated flow/cell res width. For midslopes (between cutoff 1 and 2) this is done by multiplying slope by accumulated flow with the m and n exponents set to 1. For channel catchment heads (between cutoff 2 and 3), this is done by multiplying slope by accumulated flow with the m and n exponents set to 1.6 and 1.3 respectively. For Channelized flow in streams (above cutoff 3), this is done by calculating the reach average shear stress (hydraulic radius [here estimated for a cellular landscape simply as the depth of flow]  times  slope times accumulated flow [cells] times gravitatiopnal acceleration of water [9806.65 newtons], all raised to the appropriate exponant for the type of transport (bedload or suspended load), and then divided by the resolution. Depth of flow is calculated as a mean "instantaneous depth" during any given rain event, here estimated by the maximum depth of an idealized unit hydrograph with base equal to the duration of the storm, and area equal to the total accumulated excess rainfall during the storm. Then finally calculates the stream power or sediment carrying capacity (qs) of the water flowing at each part of the map by multiplying the reach average shear stress (channelized flow in streams) or the estimated flow force (overland flow) by the transport coeficient (estimated by R*K*C for hillslopes or kt for streams). This is a "Transport Limited" equation, however, we add some constraints on detachment by checking to see if the sediment supply has been exhausted: if the current soil depth is 0 or negative (checking for a negative value is kind of an error trap) then we make the transport coefficient small (0.000001) to simulate erosion on bedrock. Because diffusion and USPED require 2D divergence later on, we calculate these as vectors in the X and Y directions. Stream flow only needs 1D difference, so it's calulated in the direction of flow.

    qsx4 = '%sQsx_diffusion%04d' % (p, o)
    qsy4 = '%sQsy_diffusion%04d' % (p, o)
    grass.mapcalc('${qsx4}=(${kappa} * sin(${slope}) * cos(${aspect}))', qsx4 = qsx4, kappa = kappa, slope = slope, aspect = aspect)
    grass.mapcalc('${qsy4}=(${kappa} * sin(${slope}) * sin(${aspect}))', qsy4 = qsy4, kappa = kappa, slope = slope, aspect = aspect)
    if cutoff1 == cutoff2:
        qsx3 = qsx4
        qsy3 = qsy4
    else:
        qsx3 = '%sQsx_sheetwash%04d' % (p, o)
        qsy3 = '%sQsy_sheetwash%04d' % (p, o)
        grass.mapcalc('${qsx3}=( (${R}*${K}*${C}*${flowacc}*${res}*sin(${slope})) * cos(${aspect}) )', qsx3 = qsx3, R = R, K = K, C =C, slope = slope, res = r, flowacc = flowacc, aspect = aspect, sdensity = sdensity)
        grass.mapcalc('${qsy3}=( (${R}*${K}*${C}*${flowacc}*${res}*sin(${slope})) * sin(${aspect}) )', qsy3 = qsy3, R = R, K = K, C =C, slope = slope, res = r, flowacc = flowacc, aspect = aspect, sdensity = sdensity)
    if cutoff2 == cutoff3:
        qsx2 = qsx3
        qsy2 = qsy3
    else:
        qsx2 = '%sQsx_rills%04d' % (p, o)
        qsy2 = '%sQsy_rills%04d' % (p, o)
        grass.mapcalc('${qsx2}=( (${R}*${K}*${C}*exp((${flowacc}*${res}),1.6000000)*exp(sin(${slope}),1.3000000)) * cos(${aspect}))', qsx2 = qsx2, R = R, K = K, C =C, slope = slope, res = r, flowacc = flowacc, aspect = aspect, sdensity = sdensity)
        grass.mapcalc('${qsy2}=( (${R}*${K}*${C}*exp((${flowacc}*${res}),1.6000000)*exp(sin(${slope}),1.3000000)) * sin(${aspect}))', qsy2 = qsy2, R = R, K = K, C =C, slope = slope, res = r, flowacc = flowacc, aspect = aspect, sdensity = sdensity)
    if ( os.getenv("GIS_FLAG_1") == "1" ):
        #This is the 1D version
        qs1 = '%sQs_1D_streams%04d' % (p, o)
        grass.mapcalc('${qs1}=(${Kt} * exp(9806.65*(((${rain}/1000)*${flowacc})/(0.595*${stormtimet}))*sin(${slope}), ${loadexp}) )', qs1 = qs1, flowacc = flowacc, stormtimet = stormtimet, slope = slope, loadexp = loadexp, Kt = Kt, sdensity = sdensity) 
    else:
        #This is the 2D version
        qsx1 = '%sQsx_streams%04d' % (p, o)
        qsy1 = '%sQsy_streams%04d' % (p, o)
        grass.mapcalc('${qsx1}=(${Kt} * exp(9806.65*(((${rain}/1000)*${flowacc})/(0.595*${stormtimet}))*sin(${slope}), ${loadexp}) ) * cos(${aspect})', qsx1 = qsx1, rain = rain, flowacc = flowacc, stormtimet = stormtimet, slope = slope, loadexp = loadexp, Kt = Kt, sdensity = sdensity, aspect = aspect) 
        grass.mapcalc('${qsy1}=(${Kt} * exp(9806.65*(((${rain}/1000)*${flowacc})/(0.595*${stormtimet}))*sin(${slope}), ${loadexp}) ) * sin(${aspect})', qsy1 = qsy1, rain = rain, flowacc = flowacc, stormtimet = stormtimet, slope = slope, loadexp = loadexp, Kt = Kt, sdensity = sdensity, aspect = aspect)

    grass.message('\n*************************\n Year %s -- ' % o + 'step 4: calculating divergence/difference of sediment transport for each process and the actual amount of erosion or deposition in vertical meters/cell/year\n*************************\n\n')
    #Here is where we figure out the change in transport capacity, and thus the actual amount of erosion an deposition that would occur. There are two ways of doing this. On planar and convex surfaces (i.e., ridgetops, flats, hillslopes), it is better to take the 2D divergence of sediment flux (we use r.slope.aspect to calculate this), but on highly convex surfaces (i.e., in channels) it is better to take the 1D difference between one cell, and the cell that is immediately downstream from it. This all assumes that the system is always operating at Transport Capacity, or if it is not, then is still behaves as if it were (ie., that the actual differences in transported sediment between the cells would be proportional to the system operating at capacity). Thus, under this assumption, the divergence of capacity is equals to actual amount of sediment eroded/deposited.  
    #This is the way we implemnt this: First calculate, we calculate the divergence/differnce for EACH of the different flow processes on the ENTIRE map (i.e., make one map per process, difference for streams, divergence for USPED and diffusion). Then, we cut out the pieces of each of these maps that correspond to the correct landforms from each specific process (based on the user-input cutoffs in flow accumulation), and patch them together into a single map (NOTE: see output unit conversions section below to see how we get all the units to line up during this process). This counters the "boundary effect" that happens when running the differential equations for divergence across the boundary of two different flow processes.  Then we may still have to run a median smoother on the patched map to get rid of any latent spikes.
    qsxdx4 = '%sDelta_Qsx_diffusion%04d' % (p, o)
    qsydy4 = '%sDelta_Qsy_diffusion%04d' % (p, o)
    grass.run_command('r.slope.aspect', quiet = True, elevation = qsx4, dx = qsxdx4)
    grass.run_command('r.slope.aspect', quiet = True, elevation = qsy4, dy = qsydy4)
    if cutoff1 == cutoff2:
        qsxdx3 = qsxdx4
        qsydy3 = qsydy4
    else:
        qsxdx3 = '%sDelta_Qsx_sheetwash%04d' % (p, o)
        qsydy3 = '%sDelta_Qsy_sheetwash%04d' % (p, o)
        grass.run_command('r.slope.aspect', quiet = True, elevation = qsx3, dx = qsxdx3)
        grass.run_command('r.slope.aspect', quiet = True, elevation = qsy3, dy = qsydy3)
    if cutoff2 == cutoff3:
        qsxdx2 = qsxdx3
        qsydy2 = qsydy3
    else:
        qsxdx2 = '%sDelta_Qsx_rills%04d' % (p, o)
        qsydy2 = '%sDelta_Qsy_rills%04d' % (p, o)
        grass.run_command('r.slope.aspect', quiet = True, elevation = qsx2, dx = qsxdx2)
        grass.run_command('r.slope.aspect', quiet = True, elevation = qsy2, dy = qsydy2)
    if ( os.getenv("GIS_FLAG_1") == "1" ):
        #this is the 1D difference for this process
        qsd1 = '%sDelta_Qs_1D_streams%04d' % (p, o)
        grass.mapcalc('${qsd1}=if(${flowdir} == 7, (${qs1}[-1,-1]-${qs1}), if (${flowdir} == 6, (${qs1}[-1,0]-${qs1}), if (${flowdir} == 5, (${qs1}[-1,1]-${qs1}), if (${flowdir} == 4, (${qs1}[0,1]-${qs1}), if (${flowdir} == 3, (${qs1}[1,1]-${qs1}), if (${flowdir} == 2, (${qs1}[1,0]-${qs1}), if (${flowdir} == 1, (${qs1}[1,-1]-${qs1}), if (${flowdir} == 8, (${qs1}[0,-1]-${qs1}), ${qs1}))))))))', qsd1 = qsd1, flowdir = flowdir, qs1 = qs1)
    else:
        #this is the 2D version
        qsxdx1 = '%sDelta_Qsx_streams%04d' % (p, o)
        qsydy1 = '%sDelta_Qsy_streams%04d' % (p, o)
        grass.run_command('r.slope.aspect', quiet = True, elevation = qsx1, dx = qsxdx1)
        grass.run_command('r.slope.aspect', quiet = True, elevation = qsy1, dy = qsydy1)

    #This is the smoothing routine. First we calculate the rate of Erosion and Deposition by converting the Delta QS of the different processes to vertical meters by dividing by the soil denisity (with apropriate constants to get into the correct units, see UNIT CONVERSION note below), and for streams, also expand from the storm to the year level. All units of this initial (temporary) ED_rate map will be in m/cell/year. 
    #OUTPUT UNIT CONVERSIONS: In the case of the diffusion equation, the output units are in verticle meters of sediment per cell per year, so these will be left alone. In the case of stream flow, the output units are kg/m2/storm, so need to multiply by 1000 to get T/m2/storm, and then divide by the soil density (T/m3) to get verticle meters of sediment/cell/storm, and will be multiplied by the number of storms/year in order to get vertical meters of sediment/cell/year. In the case of USPED, the output is in T/Ha/year, so first multiply by 0.1 to get T/m2/year and then divide by soil density (T/m3) to get verticle meters of sediment/cell/year. 
    tempnetchange1 = '%sTEMPORARY_UNSMOOTHED_ED_rate%04d' % (p, o)
    if ( os.getenv("GIS_FLAG_1") == "1" ):
        grass.mapcalc('${tempnetchange1}=if(${flowacc} >= ${cutoff3}, ((${qsd1})/(${sdensity}*1000))*(${storms}*0.25*${stormtimet}), if(${flowacc} >= ${cutoff2} && ${flowacc} < ${cutoff3}, ((${qsxdx2}+${qsydy2})*0.1)/${sdensity}, if(${flowacc} >= ${cutoff1} && ${flowacc} < ${cutoff2}, ((${qsxdx3}+${qsydy3})*0.1)/${sdensity}, ${qsxdx4}+${qsydy4})))', tempnetchange1 = tempnetchange1, qsd1 = qsd1, qsxdx2 = qsxdx2, qsydy2 = qsydy2, qsxdx3 = qsxdx3, qsydy3 = qsydy3, qsxdx4 = qsxdx4, qsydy4 = qsydy4, flowacc = flowacc, cutoff1 = cutoff1, cutoff2 = cutoff2, cutoff3 = cutoff3, sdensity = sdensity, storms = storms, stormtimet = stormtimet)
    else:
        grass.mapcalc('${tempnetchange1}=if(${flowacc} >= ${cutoff3}, ((${qsxdx1} + ${qsydy1})/(${sdensity}*1000))*(${storms}*0.25*${stormtimet}), if(${flowacc} >= ${cutoff2} && ${flowacc} < ${cutoff3}, ((${qsxdx2}+${qsydy2})*0.1)/${sdensity}, if(${flowacc} >= ${cutoff1} && ${flowacc} < ${cutoff2}, ((${qsxdx3}+${qsydy3})*0.1)/${sdensity}, ${qsxdx4}+${qsydy4})))', tempnetchange1 = tempnetchange1, qsxdx1 = qsxdx1, qsydy1 = qsydy1, qsxdx2 = qsxdx2, qsydy2 = qsydy2, qsxdx3 = qsxdx3, qsydy3 = qsydy3, qsxdx4 = qsxdx4, qsydy4 = qsydy4, flowacc = flowacc, cutoff1 = cutoff1, cutoff2 = cutoff2, cutoff3 = cutoff3, sdensity = sdensity, storms = storms, stormtimet = stormtimet)
    #Make some temp maps of just erosion rate and just deposition rate so we can grab some stats from them (If Smoothing is 'no', then we'll also use these stats later in the stats file)
    grass.message('Running soft-knee smoothing filter...')
    tmperosion = p + 'tmperosion%04d' % o
    tmpdep = p + 'tmpdep%04d' % o
    grass.mapcalc('${tmperosion}=if(${tempnetchange1} < -0, ${tempnetchange1}, null())', tmperosion = tmperosion, tempnetchange1 = tempnetchange1)
    grass.mapcalc('${tmpdep}=if(${tempnetchange1} > 0, ${tempnetchange1}, null())', tmpdep = tmpdep, tempnetchange1 = tempnetchange1)
    #Grab the stats from these temp files and save them to dictionaries
    erosstats = grass.parse_command('r.univar', flags = 'ge', percentile = '1', map = tmperosion)
    depostats = grass.parse_command('r.univar', flags = 'ge', percentile = '99', map = tmpdep)
    maximum = depostats['max']
    minimum = erosstats['min']
    erosbreak =  float(erosstats['first_quartile'])
    deposbreak = float(depostats['third_quartile'])
    scalemin = float(erosstats['percentile_1'])
    scalemax = float(depostats['percentile_99'])
    #Use the stats we gathered to do some smoothing with a hi-cut and lo-cut filter (with soft-knee limiting) of the unsmoothed ED_rate map. Values from the 1st quartile of erosion to the minimum (i.e., the very large negative numbers) will be rescaled linearly from the 1st quartile to the 1st percentile value, and values from the 3rd quartile of deposition to the maximum (i.e., the very large positiive numbers) will be rescaled linearly from the 3rd quartile to the 99th percentile value. This brings any values that were really unreasonnable as originally calculated (spikes) into the range of what the maximum values should be on a normally distrubuted dataset, but does so with out a "brick wall" style of limiting, which would make all values above some cutoff equal to a theoretical maximum. By setting both maximum cutoff point AND a "soft" scaling point, this "soft-knee" style of limiting sill retains some of the original scaling at the high ends, which allows for the smoothed value of very high cells to still be relatively higher than values in other cells that were also above the scaling cutoff, but were not originally as high as those very high cells.
    tempnetchange2 = '%stempry_softknee_smth_ED_rate%04d' % (p, o)
    grass.mapcalc('${tempnetchange2}=graph(${tempnetchange1}, ${minimum},${scalemin}, ${erosbreak},${erosbreak}, ${deposbreak},${deposbreak}, ${maximum},${scalemax})', tempnetchange2 = tempnetchange2, tempnetchange1 =tempnetchange1, minimum = minimum, scalemin = scalemin, erosbreak = erosbreak, deposbreak = deposbreak, maximum = maximum, scalemax = scalemax)
    #Check if additional smoothing is requested. 
    if len(os.getenv("GIS_OPT_smoothing")) is 2:
        grass.message('No additional modal smoothing was requested...')
        grass.run_command('g.rename', quiet = True, rast = tempnetchange2 + ',' + netchange)
    elif len(os.getenv("GIS_OPT_smoothing")) is 3:
        grass.message('Enacting additional "low" smoothing: one pass of a 3x3 modal smoothing window.')
        grass.run_command('r.neighbors', quiet = True, input = tempnetchange2, output = netchange, method = 'mode', size = '3')
        grass.run_command('g.remove', quiet = 'True', rast = tempnetchange2)
    elif len(os.getenv("GIS_OPT_smoothing")) is 4:
        grass.message('Enacting additional "high" smoothing: one pass of a 5x5 modal smoothing window.')
        grass.run_command('r.neighbors', quiet = True, input = tempnetchange2, output = netchange, method = 'mode', size = '5')
        grass.run_command('g.remove', quiet = 'True', rast = tempnetchange2)
    else:
        grass.message('There was a problem reading the median-smoothing variable, so maps will not be median-smoothed.')
        grass.run_command('g.rename', quiet = True, rast = tempnetchange2 + ',' + netchange)    
    #Set the netchange map colors to the rules we've provided above
    grass.run_command('r.colors', quiet = True, map = netchange, rules = nccolors.name)
    #Grab the stats from these new smoothed netchange maps and save them to dictionaries (Note that the temporary erosiona nd deposition maps made in this step are overwriting the two temporary maps made for gathering the stats for the soft-knee limiting filter)
    grass.mapcalc('${tmperosion}=if(${netchange} < -0, ${netchange}, null())', tmperosion = tmperosion, netchange = netchange)
    grass.mapcalc('${tmpdep}=if(${netchange} > 0, ${netchange}, null())', tmpdep = tmpdep, netchange = netchange)
    erosstats1 = grass.parse_command('r.univar', flags = 'ge', map = tmperosion)
    depostats1 = grass.parse_command('r.univar', flags = 'ge', map = tmpdep)
    #Clean up temp maps
    grass.run_command('g.remove', quiet = True, rast = tmperosion + ',' + tmpdep + ',' + tempnetchange1)

    grass.message('\n*************************\n Year %s -- ' % o + 'step 5: calculating terrain evolution and new soil depths\n *************************\n\n')
    #Set up a temp dem, and then do initial addition of ED change to old DEM. This mapcalc statement first checks the amount of erodable soil in a given cell against the amount of erosion calculated, and keeps the cell from eroding past this amount (if there is soil, then if the amount of erosion is more than the amount of soil, just remove all the soil and stop, else remove the amount of caclulated erosion. It also runs an error catch that checks to make sure that soil depth is not negative (could happen, I suppose), and if it is, corrects it). 
    temp_dem = '%stemp_dem%04d' % (p, o)
    grass.mapcalc('${temp_dem}=eval(x=if(${old_soil} > 0.0 && (-1*${netchange}) <= ${old_soil}, ${netchange}, if((-1*${netchange}) > ${old_soil},   (-1*${old_soil}), 0)), ${old_dem} + x)', temp_dem = temp_dem, old_soil = old_soil, old_dem = old_dem, netchange = netchange)
    #Do patch-job to catch the shrinking edge problem (the edge cells have no upstream cell, so get turned null in the calculations in step 4)
    grass.run_command('r.patch', quiet = True, input = temp_dem + ',' + old_dem, output= new_dem)
    #Set colors for elevation map to match other dems and then get rid of the temp dem
    grass.run_command('r.colors', quiet = True, map = new_dem, rast = os.getenv("GIS_OPT_elev"))
    grass.run_command('g.remove', quiet = True, rast = temp_dem)
    #calculate the new soildepth map and set colors
    grass.mapcalc('${new_soil}=if ((${new_dem} - ${initbdrk}) < 0, 0, (${new_dem} - ${initbdrk}))', new_soil = new_soil, new_dem = new_dem, initbdrk = initbdrk)
    grass.run_command('r.colors', quiet = True, map = new_soil, rules = sdcolors.name)
    grass.message('\n*************************\n Year %s -- ' % o + 'step 6: writing stats to output file\n *************************\n\n')
    #Finish gathering stats (just need the soil depth stats now)
    soilstats = {}
    soilstats = grass.parse_command('r.univar', flags = 'ge', map = new_soil, percentile = '99')
    #Write stats to a new line in the stats file
    #HEADER of the file should be: "Year,,Mean Erosion,Standard Deviation Erosion,Minimum Erosion,First Quartile Erosion,Median Erosion,Third Quartile Erosion,Maximum Erosion,Original Un-smoothed Maximum Erosion,,Mean Deposition,Standard Deviation Deposition,Minimum Deposition,First Quartile Deposition,Median Deposition,Third Quartile Deposition,Maximum Deposition,Original Un-smoothed Maximum Deposition,,Mean Soil Depth,Standard Deviation Soil Depth,Minimum Soil Depth,First Quartile Soil Depth,Median Soil Depth,Third Quartile Soil Depth,Maximum Soil Depth'
    grass.message('Outputing stats to textfile: ' + q)
    f.write('\n%s' % o + ',,' + erosstats1['mean'] + ',' + erosstats1['stddev'] + ',' + erosstats1['max'] + ',' + erosstats1['third_quartile'] + ',' + erosstats1['median'] + ',' + erosstats1['first_quartile'] + ',' + erosstats1['min'] + ',' + minimum + ',,' + depostats1['mean'] + ',' + depostats1['stddev'] + ',' + depostats1['min'] + ',' + depostats1['first_quartile'] + ',' + depostats1['median'] + ',' + depostats1['third_quartile'] + ',' + depostats1['max'] + ',' + maximum + ',,' + soilstats['mean'] + ',' + soilstats['stddev'] + ',' + soilstats['min'] + ',' + soilstats['first_quartile'] + ',' + soilstats['median'] + ',' + soilstats['third_quartile'] + ',' + soilstats['max'])

    #Clean up temporary maps
    if os.getenv("GIS_FLAG_k") == "1":
        grass.message('\nTemporary maps will NOT be deleted!!!!\n')
    else:
        grass.message('\nCleaning up temporary maps...\n\n')
        if os.getenv("GIS_FLAG_s") == "1":
            grass.message('Keeping Slope map.')
        else:
            grass.run_command('g.remove', quiet =True, rast = slope)
        if os.getenv("GIS_FLAG_d") == "1":
            grass.message('Not keeping Soil Depth map.')
            grass.run_command('g.remove', quiet =True, rast = old_soil)
            #check if this is the last year and remove the "new-soil" map too
            if ( o == int(os.getenv("GIS_OPT_number"))):
                grass.run_command('g.remove', quiet =True, rast = new_soil)
        else:
            #check if this is the first year, and if so, remove the temporary "soildepths_init" map
            if ( o == 1 ):
                grass.run_command('g.remove', quiet = True, rast = old_soil)
        if ( os.getenv("GIS_FLAG_e") == "1" ):
            grass.message('Keeping Excess Transport Capacity (divergence) maps for all processes.')
        else:
            if ( os.getenv("GIS_FLAG_1") == "1" ):
                grass.run_command('g.remove', quiet = True, rast = qsxdx4 + ',' + qsydy4 + ',' + qsxdx2 + ',' + qsydy2 + ',' + qsxdx3 + ',' + qsydy3 + ',' +  qsd1)
            else:
                grass.run_command('g.remove', quiet = True, rast = qsxdx4 + ',' + qsydy4 + ',' + qsxdx2 + ',' + qsydy2 + ',' + qsxdx3 + ',' + qsydy3 + ',' +  qsxdx1 + ',' +  qsydy1)
        if ( os.getenv("GIS_FLAG_t") == "1" ):
            grass.message('Keeping Transport Capacity maps for all processes.')
        else:
            if ( os.getenv("GIS_FLAG_1") == "1" ):
                grass.run_command('g.remove', quiet = True, rast = qsx4 + ',' + qsy4 + ',' + qsx2 + ',' + qsy2 + ',' + qsx3 + ',' + qsy3 + ',' +  qs1)
            else:
                grass.run_command('g.remove', quiet = True, rast = qsx4 + ',' + qsy4 + ',' + qsx2 + ',' + qsy2 + ',' + qsx3 + ',' + qsy3 + ',' +  qsx1 + ',' +  qsy1)
        if ( os.getenv("GIS_FLAG_r") == "1" ):
            grass.message('Not keeping an Erosion and Deposition rate map.')
            grass.run_command('g.remove', quiet = True, rast = netchange)
        grass.run_command('g.remove', quiet =True, rast = flowdir + ',' + flowacc + ',' + aspect)
    sdcolors.close()
    nccolors.close()
    grass.message('\n*************************\nDone with Year %s ' % o + '\n*************************\n')

#Here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        # Set up some basic variables
        years = os.getenv("GIS_OPT_number")
        prefx = os.getenv("GIS_OPT_prefx")
        #Make the statsout file with correct column headers
        if os.getenv("GIS_OPT_statsout") == "":
            env = grass.gisenv()
            mapset = env['MAPSET']
            statsout = '%s_%slsevol_stats.csv' % (mapset, prefx)
        else:
            statsout = os.getenv("GIS_OPT_statsout")
        if os.path.isfile(statsout):
            f = file(statsout, 'a')
        else:
            f = file(statsout, 'wt')
            f.write('These statistics are in units of vertical meters (depth) per cell\nYear,,Mean Erosion,Standard Deviation Erosion,Minimum Erosion,First Quartile Erosion,Median Erosion,Third Quartile Erosion,Maximum Erosion,Original Un-smoothed Maximum Erosion,,Mean Deposition,Standard Deviation Deposition,Minimum Deposition,First Quartile Deposition,Median Deposition,Third Quartile Deposition,Maximum Deposition,Original Un-smoothed Maximum Deposition,,Mean Soil Depth,Standard Deviation Soil Depth,Minimum Soil Depth,First Quartile Soil Depth,Median Soil Depth,Third Quartile Soil Depth,Maximum Soil Depth')
        if ( os.getenv("GIS_FLAG_p") == "1" ):
            grass.message('Making sample points map for determining cutoffs.')
        else:
            grass.message('\n##################################################\n##################################################\n\n STARTING SIMULATION\n\nBeginning iteration sequence. This may take some time.\nProcess is not finished until you see the message: \'Done with everything\'\n _____________________________________________________________\n_____________________________________________________________\n')
            grass.message("Total number of iterations to be run is %s years" % years)
        #Get the region settings
        region1 = grass.region()
        # This is the loop!
        for x in range(int(years)):
            grass.message("Iteration = %s" % (x + 1))
            main(x, (x + 1), prefx, statsout, region1['nsres']);
        #Since we are now done with the loop, close the stats file.
        f.close()
        grass.message('\nIterations complete!\n\nDone with everything')




