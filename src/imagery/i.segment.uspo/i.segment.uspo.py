#!/usr/bin/env python
#
############################################################################
#
# MODULE:	i.segment.uspo
# AUTHOR(S):	Moritz Lennert
#
# PURPOSE:	Finds optimimal segmentation parameters in an unsupervised
#               process
# COPYRIGHT:	(C) 1997-2016 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
# References:
# G. M. Espindola , G. Camara , I. A. Reis , L. S. Bins , A. M. Monteiroi
# (2006),
# Parameter selection for region-growing image segmentation algorithms using
# spatial autocorrelation, International Journal of Remote Sensing, Vol. 27, Iss.
# 14, pp. 3035-3040, http://dx.doi.org/10.1080%2f01431160600617194
#
# B. A.  Johnson, M. Bragais, I. Endo, D. B. Magcale-Macandog, P. B. M. Macandog
# (2015),
# Image Segmentation Parameter Optimization Considering Within- and
# Between-Segment Heterogeneity at Multiple Scale Levels: Test Case for Mapping
# Residential Areas Using Landsat Imagery, ISPRS International Journal of
# Geo-Information, 4(4), pp. 2292-2305, http://dx.doi.org/10.3390/ijgi4042292
#############################################################################

# %Module
# % description: Unsupervised segmentation parameter optimization
# % keyword: imagery
# % keyword: variance
# % keyword: segmentation
# % keyword: threshold
# % keyword: parallel
# %end
#
# %option G_OPT_I_GROUP
# % description: Group to use for segmentation
# % required : yes
# %end
#
# %option G_OPT_R_MAPS
# % key: maps
# % description: Raster band(s) for  which to calculate variance (default: all group members)
# % required : no
# %end
#
# %option G_OPT_R_MAP
# % key: seeds
# % description: Seeds for segmentation
# % required : no
# %end
#
# %option G_OPT_F_OUTPUT
# % description: Name for output file (- for standard output)
# % required : no
# %end
#
# %option G_OPT_R_OUTPUT
# % key: segment_map
# % description: Prefix for "best" output segmentation map per region
# % required : no
# %end
#
# %option G_OPT_M_REGION
# % key: regions
# % description: Regions in which to analyze the variance
# % required: yes
# % multiple: yes
# %end
#
# %option
# % key: segmentation_method
# % type: string
# % description: Segmentation method to use
# % required: yes
# % options: region_growing,mean_shift
# % answer: region_growing
# %end
#
# %option
# % key: thresholds
# % type: double
# % description: Thresholds to test
# % required: no
# % multiple: yes
# % guisection: General
# %end
#
# %option
# % key: threshold_start
# % type: double
# % description: Lowest threshold to test
# % required: no
# % guisection: General
# %end
#
# %option
# % key: threshold_stop
# % type: double
# % description: Threshold at which to stop (not included)
# % required: no
# % guisection: General
# %end
#
# %option
# % key: threshold_step
# % type: double
# % description: Step to use between thresholds
# % required: no
# % guisection: General
# %end
#
# %option
# % key: minsizes
# % type: integer
# % description: Minimum number of cells in a segment to test
# % multiple: yes
# % required: no
# % guisection: General
# %end
#
# %option
# % key: minsize_start
# % type: integer
# % description: Lowest minimum segment size to test
# % required: no
# % guisection: General
# %end
#
# %option
# % key: minsize_stop
# % type: integer
# % description: Value for minimum segment size at which to stop (not included)
# % required: no
# % guisection: General
# %end
#
# %option
# % key: minsize_step
# % type: integer
# % description: Step to use between minimum segment sizes
# % required: no
# % guisection: General
# %end
#
# %option
# % key: radiuses
# % type: double
# % description: Radiuses to test
# % required: no
# % multiple: yes
# % guisection: Mean Shift
# %end
#
# %option
# % key: radius_start
# % type: double
# % description: Lowest radius to test
# % required: no
# % guisection: Mean Shift
# %end
#
# %option
# % key: radius_stop
# % type: double
# % description: Radius at which to stop (not included)
# % required: no
# % guisection: Mean Shift
# %end
#
# %option
# % key: radius_step
# % type: double
# % description: Step to use between radiuses
# % required: no
# % guisection: Mean Shift
# %end
#
# %option
# % key: hrs
# % type: double
# % description: Spectral bandwidths to test
# % required: no
# % multiple: yes
# % guisection: Mean Shift
# %end
#
# %option
# % key: hr_start
# % type: double
# % description: Lowest spectral bandwith to test
# % required: no
# % guisection: Mean Shift
# %end
#
# %option
# % key: hr_stop
# % type: double
# % description: Spectral bandwith at which to stop (not included)
# % required: no
# % guisection: Mean Shift
# %end
#
# %option
# % key: hr_step
# % type: double
# % description: Step to use between spectral bandwidths
# % required: no
# % guisection: Mean Shift
# %end
#
# %option
# % key: autocorrelation_indicator
# % type: string
# % description: Indicator for measuring inter-segment heterogeneity
# % required: no
# % options: morans,geary
# % answer: morans
# % guisection: Evaluation
# %end
#
# %option
# % key: optimization_function
# % type: string
# % description: Optimization function used to determine "best" parameters
# % required: no
# % options: sum,f
# % answer: sum
# % guisection: Evaluation
# %end
#
# %option
# % key: f_function_alpha
# % type: double
# % description: Alpha value used for F-measure optimization function
# % required: no
# % answer: 1
# % guisection: Evaluation
# %end
#
# %option
# % key: number_best
# % type: integer
# % description: Number of desired best parameter values and maps
# % required: no
# % answer: 1
# %end
#
# %option
# % key: memory
# % type: integer
# % description: Total memory (in MB) to allocate (will be divided by processes)
# % required: no
# % answer: 300
# %end
#
# %option
# % key: processes
# % type: integer
# % description: Number of processes to run in parallel
# % required: no
# % answer: 1
# %end
#
# %flag
# % key: k
# % description: Keep all segmented maps
# %end
#
# %flag
# % key: h
# % description: Use hierarchical segmentation
# %end
#
# %flag
# % key: a
# % description: Use adaptive spectral bandwidth (with mean shift)
# % guisection: Mean Shift
# %end
#
# %rules
# % required: thresholds,threshold_start
# % excludes: thresholds,threshold_start,threshold_stop,threshold_step
# % collective: threshold_start,threshold_stop,threshold_step
# % required: minsizes,minsize_start
# % excludes: minsizes,minsize_start,minsize_stop,minsize_step
# % collective: minsize_start,minsize_stop,minsize_step
# % excludes: radiuses,radius_start,radius_stop,radius_step
# % excludes: hrs,hr_start,hr_stop,hr_step
# % collective: radius_start,radius_stop,radius_step
# % collective: hr_start,hr_stop,hr_step
# %end

