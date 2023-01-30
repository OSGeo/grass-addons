/*!
   \file patch.c

   \brief Functions to grow patches

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

#include "keyvalue.h"
#include "inputs.h"
#include "patch.h"
#include "utils.h"

static int sort_neighbours(const void *p1, const void *p2)
{
    struct CandidateNeighbor *p1_ = (struct CandidateNeighbor *)p1;
    struct CandidateNeighbor *p2_ = (struct CandidateNeighbor *)p2;
    if (p1_->suitability > p2_->suitability) {
        return -1;
    }
    if (p2_->suitability > p1_->suitability) {
        return 1;
    }
    return 0;
}

/*!
 * \brief Computes alpha value influencing patch compactness
 *
 * Alpha is a random (uniform) value in [mean - 0.5 range, mean + 0.5 range)
 *
 * \param[in] patch_info patch parameters
 * \return alpha
 */
static float get_alpha(struct PatchInfo *patch_info)
{
    float alpha;

    alpha =
        (patch_info->compactness_mean) - (patch_info->compactness_range) * 0.5;
    alpha += G_drand48() * patch_info->compactness_range;
    return alpha;
}

/*!
 * \brief Gets randomly selected patch size from a pool of data-derived sizes
 * \param patch_sizes patch sizes
 * \param region region idx
 * \return number of cells
 */
int get_patch_size(struct PatchSizes *patch_sizes, int region)
{
    if (patch_sizes->single_column)
        region = 0;
    return patch_sizes->patch_sizes[region][(
        int)(G_drand48() * patch_sizes->patch_count[region])];
}
/*!
 * \brief Decides if to add a cell to a candidate list for patch growing
 *
 * Only adds cells if they are not developed yet. Computes cells suitability
 * based on its probability adjusted by distance from seed in order to
 * allow for different compactness.
 *
 * \param[in] row row
 * \param[in] col column
 * \param[in] seed_row initial seed row
 * \param[in] seed_col initial seed column
 * \param[in] rows number of rows
 * \param[in] cols number of cols
 * \param[in,out] candidate_list list of candidate cells
 * \param[in,out] segments segments
 * \param[in] patch_info patch parameters
 */
void add_neighbour(int row, int col, int seed_row, int seed_col, int rows,
                   int cols, struct CandidateNeighborsList *candidate_list,
                   struct Segments *segments, struct PatchInfo *patch_info)
{
    int i;
    double distance;
    float alpha;
    size_t idx;
    CELL value;
    FCELL prob;

    if (row < 0 || row >= rows || col < 0 || col >= cols)
        return;

    Segment_get(&segments->developed, (void *)&value, row, col);
    if (Rast_is_null_value(&value, CELL_TYPE))
        return;
    if (value == -1) {
        idx = get_idx_from_xy(row, col, Rast_window_cols());
        /* need to add this cell... */

        /* stop if already there */
        for (i = 0; i < candidate_list->n; i++) {
            if (candidate_list->candidates[i].id == idx) {
                return;
            }
        }
        /* or add it on the end, allocating space if necessary */
        if (candidate_list->n == candidate_list->max_n) {
            candidate_list->max_n += candidate_list->block_size;
            candidate_list->candidates = (struct CandidateNeighbor *)G_realloc(
                candidate_list->candidates,
                candidate_list->max_n * sizeof(struct CandidateNeighbor));
            if (!candidate_list->candidates) {
                G_fatal_error("Memory error in add_neighbour_if_possible()");
            }
        }
        candidate_list->candidates[candidate_list->n].id = idx;
        Segment_get(&segments->probability, (void *)&prob, row, col);
        candidate_list->candidates[candidate_list->n].potential = prob;
        distance = get_distance(seed_row, seed_col, row, col);
        alpha = get_alpha(patch_info);
        candidate_list->candidates[candidate_list->n].suitability =
            prob / pow(distance, alpha);
        candidate_list->n++;
    }
}
/*!
 * \brief Add candidate cells for patch growing
 *
 * Add immediate surrounding cells (4 or 8 neighborhood) to a list of
 * candidates.
 *
 * \param[in] row row
 * \param[in] col column
 * \param[in] seed_row initial seed row
 * \param[in] seed_col initial seed column
 * \param[in] rows number of rows
 * \param[in] cols number of cols
 * \param[in,out] candidate_list list of candidate cells
 * \param[in,out] segments segments
 * \param[in] patch_info patch parameters
 */
