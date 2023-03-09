#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.landscape.evol.py
# AUTHOR(S):    Isaac Ullah and Michael Barton
# COPYRIGHT:    (C) 2020 GRASS Development Team/Isaac Ullah
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
# % keyword: hydrology
# % keyword: erosion modeling
# % keyword: landscape evolution
# %End
# %option G_OPT_R_ELEV
# % key: elev
# % description: Input elevation map (DEM of surface)
# % required : yes
# %end
# %option G_OPT_R_INPUT
# % key: initbdrk
# % description: Bedrock elevations map (DEM of bedrock)
# % answer:
# % required : yes
# %end
# %option G_OPT_R_BASENAME_OUTPUT
# % key: prefx
# % answer: levol_
# % required : yes
# %end
# %option G_OPT_R_BASENAME_OUTPUT
# % key: outdem
# % description: Name stem for output elevation map(s) (preceded by prefix and followed by numerical suffix if more than one iteration)
# % answer: elevation
# % required: yes
# %end
# %option G_OPT_R_BASENAME_OUTPUT
# % key: outsoil
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

# %option G_OPT_R_MAP
# % key: k
# % description: Soil erodability index (K factor) map or constant (values <= 0.09 [t.ha.h /ha.MJ.mm])
# % answer: 0.05
# % required : no
# % guisection: Landscape Evolution
# %end
# %option G_OPT_R_MAP
# % key: c
# % description: Landcover index (C factor) map or constant (values <=1.0 [unitless])
# % answer: 0.005
# % required : no
# % guisection: Landscape Evolution
# %end
# %option G_OPT_R_MAP
# % key: p
# % description: Landuse practices factor (P factor) map or constant (values <=1.0 [unitless])
# % answer: 1.0
# % required : no
# % guisection: Landscape Evolution
# %end
# %option G_OPT_R_MAP
# % key: sdensity
# % description: Soil density map or constant for conversion from mass to volume (values typically >=1000 [kg/m3])
# % answer: 1218.4
# % required : no
# % guisection: Landscape Evolution
# %end
# %option
# % key: transp_eq
# % type: string
# % description: The sediment transport equation to use (USPED: Tc=R*K*C*P*A^m*B^n, Stream power: Tc=Kt*gw*1/N*h^m*B^n, or Shear stress: Tc=Kt*tau^m ).
# % answer: StreamPower
# % options: StreamPower,ShearStress,USPED
# % guisection: Landscape Evolution
# %end
# %option
# % key: exp_m
# % type: string
# % description: Exponent m relates to the influence of upslope area (and thus flow depth, discharge) on transport capacity. Values generally thought to scale inversely with increasing depth of flow between the two cutoff thresholds specified: "thresh1,m1,thresh2,m2"
# % answer: 10,2,100,1
# % required : no
# % guisection: Landscape Evolution
# %end
# %option
# % key: exp_n
# % type: string
# % description: Exponent n relates to the influence of local topographic slope on transport capacity. Default values set to scale inversely with increasing local slope between the two slope cutoff thresholds specified: "thresh1,n1,thresh2,n2"
# % answer: 10,2,45,0.5
# % required : no
# % guisection: Landscape Evolution
# %end
# %flag
# % key: m
# % description: -m Apply smoothing (useful to mitigate possible unstable conditions in streams)
# % guisection: Landscape Evolution
# %end

