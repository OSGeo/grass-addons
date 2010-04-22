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
#%  description: Creates a raster buffer of specified area around vector points using cost distances. Requires r.walk.
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
#% key: deviation
#% type: integer
#% description: Percentage to which output buffer can differ from desired buffer size (large values decrease run-time, but results will be less precise) 
#% answer: 10
#% required : yes
#%END
#%option
#% key: mapval
#% type: integer
#% description: Integer vlaue for out put catchment area (all other areas will be Null)
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


import sys
import os
import subprocess
import tempfile
# first define some useful custom methods

# m is a message (as a string) one wishes to have printed in the output window
def grass_print(m):
	subprocess.Popen('g.message message="%s"' % m, shell='bash').wait()
	return
# m is grass (or bash) command to execute (written as a string). script will wait for grass command to finish
def grass_com(m):
	subprocess.Popen('%s' % m, shell='bash').wait()
	return
# m is grass (or bash) command to execute (written as a string). script will not wait for grass command to finish
def grass_com_nw(m):
	subprocess.Popen('%s' % m, shell='bash')
	return
# m is a grass/bash command that will generate some info to stdout. You must invoke this command in the form of "variable to be made" = out2var('command')
def out2var(m):
        pn = subprocess.Popen('%s' % m, stdout=subprocess.PIPE, shell='bash')
        return pn.stdout.read()

# m is a grass/bash command that will generate some list of keyed info to stdout, n is the character that seperates the key from the data, o is a defined blank dictionary to write results to
def out2dict(m, n, o):
    p1 = subprocess.Popen('%s' % m, stdout=subprocess.PIPE, shell='bash')
    p2 = p1.stdout.readlines()
    for y in p2:
        y0,y1 = y.split('%s' % n)
        o[y0] = y1.strip('\n')

# m is a grass/bash command that will generate some charcater seperated list of info to stdout, n is the character that seperates individual pieces of information, and  o is a defined blank list to write results to
def out2list2(m, n, o):
        p1 = subprocess.Popen('%s' % m, stdout=subprocess.PIPE, shell='bash')
        p2 = p1.stdout.readlines()
        for y in p2:
            y0,y1 = y.split('%s' % n)
            o.append(y0)
            o.append(y1.strip('\n'))

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
    deviation = area*(float(os.getenv('GIS_OPT_deviation'))/100)
    buffer = os.getenv('GIS_OPT_buffer')
    mapval = os.getenv('GIS_OPT_mapval')

    grass_print("Wanted buffer area=%s\n" % int(area)) 
    grass_com('g.region --quiet rast=' + elev)
####################################################
    if bool(os.getenv('GIS_OPT_incost')) is True:
        grass_print('\n\nstep 1 of 4: Using input cost surface\n')
        cost = os.getenv('GIS_OPT_incost')
    else:
        grass_print('\n\nstep 1 of 4: Calculating cost surface\n')
        cost = 'temporary.cost'
        if bool(os.getenv('GIS_OPT_frict')) is True:
            grass_print('Calculating costs using input friction map\n')
            frict = os.getenv('GIS_OPT_frict')
        else:
            grass_print('Calculating for time costs only')
            frict = "temporary.friction"
            grass_com('r.mapcalc "' + frict + '=if(isnull(' + elev + '), null(), 1)"')
        if os.getenv('GIS_FLAG_k') == '1':
            grass_print('Using Knight\'s move\n')
            grass_com('r.walk --quiet -k elevation=' + elev + ' friction=' + frict + ' output=' + cost +' start_points=' + vect + ' lambda=' + lmbda + ' percent_memory=100 nseg=4 walk_coeff=' + a + ',' + b + ',' + c + ',' + d + ' slope_factor=' + slpfct)
        else:
            grass_com('r.walk --quiet elevation=' + elev + ' friction=' + frict + ' output=' + cost +' start_points=' + vect + ' lambda=' + lmbda + ' percent_memory=100 nseg=4 walk_coeff=' + a + ',' + b + ',' + c + ',' + d + ' slope_factor=' + slpfct)
        if bool(os.getenv('GIS_OPT_frict')) is False:
            grass_com('g.remove --quiet rast=' + frict)
