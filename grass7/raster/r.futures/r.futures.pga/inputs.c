/*!
   \file inputs.c

   \brief Functions to read in input files and rasters

   (C) 2016-2019 by Vaclav Petras and the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2).  Read the file COPYING that comes with GRASS for details.

   \author Vaclav Petras
 */

#include <stdlib.h>
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
                        struct KeyValueIntInt *potential_region_map, int num_predictors)
{
    int i;
    int row, col;
    int rows, cols;
    int fd_developed, fd_reg, fd_devpressure, fd_weights, fd_pot_reg;
    int *fds_predictors;
    int count_regions, pot_count_regions;
    int region_index, pot_region_index;
    CELL c;
    FCELL fc;
    bool isnull;

    size_t predictor_segment_cell_size;

    CELL *developed_row;
    CELL *subregions_row;
    CELL *pot_subregions_row;
    FCELL *devpressure_row;
    FCELL *predictor_row;
    FCELL *weights_row;
    FCELL *predictor_seg_row;


    rows = Rast_window_rows();
    cols = Rast_window_cols();
    count_regions = region_index = 0;
    pot_count_regions = pot_region_index = 0;

    fds_predictors = G_malloc(num_predictors * sizeof(int));

    /* open existing raster maps for reading */
    fd_developed = Rast_open_old(inputs.developed, "");
    fd_reg = Rast_open_old(inputs.regions, "");
    if (segments->use_potential_subregions)
        fd_pot_reg = Rast_open_old(inputs.potential_regions, "");
    fd_devpressure = Rast_open_old(inputs.devpressure, "");
    if (segments->use_weight)
        fd_weights = Rast_open_old(inputs.weights, "");
    for (i = 0; i < num_predictors; i++) {
        fds_predictors[i] = Rast_open_old(inputs.predictors[i], "");
    }

    predictor_segment_cell_size = sizeof(FCELL) * num_predictors;
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
    /* Segment open predictors */
    if (Segment_open(&segments->predictors, G_tempfile(), rows,
                     cols, segment_info.rows, segment_info.cols,
                     predictor_segment_cell_size, segment_info.in_memory) != 1)
        G_fatal_error(_("Cannot create temporary file with segments of predictor raster maps"));
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
    predictor_row = Rast_allocate_buf(FCELL_TYPE);
    predictor_seg_row = G_malloc(cols * num_predictors * sizeof(FCELL));
    if (segments->use_weight)
        weights_row = Rast_allocate_buf(FCELL_TYPE);
    if (segments->use_potential_subregions)
        pot_subregions_row = Rast_allocate_buf(CELL_TYPE);

    for (row = 0; row < rows; row++) {
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
        /* handle predictors separately */
        for (i = 0; i < num_predictors; i++) {
            Rast_get_row(fds_predictors[i], predictor_row, row, FCELL_TYPE);
            for (col = 0; col < cols; col++) {
                isnull = false;
                predictor_seg_row[col * num_predictors + i] = predictor_row[col];
                /* collect all nulls in predictors and set it in output raster */
                if (Rast_is_null_value(&((FCELL *) predictor_row)[col], FCELL_TYPE))
                    Rast_set_c_null_value(&((CELL *) developed_row)[col], 1);
            }
        }
        Segment_put_row(&segments->developed, developed_row, row);
        Segment_put_row(&segments->devpressure, devpressure_row, row);
        Segment_put_row(&segments->subregions, subregions_row, row);
        Segment_put_row(&segments->predictors, predictor_seg_row, row);
        if (segments->use_weight)
            Segment_put_row(&segments->weight, weights_row, row);
        if (segments->use_potential_subregions)
            Segment_put_row(&segments->potential_subregions, pot_subregions_row, row);
    }

    /* flush all segments */
    Segment_flush(&segments->developed);
    Segment_flush(&segments->subregions);
    Segment_flush(&segments->devpressure);
    Segment_flush(&segments->predictors);
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
    for (i = 0; i < num_predictors; i++)
        Rast_close(fds_predictors[i]);

    G_free(fds_predictors);
    G_free(developed_row);
    G_free(subregions_row);
    G_free(devpressure_row);
    G_free(predictor_row);
    G_free(predictor_seg_row);
    if (segments->use_weight)
        G_free(weights_row);
    if (segments->use_potential_subregions)
        G_free(pot_subregions_row);
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

    const char *fs = "\t";
    const char *td = "\"";

    tokens = G_tokenize2(buf, fs, td);
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
        if (!buf || buf[0] == '\0')
            continue;
        tokens = G_tokenize2(buf, fs, td);
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
    FILE *fp;
    if ((fp = fopen(potentialInfo->filename, "r")) == NULL)
        G_fatal_error(_("Cannot open development potential parameters file <%s>"),
                      potentialInfo->filename);

    const char *fs = "\t";
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

    char **tokens;

    while (G_getl2(buf, buflen, fp)) {
        if (!buf || buf[0] == '\0')
            continue;
        tokens = G_tokenize2(buf, fs, td);
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

    fclose(fp);
}

void read_patch_sizes(struct PatchSizes *patch_info, double discount_factor)
{
    FILE *fin;
    char *size_buffer;
    int n_max_patches;
    int patch;


    patch_info->max_patches = 0;
    patch_info->max_patch_size = 0;

    fin = fopen(patch_info->filename, "rb");
    if (fin) {
        size_buffer = (char *) G_malloc(100 * sizeof(char));
        if (size_buffer) {
            /* just scan the file twice */
            n_max_patches = 0;
            while (fgets(size_buffer, 100, fin)) {
                n_max_patches++;
            }
            rewind(fin);
            if (n_max_patches) {
                patch_info->patch_sizes =
                    (int *) G_malloc(sizeof(int) * n_max_patches);
                if (patch_info->patch_sizes) {
                    while (fgets(size_buffer, 100, fin)) {
                        patch = atoi(size_buffer) * discount_factor;
                        if (patch > 0) {
                            if (patch_info->max_patch_size < patch)
                                patch_info->max_patch_size = patch;
                            patch_info->patch_sizes[patch_info->max_patches] = patch;
                            patch_info->max_patches++;
                        }
                    }
                }
            }
            free(size_buffer);
        }
        fclose(fin);
    }
}

