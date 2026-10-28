/*!
   \file redistribute.c

   \brief Functions to redistribute population

   (C) 2016-2019 by Anna Petrasova and the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2).  Read the file COPYING that comes with GRASS for details.

   \author Anna Petrasova
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/glocale.h>

#include "map.h"
#include "redistribute.h"
#include "inputs.h"
#include "output.h"

/*!
 * \brief Select item based on its probability
 *
 * https://stackoverflow.com/questions/9330394/how-to-pick-an-item-by-its-probability
 *
 * \param probabilities array
 * \param size of array
 * \return index of array
 */
int pick_region(const float *probabilities, int size)
{
    volatile double p;
    volatile int i;
    volatile float cumulative;

    p = G_drand48();
    cumulative = 0;
    for (i = 0; i < size; i++) {
        cumulative += probabilities[i];
        if (p <= cumulative)
            return i;
    }
    return i - 1;
}

/*!
 * \brief Redistribute to other county
 *
 * \param matrix Redistribution matrix structure
 * \param demand Demand structure
 * \param regionID ID of subregion (like FIPS)
 * \param num_px number of pixels to move
 * \param region_map Maps subregion ID -> index
 * \param step Simulation step
 * \param leaving_population population leaving outside of study area
 */
void redistribute(struct RedistributionMatrix *matrix, struct Demand *demand,
                  int regionID, int num_px, map_int_t *region_map, int step,
                  float *leaving_population)
{
    int to_idx;
    int *from_idx;
    int *to_ID;
    int *demand_to_idx;
    int *demand_from_idx;
    float density_from, density_to;
    float to_px;

    from_idx = map_get_int(&matrix->from_map, regionID);
    if (!from_idx) {
        G_warning("Region %d is not in redistribution matrix rows", regionID);
        return;
    }
    to_idx = pick_region(matrix->probabilities[*from_idx], matrix->dim_to);
    to_ID = map_get_int(&matrix->to_map, to_idx);

    /* should always be there */
    demand_from_idx = map_get_int(region_map, regionID);
    density_from = demand->population_table[*demand_from_idx][step] /
                   demand->cells_table[*demand_from_idx][step];
    demand_to_idx = map_get_int(region_map, *to_ID);
    if (demand_to_idx) {
        density_to = demand->population_table[*demand_to_idx][step] /
                     demand->cells_table[*demand_to_idx][step];
        if (demand_from_idx == demand_to_idx)
            to_px = num_px;
        else if (density_from <= 0 || density_to <= 0 ||
                 !isfinite(density_from) || !isfinite(density_to))
            to_px = num_px;
        else
            /* number of pixels in 'to' region */
            to_px = num_px * density_from / density_to;
        /* increase number of px to grow next step */
        if (step + 1 < demand->max_steps) {
            demand->cells_table[*demand_to_idx][step + 1] += to_px;
            G_debug(2, "%f cells moved from %d to %d in step %d", to_px,
                    regionID, *to_ID, step);
            matrix->moved_px[*from_idx][to_idx] += to_px;
        }
        else {
            /* ignore last year */
        }
    }
    else {
        /* outside of simulation extent, assume the same density */
        matrix->moved_px[*from_idx][to_idx] += num_px;
        G_debug(2, "%d cells moved from %d to %d (outside) in step %d", num_px,
                regionID, *to_ID, step);
    }
}

/*!
 * \brief Reads redistribution matrix
 *
 * Matrix is in CSV file such as:
 *      ,27642,27645, ...
 * 27642,0.22,1.01, ...   sum of line except of region code should be < 100
 * 27645,9.12,0.28,...
 *
 * This means probability that someone from 27642 moves to 27645 is 1.01%
 *
 * \param matrix structure
 */
