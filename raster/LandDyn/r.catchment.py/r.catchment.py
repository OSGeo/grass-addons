#!/usr/bin/python
#
############################################################################
#
# MODULE:       	r.catchment
# AUTHOR(S):		Isaac Ullah, Arizona State University
# PURPOSE:		Creates a raster buffer of specified area around vector points
#			using cost distances. Module requires r.walk.
# ACKNOWLEDGEMENTS:	National Science Foundation Grant #BCS0410269 
# COPYRIGHT:		(C) 2009 by Isaac Ullah, Michael Barton, Arizona State University
#			This program is free software under the GNU General Public
#			License (>=v2). Read the file COPYING that comes with GRASS
#			for details.
#
#############################################################################


#%Module
#%  description: Creates a raster buffer of specified area around vector points using cost distances. Requires r.walk. NOTE: please run g.region first to make sure region boundaries and resolution match input elevation map.
#%END


#%option
#% key: elev
#% type: string
#% gisprompt: old,cell,raster
#% description: Input elevation map (DEM)
#% required : yes
#%END
#%option
#% key: incost
#% type: string
#% gisprompt: old,cell,raster
#% description: Input cost map (This will override the input elevation map, if none specified, one will be created from input elevation map with r.walk)
#% required : no
#%END
#%option
#% key: vect
#% type: string
#% gisprompt: old,vector,vector
#% description: Name of input vector site points map
#% required : yes
#%END
#%option
#% key: frict
#% type: string
#% gisprompt: old,cell,raster
#% description: Optional map of friction costs. If no map selected, default friction=1 making output reflect time costs only
#% answer:
#% required : no
#%END
#%option
#% key: a
#% type: double
#% description: Coefficients for walking energy formula parameters a,b,c,d
#% answer: 0.72
#% required : no
#%END
#%option
#% key: b
#% type: double
#% description:
#% answer: 6.0
#% required : no
#%END
#%option
#% key: c
#% type: double
#% description:
#% answer: 1.9998
#% required : no
#%END
#%option
#% key: d
#% type: double
#% description:
#% answer: -1.9998
#% required : no
#%END
#%option
#% key: lambda
#% type: double
#% description: Lambda value for cost distance calculation
#% answer: 0
#% required : no
#%END
#%option
#% key: slope_factor
#% type: double
#% description: Slope factor determines travel energy cost per height step
#% answer: -0.2125
#% required : no
#%END
#%option
#% key: buffer
#% type: string
#% gisprompt: old,cell,raster
#% description: Output buffer map
#% required : yes
#%END
#%option
#% key: sigma
#% type: double
#% description: Slope threshold for mask
#% answer: 
#% required : no
#%END
#%option
#% key: area
#% type: integer
#% description: Area of buffer (Integer value to nearest 100 square map units)
#% answer: 5000000
#% required : yes
#%END
#%option
#% key: mapval
#% type: integer
#% description: Integer value for output catchment area (all other areas will be Null)
#% answer: 1
#% required : yes
#%END
#%flag
#% key: k
#% description: -k Use knight's move for calculating cost surface (slower but more accurate)
#%END
#%flag
#% key: c
#% description: -c Keep cost surface used to calculate buffers
#%END
#%flag
#% key: l
#% description: -l Show a list of all cost surface values and the area of the catchment that they delimit
#%END


import sys
import os
import subprocess
import tempfile
import random
grass_install_tree = os.getenv('GISBASE')
sys.path.append(grass_install_tree + os.sep + 'etc' + os.sep + 'python')
import grass.script as grass
# first define a useful custom method 

# m is a grass/bash command that will generate some list of keyed info to stdout where the keys are numeric values, n is the character that separates the key from the data, o is a defined blank dictionary to write results to
def out2dictnum(m, n, o):
    p1 = subprocess.Popen('%s' % m, stdout=subprocess.PIPE, shell='bash')
    p2 = p1.stdout.readlines()
    for y in p2:
        y0,y1 = y.split('%s' % n)
        y0num = float(y0)
        o[y0num] = y1.strip('\n')

