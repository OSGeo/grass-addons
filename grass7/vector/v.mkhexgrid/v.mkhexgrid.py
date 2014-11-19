#!/usr/bin/env python

############################################################################
#
# MODULE:	v.mkhexgrid 
#            derived from v.mkhexgrid for GRASS 6.4 (2010-11-23)
#               modified (2011-09-14)
#                   - use of sql update over db.in.ogr because of 
#                     difficulty diagnosing error in db.in.ogr with 
#                     fields causing erroneous error messages
#
# AUTHOR(S):	Trevor Wiens
#               Some GRASS GIS 7 updates by Markus Neteler
#
# PURPOSE:      Makes a hexagonal grid
#
# COPYRIGHT:	(C) 2010-2014 GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
# EXAMPLE:
#     v.mkhexgrid map=test regionname=default@PERMANENT sidelength=1000
#
#############################################################################

#%Module
#%  description: Creates a hexagonal grid.
#%  keywords: vector
#%  keywords: geometry
#%  keywords: grid
#%  keywords: hexagon
#%End
#%option G_OPT_V_OUTPUT
#%  key: map
#%end
#%option
#%  key: regionname
#%  type: string
#%  gisprompt: old,windows,region
#%  label: Named region to set size of output grid
#%  description: Named region for geographic extent of region to survey
#%  required: yes
#%end
#%option
#%  key: method
#%  type: string
#%  options: sidelength,area
#%  answer: area
#%  description: Method to calculate size
#%  multiple: no
#%  required: no
#%end
#%option
#%  key: sidelength
#%  type: double
#%  label: Side length
#%  answer: 100.0
#%  description: Size of side length in map units
#%  required: no
#%end
#%option
#%  key: hexarea
#%  type: double
#%  label: Hexagon Area
#%  answer: 200.0
#%  description: Area of hexagon in map units
#%  required: no
#%end

import sys
import os
import subprocess
import time
import math
from grass.script import core as grass
from grass.script import db as gdb
from grass.script.utils import try_rmdir

#
# WriteHexGridVectors - Using basic trig and the fact that hexagons are constructed from 6 equalateral triangles
#                       hexagons are created
#
#

def WriteHexGridVectors(vf, sf, table_name, side_len, xstart, ystart, xlimit, ylimit):
    
    # basic trig
    angle_a = math.radians(30)
    hyp = side_len
    side_b = hyp * math.cos(angle_a)
    side_a = hyp * math.sin(angle_a)

    # adjust starting line so that entire grid shape is convex
    x = xstart + side_len + side_a
    y = ystart + side_b
    row = 1
    col = 1
    cat = 1
    while y + (2*side_b) < ylimit:
        while x + (2*side_len) < xlimit: 
            name = 'x%f_y%f' % (x,y)
            outstring = CreateHexagon((x, y), side_len, cat)
            vf.write(outstring)
            outstring = "UPDATE %s SET row_num = %d, col_num = %d, row_col = '%d_%d' WHERE cat = %d;\n" % \
                (table_name,row,col,row,col,cat)
            sf.write(outstring)
            cat = cat + 1
            x = x + (2*side_len) + (2*side_a)
            col = col + 1
        y = y + side_b
        row = row + 1
        if row % 2 <> 0:
            x = xstart + side_len + side_a
        else:
            x = xstart
        col = 1
        
#
# CreateHexagonGrid - creates hexagons based on six equalateral triangles
#
#        

def CreateHexagon(origin, side_len, cat):

    # Get the x and y from the tuple
    orgx = origin[0]
    orgy = origin[1]

    # basic trig
    angle_a = math.radians(30)
    hyp = side_len
    side_b = hyp * math.cos(angle_a)
    side_a = hyp * math.sin(angle_a)
    cx = orgx + (hyp / 2.0)
    cy = orgy + side_b
 
    # create coordinate string
    outstring = """B 2
%f %f
%f %f
B  2
%f %f
%f %f
B  2
%f %f
%f %f
B  2
%f %f
%f %f
B  2
%f %f
%f %f
B  2
%f %f
%f %f
C 1 1
%f %f
1 %d\n""" % (
    orgx, orgy,
    orgx + hyp, orgy,
    orgx + hyp, orgy,
    orgx + hyp + side_a, orgy + side_b,
    orgx + hyp + side_a, orgy + side_b,
    orgx + hyp, orgy + (2 * side_b),
    orgx + hyp, orgy + (2 * side_b),
    orgx, orgy + (2 * side_b),
    orgx, orgy + (2 * side_b),
    orgx - side_a, orgy + side_b,
    orgx - side_a, orgy + side_b,
    orgx, orgy, cx, cy, cat)
    return(outstring)

#
# WriteGrassHeader - writes GRASS header to temporary text file
#
#

