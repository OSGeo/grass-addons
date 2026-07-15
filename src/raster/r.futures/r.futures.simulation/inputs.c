/*!
   \file inputs.c

   \brief Functions to read in input files and rasters

   (C) 2016-2019 by Vaclav Petras and the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2).  Read the file COPYING that comes with GRASS for details.

   \author Vaclav Petras
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/segment.h>

#include "inputs.h"
#include "map.h"
#include "utils.h"

/*!
 * \brief Get developed value depending on step and
 * whether abandonment is being tracked
 * \param step
 * \param abandon
 * \return
 */
int get_developed_val_from_step(int step, bool abandon)
{
    if (abandon)
        return -step - 2;
    else
        return step + 1;
}

/*!
 * \brief Estimate number of undeveloped cells for later memory requirements
 * \param inputs raster inputs
 * \return number of estimated undeveloped cells
 */
size_t estimate_undev_size(struct RasterInputs inputs)
{
    int row, col;
    int rows, cols;
    int fd_developed;
    CELL *developed_row;
    size_t undeveloped;
    int skip_rows = 4;

    rows = Rast_window_rows();
    cols = Rast_window_cols();
    fd_developed = Rast_open_old(inputs.developed, "");
    developed_row = Rast_allocate_buf(CELL_TYPE);
    undeveloped = row = 0;

    while (row < rows) {
        Rast_get_row(fd_developed, developed_row, row, CELL_TYPE);
        for (col = 0; col < cols; col++) {
            if (!Rast_is_null_value(&((CELL *)developed_row)[col], CELL_TYPE)) {
                if (((CELL *)developed_row)[col] == 0)
                    undeveloped++;
            }
        }
        row += skip_rows;
    }
    Rast_close(fd_developed);
    G_free(developed_row);
    return undeveloped * skip_rows;
}

/*!
 * \brief Initialize arrays for transformation of probability values
 * \param potential_info
 * \param exponent
 */
void initialize_incentive(struct Potential *potential_info, float exponent)
{
    int i;

    potential_info->incentive_transform_size = 1001;
    potential_info->incentive_transform = (float *)G_malloc(
        sizeof(float) * potential_info->incentive_transform_size);
    i = 0;
    double step = 1. / (potential_info->incentive_transform_size - 1);
    while (i < potential_info->incentive_transform_size) {
        potential_info->incentive_transform[i] = pow(i * step, exponent);
        i++;
    }
}

/*!
 * \brief Read input rasters into segments.
 * \param inputs
 * \param segments
 * \param segment_info
 * \param region_map
 */
