#!/usr/bin/env python

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
# %Module
# % description: Simulates the cumulative effect of erosion and deposition on a landscape over time.
# % keyword: raster
# % keyword: modelling
# %End
# %option
# % key: elev
# % type: string
# % gisprompt: old,cell,raster
# % description: Input elevation map (DEM of surface)
# % required : yes
# %end
# %option
# % key: initbdrk
# % type: string
# % gisprompt: old,cell,raster
# % description: Bedrock elevations map (DEM of bedrock)
# % answer:
# % required : yes
# %end
# %option
# % key: k
# % type: string
# % gisprompt: old,cell,raster
# % description: Soil erodability index (K factor) map or constant
# % answer: 0.42
# % required : no
# % guisection: Landscape Evolution
# %end
# %option
# % key: sdensity
# % type: string
# % gisprompt: old,cell,raster
# % description: Soil density map or constant [T/m3] for conversion from mass to volume
# % answer: 1.2184
# % required : no
# % guisection: Landscape Evolution
# %end
# %option
# % key: kt
# % type: double
# % description: Stream transport efficiency variable (0.001 for a soft substrate, 0.0001 for a normal substrate, 0.00001 for a hard substrate, 0.000001 for a very hard substrate)
# % answer: 0.0001
# % required : no
# % options : 0.001,0.0001,0.00001,0.000001
# % guisection: Landscape Evolution
# %end
# %option
# % key: loadexp
# % type: double
# % description: Stream transport type variable (1.5 for mainly bedload transport, 2.5 for mainly suspended load transport)
# % answer: 1.5
# % options: 1.5,2.5
# % required : no
# % guisection: Landscape Evolution
# %end
# %option
# % key: kappa
# % type: double
# % description: Hillslope diffusion (Kappa) rate map or constant [m/kyr]
# % answer: 1
# % required : no
# % guisection: Landscape Evolution
# %end
# %option
# % key: c
# % type: string
# % gisprompt: old,cell,raster
# % description: Landcover index (C factor) map or constant
# % answer: 0.005
# % required : no
# % guisection: Landscape Evolution
# %end
# %option
# % key: rain
# % type: string
# % gisprompt: old,cell,raster
# % description: Precip totals for the average storm [mm] (or path to climate file of comma separated values of "rain,R,storms,stormlength", with a new line for each year of the simulation)
# % answer: 20.61
# % guisection: Climate
# %end
# %option
# % key: r
# % type: string
# % description: Rainfall (R factor) constant (AVERAGE FOR WHOLE MAP AREA) (or path to climate file of comma separated values of "rain,R,storms,stormlength", with a new line for each year of the simulation)
# % answer: 4.54
# % guisection: Climate
# %end
# %option
# % key: storms
# % type: string
# % description: Number of storms per year (integer) (or path to climate file of comma separated values of "rain,R,storms,stormlength", with a new line for each year of the simulation)
# % answer: 25
# % guisection: Climate
# %end
# %option
# % key: stormlength
# % type: string
# % description: Average length of the storm [h] (or path to climate file of comma separated values of "rain,R,storms,stormlength", with a new line for each year of the simulation)
# % answer: 24.0
# % guisection: Climate
# %end
# %option
# % key: speed
# % type: double
# % description: Average velocity of flowing water in the drainage [m/s]
# % answer: 1.4
# % required : no
# % guisection: Hydrology
# %end
# %option
# % key: manningn
# % type: string
# % gisprompt: old,cell,raster
# % description: Map or constant of the value of Manning's "N" value for channelized flow.
# % answer: 0.05
# % required : no
# % guisection: Hydrology
# %end
# %option
# % key: flowcontrib
# % type: string
# % gisprompt: old,cell,raster
# % description: Map or constant indicating how much each cell contributes to downstream flow (as a "percentage" from 0-100). If no map or value entered, routine will assume 100% downstream contribution
# % required : no
# % guisection: Hydrology
# %end
# %option
# % key: convergence
# % type: integer
# % description: Value for the flow convergence variable in r.watershed. Small values make water spread out, high values make it converge in narrower channels.
# % answer: 5
# % options: 1,2,3,4,5,6,7,8,9,10
# % required : no
# % guisection: Hydrology
# %end
# %option
# % key: cutoff1
# % type: double
# % description: Flow accumulation breakpoint value for shift from diffusion to overland flow
# % answer: 0
# % required : no
# % guisection: Hydrology
# %end
# %option
# % key: cutoff2
# % type: double
# % description: Flow accumulation breakpoint value for shift from overland flow to rill/gully flow (if value is the same as cutoff1, no sheetwash procesess will be modeled)
# % answer: 100
# % required : no
# % guisection: Hydrology
# %end
# %option
# % key: cutoff3
# % type: double
# % description: Flow accumulation breakpoint value for shift from rill/gully flow to stream flow (if value is the same as cutoff2, no rill procesess will be modeled)
# % answer: 100
# % required : no
# % guisection: Hydrology
# %end
# %option
# % key: smoothing
# % type: string
# % description: Amount of additional smoothing (answer "no" unless you notice large spikes in the erdep rate map)
# % answer: no
# % options: no,low,high
# % required : yes
# %end
# %option
# % key: prefx
# % type: string
# % description: Prefix for all output maps
# % answer: levol_
# % required : yes
# %end
# %option
# % key: outdem
# % type: string
# % description: Name stem for output elevation map(s) (preceded by prefix and followed by numerical suffix if more than one iteration)
# % answer: elevation
# % required: yes
# %end
# %option
# % key: outsoil
# % type: string
# % description: Name stem for the output soil depth map(s) (preceded by prefix and followed by numerical suffix if more than one iteration)
# % answer: soildepth
# % required: yes
# %end
# %option
# % key: number
# % type: integer
# % description: Number of iterations (cycles) to run
# % answer: 1
# % required : yes
# %end


# #%option
# #% key: alpha                 ###This may be added back in if I can find a good equation for mass movement
# #% type: integer
# #% description: Critical slope threshold for mass movement of sediment (in degrees above horizontal)
# #% answer: 40
# #% required : yes
# #%end