void read_redistribution_matrix(struct RedistributionMatrix *matrix)
{
    FILE *fin;
    size_t buflen = 35000;
    char *buf;
    const char *fs = ",";
    const char *td = "\"";
    int ntokens, ntokens2;
    char **tokens, **tokens2;
    int row, col;
    int new_size;

    buf = (char *)G_malloc(buflen * sizeof(char));

    if ((fin = fopen(matrix->filename, "r")) == NULL)
        G_fatal_error(_("Cannot open redistribution matrix file <%s>"),
                      matrix->filename);
    map_init(&matrix->from_map);
    map_init(&matrix->to_map);
    map_init(&matrix->reverse_from_map);

    /* read first line */
    if (G_getl2(buf, buflen, fin) == 0)
        G_fatal_error(_("Redistribution matrix file <%s>"
                        " contains less than one line"),
                      matrix->filename);
    else {
        tokens = G_tokenize2(buf, fs, td);
        ntokens = G_number_of_tokens(tokens);
        for (col = 1; col < ntokens; col++) {
            map_set_int(&matrix->to_map, col - 1, atoi(tokens[col]));
        }
    }

    matrix->dim_to = ntokens - 1;
    matrix->dim_from = matrix->dim_to;
    matrix->probabilities =
        (float **)G_malloc(matrix->dim_from * sizeof(float *));
    matrix->moved_px = (float **)G_malloc(matrix->dim_from * sizeof(float *));
    matrix->max_dim_from = matrix->dim_from;

    row = 0;
    while (G_getl2(buf, buflen, fin)) {
        if (!buf || buf[0] == '\0')
            continue;
        tokens2 = G_tokenize2(buf, fs, td);
        ntokens2 = G_number_of_tokens(tokens2);
        if (ntokens != ntokens2)
            G_fatal_error(
                _("Number of fields in row in file <%s> is not consistent"),
                matrix->filename);
        /* allocate row */
        matrix->probabilities[row] =
            (float *)G_malloc(matrix->dim_to * sizeof(float));
        matrix->moved_px[row] =
            (float *)G_malloc(matrix->dim_to * sizeof(float));
        for (col = 0; col < ntokens2; col++) {
            if (col == 0) {
                map_set(&matrix->from_map, tokens2[col], row);
                map_set_int(&matrix->reverse_from_map, row, atoi(tokens2[col]));
            }
            else {
                /* convert from % */
                matrix->probabilities[row][col - 1] = atof(tokens2[col]) / 100.;
                matrix->moved_px[row][col - 1] = 0;
            }
        }
        row++;
        if (matrix->max_dim_from <= row) {
            new_size = 2 * matrix->max_dim_from;
            matrix->probabilities = (float **)G_realloc(
                matrix->probabilities, new_size * sizeof(float *));
            matrix->moved_px = (float **)G_realloc(matrix->moved_px,
                                                   new_size * sizeof(float *));
            matrix->max_dim_from = new_size;
        }

        G_free_tokens(tokens2);
    }
    matrix->dim_from = row;
    G_free_tokens(tokens);
    G_free(buf);
}

/*!
 * \brief Returns file name for output file containing
 * matrix of moved pixels up to the step.
 *
 * \param matrix Redistribution matrix structure
 * \param step Step of simulation
 * \param nsteps Number of steps in simulation
 * \return
 */
static char *get_matrix_filename(const struct RedistributionMatrix *matrix,
                                 int step, int nsteps)
{
    const char *name;
    const char *ext;
    char *filename;

    ext = ".csv";
    name = name_for_step(matrix->output_basename, step, nsteps);
    filename = G_malloc((strlen(name) + strlen(ext) + 1) * sizeof(char));
    sprintf(filename, "%s%s", name, ext);
    return filename;
}

/*!
 * \brief Check whether any of the redistr. matrix output files exist
 * \param matrix Redistribution matrix structure
 * \param nsteps Number of steps in simulation
 * \return True if any of the files exist otherwise false
 */
bool check_matrix_filenames_exist(const struct RedistributionMatrix *matrix,
                                  int nsteps)
{
    char *filename;
    int step;
    for (step = 0; step < nsteps; step++) {
        filename = get_matrix_filename(matrix, step, nsteps);
        if (access(filename, F_OK) != -1) {
            G_free(filename);
            return true;
        }
        G_free(filename);
    }
    return false;
}

/*!
 * \brief Write redistribution matrix (number of moved pixels among counties)
 * \param matrix structure
 * \param step step number
 * \param nsteps total number of steps (for file name padding)
 */
void write_redistribution_matrix(struct RedistributionMatrix *matrix, int step,
                                 int nsteps)
{
    FILE *fp;
    const char *name;
    const char *ext;
    char *filename;
    int row, col;
    int *ID;

    ext = ".csv";
    name = name_for_step(matrix->output_basename, step, nsteps);
    filename = G_malloc((strlen(name) + strlen(ext) + 1) * sizeof(char));
    sprintf(filename, "%s%s", name, ext);
    fp = fopen(filename, "w+");
    fprintf(fp, "ID");
    for (col = 0; col < matrix->dim_to; col++) {
        ID = map_get_int(&matrix->to_map, col);
        fprintf(fp, ",%d", *ID);
    }
    fprintf(fp, "\n");
    for (row = 0; row < matrix->dim_from; row++) {
        ID = map_get_int(&matrix->reverse_from_map, row);
        fprintf(fp, "%d", *ID);
        for (col = 0; col < matrix->dim_to; col++) {
            if (matrix->moved_px[row][col] > 0)
                fprintf(fp, ",%f", matrix->moved_px[row][col]);
            else
                fprintf(fp, ",%d", (int)matrix->moved_px[row][col]);
        }
        fprintf(fp, "\n");
    }
    fclose(fp);
    G_free(filename);
}

void free_redistribution_matrix(struct RedistributionMatrix *matrix)
{
    int i;
    for (i = 0; i < matrix->dim_from; i++) {
        G_free(matrix->probabilities[i]);
        G_free(matrix->moved_px[i]);
    }
    G_free(matrix->probabilities);
    G_free(matrix->moved_px);
    map_deinit(&matrix->from_map);
    map_deinit(&matrix->to_map);
    map_deinit(&matrix->reverse_from_map);
}
