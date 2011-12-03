#!/usr/bin/python
#
############################################################################
#
# MODULE:       	r.soildepth
# AUTHOR(S):		Isaac Ullah and Claudine Gravel-Miguel, Arizona State University
# PURPOSE:		Create soil depth map based on hillslope curvature.
# ACKNOWLEDGEMENTS:	National Science Foundation Grant #BCS0410269 
#			Based on equations from Heimsath et al, 1997
# COPYRIGHT:		(C) 2011 by Isaac Ullah, Michael Barton, Claudine Gravel-Miguel Arizona State University
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
#% required : yes
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
grass_install_tree = os.getenv('GISBASE')
sys.path.append(grass_install_tree + os.sep + 'etc' + os.sep + 'python')
import grass.script as grass

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
    res = grass.region()['nsres']
    # make color rules for soil depth maps
    sdcolors = tempfile.NamedTemporaryFile()
    sdcolors.write('100% 0:249:47\n20% 78:151:211\n6% 194:84:171\n0% 227:174:217')
    sdcolors.flush()
    grass.message('STEP 1, calculating profile and tangental curvatures\n')
    grass.run_command('r.slope.aspect', quiet = "True", overwrite = "True", format='percent', elevation=elev, slope=slope, pcurv=pc, tcurv=tc)
    grass.message('STEP 2, Calculating soil depth ratios across the landscape\n')
    grass.mapcalc("${temprate}=eval(x = (-1.000*(${pc} + ${tc})), y = (if(${slope} < 1.000, 1.000, ${slope})), ((50.000*x)+50.000)/y)", quiet = "True", temprate = temprate, pc = pc, tc = tc, slope = slope)
    # create dictionary to record max and min rate so we can rescale it according the user supplied max and min desired soil depths
    ratedict = grass.parse_command('r.info', flags = 'r', map=temprate)
    grass.message('STEP 3, Calculating actual soil depths across the landscape (based on user input min and max soil depth values)\n')
    #creating and running a linear regression to scale the calculated landform soil depth ratios into real soil dpeths using user specified min and max soil depth values
    #grass_com('r.mapcalc "' + soildepth + '=eval(x = ((' + ratedict['max'] + '-' + max +')/(' + ratedict['min'] + '-' + min + ')), y = (' + ratedict['max'] + '-(y*' + ratedict['min'] + ')), (y*' + temprate + ')+x)"')  #####this is the discreet way using mapcalc, I thik the r.recode way (below) may be faster
    recode =  tempfile.NamedTemporaryFile()
    recode.write('%s:%s:%s:%s' % (ratedict['min'] , ratedict['max'] ,  min,  max))
    recode.flush()
    grass.run_command('r.recode', quiet = "True", input=temprate, output=soildepth, rules=recode.name)
    recode.close()
    #grab some stats if asked to
    if os.getenv('GIS_FLAG_s') == '1':
        depthdict = grass.parse_command('r.univar', flags = "ge", map=soildepth, percentile=90)
    grass.message('STEP 4, calculating bedrock elevation map\n')
    grass.mapcalc("${bedrock}=(${elev} - ${soildepth})", quiet = "True", bedrock = bedrock, elev = elev, soildepth = soildepth)
    grass.message('Cleaning up...')
    if os.getenv('GIS_FLAG_k') == '1':
        grass.run_command('g.remove', quiet = "true", rast = [pc, tc, slope])
        grass.run_command('g.rename', quiet = "true", rast = "%s,%s%s_rate" % (temprate, temprate, bedrock))
    else:
        grass.run_command('g.remove', quiet = "True", rast = [pc, tc, temprate, slope])
    if os.getenv('GIS_OPT_soildepth') is None:
        grass.run_command('g.remove', quiet = "true", rast = soildepth)
    else:
        grass.run_command('r.colors', quiet = "True", map=soildepth, rules=sdcolors.name)
    grass.message('\nDONE!\n')
    if os.getenv('GIS_FLAG_s') == '1':
        # have to figure that part out!
        for key in depthdict.keys():
            grass.message('%s=%s' % (key,  depthdict[key]))
        grass.message('Total volume of soil is %s cubic meters' % (float(depthdict['sum'])*res))
    return
    
# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()