void read_input_rasters(struct RasterInputs inputs, struct Segments *segments,
                        struct SegmentMemory segment_info,
                        map_int_t *region_map, map_int_t *reverse_region_map,
                        map_int_t *potential_region_map, map_int_t *HUC_map,
                        map_float_t *max_flood_probability_map,
                        map_int_t *DDF_region_map)
{
    int row, col;
    int rows, cols;
    int fd_developed = 0, fd_reg = 0, fd_devpressure = 0, fd_weights = 0,
        fd_zones = 0, fd_pot_reg = 0, fd_density = 0, fd_density_cap = 0,
        fd_HAND = 0, fd_adaptive_capacity = 0, fd_HUC = 0, fd_DDF = 0,
        fd_adaptations = 0;
    int count_regions, pot_count_regions, HUC_count, DDF_count;
    int region_index, pot_region_index, HUC_index, DDF_index;
    int *region_pindex;
    int *pot_region_pindex;
    CELL c;
    FCELL fc;
    bool isnull;
    CELL *developed_row;
    CELL *subregions_row;
    CELL *pot_subregions_row = NULL;
    FCELL *devpressure_row;
    FCELL *weights_row = NULL;
    CELL *zones_row = NULL;
    FCELL *density_row = NULL;
    FCELL *density_capacity_row = NULL;
    FCELL *HAND_row = NULL;
    FCELL *adaptive_capacity_row = NULL;
    CELL *HUC_row = NULL;
    CELL *DDF_row = NULL;
    CELL *adaptation_row = NULL;
    float *pvalue;

    rows = Rast_window_rows();
    cols = Rast_window_cols();
    count_regions = region_index = HUC_count = DDF_count = 0;
    pot_count_regions = pot_region_index = HUC_index = DDF_index = 0;
    int *pindex;

    /* open existing raster maps for reading */
    fd_developed = Rast_open_old(inputs.developed, "");
    fd_reg = Rast_open_old(inputs.regions, "");
    if (segments->use_potential_subregions)
        fd_pot_reg = Rast_open_old(inputs.potential_regions, "");
    fd_devpressure = Rast_open_old(inputs.devpressure, "");
    if (segments->use_weight)
        fd_weights = Rast_open_old(inputs.weights, "");
    if (segments->use_zone)
        fd_zones = Rast_open_old(inputs.zones, "");
    if (segments->use_density) {
        fd_density = Rast_open_old(inputs.density, "");
        fd_density_cap = Rast_open_old(inputs.density_capacity, "");
    }
    if (segments->use_climate) {
        if (inputs.HAND)
            fd_HAND = Rast_open_old(inputs.HAND, "");
        fd_adaptive_capacity = Rast_open_old(inputs.adaptive_capacity, "");
        fd_HUC = Rast_open_old(inputs.HUC, "");
        if (inputs.DDF_regions)
            fd_DDF = Rast_open_old(inputs.DDF_regions, "");
        if (inputs.adaptation)
            fd_adaptations = Rast_open_old(inputs.adaptation, "");
    }

    /* Segment open developed */
    if (Segment_open(&segments->developed, G_tempfile(), rows, cols,
                     segment_info.rows, segment_info.cols,
                     Rast_cell_size(CELL_TYPE), segment_info.in_memory) != 1)
        G_fatal_error(_("Cannot create temporary file with segments of a "
                        "raster map of development"));
    /* Segment open subregions */
    if (Segment_open(&segments->subregions, G_tempfile(), rows, cols,
                     segment_info.rows, segment_info.cols,
                     Rast_cell_size(CELL_TYPE), segment_info.in_memory) != 1)
        G_fatal_error(_("Cannot create temporary file with segments of a "
                        "raster map of subregions"));
    /* Segment open development pressure */
    if (Segment_open(&segments->devpressure, G_tempfile(), rows, cols,
                     segment_info.rows, segment_info.cols,
                     Rast_cell_size(FCELL_TYPE), segment_info.in_memory) != 1)
        G_fatal_error(_("Cannot create temporary file with segments of a "
                        "raster map of development pressure"));
    /* Segment open weights */
    if (segments->use_weight)
        if (Segment_open(&segments->weight, G_tempfile(), rows, cols,
                         segment_info.rows, segment_info.cols,
                         Rast_cell_size(FCELL_TYPE),
                         segment_info.in_memory) != 1)
            G_fatal_error(_("Cannot create temporary file with segments of a "
                            "raster map of weights"));
    /* Segment open zones */
    if (segments->use_zone)
        if (Segment_open(&segments->zone, G_tempfile(), rows, cols,
                         segment_info.rows, segment_info.cols,
                         Rast_cell_size(CELL_TYPE),
                         segment_info.in_memory) != 1)
            G_fatal_error(_("Cannot create temporary file with segments of a "
                            "raster map of zones"));
    /* Segment open potential_subregions */
    if (segments->use_potential_subregions)
        if (Segment_open(&segments->potential_subregions, G_tempfile(), rows,
                         cols, segment_info.rows, segment_info.cols,
                         Rast_cell_size(CELL_TYPE),
                         segment_info.in_memory) != 1)
            G_fatal_error(_("Cannot create temporary file with segments of a "
                            "raster map of subregions"));
    /* Segment open density */
    if (segments->use_density) {
        if (Segment_open(&segments->density, G_tempfile(), rows, cols,
                         segment_info.rows, segment_info.cols,
                         Rast_cell_size(FCELL_TYPE),
                         segment_info.in_memory) != 1)
            G_fatal_error(_("Cannot create temporary file with segments of a "
                            "raster map of density"));
        if (Segment_open(&segments->density_capacity, G_tempfile(), rows, cols,
                         segment_info.rows, segment_info.cols,
                         Rast_cell_size(FCELL_TYPE),
                         segment_info.in_memory) != 1)
            G_fatal_error(_("Cannot create temporary file with segments of a "
                            "raster map of density capacity"));
    }
    /* Segment open HAND */
    if (segments->use_climate) {
        if (inputs.HAND)
            if (Segment_open(&segments->HAND, G_tempfile(), rows, cols,
                             segment_info.rows, segment_info.cols,
                             Rast_cell_size(FCELL_TYPE),
                             segment_info.in_memory) != 1)
                G_fatal_error(_("Cannot create temporary file with segments of "
                                "a raster map of HAND"));
        if (Segment_open(&segments->adaptive_capacity, G_tempfile(), rows, cols,
                         segment_info.rows, segment_info.cols,
                         Rast_cell_size(FCELL_TYPE),
                         segment_info.in_memory) != 1)
            G_fatal_error(_("Cannot create temporary file with segments of a "
                            "raster map of adaptive capacity"));
        if (Segment_open(&segments->HUC, G_tempfile(), rows, cols,
                         segment_info.rows, segment_info.cols,
                         Rast_cell_size(CELL_TYPE),
                         segment_info.in_memory) != 1)
            G_fatal_error(_("Cannot create temporary file with segments of a "
                            "raster map of HUCs"));
        if (inputs.DDF_regions)
            if (Segment_open(&segments->DDF_subregions, G_tempfile(), rows,
                             cols, segment_info.rows, segment_info.cols,
                             Rast_cell_size(CELL_TYPE),
                             segment_info.in_memory) != 1)
                G_fatal_error(_("Cannot create temporary file with segments of "
                                "a raster map of DDF subregions"));
        if (Segment_open(&segments->adaptation, G_tempfile(), rows, cols,
                         segment_info.rows, segment_info.cols,
                         Rast_cell_size(CELL_TYPE),
                         segment_info.in_memory) != 1)
            G_fatal_error(_("Cannot create temporary file with segments of an "
                            "adaptations raster map"));
    }
    developed_row = Rast_allocate_buf(CELL_TYPE);
    subregions_row = Rast_allocate_buf(CELL_TYPE);
    devpressure_row = Rast_allocate_buf(FCELL_TYPE);
    if (segments->use_weight)
        weights_row = Rast_allocate_buf(FCELL_TYPE);
    if (segments->use_zone)
        zones_row = Rast_allocate_buf(CELL_TYPE);
    if (segments->use_potential_subregions)
        pot_subregions_row = Rast_allocate_buf(CELL_TYPE);
    if (segments->use_density) {
        density_row = Rast_allocate_buf(FCELL_TYPE);
        density_capacity_row = Rast_allocate_buf(FCELL_TYPE);
    }
    if (segments->use_climate) {
        if (inputs.HAND)
            HAND_row = Rast_allocate_buf(FCELL_TYPE);
        adaptive_capacity_row = Rast_allocate_buf(FCELL_TYPE);
        HUC_row = Rast_allocate_buf(CELL_TYPE);
        if (inputs.DDF_regions)
            DDF_row = Rast_allocate_buf(CELL_TYPE);
        adaptation_row = Rast_allocate_buf(CELL_TYPE);
    }

    for (row = 0; row < rows; row++) {
        G_percent(row, rows, 5);
        /* read developed row */
        Rast_get_row(fd_developed, developed_row, row, CELL_TYPE);
        Rast_get_row(fd_devpressure, devpressure_row, row, FCELL_TYPE);
        Rast_get_row(fd_reg, subregions_row, row, CELL_TYPE);
        if (segments->use_weight)
            Rast_get_row(fd_weights, weights_row, row, FCELL_TYPE);
        if (segments->use_zone)
            Rast_get_row(fd_zones, zones_row, row, CELL_TYPE);
        if (segments->use_potential_subregions)
            Rast_get_row(fd_pot_reg, pot_subregions_row, row, CELL_TYPE);
        if (segments->use_density) {
            Rast_get_row(fd_density, density_row, row, FCELL_TYPE);
            Rast_get_row(fd_density_cap, density_capacity_row, row, FCELL_TYPE);
        }
        if (segments->use_climate) {
            if (inputs.HAND)
                Rast_get_row(fd_HAND, HAND_row, row, FCELL_TYPE);
            Rast_get_row(fd_adaptive_capacity, adaptive_capacity_row, row,
                         FCELL_TYPE);
            Rast_get_row(fd_HUC, HUC_row, row, CELL_TYPE);
            if (inputs.DDF_regions)
                Rast_get_row(fd_DDF, DDF_row, row, CELL_TYPE);
        }
        for (col = 0; col < cols; col++) {
            isnull = false;
            /* developed */
            /* undeveloped 0 -> -1, developed 1 -> 0 */
            if (!Rast_is_null_value(&((CELL *)developed_row)[col], CELL_TYPE)) {
                c = ((CELL *)developed_row)[col];
                ((CELL *)developed_row)[col] = c - 1;
            }
            else
                isnull = true;
            /* subregions */
            if (!Rast_is_null_value(&((CELL *)subregions_row)[col],
                                    CELL_TYPE)) {
                c = ((CELL *)subregions_row)[col];
                region_pindex = map_get_int(region_map, c);
                if (!region_pindex) {
                    map_set_int(region_map, c, count_regions);
                    map_set_int(reverse_region_map, count_regions, c);
                    region_index = count_regions;
                    count_regions++;
                }
                else
                    region_index = *region_pindex;
                ((CELL *)subregions_row)[col] = region_index;
            }
            else
                isnull = true;
            if (segments->use_potential_subregions) {
                if (!Rast_is_null_value(&((CELL *)pot_subregions_row)[col],
                                        CELL_TYPE)) {
                    c = ((CELL *)pot_subregions_row)[col];
                    pot_region_pindex = map_get_int(potential_region_map, c);
                    if (!pot_region_pindex) {
                        map_set_int(potential_region_map, c, pot_count_regions);
                        pot_region_index = pot_count_regions;
                        pot_count_regions++;
                    }
                    else
                        pot_region_index = *pot_region_pindex;
                    ((CELL *)pot_subregions_row)[col] = pot_region_index;
                }
                else
                    isnull = true;
            }
            /* devpressure - just check nulls */
            if (Rast_is_null_value(&((FCELL *)devpressure_row)[col],
                                   FCELL_TYPE))
                isnull = true;
            /* density - just check nulls */
            if (segments->use_density) {
                if (Rast_is_null_value(&((FCELL *)density_row)[col],
                                       FCELL_TYPE))
                    isnull = true;
                if (Rast_is_null_value(&((FCELL *)density_capacity_row)[col],
                                       FCELL_TYPE))
                    isnull = true;
            }
            /* weights - must be in range -1, 1*/
            if (segments->use_weight) {
                if (Rast_is_null_value(&((FCELL *)weights_row)[col],
                                       FCELL_TYPE)) {
                    ((FCELL *)weights_row)[col] = 0;
                    isnull = true;
                }
                else {
                    fc = ((FCELL *)weights_row)[col];
                    if (fc > 1) {
                        G_warning(
                            _("Probability weights are > 1, truncating..."));
                        fc = 1;
                    }
                    else if (fc < -1) {
                        fc = -1;
                        G_warning(
                            _("Probability weights are < -1, truncating..."));
                    }
                    ((FCELL *)weights_row)[col] = fc;
                }
            }
            if (segments->use_zone) {
                if (Rast_is_null_value(&((CELL *)zones_row)[col], CELL_TYPE)) {
                    ((CELL *)zones_row)[col] = 0;
                }
            }
            /* flooding; run only for cells which will be part of simulation
               to avoid collecting unused hucs/ddfs */
            if (segments->use_climate && !isnull) {
                if (inputs.HAND)
                    if (Rast_is_null_value(&((FCELL *)HAND_row)[col],
                                           FCELL_TYPE))
                        isnull = true;
                if (Rast_is_null_value(&((FCELL *)adaptive_capacity_row)[col],
                                       FCELL_TYPE))
                    isnull = true;
                if (!Rast_is_null_value(&((CELL *)HUC_row)[col], CELL_TYPE)) {
                    c = ((CELL *)HUC_row)[col];
                    /* mapping: HUC id -> index */
                    pindex = map_get_int(HUC_map, c);
                    if (!pindex) {
                        map_set_int(HUC_map, c, HUC_count);
                        HUC_index = HUC_count;
                        HUC_count++;
                    }
                    else
                        HUC_index = *pindex;
                    ((CELL *)HUC_row)[col] = HUC_index;
                    /* init max flood value for each HUC */
                    pvalue = map_get_int(max_flood_probability_map, HUC_index);
                    if (!pvalue)
                        map_set_int(max_flood_probability_map, HUC_index, 0);
                }
                /* DDF subregions */
                if (inputs.DDF_regions) {
                    if (!Rast_is_null_value(&((CELL *)DDF_row)[col],
                                            CELL_TYPE)) {
                        c = ((CELL *)DDF_row)[col];
                        pindex = map_get_int(DDF_region_map, c);
                        if (!pindex) {
                            map_set_int(DDF_region_map, c, DDF_count);
                            DDF_index = DDF_count;
                            DDF_count++;
                        }
                        else
                            DDF_index = *pindex;
                        ((CELL *)DDF_row)[col] = DDF_index;
                    }
                    else
                        isnull = true;
                }
            }
            /* if in developed, subregions, devpressure or weights are any nulls
               propagate them into developed */
            if (isnull)
                Rast_set_c_null_value(&((CELL *)developed_row)[col], 1);
        }
        if (segments->use_climate)
            if (inputs.adaptation)
                Rast_get_row(fd_adaptations, adaptation_row, row, CELL_TYPE);

        Segment_put_row(&segments->developed, developed_row, row);
        Segment_put_row(&segments->devpressure, devpressure_row, row);
        Segment_put_row(&segments->subregions, subregions_row, row);
        if (segments->use_weight)
            Segment_put_row(&segments->weight, weights_row, row);
        if (segments->use_zone)
            Segment_put_row(&segments->zone, zones_row, row);
        if (segments->use_potential_subregions)
            Segment_put_row(&segments->potential_subregions, pot_subregions_row,
                            row);
        if (segments->use_density) {
            Segment_put_row(&segments->density, density_row, row);
            Segment_put_row(&segments->density_capacity, density_capacity_row,
                            row);
        }
        if (segments->use_climate) {
            if (inputs.HAND)
                Segment_put_row(&segments->HAND, HAND_row, row);
            Segment_put_row(&segments->adaptive_capacity, adaptive_capacity_row,
                            row);
            Segment_put_row(&segments->HUC, HUC_row, row);
            if (inputs.DDF_regions)
                Segment_put_row(&segments->DDF_subregions, DDF_row, row);
            Segment_put_row(&segments->adaptation, adaptation_row, row);
        }
    }
    G_percent(row, rows, 5);

    /* flush all segments */
    Segment_flush(&segments->developed);
    Segment_flush(&segments->subregions);
    Segment_flush(&segments->devpressure);
    if (segments->use_weight)
        Segment_flush(&segments->weight);
    if (segments->use_zone)
        Segment_flush(&segments->zone);
    if (segments->use_potential_subregions)
        Segment_flush(&segments->potential_subregions);
    if (segments->use_density) {
        Segment_flush(&segments->density);
        Segment_flush(&segments->density_capacity);
    }
    if (segments->use_climate) {
        if (inputs.HAND)
            Segment_flush(&segments->HAND);
        Segment_flush(&segments->adaptive_capacity);
        Segment_flush(&segments->HUC);
        if (inputs.DDF_regions)
            Segment_flush(&segments->DDF_subregions);
        Segment_flush(&segments->adaptation);
    }
    /* close raster maps */
    Rast_close(fd_developed);
    Rast_close(fd_reg);
    Rast_close(fd_devpressure);
    if (segments->use_weight)
        Rast_close(fd_weights);
    if (segments->use_zone)
        Rast_close(fd_zones);
    if (segments->use_potential_subregions)
        Rast_close(fd_pot_reg);
    if (segments->use_density) {
        Rast_close(fd_density);
        Rast_close(fd_density_cap);
    }
    if (segments->use_climate) {
        if (inputs.HAND)
            Rast_close(fd_HAND);
        Rast_close(fd_adaptive_capacity);
        Rast_close(fd_HUC);
        if (inputs.DDF_regions)
            Rast_close(fd_DDF);
        if (inputs.adaptation)
            Rast_close(fd_adaptations);
    }

    G_free(developed_row);
    G_free(subregions_row);
    G_free(devpressure_row);
    if (segments->use_weight)
        G_free(weights_row);
    if (segments->use_zone)
        G_free(zones_row);
    if (segments->use_potential_subregions)
        G_free(pot_subregions_row);
    if (segments->use_density) {
        G_free(density_row);
        G_free(density_capacity_row);
    }
    if (segments->use_climate) {
        if (inputs.HAND)
            G_free(HAND_row);
        G_free(adaptive_capacity_row);
        G_free(HUC_row);
        if (inputs.DDF_regions)
            G_free(DDF_row);
        G_free(adaptation_row);
    }
}

