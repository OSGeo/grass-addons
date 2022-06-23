/*!
   \file simulation.c

   \brief Higher-level functions simulating urban growth

   (C) 2016-2019 by Anna Petrasova, Vaclav Petras and the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2).  Read the file COPYING that comes with GRASS for details.

   \author Anna Petrasova
   \author Vaclav Petras
 */

#include <stdlib.h>
#include <stdbool.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/segment.h>

#include "inputs.h"
#include "devpressure.h"
#include "utils.h"
#include "simulation.h"
#include "output.h"

/*!
 * \brief Find a seed cell based on cumulative probability.
 *
 * Cumulative probability increases chances to pick cells
 * with higher probability, because the intervals are longer
 * and therefore more likely to be picked by a random number
 * from uniform distribution.
 *
 * \param[in] undev_cells array of undeveloped cells
 * \param[in] region region index
 * \return index in undev_cells (that's not cell id)
 */
int find_probable_seed(struct Undeveloped *undev_cells, int region)
{
    int first, last, middle;
    double p;

    p = G_drand48();
    // bisect
    first = 0;
    last = undev_cells->num[region] - 1;
    middle = (first + last) / 2;
    if (p <= undev_cells->cells[region][first].cumulative_probability)
        return 0;
    if (p >= undev_cells->cells[region][last].cumulative_probability)
        return last;
    while (first <= last) {
        if (undev_cells->cells[region][middle].cumulative_probability < p)
            first = middle + 1;
        else if (undev_cells->cells[region][middle - 1].cumulative_probability < p &&
                 undev_cells->cells[region][middle].cumulative_probability >= p) {
            return middle;
        }
        else
            last = middle - 1;
        middle = (first + last)/2;
    }
    // TODO: returning at least something but should be something more meaningful
    return 0;
}

/*!
 * \brief Get seed for growing a patch.
 * \param[in] undev_cells array for undeveloped cells
 * \param[in] region_idx region index
 * \param[in] method method to pick seed (RANDOM, PROBABILITY)
 * \param[out] row row
 * \param[out] col column
 * \return index in undev_cells (not id of a cell)
 */
int get_seed(struct Undeveloped *undev_cells, int region_idx, enum seed_search method,
              int *row, int *col)
{
    int i, id;
    if (method == RANDOM)
        i = (int)(G_drand48() * undev_cells->num[region_idx]);
    else
        i = find_probable_seed(undev_cells, region_idx);
    id = undev_cells->cells[region_idx][i].id;
    get_xy_from_idx(id, Rast_window_cols(), row, col);
    return i;
}


/*!
 * \brief Compute development probability for a cell
 * \param[in] segments segments
 * \param[in] values allocated buffer
 * \param[in] potential_info potential parameters
 * \param[in] region_index region id
 * \param[in] row row
 * \param[in] col column
 * \return probability
 */
double get_develop_probability_xy(struct Segments *segments,
                                  FCELL *values,
                                  struct Potential *potential_info,
                                  int region_index, int row, int col)
{
    float probability;
    int transformed_idx = 0;
    FCELL devpressure_val;
    FCELL predictors_val;
    FCELL weight;
    CELL pot_index;

    Segment_get(&segments->devpressure, (void *)&devpressure_val, row, col);
    Segment_get(&segments->aggregated_predictor, (void *)&predictors_val, row, col);
    if (segments->use_potential_subregions)
        Segment_get(&segments->potential_subregions, (void *)&pot_index, row, col);
    else
        pot_index = region_index;
    
    probability = potential_info->intercept[pot_index];
    probability += potential_info->devpressure[pot_index] * devpressure_val;
    /* Aggregated value of all static predictors */
    probability += predictors_val;
    probability = 1.0 / (1.0 + exp(-probability));
    if (potential_info->incentive_transform) {
        transformed_idx = (int) (probability * (potential_info->incentive_transform_size - 1));
        if (transformed_idx >= potential_info->incentive_transform_size || transformed_idx < 0)
            G_fatal_error("lookup position (%d) out of range [0, %d]",
                          transformed_idx, potential_info->incentive_transform_size - 1);
        probability = potential_info->incentive_transform[transformed_idx];
    }
    
    /* weights if applicable */
    if (segments->use_weight) {
        Segment_get(&segments->weight, (void *)&weight, row, col);
        if (weight < 0)
            probability *= 1 - fabs(weight);
        else if (weight > 0)
            probability = probability + weight - probability * weight;
    }
    return probability;
}

