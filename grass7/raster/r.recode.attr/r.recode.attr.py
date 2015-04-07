#!/usr/bin/env python
# -*- coding: utf-8 -*-

########################################################################
# 
# MODULE:       r.recode_attribute
# AUTHOR(S):    Paulo van Breugel <p.vanbreugel AT gmail.com>
# PURPOSE:      Recode raster to one or more new layers using an
#               attribute table (csv file) as input
#
# COPYRIGHT: (C) 2014 Paulo van Breugel
#            http://ecodiv.org
#            http://pvanb.wordpress.com/
# 
#            This program is free software under the GNU General Public 
#            License (>=v2). Read the file COPYING that comes with GRASS 
#            for details. 
# 
########################################################################
#
#%Module 
#% description: Recode raster using attribute table (csv file) as input
#% keyword: raster
#% keyword: recode
#%End 

#%option
#% key: input
#% type: string
#% gisprompt: old,cell,raster
#% description: Input map
#% key_desc: name
#% required: yes
#% multiple: no
#%end

#%option
#% key: output
#% type: string
#% gisprompt: old,cell,raster
#% description: name(s) output layer(s)
#% key_desc: name
#% required: yes
#% multiple: no
#%end

#%option G_OPT_F_INPUT
#% key: rules
#% label: Full path to rules file
#% required: yes
#%end

# import libraries
import os
import sys
import numpy as np
from tempfile import gettempdir, gettempprefix
from os.path import join
from string import ascii_lowercase, digits
from random import choice
import grass.script as grass

def cleanup():
	grass.run_command('g.remove', 
      type = 'raster', 
      pattern = 'tmp_map',
      flags='f',
      quiet = True)

def CreateFileName():
    (suffix1, suffix2) = ("", "")
    for _ in xrange( 8 ):
        suffix1 += choice( ascii_lowercase )
        suffix2 += choice( digits )
    flname = join(gettempdir(), '-'.join([gettempprefix(), suffix1, suffix2 ]))
    while os.path.isfile(flname):
        flname = flname + "1"
    return flname

# main function
def main():
    
    # check if GISBASE is set
    if "GISBASE" not in os.environ:
    # return an error advice
       grass.fatal(_("You must be in GRASS GIS to run this program"))
       
    # input raster map and parameters   
    inputmap = options['input']
    outBase = options['output']
    rules = options['rules']
    outNames = outBase.split(',')
    lengthNames = len(outNames)
    
    # Get attribute data
    myData = np.genfromtxt(rules, delimiter=',', skip_header=1)
    nmsData = np.genfromtxt(rules, delimiter=',', names=True)
    dimData = myData.shape
    nmsData = nmsData.dtype.names
          
    # Create recode maps
    numVar = xrange(dimData[1]-1)
    for x in numVar:
        y = x + 1
        myRecode = np.column_stack((myData[:,0], myData[:,0], myData[:,y]))
        tmpname = CreateFileName()
        np.savetxt(tmpname, myRecode, delimiter=":") 
        
        if len(numVar) == lengthNames:
            nmOutput = outNames[x]
        else:
            nmOutput = outNames[0] + '_' + nmsData[y]
            
        grass.run_command('r.recode',
                input = inputmap, 
                output = nmOutput,
                rules = '.numpy_grass_recode')
        
        os.remove('.numpy_grass_recode') 


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())