/*!
 * \brief Reads predictors and aggregates them with Potential table:
 * x_1 * a + x2 * b + ...
 * Saves memory comparing to having them separately.
 *
 * \param inputs Raster inputs
 * \param segments Segments
 * \param potential Potential table
 * \param segment_info Segment memory info
 */
void read_predictors(struct RasterInputs inputs, struct Segments *segments,
                     const struct Potential *potential,
                     const struct SegmentMemory segment_info)
{
    int i;
    int row, col;
    int rows, cols;
    int *fds_predictors;
    int pred_index;
    FCELL value;
    CELL pot_index, dev_value;
    FCELL **predictor_rows;
    FCELL *aggregated_row;

    rows = Rast_window_rows();
    cols = Rast_window_cols();
    fds_predictors = G_malloc(potential->max_predictors * sizeof(int));
    for (i = 0; i < potential->max_predictors; i++) {
        fds_predictors[i] = Rast_open_old(inputs.predictors[i], "");
    }
    predictor_rows = G_malloc(potential->max_predictors * sizeof(FCELL *));
    for (i = 0; i < potential->max_predictors; i++) {
        predictor_rows[i] = Rast_allocate_buf(FCELL_TYPE);
    }
    aggregated_row = Rast_allocate_buf(FCELL_TYPE);

    /* Segment open predictors */
    if (Segment_open(&segments->aggregated_predictor, G_tempfile(), rows, cols,
                     segment_info.rows, segment_info.cols,
                     Rast_cell_size(FCELL_TYPE), segment_info.in_memory) != 1)
        G_fatal_error(_("Cannot create temporary file with segments of "
                        "predictor raster maps"));

    /* read in */
    for (row = 0; row < rows; row++) {
        for (i = 0; i < potential->max_predictors; i++) {
            Rast_get_row(fds_predictors[i], predictor_rows[i], row, FCELL_TYPE);
        }
        for (col = 0; col < cols; col++) {
            ((FCELL *)aggregated_row)[col] = 0;
            Segment_get(&segments->developed, (void *)&dev_value, row, col);
            if (Rast_is_null_value(&dev_value, CELL_TYPE)) {
                continue;
            }
            for (i = 0; i < potential->max_predictors; i++) {
                /* collect all nulls in predictors and set it in output raster
                 */
                if (Rast_is_null_value(&((FCELL *)predictor_rows[i])[col],
                                       FCELL_TYPE)) {
                    Rast_set_c_null_value(&dev_value, 1);
                    Segment_put(&segments->developed, (void *)&dev_value, row,
                                col);
                    break;
                }
                if (segments->use_potential_subregions)
                    Segment_get(&segments->potential_subregions,
                                (void *)&pot_index, row, col);
                else
                    Segment_get(&segments->subregions, (void *)&pot_index, row,
                                col);
                pred_index = potential->predictor_indices[i];
                value = potential->predictors[i][pot_index] *
                        ((FCELL *)predictor_rows[pred_index])[col];
                ((FCELL *)aggregated_row)[col] += value;
            }
        }
        Segment_put_row(&segments->aggregated_predictor, aggregated_row, row);
    }
    Segment_flush(&segments->aggregated_predictor);
    Segment_flush(&segments->developed);
    for (i = 0; i < potential->max_predictors; i++) {
        Rast_close(fds_predictors[i]);
        G_free(predictor_rows[i]);
    }
    G_free(fds_predictors);
    G_free(predictor_rows);
    G_free(aggregated_row);
}