def WriteGrassHeader(f,outfile,xstart,ystart,xmax,ymax):
    
    today = time.strftime("%Y.%m.%d %H:%M:%S",time.localtime())
    outtext = """ORGANIZATION: n/a
DIGIT DATE: %s
DIGIT NAME: v.mkhexgrid
MAP NAME: %s
MAP DATE: %s
MAP SCALE: 
OTHER INFO: Hexagon Grid
ZONE: 0
WEST EDGE: %s
EAST EDGE: %s
SOUTH EDGE: %s
NORTH EDGE: %s
MAP THRESH: 0.000000
VERTI:\n""" % (today,outfile,today,xstart,xmax,ystart,ymax)
    f.write(outtext)
    return()
    
#
#
# calc_side_length()
#
#
def calc_side_length(hexarea):   

    tarea = hexarea/6.0
    #
    # area of an equilateral triangle = length^2 * sqrt(3)/4 
    # sqrt(3)/4 * area = length^2
    # sqrt( sqrt(3)/4 * area) = length
    #
    retval = math.sqrt( tarea / (math.sqrt(3.0)/4.0) )
    return(retval)
    
def main():
    if options['method'] == 'area':
        try:
            side_len = calc_side_length(float(options['hexarea']))
        except:
            grass.message('An error occured in calculating side length for specified area', flag='e')
            return(-1)
    else:
        side_len = options['sidelength']
    errpipe = subprocess.PIPE
    outpipe = subprocess.PIPE
    grass.message('Creating GRASS GIS ASCII file with hexagons...')
    # assign name to temporary text file
    tempname= 'tempgrid%d' % os.getpid()
    tmp_dir = grass.tempdir()
    grass.debug('tmp_dir = %s' % tmp_dir)
    vectorfile = os.path.join(tmp_dir, tempname) + '.asc'
    sqlfile = os.path.join(tmp_dir, tempname) + '.sql'
    # set region
    try:
        r = grass.run_command('g.region', region='%s' % options['regionname'])
        if r <> 0:
            raise
    except:
        grass.message("An error occured when selecting the specified region", flag='e')
        return(-1)
    current_region = grass.region()
    xstart = current_region['w']
    ystart = current_region['s']
    xmax = current_region['e']
    ymax = current_region['n']
    #print "filename: %s\nx: %s, y: %s\nxmax: %s, ymax: %s\nside_length: %s" % (outfile, xstart, ystart, xmax, ymax, side_len)
    vf = open(vectorfile, "w")
    sf = open(sqlfile, "w")
    sf.write("BEGIN TRANSACTION;\n")
    WriteGrassHeader(vf,vectorfile,xstart,ystart,xmax,ymax)
    tname = options['map'].split('@')[0]
    schema = gdb.db_connection()['schema']
    if schema.strip() == '':
        table_name = tname
    else:
        table_name = schema + '.' + tname
    WriteHexGridVectors(vf, sf, table_name, float(side_len), float(xstart), float(ystart), float(xmax), float(ymax))
    vf.close()
    sf.write("COMMIT;\n")
    sf.close()
    # now import and clean up the vector
    grass.message('Importing GRASS GIS ASCII file...')
    try:
        r = grass.run_command('v.in.ascii', input=vectorfile, output=tempname, format='standard', separator=',')
        if r <> 0:
            raise
    except:
        grass.message("An error occured when importing ASCII file", flag='e')
        return(-1)
    grass.message('Cleaning and building topology...')
    try:
        r = grass.run_command('v.clean', input=tempname, output=tname, type='point,line,boundary,centroid,area', tool='rmdupl')
        if r <> 0:
            raise
    except:
        grass.message("An error occured when cleaning grid layer", flag='e')
        return(-1)
    grass.message('Importing and linking attributes...')
    grass.message('Creating table...')
    # import attributes
    grass.debug(vectorfile)
    try:
         # add attribute table
        r = grass.run_command('v.db.addtable', map=tname, table=table_name, layer=1, columns='cat integer, row_num integer, col_num integer, row_col varchar(255)' )
        if r <> 0:
            raise
    except:
        grass.message("An error occured when importing creating attribute table", flag='e')
        return(-1)
    grass.message('Updating attributes...')
    try:
        # link to proper table
        r = grass.run_command('db.execute', input=sqlfile)
        # drop temp vector
        if r <> 0:
            raise
    except:
        grass.message("An error occured connecting attribute table", flag='e')
        return(-1)
    grass.message('Removing temporary files')
    try:
        r = grass.run_command('g.remove', type='vect', name=tempname, quiet=True, flags='f')
        if r <> 0:
            raise
    except:
        grass.message("An error occured when removing temporary layer", flag='e')
        return(-1)
    os.remove(vectorfile)
    os.remove(sqlfile)
    try_rmdir(tmp_dir)
        
if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())

