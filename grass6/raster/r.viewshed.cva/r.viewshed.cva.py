#!/usr/bin/python
#
############################################################################
#
# MODULE:       	r.viewshed.cva.py
# AUTHOR(S):	Isaac Ullah
# PURPOSE:		Undertakes a "cumulative viewshed analysis" using a vector points map as input "viewing" locations, and utilizing the faster r.viewshed instead of r.los.
# COPYRIGHT:	(C) 2013 by Isaac Ullah
# REFERENCES:    r.viewshed
#			This program is free software under the GNU General Public
#			License (>=v2). Read the file COPYING that comes with GRASS
#			for details.
#
#############################################################################


#%Module
#%  description: Undertakes a "cumulative viewshed analysis" using a vector points map as input "viewing" locations, and the faster r.viewshed instead of r.los. NOTE: this routine requires the grass addon module r.viewshed, which can be added with g.extention
#%End

#%option
#% key: elev
#% type: string
#% gisprompt: old,cell,raster
#% description: Input elevation map (DEM)
#% required : yes
#%END 

#%option
#% key: output
#% type: string
#% gisprompt: old,cell,raster
#% description: Output CVA raster
#% required : yes
#%END

#%option
#% key: vect
#% type: string
#% gisprompt: old,vector,vector
#% description: Name of input vector points map containg the set of sites for this analysis.
#% required : yes
#%END

#%option
#% key: x_column
#% type: string
#% description: Column containing x values for site coordinates
#% required : yes
#%END

#%option
#% key: y_column
#% type: string
#% description: Column containing y values for site coordinates
#% required : yes
#%END

#%option
#% key: name_column
#% type: string
#% description: Column with unique identifiers for each point in input vector map (e.g. "cat" column)
#% required : yes
#%END

#%option
#% key: obs_elev
#% type: string
#% description: Height of observation points off the ground
#%answer: 0.0
#% required : yes
#%END

#%option
#% key: tgt_elev
#% type: string
#% description: Height of target areas off the ground
#%answer: 1.75
#% required : yes
#%END

#%option
#% key: max_dist
#% type: string
#% description: Maximum viewing distance (-1 = infinity)
#%answer: -1
#% required : yes
#%END

#%option
#% key: mem
#% type: string
#% description: Amount of memory to use (in MB)
#%answer: 1500
#% required : yes
#%END

#%option
#% key: refraction_coef
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
import subprocess
import tempfile
import random
grass_install_tree = os.getenv('GISBASE')
sys.path.append(grass_install_tree + os.sep + 'etc' + os.sep + 'python')
import grass.script as grass


#main block of code starts here
def main():
    #bring in input variables
    elev = os.getenv("GIS_OPT_elev")
    out = os.getenv("GIS_OPT_output")
    vect = os.getenv("GIS_OPT_vect")
    xcol = os.getenv("GIS_OPT_x_column")
    ycol = os.getenv("GIS_OPT_y_column")
    namecol = os.getenv("GIS_OPT_name_column")
    obs_elev = os.getenv("GIS_OPT_obs_elev")
    tgt_elev = os.getenv("GIS_OPT_tgt_elev")
    max_dist = os.getenv("GIS_OPT_max_dist")
    mem = os.getenv("GIS_OPT_mem")
    refraction_coef = os.getenv("GIS_OPT_refraction_coef")
    #assemble flag string
    if os.getenv('GIS_FLAG_r') == '1':
        f1 = "r"
    else:
        f1 = ""
    if os.getenv('GIS_FLAG_c') == '1':
        f2 = "c"
    else:
        f2 = ""
    if os.getenv('GIS_FLAG_b') == '1':
        f3 = "b"
    else:
        f3 = ""
    if os.getenv('GIS_FLAG_e') == '1':
        f4 = "e"
    else:
        f4 = ""
    flagstring = f1 + f2 + f3 +f4
    #read in info from the table of the vector sites map, and parse it into a list of lists of info for each site
    s1 = grass.read_command("v.db.select", quiet = "True", map = vect, columns = xcol + "," + ycol + "," + namecol, fs = ",", nv = "False").strip()
    masterlist = []
    for item in s1.split("\n"):
        masterlist.append(item.strip("\n").split(","))
    #the first row is the column names, so pop that out of our master list
    index = masterlist.pop(0)
    #now, loop through the master list and run r.viewshed for each of the sites, and append the viewsheds to a list (so we can work with them later)
    vshed_list = []
    for site in masterlist:
        grass.message('Calculating viewshed for location %s,%s (point name = %s)\n' % (site[0], site[1], site[2]))
        tempry = "vshed_%s" % site[2]
        vshed_list.append(tempry)
        grass.run_command("r.viewshed", quiet = "True",  flags = flagstring,  input = elev, output = tempry, coordinate = site[0] + "," + site[1], obs_elev = obs_elev, tgt_elev = tgt_elev, max_dist = max_dist, mem = mem,  refraction_coef = refraction_coef)
    #now make a mapcalc statement to add all the viewsheds together to make the outout cumulative viewsheds map
    grass.message("Calculating \"Cumulative Viewshed\" map")
    #grass.mapcalc("${output}=${command_string}", quiet = "True", output = out, command_string = ("+").join(vshed_list))
    grass.run_command("r.series", quiet = "True", input = (",").join(vshed_list), output = out, method = "count")
    #Clean up temporary maps, if requested
    if os.getenv('GIS_FLAG_k') == '1':
        grass.message("Temporary viewshed maps will not removed")
    else:
        grass.message("Removing temporary viewshed maps")
        grass.run_command("g.remove",  quiet = "True",  rast = (",").join(vshed_list))
    return

# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()