void add_neighbours(int row, int col, int seed_row, int seed_col, int rows,
                    int cols, struct CandidateNeighborsList *candidate_list,
                    struct Segments *segments, struct PatchInfo *patch_info)
{
    add_neighbour(row - 1, col, seed_row, seed_col, rows, cols, candidate_list,
                  segments, patch_info); // left
    add_neighbour(row + 1, col, seed_row, seed_col, rows, cols, candidate_list,
                  segments, patch_info); // right
    add_neighbour(row, col - 1, seed_row, seed_col, rows, cols, candidate_list,
                  segments, patch_info); // down
    add_neighbour(row, col + 1, seed_row, seed_col, rows, cols, candidate_list,
                  segments, patch_info); // up
    if (patch_info->num_neighbors == 8) {
        add_neighbour(row - 1, col - 1, seed_row, seed_col, rows, cols,
                      candidate_list, segments, patch_info);
        add_neighbour(row - 1, col + 1, seed_row, seed_col, rows, cols,
                      candidate_list, segments, patch_info);
        add_neighbour(row + 1, col - 1, seed_row, seed_col, rows, cols,
                      candidate_list, segments, patch_info);
        add_neighbour(row + 1, col + 1, seed_row, seed_col, rows, cols,
                      candidate_list, segments, patch_info);
    }
}

/*!
 * @brief Grows a patch of given size using given seed
 *
 * For each cell it develops, it adds its neighbors to
 * a list of candidates. The candidates are sorted based on their suitability
 * and challenged by a randomly generated number.
 * If it can't find suitable candidates in reasonable number of iterations,
 * depending on the strategy, it will either stop growing the patch
 * or force growing a candidate cell.
 *
 * @param[in] seed_row seed row
 * @param[in] seed_col seed column
 * @param[in] patch_size size of patch in number of cells
 * @param[in] step current simulation step
 * @param[in] region currently processed region
 * @param[in] patch_info patch parameters
 * @param[in,out] segments segments
 * @param[in,out] patch_overflow to track grown cells overflowing to adjacent
 * regions
 * @param[out] added_ids array of ids of grown cells
 * @return number of grown cells including seed grown inside this region
 */
int grow_patch(int seed_row, int seed_col, int patch_size, int step, int region,
               struct PatchInfo *patch_info, struct Segments *segments,
               int *patch_overflow, int *added_ids)
{
    int i, j, iter;
    double r, p;
    int found, found_in_this_region;
    bool force, skip;
    int row, col, cols, rows;
    CELL test_region;

    struct CandidateNeighborsList candidates;
    candidates.block_size = 20;
    candidates.candidates = (struct CandidateNeighbor *)G_malloc(
        sizeof(struct CandidateNeighbor) * candidates.block_size);
    candidates.max_n = candidates.block_size;
    candidates.n = 0;

    cols = Rast_window_cols();
    rows = Rast_window_rows();
    force = false;
    skip = false;
    found = 1; /* seed is the first cell */
    found_in_this_region = 1;
    step += 1; /* e.g. first step=0 will be saved as 1 */

    /* set seed as developed */
    Segment_put(&segments->developed, (void *)&step, seed_row, seed_col);
    added_ids[0] = get_idx_from_xy(seed_row, seed_col, Rast_window_cols());

    /* add surrounding neighbors */
    add_neighbours(seed_row, seed_col, seed_row, seed_col, rows, cols,
                   &candidates, segments, patch_info);
    iter = 0;
    while (candidates.n > 0 && found < patch_size && !skip) {
        i = 0;
        while (1) {
            /* challenge the candidate */
            r = G_drand48();
            p = candidates.candidates[i].potential;
            if (r < p || force) {
                /* update list of added IDs */
                added_ids[found] = candidates.candidates[i].id;
                /* update to developed */
                get_xy_from_idx(candidates.candidates[i].id, cols, &row, &col);
                Segment_put(&segments->developed, (void *)&step, row, col);
                /* remove this one from the list by copying down everything
                 * above it */
                for (j = i + 1; j < candidates.n; j++) {
                    candidates.candidates[j - 1].id =
                        candidates.candidates[j].id;
                    candidates.candidates[j - 1].potential =
                        candidates.candidates[j].potential;
                    candidates.candidates[j - 1].suitability =
                        candidates.candidates[j].suitability;
                }
                /* reduce the size of the list */
                candidates.n--;
                /* find and add new candidates */
                add_neighbours(row, col, seed_row, seed_col, rows, cols,
                               &candidates, segments, patch_info);
                /* sort candidates based on probability */
                qsort(candidates.candidates, candidates.n,
                      sizeof(struct CandidateNeighbor), sort_neighbours);
                Segment_get(&segments->subregions, (void *)&test_region, row,
                            col);
                /* if growing outside of region, account for that, increase
                 * number of cells outside of region */
                if (test_region != region)
                    patch_overflow[test_region]++;
                else
                    found_in_this_region++;
                /* total found inside and outside of this region */
                found++;
                /* restart max iterations when cell found */
                iter = 0;
                force = false;
                break;
            }
            else {
                i++;
                if (i == candidates.n) {
                    i = 0;
                    iter++;
                    if (iter > MAX_CANDIDATE_ITER) {
                        if (patch_info->strategy == FORCE_GROW) {
                            force = true;
                        }
                        else if (patch_info->strategy == SKIP) {
                            skip = true;
                            break;
                        }
                    }
                }
            }
        }
    }

    if (candidates.max_n > 0)
        G_free(candidates.candidates);

    Segment_flush(&segments->developed);
    return found_in_this_region;
}