static int _read_demand_file(FILE *fp, const char *separator, float **table,
                             int *demand_years, map_int_t *region_map)
{

    size_t buflen = 4000;
    char buf[buflen];
    // read in the first row (header)
    if (G_getl2(buf, buflen, fp) == 0)
        G_fatal_error(_("Demand file"
                        " contains less than one line"));

    char **tokens;
    unsigned ntokens;

    const char *td = "\"";

    tokens = G_tokenize2(buf, separator, td);
    ntokens = G_number_of_tokens(tokens);
    if (ntokens == 0)
        G_fatal_error("No columns in the header row");

    struct ilist *ids = G_new_ilist();
    int count;
    // skip first column which does not contain id of the region
    unsigned i;
    for (i = 1; i < ntokens; i++) {
        G_chop(tokens[i]);
        G_ilist_add(ids, atoi(tokens[i]));
    }

    int years = 0;
    while (G_getl2(buf, buflen, fp)) {
        if (buf[0] == '\0')
            continue;

        tokens = G_tokenize2(buf, separator, td);
        unsigned ntokens2 = G_number_of_tokens(tokens);
        if (ntokens2 != ntokens)
            G_fatal_error(_("Demand: wrong number of columns in line: %s"),
                          buf);
        if (ntokens - 1 < map_nitems(region_map))
            G_fatal_error(_("Demand: some subregions are missing"));
        count = 0;
        demand_years[years] = atoi(tokens[0]);
        for (unsigned i = 1; i < ntokens; i++) {
            // skip first column which is the year which we ignore
            int *idx = map_get_int(region_map, ids->value[count]);
            if (idx) {
                G_chop(tokens[i]);
                table[*idx][years] = atof(tokens[i]);
            }
            count++;
        }
        // each line is a year
        years++;
    }
    G_free_ilist(ids);
    G_free_tokens(tokens);
    return years;
}

void read_demand_file(struct Demand *demandInfo, map_int_t *region_map)
{
    FILE *fp_cell = NULL, *fp_population = NULL;
    if ((fp_cell = fopen(demandInfo->cells_filename, "r")) == NULL)
        G_fatal_error(_("Cannot open area demand file <%s>"),
                      demandInfo->cells_filename);
    int countlines = 0;
    // Extract characters from file and store in character c
    for (char c = getc(fp_cell); c != EOF; c = getc(fp_cell))
        if (c == '\n') // Increment count if this character is newline
            countlines++;
    rewind(fp_cell);

    if (demandInfo->has_population) {
        if ((fp_population = fopen(demandInfo->population_filename, "r")) ==
            NULL)
            G_fatal_error(_("Cannot open population demand file <%s>"),
                          demandInfo->population_filename);
        int countlines2 = 0;
        for (char c = getc(fp_population); c != EOF; c = getc(fp_population))
            if (c == '\n') // Increment count if this character is newline
                countlines2++;
        if (countlines != countlines2) {
            G_fatal_error(_("Area and population demand files (<%s> and <%s>) "
                            "have different number of lines"),
                          demandInfo->cells_filename,
                          demandInfo->population_filename);
        }
        rewind(fp_population);
    }

    demandInfo->years = (int *)G_malloc(countlines * sizeof(int));
    demandInfo->cells_table =
        (float **)G_malloc(map_nitems(region_map) * sizeof(float *));
    for (unsigned i = 0; i < map_nitems(region_map); i++) {
        demandInfo->cells_table[i] =
            (float *)G_malloc(countlines * sizeof(float));
    }
    int num_years = _read_demand_file(fp_cell, demandInfo->separator,
                                      demandInfo->cells_table,
                                      demandInfo->years, region_map);
    demandInfo->max_subregions = map_nitems(region_map);
    demandInfo->max_steps = num_years;
    G_verbose_message("Number of steps in area demand file: %d", num_years);
    fclose(fp_cell);

    if (demandInfo->has_population) {
        int *years2 = (int *)G_malloc(countlines * sizeof(int));
        demandInfo->population_table =
            (float **)G_malloc(map_nitems(region_map) * sizeof(float *));
        for (unsigned i = 0; i < map_nitems(region_map); i++) {
            demandInfo->population_table[i] =
                (float *)G_malloc(countlines * sizeof(float));
        }
        int num_years2 =
            _read_demand_file(fp_population, demandInfo->separator,
                              demandInfo->population_table, years2, region_map);
        // check files for consistency
        if (num_years != num_years2)
            G_fatal_error(_("Area and population demand files (<%s> and <%s>) "
                            "have different number of years"),
                          demandInfo->cells_filename,
                          demandInfo->population_filename);
        for (int i = 0; i < num_years; i++) {
            if (demandInfo->years[i] != years2[i])
                G_fatal_error(
                    _("Area and population demand files (<%s> and <%s>) "
                      "have different years"),
                    demandInfo->cells_filename,
                    demandInfo->population_filename);
        }
        fclose(fp_population);
        G_free(years2);
    }
}

/**
 * Load "predictor@mapset" and "predictor" to map names with indices.
 * This is used when reading potential file to check column names.
 *
 */
void fill_predictor_map(struct RasterInputs inputs, map_int_t *predictor_map,
                        int num_predictors)
{
    char xname[GNAME_MAX], xmapset[GMAPSET_MAX];
    for (int i = 0; i < num_predictors; i++) {
        if (G_unqualified_name(inputs.predictors[i], "", xname, xmapset))
            map_set(predictor_map, xname, i);
        else
            map_set(predictor_map,
                    G_fully_qualified_name(
                        xname, G_find_raster2(inputs.predictors[i], "")),
                    i);
        map_set(predictor_map, inputs.predictors[i], i);
    }
}

