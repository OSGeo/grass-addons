#!/usr/bin/env python
############################################################################
#
# MODULE:	   r.mcda.electre
# AUTHOR:	   Gianluca Massei - Antonio Boggia
# PURPOSE:	   Elaborate several criteria maps and gets concordance and 
#				discordance maps indices as a base for electre analysis	 
# COPYRIGHT:  c) 2010 Gianluca Massei, Antonio Boggia  and the GRASS 
#					   Development Team. This program is free software under the 
#					   GNU General PublicLicense (>=v2). Read the file COPYING 
#					   that comes with GRASS for details.
#
#############################################################################
#%module
#% description: Gets concordance and discordance maps indices for MCDA analysis
#% keyword: raster
#% keyword: criteria maps
#% keyword: MCDA
#%end
#%option G_OPT_R_INPUTS
#% key: criteria
#% multiple: yes
#% gisprompt: old,cell,raster
#% key_desc: name
#% description: Name of criteria raster maps 
#% required: yes
#%end
#%option
#% key: weights
#% type: double
#% description: weights (w1,w2,...,wn)
#% multiple: yes
#% required: yes
#%end
#%option G_OPT_R_OUTPUT
#% key: concordancemap
#% type: string
#% gisprompt: new_file,cell,output
#% description: output concordance raster map
#% answer:concordance
#% required: yes
#%end
#%option G_OPT_R_OUTPUT
#% key: discordancemap
#% type: string
#% gisprompt: new_file,cell,output
#% description: output discordance raster map
#% answer:discordance
#% required: yes
#%end


import sys

import grass.script as gscript
from grass.pygrass import raster


def preprocessing(attributes,weights):
	matrix=[]
	for attribute in attributes:
		c=[]
		criteria = raster.RasterRowIO(str(attribute))
		#criteria.is_open()
		criteria.open('r')
		for row in criteria: 
			c.append(row)
		matrix.append(c)
		criteria.close()
	print len(matrix),weights
	print dir(criteria)

def concordance(attributes,weights,concordanceMap):
	i=0
	listMaps=[]
	for attrRow,weight in zip(attributes,weights):
		for attrCol in attributes:
			concordanceMap="conc_%s" % str(i)
			formula="%s=if(%s>%s,%s,0)" % (concordanceMap,attrRow.split('@')[0],attrCol.split('@')[0],weight)
			gscript.mapcalc(formula,overwrite = True)
			listMaps.append(concordanceMap)
			i=i+1
	endMap="%s=%s" % (concordanceMap,("+".join(listMaps)))
	gscript.mapcalc(endMap,overwrite = True)
	gscript.run_command("g.remove", type='raster',flags='f', name=",".join(listMaps))
	return 0


def discordance(attributes,discordanceMap):
	i=0
	listMaps=[]
	for attrRow in attributes:
		for attrCol in attributes:
			discordanceMap="conc_%s" % str(i)
			formula="%s=if(%s>%s,%s-%s,0)" % (discordanceMap,attrRow.split('@')[0],attrCol.split('@')[0],attrRow.split('@')[0],attrCol.split('@')[0])
			gscript.mapcalc(formula,overwrite = True)
			listMaps.append(discordanceMap)
			i=i+1
	endMap="%s=max(%s)" % (discordanceMap,("+".join(listMaps)))
	gscript.mapcalc(endMap,overwrite = True)
	gscript.run_command("g.remove", type='raster',flags='f', name=",".join(listMaps))
	return 0

def main():
	options, flags = gscript.parser()
	attributes = options['criteria'].split(',')
	weights = options['weights'].split(',')
	concordanceMap= options['concordancemap']
	discordanceMap= options['discordancemap']
	concordance(attributes,weights,concordanceMap) 
	discordance(attributes,discordanceMap)
	return 0


if __name__ == "__main__":
    sys.exit(main())