import grass.script as gscript
import sys
import os
import atexit
from multiprocessing import Process, Queue, current_process

# check requirements

# for python 3 compatibility
try:
    xrange
except NameError:
    xrange = range


def iteritems(dict):
    try:
        dictitems = dict.iteritems()
    except:
        dictitems = dict.items()
    return dictitems


def check_progs():
    found_missing = False
    for prog in ["r.neighborhoodmatrix"]:
        if not gscript.find_program(prog, "--help"):

            found_missing = True
            gscript.warning(
                _("'%s' required. Please install '%s' first using 'g.extension %s'")
                % (prog, prog, prog)
            )
    if found_missing:
        gscript.fatal(_("An ERROR occurred running i.segment.uspo"))


def cleanup():
    """Delete temporary maps"""

    if not keep:
        for mapname in maplist:
            gscript.run_command(
                "g.remove", flags="f", type="raster", pat=mapname, quiet=True
            )


def drange(start, stop, step):
    """xrange for floats"""

    r = start
    while r < stop:
        yield r
        r += step


def rg_hier_worker(parms, thresholds, minsize_queue, result_queue):
    """Launch parallel processes for hierarchical segmentation"""

    try:
        for minsize in iter(minsize_queue.get, "STOP"):
            map_list = rg_hierarchical_seg(parms, thresholds, minsize)
            for mapname, threshold, minsize in map_list:
                mapinfo = gscript.raster_info(mapname)
                if mapinfo["max"] > mapinfo["min"]:
                    variance_per_raster = []
                    autocor_per_raster = []
                    neighbordict = get_nb_matrix(mapname)
                    for raster in parms["rasters"]:
                        # there seems to be some trouble in ms windows with qualified
                        # map names
                        raster = raster.split("@")[0]
                        var = get_variance(mapname, raster)
                        variance_per_raster.append(var)
                        autocor = get_autocorrelation(
                            mapname, raster, neighbordict, parms["indicator"]
                        )
                        autocor_per_raster.append(autocor)

                    mean_lv = sum(variance_per_raster) / len(variance_per_raster)
                    mean_autocor = sum(autocor_per_raster) / len(autocor_per_raster)
                    result_queue.put(
                        [mapname, mean_lv, mean_autocor, threshold, minsize]
                    )
                else:
                    # If resulting map contains only one segment, then give high
                    # value of variance and 0 for spatial autocorrelation in order
                    # to give this map a low priority
                    result_queue.put([mapname, 999999, 0, threshold, minsize])

    except:
        exc_info = sys.exc_info()
        result_queue.put(
            [
                "%s: %s_%d failed with message:\n\n%s"
                % (current_process().name, parms["region"], minsize, exc_info)
            ]
        )

    return True