#################################################   
    grass_print('\n\nstep 2 of 4: Creating optional slope mask\n')
    if bool(os.getenv('GIS_OPT_sigma')) is True:
        slope = "temporary.slope"
        grass_com('r.slope.aspect --quiet --overwrite elevation=' + elev + ' slope=' + slope)
        grass_com('r.mapcalc "MASK=if(' + slope + ' <= ' + sigma + ', 1, null())"')
    else:
        grass_print('no slope mask created')
##################################################
    grass_print('\n\nstep 3 of 4: Calculating buffer\n')
    #set up for loop by getting initial variables from map
    costdict = {}
    out2dict('r.univar -g map=%s' % cost,'=' , costdict)
    maxcost = float(costdict['max'])
    grass_print("\nMaximum cost distance value= %s\n" % maxcost)
    arealist = []
    out2list2('r.stats -a -n input=' + cost + ' fs=, nv=* nsteps=1', ',', arealist)
    maxarea = int(float(arealist[1]))
    grass_print('Total map area = %s' % maxarea)
    cutoff = maxcost
    mincost = 0.0
    testarea = maxarea
    # set up error trap to prevent infinite loops
    lastcut = 0
    #start the loop, and home in on the target range
    while testarea not in range((int(area)-int(deviation)),(int(area)+(int(deviation)+1))) and round(lastcut) != round(cutoff):
        lastcut = cutoff
        if testarea > area:
            maxcost = cutoff
            cutoff = (maxcost+mincost)/2.0
        else:
            mincost = cutoff
            cutoff = (maxcost+mincost)/2.0
        temp = tempfile.NamedTemporaryFile()
        temp.write('0 thru %s = %s\n' % (int(cutoff),  mapval))
        temp.flush()
        grass_print('0 thru %s = %s\n' % (int(cutoff),  mapval))
        grass_com('r.reclass --overwrite --quiet input=%s output=cost.reclass rules=%s' % (cost,  temp.name))
        temp.close()
        arealist = []
        out2list2('r.stats -a -n input=cost.reclass fs=, nv=* nsteps=1', ',', arealist)
        testarea = int(float(arealist[1]))
        grass_print('\nTesting with cost distance value = %s......\ncurrent area = %s\n' % (cutoff,  testarea))
    #loop is done, so print the final stats
    difference = testarea-area
    grass_print('\n\n*************************\n\n Final cost distance cutoff of %s produces a catchment of %s square meters.\nThe difference from the requested catchment size is %s square meters.' % (cutoff,  testarea,  difference))
####################################################
    grass_print('\n\nstep 4 of 4: Creating output map\n')
    grass_com('r.mapcalc "%s=if(isnull(cost.reclass), null(), cost.reclass)"' % buffer)
    grass_print(buffer)
    grass_com('r.colors --quiet map=%s color=ryb' % buffer)
    if os.getenv('GIS_FLAG_c') == '1':
        if bool(os.getenv('GIS_OPT_incost')) is False:
            grass_com('g.rename temporary.cost,' + buffer + '_cost_surface')
            grass_print('Cleaning up...(keeping cost map)')
            grass_com('g.remove --quiet rast=cost.reclass')
        else:
            grass_print('Cleaning up...1')
            grass_com('g.remove --quiet rast=cost.reclass')
    else:
        if bool(os.getenv('GIS_OPT_incost')) is False:
            grass_print('Cleaning up...2')
            grass_com('g.remove --quiet rast=cost.reclass,temporary.cost' )
        else:
            grass_print('Cleaning up...3')
            grass_com('g.remove --quiet rast=cost.reclass')
    if bool(os.getenv('GIS_OPT_sigma')) is True:
        grass_com('g.remove --quiet rast=' + slope)
    grass_com('g.remove --quiet rast=MASK')
    grass_print('     DONE!')
    return

# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()