#main block of code starts here
def main():
    #setting up variables for use later on
    elev = os.getenv('GIS_OPT_elev')
    vect = os.getenv('GIS_OPT_vect')
    lmbda = os.getenv('GIS_OPT_lambda')
    slpfct = os.getenv('GIS_OPT_slope_factor')
    a = os.getenv('GIS_OPT_a')
    b = os.getenv('GIS_OPT_b')
    c = os.getenv('GIS_OPT_c')
    d = os.getenv('GIS_OPT_d')
    sigma = os.getenv('GIS_OPT_sigma')
    area = float(os.getenv('GIS_OPT_area'))
    buffer = os.getenv('GIS_OPT_buffer')
    mapval = os.getenv('GIS_OPT_mapval')
    w_coefs = a + ',' +  b + ',' + c + ',' + d
    if "MASK" in grass.list_grouped('rast')[grass.gisenv()['MAPSET']] and bool(os.getenv('GIS_OPT_sigma')) is True:
        grass.message('There is already a MASK in place, and you have also selected to mask slope values above %s.\n The high slope areas (slope mask) will be temporarily added to current MASKED areas for the calcualtion of the catchment geometry.\n The original MASK will be restored when the module finishes' % sigma)
        ismask = 2
    elif "MASK" in grass.list_grouped('rast')[grass.gisenv()['MAPSET']]:
        grass.message('There is a MASK in place. The areas MASKed out will be ignored while calculating catchment geometry.')
        ismask = 1
    else:
        ismask = 0
    
    grass.message("Wanted buffer area=%s\n" % int(area)) 

####################################################
    if bool(os.getenv('GIS_OPT_incost')) is True:
        grass.message('\n\nUsing input cost surface\n')
        cost = os.getenv('GIS_OPT_incost')
    else:
        grass.message('\n\nstep 1 of 4: Calculating cost surface\n')
        cost = 'temporary.cost'
        if bool(os.getenv('GIS_OPT_frict')) is True:
            grass.message('Calculating costs using input friction map\n')
            frict = os.getenv('GIS_OPT_frict')
        else:
            grass.message('Calculating for time costs only')
            frict = "temporary.friction"
            grass.mapcalc("${out} = if(isnull(${rast1}), null(), 1)",  out = frict,  rast1 = elev)
        if os.getenv('GIS_FLAG_k') == '1':
            grass.message('Using Knight\'s move\n')
            #NOTE! because "lambda" is an internal python variable, it is impossible to enter the value for key "lambda" in r.walk. It ends up with a python error.
            grass.run_command('r.walk', quiet = True, flags = 'k', elevation = elev, friction = frict, output = cost, start_points = vect, walk_coeff = w_coefs, slope_factor = slpfct)
        else:
            grass.run_command('r.walk', quiet = True, elevation = elev, friction = frict, output = cost, start_points = vect, percent_memory = '100', nseg ='4', walk_coeff = w_coefs, slope_factor = slpfct)
        if bool(os.getenv('GIS_OPT_frict')) is False:
            grass.run_command('g.remove', quiet = True,  rast = frict)
#################################################   
    if bool(os.getenv('GIS_OPT_sigma')) is True:
        grass.message('\n\nCreating optional slope mask\n')
        slope = "temporary.slope"
        grass.run_command('r.slope.aspect', quiet = True, overwrite = True,  elevation = elev,  slope = slope)
        if ismask == 2:
            grass.mapcalc("MASK=if(${rast1} <= %s, 1, if(${tempmask}, 1, null()))" % sigma,  rast1 = slope,  tempmask = tempmask)
        else:
            grass.mapcalc("MASK=if(${rast1} <= %s, 1, null())" % sigma,  rast1 = slope)
    else:
        grass.message('No slope mask created')
