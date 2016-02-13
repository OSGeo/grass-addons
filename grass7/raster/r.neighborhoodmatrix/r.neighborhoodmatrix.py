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
#%flag
#% key: d
#% description: Also take into account diagonal neighbors
#%end

import grass.script as gscript
import sys
import os
import atexit

def cleanup():
    for nmap in n_mapnames.values():
        gscript.run_command('g.remove', flags='f', type='raster',
                          pat=nmap, quiet=True)
    gscript.run_command('g.remove', flags='f', type='raster',
                      pat=temp_map, quiet=True)

    if diag:
        for nmap in n_diag_mapnames.values():
            gscript.run_command('g.remove', flags='f', type='raster',
                              pat=nmap, quiet=True)

def main():
    rinput = options['input']
    output = options['output']
    separator = gscript.separator(options['separator'])

    neighbors = []

    global pid, n_mapnames, diag, temp_map
    diag = False
    pid = os.getpid()
    n_mapnames = {}
    n_mapnames['nl'] = "temp_nl_map_%d" % pid
    n_mapnames['nr'] = "temp_nr_map_%d" % pid
    n_mapnames['nu'] = "temp_nu_map_%d" % pid
    n_mapnames['nd'] = "temp_nd_map_%d" % pid
    temp_map = "temp_rneighborhoodmatrix_map_%d" % pid

    nbs = {'nl': '[0,-1]', 'nr': '[0,1]', 'nu': '[1,0]', 'nd': '[-1,0]'}
    nbs_diag = {'nul': '[1,-1]', 'nur': '[1,1]', 'nll': '[-1,-1]', 'nlr': '[-1,1]'}
    for n, modifier in nbs.items():
        expression = "%s = (%s%s)" % (temp_map, rinput, modifier)
        gscript.run_command('r.mapcalc',
                            expression=expression,
                            overwrite=True,
                            quiet=True)
        expression = "%s = if(%s!=%s, %s, null())" % (n_mapnames[n], temp_map,
                rinput, temp_map)
        gscript.run_command('r.mapcalc',
                            expression=expression,
                            quiet=True)
        rstats_results  = gscript.read_command('r.stats',
                             input_=[rinput, n_mapnames[n]],
                             flags='n1',
                             separator=separator,
                             quiet=True)
        results = rstats_results.splitlines()
	neighbors += results


    if flags['d']:
        diag = True
        global n_diag_mapnames
        n_diag_mapnames = {}
        n_diag_mapnames['nul'] = "temp_nul_map_%d" % pid
        n_diag_mapnames['nur'] = "temp_nur_map_%d" % pid
        n_diag_mapnames['nll'] = "temp_nll_map_%d" % pid
        n_diag_mapnames['nlr'] = "temp_nlr_map_%d" % pid

        for n, modifier in nbs_diag.items():
            expression = "%s = if(%s%s!=%s, %s%s, null())" % (n_diag_mapnames[n], rinput,
                    modifier, rinput, rinput, modifier)
            gscript.run_command('r.mapcalc',
                                expression=expression,
                                quiet=True)
	    rstats_results  = gscript.read_command('r.stats',
				 input_=[rinput, n_diag_mapnames[n]],
				 flags='n1',
				 separator=separator,
				 quiet=True)
	    results = rstats_results.splitlines()
	    neighbors += results

    unique_neighbors = list(set(neighbors))
    unique_neighbors_sorted = gscript.natural_sort(unique_neighbors)

    if output == '-':
        for line in unique_neighbors_sorted:
            sys.stdout.write(line+"\n")	
    else:
	of = open(output, 'w')
        for line in unique_neighbors_sorted:
            of.write(line+"\n")
        of.close()

if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