void read_potential_file(struct Potential *potentialInfo, map_int_t *region_map,
                         map_int_t *predictor_map)
{
    FILE *fp;
    if ((fp = fopen(potentialInfo->filename, "r")) == NULL)
        G_fatal_error(
            _("Cannot open development potential parameters file <%s>"),
            potentialInfo->filename);

    const char *td = "\"";
    char **tokens;
    char **header_tokens;
    int header_ntokens;
    int ntokens;
    int i;
    int *pred_idx;

    size_t buflen = 4000;
    char buf[buflen];
    if (G_getl2(buf, buflen, fp) == 0)
        G_fatal_error(_("Development potential parameters file <%s>"
                        " contains less than one line"),
                      potentialInfo->filename);
    header_tokens = G_tokenize2(buf, potentialInfo->separator, td);
    header_ntokens = G_number_of_tokens(header_tokens);
    /* num predictors minus region id, intercept and devpressure */
    int num_predictors = header_ntokens - 3;
    if (num_predictors < 0)
        G_fatal_error(_("Incorrect header in development potential file <%s>"),
                      potentialInfo->filename);
    potentialInfo->max_predictors = num_predictors;
    potentialInfo->intercept =
        (double *)G_malloc(map_nitems(region_map) * sizeof(double));
    potentialInfo->devpressure =
        (double *)G_malloc(map_nitems(region_map) * sizeof(double));
    potentialInfo->predictors =
        (double **)G_malloc(num_predictors * sizeof(double *));
    potentialInfo->predictor_indices =
        (int *)G_malloc(num_predictors * sizeof(int));
    for (i = 0; i < num_predictors; i++) {
        potentialInfo->predictors[i] =
            (double *)G_malloc(map_nitems(region_map) * sizeof(double));
    }
    /* index of used predictors in columns within list of predictors */
    for (i = 0; i < num_predictors; i++) {
        pred_idx = map_get(predictor_map, header_tokens[3 + i]);
        if (pred_idx)
            potentialInfo->predictor_indices[i] = *pred_idx;
        else
            G_fatal_error(
                _("Specified predictor <%s> in development potential file <%s>"
                  " was not provided."),
                header_tokens[3 + i], potentialInfo->filename);
    }
    G_free(header_tokens);

    while (G_getl2(buf, buflen, fp)) {
        if (buf[0] == '\0')
            continue;
        tokens = G_tokenize2(buf, potentialInfo->separator, td);
        ntokens = G_number_of_tokens(tokens);
        if (ntokens == 0)
            continue;
        // id + intercept + devpressure + predictors
        if (ntokens != num_predictors + 3)
            G_fatal_error(_("Potential: wrong number of columns: %s"), buf);

        int *idx;
        int id;
        double coef_intercept, coef_devpressure;
        double val;
        int j;

        G_chop(tokens[0]);
        id = atoi(tokens[0]);
        idx = map_get_int(region_map, id);
        if (idx) {
            G_chop(tokens[1]);
            coef_intercept = atof(tokens[1]);
            G_chop(tokens[2]);
            coef_devpressure = atof(tokens[2]);
            potentialInfo->intercept[*idx] = coef_intercept;
            potentialInfo->devpressure[*idx] = coef_devpressure;
            for (j = 0; j < num_predictors; j++) {
                G_chop(tokens[j + 3]);
                val = atof(tokens[j + 3]);
                potentialInfo->predictors[j][*idx] = val;
            }
        }
        // else ignoring the line with region which is not used

        G_free_tokens(tokens);
    }

    fclose(fp);
}

void read_patch_sizes(struct PatchSizes *patch_sizes, map_int_t *region_map,
                      double discount_factor)
{
    FILE *fp;
    size_t buflen = 4000;
    char buf[buflen];
    int patch;
    char **tokens = NULL;
    char **header_tokens;
    unsigned ntokens;
    unsigned i, j;
    unsigned region_id;
    int *region_pid;
    const char *td = "\"";
    unsigned num_regions = 0;
    bool found;
    bool use_header;
    int n_max_patches;
    const char *key;
    map_iter_t iter;

    n_max_patches = 0;
    patch_sizes->max_patch_size = 0;
    fp = fopen(patch_sizes->filename, "rb");
    if (fp) {
        /* just scan the file twice */
        // scan in the header line
        if (G_getl2(buf, buflen, fp) == 0)
            G_fatal_error(_("Patch library file <%s>"
                            " contains less than one line"),
                          patch_sizes->filename);

        header_tokens = G_tokenize2(buf, ",", td);
        num_regions = G_number_of_tokens(header_tokens);
        use_header = true;
        patch_sizes->single_column = false;
        if (num_regions == 1) {
            use_header = false;
            patch_sizes->single_column = true;
            G_verbose_message(
                _("Only single column detected in patch library file <%s>."
                  " It will be used for all subregions."),
                patch_sizes->filename);
        }
        /* Check there are enough columns for subregions in map */
        if (num_regions != 1 && num_regions < map_nitems(region_map))
            G_fatal_error(_("Patch library file <%s>"
                            " has only %d columns but there are %d subregions"),
                          patch_sizes->filename, num_regions,
                          map_nitems(region_map));
        /* Check all subregions in map have column in the file. */
        if (use_header) {
            iter = map_iter(region_map);
            while ((key = map_next(region_map, &iter))) {
                found = false;
                for (j = 0; j < num_regions; j++)
                    if (strcmp(key, header_tokens[j]) == 0)
                        found = true;
                if (!found)
                    G_fatal_error(_("Subregion id <%s> not found in header of "
                                    "patch file <%s>"),
                                  key, patch_sizes->filename);
            }
        }
        // initialize patch_info->patch_count to all zero
        patch_sizes->patch_count = (int *)G_calloc(num_regions, sizeof(int));
        /* add one for the header reading above */
        if (!use_header)
            n_max_patches++;
        // take one line
        while (G_getl2(buf, buflen, fp)) {
            // process each column in row
            tokens = G_tokenize2(buf, ",", td);
            ntokens = G_number_of_tokens(tokens);
            if (ntokens != num_regions)
                G_fatal_error(_("Patch library file <%s>"
                                " has inconsistent number of columns"),
                              patch_sizes->filename);
            n_max_patches++;
        }
        // in a 2D array
        patch_sizes->patch_sizes =
            (int **)G_malloc(sizeof(int *) * num_regions);
        // malloc appropriate size for each area
        for (i = 0; i < num_regions; i++) {
            patch_sizes->patch_sizes[i] =
                (int *)G_malloc(n_max_patches * sizeof(int));
        }
        /* read first line to skip header */
        rewind(fp);
        if (use_header)
            G_getl2(buf, buflen, fp);

        while (G_getl2(buf, buflen, fp)) {
            tokens = G_tokenize2(buf, ",", td);
            ntokens = G_number_of_tokens(tokens);
            for (i = 0; i < ntokens; i++) {
                if (strcmp(tokens[i], "") != 0) {
                    patch = atoi(tokens[i]) * discount_factor;
                    if (patch > 0) {
                        if (patch_sizes->max_patch_size < patch)
                            patch_sizes->max_patch_size = patch;
                        if (use_header) {
                            region_pid = map_get(region_map, header_tokens[i]);
                            if (region_pid)
                                region_id = *region_pid;
                            else
                                continue;
                        }
                        else
                            region_id = 0;
                        patch_sizes
                            ->patch_sizes[region_id]
                                         [patch_sizes->patch_count[region_id]] =
                            patch;
                        patch_sizes->patch_count[region_id]++;
                    }
                }
            }
        }
        G_free_tokens(header_tokens);
        G_free_tokens(tokens);
        fclose(fp);
    }
    /* ensure there is at least one patch in each region (of size 1) */
    for (region_id = 0; region_id < num_regions; region_id++) {
        if (patch_sizes->patch_count[region_id] == 0) {
            patch_sizes->patch_sizes[region_id][0] = 1;
            patch_sizes->patch_count[region_id]++;
        }
    }
}
/**
 * @brief Read file with Depth-Damage functions
 * Header includes inundation levels in vertical units
 * (typically meters/feet), first column is id of the region
 * and values are percentages of structural damage.
 *
 * ID,0.3,0.6,0.9
 * 101,0,15,20
 * 102,10,20,30
 * ...
 * @param ddf structure
 * @param DDF_region_map
 */