##################################################
    if os.getenv('GIS_FLAG_l') == '1':
            grass.message('\n\nCalculating list of possible catchment configurations\n')
            grass.message("cost value | catchment area")
            areadict = {}
            out2dictnum('r.stats -Aani input=' + cost + ' fs=, nv=* nsteps=255', ',', areadict)
            testarea = 0
            #start the loop, and list the values
            for key in sorted(areadict):
                testarea = testarea +  int(float(areadict[key]))
                grass.message("%s | %s" % (int(key),  testarea))
            if os.getenv('GIS_FLAG_c') == '1':
                if bool(os.getenv('GIS_OPT_incost')) is False:
                    grass.run_command('g.rename',  quiet = True,  rast = 'temporary.cost,%s_cost_surface' % (buffer))
                    grass.message('Cleaning up...(keeping cost map)')
                    grass.run_command('g.remove',  quiet = True, rast='cost.reclass')
                else:
                    grass.message('Cleaning up...1')
                    grass.run_command('g.remove',  quiet = True, rast='cost.reclass')
            else:
                if bool(os.getenv('GIS_OPT_incost')) is False:
                    grass.message('Cleaning up...2')
                    grass.run_command('g.remove',  quiet = True, rast = 'cost.reclass,temporary.cost')
                else:
                    grass.message('Cleaning up...3')
                    grass.run_command('g.remove',  quiet = True, rast = 'cost.reclass')
            if bool(os.getenv('GIS_OPT_sigma')) is True:
                grass.run_command('g.remove',  quiet = True, rast = slope)
            if ismask == 2:
                grass.message('Reinstating original MASK...')
                grass.run_command('g.rename', quiet = "True", rast = tempmask +',MASK')
            elif ismask == 0 and bool(os.getenv('GIS_OPT_sigma')) is True:
                grass.run_command('g.remove',  quiet = True, rast = 'MASK')
            elif ismask == 1:
                grass.message('Keeping original MASK')
            grass.message('     DONE!')
            return
    else:
        grass.message('\n\nCalculating buffer\n')
        areadict = {}
        out2dictnum('r.stats -Aani input=' + cost + ' fs=, nv=* nsteps=255', ',', areadict)
        tot_area = 0
        for key in sorted(areadict):
            tot_area = tot_area + int(float(areadict[key]))
            maxcost = key
        grass.message("Maximum cost distance value %s covers an area of %s square map units\n\nCommencing to find a catchment configuration.....\n\n" % (int(maxcost),  tot_area))
        testarea = 0
        lastarea = 0
        lastkey = 0
        #start the loop, and home in on the target range
        for key in sorted(areadict):
            testarea = testarea +  int(float(areadict[key]))
            if testarea >= area:
                break
            lastkey = key
            lastarea = testarea
        if (testarea - area) <= (area - lastarea):
            cutoff = key
            displayarea = testarea
        else:
            cutoff = lastkey
            displayarea = lastarea
        grass.message("Catchment configuration found! Cost cutoff %s produces a catchment of %s square map units." % (int(cutoff),  displayarea))
    ####################################################
        grass.message('\n\nCreating output map\n')
        temp = tempfile.NamedTemporaryFile()
        temp.write('0 thru %s = %s\n' % (int(cutoff),  mapval))
        temp.flush()
        grass.run_command('r.reclass', overwrite = True,  input = cost,  output = 'cost.reclass',  rules = temp.name)
        temp.close()
        grass.mapcalc("${out}=if(isnull(cost.reclass), null(), cost.reclass)", out = buffer)
        grass.message("\nThe output catchment map will be named %s" % buffer)
        grass.run_command('r.colors', quiet = True,  map = buffer, color = 'ryb')
        if os.getenv('GIS_FLAG_c') == '1':
            if bool(os.getenv('GIS_OPT_incost')) is False:
                grass.run_command('g.rename',  quiet = True,  rast = 'temporary.cost,%s_cost_surface' % (buffer))
                grass.message('Cleaning up...(keeping cost map)')
                grass.run_command('g.remove',  quiet = True, rast='cost.reclass')
            else:
                grass.message('Cleaning up...1')
                grass.run_command('g.remove',  quiet = True, rast='cost.reclass')
        else:
            if bool(os.getenv('GIS_OPT_incost')) is False:
                grass.message('Cleaning up...2')
                grass.run_command('g.remove',  quiet = True, rast = 'cost.reclass,temporary.cost')
            else:
                grass.message('Cleaning up...3')
                grass.run_command('g.remove',  quiet = True, rast = 'cost.reclass')
            if bool(os.getenv('GIS_OPT_sigma')) is True:
                grass.run_command('g.remove',  quiet = True, rast = slope)
            if ismask == 2:
                grass.message('Reinstating original MASK...')
                grass.run_command('g.rename', quiet = "True", rast = tempmask +',MASK')
            elif ismask == 0 and bool(os.getenv('GIS_OPT_sigma')) is True:
                grass.run_command('g.remove',  quiet = True, rast = 'MASK')
            elif ismask == 1:
                grass.message('Keeping original MASK')
        grass.message('     DONE!')
        return

# here is where the code in "main" actually gets executed. This way of programming is necessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()
