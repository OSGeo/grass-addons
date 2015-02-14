#!/usr/bin/env python
#
############################################################################
#
# MODULE:       	r.viewshed.cva.py
# AUTHOR(S):	Isaac Ullah
# PURPOSE:	 Undertakes a "cumulative viewshed analysis" using a vector points map as input "viewing" locations, using r.viewshed to calculate the individual viewsheds.
# COPYRIGHT:	(C) 2015 by Isaac Ullah
# REFERENCES:    r.viewshed
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################


#%Module
#%  description: Undertakes a "cumulative viewshed analysis" using a vector points map as input "viewing" locations, using r.viewshed to calculate the individual viewsheds.
#%End

#%option
#% key: elev
#% type: string
#% gisprompt: new,cell,raster
#% description: Input elevation map (DEM)
#% required : yes
#%END

#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% description: Output CVA raster
#% required : yes
#%END

#%option
#% key: vect
#% type: string
#% gisprompt: new,vector,vector
#% description: Name of input vector points map containg the set of sites for this analysis.
#% required : yes
#%END

#%option
#% key: observer_elevation
#% type: string
#% description: Height of observation points off the ground
#%answer: 0.0
#% required : yes
#%END

#%option
#% key: target_elevation
#% type: string
#% description: Height of target areas off the ground
#%answer: 1.75
#% required : yes
#%END

#%option
#% key: max_distance
#% type: string
#% description: Maximum viewing distance (-1 = infinity)
#%answer: -1
#% required : yes
#%END

#%option
#% key: memory
#% type: string
#% description: Amount of memory to use (in MB)
#%answer: 1500
#% required : yes
#%END

#%option
#% key: refraction_coeff
#% type: string
#% description: Refraction coefficient (with flag -r)
#%answer: 0.14286
#% required : no
#%END


#%flag
#% key: k
#% description: -k Keep all interim viewshed maps produced by the routine (maps will be named "vshed_'name'", where 'name' is the value in "name_column" for each input point)
#%END

#%flag
#% key: c
#% description: -c Consider the curvature of the earth (current ellipsoid)
#%END

#%flag
#% key: r
#% description: -r Consider the effect of atmospheric refraction
#%END

#%flag
#% key: b
#% description: -b   Output format is {0 (invisible) 1 (visible)}
#%END

#%flag
#% key: e
#% description:  -e   Output format is invisible = NULL, else current elev - viewpoint_elev
#%END



import sys
import os
grass_install_tree = os.getenv('GISBASE')
sys.path.append(grass_install_tree + os.sep + 'etc' + os.sep + 'python')
import grass.script as grass


#main block of code starts here
def main():
    #bring in input variables
    elev = options["elev"]
    vect = options["vect"]
    observer_elevation =options["observer_elevation"]
    target_elevation = options['target_elevation']
    max_distance = options["max_distance"]
    memory = options["memory"]
    refraction_coeff = options["refraction_coeff"]
    out = options["output"]
    #assemble flag string
    if flags['r'] is True:
        f1 = "r"
    else:
        f1 = ""
    if flags['c'] is True:
        f2 = "c"
    else:
        f2 = ""
    if flags['b'] is True:
        f3 = "b"
    else:
        f3 = ""
    if flags['e'] is True:
        f4 = "e"
    else:
        f4 = ""
    flagstring = f1 + f2 + f3 +f4
    #make a tempfile, and write out the coords from the vector map.
    tmp1 = grass.tempfile()
    grass.run_command("v.out.ascii", flags = 'r', input = vect, type = "point", output = tmp1, format = "point", separator = ",")
    # note that the "r" flag will constrain to points in the current geographic region.
    grass.message("Note that the routine is constrained to points in the current geographic region.")
    #read the temp file back in, and parse it up.
    f = open(tmp1, 'r')
    masterlist = []
    for line in f.readlines():
        masterlist.append(line.strip('\n').split(','))
    f.close() #close the file
    #now, loop through the master list and run r.viewshed for each of the sites, and append the viewsheds to a list (so we can work with them later)
    vshed_list = []
    for site in masterlist:
        grass.message('Calculating viewshed for location %s,%s (point name = %s)\n' % (site[0], site[1], site[2]))
        tempry = "vshed_%s" % site[2]
        vshed_list.append(tempry)
        grass.run_command("r.viewshed", quiet = "True", overwrite = grass.overwrite(), flags = flagstring,  input = elev, output = tempry, coordinates = site[0] + "," + site[1], observer_elevation = observer_elevation, target_elevation = target_elevation, max_distance = max_distance, memory = memory,  refraction_coeff = refraction_coeff)
    #now make a mapcalc statement to add all the viewsheds together to make the outout cumulative viewsheds map
    grass.message("Calculating \"Cumulative Viewshed\" map")
    #grass.mapcalc("${output}=${command_string}", quiet = "True", output = out, command_string = ("+").join(vshed_list))
    grass.run_command("r.series", quiet = "True", overwrite = grass.overwrite(), input = (",").join(vshed_list), output = out, method = "count")
    #Clean up temporary maps, if requested
    if os.getenv('GIS_FLAG_k') == '1':
        grass.message("Temporary viewshed maps will not removed")
    else:
        grass.message("Removing temporary viewshed maps")
        grass.run_command("g.remove",  quiet = "True", flags = 'f', type = 'raster', name = (",").join(vshed_list))
    return

# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    options, flags = grass.parser()
    main()
    exit(0)
