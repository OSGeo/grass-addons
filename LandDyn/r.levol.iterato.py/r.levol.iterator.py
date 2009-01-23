#!/usr/bin/python

############################################################################
#
# MODULE:       r.levol.it.cfct.py
# AUTHOR(S):    iullah
# COPYRIGHT:    (C) 2007 GRASS Development Team/iullah
#
#  description: Create raster maps of net erosion/depostion, the modified terrain surface (DEM) after net erosion/deposition using the USPED equation, bedrock elevations after soil production, and soil depth maps. This module uses appropriate flow on different landforms by default; however, singular flow regimes can be chosen instead. THIS SCRIPT WILL PRODUCE MANY TEMPORARY MAPS AND REQUIRES A LOT OF FREE FILE SPACE! Note that all flags are disabled! Currently flags -z -b -n -f are hard coded to run by default.

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
#% description: Create raster maps of net erosion/depostion, the modified terrain surface (DEM) after net erosion/deposition using the USPED equation, bedrock elevations after soil production, and soil depth maps. This module uses appropriate flow on different landforms by default; however, singular flow regimes can be chosen instead. THIS SCRIPT WILL PRODUCE MANY TEMPORARY MAPS AND REQUIRES A LOT OF FREE FILE SPACE! Note that all flags are disabled! Currently flags -z -b -n -f are hard coded to run by default.
#%End
#%Flag
#% key: l
#% description: -l Do not output maps of soil depths
#% guisection: Input
#%End
#%Flag
#% key: k
#% description: -k Keep all intermediate files as well
#% guisection: Input
#%End
#%Flag
#% key: e
#% description: -e Keep initial soil depths map
#% guisection: Input
#%End
#%Flag
#% key: z
#% description: -z Keep region zoomed to output maps
#% answer: 1
#% guisection: Input
#%End
#%Flag
#% key: b
#% description: -b Use static bedrock elavations (do not create new soil)
#% answer: 1
#% guisection: Input
#%End
#%Flag
#% key: y
#% description: -y Don't smooth the map (faster, but spikes in erosion/deposition may result)
#% guisection: Smoothing_Filter
#%End
#%Flag
#% key: n
#% description: -n Output maps of net erosion/deposition for ever year
#% answer: 1
#% guisection: Statistics
#%End
#%Flag
#% key: c
#% description: -c Output cumulative erosion/deposition map from data for all iterations
#% guisection: Statistics
#%End
#%Flag
#% key: m
#% description: -m Output mean erosion/depostition map from data for all iterations (must check -n as well)
#% guisection: Statistics
#%End
#%Flag
#% key: t
#% description: -t Output standard deviation of erosion/depostition map from data for all iterations (must check -n as well)
#% guisection: Statistics
#%End
#%Flag
#% key: s
#% description: -s Output mean soil depths map from data for all iterations
#% guisection: Statistics
#%End
#%Flag
#% key: v
#% description: -v Output standard deviation soil depths map from data for all iterations
#% guisection: Statistics
#%End
#%Flag
#% key: a
#% description: -a Output maximum soil depths map from data for all iterations
#% guisection: Statistics
#%End
#%Flag
#% key: u
#% description: -u Output minimum soil depths map from data for all iterations
#% guisection: Statistics
#%End
#%Flag
#% key: w
#% description: -w Calcuate for only sheetwash across entire map
#% guisection: Flow_type
#%End
#%Flag
#% key: r
#% description: -r Calcuate for only channelized flow across entire map
#% guisection: Flow_type
#%End
#%Flag
#% key: d
#% description: -d Calcuate for only diffusive flow (soil creep) across entire map
#% guisection: Flow_type
#%End
#%Flag
#% key: f
#% description: -f Use r.terrflow instead of r.flow to calculate flow accumulation (better for massive grids)
#% guisection: Flow_type
#%End
#%Option
#% key: elev
#% type: string
#% required: yes
#% multiple: no
#% description: Input elevation map (DEM)
#% gisprompt: old,cell,raster
#% guisection: Input
#%End
#%Option
#% key: initbdrk
#% type: string
#% required: yes
#% multiple: no
#% description: Initial bedrock elevations map (for first iteration only)
#% answer:
#% gisprompt: old,cell,raster
#% guisection: Input
#%End
#%Option
#% key: prefx
#% type: string
#% required: yes
#% multiple: no
#% description: Prefix for all output maps
#% answer: usped_
#% guisection: Input
#%End
#%Option
#% key: outdem
#% type: string
#% required: yes
#% multiple: no
#% description: Name stem for output elevation map(s) (preceded by prefix and followed by numerical suffix if more than one iteration)
#% answer: elevation
#% gisprompt: string
#% guisection: Input
#%End
#%Option
#% key: outsoil
#% type: string
#% required: yes
#% multiple: no
#% description: Name stem for the output soil depth map(s) (preceded by prefix and followed by numerical suffix if more than one iteration)
#% answer: soildepth
#% gisprompt: string
#% guisection: Input
#%End
#%Option
#% key: outbdrk
#% type: string
#% required: no
#% multiple: no
#% description: Name stem for the output bedrock map(s) (required if the -b option is NOT checked; preceded by prefix and followed by numerical suffix if more than one iteration)
#% answer: bedrock
#% gisprompt: string
#% guisection: Input
#%End
#%Option
#% key: statsout
#% type: string
#% gisprompt: string
#% description: Name for the statsout text file (optional, if none provided, a default name will be used)
#% required: no
#% guisection: Input
#%end
#%flag
#% key: g
#% description: -g do not put header on statsout text file and always append data, even if file already exists (useful if script is being run by an outside program)
#%answer: 1
#% guisection: Input
#%end
#%Option
#% key: R
#% type: string
#% required: yes
#% multiple: no
#% description: Rainfall (R factor) constant (AVERAGE FOR WHOLE MAP AREA)
#% answer: 5
#% guisection: Variables
#%End
#%Option
#% key: K
#% type: string
#% required: yes
#% multiple: no
#% description: Soil erodability index (K factor) map or constant
#% answer: 0.32
#% gisprompt: old,cell,raster
#% guisection: Variables
#%End
#%option
#% key: sdensity
#% type: string
#% gisprompt: old,cell,raster
#% description: Soil density constant (for conversion from mass to volume)
#% answer: 1.2184
#% required : yes
#% guisection: Variables
#%end
#%Option
#% key: C
#% type: string
#% required: yes
#% multiple: no
#% description: Prefix for stack of landcover index (C factor) maps (leave off #'s)
#% answer: 0.01
#% gisprompt: old,cell,raster
#% guisection: Variables
#%End
#%Option
#% key: kappa
#% type: string
#% required: yes
#% multiple: no
#% description: Hillslope diffusion (Kappa) rate map or constant (meters per kiloyear)
#% answer: 1
#% gisprompt: old,cell,raster
#% guisection: Variables
#%End
#%Option
#% key: cutoff1
#% type: string
#% required: yes
#% multiple: no
#% description: Flow accumultion breakpoint value for shift from diffusion to overland flow (number of cells)
#% answer: 4
#% guisection: Variables
#%End
#%Option
#% key: cutoff2
#% type: string
#% required: yes
#% multiple: no
#% description: Flow accumultion breakpoint value for shift from overland flow to channelized flow (number of cells)
#% answer: 50
#% guisection: Variables
#%End
#%Option
#% key: number
#% type: integer
#% required: yes
#% multiple: no
#% description: number of iterations to run
#% answer: 1
#% guisection: Variables
#%End
#%Option
#% key: nbhood
#% type: string
#% required: yes
#% multiple: no
#% options: 1,3,5,7,9,11,13,15,17,19,21,23,25
#% description: Band-pass filter neighborhood size
#% answer: 7
#% guisection: Smoothing_Filter
#%End
#%Option
#% key: method
#% type: string
#% required: yes
#% multiple: no
#% options: average,median,mode
#% description: Neighborhood smoothing method
#% answer: median
#% guisection: Smoothing_Filter
#%End

