#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################################
#
# MODULE:	r.diversity
# AUTHOR(S):	Luca Delucchi
# PURPOSE:	It calculates the mostly used indices of diversity based on 
#		information theory
#
# COPYRIGHT:	(C) 2010 by Luca Delucchi
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%module
#% description: Calculate some vegetation index using r.li packages and moving windows
#% keywords: raster
#%end
#%option
#% key: input
#% type: string
#% gisprompt: input raster
#% key_desc: name
#% description: Name of input raster map 
#% required: yes
#%end 
#%option
#% key: output
#% type: string
#% gisprompt: output raster
#% key_desc: name
#% description: Name of output raster map 
#% required: yes
#%end 
#%option
#% key: alpha
#% type: double
#% gisprompt: alpha value
#% key_desc: alpha value for Renyi entropy
#% description: Alpha value is the order of the generalized entropy, it'll be > 0 and != 1
#% required: yes
#%end
#%option
#% key: size
#% type: integer
#% gisprompt: resolution
#% key_desc: moving window
#% description: Number of pixel used for the moving window, it must be odd number, if not set the module set your resolution to value 3 
#% required: no
#%end 
 

# import library
import os, sys, re
import grass.script as grass

# main function
def main():
    # set the home path
    home=os.path.expanduser('~')
    # set the name of conf file
    confilename = home+'/.r.li/history/conf_diversity'
    # check if GISBASE is set
    if "GISBASE" not in os.environ:
	# return an error advice
	print "You must be in GRASS GIS to run this program."
	sys.exit(1)

    # input raster map
    map_in = options['input']
    # output raster map
    map_out = options['output']
    # resolution of moving windows
    res = options['size']
    # alpha value for r.renyi
    alpha_value = options['alpha']
    # resolution
    if res=='':
	res=3
    else:
	res = int(options['size'])

    # check if is a odd number
    if res%2==0:
	# return the error advice
	print "Your size option must be an odd number"
	sys.exit(1)
    # check if ~/.r.li path exists
    if os.path.exists(home+'/.r.li/'):
	# check if ~/.r.li/history path exists
	if os.path.exists(home+'/.r.li/history'):
	    # create configuration file
	    createConfFile(res,map_in,confilename)
	else:
	    # create ~/.r.li/history path
	    os.path.mkdir(home+'/.r.li/history')
	    # create configuration file
	    createConfFile(res,map_in,confilename)
    else:
	# create ~/.r.li
	os.path.mkdir(home+'/.r.li/')
	# create ~/.r.li/history
	os.path.mkdir(home+'/.r.li/history')
	# create configuration file
	createConfFile(res,map_in,confilename)


    ### calculate r.li indices
    # if overwrite it is set
    if grass.overwrite():
        env['GRASS_OVERWRITE'] = '1'

    simpson = grass.run_command('r.li.simpson', map = map_in, out = map_out + '_simpson', conf = 'conf_diversity')
    shannon = grass.run_command('r.li.shannon', map = map_in, out = map_out+ '_shannon', conf = 'conf_diversity')
    pielou = grass.run_command('r.li.pielou', map = map_in, out = map_out+ '_pielou', conf = 'conf_diversity')
    renyi = grass.run_command('r.li.renyi', map = map_in, out = map_out+ '_renyi_' + str(alpha_value), conf = 'conf_diversity', alpha = alpha_value)
    
    os.remove(confilename)
    print 'All works are terminated'

#create configuration file instead using r.li.setup
def createConfFile(res,inpumap,filename):
    # start the text for the conf file
    outputLine = ['SAMPLINGFRAME 0|0|1|1\n']
    # return r.info about input file
    rinfo = grass.raster_info(inpumap)
    # calculate number of lines
    rows = (rinfo["north"]-rinfo["south"])/rinfo['nsres']
    # calculate number of columns
    columns = (rinfo['east']-rinfo['west'])/rinfo['ewres']
    # value for row
    rV = res/rows
    # value for column
    cV = res/columns
    # append the text for the conf file
    outputLine.append('SAMPLEAREA -1|-1|'+str(rV)+'|'+str(cV)+'\n')
    outputLine.append('MOVINGWINDOW\n')
    # open configuration file
    fileConf=open(filename,'w')
    # write file 
    fileConf.writelines(outputLine)
    # close file
    fileConf.close()

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())