/*!
 * \brief Recompute development probabilities.
 *
 * Compute probabilities for each cell and update
 * probability segment and undev_cells.
 * Also recompute cumulative probability
 *
 * \param undeveloped_cells array of undeveloped cells
 * \param segments segments
 * \param potential_info potential parameters
 */
void recompute_probabilities(struct Undeveloped *undeveloped_cells,
                             struct Segments *segments,
                             struct Potential *potential_info)
{
    int row, col, cols, rows;
    int id, i, idx, new_size;
    int region_idx;
    CELL developed;
    CELL region;
    FCELL *values;
    float probability;
    float sum;
    
    cols = Rast_window_cols();
    rows = Rast_window_rows();
    values = G_malloc(potential_info->max_predictors * sizeof(FCELL *));
    
    for (region_idx = 0; region_idx < undeveloped_cells->max_subregions; region_idx++) {
        undeveloped_cells->num[region_idx] = 0;
    }
    for (row = 0; row < rows; row++) {
        for (col = 0; col < cols; col++) {
            Segment_get(&segments->developed, (void *)&developed, row, col);
            if (Rast_is_null_value(&developed, CELL_TYPE))
                continue;
            if (developed != -1)
                continue;
            Segment_get(&segments->subregions, (void *)&region, row, col);
            
            /* realloc if needed */
            if (undeveloped_cells->num[region] >= undeveloped_cells->max[region]) {
                new_size = 1.25 * undeveloped_cells->max[region];
                undeveloped_cells->cells[region] = 
                        (struct UndevelopedCell *) G_realloc(undeveloped_cells->cells[region],
                                                             new_size * sizeof(struct UndevelopedCell));
                undeveloped_cells->max[region] = new_size;
            }
            id = get_idx_from_xy(row, col, cols);
            idx = undeveloped_cells->num[region];
            undeveloped_cells->cells[region][idx].id = id;
            undeveloped_cells->cells[region][idx].tried = 0;
            /* get probability and update undevs and segment*/
            probability = get_develop_probability_xy(segments, values,
                                                     potential_info, region, row, col);
            Segment_put(&segments->probability, (void *)&probability, row, col);
            undeveloped_cells->cells[region][idx].probability = probability;
            
            undeveloped_cells->num[region]++;
            
        }
    }
    Segment_flush(&segments->probability);

    i = 0;
    for (region_idx = 0; region_idx < undeveloped_cells->max_subregions; region_idx++) {
        probability = undeveloped_cells->cells[region_idx][0].probability;
        undeveloped_cells->cells[region_idx][0].cumulative_probability = probability;
        for (i = 1; i < undeveloped_cells->num[region_idx]; i++) {
            probability = undeveloped_cells->cells[region_idx][i].probability;
            undeveloped_cells->cells[region_idx][i].cumulative_probability = 
                    undeveloped_cells->cells[region_idx][i - 1].cumulative_probability + probability;
        }
        sum = undeveloped_cells->cells[region_idx][i - 1].cumulative_probability;
        for (i = 0; i < undeveloped_cells->num[region_idx]; i++) {
            undeveloped_cells->cells[region_idx][i].cumulative_probability /= sum;
        }
    }
}
/*!
 * \brief Compute step of the simulation
 *
 * Note: The specified number of cells to grow will be respected
 * but the final number may be slightly different because the end-year
 * balance for the final year is not accounted for. We allow to grow patches
 * outside of currently processed region and we account for the number of cells
 * of the patch grown inside and outside of the region.
 *
 * \param undev_cells array of undeveloped cells
 * \param demand Demand parameters
 * \param search_alg seed search method
 * \param segments segments
 * \param patch_sizes list of patch sizes to pick from
 * \param patch_info patch parameters
 * \param devpressure_info development presure parameters
 * \param patch_overflow overflow of cells to next step
 * \param step step number
 * \param region region index
 * \param overgrow allow patches to grow bigger than demand allows
 */
