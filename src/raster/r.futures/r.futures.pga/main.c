/****************************************************************************
 *
 * MODULE:       r.futures.pga
 * AUTHOR(S):    Ross K. Meentemeyer
 *               Wenwu Tang
 *               Monica A. Dorning
 *               John B. Vogler
 *               Nik J. Cunniffe
 *               Douglas A. Shoemaker
 *               Jennifer A. Koch
 *               Vaclav Petras <wenzeslaus gmail com>
 *               Anna Petrasova
 *               (See the manual page for details and references.)
 *
 * PURPOSE:      Simulation of urban-rural landscape structure (FUTURES model)
 *
 * COPYRIGHT:    (C) 2013-2016 by Anna Petrasova and Meentemeyer et al.
 *
 *               This program is free software: you can redistribute it and/or
 *               modify it under the terms of the GNU General Public License
 *               as published by the Free Software Foundation, either version 3
 *               of the License, or (at your option) any later version.
 *
 *               This program is distributed in the hope that it will be useful,
 *               but WITHOUT ANY WARRANTY; without even the implied warranty of
 *               MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *               GNU General Public License for more details.
 *
 *               You should have received a copy of the GNU General Public
 *               License along with this program. If not, see
 *               <http://www.gnu.org/licenses/> or read the file COPYING that
 *               comes with GRASS GIS for details.
 *
 *****************************************************************************/

/**
    \file main.c
    
    The main file containing both the model code and the data handing part.
    
    The language of the code is subject to change. The goal is to use either
    C or C++, not both mixed as it is now. Update: only C is used now.
    
    Major refactoring of the code is expected.
*/

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>
#include <sys/time.h>

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/segment.h>

#include "keyvalue.h"
#include "inputs.h"
#include "output.h"
#include "patch.h"
#include "devpressure.h"
#include "simulation.h"


struct Undeveloped *initialize_undeveloped(int num_subregions)
{
    struct Undeveloped *undev = (struct Undeveloped *) G_malloc(sizeof(struct Undeveloped));
    undev->max_subregions = num_subregions;
    undev->max = (size_t *) G_malloc(undev->max_subregions * sizeof(size_t));
    undev->num = (size_t *) G_calloc(undev->max_subregions, sizeof(size_t));
    undev->cells = (struct UndevelopedCell **) G_malloc(undev->max_subregions * sizeof(struct UndevelopedCell *));
    for (int i = 0; i < undev->max_subregions; i++){
        undev->max[i] = (Rast_window_rows() * Rast_window_cols()) / num_subregions;
        undev->cells[i] = (struct UndevelopedCell *) G_malloc(undev->max[i] * sizeof(struct UndevelopedCell));
    }
    return undev;
}


static int manage_memory(struct SegmentMemory *memory, struct Segments *segments,
                         float input_memory)
{
    int nseg, nseg_total;
    int cols, rows;
    int undev_size;
    size_t size;
    size_t estimate;

    memory->rows = 64;
    memory->cols = 64;
    rows = Rast_window_rows();
    cols = Rast_window_cols();

    undev_size = (sizeof(size_t) + sizeof(float) * 2 + sizeof(bool)) * rows * cols;
    estimate = undev_size;

    if (input_memory > 0 && undev_size > 1e9 * input_memory)
        G_warning(_("Not sufficient memory, will attempt to use more "
                    "than specified. Will need at least %d MB"), (int) (undev_size / 1.0e6));

    /* developed, subregions */
    size = sizeof(CELL) * 2;
    /* predictors, devpressure, probability */
    size += sizeof(FCELL) * 3;
    if (segments->use_weight)
        size += sizeof(FCELL);
    if (segments->use_potential_subregions)
        size += sizeof(CELL);
    estimate = estimate + (size * rows * cols);
    size *= memory->rows * memory->cols;

    nseg = (1e9 * input_memory - undev_size) / size;
    if (nseg <= 0)
        nseg = 1;
    nseg_total = (rows / memory->rows + (rows % memory->rows > 0)) *
                 (cols / memory->cols + (cols % memory->cols > 0));

    if (nseg > nseg_total || input_memory < 0)
	nseg = nseg_total;
    G_verbose_message(_("Number of segments in memory: %d of %d total"),
                      nseg, nseg_total);
    G_verbose_message(_("Estimated minimum memory footprint without using disk cache: %d MB"),
                      (int) (estimate / 1.0e6));
    return nseg;
}

