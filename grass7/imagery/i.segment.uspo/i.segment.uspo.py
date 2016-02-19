#!/usr/bin/env python
#
############################################################################
#
# MODULE:	i.segment.variance
# AUTHOR(S):	Moritz Lennert
#
# PURPOSE:	Calculate variation of variance by variation of 
#		segmentation threshold
# COPYRIGHT:	(C) 1997-2016 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################
# References:
# TODO
#  
# 
#
#############################################################################

#%Module
#% description: Analyzes variation of variance with variation of segmentation threshold
#% keyword: imagery
#% keyword: variance
#% keyword: segmentation
#% keyword: threshold
#%end
#
#%option G_OPT_I_GROUP
#% description: Group to use for segmentation
#% required : yes
#%end
#
#%option G_OPT_R_MAPS
#% key: maps
#% description: Raster band(s) for  which to calculate variance (default: all group members)
#% required : no
#%end
#
#%option G_OPT_F_OUTPUT
#% description: Name for output file (- for standard output)
#%end
#
#%option G_OPT_R_OUTPUT
#% key: segment_map
#% description: Prefix for "best" output segmentation map per region
#% required : no
#%end
#
#%option G_OPT_M_REGION
#% key: regions
#% description: Regions in which to analyze the variance
#% required: yes
#% multiple: yes
#%end
#
#%option
#% key: thresholds
#% type: double
#% description: Thresholds to test
#% required: no
#% multiple: yes
#%end
#
#%option
#% key: threshold_start
#% type: double
#% description: Lowest threshold to test
#% required: no
#%end
#
#%option
#% key: threshold_stop
#% type: double
#% description: Threshold at which to stop (not included)
#% required: no
#%end
#
#%option
#% key: threshold_step
#% type: double
#% description: Step to use between thresholds
#% required: no
#%end
#
#%option
#% key: minsizes
#% type: integer
#% description: Minimum number of cells in a segment
#% multiple: yes
#% required: no
#%end
#
#%option
#% key: minsize_start
#% type: integer
#% description: Lowest minimum segment size to test
#% required: no
#%end
#
#%option
#% key: minsize_stop
#% type: integer
#% description: Value for minimum segment size at which to stop (not included)
#% required: no
#%end
#
#%option
#% key: minsize_step
#% type: integer
#% description: Step to use between thresholds
#% required: no
#%end
#
#%option
#% key: autocorrelation_indicator
#% type: string
#% description: Indicator for measuring inter-segment heterogeneity
#% required: no
#% options: morans,geary
#% answer: morans
#%end
#
#%option
#% key: optimization_function
#% type: string
#% description: Optimization function used to determine "best" parameters
#% required: no
#% options: sum,f
#% answer: sum
#%end
#
#%option
#% key: f_function_alpha
#% type: double
#% description: Alpha value used for F-measure optimization function
#% required: no
#% answer: 1
#%end
#
#%option
#% key: number_best
#% type: integer
#% description: Number of desired best parameter values and maps
#% required: no
#% answer: 1
#%end
#
#%option
#% key: memory
#% type: integer
#% description: Total memory to allocate (will be divided by processes)
#% required: yes
#% answer: 300
#%end
#
#%option
#% key: processes
#% type: integer
#% description: Number of processes to run in parallel
#% required: yes
#% answer: 1
#%end
#
#%flag
#% key: k
#% description: Keep all segmented maps
#%end
#
#%flag
#% key: n
#% description: Non-hierarchical segmentation
#%end
#
#%rules
#% required: thresholds,threshold_start
#% excludes: thresholds,threshold_start,threshold_stop,threshold_step
#% collective: threshold_start,threshold_stop,threshold_step
#% required: minsizes,minsize_start
#% excludes: minsizes,minsize_start,minsize_stop,minsize_step
#% collective: minsize_start,minsize_stop,minsize_step
#%end

import grass.script as gscript
import sys
import os
import atexit
from multiprocessing import Process, Queue, current_process

def cleanup():
    """ Delete temporary maps """

    if not keep:
        gscript.run_command('g.remove',
                            flags='f',
                            type='raster',
                            pat=temp_segment_map+"*",
                            quiet=True)
    gscript.run_command('g.remove',
                        flags='f',
                        type='raster',
                        name=temp_variance_map,
                        quiet=True)
    if gscript.find_file(temp_vector_map, element='vector')['name']:
        gscript.run_command('g.remove',
                            flags='f',
                            type='vector',
                            name=temp_vector_map,
                            quiet=True)

def drange(start, stop, step):
    """ xrange for floats """

    r = start
    while r < stop:
        yield r
        r += step