# %flag
# % key: p
# % description: -p Output a vector points map with sampled values of flow accumulation and curvatures suitable for determining cutoff values. NOTE: Overrides all other output options, and exits after completion. The output vector points map will be named  "PREFIX_#_randomly_sampled_points".
# % guisection: Optional
# %end
# %flag
# % key: 1
# % description: -1 Calculate streams as 1D difference instead of 2D divergence
# % guisection: Landscape Evolution
# %end
# %flag
# % key: c
# % description: -c Calculate streams with a shear stress equation, rather than a stream-power equation
# % guisection: Landscape Evolution
# %end
# %flag
# % key: k
# % description: -k Keep ALL temporary maps (overides flags -drst). This will make A LOT of maps!
# % guisection: Optional
# %end
# %flag
# % key: d
# % description: -d Don't output yearly soil depth maps
# % guisection: Optional
# %end
# %flag
# % key: r
# % description: -r Don't output yearly maps of the erosion/deposition rates ("ED_rate" map, in vertical meters)
# % guisection: Optional
# %end
# %flag
# % key: s
# % description: -s Keep all slope maps
# % guisection: Optional
# %end
# %flag
# % key: t
# % description: -t Keep yearly maps of the Transport Capacity at each cell ("Qs" maps)
# % guisection: Optional
# %end
# %flag
# % key: e
# % description: -e Keep yearly maps of the Excess Transport Capacity (divergence) at each cell ("DeltaQs" maps)
# % guisection: Optional
# %end
# %Option
# % key: statsout
# % type: string
# % description: Name for the statsout text file (optional, if none provided, a default name will be used)
# % required: no
# % guisection: Optional
# %end

import sys
import os
import math
import tempfile

grass_install_tree = os.getenv("GISBASE")
sys.path.append(grass_install_tree + os.sep + "etc" + os.sep + "python")
import grass.script as grass