void compute_step(struct Undeveloped *undev_cells, struct Demand *demand,
                  enum seed_search search_alg,
                  struct Segments *segments,
                  struct PatchSizes *patch_sizes, struct PatchInfo *patch_info,
                  struct DevPressure *devpressure_info, int *patch_overflow,
                  int step, int region, struct KeyValueIntInt *reverse_region_map,
                  bool overgrow)
{
    int i, idx;
    int region_id;
    int n_to_convert;
    int n_done;
    int found;
    int seed_row, seed_col;
    int row, col;
    int patch_size;
    int *added_ids;
    bool force_convert_all;
    int extra;
    bool allow_already_tried_ones;
    int unsuccessful_tries;
    FCELL prob;
    CELL developed;


    added_ids = (int *) G_malloc(sizeof(int) * patch_sizes->max_patch_size);
    n_to_convert = demand->table[region][step];
    n_done = 0;
    force_convert_all = false;
    allow_already_tried_ones = false;
    unsuccessful_tries = 0;
    extra = patch_overflow[region];

    if (extra > 0) {
        if (n_to_convert - extra > 0) {
            n_to_convert -= extra;
            extra = 0;
        }
        else {
            extra -= n_to_convert;
            n_to_convert = 0;
        }
    }

    KeyValueIntInt_find(reverse_region_map, region, &region_id);
    if (n_to_convert >= undev_cells->num[region]) {
        G_warning("Not enough undeveloped cells in region %d (requested: %d,"
                  " available: %ld). Converting all available.",
                  region_id, n_to_convert, undev_cells->num[region]);
        n_to_convert = undev_cells->num[region];
        force_convert_all = true;
    }
    
    while (n_done < n_to_convert) {
        /* too many failed attempts, can't develop here any more */
        if (unsuccessful_tries > MAX_TRIES_ITER) {
            G_warning("Too many failed attempts to find a seed for region %d, "
                      "won't be able to develop %d cells.",
                      region_id, n_to_convert - n_done);
            break;
        }

        /* if we can't find a seed, turn off the restriction to use only untried ones */
        if (!allow_already_tried_ones && unsuccessful_tries > MAX_SEED_ITER * n_to_convert)
            allow_already_tried_ones = true;

        /* get seed's row, col and index in undev cells array */
        idx = get_seed(undev_cells, region, search_alg, &seed_row, &seed_col);
        /* skip if seed was already tried unless we switched of this check because we can't get any seed */
        if (!allow_already_tried_ones && undev_cells->cells[region][idx].tried) {
            unsuccessful_tries++;
            continue;
        }
        /* mark as tried */
        undev_cells->cells[region][idx].tried = 1;
        /* see if seed was already developed during this time step */
        Segment_get(&segments->developed, (void *)&developed, seed_row, seed_col);
        if (developed != -1) {
            unsuccessful_tries++;
            continue;
        }
        /* get probability */
        Segment_get(&segments->probability, (void *)&prob, seed_row, seed_col);
        /* challenge probability unless we need to convert all */
        if(force_convert_all || G_drand48() < prob) {
            /* ger random patch size */
            patch_size = get_patch_size(patch_sizes, region);
            /* last year: we shouldn't grow bigger patches than we have space for */
            if (!overgrow && patch_size + n_done > n_to_convert)
                patch_size = n_to_convert - n_done;
            /* grow patch and return the actual grown size which could be smaller */
            found = grow_patch(seed_row, seed_col, patch_size, step, region,
                               patch_info, segments, patch_overflow, added_ids);
            /* for development testing */
            /*output_developed_step(&segments->developed, "debug",
                                  2000, -1, step, false, false);
            */
            /* update devpressure for every newly developed cell */
            for (i = 0; i < found; i++) {
                get_xy_from_idx(added_ids[i], Rast_window_cols(), &row, &col);
                update_development_pressure_precomputed(row, col, segments, devpressure_info);
            }
            Segment_flush(&segments->devpressure);
            n_done += found;
        }
    }
    extra += (n_done - n_to_convert);
    patch_overflow[region] = extra;
    G_debug(2, "There are %d extra cells for next timestep", extra);
    G_free(added_ids);
}

