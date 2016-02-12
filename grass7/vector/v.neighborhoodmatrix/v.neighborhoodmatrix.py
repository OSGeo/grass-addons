#!/usr/bin/env python
############################################################################
#
# MODULE:       v.neighborhoodmatrix
# AUTHOR:       Moritz Lennert
# PURPOSE:      Exports a csv file with the neighborhood matrix of polygons
#
# COPYRIGHT:    (c) 2014 Moritz Lennert, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Exports the neighborhood matrix of polygons in a vector map
#% keyword: vector
#% keyword: neighborhood matrix
#%end
#%option G_OPT_V_INPUT
#%end
#%option
#% key: player
#% type: integer
#% description: Layer in map where polygons are to be found
#% answer: 1
#% required: no
#%end
#%option G_OPT_F_OUTPUT
#% description: Name for output file (if omitted or "-" output to stdout)
#% required: no
#%end
#%option G_OPT_F_SEP
#%end
#%flag
#% key: b
#% description: create bidirectional matrix (same neighborhood relation repeated twice)
#%end

import sys
import grass.script as grass

def main():
    # if no output filename, output to stdout
    input = options['input']
    player = int(options['player'])
    output = options['output']
    sep = grass.utils.separator(options['separator'])
    bidirectional = flags['b']
    tempmapname='neighborhoodmatrix_tempmap'
    #TODO: automatically determine the first available layer in file
    blayer = player+1

    grass.run_command('v.category', input=input, output=tempmapname,
            option='add', layer=blayer, type='boundary', quiet=True,
            overwrite=True)
    vtodb_results=grass.read_command('v.to.db', flags='p', map=tempmapname,
            type='boundary', option='sides', layer=blayer, qlayer=player, quiet=True)
    grass.run_command('g.remove', flags='f', type='vector', name=tempmapname, quiet=True)

    #put result into a list of integer pairs
    temp_neighbors=[]
    for line in vtodb_results.splitlines():
        if line.split('|')[1]<>'-1' and line.split('|')[2]<>'-1':
                temp_neighbors.append([int(line.split('|')[1]), int(line.split('|')[2])])

    #uniqify the list of integer pairs
    n = len(temp_neighbors)
    t=list(temp_neighbors)
    t.sort()
    assert n > 0
    last = t[0]
    lasti = i = 1
    while i < n:
        if t[i] != last:
                t[lasti] = last = t[i]
                lasti += 1
        i += 1
    neighbors=t[:lasti]

    #if user wants bidirectional matrix, add the inversed pairs to the original
    if bidirectional:
        neighbors_reversed=[]
        for pair in neighbors:
                neighbors_reversed.append([pair[1], pair[0]])
        neighbors += neighbors_reversed

    neighbors.sort()

    if output and output != '-':
        out=open(output, 'w')
        for pair in neighbors:
               	out.write(str(pair[0]) + sep + str(pair[1])+'\n')
        out.close()
    else:
        for pair in neighbors:
               	print(str(pair[0]) + sep + str(pair[1]))



    sys.exit()

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