def rg_nonhier_worker(parms, parameter_queue, result_queue):
    """Launch parallel processes for non-hierarchical segmentation"""

    try:
        for threshold, minsize in iter(parameter_queue.get, "STOP"):
            mapname = rg_non_hierarchical_seg(parms, threshold, minsize)
            mapinfo = gscript.raster_info(mapname)
            if mapinfo["max"] > mapinfo["min"]:
                variance_per_raster = []
                autocor_per_raster = []
                neighbordict = get_nb_matrix(mapname)
                for raster in parms["rasters"]:
                    # there seems to be some trouble in ms windows with qualified
                    # map names
                    raster = raster.split("@")[0]
                    var = get_variance(mapname, raster)
                    variance_per_raster.append(var)
                    autocor = get_autocorrelation(
                        mapname, raster, neighbordict, parms["indicator"]
                    )
                    autocor_per_raster.append(autocor)

                mean_lv = sum(variance_per_raster) / len(variance_per_raster)
                mean_autocor = sum(autocor_per_raster) / len(autocor_per_raster)
                result_queue.put([mapname, mean_lv, mean_autocor, threshold, minsize])
            else:
                # If resulting map contains only one segment, then give high
                # value of variance and 0 for spatial autocorrelation in order
                # to give this map a low priority
                result_queue.put([mapname, 999999, 0, threshold, minsize])

    except:
        exc_info = sys.exc_info()
        result_queue.put(
            [
                "%s: %s_%f_%d failed with message:\n\n %s"
                % (
                    current_process().name,
                    parms["region"],
                    threshold,
                    minsize,
                    exc_info,
                )
            ]
        )

    return True


def rg_hierarchical_seg(parms, thresholds, minsize):
    """Do hierarchical segmentation for a vector of thresholds and a specific minsize"""

    outputs_prefix = parms["temp_segment_map"] + "__%s" % parms["region"]
    outputs_prefix += "__%.4f"
    outputs_prefix += "__%d" % minsize
    previous = None
    map_list = []
    for threshold in thresholds:
        temp_segment_map_thresh = outputs_prefix % threshold
        map_list.append([temp_segment_map_thresh, threshold, minsize])
        if previous is None:
            gscript.run_command(
                "i.segment",
                group=parms["group"],
                threshold=threshold,
                minsize=minsize,
                output=temp_segment_map_thresh,
                memory=parms["memory"],
                quiet=True,
                overwrite=True,
            )
            previous = temp_segment_map_thresh
        else:
            gscript.run_command(
                "i.segment",
                group=parms["group"],
                threshold=threshold,
                minsize=minsize,
                output=temp_segment_map_thresh,
                seeds=previous,
                memory=parms["memory"],
                quiet=True,
                overwrite=True,
            )
            previous = temp_segment_map_thresh

    return map_list