# %option G_OPT_R_MAP
# % key: r
# % description: Rainfall (R factor) map or constant (Employed only in the USPED equation) (values typically between 500 and 10000 [MJ.mm/ha.h.yr])
# % answer: 720
# % guisection: Climate
# %end
# %option G_OPT_R_MAP
# % key: rain
# % description: Precip total for the average erosion-causing storm map (Employed in stream power and shear stress equations) (values typically >=30.0 [mm])
# % answer: 30
# % guisection: Climate
# %end
# %option G_OPT_R_MAP
# % key: storms
# % description: Number of erosion-causing storms per year map or constant (Employed in stream power and shear stress equations) (values >=0 [integer])
# % answer: 2
# % guisection: Climate
# %end
# %option G_OPT_R_MAP
# % key: stormlength
# % description: Average length of the storm map or constant (Employed in stream power and shear stress equations) (values >=0.0 [h])
# % answer: 24.0
# % guisection: Climate
# %end
# %option G_OPT_R_MAP
# % key: stormi
# % description: Proportion of the length of the storm where the storm is at peak intensity map or constant (Employed in stream power and shear stress equations) (values typically ~0.05 [unitless proportion])
# % answer: 0.05
# % guisection: Climate
# %end
# %option G_OPT_F_INPUT
# % key: climfile
# % required: no
# % description: Path to climate file of comma separated values of "rain,R,storms,stormlength,stormi", with a new line for each year of the simulation. This option will override values or maps entered above.
# % guisection: Climate
# %end
# %option G_OPT_R_MAP
# % key: manningn
# % description: Map or constant of the value of Manning's "N" value for channelized flow. (Employed in stream power and shear stress equations) (0.03 = clean/straight stream channel, 0.035 = major river, 0.04 = sluggish stream with pools, 0.06 = very clogged streams [unitless])
# % answer: 0.03
# % required: no
# % guisection: Hydrology
# %end
# %option G_OPT_R_MAP
# % key: flowcontrib
# % description: Map or constant indicating how much each cell contributes to downstream flow (this typically relates to vegetation or conservation practices). If no map or value entered, routine will assume 100% downstream contribution (values between 0 and 100 [unitless percentage])
# % answer: 100
# % required : no
# % guisection: Hydrology
# %end
# %option
# % key: convergence
# % type: integer
# % description: Value for the flow convergence variable in r.watershed. Small values make water spread out, high values make it converge in narrower channels.
# % answer: 5
# % options: 1,2,3,4,5,6,7,8,9,10
# % required: no
# % guisection: Hydrology
# %end


# %flag
# % key: p
# % description: -p Run a sampling procedure to generate a vector points map with scaled flow accumulation values suitable for determining transport equation thresholds. Overrides all other output.
# % guisection: Optional
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
# %Option G_OPT_F_OUTPUT
# % key: statsout
# % description: Name for the statsout text file (optional, if none provided, a default name will be used)
# % required: no
# % guisection: Optional
# %end

import sys
import os
import math

GISBASE = os.getenv("GISBASE")
sys.path.append(GISBASE + os.sep + "etc" + os.sep + "python")
import grass.script as grass


def main():
    """
    This is the main code block where the variables and loop are set up and
    executed.
    """
    # Set up some basic variables
    years = options["number"]
    prefx = options["prefx"]

    # These values could be read in from a climate file, so check that, and
    # act accordingly. Either way, the result will be some lists with the same
    # number of entries as there are iterations.
    if options["climfile"]:
        R2 = climfile(options["climfile"], 0, years)
        rain2 = climfile(options["climfile"], 1, years)
        stormlength2 = climfile(options["climfile"], 2, years)
        storms2 = climfile(options["climfile"], 3, years)
        stormi2 = climfile(options["climfile"], 4, years)
    else:
        R2 = climfile(options["r"], 0, years)
        rain2 = climfile(options["rain"], 1, years)
        stormlength2 = climfile(options["stormlength"], 2, years)
        storms2 = climfile(options["storms"], 3, years)
        stormi2 = climfile(options["stormi"], 4, years)

    # Now gather these four lists into one master list, to make it easier to pass on to main()
    masterlist = [R2, rain2, stormlength2, storms2, stormi2]

    # Make the statsout file with correct column headers
    if options["statsout"] == "":
        env = grass.gisenv()
        mapset = env["MAPSET"]
        statsout = "%s_%slsevol_stats.csv" % (mapset, prefx)
    else:
        statsout = options["statsout"]
    if os.path.isfile(statsout):
        f = open(statsout, "at")
    else:
        f = open(statsout, "wt")
        f.write(
            "These statistics are in units of vertical meters (depth) per cell\n"
            + " ,,Mean Values,,,,Standard Deviations,,,,Totals,,,Additional Stats\n"
            + "Iteration,,Mean Erosion,Mean Deposition,Mean Soil Depth,,"
            + "Standard Deviation Erosion,Standard Deviation Deposition,Standard Deviation Soil Depth,,"
            + "Total Sediment Eroded,Total Sediment Deposited,,"
            + "Minimum Erosion,First Quartile Erosion,Median Erosion,Third Quartile Erosion,Maximum Erosion,Original Un-smoothed Maximum Erosion,,"
            + "Minimum Deposition,First Quartile Deposition,Median Deposition,Third Quartile Deposition,Maximum Deposition,Original Un-smoothed Maximum Deposition,,"
            + "Minimum Soil Depth,First Quartile Soil Depth,Median Soil Depth,Third Quartile Soil Depth,Maximum Soil Depth"
        )
    if flags["p"] is True:
        grass.message("Making sample points map for determining cutoffs.")
    else:
        grass.message(
            "\n##################################################"
            + "\n##################################################\n"
            + "\n STARTING SIMULATION\n"
            + "\nBeginning iteration sequence. This may take some time.\n"
            + "Process is not finished until you see the message: 'Done with everything!'\n"
            + " _____________________________________________________________\n"
            + "_____________________________________________________________\n"
        )
        grass.message("Total number of iterations to be run is %s" % years)

    # Get the region settings
    region1 = grass.region()

    # This is the main loop for interating landscape evolution!
    if years == 1:
        landscapeEvol(0, 1, prefx, statsout, region1["nsres"], masterlist, f)
    else:
        for x in range(int(years)):
            grass.message(
                "\n##################################################\n"
                + "\n*************************\n"
                + "Starting Iteration = %s" % (x + 1)
                + "\n*************************\n"
            )
            landscapeEvol(x, (x + 1), prefx, statsout, region1["nsres"], masterlist, f)

        # Since we are now done with the loop, close the stats file.
    f.close()
    grass.message("\nIterations complete!\n" + "\nDone with everything!")
    sys.exit(0)