import sys
import os
import subprocess

def grass_print(m):
	subprocess.Popen('g.message message="%s"' % m, shell='bash').wait()
	return


def main(n, o, p, q):
	initbdrk = os.getenv("GIS_OPT_initbdrk")
	outbdrk = "%s_%s" % (os.getenv("GIS_OPT_outbdrk"), o)
	outdem = "%s_%s" % (os.getenv("GIS_OPT_outdem"), o)
	outsoil = "%s_%s" % (os.getenv("GIS_OPT_outsoil"), o)
	R = os.getenv("GIS_OPT_R")
	K = os.getenv("GIS_OPT_K")
	sdensity = os.getenv("GIS_OPT_sdensity")
	C = "%s_%s" % (os.getenv("GIS_OPT_C"), o)
	kappa = os.getenv("GIS_OPT_kappa")
	aplpha = os.getenv("GIS_OPT_method")
	sigma = os.getenv("GIS_OPT_sigma")
	nbhood = os.getenv("GIS_OPT_nbhood")
	cutoff1 = os.getenv("GIS_OPT_cutoff1")
	cutoff2 = os.getenv("GIS_OPT_cutoff2")
	method = os.getenv("GIS_OPT_method")
	years = os.getenv("GIS_OPT_number")
	
	letters = list('lkezbyncmtsvauwrdfg')
	flags = []
	for letter in letters:
		flag = "GIS_FLAG_%s" % (letter)
		if ( os.getenv(flag) == "1" ):
			flags.append("-" + letter)
	
	conditions = ["elev=%s" % n, "initbdrk=%s" % initbdrk, "prefx=%s" % p, "outdem=%s" % outdem,\
	 "outsoil=%s" % outsoil, "outbdrk=%s" % outbdrk, "statsout=%s" % q, "R=%s" % R, "K=%s" % K, "sdensity=%s" % sdensity, "C=%s" % C,\
	  "kappa=%s" % kappa, "cutoff1=%s" % cutoff1, "cutoff2=%s" % cutoff2, "number=1", "nbhood=%s" % nbhood,\
	   "method=%s" % method]
	sep = ' '
	flags_string = sep.join(flags)
	variables_string = sep.join(conditions)
	command_string = "r.landscape.evol.fast %s %s" % (flags_string, variables_string)

	#command = ["r.landscape.evol"]
	#command.extend(flags)
	#command.extend(conditions)
	#print command
	subprocess.Popen(command_string, shell='bash').wait()
	
	return	grass_print("Command for previous run: '"'%s'"'" % command_string)

