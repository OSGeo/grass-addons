#!/usr/bin/env python


############################################################################
#
# MODULE:       	r.accumulate.erdep.py
# AUTHOR(S):		Isaac Ullah, Arizona State University
# PURPOSE:		Takes the output "netchange" maps and adds them chronologically
#			to make a series showing the "to-date" net change for each year. Good for animations.
# ACKNOWLEDGEMENTS:	National Science Foundation Grant #BCS0410269 
# COPYRIGHT:		(C) 2007 by Isaac Ullah, Michael Barton, Arizona State University
#			This program is free software under the GNU General Public
#			License (>=v2). Read the file COPYING that comes with GRASS
#			for details.
#
#############################################################################


#%Module
#%  description: Takes the output "netchange" maps and adds them chronologically to make a series showing the "to-date" net change for each year. Good for animations.
#%END

#%option
#% key: pattern
#% type: string
#% gisprompt: old,cell,raster
#% description: Pattern of first part of file names (prefixes) for map series (leave off #'s, but include any "_"'s or "."'s between the prefix and #)
#% required : yes
#%END
#%option
#% key: startnum
#% type: integer
#% description: Smallest number of the input map series (ie. # of the first map you'd like to include in the cumulative series).
#% required : yes
#%END
#%option
#% key: endnum
#% type: integer
#% description: Largest number of the input map series (ie. # of the last map you'd like to include in the cumulative series).
#% required : yes
#%END
#%option
#% key: digits
#% type: integer
#% description: Total number of digits for input (and output) numbers. (for padding with leading zeros. if zero, numbers are given no leading zeroes)
#% required : yes
#% answer: 0
#%END
#%option
#% key: infix
#% type: string
#% description: Infix inserted between the prefix and number of the output maps
#% answer: _cumseries_
#% required : yes
#%END
#%option
#% key: suffix
#% type: string
#% gisprompt: old,cell,raster
#% description: Pattern of last part of file names (suffixes) for map series with infixed numbers (leave blank if numbers are on the end of the file name!!!)
#% required : no
#%END
#%option
#% key: statsout
#% type: string
#% description: Name of text file to write yearly cumulative erosion/deposition stats to (if blank, no stats file will be written)
#% answer: erdep_stats.csv
#% required : no
#%END
#%Flag
#% key: e
#% description: -e export all maps to PNG files in home directory (good for animation in other programs)
#%End

import sys
import os
import tempfile
import subprocess
grass_install_tree = os.getenv('GISBASE')
sys.path.append(grass_install_tree + os.sep + 'etc' + os.sep + 'python')
import grass.script as grass