def hier_worker(region, thresholds, minsize_queue, done_queue):
    """ Launch parallel processes for hierarchical segmentation """

    try:
        for minsize in iter(minsize_queue.get, 'STOP'):
            hierarchical_seg(region, thresholds, minsize)
            done_queue.put("%s_%d ok" % (region, minsize))
    except:
        done_queue.put("%s: %s_%d failed" % (current_process().name, region,
                                             minsize))

    return True

def nonhier_worker(region, parameter_queue, done_queue):
    """ Launch parallel processes for non-hierarchical segmentation """

    try:
        for threshold, minsize in iter(parameter_queue.get, 'STOP'):
            non_hierarchical_seg(region, threshold, minsize)
            done_queue.put("%s_%f_%d ok" % (region, threshold, minsize))
    except:
        done_queue.put("%s: %s_%f_%d failed" % (current_process().name, region,
                                                threshold, minsize))
        
    return True


def hierarchical_seg(region, thresholds, minsize):
    """ Do hierarchical segmentation for a vector of thresholds and a specific minsize"""

    outputs_prefix = temp_segment_map + "_%s" % region
    outputs_prefix += "__%.2f"
    outputs_prefix += "__%d" % minsize
    gscript.run_command('i.segment.hierarchical',
                      group=group,
                      thresholds=thresholds,
                      minsizes=minsize,
                      output=temp_segment_map,
                      outputs_prefix=outputs_prefix,
                      memory=memory,
                      quiet=True)

def non_hierarchical_seg(region, threshold, minsize):
    """ Do non-hierarchical segmentation for a specific threshold and minsize"""

    temp_segment_map_thresh = temp_segment_map + "_%s" % region
    temp_segment_map_thresh += "__%.2f" % threshold
    temp_segment_map_thresh += "__%d" % minsize
    gscript.run_command('i.segment',
                        group=group,
                        threshold=threshold,
                        minsize=minsize,
                        output=temp_segment_map_thresh,
                        memory=memory,
                        quiet=True,
                        overwrite=True) 


def variable_worker(region, parameter_queue, result_queue):
    """ Launch parallel processes for calculating optimization criteria """

    for threshold, minsize in iter(parameter_queue.get, 'STOP'):
       temp_segment_map_thresh = temp_segment_map + "_%s" % region
       temp_segment_map_thresh += "__%.2f" % threshold
       temp_segment_map_thresh += "__%d" % minsize
       variance_per_raster = []
       autocor_per_raster = []
       neighbordict = get_nb_matrix(temp_segment_map_thresh)
       for raster in rasters:
           var = get_variance(temp_segment_map_thresh, raster)
           variance_per_raster.append(var)
           autocor = get_autocorrelation(temp_segment_map_thresh, raster,
   	                                 neighbordict, indicator)
           autocor_per_raster.append(autocor)

       mean_lv = sum(variance_per_raster) / len(variance_per_raster)
       mean_autocor = sum(autocor_per_raster) / len(autocor_per_raster)
       result_queue.put([temp_segment_map_thresh, mean_lv, mean_autocor,
			threshold, minsize])


def get_variance(mapname, raster):
    """ Calculate intra-segment variance of the values of the given raster"""

    temp_map = temp_variance_map + current_process().name.replace('-', '_')
    gscript.run_command('r.stats.zonal',
                        base=mapname,
                        cover=raster,
                        method='variance',
                        output=temp_map,
                        overwrite=True,
                        quiet=True)
    univar = gscript.parse_command('r.univar',
                                   map_=temp_map,
                                   flags='g',
                                   quiet=True)
    var = float(univar['mean'])
    gscript.run_command('g.remove',
                        type_='raster',
                        name=temp_map,
                        flags='f',
                        quiet=True)
    return var

def get_nb_matrix (mapname):
    """ Create a dictionary with neighbors per segment"""

    res = gscript.read_command('r.neighborhoodmatrix',
                               input_=mapname,
                               output='-',
                               sep='comma',
                               quiet=True)

    neighbordict = {}
    for line in res.splitlines():
        n1=line.split(',')[0]
        n2=line.split(',')[1]
        if n1 in neighbordict:
            neighbordict[n1].append(n2)
        else:
            neighbordict[n1] = [n2]

    return neighbordict


