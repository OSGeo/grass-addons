#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
##############################################################################
#
# MODULE:       r.futures.calib
#
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#
# PURPOSE:      FUTURES patches calibration tool
#
# COPYRIGHT:    (C) 2016 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
##############################################################################

#%module
#% description: Module for calibrating patch characteristics used as input to r.futures.pga
#% keyword: raster
#% keyword: patch
#%end
#%option G_OPT_R_INPUT
#% key: development_start
#% label: Name of input binary raster map representing development in the beginning
#% description: Raster map of developed areas (=1), undeveloped (=0) and excluded (no data)
#% guisection: Calibration
#%end
#%option G_OPT_R_INPUT
#% key: development_end
#% label: Name of input binary raster map representing development in the end
#% description: Raster map of developed areas (=1), undeveloped (=0) and excluded (no data)
#% guisection: Calibration
#%end
#%option
#% type: integer
#% key: repeat
#% description: How many times is the simulation repeated
#% required: no
#% guisection: Calibration
#%end
#%option
#% key: compactness_mean
#% type: double
#% description: Patch compactness mean to be tested
#% required: no
#% multiple: yes
#% guisection: Calibration
#%end
#%option
#% type: double
#% key: compactness_range
#% description: Patch compactness range to be tested
#% required: no
#% multiple: yes
#% guisection: Calibration
#%end
#%option
#% type: double
#% key: discount_factor
#% description: Patch size discount factor
#% key: discount_factor
#% multiple: yes
#% required: no
#% guisection: Calibration
#%end
#%option
#% type: double
#% key: patch_threshold
#% description: Minimum size of a patch in meters squared
#% required: yes
#% answer: 0
#% guisection: Calibration
#%end
#%option G_OPT_F_OUTPUT
#% key: patch_sizes
#% description: Output file with patch sizes
#% required: yes
#% guisection: Calibration
#%end
#%option G_OPT_F_OUTPUT
#% key: calibration_results
#% description: Output file with calibration results
#% required: no
#% guisection: Calibration
#%end
#%option
#% key: nprocs
#% type: integer
#% description: Number of parallel processes
#% required: yes
#% answer: 1
#% guisection: Calibration
#%end
#%option G_OPT_R_INPUT
#% key: development_pressure
#% required: no
#% description: Raster map of development pressure
#% guisection: PGA
#%end
#%option
#% key: incentive_power
#% type: double
#% required: no
#% multiple: no
#% options: 0-10
#% label: Exponent to transform probability values p to p^x to simulate infill vs. sprawl
#% description: Values > 1 encourage infill, < 1 urban sprawl
#% answer: 1
#% guisection: PGA
#%end
#%option G_OPT_R_INPUT
#% key: constrain_weight
#% required: no
#% label: Name of raster map representing development potential constraint weight for scenarios
#% description: Values must be between 0 and 1, 1 means no constraint
#% guisection: PGA
#%end
#%option G_OPT_R_INPUTS
#% key: predictors
#% required: no
#% multiple: yes
#% description: Names of predictor variable raster maps
#% guisection: PGA
#%end
#%option
#% key: n_dev_neighbourhood
#% type: integer
#% description: Size of square used to recalculate development pressure
#% required: no
#% guisection: PGA
#%end
#%option G_OPT_F_INPUT
#% key: devpot_params
#% required: no
#% multiple: yes
#% label: Development potential parameters for each region
#% description: Each line should contain region ID followed by parameters. Values are separated by whitespace (spaces or tabs). First line is ignored, so it can be used for header
#% guisection: PGA
#%end
#%option
#% key: num_neighbors
#% type: integer
#% required: no
#% multiple: no
#% options: 4,8
#% description: The number of neighbors to be used for patch generation (4 or 8)
#% guisection: PGA
#%end
#%option
#% key: seed_search
#% type: string
#% required: yes
#% multiple: no
#% options: random,probability
#% description: The way location of a seed is determined (1: uniform distribution 2: development probability)
#% answer: probability
#% guisection: PGA
#%end
#%option
#% key: development_pressure_approach
#% type: string
#% required: no
#% multiple: no
#% options: occurrence,gravity,kernel
#% description: Approaches to derive development pressure
#% guisection: PGA
#%end
#%option
#% key: gamma
#% type: double
#% required: no
#% multiple: no
#% description: Influence of distance between neighboring cells
#% guisection: PGA
#%end
#%option
#% key: scaling_factor
#% type: double
#% required: no
#% multiple: no
#% description: Scaling factor of development pressure
#% guisection: PGA
#%end
#%option
#% key: num_steps
#% type: integer
#% required: no
#% multiple: no
#% description: Number of steps to be simulated
#% guisection: PGA
#%end
#%option G_OPT_R_INPUT
#% key: subregions
#% required: yes
#% description: Raster map of subregions with categories starting with 1
#% guisection: PGA
#%end
#%option G_OPT_F_INPUT
#% key: demand
#% required: no
#% description: Control file with number of cells to convert
#% guisection: PGA
#%end
#%flag
#% key: l
#% description: Only create patch size distribution file
#% guisection: Calibration
#%end
#%rules
#% collective: demand,scaling_factor,gamma,development_pressure_approach,seed_search,num_neighbors,devpot_params,n_dev_neighbourhood,predictors,development_pressure,calibration_results,discount_factor,compactness_range,compactness_mean,repeat
#% exclusive: -l,demand
#% exclusive: -l,num_steps
#% exclusive: -l,scaling_factor
#% exclusive: -l,gamma
#% exclusive: -l,development_pressure_approach
#% exclusive: -l,seed_search
#% exclusive: -l,num_neighbors
#% exclusive: -l,incentive_power
#% exclusive: -l,devpot_params
#% exclusive: -l,n_dev_neighbourhood
#% exclusive: -l,predictors
#% exclusive: -l,constrain_weight
#% exclusive: -l,development_pressure
#% exclusive: -l,calibration_results
#% exclusive: -l,discount_factor
#% exclusive: -l,compactness_range
#% exclusive: -l,compactness_mean
#% exclusive: -l,repeat
#% required: -l,demand
#% required: -l,scaling_factor
#% required: -l,gamma
#% required: -l,development_pressure_approach
#% required: -l,seed_search
#% required: -l,num_neighbors
#% required: -l,devpot_params
#% required: -l,n_dev_neighbourhood
#% required: -l,predictors
#% required: -l,development_pressure
#% required: -l,calibration_results
#% required: -l,discount_factor
#% required: -l,compactness_range
#% required: -l,compactness_mean
#% required: -l,repeat
#%end