def main():
    pattern = os.getenv("GIS_OPT_pattern")
    startnum = int(os.getenv("GIS_OPT_startnum"))
    endnum = int(os.getenv("GIS_OPT_endnum"))
    infix = os.getenv("GIS_OPT_infix")
    digits = int(os.getenv("GIS_OPT_digits"))
    #create temp file for color rules
    temp = tempfile.NamedTemporaryFile()
    temp.write("100% 0 0 100\n1 blue\n0.5 indigo\n0.01 green\n0 white\n-0.01 yellow\n-0.5 orange\n-1 red\n0% 150 0 50")
    temp.flush()
    #test to see if we make a stats file, and make it if true
    if bool(os.getenv("GIS_OPT_statsout")) == True:
        statsfile = file(os.getenv("GIS_OPT_statsout"), 'w')
        statsfile.write('Erosion Stats,,,,,,Deposition Stats,,,,,\nMax,Min,Mean,Standard Deviation,99th percentile,,Max,Min,Mean,Standard Deviation,99th percentile\n')
    #if clause tests if numbers are inixed, and then runs the loop accordingly
    if bool(os.getenv("GIS_OPT_suffix")) == False:
        grass.message("Numbers are suffixes to prefix: " + pattern)
        for x in range((startnum - 1), endnum):
            tempmap = "temp_cum_netchange_before_smoothing_%s" % (x + 1)
            if (x + 1) == startnum:
                outmap = "%s%s%s" % (pattern, infix, str(startnum).zfill(digits))
                grass.run_command('g.copy',  quiet = True,  rast = '%s%s,%s' % (pattern, str(startnum).zfill(digits), outmap))
                grass.run_command('r.colors',  quiet = True,  map = outmap,  rules =  temp.name)
            else:
                mapone = "%s%s%s" % (pattern, infix, str(x).zfill(digits))
                maptwo = "%s%s" % (pattern, str(x + 1).zfill(digits))
                outmap = "%s%s%s" % (pattern, infix, str(x + 1).zfill(digits))
                grass.message('doing mapcalc statement for cum netchange map of year %s' % (str(x + 1).zfill(digits)))
                grass.mapcalc('${out}=if(abs(${map1} + ${map2}) < 20, ${map1} + ${map2}, 20) ',  out = tempmap,  map1 = mapone, map2=maptwo)
                grass.run_command('r.neighbors', quiet = True, input = tempmap, output = outmap, method = 'mode', size = '5')
                grass.message('setting colors for statement for map ' + outmap)
                grass.run_command('r.colors',  quiet = True,  map = outmap,  rules =  temp.name)
            if ( os.getenv("GIS_FLAG_e") == "1" ):
                grass.message('creating png image of map ' + outmap)
                grass.run_command('r.out.png',  quiet = True,  input = outmap,  output = outmap + '.png')
            if bool(os.getenv("GIS_OPT_statsout")) == True:
                grass.message('calculating erosion/deposition statistics for map ' + outmap)
                grass.mapcalc('temperosion=if(${map1} < 0 && ${map1} > -20, ${map1}, null())',  map1 = outmap)
                grass.mapcalc('tempdep=if(${map1} > 0 && ${map1} < 20, ${map1}, null())',  map1 = outmap)
                dict1 = grass.parse_command('r.univar',  flags = 'ge',  map = 'temperosion',  percentile = '1')
                dict2 = grass.parse_command('r.univar',  flags = 'ge',  map = 'tempdep',  percentile = '99')
                grass.run_command('g.remove',  quiet = True,  flags = 'f',  rast = 'temperosion,tempdep,' + tempmap)
                statsfile.write('%s,%s,%s,%s,%s,,%s,%s,%s,%s,%s\n' % (dict1['max'], dict1['min'], dict1['mean'], dict1['stddev'], dict1['percentile_1'], dict2['max'], dict2['min'], dict2['mean'], dict2['stddev'], dict2['percentile_99']))
    else:
        suffix = os.getenv("GIS_OPT_suffix")
        grass.message("Numbers are infixes between prefix: %s and suffix: %s" % (pattern, suffix))
        for x in range((startnum - 1), endnum):
            tempmap = "temp_cum_netchange_before_smoothing_%s" % (x + 1)
            if (x + 1) == startnum:
                outmap = "%s%s%s%s" % (pattern, str(startnum).zfill(digits), infix, suffix)
                grass.run_command('r.neighbors', input = '%s%s%s' % (pattern, str(startnum).zfill(digits), suffix), output = outmap, method = 'mode', size = '5')
                #grass.run_command('g.copy',  quiet = True,  rast = '%s%s%s,%s' % (pattern, str(startnum).zfill(digits), suffix, outmap))
                grass.run_command('r.colors',  quiet = True,  map = outmap,  rules =  temp.name)
            else:
                mapone = "%s%s%s%s" % (pattern, str(x).zfill(digits), infix, suffix)
                maptwo = "%s%s%s" % (pattern, str(x + 1).zfill(digits), suffix)
                outmap = "%s%s%s%s" % (pattern, str(x + 1).zfill(digits), infix, suffix)
                grass.message('doing mapcalc statement for cum netchange map of year %s' % (str(x + 1).zfill(digits)))
                grass.run_command('r.neighbors', input = maptwo, output = tempmap, method = 'mode', size = '5')
                grass.mapcalc('${out}=${map1} + ${map2}',  out = outmap,  map1 = mapone, map2=tempmap)
                grass.message('setting colors for statement for map %s' % outmap)
                grass.run_command('r.colors',  quiet = True,  map = outmap,  rules =  temp.name)
            if ( os.getenv("GIS_FLAG_e") == "1" ):
                grass.message('creating png image of map ' + outmap)
                grass.run_command('r.out.png',  quiet = True,  input = outmap,  output = outmap + '.png')
            if bool(os.getenv("GIS_OPT_statsout")) == True:
                grass.message('calculating erosion/deposition statistics for map ' + outmap)
                grass.mapcalc('temperosion=if(${map1} < -0, ${map1}, null())',  map1 = outmap)
                grass.mapcalc('tempdep=if(${map1} > 0, ${map1}, null())',  map1 = outmap)
                dict1 = grass.parse_command('r.univar',  flags = 'ge',  map = 'temperosion',  percentile = '1')
                dict2 = grass.parse_command('r.univar',  flags = 'ge',  map = 'tempdep',  percentile = '99')
                grass.run_command('g.remove',  quiet = True,  flags = 'f',  rast = 'temperosion,tempdep,' + tempmap)
                statsfile.write('%s,%s,%s,%s,%s,,%s,%s,%s,%s,%s\n' % (dict1['max'], dict1['min'], dict1['mean'], dict1['stddev'], dict1['percentile_1'], dict2['max'], dict2['min'], dict2['mean'], dict2['stddev'], dict2['percentile_99']))
    if bool(os.getenv("GIS_OPT_statsout")) == True:
        statsfile.close()
    temp.close()
    return

if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        grass.message("       Starting the process--hold on!")
        grass.message("It is not done until you see DONE WITH EVERYTHING!")
        main();
        grass.message("DONE WITH EVERYTHING!")
