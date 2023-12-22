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

#include "keyvalue.h"
#include "inputs.h"

/*!
 * \brief Initialize arrays for transformation of probability values
 * \param potential_info
 * \param exponent
 */
void initialize_incentive(struct Potential *potential_info, float exponent)
{
    int i;

    potential_info->incentive_transform_size = 1001;
    potential_info->incentive_transform = (float *) G_malloc(sizeof(float) *
                                                             potential_info->incentive_transform_size);
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
 * \param num_predictors
 */
void read_input_rasters(struct RasterInputs inputs, struct Segments *segments,
                        struct SegmentMemory segment_info, struct KeyValueIntInt *region_map,
                        struct KeyValueIntInt *reverse_region_map,
                        struct KeyValueIntInt *potential_region_map)
{
    int row, col;
    int rows, cols;
    int fd_developed, fd_reg, fd_devpressure, fd_weights, fd_pot_reg;
    int count_regions, pot_count_regions;
    int region_index, pot_region_index;
    CELL c;
    FCELL fc;
    bool isnull;
    CELL *developed_row;
    CELL *subregions_row;
    CELL *pot_subregions_row;
    FCELL *devpressure_row;
    FCELL *weights_row;


    rows = Rast_window_rows();
    cols = Rast_window_cols();
    count_regions = region_index = 0;
    pot_count_regions = pot_region_index = 0;

    /* open existing raster maps for reading */
    fd_developed = Rast_open_old(inputs.developed, "");
    fd_reg = Rast_open_old(inputs.regions, "");
    if (segments->use_potential_subregions)
        fd_pot_reg = Rast_open_old(inputs.potential_regions, "");
    fd_devpressure = Rast_open_old(inputs.devpressure, "");
    if (segments->use_weight)
        fd_weights = Rast_open_old(inputs.weights, "");

    /* Segment open developed */
    if (Segment_open(&segments->developed, G_tempfile(), rows,
                     cols, segment_info.rows, segment_info.cols,
                     Rast_cell_size(CELL_TYPE), segment_info.in_memory) != 1)
        G_fatal_error(_("Cannot create temporary file with segments of a raster map of development"));
    /* Segment open subregions */
    if (Segment_open(&segments->subregions, G_tempfile(), rows,
                     cols, segment_info.rows, segment_info.cols,
                     Rast_cell_size(CELL_TYPE), segment_info.in_memory) != 1)
        G_fatal_error(_("Cannot create temporary file with segments of a raster map of subregions"));
    /* Segment open development pressure */
    if (Segment_open(&segments->devpressure, G_tempfile(), rows,
                     cols, segment_info.rows, segment_info.cols,
                     Rast_cell_size(FCELL_TYPE), segment_info.in_memory) != 1)
        G_fatal_error(_("Cannot create temporary file with segments of a raster map of development pressure"));
    /* Segment open weights */
    if (segments->use_weight)
        if (Segment_open(&segments->weight, G_tempfile(), rows,
                         cols, segment_info.rows, segment_info.cols,
                         Rast_cell_size(FCELL_TYPE), segment_info.in_memory) != 1)
            G_fatal_error(_("Cannot create temporary file with segments of a raster map of weights"));
    /* Segment open potential_subregions */
    if (segments->use_potential_subregions)
        if (Segment_open(&segments->potential_subregions, G_tempfile(), rows,
                         cols, segment_info.rows, segment_info.cols,
                         Rast_cell_size(CELL_TYPE), segment_info.in_memory) != 1)
            G_fatal_error(_("Cannot create temporary file with segments of a raster map of weights"));
    developed_row = Rast_allocate_buf(CELL_TYPE);
    subregions_row = Rast_allocate_buf(CELL_TYPE);
    devpressure_row = Rast_allocate_buf(FCELL_TYPE);

    if (segments->use_weight)
        weights_row = Rast_allocate_buf(FCELL_TYPE);
    if (segments->use_potential_subregions)
        pot_subregions_row = Rast_allocate_buf(CELL_TYPE);

    for (row = 0; row < rows; row++) {
        G_percent(row, rows, 5);
        /* read developed row */
        Rast_get_row(fd_developed, developed_row, row, CELL_TYPE);
        Rast_get_row(fd_devpressure, devpressure_row, row, FCELL_TYPE);
        Rast_get_row(fd_reg, subregions_row, row, CELL_TYPE);
        if (segments->use_weight)
            Rast_get_row(fd_weights, weights_row, row, FCELL_TYPE);
        if (segments->use_potential_subregions)
            Rast_get_row(fd_pot_reg, pot_subregions_row, row, CELL_TYPE);
        for (col = 0; col < cols; col++) {
            isnull = false;
            /* developed */
            /* undeveloped 0 -> -1, developed 1 -> 0 */
            if (!Rast_is_null_value(&((CELL *) developed_row)[col], CELL_TYPE)) {
                c = ((CELL *) developed_row)[col];
                ((CELL *) developed_row)[col] = c - 1;
            }
            else
                isnull = true;
            /* subregions */
            if (!Rast_is_null_value(&((CELL *) subregions_row)[col], CELL_TYPE)) {
                c = ((CELL *) subregions_row)[col];
                if (!KeyValueIntInt_find(region_map, c, &region_index)) {
                    KeyValueIntInt_set(region_map, c, count_regions);
                    KeyValueIntInt_set(reverse_region_map, count_regions, c);
                    region_index = count_regions;
                    count_regions++;
                }
                ((CELL *) subregions_row)[col] = region_index;
            }
            else
                isnull = true;
            if (segments->use_potential_subregions) {
                if (!Rast_is_null_value(&((CELL *) pot_subregions_row)[col], CELL_TYPE)) {
                    c = ((CELL *) pot_subregions_row)[col];
                    if (!KeyValueIntInt_find(potential_region_map, c, &pot_region_index)) {
                        KeyValueIntInt_set(potential_region_map, c, pot_count_regions);
                        pot_region_index = pot_count_regions;
                        pot_count_regions++;
                    }
                    ((CELL *) pot_subregions_row)[col] = pot_region_index;
                }
                else
                    isnull = true;
            }
            /* devpressure - just check nulls */
            if (Rast_is_null_value(&((FCELL *) devpressure_row)[col], FCELL_TYPE))
                isnull = true;
            /* weights - must be in range -1, 1*/
            if (segments->use_weight) {
                if (Rast_is_null_value(&((FCELL *) weights_row)[col], FCELL_TYPE)) {
                    ((FCELL *) weights_row)[col] = 0;
                    isnull = true;
                }
                else {
                    fc = ((FCELL *) weights_row)[col];
                    if (fc > 1) {
                        G_warning(_("Probability weights are > 1, truncating..."));
                        fc = 1;
                    }
                    else if (fc < -1) {
                        fc = -1;
                        G_warning(_("Probability weights are < -1, truncating..."));
                    }
                    ((FCELL *) weights_row)[col] = fc;
                }
            }
            /* if in developed, subregions, devpressure or weights are any nulls
               propagate them into developed */
            if (isnull)
                Rast_set_c_null_value(&((CELL *) developed_row)[col], 1);
        }

        Segment_put_row(&segments->developed, developed_row, row);
        Segment_put_row(&segments->devpressure, devpressure_row, row);
        Segment_put_row(&segments->subregions, subregions_row, row);
        if (segments->use_weight)
            Segment_put_row(&segments->weight, weights_row, row);
        if (segments->use_potential_subregions)
            Segment_put_row(&segments->potential_subregions, pot_subregions_row, row);
    }
    G_percent(row, rows, 5);

    /* flush all segments */
    Segment_flush(&segments->developed);
    Segment_flush(&segments->subregions);
    Segment_flush(&segments->devpressure);
    if (segments->use_weight)
        Segment_flush(&segments->weight);
    if (segments->use_potential_subregions)
        Segment_flush(&segments->potential_subregions);

    /* close raster maps */
    Rast_close(fd_developed);
    Rast_close(fd_reg);
    Rast_close(fd_devpressure);
    if (segments->use_weight)
        Rast_close(fd_weights);
    if (segments->use_potential_subregions)
        Rast_close(fd_pot_reg);

    G_free(developed_row);
    G_free(subregions_row);
    G_free(devpressure_row);

    if (segments->use_weight)
        G_free(weights_row);
    if (segments->use_potential_subregions)
        G_free(pot_subregions_row);
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
    if (Segment_open(&segments->aggregated_predictor, G_tempfile(), rows,
                     cols, segment_info.rows, segment_info.cols,
                     Rast_cell_size(FCELL_TYPE), segment_info.in_memory) != 1)
        G_fatal_error(_("Cannot create temporary file with segments of predictor raster maps"));

    /* read in */
    for (row = 0; row < rows; row++) {
        for (i = 0; i < potential->max_predictors; i++) {
            Rast_get_row(fds_predictors[i], predictor_rows[i], row, FCELL_TYPE);
        }
        for (col = 0; col < cols; col++) {
            ((FCELL *) aggregated_row)[col] = 0;
            Segment_get(&segments->developed, (void *)&dev_value, row, col);
            if (Rast_is_null_value(&dev_value, CELL_TYPE)) {
                continue;
            }
            for (i = 0; i < potential->max_predictors; i++) {
                /* collect all nulls in predictors and set it in output raster */
                if (Rast_is_null_value(&((FCELL *) predictor_rows[i])[col], FCELL_TYPE)) {
                    Rast_set_c_null_value(&dev_value, 1);
                    Segment_put(&segments->developed, (void *)&dev_value, row, col);
                    break;
                }
                if (segments->use_potential_subregions)
                    Segment_get(&segments->potential_subregions, (void *)&pot_index, row, col);
                else
                    Segment_get(&segments->subregions, (void *)&pot_index, row, col);
                value = potential->predictors[i][pot_index] * ((FCELL *) predictor_rows[i])[col];
                ((FCELL *) aggregated_row)[col] += value;
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


void read_demand_file(struct Demand *demandInfo, struct KeyValueIntInt *region_map)
{
    FILE *fp;
    if ((fp = fopen(demandInfo->filename, "r")) == NULL)
        G_fatal_error(_("Cannot open population demand file <%s>"),
                      demandInfo->filename);
    int countlines = 0;
    // Extract characters from file and store in character c
    for (char c = getc(fp); c != EOF; c = getc(fp))
        if (c == '\n') // Increment count if this character is newline
            countlines++;

    rewind(fp);

    size_t buflen = 4000;
    char buf[buflen];
    if (G_getl2(buf, buflen, fp) == 0)
        G_fatal_error(_("Population demand file <%s>"
                        " contains less than one line"), demandInfo->filename);

    char **tokens;
    int ntokens;

    const char *td = "\"";

    tokens = G_tokenize2(buf, demandInfo->separator, td);
    ntokens = G_number_of_tokens(tokens);
    if (ntokens == 0)
        G_fatal_error("No columns in the header row");

    struct ilist *ids = G_new_ilist();
    int count;
    // skip first column which does not contain id of the region
    int i;
    for (i = 1; i < ntokens; i++) {
        G_chop(tokens[i]);
        G_ilist_add(ids, atoi(tokens[i]));
    }

    int years = 0;
    demandInfo->table = (int **) G_malloc(region_map->nitems * sizeof(int *));
    for (int i = 0; i < region_map->nitems; i++) {
        demandInfo->table[i] = (int *) G_malloc(countlines * sizeof(int));
    }
    demandInfo->years = (int *) G_malloc(countlines * sizeof(int));
    while(G_getl2(buf, buflen, fp)) {
        if (buf[0] == '\0')
            continue;
        tokens = G_tokenize2(buf, demandInfo->separator, td);
        int ntokens2 = G_number_of_tokens(tokens);
        if (ntokens2 == 0)
            continue;
        if (ntokens2 != ntokens)
            G_fatal_error(_("Demand: wrong number of columns in line: %s"), buf);

        count = 0;
        int i;
        demandInfo->years[years] = atoi(tokens[0]);
        for (i = 1; i < ntokens; i++) {
            // skip first column which is the year which we ignore
            int idx;
            if (KeyValueIntInt_find(region_map, ids->value[count], &idx)) {
                G_chop(tokens[i]);
                demandInfo->table[idx][years] = atoi(tokens[i]);
            }
            count++;
        }
        // each line is a year
        years++;
    }
    demandInfo->max_subregions = region_map->nitems;
    demandInfo->max_steps = years;
    G_verbose_message("Number of steps in demand file: %d", years);
    //    if (!sParams.nSteps)
    //        sParams.nSteps = years;
    G_free_ilist(ids);
    G_free_tokens(tokens);
}

void read_potential_file(struct Potential *potentialInfo, struct KeyValueIntInt *region_map,
                         int num_predictors)
{
    int i;
    FILE *fp;
    bool *check;
    bool problem;
    if ((fp = fopen(potentialInfo->filename, "r")) == NULL)
        G_fatal_error(_("Cannot open development potential parameters file <%s>"),
                      potentialInfo->filename);

    const char *td = "\"";

    size_t buflen = 4000;
    char buf[buflen];
    if (G_getl2(buf, buflen, fp) == 0)
        G_fatal_error(_("Development potential parameters file <%s>"
                        " contains less than one line"), potentialInfo->filename);
    potentialInfo->max_predictors = num_predictors;
    potentialInfo->intercept = (double *) G_malloc(region_map->nitems * sizeof(double));
    potentialInfo->devpressure = (double *) G_malloc(region_map->nitems * sizeof(double));
    potentialInfo->predictors = (double **) G_malloc(num_predictors * sizeof(double *));
    for (int i = 0; i < num_predictors; i++) {
        potentialInfo->predictors[i] = (double *) G_malloc(region_map->nitems * sizeof(double));
    }
    check = G_calloc(region_map->nitems, sizeof(int));

    char **tokens;

    while (G_getl2(buf, buflen, fp)) {
        if (buf[0] == '\0')
            continue;
        tokens = G_tokenize2(buf, potentialInfo->separator, td);
        int ntokens = G_number_of_tokens(tokens);
        if (ntokens == 0)
            continue;
        // id + intercept + devpressure + predictores
        if (ntokens != num_predictors + 3)
            G_fatal_error(_("Potential: wrong number of columns: %s"), buf);

        int idx;
        int id;
        double coef_intercept, coef_devpressure;
        double val;
        int j;

        G_chop(tokens[0]);
        id = atoi(tokens[0]);
        if (KeyValueIntInt_find(region_map, id, &idx)) {
            check[idx] = 1;
            G_chop(tokens[1]);
            coef_intercept = atof(tokens[1]);
            G_chop(tokens[2]);
            coef_devpressure = atof(tokens[2]);
            potentialInfo->intercept[idx] = coef_intercept;
            potentialInfo->devpressure[idx] = coef_devpressure;
            for (j = 0; j < num_predictors; j++) {
                G_chop(tokens[j + 3]);
                val = atof(tokens[j + 3]);
                potentialInfo->predictors[j][idx] = val;
            }
        }
        // else ignoring the line with region which is not used

        G_free_tokens(tokens);
    }
    problem = false;
    for (i = 0; i < region_map->nitems; i++) {
        if (!check[i]) {
            G_warning("Region %d missing in potential file.", region_map->key[i]);
            problem = true;
        }
    }
    G_free(check);
    fclose(fp);
    if (problem)
        G_fatal_error("Missing counties in potential file");
}

void read_patch_sizes(struct PatchSizes *patch_sizes,
                      struct KeyValueIntInt *region_map,
                      double discount_factor)
{
    FILE *fp;
    size_t buflen = 4000;
    char buf[buflen];
    int patch;
    char** tokens;
    char** header_tokens;
    int ntokens;
    int i, j;
    int region_id;
    const char *td = "\"";
    int num_regions;
    bool found;
    bool use_header;
    int n_max_patches;

    n_max_patches = 0;
    patch_sizes->max_patch_size = 0;
    fp = fopen(patch_sizes->filename, "rb");
    if (fp) {
        /* just scan the file twice */
        // scan in the header line
        if (G_getl2(buf, buflen, fp) == 0)
            G_fatal_error(_("Patch library file <%s>"
                            " contains less than one line"), patch_sizes->filename);

        header_tokens = G_tokenize2(buf, ",", td);
        num_regions = G_number_of_tokens(header_tokens);
        use_header = true;
        patch_sizes->single_column = false;
        if (num_regions == 1) {
            use_header = false;
            patch_sizes->single_column = true;
            G_verbose_message(_("Only single column detected in patch library file <%s>."
                                " It will be used for all subregions."), patch_sizes->filename);
        }
        /* Check there are enough columns for subregions in map */
        if (num_regions != 1 && num_regions < region_map->nitems)
            G_fatal_error(_("Patch library file <%s>"
                            " has only %d columns but there are %d subregions"), patch_sizes->filename,
                          num_regions, region_map->nitems);
        /* Check all subregions in map have column in the file. */
        if (use_header) {
            for (i = 0; i < region_map->nitems; i++) {
                found = false;
                for (j = 0; j < num_regions; j++)
                    if (region_map->key[i] == atoi(header_tokens[j]))
                        found = true;
                if (!found)
                    G_fatal_error(_("Subregion id <%d> not found in header of patch file <%s>"),
                                  region_map->key[i], patch_sizes->filename);
            }
        }
        // initialize patch_info->patch_count to all zero
        patch_sizes->patch_count = (int*) G_calloc(num_regions, sizeof(int));
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
                                " has inconsistent number of columns"), patch_sizes->filename);
            n_max_patches++;
        }
        // in a 2D array
        patch_sizes->patch_sizes = (int **) G_malloc(sizeof(int * ) * num_regions);
        // malloc appropriate size for each area
        for(i = 0; i < num_regions; i++) {
            patch_sizes->patch_sizes[i] =
                    (int *) G_malloc(n_max_patches * sizeof(int));
        }
        /* read first line to skip header */
        rewind(fp);
        if (use_header)
            G_getl2(buf, buflen, fp);

        while (G_getl2(buf, buflen, fp)) {
            tokens = G_tokenize2(buf, ",", td);
            ntokens = G_number_of_tokens(tokens);
            for (i = 0; i < ntokens; i++) {
                if (strcmp(tokens[i], "") != 0 ) {
                    patch = atoi(tokens[i]) * discount_factor;
                    if (patch > 0) {
                        if (patch_sizes->max_patch_size < patch)
                            patch_sizes->max_patch_size = patch;
                        if (use_header) {
                            if (!KeyValueIntInt_find(region_map, atoi(header_tokens[i]), &region_id))
                                continue;
                        }
                        else
                            region_id = 0;
                        patch_sizes->patch_sizes[region_id][patch_sizes->patch_count[region_id]] = patch;
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