import sys
import os
import atexit
import numpy as np
import tempfile
from multiprocessing import Process, Queue

import grass.script.core as gcore
import grass.script.raster as grast
import grass.script.utils as gutils
from grass.exceptions import CalledModuleError


TMP = []
TMPFILE = None


def cleanup(tmp=None):
    if tmp:
        maps = tmp
    else:
        maps = TMP
    gcore.run_command('g.remove', flags='f', type=['raster', 'vector'], name=maps)
    gutils.try_remove(TMPFILE)


def run_one_combination(repeat, development_start, compactness_mean, compactness_range,
                        discount_factor, patches_file, fut_options, threshold,
                        hist_bins_area_orig, hist_range_area_orig, hist_bins_compactness_orig,
                        hist_range_compactness_orig, cell_size, histogram_area_orig, histogram_compactness_orig,
                        tmp_name, queue):
    TMP_PROCESS = []
    # unique name, must be sql compliant
    suffix = (str(discount_factor) + str(compactness_mean) + str(compactness_range)).replace('.', '')
    simulation_dev_end = tmp_name + 'simulation_dev_end_' + suffix
    simulation_dev_diff = tmp_name + 'simulation_dev_diff' + suffix
    tmp_patch_vect = tmp_name + 'tmp_patch_vect' + suffix
    tmp_patch_vect2 = tmp_name + 'tmp_patch_vect2' + suffix
    TMP_PROCESS.append(simulation_dev_diff)
    TMP_PROCESS.append(simulation_dev_diff)
    TMP_PROCESS.append(tmp_patch_vect)
    TMP_PROCESS.append(tmp_patch_vect2)

    sum_dist_area = 0
    sum_dist_compactness = 0
    for i in range(repeat):
        gcore.message(_("Running FUTURES simulation {i}/{repeat}...".format(i=i + 1, repeat=repeat)))
        try:
            run_simulation(development_start=development_start, development_end=simulation_dev_end,
                           compactness_mean=compactness_mean, compactness_range=compactness_range,
                           discount_factor=discount_factor, patches_file=patches_file, fut_options=fut_options)
        except CalledModuleError as e:
            queue.put(None)
            cleanup(tmp=TMP_PROCESS)
            gcore.error(_("Running r.futures.pga failed. Details: {e}").format(e=e))
            return
        new_development(simulation_dev_end, simulation_dev_diff)

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        patch_analysis(simulation_dev_diff, threshold, tmp_patch_vect, tmp_patch_vect2, temp_file.name)
        sim_hist_area, sim_hist_compactness = create_histograms(temp_file.name, hist_bins_area_orig, hist_range_area_orig,
                                                                hist_bins_compactness_orig, hist_range_compactness_orig, cell_size)
        os.remove(temp_file.name)

        sum_dist_area += compare_histograms(histogram_area_orig, sim_hist_area)
        sum_dist_compactness += compare_histograms(histogram_compactness_orig, sim_hist_compactness)

    mean_dist_area = sum_dist_area / repeat
    mean_dist_compactness = sum_dist_compactness / repeat

    data = {}
    data['input_discount_factor'] = discount_factor
    data['input_compactness_mean'] = compactness_mean
    data['input_compactness_range'] = compactness_range
    data['area_distance'] = mean_dist_area
    data['compactness_distance'] = mean_dist_compactness
    queue.put(data)
    cleanup(tmp=TMP_PROCESS)


