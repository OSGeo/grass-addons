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
import subprocess

def grass_print(m):
	return subprocess.Popen("g.message message='"'%s'"'" % m, shell='bash').wait()

def main():
    pattern = os.getenv("GIS_OPT_pattern")
    startnum = int(os.getenv("GIS_OPT_startnum"))
    endnum = int(os.getenv("GIS_OPT_endnum"))
    infix = os.getenv("GIS_OPT_infix")
    digits = int(os.getenv("GIS_OPT_digits"))
    #create temp file for color rules
    f1 = open('temp_color_rules.txt', 'w')
    f1.write("100% 0 0 100\n5 purple\n0.5 blue\n0.000075 108 166 205\n0 230 230 230\n-0.000075 205 092 092\n-0.5 red\n-5 magenta\n0% 150 0 50")
    f1.close()
    #test to see if we make a stats file, and make it if true
    if bool(os.getenv("GIS_OPT_statsout")) == True:
        statsfile = file(os.getenv("GIS_OPT_statsout"), 'w')
        statsfile.write('Erosion Stats,,,,,,Deposition Stats,,,,,\nMax,Min,Mean,Standard Deviation,99th percentile,,Max,Min,Mean,Standard Deviation,99th percentile\n')
    #if clause tests if numbers are inixed, and then runs the loop accordingly
    if bool(os.getenv("GIS_OPT_suffix")) == False:
        grass_print("Numbers are suffixes to prefix: %s" % pattern)
        for x in range((startnum - 1), endnum):
            if (x + 1) == startnum:
                outmap = "%s%s%s" % (pattern, infix, str(startnum).zfill(digits))
                subprocess.Popen('g.copy --quiet rast=%s%s,%s' % (pattern, str(startnum).zfill(digits), outmap), shell='bash').wait()
                subprocess.Popen('r.colors --quiet map=%s rules=$HOME/temp_color_rules.txt' % (outmap), shell='bash').wait()
            else:
                mapone = "%s%s%s" % (pattern, infix, str(x).zfill(digits))
                maptwo = "%s%s" % (pattern, str(x + 1).zfill(digits))
                outmap = "%s%s%s" % (pattern, infix, str(x + 1).zfill(digits))
                grass_print('doing mapcalc statement for cum netchange map of year %s' % (str(x + 1).zfill(digits)))
                subprocess.Popen('r.mapcalc "%s = (%s + %s)"' % (outmap, mapone, maptwo), shell='bash').wait()
                grass_print('setting colors for statement for map %s' % outmap)
                subprocess.Popen('r.colors --quiet map=%s rules=$HOME/temp_color_rules.txt' % (outmap), shell='bash').wait()
            if ( os.getenv("GIS_FLAG_e") == "1" ):
                    grass_print('creating png image of map %s' % outmap)
                    subprocess.Popen('r.out.png --quiet input=%s output=%s.png' % (outmap, outmap), shell='bash').wait()
            if bool(os.getenv("GIS_OPT_statsout")) == True:
                grass_print('calculating erosion/deposition statistics for map %s' % outmap)
                subprocess.Popen('r.mapcalc "temperosion=if(%s < 0, %s, null())"' % (outmap, outmap), shell='bash').wait()
                subprocess.Popen('r.mapcalc "tempdep=if(%s > 0, %s, null())"' % (outmap, outmap), shell='bash').wait()
                p1 = subprocess.Popen('r.univar -g -e map=temperosion percentile=1', stdout=subprocess.PIPE, shell='bash')
                erstats = p1.stdout.readlines()
                dict1 = {}
                for y in erstats:
                    y0,y1 = y.split('=')
                    dict1[y0] = y1.strip()
                p2 = subprocess.Popen('r.univar -g -e map=tempdep percentile=99', stdout=subprocess.PIPE, shell='bash')
                depstats = p2.stdout.readlines()
                dict2 = {}
                for z in depstats:
                    z0,z1 = z.split('=')
                    dict2[z0] = z1.strip()
                statsfile.write('%s,%s,%s,%s,%s,,%s,%s,%s,%s,%s\n' % (dict1['max'], dict1['min'], dict1['mean'], dict1['stddev'], dict1['percentile_1'], dict2['max'], dict2['min'], dict2['mean'], dict2['stddev'], dict2['percentile_99']))
    else:
        suffix = os.getenv("GIS_OPT_suffix")
        grass_print("Numbers are infixes between prefix: %s and suffix: %s" % (pattern, suffix))
        for x in range((startnum - 1), endnum):
            if (x + 1) == startnum:
                outmap = "%s%s%s%s" % (pattern, str(startnum).zfill(digits), infix, suffix)
                subprocess.Popen('g.copy --quiet rast=%s%s%s,%s' % (pattern, str(startnum).zfill(digits), suffix, outmap), shell='bash').wait()
                subprocess.Popen('r.colors --quiet map=%s rules=$HOME/temp_color_rules.txt' % (outmap), shell='bash').wait()
            else:
                mapone = "%s%s%s%s" % (pattern, str(x).zfill(digits), infix, suffix)
                maptwo = "%s%s%s" % (pattern, str(x + 1).zfill(digits), suffix)
                outmap = "%s%s%s%s" % (pattern, str(x + 1).zfill(digits), infix, suffix)
                grass_print('doing mapcalc statement for cum netchange map of year %s' % (str(x + 1).zfill(digits)))
                subprocess.Popen('r.mapcalc "%s = (%s + %s)"' % (outmap, mapone, maptwo), shell='bash').wait()
                grass_print('setting colors for statement for map %s' % outmap)
                subprocess.Popen('r.colors --quiet map=%s rules=$HOME/temp_color_rules.txt' % (outmap), shell='bash').wait()
            if ( os.getenv("GIS_FLAG_e") == "1" ):
                grass_print('creating png image of map %s' % outmap)
                subprocess.Popen('r.out.png --quiet input=%s output=%s.png' % (outmap, outmap), shell='bash').wait()
            if bool(os.getenv("GIS_OPT_statsout")) == True:
                grass_print('calculating erosion/deposition statistics for map %s' % outmap)
                subprocess.Popen('r.mapcalc "temperosion=if(%s < 0, %s, null())"' % (outmap, outmap), shell='bash').wait()
                subprocess.Popen('r.mapcalc "tempdep=if(%s > 0, %s, null())"' % (outmap, outmap), shell='bash').wait()
                p1 = subprocess.Popen('r.univar -g -e map=temperosion percentile=1', stdout=subprocess.PIPE, shell='bash')
                erstats = p1.stdout.readlines()
                dict1 = {}
                for y in erstats:
                    y0,y1 = y.split('=')
                    dict1[y0] = y1.strip('\n')
                p2 = subprocess.Popen('r.univar -g -e map=tempdep percentile=99', stdout=subprocess.PIPE, shell='bash')
                depstats = p2.stdout.readlines()
                dict2 = {}
                for z in depstats:
                    z0,z1 = z.split('=')
                    dict2[z0] = z1.strip('\n')
                statsfile.write('%s,%s,%s,%s,%s,,%s,%s,%s,%s,%s\n' % (dict1['max'], dict1['min'], dict1['mean'], dict1['stddev'], dict1['percentile_1'], dict2['max'], dict2['min'], dict2['mean'], dict2['stddev'], dict2['percentile_99']))
    if bool(os.getenv("GIS_OPT_statsout")) == True:
        statsfile.close()
    subprocess.Popen('rm -f $HOME"/temp_color_rules.txt"', shell="bash")
    subprocess.Popen('g.remove -f rast=temperosion,tempdep', shell="bash")
    return
        
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        grass_print("       Starting the process--hold on!")
	grass_print("It is not done until you see DONE WITH EVERYTHING!")
        main();
        grass_print("DONE WITH EVERYTHING!")