def landscapeEvol(m, o, p, q, res, s, f):
    """
    Now define  "landscapeEvol",  our main block of code, here defined
    because of the way g.parser needs to be called with python codes for grass
    (see below)
    m = last iteration number,
    o = iteration number,
    p = prefx,
    q = statsout,
    res = resolution of input elev map,
    s = master list of lists of climate data
    f = name of text file to write stats to
    """

    # Get the process id to tag any temporary maps we make for easy clean up in the loop
    pid = os.getpid()

    # Get variables from user input
    elev = options["elev"]
    transp_eq = options["transp_eq"]
    initbdrk = options["initbdrk"]
    outdem = options["outdem"]
    outsoil = options["outsoil"]
    sdensity = options["sdensity"]
    K = options["k"]
    P = options["p"]
    C = options["c"]
    exp_m = options["exp_m"].split(",")
    exp_n = options["exp_n"].split(",")
    flowcontrib = options["flowcontrib"]
    convergence = options["convergence"]
    manningn = options["manningn"]
    p = options["prefx"]

    # Make some variables for temporary map names
    aspect = "%saspect%04d" % (p, o)
    flowacc = "%sflowacc%04d" % (p, o)
    flowdir = "%sflowdir%04d" % (p, o)
    flacclargenum = "%sflowacclargenum%04d" % (p, o)
    pc = "%spc%04d" % (p, o)
    tc = "%stc%04d" % (p, o)
    qsx = "%sQsx_%04d" % (p, o)
    qsy = "%sQsy_%04d" % (p, o)
    qsxdx = "%sDelta_Qsx_%04d" % (p, o)
    qsydy = "%sDelta_Qsy_%04d" % (p, o)
    rainexcess = "%s_rainfall_excess_map_%04d" % (p, o)
    tmpnetchange = "tmp%s_netchange%04d" % (pid, o)
    tmp90qle = "tmp%s_netchange_90qle%04d" % (pid, o)
    tmp10qle = "tmp%s_netchange_10qle%04d" % (pid, o)
    tmperosion = "tmp%s_erosion%04d" % (pid, o)
    tmpdep = "tmp%s_deposition%04d" % (pid, o)

    # List of temp maps to remove unless user wants to keep them all
    mapstoremove = [
        aspect,
        flowacc,
        flowdir,
        flacclargenum,
        pc,
        tc,
        rainexcess,
        tmpnetchange,
        tmp10qle,
        tmp90qle,
        tmperosion,
        tmpdep,
    ]

    # Variables that come in as a list of lists and can update with each iteration
    # masterlist = [R2,rain2,stormlength2,storms2,stormi2]
    R = s[0][m]
    rain = s[1][m]
    stormtimet = float(s[2][m]) * 3600.00  # Convert storm length to seconds
    storms = s[3][m]
    stormi = (
        float(s[4][m]) * stormtimet
    )  # Calculate the length of time at peak flow depth


    # If first iteration, use input maps. Otherwise, use maps generated from
    # previous iterations, with no iteration numbers appended to map names
    if o == 1:
        old_dem = elev
        old_soil = old_soil = "%s%s%s" % (p, outsoil, pid)
        slope = "%sslope" % (p)
        netchange = "%sED_rate" % (p)
        new_dem = "%s%s" % (p, outdem)
        new_soil = "%s%s" % (p, outsoil)
    else:
        # Iterative mode, so we will make some maps that will update
        # at each iteration to record state of landscape
        old_dem = "%s%s%04d" % (p, outdem, m)
        old_soil = "%s%s%04d" % (p, outsoil, m)
        slope = "%sslope%04d" % (p, o)
        netchange = "%sED_rate%04d" % (p, o)
        new_dem = "%s%s%04d" % (p, outdem, o)
        new_soil = "%s%s%04d" % (p, outsoil, o)
    # Grab the number of cells in the starting DEM
    numcells = grass.parse_command(
        "r.univar",
        flags="g",
        map=old_dem,
    )["n"]

    # Calculate soil as difference between surface and bedrock
    grass.mapcalc(
        "${old_soil}=${old_dem}-${initbdrk}",
        overwrite=True,
        quiet=True,
        old_soil=old_soil,
        old_dem=old_dem,
        initbdrk=initbdrk,
    )

    grass.message(
        "\n*************************\n"
        + "Iteration %s -- " % o
        + "step 1/6: calculating slope\n"
        + "*************************\n"
    )
    grass.run_command(
        "r.slope.aspect", quiet=True, elevation=old_dem, aspect=aspect, slope=slope
    )

    grass.message(
        "\n*************************\n"
        + "Iteration %s -- " % o
        + "step 2/6: calculating accumulated flow depths\n"
        + "*************************\n"
    )
    # Make map of rainfall excess (proportion each cell contributes to
    # downstrem flow) from flowcontrib. Note that if flowcontrib is a map, we
    # are just making a copy of it. This map is a percentage, but has to be
    # scaled from 0-100, because r.watershed will only allow values greater
    # than 1 as input in it's 'flow' variable. This creates a flow accumulation
    # map with large numbers, which will be divided by 100 after it is
    # made, bringing the values back down to what they should be.

    grass.mapcalc(
        "${rainexcess}=int(${flowcontrib})",
        quiet=True,
        rainexcess=rainexcess,
        flowcontrib=flowcontrib,
    )

    grass.run_command(
        "r.watershed",
        quiet=True,
        flags="a",
        elevation=old_dem,
        threshold=numcells,
        flow=rainexcess,
        accumulation=flacclargenum,
        drainage=flowdir,
        convergence=convergence,
    )

    grass.mapcalc(
        "${flowacc}=${flacclargenum}/100",
        quiet=True,
        flowacc=flowacc,
        flacclargenum=flacclargenum,
    )

    # again, do something different if we are only making an evaluation of cutoffs
    if flags["p"] is True:
        samplePoints(old_dem, aspect, slope, pc, tc, flowacc, p)

    grass.message(
        "\n*************************\n"
        + "Iteration %s -- " % o
        + "step 3/6: calculating sediment transport rates \n"
        + "*************************\n"
    )
    # Figure out which transport equation to run. All equations estimate transport capacity as kg/m.s. Note that we integrate the step to calculate the Tc in the east and west directions, to simplify the divergence calculations in the next step (i.e., to reduce the overall number of mapcalc statements and intermediate maps)

    if transp_eq == "StreamPower":
        # Stream power equation: Tc=Kt*gw*1/N*h^m*B^n
        # where: h = depth of flow = (i*A)/(0.595*t)
        # and: B = change in slope
        # GIS Implementation:
        # Tc=K*C*P*gw*(1/N)*((i*A)/(0.595*t))^m*(tan(S)^n)
        # Variables:
        # Tc=Transport Capacity [kg/meters.second]
        # K*C*P=Kt=mitigating effects of soil type, vegetation cover, and landuse practices. [unitless]
        # gw=Hydrostatic pressure of water 9810 [kg/m2.second]
        # N=Manning's coefficient ~0.3-0.6 for different types of stream channesl [unitless]
        # i=rainfall intentsity [m/rainfall event]
        # A=uplsope accumulated area per contour (cell) width [m2/m] = [m]
        # 0.595 = constant for time-lagged peak flow (assumes symmetrical unit hydrograph)
        # t=length of rainfall event [seconds]
        # S=topographic slope [degrees]
        # m = transport coefficient for upslope area [unitless]
        # n transport coefficient for slope [unitless]
        # SLOPE VERSISON
        e1 = """${qsx}=${K}*${C}*${P} * exp(${manningn}, -1) * 9810. * \
        exp((((${rain}/1000.)*${flowacc})/(0.595*${stormtimet})), \
        graph(${flowacc}, ${exp_m1a},${exp_m1b}, ${exp_m2a},${exp_m2b}) ) * \
        exp(tan(${slope}), graph(${slope}, ${exp_n1a},${exp_n1b}, ${exp_n2a},${exp_n2b}))\
        * cos(${aspect})"""

        e2 = """${qsy}=${K}*${C}*${P} * exp(${manningn}, -1) * 9810. * \
        exp((((${rain}/1000.)*${flowacc})/(0.595*${stormtimet})), \
        graph(${flowacc}, ${exp_m1a},${exp_m1b}, ${exp_m2a},${exp_m2b})) * \
        exp(tan(${slope}),  graph(${slope}, ${exp_n1a},${exp_n1b}, ${exp_n2a},${exp_n2b}))\
        * sin(${aspect})"""

    elif transp_eq == "ShearStress":
        # Shear stress equation: Tc=Kt*tau^m  (critical shear stress assumed to be 0)
        # where: tau = shear stress = gw*h*B
        # and: S =  change in slope
        # and: h = depth of flow = (i*A)/(0.595*t)
        # GIS Implmentation:
        # Tc=K*C*P*(gw*((i*A)/(0.595*t)*(tan(S))))^m
        # Variables:
        # Tc=Transport Capacity [kg/meters.second]
        # K*C*P=Kt=mitigating effects of soil type, vegetation cover, and landuse practices. [unitless]
        # gw=Hydrostatic pressure of water 9810 [kg/m2.second]
        # N=Manning's coefficient ~0.3-0.6 for different types of stream channesl [unitless]
        # i=rainfall intentsity [m/rainfall event]
        # A=uplsope accumulated area per contour (cell) width [m2/m] = [m]
        # 0.595 = constant for time-lagged peak flow (assumes symmetrical unit hydrograph)
        # t=length of rainfall event [seconds]
        # B=topographic slope [degrees]
        # m = transport coefficient (here assumed to be scaled to upslope area) [unitless]

        e1 = """${qsx}=(${K}*${C}*${P} * \
        exp(9810.*(((${rain}/1000)*${flowacc})/(0.595*${stormtimet}))*tan(${slope}), \
        graph(${flowacc}, ${exp_n1a},${exp_n1b}, ${exp_n2a},${exp_n2b}))) * \
        cos(${aspect})"""

        e2 = """${qsy}=(${K}*${C}*${P} * \
        exp(9810.*(((${rain}/1000)*${flowacc})/(0.595*${stormtimet}))*tan(${slope}), \
        graph(${flowacc}, ${exp_n1a},${exp_n1b}, ${exp_n2a},${exp_n2b}) )) * \
        sin(${aspect})"""

    elif transp_eq == "USPED":
        # USPED equation: Tc=R*K*C*P*A^m*B^n
        # where: B = change in slope
        # GIS Implementation:
        # Tc=R*K*C*P*A^m*tan(S)^n
        # Variables:
        # Tc=Transport Capacity [kg/meters.second]
        # R=Rainfall intensivity factor [MJ.mm/ha.h.yr]
        # A=uplsope accumulated area per contour (cell) width [m2/m] = [m]
        # S=topographic slope [degrees]
        # m = transport coefficient for upslope area [unitless]
        # n transport coefficient for slope [unitless]

        e1 = """${qsx}=((${R}*${K}*${C}*${P}*\
        exp((${flowacc}*${res}),graph(${flowacc}, ${exp_m1a},${exp_m1b}, ${exp_m2a},${exp_m2b}))*\
        exp(sin(${slope}), graph(${slope}, ${exp_n1a},${exp_n1b}, ${exp_n2a},${exp_n2b})))\
        * cos(${aspect}))"""

        e2 = """${qsy}=((${R}*${K}*${C}*${P}*\
        exp((${flowacc}*${res}),graph(${flowacc}, ${exp_m1a},${exp_m1b}, ${exp_m2a},${exp_m2b}))*\
        exp(sin(${slope}), graph(${slope}, ${exp_n1a},${exp_n1b}, ${exp_n2a},${exp_n2b})))\
        * sin(${aspect}))"""

    else:
        grass.fatal(
            'You have entered a non-viable tranport equation name. Please ensure option "transp_eq" is one of "StreamPower," "ShearStress," or "USPED."'
        )

    # Actually do the mapcalc statement for chosen transport equation
    x = grass.mapcalc_start(
        e1,
        quiet=True,
        qsx=qsx,
        slope=slope,
        aspect=aspect,
        R=R,
        K=K,
        C=C,
        P=P,
        res=res,
        flowacc=flowacc,
        rain=rain,
        stormtimet=stormtimet,
        stormi=stormi,
        exp_m1a=exp_m[0],
        exp_m1b=exp_m[1],
        exp_m2a=exp_m[2],
        exp_m2b=exp_m[3],
        exp_n1a=exp_n[0],
        exp_n1b=exp_n[1],
        exp_n2a=exp_n[2],
        exp_n2b=exp_n[3],
        manningn=manningn,
    )

    y = grass.mapcalc_start(
        e2,
        quiet=True,
        qsy=qsy,
        slope=slope,
        aspect=aspect,
        R=R,
        K=K,
        C=C,
        P=P,
        res=res,
        flowacc=flowacc,
        rain=rain,
        stormtimet=stormtimet,
        stormi=stormi,
        exp_m1a=exp_m[0],
        exp_m1b=exp_m[1],
        exp_m2a=exp_m[2],
        exp_m2b=exp_m[3],
        exp_n1a=exp_n[0],
        exp_n1b=exp_n[1],
        exp_n2a=exp_n[2],
        exp_n2b=exp_n[3],
        manningn=manningn,
    )
    x.wait()
    y.wait()

    grass.message(
        "\n*************************\n"
        + "Iteration %s -- " % o
        + "step 4/6: calculating divergence/difference of sediment transport and the actual amount of erosion or deposition in vertical meters/cell/year\n"
        + "*************************\n"
    )

    # Taking divergence of transport capacity Tc converts kg/m.s to kg/m2.s
    sax = grass.start_command("r.slope.aspect", quiet=True, elevation=qsx, dx=qsxdx)
    say = grass.start_command("r.slope.aspect", quiet=True, elevation=qsy, dy=qsydy)

    sax.wait()
    say.wait()

    # Now convert output of divergence to calculated erosion and deposition in
    # vertical meters of elevation change. Add back the divergence in EW and NS
    # directions. Units are in kg/m2.s, so start by dividing by soil density
    # [kg/m3] to get m/s elevation change (for USPED that is m/year already,
    # but not for the shear stress or stream power).
    # For shear stress and stream power, also multiply by the number
    # of seconds at peak flow depth (stormi) and then by the number of erosive
    # storms per year to get m/year elevation change.
    if transp_eq == "USPED":
        ed = """${netchange}=((${qsxdx}+${qsydy})/${sdensity})"""
        grass.mapcalc(
            ed,
            quiet=True,
            netchange=tmpnetchange,
            qsxdx=qsxdx,
            qsydy=qsydy,
            sdensity=sdensity,
        )
    else:
        ed = """${netchange}=((${qsxdx}+${qsydy})/${sdensity})*${stormi}*${storms}"""
        grass.mapcalc(
            ed,
            quiet=True,
            netchange=tmpnetchange,
            qsxdx=qsxdx,
            qsydy=qsydy,
            sdensity=sdensity,
            stormi=stormi,
            storms=storms,
        )
    # Apply smoothing to the output to remove some spikes. Map will only be smoothed for values above the 90th quantile and below the 10th quantile (i.e., only extreme values will be smoothed)
    if flags["m"] is True:
        a = grass.start_command(
            "r.neighbors",
            quiet=True,
            input=tmpnetchange,
            output=tmp10qle,
            method="quantile",
            size=5,
            quantile=0.1,
        )
        b = grass.start_command(
            "r.neighbors",
            quiet=True,
            input=tmpnetchange,
            output=tmp90qle,
            method="quantile",
            size=5,
            quantile=0.9,
        )
        a.wait()
        b.wait()
        smoother = """${netchange}=if(${tmpnetchange}<${tmp10qle}, ${tmp10qle}, if(${tmpnetchange}>${tmp90qle}, ${tmp90qle}, ${tmpnetchange}))"""
        grass.mapcalc(
            smoother,
            quiet=True,
            netchange=netchange,
            tmpnetchange=tmpnetchange,
            tmp90qle=tmp90qle,
            tmp10qle=tmp10qle,
        )
    else:
        grass.run_command("g.rename", quiet=True, raster=tmpnetchange + "," + netchange)

    grass.message(
        "\n*************************\n"
        + "Iteration %s -- " % o
        + "step 5/6: calculating terrain evolution and new soil depths\n"
        + " *************************\n"
    )
    # Compute elevation changes: addition of ED change to old DEM.
    # This mapcalc statement first checks the amount of erodable soil in a given
    # cell against the amount of erosion calculated, and keeps the cell from
    # eroding past this amount (if there is soil, then if the amount of erosion
    # is more than the amount of soil, just remove all the soil and stop, else
    # remove the amount of caclulated erosion. It also runs an error catch that
    # checks to make sure that soil depth is not negative (could happen, I
    # suppose), and if it is, corrects it). Finally, do patch-job to catch the
    # shrinking edge problem (the edge cells have no upstream cell, so get
    # turned null in the calculations in step 4)

    e = """${new_dem} = eval(x=if(${old_soil} > 0.0 && (-1*${netchange}) <= ${old_soil}, ${netchange}, \
           if((-1*${netchange}) > ${old_soil}, (-1*${old_soil}), 0)), \
           y=(${old_dem} + x), if(isnull(y), ${old_dem}, y))"""
    grass.mapcalc(
        e,
        quiet=True,
        new_dem=new_dem,
        old_soil=old_soil,
        old_dem=old_dem,
        netchange=netchange,
    )

    # Calculate new soil depths by subtracting initial bedrock elevations from
    # the new DEM.
    e = """${new_soil} = if((${new_dem} - ${initbdrk}) < 0, 0, (${new_dem} - ${initbdrk}))"""
    grass.mapcalc(e, quiet=True, new_soil=new_soil, new_dem=new_dem, initbdrk=initbdrk)

    # Set colors for elevation, soil, and ED maps
    grass.run_command("r.colors", quiet=True, map=new_dem, color="srtm")

    sdcolors = ["100% 0:249:47", "20% 78:151:211", "6% 194:84:171", "0% 227:174:217"]
    sdc = grass.feed_command("r.colors", quiet=True, map=new_soil, rules="-")
    sdc.stdin.write("\n".join(sdcolors).encode('utf-8'))
    sdc.stdin.close()

    nccolors = [
        "100 127:0:255",
        "1 0:0:255",
        ".1 0:255:0",
        "0.001 152:251:152",
        "0 250:250:250",
        "-0.001 255:255:50",
        "-.1 255:127:0",
        "-1 255:0:0",
        "-100 127:0:255",
    ]
    ncc = grass.feed_command("r.colors", quiet=True, map=netchange, rules="-")
    ncc.stdin.write("\n".join(nccolors).encode('utf-8'))
    ncc.stdin.close()

    sdc.wait()
    ncc.wait()

    grass.message(
        "\n*************************\n"
        + "Iteration %s -- " % o
        + "step 6/6: writing stats to output file\n"
        + "*************************\n"
    )
    # Make some temp maps of just erosion rate and just deposition rates
    e = """${tmperosion}=if(${netchange} < -0, ${netchange}, null())"""
    ero1 = grass.mapcalc_start(
        e, quiet=True, tmperosion=tmperosion, netchange=netchange
    )

    e = """${tmpdep}=if(${netchange} > 0, ${netchange}, null())"""
    dep1 = grass.mapcalc_start(e, quiet=True, tmpdep=tmpdep, netchange=netchange)

    ero1.wait()
    dep1.wait()

    # Grab the stats from these temp files and save them to dictionaries
    erosstats = grass.parse_command(
        "r.univar", flags="ge", percentile="1", map=tmperosion
    )
    depostats = grass.parse_command("r.univar", flags="ge", percentile="99", map=tmpdep)

    # Finish gathering stats (just need the soil depth stats now)
    soilstats = grass.parse_command(
        "r.univar", flags="ge", map=new_soil, percentile="99"
    )

    # Write stats to a new line in the stats file
    # HEADER of the file should be: ',,Mean Values,,,,Standard Deviations,,,,Totals,,,Additional Stats\nIteration,,Mean Erosion,Mean Deposition,Mean Soil Depth,,Standard Deviation Erosion,Standard Deviation Deposition,Standard Deviation Soil Depth,,Total Sediment Eroded,Total Sediment Deposited,,Minimum Erosion,First Quartile Erosion,Median Erosion,Third Quartile Erosion,Maximum Erosion,Original Un-smoothed Maximum Erosion,,Minimum Deposition,First Quartile Deposition,Median Deposition,Third Quartile Deposition,Maximum Deposition,Original Un-smoothed Maximum Deposition,,Minimum Soil Depth,First Quartile Soil Depth,Median Soil Depth,Third Quartile Soil Depth,Maximum Soil Depth'

    f.write(
        "\n%s" % o
        + ",,"
        + erosstats["mean"]
        + ","
        + depostats["mean"]
        + ","
        + soilstats["mean"]
        + ",,"
        + erosstats["stddev"]
        + ","
        + depostats["stddev"]
        + ","
        + soilstats["stddev"]
        + ",,"
        + erosstats["sum"]
        + ","
        + depostats["sum"]
        + ",,"
        + erosstats["max"]
        + ","
        + erosstats["third_quartile"]
        + ","
        + erosstats["median"]
        + ","
        + erosstats["first_quartile"]
        + ","
        + erosstats["min"]
        + ","
        + depostats["min"]
        + ","
        + depostats["first_quartile"]
        + ","
        + depostats["median"]
        + ","
        + depostats["third_quartile"]
        + ","
        + depostats["max"]
        + ","
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

    # Cleanup temporary files
    if flags["k"] is True:
        grass.message("\nTemporary maps will NOT be deleted!!!!\n")
    else:
        grass.message("\nCleaning up temporary maps...\n\n")
        # Check all the flag options, and add to list of maps to delete
        if flags["s"] is True:
            grass.message("Keeping Slope map.")
        else:
            mapstoremove.append(slope)
        if flags["d"] is True:
            grass.message("Not keeping Soil Depth map.")
            mapstoremove.append(old_soil)
            # Check if this is the last year and remove the "new-soil" map too
            if o == int(options["number"]):
                mapstoremove.append(new_soil)
        else:
            # Check if this is the first year, and if so, remove the temporary initial soil depths map
            if o <= 1:
                grass.message(("%s%s%04d" % (p, outsoil, m)))
                mapstoremove.append("%s%s%04d" % (p, outsoil, m))
        if flags["e"] is True:
            grass.message("Keeping delta Transport Capacity (divergence) maps.")
        else:
            mapstoremove.extend([qsxdx, qsydy])
        if flags["t"] is True:
            grass.message("Keeping Transport Capacity maps.")
        else:
            mapstoremove.extend([qsx, qsy])
        if flags["r"] is True:
            grass.message("Not keeping an Erosion and Deposition rate map.")
            mapstoremove.append(netchange)
        if o == 1:
            mapstoremove.append(old_soil)
        if len(mapstoremove) == 0:
            pass
        else:
            grass.run_command(
                "g.remove",
                quiet=True,
                flags="f",
                type="rast",
                name=",".join(mapstoremove),
            )

    grass.message(
        "\n*************************\n"
        + "Done with Iteration %s " % o
        + "\n*************************\n"
    )
    return 0


def climfile(d, y, years):
    """
    Check a climate variable and read in from text if needed.
    Takes a variable name to check and returns as a parsed list of variables
    If there is a climate file, values will be read in for each year.
    If not, the value entered will be applied to all years
    d = climate variable to be parsed
    y = column containing that climate variable in the input file
    years = number of years of the simulation
    """
    l = []
    try:
        d1 = float(d)
        for year in range(int(years)):
            l.append(d1)
        return l
    except:
        with open(d, "rU") as f:
            for line in f:
                l.append(line.split(",")[y])

        # Check for text header and remove if present
        try:
            float(l[0])
        except:
            del l[0]

        # Throw a warning if there aren't enough values in the column
        if len(l) != int(years):
            grass.fatal(
                "Number of rows of rainfall data in your climate file\ndo not match the number of iterations you wish to run.\n Please ensure that these numbers match and try again"
            )
            sys.exit(1)
        return l


def samplePoints(old_dem, aspect, slope, pc, tc, flowacc, p):
    # Create terrain morphology maps
    grass.run_command(
        "r.slope.aspect",
        quiet=True,
        elevation=old_dem,
        aspect=aspect,
        slope=slope,
        pcurv=pc,
        tcurv=tc,
    )

    # Generate random vector points and sample terrain to determine cutoff values for flow accumulation coefficients
    grass.message(
        "GATHERING STATISTICS FOR DETERMINING CUTOFF VALUES\n-------------------------------------------------\n1) Calculating slope and curvatures"
    )

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
        "r.random", quiet=True, input=flowacc, cover=pc, npoints=numpts, vector=vout
    )

    grass.run_command(
        "v.db.renamecolumn", quiet=True, map=vout, column="value,Flow_acc"
    )
    grass.run_command(
        "v.db.renamecolumn", quiet=True, map=vout, column="covervalue,Princ_curv"
    )
    grass.run_command(
        "v.db.addcolumn",
        quiet=True,
        map=vout,
        columns="Tang_curv double precision, Slope double precision",
    )
    grass.run_command(
        "v.what.rast", quiet=True, map=vout, raster=tc, column="Tang_curv"
    )
    grass.run_command("v.what.rast", quiet=True, map=vout, raster=slope, column="Slope")

    if flags["k"] is True:
        grass.message(
            "--Keeping the created maps (Flow Accumulation, Slope, Principle Curvature, Tangential Curvature)"
        )
    else:
        grass.message("6) Cleaning up...")
        grass.run_command(
            "g.remove",
            quiet=True,
            flags="f",
            type="rast",
            name=slope + "," + pc + "," + tc + "," + flowacc,
        )

    grass.message(
        'FINISHED. \nRandom sample points map "%s" created successfully.\n' % vout
    )

    sys.exit(0)


# Here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    options, flags = grass.parser()
    main()
