#!/usr/bin/env python
#
############################################################################
#
# MODULE:	r.neighborhoodmatrix
# AUTHOR(S):	Moritz Lennert
#
# PURPOSE:	Calculates a neighborhood matrix for a raster map with regions
#               (e.g. the output of r.clump or i.segment)
# COPYRIGHT:	(C) 1997-2016 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#

#%Module
#% description: Calculates a neighborhood matrix for a raster map with regions
#% keyword: raster
#% keyword: neighboorhood
#% keyword: regions
#%end
#
#%option G_OPT_R_INPUT
#% description: Raster for which to calculate the neighboorhood matrix
#% required: yes
#%end
#
#%option G_OPT_F_OUTPUT
#% description: Name for output file (- for standard output)
#% required: yes
#% answer: -
#%end
#
#%option G_OPT_F_SEP
#%end
#
#%option
#% key: processes
#% type: integer
#% description: Number of processes to run in parallel (for multiple rasters)
#% required: no
#% answer: 1
#%end
#%flag
#% key: d
#% description: Also take into account diagonal neighbors
#%end
#%flag
#% key: l
#% description: Also output length of common border (in pixels)
#%end

import grass.script as gscript
import sys
import os
import atexit
import heapq
from functools import partial
from multiprocessing import Pool, Process, Queue

def cleanup():
    for mapname in mapnames:
        gscript.run_command('g.remove', flags='f', type='raster',
                          name=mapname, quiet=True)

    for filename in filenames:
        os.remove(filename)

    if outfile:
        os.remove(outfile)

    return 0

def worker(input_queue, rinput, separator, result_queue):
        for mapname, modifier in iter(input_queue.get, 'STOP'):
            expression = "%s = if(%s%s!=%s, %s%s, null())" % (mapname, rinput, modifier, rinput, rinput, modifier)
            gscript.run_command('r.mapcalc',
                                expression=expression,
                                quiet=True)
            tfdir = gscript.tempdir()
            tf = os.path.join(tfdir, mapname)
            rstats_results  = gscript.read_command('r.stats',
                             input_=[rinput, mapname],
                             flags='nc',
                             output=tf,
                             separator=separator,
                             quiet=True)
            result_queue.put(tf)

# Sort by both cat values
def keyfunc(s):
    return [int(x) for x in s.split(separator)[:2]]

def decorated_file(f, key):
    for line in f: 
        yield (key(line), line)

def main():
    global mapnames
    mapnames = []
    global filenames
    filenames = []
    global outfile
    outfile = None
    rinput = options['input']
    output = options['output']

    #Check that input map is CELL
    datatype = gscript.parse_command('r.info', flags='g', map=rinput)['datatype']
    if datatype != 'CELL':
        gscript.fatal(_("Input map has to be of CELL (integer) type"))

    mapinfo = gscript.raster_info(rinput)
    if mapinfo['max'] == mapinfo['min']:
        gscript.fatal(_("Need at least two different category values to determine neighbors"))

    global separator
    separator = gscript.separator(options['separator'])
    processes = int(options['processes'])

    pid = os.getpid()
    nbnames = ['nl', 'nr', 'nu', 'nd', 'nul', 'nur', 'nll', 'nlr'] 
    modifiers = ['[0,-1]', '[0,1]', '[1,0]', '[-1,0]', '[1,-1]', '[1,1]', '[-1,-1]', '[-1,1]']

    # If the diagonal flag is not set, only keep direct neighbors
    if not flags['d']:
        nbnames = nbnames[:4]
        modifiers = modifiers[:4]

    mapnames = ["nb_temp_%s_map_%d" % (nbname, pid) for nbname in nbnames]
    input_data = zip(mapnames, modifiers)
    input_queue = Queue()
    for input_datum in input_data:
        input_queue.put(input_datum)
    result_queue = Queue()

    # Launch processes for r.mapcalc and r.stats in as many processes as
    # requested
    processes_list = []
    for p in xrange(processes):
        proc = Process(target=worker, args=(input_queue, rinput, separator, result_queue))
        proc.start()
        processes_list.append(proc)
        input_queue.put('STOP')
    for p in processes_list:
        p.join()
    result_queue.put('STOP')


    # Now merge all r.stats outputs (which are already sorted)
    # into one file
    for tf in iter(result_queue.get, 'STOP'):
	filenames.append(tf)
    files = map(open, filenames)
    outfile = gscript.tempfile()

    # This code comes from https://stackoverflow.com/a/1001625
    with open(outfile, 'wb') as outf:
        for line in heapq.merge(*[decorated_file(f, keyfunc) for f in files]):
            outf.write(line[1])

    # Define final output
    if output == '-':
        of = sys.stdout
    else:
        of = open(output, 'w')

    # Read the merged output file and sum the results per neighborhood pair
    OldAcat = None
    OldBcat = None
    Sum = 0
    with open(outfile, 'r') as fin:
        for line in fin:
            Acat = line.split(separator)[0]
            Bcat = line.split(separator)[1]
            value = int(line.split(separator)[2])
            if Acat == OldAcat and Bcat == OldBcat:
                Sum += value
            else:
                if OldAcat and OldBcat:
                    if flags['l']:
                        woutput = separator.join([OldAcat, OldBcat, str(Sum)])
                    else:
                        woutput = separator.join([OldAcat, OldBcat])
                    of.write(woutput+"\n")	
                OldAcat = Acat
                OldBcat = Bcat
                Sum = value
    if OldAcat and OldBcat:
        if flags['l']:
            woutput = separator.join([OldAcat, OldBcat, str(Sum)])
        else:
            woutput = separator.join([OldAcat, OldBcat])
        of.write(woutput+"\n")	
    of.close()

if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
