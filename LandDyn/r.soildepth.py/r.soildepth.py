#!/usr/bin/python
#
############################################################################
#
# MODULE:       	r.soildepth
# AUTHOR(S):		Isaac Ullah, Arizona State University
# PURPOSE:		Create soil depth map based on hillslope curvature.
# ACKNOWLEDGEMENTS:	National Science Foundation Grant #BCS0410269 
#			Based on equations from Heimsath et al, 1997
# COPYRIGHT:		(C) 2007 by Isaac Ullah, Michael Barton, Arizona State University
#			This program is free software under the GNU General Public
#			License (>=v2). Read the file COPYING that comes with GRASS
#			for details.
#
#############################################################################


#%Module
#%  description: Create soil depth map based on hillslope curvature
#%End
#%option
#% key: elev
#% type: string
#% gisprompt: old,cell,raster
#% description: Input elevation map (DEM)
#% required : yes
#%END 
#%option
#% key: bedrock
#% type: string
#% gisprompt: old,cell,raster
#% description: Output bedrock elevation map
#% required : yes
#%END
#%option
#% key: soildepth
#% type: string
#% gisprompt: old,cell,raster
#% description: Output soil depths map
#% required : no
#%END 
#%option
#% key: min
#% type: double
#% description: What are the actual (empircal) minimum soil depths in this area (in meters)?
#% answer: 0.0001
#% required : yes
#%END
#%option
#% key: max
#% type: double
#% description: What are the actual (empircal) maximum soil depths in this area (in meters)?
#% answer: 5.0
#% required : yes
#%END
#%flag
#% key: k
#% description: -k Keep the soil rate map (map name will be the same as specified in input option 'bedrock" with suffix "_rate" appended to it)
#%END
#%flag
#% key: s
#% description: -s Print some useful statistics about the output soil depths (written to stdout)
#%END

import sys
import os
import subprocess
import tempfile

# m is a message (as a string) one wishes to have printed in the output window
def grass_print(m):
	subprocess.Popen('g.message message="%s"' % m, shell='bash').wait()
	return
# m is grass (or bash) command to execute (written as a string). script will wait for grass command to finish
def grass_com(m):
	subprocess.Popen('%s' % m, shell='bash').wait()
	return
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

def main():
    if os.getenv('GIS_OPT_soildepth') == None:
        soildepth = "temp.soildepth"
    else:
        soildepth = os.getenv('GIS_OPT_soildepth')
    elev = os.getenv('GIS_OPT_elev')
    bedrock = os.getenv('GIS_OPT_bedrock')
    min = os.getenv('GIS_OPT_min')
    max = os.getenv('GIS_OPT_max')
    slope = "temp_slope_deletable"
    pc = "temp_pc_deletable"
    tc = "temp_tc_deletable"
    temprate = "temp_rate_deletable"
    #let's grab the current resolution
    reg1 = {}
    out2dict('g.region -p -m -g', '=', reg1)
    res = int(float(reg1['nsres']))
    # make color rules for soil depth maps
    sdcolors = tempfile.NamedTemporaryFile()
    sdcolors.write('100% 0:249:47\n20% 78:151:211\n6% 194:84:171\n0% 227:174:217')
    sdcolors.flush()
    grass_print('STEP 1, calculating profile and tangental curvatures\n')
    grass_com('r.slope.aspect --quiet --overwrite format=percent elevation=%s slope=%s pcurv=%s tcurv=%s' % (elev,  slope,  pc,  tc))
    grass_print('STEP 2, Calculating soil depth ratios across the landscape\n')
    grass_com('r.mapcalc "' + temprate + '=eval(x = (-1*(' + pc + '+' + tc + ')), y = (if(' + slope + ' < 1, 1, ' + slope + ')), ((50*x)+50)/y)"')
    # create dictionary to record max and min rate so we can rescale it according the user supplied max and min desired soil depths
    ratedict = {}
    out2dict('r.info -r map=%s' % temprate, '=', ratedict)
    grass_print('STEP 3, Calculating actual soil depths across the landscape (based on user input min and max soil depth values)\n')
    #creating and running a linear regression to scale the calculated landform soil depth ratios into real soil dpeths using user specified min and max soil depth values
    #grass_com('r.mapcalc "' + soildepth + '=eval(x = ((' + ratedict['max'] + '-' + max +')/(' + ratedict['min'] + '-' + min + ')), y = (' + ratedict['max'] + '-(y*' + ratedict['min'] + ')), (y*' + temprate + ')+x)"')  #####this is the discreet way using mapcalc, I thik the r.recode way (below) may be faster
    recode =  tempfile.NamedTemporaryFile()
    recode.write('%s:%s:%s:%s' % (ratedict['min'] , ratedict['max'] ,  min,  max))
    recode.flush()
    grass_com('r.recode --quiet input=%s output=%s rules=%s' % (temprate,  soildepth,  recode.name))
    recode.close()
    #grab some stats if asked to
    if os.getenv('GIS_FLAG_s') == '1':
        depthdict = {}
        out2dict('r.univar -ge map=' + soildepth + ' percentile=90', '=',  depthdict)
    grass_print('STEP 4, calculating bedrock elevation map\n')
    grass_com('r.mapcalc "' + bedrock + '=(' + elev + ' - ' + soildepth + ')"')
    grass_print('Cleaning up...')
    if os.getenv('GIS_FLAG_k') == '1':
        grass_com('g.remove --quiet rast=' + pc + ',' + tc)
        grass_com('g.rename --quiet rast=' + temprate + ',' + bedrock + '_rate')
    else:
        grass_com('g.remove --quiet rast=' + pc + ',' + tc + ',' + temprate)
    if os.getenv('GIS_OPT_soildepth') is None:
        grass_com('g.remove --quiet rast=' + soildepth)
    else:
        grass_com('r.colors --quiet  map=%s rules=%s' % (soildepth ,  sdcolors.name))
    grass_print('\nDONE!\n')
    if os.getenv('GIS_FLAG_s') == '1':
        for key in depthdict.keys():
            grass_print('%s=%s' % (key,  depthdict[key]))
        grass_print('Total volume of soil is %s cubic meters' % (float(depthdict['sum'])*res))
    return
    
# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()





