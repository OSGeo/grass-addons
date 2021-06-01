#!/usr/bin/python

############################################################################
#
# MODULE:
# AUTHOR(S):    iullah
# COPYRIGHT:    (C) 2007 GRASS Development Team/iullah
#
#  description: fixes a run of r.landscape.evol that did not make netchange maps

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
#% description: fixes a run of r.landscape.evol that did not make netchange maps
#%End
#%option
#% key: initdem
#% type: string
#% gisprompt: old,cell,raster
#% description: initial dem that was used as the starting dem for r.landscape.evol
#% answer: init_dem@PERMANENT
#% required : yes
#%END
#%option
#% key: pattern
#% type: string
#% gisprompt: old,cell,raster
#% description: Pattern of first part of file names (prefixes) for map series (don't include suffixes like "elevation_", "soildepth_", etc., and leave off #'s)
#% required : yes
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
#%Flag
#% key: e
#% description: -e export accumulated netchange maps to PNG files in home directory (good for animation in other programs)
#	#% answer: 1
#%End

import sys
import os
import subprocess
import tempfile



# m is a grass/bash command that will generate some list of info to stdout seperated by newlines, n is a defined blank list to write results to
def out2list(m, n):
    p1 = subprocess.Popen('%s' % m, stdout=subprocess.PIPE, shell='bash')
    p2 = p1.stdout.readlines()
    for y in p2:
        n.append(y.strip('\n'))

# m is a grass/bash command that will generate some list of keyed info to stdout, n is the character that seperates the key from the data, o is a defined blank dictionary to write results to
def out2dict(m, n, o):
    p1 = subprocess.Popen('%s' % m, stdout=subprocess.PIPE, shell='bash')
    p2 = p1.stdout.readlines()
    for y in p2:
        y0,y1 = y.split('%s' % n)
        o[y0] = y1.strip('\n')

# m is a grass/bash command that will generate some info to stdout. You must invoke this command in the form of "variable to be made" = out2var('command')
def out2var(m):
    pn = subprocess.Popen('%s' % m, stdout=subprocess.PIPE, shell='bash')
    return pn.stdout.read()

# m is a message (as a string) one wishes to have printed in the output window
def grass_print(m):
    subprocess.Popen('g.message message="%s"' % m, shell='bash').wait()
    return

# m is grass (or bash) command to execute (written as a string). script will wait for grass command to finish
def grass_com(m):
    subprocess.Popen('%s' % m, shell='bash').wait()
    return

# m is grass (or bash) command to execute (written as a string). script will not wait for grass command to finish
def grass_com_nowait(m):
    subprocess.Popen('%s' % m, shell='bash')
    return

def netchange(initdem, pattern, startnum, endnum):

    grass_print ('Working on netchange map series, please stand by.....')        

    tempfilename = tempfile.NamedTemporaryFile()
    nccolors = open(tempfilename, 'w')
    nccolors.write('100% 0 0 100\n1 blue\n0.5 indigo\n0.01 green\n0 white\n-0.01 yellow\n-0.5 orange\n-1 red\n0% 150 0 50')
    nccolors.close()

    mapset = out2var('g.gisenv get=MAPSET store=gisrc --quiet').replace('\n','')

    maplist = []
    out2list('g.mlist type=rast mapset=%s pattern=%s*' % (mapset, pattern), maplist)
    mapstring = ', '.join(maplist)

    for x in range(startnum, endnum+1):
        iter = x
        last_iter = x-1

        if '%selevation_%i' % (pattern, startnum) in mapstring:
            elevpattern = pattern+'elevation_'
        elif '%selevation%i' % (pattern, startnum) in mapstring:
            elevpattern = pattern+'elevation'
        elif pattern.strip('_')+'elevation%i' % startnum in mapstring:
            elevpattern = pattern.strip('_')+'elevation'
        elif pattern.strip('_')+'elevation_%i' % startnum in mapstring:
            elevpattern = pattern.strip('_')+'elevation_'
        else:
            grass_print('No properly named elevation maps in mapset, ending run unsuccessfully')
            break

        if iter == startnum:
            mapone = initdem
        elif pattern+'%i_elevation' % startnum in mapstring:
            mapone =  pattern+'%i_elevation' % last_iter
        else:
            mapone = '%s%i' % (elevpattern, last_iter)
        maptwo = '%s%i' % (elevpattern, iter)
        outmap = '%snetchange_%s' % (pattern, iter)

        grass_com('r.mapcalc "%s=%s - %s"' % (outmap, maptwo, mapone))

        grass_com('r.colors --quiet map=%s rules=%s' % (outmap, tempfilename.name))

    close(tempfilename)
    grass_print('Netchange map series done!')

