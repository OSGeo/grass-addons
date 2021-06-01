#!/usr/bin/env python
#
#############################################################################
#
# MODULE:      v.transects.py
# AUTHOR(S):   Eric Hardin
# PURPOSE:     Creates lines or quadrilateral areas perpendicular to a polyline
# COPYRIGHT:   (C) 2011
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
# 
# UPDATES:     John Lloyd November 2011
#
#############################################################################
#%Module
#% description: Creates transect lines or quadrilateral areas at regular intervals perpendicular to a polyline.
#%End
#%option
#% key: input
#% type: string
#% description: Name of input vector map
#% gisprompt: old,vector,vector
#% required : yes
#%end
#%option
#% key: output
#% type: string
#% description: Name of output vector map
#% gisprompt: new,vector,vector
#% required : yes
#%end
#%option
#% key: transect_spacing
#% type: double
#% description: Transect spacing along input polyline
#% required : yes
#%end
#%option
#% key: dleft
#% type: double
#% label: Distance transect extends to the left of input line
#% description: Default is the same as the transect spacing
#% required : no
#%end
#%option
#% key: dright
#% type: double
#% label: Distance transect extends to the right of input line
#% description: Default is the same as the transect spacing
#% required : no
#%end
#%option
#% key: type
#% type: string
#% description: Feature type
#% required : no
#% options: line,area,point
#% answer : line
#%end

from subprocess import Popen, PIPE, STDOUT
from numpy import array
from math import sqrt
import grass.script as grass
import tempfile
####################################
# Returns the name of a vector map not in the current mapset.
# mapname is of the form temp_xxxxxx where xxxxxx is a random number
def tempmap():
    import random
    rand_number = [ random.randint(0,9) for i in range(6) ]
    rand_number_str = ''.join( map(str,rand_number) )
    mapname = 'temp_' + rand_number_str
    maplist = grass.read_command('g.list',type='vect',mapset='.').split()
    while mapname in maplist:
        rand_number = [ random.randint(0,9) for i in range(6) ]
        rand_number_str = ''.join( map(str,rand_number) )
        mapname = 'temp_' + rand_number_str
        maplist = grass.read_command('g.list',type='vect',mapset='.').split()
    return mapname

####################################
# load vector lines into python list
# returns v
# len(v) = number of lines in vector map
# len(v[i]) = number of vertices in ith line 
# v[i][j] = [ xij, yij ] ,i.e., jth vertex in ith line
def loadVector( vector ):
    expVecCmmd = 'v.out.ascii format=standard input='+vector
# JL    p = Popen(expVecCmmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    p = Popen(expVecCmmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=False)
    vectorAscii = p.stdout.read().strip('\n').split('\n')
    l = 0
    while 'ORGANIZATION' not in vectorAscii[l]:
        l += 1
    while ':' in vectorAscii[l]:
        l += 1
    v = []
    while l < len(vectorAscii):
        line = vectorAscii[l].split()
        if line[0] in ['L','B','A']:
            skip = len(line)-2
            vertices = int(line[1])
            l += 1
            v.append([])
            for i in range(vertices):
                v[-1].append( map(float,vectorAscii[l].split()[:2]) )
                l += 1
            l += skip
        elif line[0] in ['P','C','F','K']:
            skip = len(line)-2
            vertices = int(line[1])
            l += 1
            for i in range(vertices):
                l += 1
            l += skip
        else:
            grass.fatal(_("Problem with line: <%s>") % vectorAscii[l])
    if len(v) < 1:
        grass.fatal(_("Zero lines found in vector map <%s>") % vector)
    return v

####################################
# get transects locations along input vector lines
def get_transects_locs( vector, transect_spacing ): 
    transect_locs = [] # holds locations where transects should intersect input vector lines
    for line in vector:    
        transect_locs.append([line[0]])
        # i starts at the beginning of the line.
        # j walks along the line until j and i are separated by a distance of transect_spacing.
        # then, a transect is placed at j, i is moved to j, and this is iterated until the end of the line is reached
        i = 0
        j = i+1
        while j < len(line):
            d = dist( line[i],line[j] )
            if d > transect_spacing:
                r = (transect_spacing - dist(line[i],line[j-1]) )/( dist(line[i],line[j]) - dist(line[i],line[j-1]) )
                transect_locs[-1].append(  (r*array( line[j] ) + (1-r)*array( line[j-1] )).tolist()  )
                i = j-1
                line[i] = transect_locs[-1][-1]
            else:
                j += 1
    return transect_locs

####################################
# from transects locations along input vector lines, get transect ends
def get_transect_ends( transect_locs, dleft, dright ):
    transect_ends = []
    for transect in transect_locs:
        if len(transect) < 2: # if a line in input vec was shorter than transect_spacing
            continue # then don't put a transect on it
        transect_ends.append([])
        transect = array( transect )
        v = NR( transect[0], transect[1] ) # vector pointing parallel to transect
        transect_ends[-1].append( [ transect[0]+dleft*v, transect[0]-dright*v ] )
        for i in range(1,len( transect )-1,1):
            v = NR( transect[i-1], transect[i+1] )
            transect_ends[-1].append( [ transect[i]+dleft*v, transect[i]-dright*v ] )
        v = NR( transect[-2], transect[-1] )
        transect_ends[-1].append( [ transect[-1]+dleft*v, transect[-1]-dright*v ] )
    return transect_ends