def get_autocorrelation (mapname, raster, neighbordict, indicator):
    """ Calculate either Moran's I or Geary's C for values of the given raster """

    raster_vars = gscript.parse_command('r.univar',
			  		map_=raster,
			  		flags='g',
			  		quiet=True)
    global_mean = float(raster_vars['mean'])

    univar_res = gscript.read_command('r.univar',
			 	      flags='t',
			 	      map_=raster,
			 	      zones=mapname,
			 	      out='-',
			 	      sep='comma',
                                      quiet=True)

    means = {}
    mean_diffs = {}
    firstline = True
    for line in univar_res.splitlines():
	l = line.split(',')
	if firstline:
	    i = l.index('mean')
	    firstline = False
	else:
	    means[l[0]] = float(l[i])
	    mean_diffs[l[0]] = float(l[i]) - global_mean
    
    sum_sq_mean_diffs = sum(x**2 for x in mean_diffs.values())

    total_nb_neighbors = 0
    for region in neighbordict:
	total_nb_neighbors += len(neighbordict[region])
    
    N = len(means)
    sum_products = 0
    sum_squared_differences = 0
    for region in neighbordict:
	region_value = means[region] - global_mean
	neighbors = neighbordict[region]
	nb_neighbors = len(neighbors)
	for neighbor in neighbors:
	    neighbor_value = means[neighbor] - global_mean
	    sum_products += region_value * neighbor_value
            sum_squared_differences = ( means[region] - means[neighbor] ) ** 2

    if indicator == 'morans':
        autocor = ( ( float(N) / total_nb_neighbors ) * (float(sum_products)  /  sum_sq_mean_diffs ) )
    elif indicator == 'geary':
        autocor = ( float(N - 1) /  ( 2 * total_nb_neighbors ) ) * ( float(sum_squared_differences)  / sum_sq_mean_diffs )

    return autocor

def normalize_criteria (crit_list, direction):
    """ Normalize the optimization criteria """

    maxval = max(crit_list)
    minval = min(crit_list)
    if direction == 'low':
        normlist = [float(maxval - x) / float(maxval - minval) for x in crit_list]
    else:
        normlist = [float(x - minval) / float(maxval - minval) for x in crit_list]
    return normlist

def create_optimization_list(variancelist, autocorlist, opt_function, alpha, direction):
    """ Create list of optimization function value for each parameter combination """

    normvariance = normalize_criteria(variancelist, 'low')
    normautocor = normalize_criteria(autocorlist, direction)
    
    if opt_function == 'sum':
        optlist = [normvariance[x] + normautocor[x] for x in range(len(normvariance))]
    if opt_function == 'f':
        optlist = [( 1 + alpha**2 ) * ( ( normvariance[x] * normautocor[x] ) / float( alpha**2 * normautocor[x] + normvariance[x] ) ) for x in range(len(normvariance))]
    return optlist


def find_optimal_value_indices(optlist, nb_best):
    """ Find the nb_best values in the list of optimization function values and return their indices """

    sorted_list = sorted(optlist, reverse=True)
    opt_indices = [] 
    for best in range(nb_best):
	 opt_indices.append(optlist.index(sorted_list[best]))

    return opt_indices

