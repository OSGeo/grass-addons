#!/usr/bin/env python

"""
MODULE:    v.fixed.segmentpoints

AUTHOR(S): Helmut Kudrnovsky <alectoria AT gmx at>

PURPOSE:   Creates segment points along a vector line with fixed distances
           by using the v.segment module

COPYRIGHT: (C) 2014 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

#%module
#% description: segment points along a vector line with fixed distances
#% keywords: vector
#%end

#%option G_OPT_V_INPUT
#% key: vector
#% required: yes
#%end

#%option G_OPT_V_CAT
#% key: cat
#% description: Category of a vector line
#% required: yes
#%end

#%option G_OPT_M_DIR
#% key: dir
#% description: Directory where the output will be found
#% required : yes
#%end

#%option
#% key: distance
#% type: integer
#% key_desc: integer
#% description: fixed distance between segment points
#% required : no
#% answer: 100
#%end

import sys
import os
import math
import grass.script as grass

if not os.environ.has_key("GISBASE"):
    grass.message( "You must be in GRASS GIS to run this program." )
    sys.exit(1)

def main():
    vlines = options['vector'].split('@')[0] 
    vcat = options['cat']
    directory = options['dir']
    sdistance = options['distance']
    fpoints = 'segmentpoints.txt'
    global tmp	 
	
    # Extract vector line
    grass.message( "Extract vector line for which segment points should be calculated ..." )
    grass.run_command('v.extract', input = vlines, 
                                     output = 'vlinesingle', 
                                     cats = vcat)
    grass.message( "Extraction done." )
    grass.message( "----" )

    # Calculate vector line length and populate it to the attribute table
    grass.message( "Calculate vector line length and populate it to the attribute table ..." )	
    grass.run_command("v.db.addcolumn", map = 'vlinesingle',
                                     layer = 1, 
                                     columns = "vlength double")		

    grass.run_command("v.to.db", map = 'vlinesingle',
                                     option = 'length',
                                     layer = 1, 
                                     columns = 'vlength',
                                     overwrite = True)

    grass.message( "Calculate vector line length done." )	
    grass.message( "----" )	

    # Read length
    tmp = grass.read_command('v.to.db', map = 'vlinesingle', 
                                     type = 'line', 
                                     layer = 1, 
                                     qlayer = 1, 
                                     option = 'length', 
                                     units = 'meters', 
                                     column = 'vlength',
                                     flags = 'p')                         
    vector_line_length = float(tmp.split('\n')[1].split('|')[1])    

    # Print vector line length
    grass.message( "Vector line length in meter:" )
    grass.message( vector_line_length )
    grass.message( "----" )
	
    # Calculation number of segment points (start and end point included)
    # number of segment points without end point
    
    number_segmentpoints_without_end = math.floor( vector_line_length / float(sdistance) )

    number_segmentpoints_with_end = int(number_segmentpoints_without_end + 2)	

    grass.message( "Number of segment points (start and end point included):" )
    grass.message( number_segmentpoints_with_end )
    grass.message( "----" )
	
    segmentpointsrange_without_end = range(1, number_segmentpoints_with_end, 1)
    max_distancerange = float(sdistance) * number_segmentpoints_with_end
    distancesrange_without_end = range(0, int(max_distancerange), int(sdistance))

    # Write segment point input file for g.segment to G_OPT_M_DIR
    grass.message( "Write segment point input file for g.segment" )
    segment_points_file = os.path.join( directory, fpoints )
    file = open(segment_points_file, 'a')
    for f, b in zip(segmentpointsrange_without_end, distancesrange_without_end):
                                     file.write("P %s %s %s\n" % (f, vcat, b))
    file.close()

    file = open(segment_points_file, 'a')
    file.write("P %s %s -0" % (number_segmentpoints_with_end, vcat))
    file.close()	

    # Give information where output file 									 
    grass.message( "Segment points file:" )
    grass.message( segment_points_file )	
    grass.message( "----" )

    # Run v.segment with the segment point input	

    grass.run_command("v.segment", input = 'vlinesingle',
                                     output = 'segmentpoints',
                                     file = segment_points_file)	

    grass.run_command("v.db.addtable", map = 'segmentpoints')
	
									 
#    TODO join point segment file to point vector								 
#    grass.run_command("db.in.ogr", dsn = segment_points_file,
#                                     output = 't_segment_points_file')									 
									 
    grass.message( "Segment points file created" )									 
    grass.message( "----" )

    # v.fixed.segmentpoints done!	
    grass.message( "v.fixed.segmentpoints done!" )	

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