def run_simulation(development_start, development_end, compactness_mean, compactness_range, discount_factor, patches_file, fut_options):
    parameters = dict(compactness_mean=compactness_mean, compactness_range=compactness_range,
                      discount_factor=discount_factor, patch_sizes=patches_file,
                      developed=development_start)
    futures_parameters = dict(development_pressure=fut_options['development_pressure'],
                              predictors=fut_options['predictors'], n_dev_neighbourhood=fut_options['n_dev_neighbourhood'],
                              devpot_params=fut_options['devpot_params'],
                              num_neighbors=fut_options['num_neighbors'], seed_search=fut_options['seed_search'],
                              development_pressure_approach=fut_options['development_pressure_approach'], gamma=fut_options['gamma'],
                              scaling_factor=fut_options['scaling_factor'],
                              subregions=fut_options['subregions'], demand=fut_options['demand'],
                              output=development_end)
    parameters.update(futures_parameters)
    for not_required in ('constrain_weight', 'num_steps', 'incentive_power'):
        if fut_options[not_required]:
            parameters.update({not_required: fut_options[not_required]})

    gcore.run_command('r.futures.pga', flags='s', overwrite=True, **parameters)


def diff_development(development_start, development_end, subregions, development_diff):
    grast.mapcalc(exp="{res} = if({subregions} && {dev_end} && (isnull({dev_start}) ||| !{dev_start}), 1, null())".format(res=development_diff, subregions=subregions,
                  dev_end=development_end, dev_start=development_start), overwrite=True, quiet=True)


def new_development(development_end, development_diff):
    grast.mapcalc(exp="{res} = if({dev_end} > 0, 1, null())".format(res=development_diff,
                  dev_end=development_end), overwrite=True, quiet=True)


def patch_analysis(development_diff, threshold, tmp_vector_patches, tmp_vector_patches2, output_file):
    gcore.run_command('r.to.vect', input=development_diff, output=tmp_vector_patches2, type='area', overwrite=True, quiet=True)
    gcore.run_command('v.clean', input=tmp_vector_patches2, output=tmp_vector_patches, tool='rmarea', threshold=threshold, quiet=True, overwrite=True)
    gcore.run_command('v.db.addcolumn', map=tmp_vector_patches, columns="area double precision,perimeter double precision", quiet=True)
    gcore.run_command('v.to.db', map=tmp_vector_patches, option='area', column='area', units='meters', quiet=True)
    gcore.run_command('v.to.db', map=tmp_vector_patches, option='perimeter', column='perimeter', units='meters', quiet=True)
    gcore.run_command('v.db.select', map=tmp_vector_patches, columns=['area', 'perimeter'],
                      flags='c', separator='space', file_=output_file, overwrite=True, quiet=True)


def create_histograms(input_file, hist_bins_area_orig, hist_range_area_orig, hist_bins_compactness_orig, hist_range_compactness_orig, cell_size):
    area, perimeter = np.loadtxt(fname=input_file, unpack=True)
    compact = compactness(area, perimeter)
    histogram_area, _edges = np.histogram(area / cell_size, bins=hist_bins_area_orig,
                                          range=hist_range_area_orig, density=True)
    histogram_area = histogram_area * 100
    histogram_compactness, _edges = np.histogram(compact, bins=hist_bins_compactness_orig,
                                                 range=hist_range_compactness_orig, density=True)
    histogram_compactness = histogram_compactness * 100
    return histogram_area, histogram_compactness


def write_patches_file(vector_patches, cell_size, output_file):
    gcore.run_command('v.db.select', map=vector_patches, columns='area',
                      flags='c', separator='space', file_=output_file, quiet=True)
    areas = np.loadtxt(fname=output_file)
    areas = np.round(areas / cell_size)
    np.savetxt(fname=output_file, X=areas.astype(int), fmt='%u')


def compare_histograms(hist1, hist2):
    """
    >>> hist1, edg = np.histogram(np.array([1, 1, 2, 2.5, 2.4]), bins=3, range=(0, 6))
    >>> hist2, edg = np.histogram(np.array([1, 1, 3 ]), bins=3, range=(0, 6))
    >>> compare_histograms(hist1, hist2)
    0.5
    """
    mask = np.logical_not(np.logical_or(hist1, hist2))
    hist1 = np.ma.masked_array(hist1, mask=mask)
    hist2 = np.ma.masked_array(hist2, mask=mask)
    res = 0.5 * np.sum(np.power(hist1 - hist2, 2) / (hist1.astype(float) + hist2))
    return res