void read_DDF_file(struct DepthDamageFunctions *ddf, map_int_t *DDF_region_map)
{
    FILE *fp;
    if ((fp = fopen(ddf->filename, "r")) == NULL)
        G_fatal_error(_("Cannot open file <%s> with depth-damage functions"),
                      ddf->filename);

    const char *td = "\"";
    char **tokens;
    char **header_tokens;
    int header_ntokens;
    int ntokens;
    int i;
    int num_levels;
    int *pidx;
    char *id;
    double val;
    int j;
    int nitems;
    size_t buflen = 4000;
    char buf[buflen];
    if (G_getl2(buf, buflen, fp) == 0)
        G_fatal_error(_("Depth-damage functions file <%s>"
                        " contains less than one line"),
                      ddf->filename);
    header_tokens = G_tokenize2(buf, ddf->separator, td);
    header_ntokens = G_number_of_tokens(header_tokens);
    num_levels = header_ntokens - 1;
    if (num_levels < 0)
        G_fatal_error(_("Incorrect header in depth-damage functions file <%s>"),
                      ddf->filename);
    nitems = map_nitems(DDF_region_map);

    ddf->max_levels = num_levels;
    ddf->max_subregions = nitems;
    ddf->levels = (double *)G_malloc(num_levels * sizeof(double));
    ddf->damage = (double **)G_calloc(nitems, sizeof(double *));
    ddf->loaded = (bool *)G_malloc(nitems * sizeof(bool));
    for (i = 0; i < nitems; i++) {
        ddf->damage[i] = (double *)G_malloc(num_levels * sizeof(double));
        ddf->loaded[i] = false;
    }
    /* read inundation levels */
    for (i = 0; i < num_levels; i++) {
        ddf->levels[i] = atof(header_tokens[i + 1]);
    }

    while (G_getl2(buf, buflen, fp)) {
        if (buf[0] == '\0')
            continue;
        tokens = G_tokenize2(buf, ddf->separator, td);
        ntokens = G_number_of_tokens(tokens);
        if (ntokens == 0)
            continue;
        if (ntokens != num_levels + 1)
            G_fatal_error(_("DDF: wrong number of columns: %s"), buf);

        G_chop(tokens[0]);
        id = tokens[0];
        pidx = map_get(DDF_region_map, id);
        if (pidx) {
            for (j = 0; j < num_levels; j++) {
                G_chop(tokens[j + 1]);
                val = atof(tokens[j + 1]);
                ddf->damage[*pidx][j] = val;
            }
            ddf->loaded[*pidx] = true;
        }
        // else ignoring the line with region which is not used

        G_free_tokens(tokens);
    }
    for (i = 0; i < ddf->max_subregions; i++) {
        if (!ddf->loaded[i])
            G_fatal_error(_("DDF: not all subregions have associated DDF"));
    }

    fclose(fp);
}

/**
 * Create bounding boxes for all categories in a raster.
 * @param raster CELL map as segment
 * @param masking CELL raster map as segment containing nulls
 * @param bboxes
 */
void create_bboxes(SEGMENT *raster, SEGMENT *masking, struct BBoxes *bboxes)
{
    int rows, cols;
    int row, col;
    CELL cat;
    int *index;

    rows = Rast_window_rows();
    cols = Rast_window_cols();
    map_init(&bboxes->map);
    bboxes->max_bbox = 100;
    bboxes->n_bbox = 0;
    bboxes->bbox =
        (struct BBox *)G_malloc(bboxes->max_bbox * sizeof(struct BBox));
    for (row = 0; row < rows; row++)
        for (col = 0; col < cols; col++) {
            Segment_get(masking, (void *)&cat, row, col);
            if (Rast_is_null_value(&cat, CELL_TYPE))
                continue;
            Segment_get(raster, (void *)&cat, row, col);
            index = map_get_int(&bboxes->map, cat);
            if (index) {
                if (bboxes->bbox[*index].e < col)
                    bboxes->bbox[*index].e = col;
                if (bboxes->bbox[*index].w > col)
                    bboxes->bbox[*index].w = col;
                if (bboxes->bbox[*index].n > row)
                    bboxes->bbox[*index].n = row;
                if (bboxes->bbox[*index].s < row)
                    bboxes->bbox[*index].s = row;
            }
            else {
                if (bboxes->n_bbox == bboxes->max_bbox) {
                    bboxes->max_bbox *= 2;
                    bboxes->bbox = (struct BBox *)G_realloc(
                        bboxes->bbox, bboxes->max_bbox * sizeof(struct BBox));
                }
                /* HUC idx -> bbox idx */
                map_set_int(&bboxes->map, cat, bboxes->n_bbox);
                bboxes->bbox[bboxes->n_bbox].e = col;
                bboxes->bbox[bboxes->n_bbox].w = col;
                bboxes->bbox[bboxes->n_bbox].s = row;
                bboxes->bbox[bboxes->n_bbox].n = row;
                bboxes->n_bbox++;
            }
        }
}

void update_flood_probability(int step, const struct FloodInputs *flood_inputs,
                              struct Segments *segments, map_int_t *HUC_map,
                              map_float_t *max_flood_probability_map)
{
    int i;
    int row, col;
    int fd_flood_probability = 0;
    FCELL *flood_probability_row;
    FCELL fc;
    float *pvalue;
    float max_flood_probability;
    int HUC_index;
    map_iter_t iter;
    const char *key;
    bool found;

    /* Is step in input file at all? */
    found = false;
    for (i = 0; i < flood_inputs->num_steps; i++) {
        if (step == flood_inputs->steps[i]) {
            found = true;
            break;
        }
    }
    if (!found)
        return;
    // zero all values in HUC->max_flood map
    iter = map_iter(max_flood_probability_map);
    while ((key = map_next(max_flood_probability_map, &iter)))
        map_set(max_flood_probability_map, key, 0);

    for (i = 0; i < flood_inputs->size; i++)
        if (flood_inputs->array[i].step == step) {
            fd_flood_probability =
                Rast_open_old(flood_inputs->array[i].map, "");
            G_verbose_message("Loading flood probability raster %s",
                              flood_inputs->array[i].map);
            break;
        }

    flood_probability_row = Rast_allocate_buf(FCELL_TYPE);
    for (row = 0; row < Rast_window_rows(); row++) {
        Rast_get_row(fd_flood_probability, flood_probability_row, row,
                     FCELL_TYPE);
        for (col = 0; col < Rast_window_cols(); col++) {
            if (!Rast_is_null_value(&((FCELL *)flood_probability_row)[col],
                                    FCELL_TYPE)) {
                Segment_get(&segments->HUC, (void *)&HUC_index, row, col);
                fc = ((FCELL *)flood_probability_row)[col];
                pvalue = map_get_int(max_flood_probability_map, HUC_index);
                if (pvalue) {
                    max_flood_probability = *pvalue;
                    if (fc > max_flood_probability)
                        map_set_int(max_flood_probability_map, HUC_index, fc);
                }
                else
                    map_set_int(max_flood_probability_map, HUC_index, fc);
            }
        }
        Segment_put_row(&segments->flood_probability, flood_probability_row,
                        row);
    }
    Segment_flush(&segments->flood_probability);
    G_free(flood_probability_row);
}

