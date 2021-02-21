#!/usr/bin/env python


############################################################################
#
# MODULE:
# AUTHOR(S):    iullah
# COPYRIGHT:    (C) 2007 GRASS Development Team/iullah
#
#  description: Grabs landcover stats from a stack of sequnetially numbered landcover maps, and makes a formatted csv file

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
#% description: Grabs landcover stats from a stack of sequnetially numbered landcover maps, and makes a formatted csv file
#%End

#%option
#% key: pattern
#% type: string
#% gisprompt: old,cell,raster
#% description: Pattern of first part of file names (prefixes) for input landcover map series (leave off #'s)
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
#% key: startnum
#% type: integer
#% description: Smallest number of the input map series (ie. # of the first map you'd like to include in the cumulative series).
#% answer: 1
#% required : yes
#%END
#%option
#% key: endnum
#% type: integer
#% description: Largest number of the input map series (ie. # of the last map you'd like to include in the cumulative series).
#% answer: 40
#% required : yes
#%END
#%option
#% key: categories
#% type: integer
#% description: Number of landcover categories used in the input maps
#% answer: 50
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
#% key: statsout
#% type: string
#% description: Name of output stats file
#% answer: lc_stats.csv
#% required : yes
#%END
#%Flag
#% key: n
#% description: -n Automatically name stats file  "lc_stats_'mapset'_'pattern'.csv". Disregards option "statsout".
#%End
#%Flag
#% key: r
#% description: -r Output stats file formatted as a GRASS xy ASCII raster matrix (X = categories, Y = years).
#%End
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
    categories = int(os.getenv("GIS_OPT_categories"))
    digits = int(os.getenv("GIS_OPT_digits"))

    msp = subprocess.Popen('g.gisenv get=MAPSET store=gisrc --quiet', stdout=subprocess.PIPE, shell='bash')
    mapset = msp.stdout.read().replace('\n','')
    if os.getenv("GIS_FLAG_n") == "1":
        statsout = 'lc_stats_%s_%s.csv' % (mapset,pattern)
    else:
        statsout = os.getenv("GIS_OPT_statsout")
    f = open(statsout, 'w')
    l = [str(x) for x in range(0,categories+1)]
    md = {}
    if bool(os.getenv("GIS_OPT_suffix")) == False:
        grass_print("Numbers are suffixes to prefix: %s" % pattern)
        for number in range(startnum, endnum+1):
            outmap = '%s%s' % (pattern, str(number).zfill(digits))
            p = subprocess.Popen('r.stats -a -n input=%s fs=space nv=* nsteps=255 --quiet' % outmap, stdout=subprocess.PIPE, shell='bash')
            out = p.stdout.readlines()
            dict1 = {}
            for x in out:
                x0,x1 = x.split()
                dict1[x0] = x1
            mdlist = []
            for key in l:
                if dict1.has_key(key):
                    mdlist.append(dict1[key])
                else:
                    mdlist.append('0')
            md[number] = mdlist
            if ( os.getenv("GIS_FLAG_e") == "1" ):
                subprocess.Popen('r.out.png --quiet quiet input=%s output=%s.png' % (outmap, outmap), shell='bash').wait()


        if os.getenv("GIS_FLAG_r") == "1":
            f.write('north: %s\nsouth: %s\neast: %s\nwest: 1\ncols: %s\nrows: %s\n' % (endnum,startnum,categories,categories,endnum))
            stat_list = []
            for key in md.iterkeys():
                stats = md[key]
                stat_list.append('%s\n' % (','.join(stats)))
            stat_list.reverse()
            grass_print(stat_list)
            f.writelines(stat_list)
            f.close()
        else:
            f.write('Landcover Category,%s\n' % ','.join(l))
            for key in md.iterkeys():
                stats = md.get(key, [])
                stat_str = 'Year %s,%s\n' % (key, ','.join(stats))
                f.write(stat_str)
    else:
        suffix = os.getenv("GIS_OPT_suffix")
        grass_print("Numbers are infixes between prefix: %s and suffix: %s" % (pattern, suffix))
        for number in range(startnum, endnum+1):
            outmap = '%s%s%s' % (pattern, str(number).zfill(digits), suffix)
            p = subprocess.Popen('r.stats -a -n input=%s fs=space nv=* nsteps=255 --quiet' % outmap, stdout=subprocess.PIPE, shell='bash')
            out = p.stdout.readlines()
            dict1 = {}
            for x in out:
                x0,x1 = x.split()
                dict1[x0] = x1
            mdlist = []
            for key in l:
                if dict1.has_key(key):
                    mdlist.append(dict1[key])
                else:
                    mdlist.append('0')
            md[number] = mdlist
            if ( os.getenv("GIS_FLAG_e") == "1" ):
                subprocess.Popen('r.out.png --quiet quiet input=%s output=%s.png' % (outmap, outmap), shell='bash').wait()

        if os.getenv("GIS_FLAG_r") == "1":
            f.write('north: %s\nsouth: %s\neast: %s\nwest: 1\ncols: %s\nrows: %s\n' % (endnum,startnum,categories,categories,endnum))
            stat_list = []
            for key in md.iterkeys():
                stats = md[key]
                stat_list.append('%s\n' % (','.join(stats)))
            stat_list.reverse()
            grass_print(stat_list)
            f.writelines(stat_list)
            f.close()
        else:
            f.write('Landcover Category,%s\n' % ','.join(l))
            for key in md.iterkeys():
                stats = md.get(key, [])
                stat_str = 'Year %s,%s\n' % (key, ','.join(stats))
                f.write(stat_str)
    f.close()
    return

if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        grass_print("Starting the process, hold on!")
        grass_print("It is not done until you see DONE WITH EVERYTHING!")
        main();
        grass_print("DONE WITH EVERYTHING!")