# Now define  "main",  our main block of code, here defined because of the way g.parser needs to be called with python codes for grass (see below)
# m = last iteration number, o = iteration number, p = prefx, q = statsout, r = resolution of input elev map, s = master list of lists of climate data
def main(m, o, p, q, r, s):
    # get the process id to tag any temporary maps we make for easy clean up in the loop
    pid = os.getpid()
    # Get variables from user input
    smoothing = options["smoothing"]
    years = options["number"]
    initbdrk = options["initbdrk"]
    outdem = options["outdem"]
    outsoil = options["outsoil"]
    K = options["k"]
    sdensity = options["sdensity"]
    C = options["c"]
    kappa = options["kappa"]
    cutoff1 = options["cutoff1"]
    cutoff2 = options["cutoff2"]
    cutoff3 = options["cutoff3"]
    flowcontrib = options["flowcontrib"]
    convergence = options["convergence"]
    manningn = options["manningn"]
    old_bdrk = options["initbdrk"]
    # these variables come in as a list of lists, so let's get this year's numbers out of them.
    rain = s[0][m]
    storms = s[2][m]
    # CHANGES
    R = s[1][m] / storms
    # R = s[1][m]
    stormlengthsecs = float(s[3][m]) * 3600.00  # number of seconds in the storm
    stormtimet = stormlengthsecs / (
        float(options["speed"]) * float(r)
    )  # number of hydrologic instants in the storm
    #    timet = stormlengthsecs/stormtimet      # length of a single hydrologic instant in seconds, currently unused, but might be important in future versions
    Kt = options["kt"]
    loadexp = options["loadexp"]
    # Make some variables for temporary map names, labeled different depending on if we keep them or not
    if flags["k"] is True:
        aspect = "%saspect%04d" % (p, o)
        flowacc = "%sflowacc%04d" % (p, o)
        flacclargenums = "%sflowacc_largenums%04d" % (p, o)
        flowdir = "%sflowdir%04d" % (p, o)
        pc = "%spc%04d" % (p, o)
        tc = "%stc%04d" % (p, o)
        #        meancurv = '%smeancurv%04d' % (p, o)    # This variable might be used if bedrock weathering is ever implemented
        #        rate = '%srate%04d' % (p, o)    # This variable might be used if bedrock weathering is ever implemented
        rainexcess = "%s_rainfall_excess_map_%04d" % (p, o)
        tempnetchange1 = "%sTEMPORARY_unsmoothed_ED_rate%04d" % (p, o)
        tempnetchange2 = "%sTEMPORARY_smoothed_ED_rate%04d" % (p, o)
        tmperosion = "%sTEMPORARY_erosion%04d" % (p, o)
        tmpdep = "%sTEMPORARY_deposition%04d" % (p, o)
    else:
        aspect = "%saspect%04d" % (pid, o)
        flowacc = "%sflowacc%04d" % (pid, o)
        flacclargenums = "%sflowacc_largenums%04d" % (pid, o)
        flowdir = "%sflowdir%04d" % (pid, o)
        pc = "%spc%04d" % (pid, o)
        tc = "%stc%04d" % (pid, o)
        #        meancurv = '%smeancurv%04d' % (pid, o)    # This variable might be used if bedrock weathering is ever implemented
        #        rate = '%srate%04d' % (p, o)    # This variable might be used if bedrock weathering is ever implemented
        rainexcess = "%s_rainfall_excess_map_%04d" % (pid, o)
        tempnetchange1 = "%sTEMPORARY_unsmoothed_ED_rate%04d" % (pid, o)
        tempnetchange2 = "%sTEMPORARY_smoothed_ED_rate%04d" % (pid, o)
        tmperosion = "%sTEMPORARY_erosion%04d" % (pid, o)
        tmpdep = "%sTEMPORARY_deposition%04d" % (pid, o)
    # Make color rules for netchange maps
    nccolors = "100% 0 0 100\n1 blue\n0.5 indigo\n0.01 green\n0 white\n-0.01 yellow\n-0.5 orange\n-1 red\n0% 150 0 50"
    # Make color rules for soil depth maps
    sdcolors = "100% 0:249:47\n20% 78:151:211\n6% 194:84:171\n0% 227:174:217"
    # If first iteration, use input maps. Otherwise, use maps generated from previous iterations
    if o == 1:
        old_dem = "%s" % options["elev"]
        old_soil = "%s%s_init" % (prefx, options["outsoil"])
        grass.mapcalc(
            "${old_soil}=${old_dem}-${old_bdrk}",
            overwrite="True",
            quiet="True",
            old_soil=old_soil,
            old_dem=old_dem,
            old_bdrk=old_bdrk,
        )
    else:
        old_dem = "%s%s%04d" % (p, options["outdem"], m)
        old_soil = "%s%s%04d" % (p, options["outsoil"], m)
    # Checking for special condition of there being only one run, and setting variables accordingly (one year runs have no numbers suffixed to the output map names)
    if years == "1":
        slope = "%sslope" % p
        netchange = "%sED_rate" % p
        new_dem = "%s%s" % (p, outdem)
        new_soil = "%s%s" % (p, outsoil)
    else:
        slope = "%sslope%04d" % (p, o)
        netchange = "%sED_rate%04d" % (p, o)
        new_dem = "%s%s%04d" % (p, outdem, o)
        new_soil = "%s%s%04d" % (p, outsoil, o)
    # Check to see if we are going to only output diagnostics for determing cutoff values, and act accordingly
    if flags["p"] is True:
        grass.message(
            "GATHERING STATISTICS FOR DETERMINING CUTOFF VALUES\n-------------------------------------------------\n1) Calculating slope and curvatures"
        )
        grass.run_command(
            "r.slope.aspect",
            quiet="True",
            elevation=old_dem,
            slope=slope,
            pcurv=pc,
            tcurv=tc,
        )
    else:
        grass.message(
            "\n##################################################\n\n*************************\n Iteration %s -- "
            % o
            + "step 1: calculating slope\n*************************\n"
        )
        grass.run_command(
            "r.slope.aspect",
            quiet="True",
            elevation=old_dem,
            aspect=aspect,
            slope=slope,
        )
    if flags["p"] is True:
        grass.message("2) Calculating map of rainfall excess")
    else:
        grass.message(
            "\n*************************\n Iteration %s -- " % o
            + "step 2: calculating accumulated flow depths\n*************************\n"
        )
        grass.message(
            'Calculating runoff excess rates (uplsope accumulated cells scaled to "flowcontrib" map'
        )

    # make map of rainfall excess (proportion each cell contributes to downstrem flow) from flowcontrib. Note that if flowcontrib is a map, we are just making a copy of it. This map is a percentage, but has to be scale from 0-100, because r.watershed will only allow values greater than 1 as input in it's 'flow' variable. This creates a flow accumulation map with large numbers, but this map will be divided by 100 after it is made, which brings the values back down to what they should be.
    if flowcontrib == "":
        flowcontrib = 100
    grass.mapcalc(
        "${rainexcess}=int(${flowcontrib})",
        quiet="True",
        rainexcess=rainexcess,
        flowcontrib=flowcontrib,
    )
    if os.getenv("GIS_FLAG_p") == "1":
        grass.message(
            "3) Calculating accumulated flow (in numbers of upslope cells, scaled by runoff contribution"
        )
    grass.run_command(
        "r.watershed",
        quiet="True",
        flags="a",
        elevation=old_dem,
        flow=rainexcess,
        accumulation=flacclargenums,
        drainage=flowdir,
        convergence=convergence,
    )
    grass.mapcalc(
        "${flowacc}=${flacclargenums}/100",
        quiet="True",
        flowacc=flowacc,
        flacclargenums=flacclargenums,
    )
    # again, do something different if we are only making an evaluation of cutoffs
    if flags["p"] is True:
        grass.message(
            '4) Determining number of sampling points using formula: "ln(#cells_in_input_map)*100"'
        )
        flaccstats = grass.parse_command("r.univar", flags="g", map=flowacc)
        numpts = int(math.log(int(flaccstats["n"])) * 100)
        grass.message(
            "5) Creating random points and sampling values of flow accumulation, curvatures, and slope."
        )
        vout = "%s%s_randomly_sampled_points" % (p, numpts)
        grass.run_command(
            "r.random",
            quiet="True",
            input=flowacc,
            cover=pc,
            npoints=numpts,
            vector=vout,
        )
        grass.run_command(
            "v.db.renamecolumn", quiet="True", map=vout, column="value,Flow_acc"
        )
        grass.run_command(
            "v.db.renamecolumn", quiet="True", map=vout, column="covervalue,Princ_curv"
        )
        grass.run_command(
            "v.db.addcolumn",
            quiet="True",
            map=vout,
            columns="Tang_curv double precision, Slope double precision",
        )
        grass.run_command(
            "v.what.rast", quiet="True", map=vout, raster=tc, column="Tang_curv"
        )
        grass.run_command(
            "v.what.rast", quiet="True", map=vout, raster=slope, column="Slope"
        )
        if flags["k"] is True:
            grass.message(
                "--Keeping the created maps (Flow Accumulation, Slope, Principle Curvature, Tangential Curvature)"
            )
        else:
            grass.message("6) Cleaning up...")
            grass.run_command(
                "g.remove",
                quiet="True",
                flags="f",
                type="rast",
                name=slope + "," + pc + "," + tc + "," + flowacc,
            )
        grass.message(
            'FINISHED. \nRandom sample points map "%s" created successfully.\n' % vout
        )
        sys.exit(0)
    grass.message(
        "\n*************************\n Iteration %s -- " % o
        + "step 3: calculating sediment transport rates (units variable depending upon process) \n*************************\n"
    )
    # This step calculates the force of the flowing water at every cell on the landscape using the proper transport process law for the specific point in the flow regime. For upper hillslopes (below cutoff point 1) this done by multiplying the diffusion coeficient by the accumulated flow/cell res width. For midslopes (between cutoff 1 and 2) this is done by multiplying slope by accumulated flow with the m and n exponents set to 1. For channel catchment heads (between cutoff 2 and 3), this is done by multiplying slope by accumulated flow with the m and n exponents set to 1.6 and 1.3 respectively. For Channelized flow in streams (above cutoff 3), this is done by calculating the reach average shear stress (hydraulic radius [here estimated for a cellular landscape simply as the depth of flow]  times  slope times accumulated flow [cells] times gravitatiopnal acceleration of water [9806.65 newtons], all raised to the appropriate exponant for the type of transport (bedload or suspended load), and then divided by the resolution. Depth of flow is calculated as a mean "instantaneous depth" during any given rain event, here estimated by the maximum depth of an idealized unit hydrograph with base equal to the duration of the storm, and area equal to the total accumulated excess rainfall during the storm. Then finally calculates the stream power or sediment carrying capacity (qs) of the water flowing at each part of the map by multiplying the reach average shear stress (channelized flow in streams) or the estimated flow force (overland flow) by the transport coeficient (estimated by R*K*C for hillslopes or kt for streams). This is a "Transport Limited" equation, however, we add some constraints on detachment by checking to see if the sediment supply has been exhausted: if the current soil depth is 0 or negative (checking for a negative value is kind of an error trap) then we make the transport coefficient small (0.000001) to simulate erosion on bedrock. Because diffusion and USPED require 2D divergence later on, we calculate these as vectors in the X and Y directions. Stream flow only needs 1D difference, so it's calulated in the direction of flow.
    if flags["1"] is True:
        # This is the version with 1D streams
        qs1 = "%sQs_1D_streams%04d" % (p, o)
        # CHANGES
        # choose shear stress or stream power
        # these are the stream-power versions * note that I'm converting the stream-power output (kg/m2) to same units as USPED (T/ha) by multiplying by ten. This ensures they are even going into the divergence calculation #Qs = Kt * n^-1 * 9810 * depth^1.6 * tan(slope)^1.5
        if flags["c"] is True:
            grass.mapcalc(
                "${qs1}=(${Kt} * exp(9806.65*(((${rain}/1000)*${flowacc})/(0.595*${stormtimet}))*tan(${slope}), ${loadexp}) )",
                quiet="True",
                qs1=qs1,
                flowacc=flowacc,
                stormtimet=stormtimet,
                rain=rain,
                slope=slope,
                loadexp=loadexp,
                Kt=Kt,
                sdensity=sdensity,
            )
        else:
            grass.mapcalc(
                "${qs1}=10 * ${Kt} * exp(${manningn}, -1) * 9810 * exp( ( ( (${rain}/1000)*${flowacc}) / (0.595*${stormtimet}) ), 1.6) * exp(tan(${slope}), 1.5)",
                quiet="True",
                qs1=qs1,
                flowacc=flowacc,
                stormtimet=stormtimet,
                rain=rain,
                slope=slope,
                loadexp=loadexp,
                Kt=Kt,
                sdensity=sdensity,
                manningn=manningn,
            )
        qsx = "%sQsx_%04d" % (p, o)
        qsy = "%sQsy_%04d" % (p, o)
        grass.mapcalc(
            "${qsx}=eval(a=(${kappa} * sin(${slope}) * cos(${aspect})), b=((${R}*${K}*${C}*${flowacc}*${res}*sin(${slope})) * cos(${aspect})), c=( (${R}*${K}*${C}*exp((${flowacc}*${res}),1.6000000)*exp(sin(${slope}),1.3000000)) * cos(${aspect})),  if(${flowacc} <= ${cutoff1}, a, if(${flowacc} <= ${cutoff2} && ${flowacc} > ${cutoff1}, b, c)) )",
            quiet="True",
            qsx=qsx,
            kappa=kappa,
            slope=slope,
            aspect=aspect,
            R=R,
            K=K,
            C=C,
            res=r,
            flowacc=flowacc,
            Kt=Kt,
            rain=rain,
            stormtimet=stormtimet,
            loadexp=loadexp,
            cutoff1=cutoff1,
            cutoff2=cutoff2,
            cutoff3=cutoff3,
        )
        grass.mapcalc(
            "${qsy}=eval(a=(${kappa} * sin(${slope}) * sin(${aspect})), b=((${R}*${K}*${C}*${flowacc}*${res}*sin(${slope})) * sin(${aspect})), c=( (${R}*${K}*${C}*exp((${flowacc}*${res}),1.6000000)*exp(sin(${slope}),1.3000000)) * sin(${aspect})), if(${flowacc} <= ${cutoff1}, a, if(${flowacc} <= ${cutoff2} && ${flowacc} > ${cutoff1}, b, c)) )",
            quiet="True",
            qsy=qsy,
            kappa=kappa,
            slope=slope,
            aspect=aspect,
            R=R,
            K=K,
            C=C,
            res=r,
            flowacc=flowacc,
            Kt=Kt,
            rain=rain,
            stormtimet=stormtimet,
            loadexp=loadexp,
            cutoff1=cutoff1,
            cutoff2=cutoff2,
            cutoff3=cutoff3,
        )
    else:
        # This is the normal version (with 2D streams)
        qsx = "%sQsx_%04d" % (p, o)
        qsy = "%sQsy_%04d" % (p, o)
        if (
            flags["c"] is True
        ):  # do the shear stress version. Note that I'm converting the stream-power output (kg/m2) to same units as USPED (T/ha) by multiplying by ten. This ensures they are even going into the divergence calculation
            grass.mapcalc(
                "${qsx}=eval(a=(${kappa} * sin(${slope}) * cos(${aspect})), b=((${R}*${K}*${C}*${flowacc}*${res}*sin(${slope})) * cos(${aspect})), c=( (${R}*${K}*${C}*exp((${flowacc}*${res}),1.6000000)*exp(sin(${slope}),1.3000000)) * cos(${aspect})), d=10 * (${Kt} * exp(9806.65*(((${rain}/1000)*${flowacc})/(0.595*${stormtimet}))*tan(${slope}), ${loadexp}) ) * cos(${aspect}),  if(${flowacc} >= ${cutoff3}, a, if(${flowacc} >= ${cutoff2} && ${flowacc} < ${cutoff3}, b, if(${flowacc} >= ${cutoff1} && ${flowacc} < ${cutoff2}, c, d))) )",
                quiet="True",
                qsx=qsx,
                kappa=kappa,
                slope=slope,
                aspect=aspect,
                R=R,
                K=K,
                C=C,
                res=r,
                flowacc=flowacc,
                Kt=Kt,
                rain=rain,
                stormtimet=stormtimet,
                loadexp=loadexp,
                cutoff1=cutoff1,
                cutoff2=cutoff2,
                cutoff3=cutoff3,
            )
            grass.mapcalc(
                "${qsy}=eval(a=(${kappa} * sin(${slope}) * sin(${aspect})), b=((${R}*${K}*${C}*${flowacc}*${res}*sin(${slope})) * sin(${aspect})), c=( (${R}*${K}*${C}*exp((${flowacc}*${res}),1.6000000)*exp(sin(${slope}),1.3000000)) * sin(${aspect})), d=10 * (${Kt} * exp(9806.65*(((${rain}/1000)*${flowacc})/(0.595*${stormtimet}))*tan(${slope}), ${loadexp}) ) * sin(${aspect}), if(${flowacc} >= ${cutoff3}, a, if(${flowacc} >= ${cutoff2} && ${flowacc} < ${cutoff3}, b, if(${flowacc} >= ${cutoff1} && ${flowacc} < ${cutoff2}, c, d))) )",
                quiet="True",
                qsy=qsy,
                kappa=kappa,
                slope=slope,
                aspect=aspect,
                R=R,
                K=K,
                C=C,
                res=r,
                flowacc=flowacc,
                Kt=Kt,
                rain=rain,
                stormtimet=stormtimet,
                loadexp=loadexp,
                cutoff1=cutoff1,
                cutoff2=cutoff2,
                cutoff3=cutoff3,
            )
        else:  # do the stream powered version. Note that I'm converting the stream-power output (kg/m2) to same units as USPED (T/ha) by multiplying by ten. This ensures they are even going into the divergence calculation #Qs = Kt * n^-1 * 9810 * depth^1.6 * tan(slope)^1.5
            grass.mapcalc(
                "${qsx}=eval(a=(${kappa} * sin(${slope}) * cos(${aspect})), b=((${R}*${K}*${C}*${flowacc}*${res}*sin(${slope})) * cos(${aspect})), c=( (${R}*${K}*${C}*exp((${flowacc}*${res}),1.6000000)*exp(sin(${slope}),1.3000000)) * cos(${aspect})), d=10 *${Kt} * exp(${manningn}, -1) * 9810 * exp((((${rain}/1000)*${flowacc})/(0.595*${stormtimet})), 1.6) * exp(tan(${slope}), 1.5) * cos(${aspect}), if(${flowacc} <= ${cutoff1}, a, if(${flowacc} <= ${cutoff2} && ${flowacc} > ${cutoff1}, b, if(${flowacc} <= ${cutoff3} && ${flowacc} > ${cutoff2}, c, d))) )",
                quiet="True",
                qsx=qsx,
                kappa=kappa,
                slope=slope,
                aspect=aspect,
                R=R,
                K=K,
                C=C,
                res=r,
                flowacc=flowacc,
                Kt=Kt,
                rain=rain,
                stormtimet=stormtimet,
                loadexp=loadexp,
                cutoff1=cutoff1,
                cutoff2=cutoff2,
                cutoff3=cutoff3,
                manningn=manningn,
            )
            grass.mapcalc(
                "${qsy}=eval(a=(${kappa} * sin(${slope}) * sin(${aspect})), b=((${R}*${K}*${C}*${flowacc}*${res}*sin(${slope})) * sin(${aspect})), c=( (${R}*${K}*${C}*exp((${flowacc}*${res}),1.6000000)*exp(sin(${slope}),1.3000000)) * sin(${aspect})), d=10 * ${Kt} * exp(${manningn}, -1) * 9810 * exp((((${rain}/1000)*${flowacc})/(0.595*${stormtimet})), 1.6) * exp(tan(${slope}), 1.5) * sin(${aspect}), if(${flowacc} <= ${cutoff1}, a, if(${flowacc} <= ${cutoff2} && ${flowacc} > ${cutoff1}, b, if(${flowacc} <= ${cutoff3} && ${flowacc} > ${cutoff2}, c, d))) )",
                quiet="True",
                qsy=qsy,
                kappa=kappa,
                slope=slope,
                aspect=aspect,
                R=R,
                K=K,
                C=C,
                res=r,
                flowacc=flowacc,
                Kt=Kt,
                rain=rain,
                stormtimet=stormtimet,
                loadexp=loadexp,
                cutoff1=cutoff1,
                cutoff2=cutoff2,
                cutoff3=cutoff3,
                manningn=manningn,
            )
        # make a map of the total TC for debugging purposes
        # TC = "%sTC_%04d" % (p,o)
        # grass.mapcalc("${TC}=eval(a=${kappa} * sin(${slope}), b=${R}*${K}*${C}*${flowacc}*${res}*sin(${slope}), c=${R}* ${K}* ${C}* exp( (${flowacc}*${res}),1.6000000) * exp(sin(${slope}),1.3000000), d=10 * ${Kt} * exp(${manningn}, -1) * 9810 * exp( ( ( (${rain}/1000)*${flowacc}) / (0.595*${stormtimet}) ), 1.6) * exp(tan(${slope}), 1.5), if(${flowacc} >= ${cutoff3}, a, if(${flowacc} >= ${cutoff2} && ${flowacc} < ${cutoff3}, b, if(${flowacc} >= ${cutoff1} && ${flowacc} < ${cutoff2}, c, d) ) ) )", quiet = "True", TC = TC, kappa = kappa, slope = slope, aspect = aspect, R = R, K = K, C =C, res = r, flowacc = flowacc, Kt = Kt, rain = rain, stormtimet = stormtimet, loadexp = loadexp, cutoff1 = cutoff1, cutoff2 = cutoff2, cutoff3 = cutoff3, manningn = manningn)
        # /CHANGES

    grass.message(
        "\n*************************\n Iteration %s -- " % o
        + "step 4: calculating divergence/difference of sediment transport for each process and the actual amount of erosion or deposition in vertical meters/cell/year\n*************************\n\n"
    )
    # Here is where we figure out the change in transport capacity, and thus the actual amount of erosion an deposition that would occur. There are two ways of doing this. On planar and convex surfaces (i.e., ridgetops, flats, hillslopes), it is better to take the 2D divergence of sediment flux (we use r.slope.aspect to calculate this), but on highly convex surfaces (i.e., in channels) it is better to take the 1D difference between one cell, and the cell that is immediately downstream from it. This all assumes that the system is always operating at Transport Capacity, or if it is not, then is still behaves as if it were (ie., that the actual differences in transported sediment between the cells would be proportional to the system operating at capacity). Thus, under this assumption, the divergence of capacity is equals to actual amount of sediment eroded/deposited.
    # This is the way we implemnt this: First calculate, we calculate the divergence/differnce for EACH of the different flow processes on the ENTIRE map (i.e., make one map per process, difference for streams, divergence for USPED and diffusion). Then, we cut out the pieces of each of these maps that correspond to the correct landforms from each specific process (based on the user-input cutoffs in flow accumulation), and patch them together into a single map (NOTE: see output unit conversions section below to see how we get all the units to line up during this process). This counters the "boundary effect" that happens when running the differential equations for divergence across the boundary of two different flow processes.  Then we may still have to run a median smoother on the patched map to get rid of any latent spikes.
    if flags["1"] is True:
        # This is the version with 1D streams
        qsd1 = "%sDelta_Qs_1D_streams%04d" % (p, o)
        grass.mapcalc(
            "${qsd1}=if(${flowdir} == 7, (${qs1}[-1,-1]-${qs1}), if (${flowdir} == 6, (${qs1}[-1,0]-${qs1}), if (${flowdir} == 5, (${qs1}[-1,1]-${qs1}), if (${flowdir} == 4, (${qs1}[0,1]-${qs1}), if (${flowdir} == 3, (${qs1}[1,1]-${qs1}), if (${flowdir} == 2, (${qs1}[1,0]-${qs1}), if (${flowdir} == 1, (${qs1}[1,-1]-${qs1}), if (${flowdir} == 8, (${qs1}[0,-1]-${qs1}), ${qs1}))))))))",
            quiet="True",
            qsd1=qsd1,
            flowdir=flowdir,
            qs1=qs1,
        )
        qsxdx = "%sDelta_Qsx_%04d" % (p, o)
        qsydy = "%sDelta_Qsy_%04d" % (p, o)
        grass.run_command("r.slope.aspect", quiet="True", elevation=qsx, dx=qsxdx)
        grass.run_command("r.slope.aspect", quiet="True", elevation=qsy, dy=qsydy)
    else:
        # This is the normal version (with 2D streams)
        qsxdx = "%sDelta_Qsx_%04d" % (p, o)
        qsydy = "%sDelta_Qsy_%04d" % (p, o)
        grass.run_command("r.slope.aspect", quiet="True", elevation=qsx, dx=qsxdx)
        grass.run_command("r.slope.aspect", quiet="True", elevation=qsy, dy=qsydy)

    # This is the smoothing routine. First we calculate the rate of Erosion and Deposition by converting the Delta QS of the different processes to vertical meters by dividing by the soil denisity (with apropriate constants to get into the correct units, see UNIT CONVERSION note below), and for streams, also expand from the storm to the year level. All units of this initial (temporary) ED_rate map will be in m/cell/year.
    # CHANGES
    # OUTPUT UNIT CONVERSIONS: In the case of the diffusion equation, the output units are in vertical meters of sediment per cell per year, so these will be left alone. Everything else should be in units of T/cell per storm. So we just need to convert to kg/cell, divide by the soil density and multiply the number of storms
    if flags["1"] is True:
        # This is the version with 1D streams
        grass.mapcalc(
            "${tempnetchange1}=if(${flowacc} >= ${cutoff3}, ((${qsd1}*0.1)/${sdensity})*${storms}, if(${flowacc} >= ${cutoff1} && ${flowacc} < ${cutoff3}, (((${qsxdx}+${qsydy})*0.1)/${sdensity})*${storms}, ${qsxdx}+${qsydy}))",
            quiet="True",
            tempnetchange1=tempnetchange1,
            qsd1=qsd1,
            qsxdx=qsxdx,
            qsydy=qsydy,
            flowacc=flowacc,
            cutoff1=cutoff1,
            cutoff3=cutoff3,
            sdensity=sdensity,
            storms=storms,
            stormtimet=stormtimet,
        )
    else:
        # This is the normal version (with 2D streams)
        grass.mapcalc(
            "${tempnetchange1}=if(${flowacc} >= ${cutoff1}, (((${qsxdx} + ${qsydy})*0.1)/${sdensity})*${storms}, ${qsxdx}+${qsydy})",
            quiet="True",
            tempnetchange1=tempnetchange1,
            qsxdx=qsxdx,
            qsydy=qsydy,
            flowacc=flowacc,
            cutoff1=cutoff1,
            cutoff3=cutoff3,
            sdensity=sdensity,
            storms=storms,
            stormtimet=stormtimet,
        )
        # grass.mapcalc('${tempnetchange1}=if(${flowacc} >= ${cutoff3}, (((${qsxdx} + ${qsydy})*0.1)/${sdensity})*${storms}, if(${flowacc} >= ${cutoff1} && ${flowacc} < ${cutoff3}, ((${qsxdx}+${qsydy})*0.1)/${sdensity}, ${qsxdx}+${qsydy}))', quiet = "True", tempnetchange1 = tempnetchange1, qsxdx = qsxdx, qsydy = qsydy, flowacc = flowacc, cutoff1 = cutoff1, cutoff3 = cutoff3, sdensity = sdensity, storms = storms, stormtimet = stormtimet)
        # /CHANGES

    # Make some temp maps of just erosion rate and just deposition rate so we can grab some stats from them for the soft-knee limiting filter
    grass.message("Running soft-knee smoothing filter...")
    grass.mapcalc(
        "${tmperosion}=if(${tempnetchange1} < -0, ${tempnetchange1}, null())",
        quiet="True",
        tmperosion=tmperosion,
        tempnetchange1=tempnetchange1,
    )
    grass.mapcalc(
        "${tmpdep}=if(${tempnetchange1} > 0, ${tempnetchange1}, null())",
        quiet="True",
        tmpdep=tmpdep,
        tempnetchange1=tempnetchange1,
    )
    # Grab the stats from these temp files and save them to dictionaries
    erosstats = grass.parse_command(
        "r.univar", flags="ge", percentile="1", map=tmperosion
    )
    depostats = grass.parse_command("r.univar", flags="ge", percentile="99", map=tmpdep)
    maximum = depostats["max"]
    minimum = erosstats["min"]
    erosbreak = float(erosstats["first_quartile"])
    deposbreak = float(depostats["third_quartile"])
    scalemin = float(erosstats["percentile_1"])
    scalemax = float(depostats["percentile_99"])
    # Use the stats we gathered to do some smoothing with a hi-cut and lo-cut filter (with soft-knee limiting) of the unsmoothed ED_rate map. Values from the 1st quartile of erosion to the minimum (i.e., the very large negative numbers) will be rescaled linearly from the 1st quartile to the 1st percentile value, and values from the 3rd quartile of deposition to the maximum (i.e., the very large positiive numbers) will be rescaled linearly from the 3rd quartile to the 99th percentile value. This brings any values that were really unreasonnable as originally calculated (spikes) into the range of what the maximum values should be on a normally distrubuted dataset, but does so with out a "brick wall" style of limiting, which would make all values above some cutoff equal to a theoretical maximum. By setting both maximum cutoff point AND a "soft" scaling point, this "soft-knee" style of limiting sill retains some of the original scaling at the high ends, which allows for the smoothed value of very high cells to still be relatively higher than values in other cells that were also above the scaling cutoff, but were not originally as high as those very high cells.
    grass.mapcalc(
        "${tempnetchange2}=graph(${tempnetchange1}, ${minimum},${scalemin}, ${erosbreak},${erosbreak}, ${deposbreak},${deposbreak}, ${maximum},${scalemax})",
        quiet="True",
        tempnetchange2=tempnetchange2,
        tempnetchange1=tempnetchange1,
        minimum=minimum,
        scalemin=scalemin,
        erosbreak=erosbreak,
        deposbreak=deposbreak,
        maximum=maximum,
        scalemax=scalemax,
    )
    # Check if additional smoothing is requested.
    if smoothing == "no":
        grass.message("No additional modal smoothing was requested...")
        grass.run_command(
            "g.rename", quiet="True", rast=tempnetchange2 + "," + netchange
        )
    elif smoothing == "low":
        grass.message(
            'Enacting additional "low" smoothing: one pass of a 3x3 modal smoothing window.'
        )
        grass.run_command(
            "r.neighbors",
            quiet="True",
            input=tempnetchange2,
            output=netchange,
            method="mode",
            size="3",
        )
    elif smoothing == "high":
        grass.message(
            'Enacting additional "high" smoothing: one pass of a 5x5 modal smoothing window.'
        )
        grass.run_command(
            "r.neighbors",
            quiet="True",
            input=tempnetchange2,
            output=netchange,
            method="mode",
            size="5",
        )
    else:
        grass.message(
            "There was a problem reading the median-smoothing variable, so maps will not be median-smoothed."
        )
        grass.run_command(
            "g.rename", quiet="True", rast=tempnetchange2 + "," + netchange
        )
    # Set the netchange map colors to the rules we've provided above
    grass.write_command(
        "r.colors", quiet=True, map=netchange, rules="-", stdin=nccolors
    )
    # Grab the stats from these new smoothed netchange maps and save them to dictionaries (Note that the temporary erosion and deposition maps made in this step are overwriting the two temporary maps made for gathering the stats for the soft-knee limiting filter)
    grass.mapcalc(
        "${tmperosion}=if(${netchange} < -0, ${netchange}, null())",
        quiet="True",
        overwrite="True",
        tmperosion=tmperosion,
        netchange=netchange,
    )
    grass.mapcalc(
        "${tmpdep}=if(${netchange} > 0, ${netchange}, null())",
        quiet="True",
        overwrite="True",
        tmpdep=tmpdep,
        netchange=netchange,
    )
    erosstats1 = grass.parse_command("r.univar", flags="ge", map=tmperosion)
    depostats1 = grass.parse_command("r.univar", flags="ge", map=tmpdep)

    grass.message(
        "\n*************************\n Iteration %s -- " % o
        + "step 5: calculating terrain evolution and new soil depths\n *************************\n\n"
    )
    # Set up a temp dem, and then do initial addition of ED change to old DEM. This mapcalc statement first checks the amount of erodable soil in a given cell against the amount of erosion calculated, and keeps the cell from eroding past this amount (if there is soil, then if the amount of erosion is more than the amount of soil, just remove all the soil and stop, else remove the amount of caclulated erosion. It also runs an error catch that checks to make sure that soil depth is not negative (could happen, I suppose), and if it is, corrects it). Finally, do patch-job to catch the shrinking edge problem (the edge cells have no upstream cell, so get turned null in the calculations in step 4)
    grass.mapcalc(
        "${new_dem}=eval(x=if(${old_soil} > 0.0 && (-1*${netchange}) <= ${old_soil}, ${netchange}, if((-1*${netchange}) > ${old_soil},   (-1*${old_soil}), 0)), y=(${old_dem} + x), if(isnull(y), ${old_dem}, y))",
        quiet="True",
        new_dem=new_dem,
        old_soil=old_soil,
        old_dem=old_dem,
        netchange=netchange,
    )
    # Set colors for elevation map to match other dems
    grass.run_command("r.colors", quiet="True", map=new_dem, rast=options["elev"])
    grass.mapcalc(
        "${new_soil}=if ((${new_dem} - ${initbdrk}) < 0, 0, (${new_dem} - ${initbdrk}))",
        quiet="True",
        new_soil=new_soil,
        new_dem=new_dem,
        initbdrk=initbdrk,
    )
    grass.write_command("r.colors", quiet=True, map=new_soil, rules="-", stdin=sdcolors)
    grass.message(
        "\n*************************\n Iteration %s -- " % o
        + "step 6: writing stats to output file\n *************************\n\n"
    )
    # Finish gathering stats (just need the soil depth stats now)
    soilstats = grass.parse_command(
        "r.univar", flags="ge", map=new_soil, percentile="99"
    )
    # Write stats to a new line in the stats file
    # HEADER of the file should be: ',,Mean Values,,,,Standard Deviations,,,,Totals,,,Additional Stats\nIteration,,Mean Erosion,Mean Deposition,Mean Soil Depth,,Standard Deviation Erosion,Standard Deviation Deposition,Standard Deviation Soil Depth,,Total Sediment Eroded,Total Sediment Deposited,,Minimum Erosion,First Quartile Erosion,Median Erosion,Third Quartile Erosion,Maximum Erosion,Original Un-smoothed Maximum Erosion,,Minimum Deposition,First Quartile Deposition,Median Deposition,Third Quartile Deposition,Maximum Deposition,Original Un-smoothed Maximum Deposition,,Minimum Soil Depth,First Quartile Soil Depth,Median Soil Depth,Third Quartile Soil Depth,Maximum Soil Depth'
    grass.message("Outputing stats to textfile: " + q)
    f.write(
        "\n%s" % o
        + ",,"
        + erosstats1["mean"]
        + ","
        + depostats1["mean"]
        + ","
        + soilstats["mean"]
        + ",,"
        + erosstats1["stddev"]
        + ","
        + depostats1["stddev"]
        + ","
        + soilstats["stddev"]
        + ",,"
        + erosstats1["sum"]
        + ","
        + depostats1["sum"]
        + ",,"
        + erosstats1["max"]
        + ","
        + erosstats1["third_quartile"]
        + ","
        + erosstats1["median"]
        + ","
        + erosstats1["first_quartile"]
        + ","
        + erosstats1["min"]
        + ","
        + minimum
        + ",,"
        + depostats1["min"]
        + ","
        + depostats1["first_quartile"]
        + ","
        + depostats1["median"]
        + ","
        + depostats1["third_quartile"]
        + ","
        + depostats1["max"]
        + ","
        + maximum
        + ",,"
        + soilstats["min"]
        + ","
        + soilstats["first_quartile"]
        + ","
        + soilstats["median"]
        + ","
        + soilstats["third_quartile"]
        + ","
        + soilstats["max"]
    )

    # Clean up temporary maps
    if flags["k"] is True:
        grass.message("\nTemporary maps will NOT be deleted!!!!\n")
    else:
        grass.message("\nCleaning up temporary maps...\n\n")
        # first remove all the easy temporary maps labeled with "pid"
        grass.run_command(
            "g.remove", quiet="True", flags="f", type="rast", pattern="%s*" % pid
        )
        # now check all the flag options, and build a list of maps to delete
        mapstoremove = []
        if flags["s"] is True:
            grass.message("Keeping Slope map.")
        else:
            mapstoremove.append(slope)
        if flags["d"] is True:
            grass.message("Not keeping Soil Depth map.")
            mapstoremove.append(old_soil)
            # check if this is the last year and remove the "new-soil" map too
            if o == int(options["number"]):
                mapstoremove.append(new_soil)
        else:
            # check if this is the first year, and if so, remove the temporary "soildepths_init" map
            if o <= 1:
                mapstoremove.append("%s%s_init" % (prefx, options["outsoil"]))
        if flags["e"] is True:
            grass.message(
                "Keeping Excess Transport Capacity (divergence) maps for all processes."
            )
        else:
            mapstoremove.extend([qsxdx, qsydy])
            if flags["1"] is True:
                mapstoremove.append(qsd1)
        if flags["t"] is True:
            grass.message("Keeping Transport Capacity maps for all processes.")
        else:
            mapstoremove.extend([qsx, qsy])
            if flags["1"] is True:
                mapstoremove.append(qs1)
        if flags["r"] is True:
            grass.message("Not keeping an Erosion and Deposition rate map.")
            mapstoremove.append(netchange)
        if len(mapstoremove) == 0:
            pass
        else:
            grass.run_command(
                "g.remove",
                quiet="True",
                flags="f",
                type="rast",
                name=",".join(mapstoremove),
            )

    grass.message(
        "\n*************************\nDone with Iteration %s " % o
        + "\n*************************\n"
    )
    return 0