int main(int argc, char **argv)
{

    struct
    {
        struct Option
                *developed, *subregions, *potentialSubregions, *predictors,
                *devpressure, *nDevNeighbourhood, *devpressureApproach, *scalingFactor, *gamma,
                *potentialFile, *numNeighbors, *discountFactor, *seedSearch,
                *patchMean, *patchRange,
                *incentivePower, *potentialWeight,
                *demandFile, *separator, *patchFile, *numSteps, *output, *outputSeries, *seed, *memory;

    } opt;

    struct
    {
        struct Flag *generateSeed;
    } flg;

    int i;
    int num_predictors;
    int num_steps;
    int nseg;
    int region;
    int region_id;
    int step;
    float memory;
    double discount_factor;
    float exponent;
    enum seed_search search_alg;
    struct RasterInputs raster_inputs;
    struct KeyValueIntInt *region_map;
    struct KeyValueIntInt *reverse_region_map;
    struct KeyValueIntInt *potential_region_map;
    struct Undeveloped *undev_cells;
    struct Demand demand_info;
    struct Potential potential_info;
    struct SegmentMemory segment_info;
    struct PatchSizes patch_sizes;
    struct PatchInfo patch_info;
    struct DevPressure devpressure_info;
    struct Segments segments;
    int *patch_overflow;
    char *name_step;
    bool overgrow;

    G_gisinit(argv[0]);

    struct GModule *module = G_define_module();

    G_add_keyword(_("raster"));
    G_add_keyword(_("patch growing"));
    G_add_keyword(_("urban"));
    G_add_keyword(_("landscape"));
    G_add_keyword(_("modeling"));
    module->label =
            _("Simulates landuse change using FUTure Urban-Regional Environment Simulation (FUTURES).");
    module->description =
            _("Module uses Patch-Growing Algorithm (PGA) to"
              " simulate urban-rural landscape structure development.");

    opt.developed = G_define_standard_option(G_OPT_R_INPUT);
    opt.developed->key = "developed";
    opt.developed->required = YES;
    opt.developed->description =
            _("Raster map of developed areas (=1), undeveloped (=0) and excluded (no data)");
    opt.developed->guisection = _("Basic input");

    opt.subregions = G_define_standard_option(G_OPT_R_INPUT);
    opt.subregions->key = "subregions";
    opt.subregions->required = YES;
    opt.subregions->description = _("Raster map of subregions");
    opt.subregions->guisection = _("Basic input");

    opt.potentialSubregions = G_define_standard_option(G_OPT_R_INPUT);
    opt.potentialSubregions->key = "subregions_potential";
    opt.potentialSubregions->required = NO;
    opt.potentialSubregions->label = _("Raster map of subregions used with potential file");
    opt.potentialSubregions->description = _("If not specified, the raster specified in subregions parameter is used");
    opt.potentialSubregions->guisection = _("Potential");

    opt.predictors = G_define_standard_option(G_OPT_R_INPUTS);
    opt.predictors->key = "predictors";
    opt.predictors->required = YES;
    opt.predictors->multiple = YES;
    opt.predictors->label = _("Names of predictor variable raster maps");
    opt.predictors->description = _("Listed in the same order as in the development potential table");
    opt.predictors->guisection = _("Potential");

    opt.devpressure = G_define_standard_option(G_OPT_R_INPUT);
    opt.devpressure->key = "development_pressure";
    opt.devpressure->required = YES;
    opt.devpressure->description =
            _("Raster map of development pressure");
    opt.devpressure->guisection = _("Development pressure");

    opt.nDevNeighbourhood = G_define_option();
    opt.nDevNeighbourhood->key = "n_dev_neighbourhood";
    opt.nDevNeighbourhood->type = TYPE_INTEGER;
    opt.nDevNeighbourhood->required = YES;
    opt.nDevNeighbourhood->description =
        _("Size of square used to recalculate development pressure");
    opt.nDevNeighbourhood->guisection = _("Development pressure");

    opt.devpressureApproach = G_define_option();
    opt.devpressureApproach->key = "development_pressure_approach";
    opt.devpressureApproach->type = TYPE_STRING;
    opt.devpressureApproach->required = YES;
    opt.devpressureApproach->options = "occurrence,gravity,kernel";
    opt.devpressureApproach->description =
        _("Approaches to derive development pressure");
    opt.devpressureApproach->answer = "gravity";
    opt.devpressureApproach->guisection = _("Development pressure");

    opt.gamma = G_define_option();
    opt.gamma->key = "gamma";
    opt.gamma->type = TYPE_DOUBLE;
    opt.gamma->required = YES;
    opt.gamma->description =
        _("Influence of distance between neighboring cells");
    opt.gamma->guisection = _("Development pressure");

    opt.scalingFactor = G_define_option();
    opt.scalingFactor->key = "scaling_factor";
    opt.scalingFactor->type = TYPE_DOUBLE;
    opt.scalingFactor->required = YES;
    opt.scalingFactor->description =
        _("Scaling factor of development pressure");
    opt.scalingFactor->guisection = _("Development pressure");

    opt.output = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.output->key = "output";
    opt.output->required = YES;
    opt.output->description =
            _("State of the development at the end of simulation");
    opt.output->guisection = _("Output");

    opt.outputSeries = G_define_standard_option(G_OPT_R_BASENAME_OUTPUT);
    opt.outputSeries->key = "output_series";
    opt.outputSeries->required = NO;
    opt.outputSeries->label =
        _("Basename for raster maps of development generated after each step");
    opt.outputSeries->guisection = _("Output");

    opt.potentialFile = G_define_standard_option(G_OPT_F_INPUT);
    opt.potentialFile->key = "devpot_params";
    opt.potentialFile->required = YES;
    opt.potentialFile->label =
        _("CSV file with development potential parameters for each region");
    opt.potentialFile->description =
        _("Each line should contain region ID followed"
          " by parameters (intercepts, development pressure, other predictors)."
          " First line is ignored, so it can be used for header");
    opt.potentialFile->guisection = _("Potential");

    opt.demandFile = G_define_standard_option(G_OPT_F_INPUT);
    opt.demandFile->key = "demand";
    opt.demandFile->required = YES;
    opt.demandFile->description =
            _("CSV file with number of cells to convert for each step and subregion");
    opt.demandFile->guisection = _("Demand");

    opt.separator = G_define_standard_option(G_OPT_F_SEP);
    opt.separator->answer = "comma";
    opt.separator->description =
            _("Separator used in input CSV files");

    opt.patchFile = G_define_standard_option(G_OPT_F_INPUT);
    opt.patchFile->key = "patch_sizes";
    opt.patchFile->required = YES;
    opt.patchFile->description =
        _("File containing list of patch sizes to use");
    opt.patchFile->guisection = _("PGA");

    opt.numNeighbors = G_define_option();
    opt.numNeighbors->key = "num_neighbors";
    opt.numNeighbors->type = TYPE_INTEGER;
    opt.numNeighbors->required = YES;
    opt.numNeighbors->options = "4,8";
    opt.numNeighbors->answer = "4";
    opt.numNeighbors->description =
        _("The number of neighbors to be used for patch generation (4 or 8)");
    opt.numNeighbors->guisection = _("PGA");

    opt.discountFactor = G_define_option();
    opt.discountFactor->key = "discount_factor";
    opt.discountFactor->type = TYPE_DOUBLE;
    opt.discountFactor->required = YES;
    opt.discountFactor->description = _("Discount factor of patch size");
    opt.discountFactor->guisection = _("PGA");

    opt.seedSearch = G_define_option();
    opt.seedSearch->key = "seed_search";
    opt.seedSearch->type = TYPE_STRING;
    opt.seedSearch->required = YES;
    opt.seedSearch->options = "random,probability";
    opt.seedSearch->answer = "probability";
    opt.seedSearch->description =
        _("The way location of a seed is determined (1: uniform distribution 2: development probability)");
    opt.seedSearch->guisection = _("PGA");
    
    opt.patchMean = G_define_option();
    opt.patchMean->key = "compactness_mean";
    opt.patchMean->type = TYPE_DOUBLE;
    opt.patchMean->required = YES;
    opt.patchMean->description =
        _("Mean value of patch compactness to control patch shapes");
    opt.patchMean->guisection = _("PGA");

    opt.patchRange = G_define_option();
    opt.patchRange->key = "compactness_range";
    opt.patchRange->type = TYPE_DOUBLE;
    opt.patchRange->required = YES;
    opt.patchRange->description =
        _("Range of patch compactness to control patch shapes");
    opt.patchRange->guisection = _("PGA");

    opt.numSteps = G_define_option();
    opt.numSteps->key = "num_steps";
    opt.numSteps->type = TYPE_INTEGER;
    opt.numSteps->required = NO;
    opt.numSteps->description =
        _("Number of steps to be simulated");
    opt.numSteps->guisection = _("Basic input");

    opt.potentialWeight = G_define_standard_option(G_OPT_R_INPUT);
    opt.potentialWeight->key = "potential_weight";
    opt.potentialWeight->required = NO;
    opt.potentialWeight->label =
            _("Raster map of weights altering development potential");
    opt.potentialWeight->description =
            _("Values need to be between -1 and 1, where negative locally reduces"
              "probability and positive increases probability.");
    opt.potentialWeight->guisection = _("Scenarios");
    
    opt.incentivePower = G_define_option();
    opt.incentivePower->key = "incentive_power";
    opt.incentivePower->required = NO;
    opt.incentivePower->type = TYPE_DOUBLE;
    opt.incentivePower->answer = "1";
    opt.incentivePower->label =
        _("Exponent to transform probability values p to p^x to simulate infill vs. sprawl");
    opt.incentivePower->description =
        _("Values > 1 encourage infill, < 1 urban sprawl");
    opt.incentivePower->guisection = _("Scenarios");
    opt.incentivePower->options = "0-10";

    opt.seed = G_define_option();
    opt.seed->key = "random_seed";
    opt.seed->type = TYPE_INTEGER;
    opt.seed->required = NO;
    opt.seed->label = _("Seed for random number generator");
    opt.seed->description =
            _("The same seed can be used to obtain same results"
              " or random seed can be generated by other means.");
    opt.seed->guisection = _("Random numbers");

    flg.generateSeed = G_define_flag();
    flg.generateSeed->key = 's';
    flg.generateSeed->label =
            _("Generate random seed (result is non-deterministic)");
    flg.generateSeed->description =
            _("Automatically generates random seed for random number"
              " generator (use when you don't want to provide the seed option)");
    flg.generateSeed->guisection = _("Random numbers");

    opt.memory = G_define_option();
    opt.memory->key = "memory";
    opt.memory->type = TYPE_DOUBLE;
    opt.memory->required = NO;
    opt.memory->description = _("Memory in GB");

    // TODO: add mutually exclusive?
    // TODO: add flags or options to control values in series and final rasters

    // provided XOR generated
    G_option_exclusive(opt.seed, flg.generateSeed, NULL);
    G_option_required(opt.seed, flg.generateSeed, NULL);
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    long seed_value;

    if (flg.generateSeed->answer) {
        seed_value = G_srand48_auto();
        G_message("Generated random seed (-s): %ld", seed_value);
    }
    if (opt.seed->answer) {
        seed_value = atol(opt.seed->answer);
        // this does nothing since we are not using GRASS random function
        G_srand48(seed_value);
        G_message("Read random seed from %s option: %ld",
                  opt.seed->key, seed_value);
    }

    devpressure_info.scaling_factor = atof(opt.scalingFactor->answer);
    devpressure_info.gamma = atof(opt.gamma->answer);
    devpressure_info.neighborhood = atoi(opt.nDevNeighbourhood->answer);
    discount_factor = atof(opt.discountFactor->answer);
    if (strcmp(opt.devpressureApproach->answer, "occurrence") == 0)
        devpressure_info.alg = OCCURRENCE;
    else if (strcmp(opt.devpressureApproach->answer, "gravity") == 0)
        devpressure_info.alg = GRAVITY;
    else if (strcmp(opt.devpressureApproach->answer, "kernel") == 0)
        devpressure_info.alg = KERNEL;
    else
        G_fatal_error(_("Approach doesn't exist"));
    initialize_devpressure_matrix(&devpressure_info);

    if (strcmp(opt.seedSearch->answer, "random") == 0)
        search_alg = RANDOM;
    else if (strcmp(opt.seedSearch->answer, "probability") == 0)
        search_alg = PROBABILITY;
    else
        G_fatal_error(_("Approach doesn't exist"));
    patch_info.compactness_mean = atof(opt.patchMean->answer);
    patch_info.compactness_range = atof(opt.patchRange->answer);
    patch_info.num_neighbors = atoi(opt.numNeighbors->answer);
    patch_info.strategy = SKIP;
    
    num_steps = 0;
    if (opt.numSteps->answer)
        num_steps = atoi(opt.numSteps->answer);
    
    num_predictors = 0;
    for (i = 0; opt.predictors->answers[i]; i++)
        num_predictors++;
    
    segments.use_weight = false;
    if (opt.potentialWeight->answer) {
        segments.use_weight = true;
    }
    segments.use_potential_subregions = false;
    if (opt.potentialSubregions->answer) {
        segments.use_potential_subregions = true;
    }
    memory = -1;
    if (opt.memory->answer)
        memory = atof(opt.memory->answer);
    nseg = manage_memory(&segment_info, &segments, memory);
    segment_info.in_memory = nseg;

    potential_info.incentive_transform_size = 0;
    potential_info.incentive_transform = NULL;
    if (opt.incentivePower->answer) {
        exponent = atof(opt.incentivePower->answer);
        if (exponent !=  1)  /* 1 is no-op */
            initialize_incentive(&potential_info, exponent);
    }

    raster_inputs.developed = opt.developed->answer;
    raster_inputs.regions = opt.subregions->answer;
    raster_inputs.devpressure = opt.devpressure->answer;
    raster_inputs.predictors = opt.predictors->answers;
    if (opt.potentialWeight->answer)
        raster_inputs.weights = opt.potentialWeight->answer;
    if (opt.potentialSubregions->answer)
        raster_inputs.potential_regions = opt.potentialSubregions->answer;

    //    read Subregions layer
    region_map = KeyValueIntInt_create();
    reverse_region_map = KeyValueIntInt_create();
    potential_region_map = KeyValueIntInt_create();
    G_verbose_message("Reading input rasters...");
    read_input_rasters(raster_inputs, &segments, segment_info, region_map,
                       reverse_region_map, potential_region_map);

    /* create probability segment*/
    if (Segment_open(&segments.probability, G_tempfile(), Rast_window_rows(),
                     Rast_window_cols(), segment_info.rows, segment_info.cols,
                     Rast_cell_size(FCELL_TYPE), segment_info.in_memory) != 1)
        G_fatal_error(_("Cannot create temporary file with segments of a raster map"));

    /* read Potential file */
    G_verbose_message("Reading potential file...");
    potential_info.filename = opt.potentialFile->answer;
    potential_info.separator = G_option_to_separator(opt.separator);
    read_potential_file(&potential_info, opt.potentialSubregions->answer ? potential_region_map : region_map, num_predictors);

    /* read in predictors and aggregate to save memory */
    G_verbose_message("Reading predictors...");
    read_predictors(raster_inputs, &segments, &potential_info,
                    segment_info);

    /* read Demand file */
    G_verbose_message("Reading demand file...");
    demand_info.filename = opt.demandFile->answer;
    demand_info.separator = G_option_to_separator(opt.separator);
    read_demand_file(&demand_info, region_map);
    if (num_steps == 0)
        num_steps = demand_info.max_steps;

    /* read Patch sizes file */
    G_verbose_message("Reading patch size file...");
    patch_sizes.filename = opt.patchFile->answer;
    read_patch_sizes(&patch_sizes, region_map, discount_factor);

    undev_cells = initialize_undeveloped(region_map->nitems);
    patch_overflow = G_calloc(region_map->nitems, sizeof(int));
    /* here do the modeling */
    overgrow = true;
    G_verbose_message("Starting simulation...");
    for (step = 0; step < num_steps; step++) {
        recompute_probabilities(undev_cells, &segments, &potential_info);
        if (step == num_steps - 1)
            overgrow = false;
        for (region = 0; region < region_map->nitems; region++) {
            KeyValueIntInt_find(reverse_region_map, region, &region_id);
            G_verbose_message("Computing step %d (out of %d), region %d (%d out of %d)", step + 1, num_steps, region_id,
                              region + 1, region_map->nitems);
            compute_step(undev_cells, &demand_info, search_alg, &segments,
                         &patch_sizes, &patch_info, &devpressure_info, patch_overflow,
                         step, region, reverse_region_map, overgrow);
        }
        /* export developed for that step */
        if (opt.outputSeries->answer) {
            name_step = name_for_step(opt.outputSeries->answer, step, num_steps);
            output_developed_step(&segments.developed, name_step,
                                  demand_info.years[step], -1, num_steps, true, true);
        }
    }

    /* write */
    output_developed_step(&segments.developed, opt.output->answer,
                          demand_info.years[0], demand_info.years[step-1],
                          num_steps, false, false);

    /* close segments and free memory */
    Segment_close(&segments.developed);
    Segment_close(&segments.subregions);
    Segment_close(&segments.devpressure);
    Segment_close(&segments.probability);
    Segment_close(&segments.aggregated_predictor);
    if (opt.potentialWeight->answer) {
        Segment_close(&segments.weight);
    }
    if (opt.potentialSubregions->answer)
        Segment_close(&segments.potential_subregions);

    KeyValueIntInt_free(region_map);
    KeyValueIntInt_free(reverse_region_map);
    if (demand_info.table) {
        for (int i = 0; i < demand_info.max_subregions; i++)
            G_free(demand_info.table[i]);
        G_free(demand_info.table);
        G_free(demand_info.years);
    }
    if (potential_info.predictors) {
        for (int i = 0; i < potential_info.max_predictors; i++)
            G_free(potential_info.predictors[i]);
        G_free(potential_info.predictors);
        G_free(potential_info.devpressure);
        G_free(potential_info.intercept);
    }
    for (int i = 0; i < devpressure_info.neighborhood * 2 + 1; i++)
        G_free(devpressure_info.matrix[i]);
    G_free(devpressure_info.matrix);
    if (potential_info.incentive_transform_size > 0)
        G_free(potential_info.incentive_transform);
    if (undev_cells) {
        G_free(undev_cells->num);
        G_free(undev_cells->max);
        for (int i = 0; i < undev_cells->max_subregions; i++)
            G_free(undev_cells->cells[i]);
        G_free(undev_cells->cells);
        G_free(undev_cells);
    }

    G_free(patch_sizes.patch_sizes);
    G_free(patch_overflow);

    return EXIT_SUCCESS;
}