if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
	outdem = os.getenv("GIS_OPT_outdem")
	years = os.getenv("GIS_OPT_number")
	prefx = os.getenv("GIS_OPT_prefx")
	if os.getenv("GIS_OPT_statsout") == "":
		p = subprocess.Popen("g.gisenv get=MAPSET", stdout=subprocess.PIPE, shell='bash')
		out = p.stdout.read()
		mapset = out.strip()
		statsout = '%s_%s_lsevol_stats.txt' % (mapset, prefx)
		f = file('%s_%s_lsevol_stats.txt' % (mapset, prefx), 'wt')
	else:
		statsout = os.getenv("GIS_OPT_statsout")
		f = file(os.getenv("GIS_OPT_statsout"), 'wt')
	grass_print("Total number of Python iterated iterations to be run is %s years" % years)
	f.write('Year,,Mean Erosion,Max Erosion,Min Erosion,99th Percentile Erosion,,Mean Deposition,Min Deposition,Max Deposition,99th Percentile Deposition,,Mean Soil Depth,Min Soil Depth,Max Soil Depth,99th Percentile Soil Depth')
	f.close()
	for x in range(int(years)):
		grass_print("REAL YEAR = %s" % (x + 1))
		if ( x == 0 ):
			elev_in = os.getenv("GIS_OPT_elev")
		
		else:
			elev_in = "%s%s_%s" % (prefx, outdem, x)

		main(elev_in, (x + 1), prefx, statsout);
		
grass_print("All Python iterated iterations complete! Have a nice day!")