def rg_non_hierarchical_seg(parms, threshold, minsize):
    """Do non-hierarchical segmentation for a specific threshold and minsize"""

    temp_segment_map_thresh = parms["temp_segment_map"] + "__%s" % parms["region"]
    temp_segment_map_thresh += "__%.4f" % threshold
    temp_segment_map_thresh += "__%d" % minsize
    if parms["seeds"]:
        gscript.run_command(
            "i.segment",
            group=parms["group"],
            threshold=threshold,
            minsize=minsize,
            seeds=parms["seeds"],
            output=temp_segment_map_thresh,
            memory=parms["memory"],
            quiet=True,
            overwrite=True,
        )
    else:
        gscript.run_command(
            "i.segment",
            group=parms["group"],
            threshold=threshold,
            minsize=minsize,
            output=temp_segment_map_thresh,
            memory=parms["memory"],
            quiet=True,
            overwrite=True,
        )

    return temp_segment_map_thresh


def ms_worker(parms, parameter_queue, result_queue):
    """Launch parallel processes for non-hierarchical segmentation"""

    try:
        for threshold, hr, radius, minsize in iter(parameter_queue.get, "STOP"):
            mapname = ms_seg(parms, threshold, hr, radius, minsize)
            variance_per_raster = []
            autocor_per_raster = []
            neighbordict = get_nb_matrix(mapname)
            for raster in parms["rasters"]:
                var = get_variance(mapname, raster)
                variance_per_raster.append(var)
                autocor = get_autocorrelation(
                    mapname, raster, neighbordict, parms["indicator"]
                )
                autocor_per_raster.append(autocor)

            if len(variance_per_raster) > 0:
                mean_lv = sum(variance_per_raster) / len(variance_per_raster)
            else:
                mean_lv = 999999
            if len(autocor_per_raster) > 0:
                mean_autocor = sum(autocor_per_raster) / len(autocor_per_raster)
            else:
                mean_autocor = 0
            result_queue.put(
                [mapname, mean_lv, mean_autocor, threshold, hr, radius, minsize]
            )

    except:
        result_queue.put(
            [
                "%s: %s_%f_%f_%f_%d failed"
                % (
                    current_process().name,
                    parms["region"],
                    threshold,
                    hr,
                    radius,
                    minsize,
                )
            ]
        )

    return True


def ms_seg(parms, threshold, hr, radius, minsize):
    """Do non-hierarchical segmentation for a specific threshold and minsize"""

    temp_segment_map_thresh = parms["temp_segment_map"] + "__%s" % parms["region"]
    temp_segment_map_thresh += "__%.2f" % threshold
    temp_segment_map_thresh += "__%.2f" % hr
    temp_segment_map_thresh += "__%.2f" % radius
    temp_segment_map_thresh += "__%d" % minsize
    if parms["adaptive"]:
        gscript.run_command(
            "i.segment",
            group=parms["group"],
            threshold=threshold,
            hr=hr,
            radius=radius,
            minsize=minsize,
            method="mean_shift",
            output=temp_segment_map_thresh,
            memory=parms["memory"],
            flags="a",
            quiet=True,
            overwrite=True,
        )
    else:
        gscript.run_command(
            "i.segment",
            group=parms["group"],
            threshold=threshold,
            hr=hr,
            radius=radius,
            minsize=minsize,
            method="mean_shift",
            output=temp_segment_map_thresh,
            memory=parms["memory"],
            quiet=True,
            overwrite=True,
        )

    return temp_segment_map_thresh


def get_variance(mapname, raster):
    """Calculate intra-segment variance of the values of the given raster"""

    # current_process name contains '-' which can cause problems so we replace
    # with '_'
    temp_map = "isegmentuspo_temp_variance_map_%d_%s" % (
        os.getpid(),
        current_process().name.replace("-", "_"),
    )
    gscript.run_command(
        "r.stats.zonal",
        base=mapname,
        cover=raster,
        method="variance",
        output=temp_map,
        overwrite=True,
        quiet=True,
    )
    univar = gscript.parse_command("r.univar", map_=temp_map, flags="g", quiet=True)
    var = float(univar["mean"])
    gscript.run_command(
        "g.remove", type_="raster", name=temp_map, flags="f", quiet=True
    )
    return var