def compactness(area, perimeter):
    return perimeter / (2 * np.sqrt(np.pi * area))


def main():
    dev_start = options['development_start']
    dev_end = options['development_end']
    only_file = flags['l']
    if not only_file:
        repeat = int(options['repeat'])
        compactness_means = [float(each) for each in options['compactness_mean'].split(',')]
        compactness_ranges = [float(each) for each in options['compactness_range'].split(',')]
        discount_factors = [float(each) for each in options['discount_factor'].split(',')]
    patches_file = options['patch_sizes']
    threshold = float(options['patch_threshold'])
    # v.clean removes size <= threshold, we want to keep size == threshold
    threshold -= 1e-6

    # compute cell size
    region = gcore.region()
    res = (region['nsres'] + region['ewres'])/2.
    coeff = float(gcore.parse_command('g.proj', flags='g')['meters'])
    cell_size = res * res * coeff * coeff

    tmp_name = 'tmp_futures_calib_' + str(os.getpid()) + '_'
    global TMP, TMPFILE

    orig_patch_diff = tmp_name + 'orig_patch_diff'
    TMP.append(orig_patch_diff)
    tmp_patch_vect = tmp_name + 'tmp_patch_vect'
    tmp_patch_vect2 = tmp_name + 'tmp_patch_vect2'
    TMP.append(tmp_patch_vect)
    TMP.append(tmp_patch_vect2)
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    TMPFILE = temp_file.name

    gcore.message(_("Analyzing original patches..."))
    diff_development(dev_start, dev_end, options['subregions'], orig_patch_diff)
    patch_analysis(orig_patch_diff, threshold, tmp_patch_vect, tmp_patch_vect2, temp_file.name)
    write_patches_file(tmp_patch_vect, cell_size, patches_file)
    if only_file:
        return

    area, perimeter = np.loadtxt(fname=temp_file.name, unpack=True)
    compact = compactness(area, perimeter)

    # area histogram
    area = area / cell_size
    bin_width = 1.  # automatic ways to determine bin width do not perform well in this case
    hist_bins_area_orig = int(np.ptp(area) / bin_width)
    hist_range_area_orig = (np.min(area), np.max(area))
    histogram_area_orig, _edges = np.histogram(area, bins=hist_bins_area_orig,
                                               range=hist_range_area_orig, density=True)
    histogram_area_orig = histogram_area_orig * 100  # to get percentage for readability

    # compactness histogram
    bin_width = 0.1
    hist_bins_compactness_orig = int(np.ptp(compact) / bin_width)
    hist_range_compactness_orig = (np.min(compact), np.max(compact))
    histogram_compactness_orig, _edges = np.histogram(compact, bins=hist_bins_compactness_orig,
                                                      range=hist_range_compactness_orig, density=True)
    histogram_compactness_orig = histogram_compactness_orig * 100  # to get percentage for readability

    nprocs = int(options['nprocs'])
    count = 0
    proc_count = 0
    queue_list = []
    proc_list = []
    num_all = len(compactness_means) * len(compactness_ranges) * len(discount_factors)
    with open(options['calibration_results'], 'a') as f:
        f.write(','.join(['input_discount_factor', 'area_distance',
                          'input_compactness_mean', 'input_compactness_range',
                          'compactness_distance']))
        f.write('\n')
        for com_mean in compactness_means:
            for com_range in compactness_ranges:
                for discount_factor in discount_factors:
                    count += 1
                    q = Queue()
                    p = Process(target=run_one_combination,
                                args=(repeat, dev_start, com_mean, com_range,
                                      discount_factor, patches_file, options, threshold,
                                      hist_bins_area_orig, hist_range_area_orig, hist_bins_compactness_orig,
                                      hist_range_compactness_orig, cell_size, histogram_area_orig, histogram_compactness_orig,
                                      tmp_name, q))
                    p.start()
                    queue_list.append(q)
                    proc_list.append(p)
                    proc_count += 1
                    if proc_count == nprocs or count == num_all:
                        for i in range(proc_count):
                            proc_list[i].join()
                            data = queue_list[i].get()
                            if not data:
                                continue
                            f.write(','.join([str(data['input_discount_factor']), str(data['area_distance']),
                                              str(data['input_compactness_mean']), str(data['input_compactness_range']),
                                              str(data['compactness_distance'])]))
                            f.write('\n')
                        f.flush()
                        proc_count = 0
                        proc_list = []
                        queue_list = []

if __name__ == "__main__":
    options, flags = gcore.parser()
    atexit.register(cleanup)
    sys.exit(main())