def main():
    global group
    group = options['group']
    output = options['output']
    global indicator
    indicator = options['autocorrelation_indicator']
    opt_function = options['optimization_function']
    alpha = float(options['f_function_alpha'])

    # which is "better", higher or lower ?
    directions = {'morans': 'low', 'geary': 'high'}

    if options['segment_map']:
        segmented_map = options['segment_map']
    else:
	segmented_map = None

    # If no list of rasters is given we take all members of the group
    global rasters
    if options['maps']:
        rasters = options['maps'].split(',')
    else:
        list_rasters = gscript.read_command('i.group',
                                            group=group,
                                            flags='gl',
                                            quiet=True)
        rasters = list_rasters.split('\n')[:-1]

    if options['thresholds']:
        thresholds = [float(x) for x in options['thresholds'].split(',')]
    else:
        step = float(options['threshold_step'])
        start = float(options['threshold_start'])
        stop = float(options['threshold_stop'])
        iter_thresh = drange(start,stop,step)
        # We want to keep a specific precision, so we go through string
        # representation and back to float
        thresholds = [float(y) for y in ["%.2f" % x for x in iter_thresh]]

    if options['minsizes']:
        minsizes = [int(x) for x in options['minsizes'].split(',')]
    else:
        step = int(options['minsize_step'])
        start = int(options['minsize_start'])
        stop = int(options['minsize_stop'])
        minsizes = range(start,stop,step)

    if options['regions']:
	regions = options['regions'].split(',')
    else:
	regions = False

    nb_best = int(options['number_best'])
    global memory
    memory = int(options['memory'])
    processes = int(options['processes'])
    memory /= processes


    global keep
    keep = False
    if flags['k']:
        keep = True

    global temp_segment_map, temp_variance_map, temp_vector_map
    temp_segment_map = "segment_uspo_temp_segment_map_%d" % os.getpid()
    temp_variance_map = "segment_uspo_temp_variance_map_%d" % os.getpid()
    temp_vector_map = "segment_uspo_temp_vector_map_%d" % os.getpid()

    # Don't change general mapset region settings when switching regions
    gscript.use_temp_region()

    regiondict = {}
    best_values = {}
    maps_to_keep = []
    for region in regions:

        gscript.message("Working on region %s\n" % region)

        gscript.run_command('g.region', 
                            region=region,
                            quiet=True)

	# Launch segmentation in parallel processes
    	processes_list = []
    	done_queue = Queue()
        if not flags['n']:
            minsize_queue = Queue()
            for minsize in minsizes:
                minsize_queue.put(minsize)
            for p in xrange(processes):
                proc = Process(target=hier_worker, args=(region, thresholds,
                               minsize_queue, done_queue))
                proc.start()
                processes_list.append(proc)
                minsize_queue.put('STOP')
            for p in processes_list:
                p.join()
            done_queue.put('STOP')
        else:
            parameter_queue = Queue()
            for threshold in thresholds:
                for minsize in minsizes:
                    parameter_queue.put([threshold, minsize])
            for p in xrange(processes):
                proc = Process(target=nonhier_worker, args=(region,
                               parameter_queue, done_queue))
                proc.start()
                processes_list.append(proc)
                parameter_queue.put('STOP')
            for p in processes_list:
                p.join()
            done_queue.put('STOP')


	# Launch calculation of optimization values in parallel processes
    	processes_list = []
    	parameter_queue = Queue()
	result_queue=Queue()
    	for threshold in thresholds:
	    for minsize in minsizes:
	    	parameter_queue.put([threshold, minsize])
	for p in xrange(processes):
	    proc = Process(target=variable_worker, args=(region, 
			       parameter_queue, result_queue))
	    proc.start()
	    processes_list.append(proc)
            parameter_queue.put('STOP')
	for p in processes_list:
	    p.join()
	result_queue.put('STOP')

	# Construct result lists
	maplist = []
        threshlist = []
	minsizelist = []
        variancelist = []
        autocorlist = []

	for segmap, lv, autocor, threshold, minsize in iter(result_queue.get, 'STOP'):
	    maplist.append(segmap)
	    variancelist.append(lv)
	    autocorlist.append(autocor)
	    threshlist.append(threshold)
	    minsizelist.append(minsize)
		
	# Calculate optimization function values and get indices of best values
        optlist = create_optimization_list(variancelist,
                                           autocorlist,
                                           opt_function,
                                           alpha,
                                           directions[indicator])
	regiondict[region] = zip(threshlist, minsizelist, variancelist, autocorlist, optlist)

	optimal_indices = find_optimal_value_indices(optlist, nb_best)
        best_values[region] = []
     	for optind in optimal_indices:
	    best_values[region].append([threshlist[optind], minsizelist[optind], optlist[optind]])
	    maps_to_keep.append(maplist[optind])

    # Create output

    # Output of results of all attempts
    header_string = "region,threshold,minsize,variance,spatial_autocorrelation,optimization criteria\n"

    if output == '-':
        sys.stdout.write(header_string)	
	for region, resultslist in regiondict.iteritems():
	    for result in resultslist:
                output_string = "%s," % region
		output_string += ",".join(map(str, result))
                output_string += "\n"
	    	sys.stdout.write(output_string)	
    else:
	of = open(output, 'w')
        of.write(header_string)
        for region, resultslist in regiondict.iteritems():
	    for result in resultslist:
                output_string = "%s," % region
                print region, ",".join(map(str, result))
		output_string += ",".join(map(str, result))
                output_string += "\n"
                of.write(output_string)
        of.close()

    # Output of best values found
    msg = "Best values:\n"
    msg += "Region\tThresh\tMinsize\tOptimization\n"
    for region, resultlist in best_values.iteritems():
	for result in resultlist:
	    msg += "%s\t" % region
            msg += "\t".join(map(str, result))
	    msg += "\n"
    gscript.message(msg)


    # Keep copies of segmentation results with best values
    if segmented_map:
        for bestmap in maps_to_keep:
	    outputmap = bestmap.replace(temp_segment_map, segmented_map)
            gscript.run_command('g.copy',
                                raster=[bestmap,outputmap],
                                quiet=True)

if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