def get_nb_matrix(mapname):
    """Create a dictionary with neighbors per segment"""

    res = gscript.read_command(
        "r.neighborhoodmatrix", input_=mapname, output="-", sep="comma", quiet=True
    )

    neighbordict = {}
    for line in res.splitlines():
        n1 = line.split(",")[0]
        n2 = line.split(",")[1]
        if n1 in neighbordict:
            neighbordict[n1].append(n2)
        else:
            neighbordict[n1] = [n2]

    return neighbordict


def get_autocorrelation(mapname, raster, neighbordict, indicator):
    """Calculate either Moran's I or Geary's C for values of the given raster"""

    raster_vars = gscript.parse_command("r.univar", map_=raster, flags="g", quiet=True)
    global_mean = float(raster_vars["mean"])

    univar_res = gscript.read_command(
        "r.univar",
        flags="t",
        map_=raster,
        zones=mapname,
        out="-",
        sep="comma",
        quiet=True,
    )

    means = {}
    mean_diffs = {}
    firstline = True
    for line in univar_res.splitlines():
        l = line.split(",")
        if firstline:
            i = l.index("mean")
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
            sum_squared_differences = (means[region] - means[neighbor]) ** 2

    if indicator == "morans":
        autocor = (float(N) / total_nb_neighbors) * (
            float(sum_products) / sum_sq_mean_diffs
        )
    elif indicator == "geary":
        autocor = (float(N - 1) / (2 * total_nb_neighbors)) * (
            float(sum_squared_differences) / sum_sq_mean_diffs
        )

    return autocor


def normalize_criteria(crit_list, direction):
    """Normalize the optimization criteria"""

    maxval = max(crit_list)
    minval = min(crit_list)

    # If maxval = minval then results are not useful so set
    # all value to 0
    if float(maxval) - float(minval) == 0:
        return [0] * len(crit_list)

    if direction == "low":
        normlist = [float(maxval - x) / float(maxval - minval) for x in crit_list]
    else:
        normlist = [float(x - minval) / float(maxval - minval) for x in crit_list]
    return normlist


def create_optimization_list(variancelist, autocorlist, opt_function, alpha, direction):
    """Create list of optimization function value for each parameter combination"""

    normvariance = normalize_criteria(variancelist, "low")
    normautocor = normalize_criteria(autocorlist, direction)

    if opt_function == "sum":
        optlist = [normvariance[x] + normautocor[x] for x in range(len(normvariance))]
    if opt_function == "f":
        optlist = [
            (
                (1 + alpha**2)
                * (
                    (normvariance[x] * normautocor[x])
                    / float(alpha**2 * normautocor[x] + normvariance[x])
                )
                if (normautocor[x] + normvariance[x]) > 0
                else 0
            )
            for x in range(len(normvariance))
        ]
    return optlist


def find_optimal_value_indices(optlist, nb_best):
    """Find the nb_best values in the list of optimization function values and return their indices"""

    sorted_list = sorted(optlist, reverse=True)
    if len(sorted_list) < nb_best:
        nb_best = len(sorted_list)
    opt_indices = []
    for best in range(nb_best):
        opt_indices.append(optlist.index(sorted_list[best]))

    return opt_indices