####################################
# calculate distance between two points
def dist( ip, fp ): 
    return sqrt( (ip[0]-fp[0])**2 + (ip[1]-fp[1])**2 )

####################################
# take a vector, normalize and rotate it 90 degrees
def NR( ip, fp ): 
    x = fp[0] - ip[0]
    y = fp[1] - ip[1]
    r = sqrt( x**2 + y**2 )
    return array([ -y/r, x/r ])

####################################
# write transects
def writeTransects( transects, output ):
    transects_str = ''
    for transect in transects:
        transects_str += '\n'.join( [ 'L 2\n'+' '.join(map(str,end_points[0]))+'\n'+' '.join(map(str,end_points[1]))+'\n' for end_points in transect ] )
    # JL Rewrote Temporary File Logic for Windows
    _, temp_path = tempfile.mkstemp()
    a = open(temp_path, 'w')
    a.write( transects_str )
    a.seek(0)
    a.close()
    grass.run_command('v.in.ascii', flags='n', input=temp_path, output=output, format='standard')


####################################
# writes areas 
def writeQuads( transects, output ):
    quad_str = ''
    cnt = 1
    for line in transects:
        for tran in range( len(line)-1 ):
            pt1 = ' '.join( map(str,line[tran][0]) )
            pt2 = ' '.join( map(str,line[tran][1]) )
            pt3 = ' '.join( map(str,line[tran+1][1]) )
            pt4 = ' '.join( map(str,line[tran+1][0]) )
            pt5 = pt1
            # centroid is the average of the four corners
            c = ' '.join( map(str,[ 0.25*(line[tran][0][0]+line[tran][1][0]+line[tran+1][0][0]+line[tran+1][1][0]), 0.25*(line[tran][0][1]+line[tran][1][1]+line[tran+1][0][1]+line[tran+1][1][1]) ]) )
            quad_str += 'B 5\n' + '\n'.join([pt1,pt2,pt3,pt4,pt5]) + '\n'
            quad_str += 'C 1 1\n' + c + '\n1 ' + str(cnt) + '\n'
            cnt += 1
    # JL Rewrote Temporary File Logic for Windows
    _, temp_path = tempfile.mkstemp()
    a = open(temp_path, 'w')
    a.write( quad_str )
    a.seek(0)
    a.close()
    grass.run_command('v.in.ascii', flags='n', input=a.name, output=output, format='standard')

####################################
# writes areas 
def writePoints( transect_locs, output ):
    pt_str = ''
    for pts in transect_locs:
        pt_str += '\n'.join( [ ','.join(map(str,pt)) for pt in pts ] ) + '\n'
    _, temp_path = tempfile.mkstemp()
    a = open(temp_path, 'w')
    a.write( pt_str )
    a.seek(0)
    a.close()
    grass.run_command('v.in.ascii', input=a.name, output=output, format='point', fs=',', x=1, y=2)

####################################
# Main method
def main():
    vector = options['input']
    output = options['output']
    # JL Handling Invalid transect_spacing parameter
    try:
        transect_spacing = float(options['transect_spacing'])
    except:
        grass.fatal(_("Invalid transect_spacing value."))
    if transect_spacing == 0.0:
        grass.fatal(_("Zero invalid transect_spacing value."))
    dleft = options['dleft']
    dright = options['dright']
    shape = options['type']
    print dleft, transect_spacing
    if not dleft: 
        dleft = transect_spacing
    else:
        # JL Handling Invalid dleft parameter
        try:
            dleft = float(dleft)
        except:
            grass.fatal(_("Invalid dleft value."))
    if not dright: 
        dright = transect_spacing
    else:
        # JL Handling Invalid dright parameter
        try:
            dright = float(dright)
        except:
            grass.fatal(_("Invalid dright value."))
    # check if input file does not exists
    if not grass.find_file(vector, element='vector')['file']: 
        grass.fatal(_("<%s> does not exist.") % vector)
    # check if output file exists
    if grass.find_file(output, element='vector')['mapset'] == grass.gisenv()['MAPSET']: 
        if not grass.overwrite():
            grass.fatal(_("output map <%s> exists") % output)

    #JL Is the vector a line and does if have at least one feature?
    info = grass.parse_command('v.info', flags = 't', map = vector)
    if info['lines'] == '0':
        grass.fatal(_("vector <%s> does not contain lines") % vector)

    #################################
    v = loadVector( vector )
    transect_locs = get_transects_locs( v, transect_spacing )
    temp_map = tempmap()
    if shape == 'line' or not shape: 
        transect_ends = get_transect_ends( transect_locs, dleft, dright )
        writeTransects( transect_ends, temp_map )
    elif shape == 'area':
        transect_ends = get_transect_ends( transect_locs, dleft, dright )
        writeQuads( transect_ends, temp_map )
    else:
        writePoints( transect_locs, temp_map )

    grass.run_command( 'v.category', input=temp_map, output=output, type=shape )
    grass.run_command( 'g.remove', vect=temp_map )

if __name__ == "__main__":
    options, flags = grass.parser()
    main()


