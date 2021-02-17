#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################################
#
# MODULE:	r.diversity
# AUTHOR(S):	Luca Delucchi
# PURPOSE:	It calculates the mostly used indices of diversity based on 
#		information theory
#
# COPYRIGHT: (C) 2010-2012 by Luca Delucchi
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%module
#% description: Calculate diversity indices based on a moving window using r.li packages
#% keywords: raster
#%end
#%option
#% key: input
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: name
#% description: Name of input raster map 
#% required: yes
#%end 
#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% key_desc: name
#% description: Name of output raster map 
#% required: yes
#%end 
#%option
#% key: alpha
#% type: double
#% key_desc: alpha value for Renyi entropy
#% description: Order of generalized entropy (> 0.0; undefined for 1.0)
#% multiple: yes
#% required: no
#%end
#%option
#% key: size
#% type: integer
#% key_desc: moving window
#% multiple: yes
#% description: Size of processing window (odd number only)
#% answer: 3
#% required: no
#%end 
#%option
#% key: method
#% type: string
#% key_desc: method
#% options: simpson,shannon,pielou,renyi
#% multiple: yes
#% description: Name of methods to use
#% required: no
#%end
#%option
#% key: exclude
#% type: string
#% key_desc: exclude method
#% options: simpson,shannon,pielou,renyi
#% multiple: yes
#% description: Exclude methods
#% required: no
#%end


# import library
import os, sys, re
import grass.script as grass

# main function
def main():
    # set the home path
    home=os.path.expanduser('~')
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
    alpha = options['alpha']
    # method to use
    methods = options['method']
    # excluded method
    excludes = options['exclude']


    resolution = checkValues(res)

    if alpha != '':
        alpha_value = checkValues(alpha,True)
        print alpha_value

    # check if ~/.r.li path exists
    if not os.path.exists(home + '/.r.li'):
        # create ~/.r.li
        os.mkdir(home + '/.r.li')
        # create ~/.r.li/history
        os.mkdir(home + '/.r.li/history')
    else:
        if not os.path.exists(home + '/.r.li/history'):
            # create ~/.r.li/history
            os.mkdir(home + '/.r.li/history')

    # set overwrite
    if grass.overwrite():
        env['GRASS_OVERWRITE'] = '1'

    # if method and exclude option are not null return an error
    if methods != '' and excludes != '':
        print "You can use method or exclude option not both"
        sys.exit(1)
    # if method and exclude option are null calculate all module
    elif methods == '' and excludes == '':
        # check if alpha_value is set, else return an error
        if alpha_value == '':
            print "Please you must set alpha value for Renyi entropy"
            sys.exit(1)	    
        calculateAll(home, map_in, map_out, resolution, alpha_value)
    # calculate method
    elif methods != '':
        methods = methods.split(',')
        checkAlpha(methods,alpha_value)
        calculateM(home, map_in, map_out, resolution, alpha_value,methods)
    # calculate not excluded index
    elif excludes != '':
        excludes = excludes.split(',')
        checkAlpha(excludes,alpha_value,True)
        calculateE(home, map_in, map_out, resolution, alpha_value,excludes)

    # remove configuration files
    removeConfFile(resolution,home)
    print 'All works are terminated'

# calculate all index
def calculateAll(home, map_in, map_out, res, alpha):
    # for each resolution create the config file and calculate all index
    for r in res:
        createConfFile(r,map_in,home)
        r = str(r)	
        grass.run_command('r.li.simpson', map = map_in, out = map_out + 
        '_simpson_size_' + r, conf = 'conf_diversity_' + r)
        grass.run_command('r.li.shannon', map = map_in, out = map_out + 
        '_shannon_size_' + r, conf = 'conf_diversity_' + r)
        grass.run_command('r.li.pielou', map = map_in, out = map_out + 
        '_pielou_size_' + r, conf = 'conf_diversity_' + r)
        for alp in alpha:
            grass.run_command('r.li.renyi', map = map_in, out = map_out+ 
            '_renyi_size_' + r + '_alpha_'+ str(alp), conf = 
            'conf_diversity_' + r, alpha = alp)  