# Here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    options, flags = grass.parser()
    # Set up some basic variables
    years = options["number"]
    prefx = options["prefx"]
    # these values could be read in from a climate file, so check that, and act accordingly. Either way, the result will be some lists with the same number of entries as there are iterations.
    rain2 = []
    try:
        rain1 = float(options["rain"])
        for year in range(int(years)):
            rain2.append(rain1)
    except:
        with open(options["rain"], "rU") as f:
            for line in f:
                rain2.append(line.split(",")[0])
        # check for text header and remove if present
        try:
            float(rain2[0])
        except:
            del rain2[0]
        # throw a warning if there aren't enough values in the column
        if len(rain2) != int(years):
            grass.fatal(
                "Number of rows of rainfall data in your climate file\n do not match the number of iterations you wish to run.\n Please ensure that these numbers match and try again"
            )
            sys.exit(1)
    R2 = []
    try:
        R1 = float(options["r"])
        for year in range(int(years)):
            R2.append(R1)
    except:
        with open(options["r"], "rU") as f:
            for line in f:
                R2.append(line.split(",")[1])
        # check for text header and remove if present
        try:
            float(R2[0])
        except:
            del R2[0]
        # throw a warning if there aren't enough values in the column
        if len(R2) != int(years):
            grass.fatal(
                "Number of rows of R-Factor data in your climate file\n do not match the number of iterations you wish to run.\n Please ensure that these numbers match and try again"
            )
            sys.exit(1)
    storms2 = []
    try:
        storms1 = float(options["storms"])
        for year in range(int(years)):
            storms2.append(storms1)
    except:
        with open(options["storms"], "rU") as f:
            for line in f:
                storms2.append(line.split(",")[2])
        # check for text header and remove if present
        try:
            float(storms2[0])
        except:
            del storms2[0]
        # throw a warning if there aren't enough values in the column
        if len(storms2) != int(years):
            grass.fatal(
                "Number of rows of storm frequency data in your climate file\n do not match the number of iterations you wish to run.\n Please ensure that these numbers match and try again"
            )
            sys.exit(1)
    stormlength2 = []
    try:
        stormlength1 = float(options["stormlength"])
        for year in range(int(years)):
            stormlength2.append(stormlength1)
    except:
        with open(options["stormlength"], "rU") as f:
            for line in f:
                stormlength2.append(line.split(",")[3])
        # check for text header and remove if present
        try:
            float(stormlength2[0])
        except:
            del stormlength2[0]
        # throw a warning if there aren't enough values in the column
        if len(stormlength2) != int(years):
            grass.fatal(
                "Number of rows of storm length data in your climate file\n do not match the number of iterations you wish to run.\n Please ensure that these numbers match and try again"
            )
            sys.exit(1)
    # Now gather these four lists into one master list, to make it easier to pass on to main()
    masterlist = [rain2, R2, storms2, stormlength2]
    # Make the statsout file with correct column headers
    if options["statsout"] == "":
        env = grass.gisenv()
        mapset = env["MAPSET"]
        statsout = "%s_%slsevol_stats.csv" % (mapset, prefx)
    else:
        statsout = options["statsout"]
    if os.path.isfile(statsout):
        f = open(statsout, "a")
    else:
        f = open(statsout, "wt")
        f.write(
            "These statistics are in units of vertical meters (depth) per cell\n,,Mean Values,,,,Standard Deviations,,,,Totals,,,Additional Stats\nIteration,,Mean Erosion,Mean Deposition,Mean Soil Depth,,Standard Deviation Erosion,Standard Deviation Deposition,Standard Deviation Soil Depth,,Total Sediment Eroded,Total Sediment Deposited,,Minimum Erosion,First Quartile Erosion,Median Erosion,Third Quartile Erosion,Maximum Erosion,Original Un-smoothed Maximum Erosion,,Minimum Deposition,First Quartile Deposition,Median Deposition,Third Quartile Deposition,Maximum Deposition,Original Un-smoothed Maximum Deposition,,Minimum Soil Depth,First Quartile Soil Depth,Median Soil Depth,Third Quartile Soil Depth,Maximum Soil Depth"
        )
    if flags["p"] is True:
        grass.message("Making sample points map for determining cutoffs.")
    else:
        grass.message(
            "\n##################################################\n##################################################\n\n STARTING SIMULATION\n\nBeginning iteration sequence. This may take some time.\nProcess is not finished until you see the message: 'Done with everything'\n _____________________________________________________________\n_____________________________________________________________\n"
        )
        grass.message("Total number of iterations to be run is %s" % years)
    # Get the region settings
    region1 = grass.region()
    # This is the loop!
    for x in range(int(years)):
        grass.message("Iteration = %s" % (x + 1))
        main(x, (x + 1), prefx, statsout, region1["nsres"], masterlist)
    # Since we are now done with the loop, close the stats file.
    f.close()
    grass.message("\nIterations complete!\n\nDone with everything")
    sys.exit(0)