void read_flood_file(struct FloodInputs *flood_inputs)
{
    FILE *fp;
    if ((fp = fopen(flood_inputs->filename, "r")) == NULL)
        G_fatal_error(_("Cannot open file <%s> with flood inputs"),
                      flood_inputs->filename);

    const char *td = "\"";
    char **tokens;
    char **header_tokens;
    int header_ntokens;
    int ntokens;
    int i;
    int j;
    size_t buflen = 1000;
    char buf[buflen];
    bool found;

    if (G_getl2(buf, buflen, fp) == 0)
        G_fatal_error(_("Flood inputs file <%s>"
                        " contains less than one line"),
                      flood_inputs->filename);
    header_tokens = G_tokenize2(buf, flood_inputs->separator, td);
    header_ntokens = G_number_of_tokens(header_tokens);
    if (header_ntokens == 3)
        flood_inputs->depth = true;
    else if (header_ntokens == 2)
        flood_inputs->depth = false;
    else
        G_fatal_error(
            _("Incorrect number of columns (%d) detected in file <%s>"),
            header_ntokens, flood_inputs->filename);
    /* read to get length and checks */
    i = 0;
    while (G_getl2(buf, buflen, fp)) {
        // process each column in row
        tokens = G_tokenize2(buf, flood_inputs->separator, td);
        ntokens = G_number_of_tokens(tokens);
        if (ntokens != header_ntokens)
            G_fatal_error(_("Flood input file <%s>"
                            " has inconsistent number of columns"),
                          flood_inputs->filename);
        i++;
    }
    flood_inputs->array =
        (struct FloodInput *)G_malloc(sizeof(struct FloodInput) * i);
    flood_inputs->return_periods = G_calloc(i, sizeof(float));
    flood_inputs->steps = G_calloc(i, sizeof(int));
    i = 0;
    rewind(fp);
    /* skip header */
    G_getl2(buf, buflen, fp);
    while (G_getl2(buf, buflen, fp)) {
        if (buf[0] == '\0')
            continue;
        tokens = G_tokenize2(buf, flood_inputs->separator, td);
        ntokens = G_number_of_tokens(tokens);

        flood_inputs->array[i].step = atoi(G_chop(tokens[0])) - 1;
        if (flood_inputs->depth) {
            flood_inputs->array[i].return_period = atof(G_chop(tokens[1]));
            flood_inputs->array[i].map = G_store(G_chop(tokens[2]));
        }
        else
            flood_inputs->array[i].map = G_store(G_chop(tokens[1]));
        i++;
        G_free_tokens(tokens);
    }
    flood_inputs->size = i;
    flood_inputs->num_steps = 0;
    for (i = 0; i < flood_inputs->size; i++) {
        found = false;
        for (j = 0; j < flood_inputs->num_steps; j++) {
            if (flood_inputs->array[i].step == flood_inputs->steps[j]) {
                found = true;
                break;
            }
        }
        if (!found) {
            flood_inputs->steps[flood_inputs->num_steps] =
                flood_inputs->array[i].step;
            flood_inputs->num_steps++;
        }
    }
    qsort(flood_inputs->steps, flood_inputs->num_steps, sizeof(int), int_cmp);

    if (flood_inputs->depth) {
        flood_inputs->return_periods[0] = flood_inputs->array[0].return_period;
        flood_inputs->num_return_periods = 1;
        for (i = 1; i < flood_inputs->size; i++) {
            found = false;
            for (j = 0; j < flood_inputs->num_return_periods; j++) {
                if (flood_inputs->array[i].return_period ==
                    flood_inputs->return_periods[j]) {
                    found = true;
                    break;
                }
            }
            if (!found) {
                flood_inputs->return_periods[flood_inputs->num_return_periods] =
                    flood_inputs->array[i].return_period;
                flood_inputs->num_return_periods++;
            }
        }
        qsort(flood_inputs->return_periods, flood_inputs->num_return_periods,
              sizeof(float), float_cmp);
    }
    G_free_tokens(header_tokens);
    fclose(fp);
}

void init_flood_segment(const struct FloodInputs *flood_inputs,
                        struct Segments *segments,
                        struct SegmentMemory segment_info)
{
    int rows, cols;
    size_t flood_depths_segment_cell_size;
    rows = Rast_window_rows();
    cols = Rast_window_cols();
    if (flood_inputs->depth) {
        flood_depths_segment_cell_size =
            sizeof(FCELL) * flood_inputs->num_return_periods;
        if (Segment_open(&segments->flood_depths, G_tempfile(), rows, cols,
                         segment_info.rows, segment_info.cols,
                         flood_depths_segment_cell_size,
                         segment_info.in_memory) != 1)
            G_fatal_error(_("Cannot create temporary file with segments of "
                            "flood depth raster maps"));
    }
    else {
        if (Segment_open(&segments->flood_probability, G_tempfile(), rows, cols,
                         segment_info.rows, segment_info.cols,
                         Rast_cell_size(FCELL_TYPE),
                         segment_info.in_memory) != 1)
            G_fatal_error(_("Cannot create temporary file with segments of "
                            "flood probability raster maps"));
    }
}

void update_flood_depth(int step, const struct FloodInputs *flood_inputs,
                        struct Segments *segments,
                        map_float_t *max_flood_probability_map)
{
    int i;
    int rp;
    int row, col;
    int rows, cols;
    FCELL *flood_depths_row;
    FCELL *flood_depths_seg_row;
    int *fds_flood_depths;
    float max_rp;
    map_iter_t iter;
    const char *key;
    rows = Rast_window_rows();
    cols = Rast_window_cols();
    fds_flood_depths = G_malloc(flood_inputs->num_return_periods * sizeof(int));
    rp = 0;
    i = 0;
    bool found;

    /* Is step in input file at all? */
    found = false;
    for (i = 0; i < flood_inputs->num_steps; i++) {
        if (step == flood_inputs->steps[i]) {
            found = true;
            break;
        }
    }
    if (!found)
        return;

    while (rp < flood_inputs->num_return_periods) {
        if (flood_inputs->array[i].step == step &&
            flood_inputs->array[i].return_period ==
                flood_inputs->return_periods[rp]) {
            fds_flood_depths[rp] =
                Rast_open_old(flood_inputs->array[i].map, "");
            G_verbose_message("Loading flood depth raster %s",
                              flood_inputs->array[i].map);
            rp++;
        }
        if (++i >= flood_inputs->size)
            i = 0;
    }
    flood_depths_row = Rast_allocate_buf(FCELL_TYPE);
    flood_depths_seg_row =
        G_malloc(cols * flood_inputs->num_return_periods * sizeof(FCELL));
    for (row = 0; row < rows; row++) {
        for (rp = 0; rp < flood_inputs->num_return_periods; rp++) {
            Rast_get_row(fds_flood_depths[rp], flood_depths_row, row,
                         FCELL_TYPE);
            for (col = 0; col < cols; col++)
                flood_depths_seg_row[col * flood_inputs->num_return_periods +
                                     rp] = flood_depths_row[col];
        }
        Segment_put_row(&segments->flood_depths, flood_depths_seg_row, row);
    }
    Segment_flush(&segments->flood_depths);
    for (rp = 0; rp < flood_inputs->num_return_periods; rp++)
        Rast_close(fds_flood_depths[rp]);
    G_free(fds_flood_depths);
    G_free(flood_depths_row);
    G_free(flood_depths_seg_row);
    // set values in HUC->max_flood map to max return period
    max_rp = 0;
    for (rp = 0; rp < flood_inputs->num_return_periods; rp++)
        if (flood_inputs->return_periods[rp] > max_rp)
            max_rp = flood_inputs->return_periods[rp];
    iter = map_iter(max_flood_probability_map);
    while ((key = map_next(max_flood_probability_map, &iter)))
        map_set(max_flood_probability_map, key, max_rp);
}