# calculate only method included in method option
def calculateM(home, map_in, map_out, res, alpha, method):
    # for each resolution create the config file
    for r in res:
        createConfFile(r,map_in,home)
        r = str(r)	
        # for each method in method option calculate index
        for i in method:
            if i == 'renyi':
                for alp in alpha:
                    grass.run_command('r.li.renyi', map = map_in, out = 
                    map_out + '_renyi_size_' + r + '_alpha_' + str(alp), 
                    conf = 'conf_diversity_' + r, alpha = alp)
            else:
                grass.run_command('r.li.' + i, map = map_in, out = map_out + 
                '_' + i + '_size_' + r, conf = 'conf_diversity_' + r)

# calculate only method excluded with exclude option
def calculateE(home, map_in, map_out, res, alpha, method):
    # set a tuple with all index 
    methods = ('simpson','shannon','pielou','renyi')
    # for each resolution create the config file    
    for r in res:
        createConfFile(r,map_in,home)
        r = str(r)	
        # for each method
        for i in methods:
            # if method it isn't in exclude option it is possible to calculate
            if method.count(i) == 0:
                if i == 'renyi':
                    for alp in alpha:
                        grass.run_command('r.li.renyi', map = map_in, out = 
                        map_out + '_renyi_size_' + r + '_alpha_' + str(alp), 
                        conf = 'conf_diversity_' + r, alpha = alp)
                else:
                    grass.run_command('r.li.' + i, map = map_in, out = map_out +
                    '_' + i+ '_size_' + r, conf = 'conf_diversity_' + r)

# check if alpha value it's set when renyi entropy must be calculate
def checkAlpha(method,alpha_val,negative=False):
    for alpha in alpha_val:
        # it's used when we check the exclude option
        if negative:
            if method.count('renyi') != 1 and alpha == '':
                print "Please you must set alpha value for Renyi entropy"
                sys.exit(1)
        # it's used when we check the method option    
        else:
            if method.count('renyi') == 1 and alpha == '':
                print "Please you must set alpha value for Renyi entropy"
                sys.exit(1)

#create configuration file instead using r.li.setup
def createConfFile(res,inpumap,home):
    # set the name of conf file
    confilename = home + '/.r.li/history/conf_diversity_' + str(res)  
    # start the text for the conf file
    outputLine = ['SAMPLINGFRAME 0|0|1|1\n']
    # return r.info about input file
    rinfo = grass.raster_info(inpumap)
    # calculate number of lines
    rows = (rinfo["north"]-rinfo["south"])/rinfo['nsres']
    # calculate number of columns
    columns = (rinfo['east']-rinfo['west'])/rinfo['ewres']
    # value for row
    rV = int(res)/rows
    # value for column
    cV = int(res)/columns
    # append the text for the conf file
    outputLine.append('SAMPLEAREA -1|-1|'+str(rV)+'|'+str(cV)+'\n')
    outputLine.append('MOVINGWINDOW\n')
    # open configuration file
    fileConf=open(confilename,'w')
    # write file 
    fileConf.writelines(outputLine)
    # close file
    fileConf.close()

# return a list of resolution
def checkValues(res,alpha=False):
    # check if more values are passed
    if res.count(',') == 1:
        typ = 'values'
        reso = res.split(',')
    # check if a range of values are passed	  
    elif res.count('-') == 1:
        typ = 'range'
        reso = res.split('-')
    # else only a value is passed
    else:
        typ = 'value'
        reso = [res]
    # trasforn string to int and check if is a odd number
    for i in range(len(reso)):
        # check if is a odd number
        reso[i] = float(reso[i])
        if reso[i] % 2 == 0:
            # return the error advice
            print "Your size option could not contain odd number"
            sys.exit(1)
    # create a range
    if typ == 'range':
        if alpha:
            print "Range for alpha values it isn't supported"
            sys.exit(1)
        else:
            reso = range(reso[0],reso[1]+1,2)
    return reso

def removeConfFile(res,home):
    for r in res:
        confilename = home + '/.r.li/history/conf_diversity_' + str(r)
        os.remove(confilename)

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())