def main():
    global maplist
    global keep
    maplist = []
    keep = False
    if flags["k"]:
        keep = True
    hierarchical_segmentation = False
    if flags["h"]:
        hierarchical_segmentation = True
        message = "INFO: Using hierarchical segmentation.\n"
        message += "INFO: Note that this leads to less optimal parallization."
        gscript.info(message)

    check_progs()

    parms = {}
    group = options["group"]
    parms["group"] = group
    method = options["segmentation_method"]
    rg = False
    if method == "region_growing":
        rg = True
    parms["seeds"] = False
    if options["seeds"]:
        parms["seeds"] = options["seeds"]
    output = False
    if options["output"]:
        output = options["output"]
    indicator = options["autocorrelation_indicator"]
    parms["indicator"] = indicator
    opt_function = options["optimization_function"]
    alpha = float(options["f_function_alpha"])
    parms["adaptive"] = False
    if flags["a"]:
        parms["adaptive"] = True

    # which is "better", higher or lower ?
    directions = {"morans": "low", "geary": "high"}

    if options["segment_map"]:
        segmented_map = options["segment_map"]
    else:
        segmented_map = None

    # If no list of rasters is given we take all members of the group
    if options["maps"]:
        rasters = options["maps"].split(",")
    else:
        list_rasters = gscript.read_command(
            "i.group", group=group, flags="gl", quiet=True
        )
        rasters = list_rasters.split("\n")[:-1]
    parms["rasters"] = rasters

    if options["thresholds"]:
        thresholds = [float(x) for x in options["thresholds"].split(",")]
    else:
        step = float(options["threshold_step"])
        start = float(options["threshold_start"])
        stop = float(options["threshold_stop"])
        iter_thresh = drange(start, stop, step)
        # We want to keep a specific precision, so we go through string
        # representation and back to float
        thresholds = [float(y) for y in ["%.4f" % x for x in iter_thresh]]

    if options["minsizes"]:
        minsizes = [int(x) for x in options["minsizes"].split(",")]
    else:
        step = int(options["minsize_step"])
        start = int(options["minsize_start"])
        stop = int(options["minsize_stop"])
        minsizes = range(start, stop, step)

    if options["hrs"]:
        hrs = [float(x) for x in options["hrs"].split(",")]
    if options["hr_step"]:
        step = float(options["hr_step"])
        start = float(options["hr_start"])
        stop = float(options["hr_stop"])
        iter_hrs = drange(start, stop, step)
        # We want to keep a specific precision, so we go through string
        # representation and back to float
        hrs = [float(y) for y in ["%.2f" % x for x in iter_hrs]]

    if options["radiuses"]:
        radiuses = [float(x) for x in options["radiuses"].split(",")]
    if options["radius_step"]:
        step = float(options["radius_step"])
        start = float(options["radius_start"])
        stop = float(options["radius_stop"])
        iter_radiuses = drange(start, stop, step)
        # We want to keep a specific precision, so we go through string
        # representation and back to float
        radiuses = [float(y) for y in ["%.2f" % x for x in iter_radiuses]]

    if options["regions"]:
        regions = options["regions"].split(",")
    else:
        regions = False

    nb_best = int(options["number_best"])
    memory = int(options["memory"])
    processes = int(options["processes"])
    parms["memory"] = memory / processes

    temp_segment_map = "temp_segment_uspo_%d" % os.getpid()
    parms["temp_segment_map"] = temp_segment_map

    # Don't change general mapset region settings when switching regions
    gscript.use_temp_region()

    regiondict = {}
    best_values = {}
    maps_to_keep = []
    for region in regions:

        gscript.message("Working on region %s\n" % region)
        parms["region"] = region.replace("@", "_at_")

        gscript.run_command("g.region", region=region, quiet=True)

        # Launch segmentation and optimization calculation in parallel processes
        processes_list = []
        result_queue = Queue()
        if rg:
            if hierarchical_segmentation:
                minsize_queue = Queue()
                for minsize in minsizes:
                    minsize_queue.put(minsize)
                for p in xrange(processes):
                    proc = Process(
                        target=rg_hier_worker,
                        args=(parms, thresholds, minsize_queue, result_queue),
                    )
                    proc.start()
                    processes_list.append(proc)
                    minsize_queue.put("STOP")
                for p in processes_list:
                    p.join()
                result_queue.put("STOP")
            else:
                parameter_queue = Queue()
                for minsize in minsizes:
                    for threshold in thresholds:
                        parameter_queue.put([threshold, minsize])
                for p in xrange(processes):
                    proc = Process(
                        target=rg_nonhier_worker,
                        args=(parms, parameter_queue, result_queue),
                    )
                    proc.start()
                    processes_list.append(proc)
                    parameter_queue.put("STOP")
                for p in processes_list:
                    p.join()
                result_queue.put("STOP")

        else:
            parameter_queue = Queue()
            for minsize in minsizes:
                for threshold in thresholds:
                    for hr in hrs:
                        for radius in radiuses:
                            parameter_queue.put([threshold, hr, radius, minsize])
            for p in xrange(processes):
                proc = Process(
                    target=ms_worker, args=(parms, parameter_queue, result_queue)
                )
                proc.start()
                processes_list.append(proc)
                parameter_queue.put("STOP")
            for p in processes_list:
                p.join()
            result_queue.put("STOP")

        # Construct result lists
        regional_maplist = []
        threshlist = []
        minsizelist = []
        variancelist = []
        autocorlist = []

        if rg:
            for result in iter(result_queue.get, "STOP"):
                if len(result) == 5:
                    mapname, lv, autocor, threshold, minsize = result
                    regional_maplist.append(mapname)
                    variancelist.append(lv)
                    autocorlist.append(autocor)
                    threshlist.append(threshold)
                    minsizelist.append(minsize)
                else:
                    gscript.message("Error in worker function: %s" % result)
        else:
            hrlist = []
            radiuslist = []
            for result in iter(result_queue.get, "STOP"):
                if len(result) == 7:
                    mapname, lv, autocor, threshold, hr, radius, minsize = result
                    regional_maplist.append(mapname)
                    variancelist.append(lv)
                    autocorlist.append(autocor)
                    threshlist.append(threshold)
                    hrlist.append(hr)
                    radiuslist.append(radius)
                    minsizelist.append(minsize)
                else:
                    gscript.message("Error in worker function: %s" % result)

        maplist += regional_maplist
        # Calculate optimization function values and get indices of best values
        if max(variancelist) > min(variancelist) and max(autocorlist) > min(
            autocorlist
        ):
            optlist = create_optimization_list(
                variancelist, autocorlist, opt_function, alpha, directions[indicator]
            )
            if rg:
                regiondict[region] = zip(
                    threshlist, minsizelist, variancelist, autocorlist, optlist
                )
            else:
                regiondict[region] = zip(
                    threshlist,
                    hrlist,
                    radiuslist,
                    minsizelist,
                    variancelist,
                    autocorlist,
                    optlist,
                )

            optimal_indices = find_optimal_value_indices(optlist, nb_best)
            best_values[region] = []
            rank = 1
            for optind in optimal_indices:
                if rg:
                    best_values[region].append(
                        [threshlist[optind], minsizelist[optind], optlist[optind]]
                    )
                else:
                    best_values[region].append(
                        [
                            threshlist[optind],
                            hrlist[optind],
                            radiuslist[optind],
                            minsizelist[optind],
                            optlist[optind],
                        ]
                    )
                maps_to_keep.append([regional_maplist[optind], rank, parms["region"]])
                rank += 1
        else:
            best_values[region] = []
            if rg:
                best_values[region].append([threshlist[0], minsizelist[0], -1])
            else:
                best_values[region].append(
                    [threshlist[0], hrlist[0], radiuslist[0], minsizelist[0], -1]
                )
            maps_to_keep.append([regional_maplist[0], -1, parms["region"]])

    # Create output

    # Output of results of all attempts
    if rg:
        header_string = "region,threshold,minsize,variance,spatial_autocorrelation,optimization_criteria\n"
    else:
        header_string = "region,threshold,hr,radius,minsize,variance,spatial_autocorrelation,optimization_criteria\n"

    if output:
        if output == "-":
            sys.stdout.write(header_string)
            for region, resultslist in iteritems(regiondict):
                for result in resultslist:
                    output_string = "%s," % region
                    output_string += ",".join(map(str, result))
                    output_string += "\n"
                    sys.stdout.write(output_string)
        else:
            of = open(output, "w")
            of.write(header_string)
            for region, resultslist in iteritems(regiondict):
                for result in resultslist:
                    output_string = "%s," % region
                    output_string += ",".join(map(str, result))
                    output_string += "\n"
                    of.write(output_string)
            of.close()

    # Output of best values found
    msg = "Best values:\n"
    if rg:
        msg += "Region\tThresh\tMinsize\tOptimization\n"
    else:
        msg += "Region\tThresh\tHr\tRadius\tMinsize\tOptimization\n"
    for region, resultlist in iteritems(best_values):
        for result in resultlist:
            msg += "%s\t" % region
            msg += "\t".join(map(str, result))
            msg += "\n"
    gscript.message(msg)

    # Keep copies of segmentation results with best values

    if segmented_map:
        for bestmap, rank, region in maps_to_keep:
            outputmap = segmented_map + "_" + region + "_rank%d" % rank
            gscript.run_command(
                "g.copy",
                raster=[bestmap, outputmap],
                quiet=True,
                overwrite=gscript.overwrite(),
            )


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
