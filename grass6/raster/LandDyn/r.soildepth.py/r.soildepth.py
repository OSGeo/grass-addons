#!/usr/bin/python
#
############################################################################
#
# MODULE:       	r.soildepth
# AUTHOR(S):		Isaac Ullah and Claudine Gravel-Miguel, Arizona State University
# PURPOSE:		Create soil depth map based on hillslope curvature.
# ACKNOWLEDGEMENTS:	National Science Foundation Grant #BCS0410269 
#			Based on equations from Heimsath et al, 1997
# COPYRIGHT:		(C) 2012 by Isaac Ullah, Michael Barton, Claudine Gravel-Miguel Arizona State University
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
#% description: What are the actual (empircal) minimum soil depths in this area (in meters)? (NOTE: The smoothing operation will trim extreme values, so resulting soildepth map may not have minimum depths exactly equal to this number)
#% answer: 0.0001
#% required : yes
#%END
#%option
#% key: max
#% type: double
#% description: What are the actual (empircal) maximum soil depths in this area (in meters)? (NOTE: The smoothing operation will trim extreme values, so resulting soildepth map may not have maximum depths exactly equal to this number)
#% answer: 20.0
#% required : yes
#%END
#%option
#% key: slopebreaks
#% type: string
#% description: Slope remapping pairs in the form: "x1,y1;x2,y2" where x is a slope value (in degrees), and y is a number between 0 and 1 to rescale to. (Two pairs are needed, in order, lower slope then higher slope.)
#% answer: 15,0.5;45,0.15
#% required : yes
#%END
#%option
#% key: curvebreaks 
#% type: string
#% description: Breakpoints in mean curvature values for maximum and minimum soil depths in the form of: "x1,y1;x2,y2" where x1 and x2 are the concavity and convexity value breakpoints respectively, y1 is a number between 0 and -1 and y2 is a number between 0 and 1. (Note: if x1 and/orx2 are too large, the real max and/or min curvaturewill be used.)
#% answer: -0.015,-0.5;0.015,0.5
#% required : yes
#%END
#%option
#% key: smoothingtype
#% type: string
#% description: Type of smoothing to perform ("median" is recommended)
#% answer: median
#% options: average,median,mode,minimum,maximum
#% required : yes
#%END 
#%option
#% key: smoothingsize
#% type: integer
#% description: Size (in cells) of the smoother's moving window
#% answer: 3
#% required : yes
#%END
#%flag
#% key: k
#% description: -k Keep the soil depth "potential" map (map name will be the same as specified in input option 'bedrock" with suffix "_depth_potential" appended to it)
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
    soildepth = "temp.soildepth"
    tempsdepth = "temp.soildepth2"
    if os.getenv('GIS_OPT_soildepth') == None:
        soildepth2 = "temp.soildepth3"
    else:
        soildepth2 = os.getenv('GIS_OPT_soildepth')
    elev = os.getenv('GIS_OPT_elev')
    bedrock = os.getenv('GIS_OPT_bedrock')
    smoothingtype = os.getenv('GIS_OPT_smoothingtype')
    smoothingsize = os.getenv('GIS_OPT_smoothingsize')
    slopebreaks = os.getenv('GIS_OPT_slopebreaks').split(";") 
    curvebreaks = os.getenv('GIS_OPT_curvebreaks').split(";") 
    smin = os.getenv('GIS_OPT_min')
    smax = os.getenv('GIS_OPT_max')
    slope = "temp_slope_deletable"
    pc = "temp_pc_deletable"
    tc = "temp_tc_deletable"
    mc = "temp_mc_deletable"
    temprate = "temp_rate_deletable"
    #let's grab the current resolution
    res = grass.region()['nsres']
    # make color rules for soil depth maps
    sdcolors = tempfile.NamedTemporaryFile()
    sdcolors.write('100% 0:249:47\n20% 78:151:211\n6% 194:84:171\n0% 227:174:217')
    sdcolors.flush()
    grass.message('STEP 1, Calculating curvatures\n')
    grass.run_command('r.slope.aspect', quiet = "True", overwrite = "True", elevation=elev, slope=slope, pcurv=pc, tcurv=tc)
    #creat meancurvature map (in a manner compatible with older versions of grass6), and then grab some stats from it for the later rescale operation
    grass.mapcalc("${mc}=(${tc}+${pc})/2", quiet = "True", mc = mc, tc = tc, pc = pc)
    mcdict = grass.parse_command('r.univar', flags = "g", map=mc)
    #figuring out if user-supplied curvature breakpoints exceed actual limits of curvature in the map, and adjusting if necessary
    if mcdict['min'] < curvebreaks[0].split(',')[0]:
        y1 = mcdict['min'] + ',' + curvebreaks[0].split(',')[1]
    else:
        y1 = curvebreaks[0]
    if mcdict['max'] > curvebreaks[1].split(',')[0]:
        y2 = mcdict['max'] + ',' + curvebreaks[1].split(',')[1]
    else:
        y2 = curvebreaks[1]
    
    grass.message('STEP 2, Calculating "depth potential" across the landscape\n')
    #nested rescale of first slope (to percentage of maximum soil depth potential), and then curvature (to percentage offset from slope function), and then combining the two measures to make final estimation of soil depth potential. Final output depth potential map will be scaled between 0 and 1, which maps to lowest depth potential to highest depth potential.
    grass.mapcalc("${temprate}=eval(x=graph( ${slope}, 0,1 , ${x1}, ${x2}, 90,0), y=graph(${mc}, ${y1}, 0,0, ${y2}), z=if(y < 0, x+(x*y), x+((1-x)*y)), if(z < 0, 0, if(z > 1, 1, z)))", quiet = "True", temprate = temprate, slope = slope, x1 = slopebreaks[0], x2 = slopebreaks[1], mc = mc, y1 = y1, y2 = y2)

    grass.message('STEP 3, Calculating actual soil depths across the landscape (based on user input min and max soil depth values)\n')
    # create dictionary to record max and min rate so we can rescale it according the user supplied max and min desired soil depths
    ratedict = grass.parse_command('r.univar', flags = "g", map=temprate)
    #creating and running a linear regression to scale the calculated landform soil depth potential into real soil depths using user specified min and max soil depth values
    grass.mapcalc('${soildepth}=graph(${temprate}, ${rmin},${smin}, ${rmax},${smax})', quiet = "True", soildepth = soildepth, temprate = temprate, rmin = ratedict['min'], rmax = ratedict['max'], smin = smin, smax = smax)
    unsmodict = grass.parse_command('r.univar', flags = "g", map=soildepth)
    grass.run_command('r.neighbors', quiet = "True", input=soildepth, output=tempsdepth, size=smoothingsize, method=smoothingtype)
    #fix shrinking edge caused by eighborhood operation (and r.slope.aspect above) by filling in the null areas. We do this by 0.98 * smax, since the null cells are all the cells of the actual drainage divide with slope basically = 0, and very mildly convex curvatures. This basically blends them in nicely with the neighboring cells.
    grass.mapcalc('${soildepth_real}=if(isnull(${input_sdepth}) && isnull(${elev}), null(), if(isnull(${input_sdepth}), 0.98*${smax},${input_sdepth}))', quiet = 'True',  input_sdepth = tempsdepth , soildepth_real = soildepth2, elev = elev, smax = smax)
    #grab some stats if asked to
    if os.getenv('GIS_FLAG_s') == '1':
        depthdict = grass.parse_command('r.univar', flags = "ge", map=soildepth2, percentile=90)
    
    grass.message('STEP 4, calculating bedrock elevation map\n')
    grass.mapcalc("${bedrock}=eval(x=(${elev} - ${soildepth}), if(isnull(x), ${elev}, x))", quiet = "True", bedrock = bedrock, elev = elev, soildepth = soildepth)
    grass.message('Cleaning up...')
    grass.run_command('g.remove', quiet = "true", rast = [pc, tc, mc, slope, soildepth, tempsdepth])
    if os.getenv('GIS_FLAG_k') == '1':
        grass.run_command('g.rename', quiet = "true", rast = "%s,%s_depth_potential" % (temprate, bedrock))
    else:
        grass.run_command('g.remove', quiet = "True", rast = temprate)
    if os.getenv('GIS_OPT_soildepth') is None:
        grass.run_command('g.remove', quiet = "true", rast = soildepth2)
    else:
        grass.run_command('r.colors', quiet = "True", map=soildepth2, rules=sdcolors.name)
    grass.message('\nDONE!\n')
    if os.getenv('GIS_FLAG_s') == '1':
        grass.message("min, max, and mean before smoothing: " + unsmodict['min']  + ", " + unsmodict['max'] + ", " + unsmodict['mean'])
        for key in depthdict.keys():
            grass.message('%s=%s' % (key,  depthdict[key]))
        grass.message('Total volume of soil is %s cubic meters' % (float(depthdict['sum'])*res*res))
    return
    
# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()