def accumulate_erdep(pattern, startnum, endnum):

    tempfilename = tempfile.mktemp()
    nccolors = open(tempfilename, 'w')
    nccolors.write('100% 0 0 100\n1 blue\n0.5 indigo\n0.01 green\n0 white\n-0.01 yellow\n-0.5 orange\n-1 red\n0% 150 0 50')
    nccolors.close()

    grass_print('Working on accumulated netchange map series, please stand by.....')

    pattern2 = '%snetchange_' % pattern
    infix = 'cumseries_'

    for x in range(startnum, endnum+1):
        iter = x
        last_iter = x-1

        outmap = '%s%s%04i' % (pattern2, infix, iter)

        if iter == startnum:
            grass_com('g.copy --quiet rast=%s%s,%s' % (pattern2, startnum, outmap))

            grass_com('r.colors --quiet map=%s rules=%s' % (outmap, tempfilename))
        else:
            mapone = '%s%s%04i' % (pattern2, infix, last_iter)
            maptwo = '%s%s' % (pattern2, iter)


            grass_com('r.mapcalc "%s=%s + %s"' % (outmap, mapone, maptwo))
            grass_com('r.colors --quiet map=%s rules=%s' % (outmap, tempfilename))

        if ( os.getenv("GIS_FLAG_e") == "1" ):
            grass_com('r.out.png --quiet input=%s output=%s.png' % (outmap, outmap))

    os.remove(tempfilename)    
    grass_print('Accumulated netchange map series done!')

def stats_file(pattern, startnum, endnum):

    nc_pattern = '%snetchange_' % pattern
    sd_pattern = '%ssoildepth' % pattern
    prefix = pattern
    iter = startnum
    mapset = out2var('g.gisenv get=MAPSET store=gisrc --quiet').replace('\n','')
    txtout = open('%s_%slsevol_stats.txt' % (mapset, prefix), 'w+')

    maplist = []
    out2list('g.mlist type=rast mapset=%s pattern=%s*' % (mapset, pattern), maplist)
    mapstring = ', '.join(maplist)

    grass_print('Working on stats file, please stand by.....')
    grass_print('Outputting stats to textfile: %s_%slsevol_stats.txt' % (mapset, prefix))

    for x in range(startnum, endnum+1):
        iter = x
        lastiter = iter-1

        #grabsomestats
        tmperosion = "tmperosion_%i" % iter
        tmpdep = "tmpdep_%i" % iter
        netchange = '%s%i' % (nc_pattern, iter)
        if 'soildepth_%i' % startnum in mapstring:
            soildepth = '%s_%i' % (sd_pattern, iter)
        elif 'soildepth%i' % startnum in mapstring:
            soildepth = '%s%i' % (sd_pattern, iter)
        elif pattern.strip('_')+'soildepth_%i' % startnum in mapstring:
            soildepth = pattern.strip('_')+'soildepth_%i' % iter  
        else:
            grass_print('No properly named soil depth maps in mapset, ending run unsuccessfully')
            break

        grass_com('r.mapcalc "%s=if(%s < 0, %s, null())"' % (tmperosion, netchange, netchange))

        grass_com('r.mapcalc "%s=if(%s > 0, %s, null())"' % (tmpdep, netchange, netchange))

        soilstats = {}
        out2dict('r.univar -g -e map=%s percentile=99' % soildepth, '=', soilstats)

        erosstats = {}
        out2dict('r.univar -g -e map=%s percentile=1' % tmperosion, '=', erosstats)

        depostats = {}
        out2dict('r.univar -g -e map=%s percentile=99' % tmpdep, '=', depostats)

        grass_com('g.remove --quiet rast=%s,%s' % (tmperosion, tmpdep))



        if iter == startnum:
            txtout.write('Stats for erosion and deposition simulation for: %s\n\nYear,,Mean Erosion,Max Erosion,Min Erosion,99th Percentile Erosion,,Mean Deposition,Min Deposition,Max Deposition,99th Percentile Deposition,,Mean Soil Depth,Min Soil Depth,Max Soil Depth,99th Percentile Soil Depth\n' % prefix)

        txtout.write('%s,,%s,%s,%s,%s,,%s,%s,%s,%s,,%s,%s,%s,%s\n' %(iter, erosstats['mean'], erosstats['min'], erosstats['max'], erosstats['percentile_1'], depostats['mean'], depostats['min'], depostats['max'], depostats['percentile_99'], soilstats['mean'], soilstats['min'], soilstats['max'], soilstats['percentile_99']))

    txtout.close
    grass_print('Stats file done!')


if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        grass_print("Starting the process, hold on! It is not done until you see DONE WITH EVERYTHING!")

        initdem = os.getenv("GIS_OPT_initdem")
        pattern = os.getenv("GIS_OPT_pattern")
        startnum = int(os.getenv("GIS_OPT_startnum"))
        endnum = int(os.getenv("GIS_OPT_endnum"))

        netchange(initdem, pattern, startnum, endnum);
        accumulate_erdep(pattern, startnum, endnum);
        stats_file(pattern, startnum, endnum);

        grass_print("\nDONE WITH EVERYTHING!")