void initialize_zoning_effects(struct ZoningEffects *zoning_effects)
{
    zoning_effects->num_zones = 14;
    zoning_effects->num_regions = 0;
    zoning_effects->zones = (struct Zone *)G_malloc(sizeof(struct Zone) *
                                                    zoning_effects->num_zones);
    zoning_effects->zones[0].id = 100; // Residential High Density
    zoning_effects->zones[0].effect = 0;
    zoning_effects->zones[1].id = 101; // Residential Medium-High Density
    zoning_effects->zones[1].effect = -0.124;
    zoning_effects->zones[2].id = 110; // Residential Medium Density
    zoning_effects->zones[2].effect = -0.440;
    zoning_effects->zones[3].id = 120; // Residential Medium-Low Density
    zoning_effects->zones[3].effect = -0.656;
    zoning_effects->zones[4].id = 130; // Residential Low Density
    zoning_effects->zones[4].effect = -0.78;
    zoning_effects->zones[5].id = 131; // Residential Rural and Agricultural
    zoning_effects->zones[5].effect = -0.79;
    zoning_effects->zones[6].id = 200; // Commercial
    zoning_effects->zones[6].effect = -0.157;
    zoning_effects->zones[7].id = 201; // Industrial
    zoning_effects->zones[7].effect = -0.026;
    zoning_effects->zones[8].id = 202; // Office and Institutional
    zoning_effects->zones[8].effect = -0.127;
    zoning_effects->zones[9].id = 203; // Parks and Recreation
    zoning_effects->zones[9].effect = -0.817;
    zoning_effects->zones[10].id = 300; // Mixed Use
    zoning_effects->zones[10].effect = -0.105;
    zoning_effects->zones[11].id = 301; // Planned Use
    zoning_effects->zones[11].effect = 0.115;
    zoning_effects->zones[12].id = 302; // Downtown
    zoning_effects->zones[12].effect = -1;
    zoning_effects->zones[13].id = 0; // null value, no effect
    zoning_effects->zones[13].effect = 0;
}

void read_zoning_file(struct ZoningEffects *zoning_effects,
                      map_int_t *region_map)
{
    if (zoning_effects->user_effects) {
        FILE *fp;
        if ((fp = fopen(zoning_effects->filename, "r")) == NULL)
            G_fatal_error(_("Cannot open zone effects file <%s>"),
                          zoning_effects->filename);

        const char *td = "\"";
        char **tokens;
        char **header_tokens;
        int header_ntokens;
        int ntokens;

        size_t buflen = 4000;
        char buf[buflen];
        if (G_getl2(buf, buflen, fp) == 0)
            G_fatal_error(_("Zone effects file <%s>"
                            " contains less than one line"),
                          zoning_effects->filename);
        header_tokens = G_tokenize2(buf, zoning_effects->separator, td);
        header_ntokens = G_number_of_tokens(header_tokens);
        /* number of zones is number of headers minus 2 (region ID and
         * stringency) */
        int num_zones = header_ntokens - 2;
        /* TODO could add a check here against the number of unique zones in
         * zoning file*/
        if (header_ntokens < 2)
            G_fatal_error(_("Incorrect header in zone effects file <%s>"),
                          zoning_effects->filename);
        zoning_effects->num_zones = num_zones;
        zoning_effects->stringency =
            (float *)G_malloc(map_nitems(region_map) * sizeof(float));
        /* If no zones are passed to file, set to default */
        if (num_zones == 0) {
            initialize_zoning_effects(zoning_effects);
        }
        else {
            zoning_effects->num_regions = map_nitems(region_map);
            zoning_effects->zones = (struct Zone *)G_malloc(
                num_zones * zoning_effects->num_regions * sizeof(struct Zone));
        }
        int zone_counter = 0;
        int stringency_counter = 0;
        int region_counter = 0;
        while (G_getl2(buf, buflen, fp)) {
            if (buf[0] == '\0')
                continue;
            tokens = G_tokenize2(buf, zoning_effects->separator, td);
            ntokens = G_number_of_tokens(tokens);
            if (ntokens < 2)
                G_fatal_error(_("Wrong number of columns (%s) in zone effects "
                                "file, should be at least 2"),
                              buf);

            int *idx;
            int region;
            float stringency;
            int j;
            double val;
            int zone_id;

            G_chop(tokens[0]);
            region = atoi(tokens[0]);
            idx = map_get_int(region_map, region);
            if (idx) {
                region_counter++;
                G_chop(tokens[1]);
                stringency = atof(tokens[1]);
                if (stringency <= 0 || stringency >= 2) {
                    G_fatal_error(_("Zoning stringency must be a value between "
                                    "0 and 2 not including 0 or 2 (region %d, "
                                    "index %d, stringency %.2f). If you do not "
                                    "wish to assign stringency, set to 1"),
                                  region, *idx, stringency);
                }
                if (stringency == 1)
                    stringency_counter++;
                zoning_effects->stringency[*idx] = stringency;
                G_verbose_message("region %d, index %d, stringency %.2f",
                                  region, *idx,
                                  zoning_effects->stringency[*idx]);
                /* If zones are included in file, set zones per region */
                if (num_zones > 0) {
                    for (j = 2; j < num_zones + 2; j++) {
                        G_chop(tokens[j]);
                        G_chop(header_tokens[j]);
                        val = atof(tokens[j]);
                        if (val < -1 || val > 1) {
                            G_fatal_error(
                                _("Zoning effect must be a value between -1 "
                                  "and 1 (region %d, index %d, zoning effect "
                                  "%.2f). If you do not wish to assign a zone "
                                  "effect, set to 0"),
                                region, *idx, val);
                        }
                        zone_id = atoi(header_tokens[j]);
                        zoning_effects->zones[zone_counter].region = *idx;
                        zoning_effects->zones[zone_counter].id = zone_id;
                        zoning_effects->zones[zone_counter].effect = val;
                        zone_counter++;
                    }
                }
            }

            // else ignoring the line with region which is not used
            G_free_tokens(tokens);
        }
        if (region_counter != map_nitems(region_map)) {
            G_fatal_error(_("Incorrect number of regions provided in zoning "
                            "effects file (%d, instead of %d)."),
                          region_counter, map_nitems(region_map));
        }
        if (stringency_counter == map_nitems(region_map))
            zoning_effects->user_effects = false;

        fclose(fp);
    }
    else {
        initialize_zoning_effects(zoning_effects);
    }
}

float zone_to_effect(struct ZoningEffects *zoning_effects, int id,
                     int region_idx)
{
    int num_zones = zoning_effects->num_zones;
    int num_regions = zoning_effects->num_regions;
    if (num_regions > 0) {
        // This could be optimized with hash map or 2D array
        for (int i = 0; i < (num_zones * num_regions); i++) {
            if ((zoning_effects->zones[i].id == id) &&
                (zoning_effects->zones[i].region == region_idx)) {
                return zoning_effects->zones[i].effect;
            }
        }
        G_fatal_error(_("No zoning effect found for zone id %d in region index "
                        "%d. Values in zoning raster (zoning IDs) must be one "
                        "of the predefined IDs (see documentation) or must be "
                        "provided in zoning_effects file."),
                      id, region_idx);
    }
    else {
        for (int i = 0; i < num_zones; i++) {
            if (zoning_effects->zones[i].id == id) {
                return zoning_effects->zones[i].effect;
            }
        }
        G_fatal_error(
            _("No zoning effect found for zone id %d. Values in zoning raster "
              "(zoning IDs) must be one of the predefined IDs (see "
              "documentation) or must be provided in zoning_effects file."),
            id);
    }
    return 0;
}
