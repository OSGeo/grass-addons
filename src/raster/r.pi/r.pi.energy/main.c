/*
 ****************************************************************************
 *
 * MODULE:       r.pi.energy
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Individual-based dispersal model for connectivity analysis -
 *               energy-based
 *
 * COPYRIGHT:    (C) 2009-2011,2017 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#define MAIN

#include "local_proto.h"

int main(int argc, char *argv[])
{
    /* input */
    char *oldname;
    const char *oldmapset;

    /* costmap */
    char *costname;
    const char *costmapset;

    /* suitability map */
    char *suitname;
    const char *suitmapset;

    /* in and out file pointers */
    int in_fd, out_fd;
    FILE *out_fp;

    /* maps */
    int *map;
    DCELL *costmap;
    DCELL *suitmap;

    /* other parameters */
    DCELL threshold;

    /* helper variables */
    int row, col;
    int sx, sy;
    CELL *result;
    DCELL *d_res;
    int neighb_count;
    int i, j;
    Coords *p;
    int sum;
    int out_progress, out_max;
    int fragcount;
    int n;

    struct GModule *module;
    struct {
        struct Option *input, *costmap, *suitability, *output, *out_immi;
        struct Option *keyval, *step_length, *step_range, *perception,
            *multiplicator, *n;
        struct Option *energy, *percent, *out_freq, *immi_matrix, *mig_matrix,
            *binary_matrix;
        struct Option *threshold, *title;
    } parm;
    struct {
        struct Flag *adjacent, *setback, *diversity, *indices;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("landscape structure analysis"));
    G_add_keyword(_("connectivity analysis"));
    module->description = _("Individual-based dispersal model for connectivity "
                            "analysis - energy based.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.costmap = G_define_option();
    parm.costmap->key = "costmap";
    parm.costmap->type = TYPE_STRING;
    parm.costmap->required = NO;
    parm.costmap->gisprompt = "old,cell,raster";
    parm.costmap->description = _("Name of the costmap");
    parm.costmap->guisection = "Optional";

    parm.suitability = G_define_option();
    parm.suitability->key = "suitability";
    parm.suitability->type = TYPE_STRING;
    parm.suitability->required = NO;
    parm.suitability->gisprompt = "old,cell,raster";
    parm.suitability->description =
        _("Name of the suitability raster with values from 0-100");
    parm.suitability->guisection = "Optional";

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.out_immi = G_define_option();
    parm.out_immi->key = "out_immi";
    parm.out_immi->type = TYPE_STRING;
    parm.out_immi->required = NO;
    parm.out_immi->gisprompt = "new,cell,raster";
    parm.out_immi->description =
        _("Name of the optional raster file for patch immigrants count");
    parm.out_immi->guisection = "Optional";

    parm.immi_matrix = G_define_option();
    parm.immi_matrix->key = "immi_matrix";
    parm.immi_matrix->type = TYPE_STRING;
    parm.immi_matrix->required = NO;
    parm.immi_matrix->gisprompt = "new_file,file,output";
    parm.immi_matrix->description = _("Name for immigrants matrix ASCII-file");
    parm.immi_matrix->guisection = "Optional";

    parm.mig_matrix = G_define_option();
    parm.mig_matrix->key = "mig_matrix";
    parm.mig_matrix->type = TYPE_STRING;
    parm.mig_matrix->required = NO;
    parm.mig_matrix->gisprompt = "new_file,file,output";
    parm.mig_matrix->description = _("Name for migrants matrix ASCII-file");
    parm.mig_matrix->guisection = "Optional";

    parm.binary_matrix = G_define_option();
    parm.binary_matrix->key = "binary_matrix";
    parm.binary_matrix->type = TYPE_STRING;
    parm.binary_matrix->required = NO;
    parm.binary_matrix->gisprompt = "new_file,file,output";
    parm.binary_matrix->description =
        _("Name for binary immigrants(migrants) matrix ASCII-file");
    parm.binary_matrix->guisection = "Optional";

    parm.threshold = G_define_option();
    parm.threshold->key = "threshold";
    parm.threshold->type = TYPE_DOUBLE;
    parm.threshold->required = NO;
    parm.threshold->description =
        _("Percentage of individuals which must have immigrated(migrated)"
          " successfully to be considered for the binary immigrants(migrants) "
          "matrix");
    parm.threshold->guisection = "Optional";

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->description = _("Category value of the patches");
    parm.keyval->guisection = "Required";

    parm.step_length = G_define_option();
    parm.step_length->key = "step_length";
    parm.step_length->type = TYPE_INTEGER;
    parm.step_length->required = YES;
    parm.step_length->description =
        _("Length of a single step measured in pixels");
    parm.step_length->guisection = "Required";

    parm.step_range = G_define_option();
    parm.step_range->key = "step_range";
    parm.step_range->type = TYPE_DOUBLE;
    parm.step_range->required = NO;
    parm.step_range->description =
        _("Range to choose the next step direction from, in degrees"
          " [default = 180°]");
    parm.step_range->guisection = "Optional";

    parm.perception = G_define_option();
    parm.perception->key = "perception";
    parm.perception->type = TYPE_INTEGER;
    parm.perception->required = NO;
    parm.perception->description = _("Perception range");
    parm.perception->guisection = "Optional";

    parm.multiplicator = G_define_option();
    parm.multiplicator->key = "multiplicator";
    parm.multiplicator->type = TYPE_DOUBLE;
    parm.multiplicator->required = NO;
    parm.multiplicator->description = _("Attractivity of patches [1-inf]");
    parm.multiplicator->guisection = "Optional";

    parm.n = G_define_option();
    parm.n->key = "n";
    parm.n->type = TYPE_INTEGER;
    parm.n->required = YES;
    parm.n->description = _("Number of individuals");
    parm.n->guisection = "Required";

    parm.energy = G_define_option();
    parm.energy->key = "energy";
    parm.energy->type = TYPE_DOUBLE;
    parm.energy->required = YES;
    parm.energy->description = _("Initial energy of the individuals");
    parm.energy->guisection = "Required";

    parm.percent = G_define_option();
    parm.percent->key = "percent";
    parm.percent->type = TYPE_DOUBLE;
    parm.percent->required = YES;
    parm.percent->description =
        _("Percentage of finished individuals desired before simulation ends");
    parm.percent->guisection = "Required";

    parm.out_freq = G_define_option();
    parm.out_freq->key = "out_freq";
    parm.out_freq->type = TYPE_INTEGER;
    parm.out_freq->required = NO;
    parm.out_freq->description =
        _("Output an intermediate state of simulation each [out_freq] steps");
    parm.out_freq->guisection = "Optional";

    parm.title = G_define_option();
    parm.title->key = "title";
    parm.title->key_desc = "\"phrase\"";
    parm.title->type = TYPE_STRING;
    parm.title->required = NO;
    parm.title->description = _("Title for resultant raster map");
    parm.title->guisection = "Optional";

    flag.adjacent = G_define_flag();
    flag.adjacent->key = 'a';
    flag.adjacent->description =
        _("Set for 8 cell-neighbors. 4 cell-neighbors are default");

    flag.setback = G_define_flag();
    flag.setback->key = 'b';
    flag.setback->description =
        _("Set if individuals should be set back after leaving area");

    flag.diversity = G_define_flag();
    flag.diversity->key = 'd';
    flag.diversity->description = _("Output diversity map");

    flag.indices = G_define_flag();
    flag.indices->key = 'i';
    flag.indices->description = _("Output Shannon- and Simpson-index");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* initialize random generator */
    srand(time(NULL));

    /* get name of input file */
    oldname = parm.input->answer;

    /* test input file existance */
    oldmapset = G_find_raster2(oldname, "");
    if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

    /* get name of costmap */
    costname = parm.costmap->answer;
    costmapset = NULL;

    /* test costmap existance */
    if (costname && (costmapset = G_find_raster2(costname, "")) == NULL)
        G_fatal_error(_("Raster map <%s> not found"), costname);

    /* get name of suitability map */
    suitname = parm.suitability->answer;
    suitmapset = NULL;

    /* test costmap existance */
    if (suitname && (suitmapset = G_find_raster2(suitname, "")) == NULL)
        G_fatal_error(_("Raster map <%s> not found"), suitname);

    /* get keyval */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get step_length */
    sscanf(parm.step_length->answer, "%d", &step_length);

    /* get step_range */
    if (parm.step_range->answer) {
        sscanf(parm.step_range->answer, "%lf", &step_range);
        step_range /= 180.0;
    }
    else {
        step_range = 1.0;
    }

    /* get perception_range */
    if (parm.perception->answer) {
        sscanf(parm.perception->answer, "%d", &perception_range);
    }
    else {
        perception_range = step_length;
    }

    /* get multiplicator */
    if (parm.multiplicator->answer) {
        sscanf(parm.multiplicator->answer, "%lf", &multiplicator);
    }
    else {
        multiplicator = 1.0;
    }

    /* get n */
    sscanf(parm.n->answer, "%d", &n);

    /* get energy */
    sscanf(parm.energy->answer, "%lf", &energy);

    /* get percent */
    sscanf(parm.percent->answer, "%lf", &percent);

    /* get number of cell-neighbors */
    neighb_count = flag.adjacent->answer ? 8 : 4;

    /* get setback flag */
    setback = flag.adjacent->answer;

    /* get out_freq */
    if (parm.out_freq->answer != NULL) {
        sscanf(parm.out_freq->answer, "%d", &out_freq);
    }
    else {
        out_freq = 0;
    }

    /* get threshold */
    if (parm.threshold->answer) {
        sscanf(parm.threshold->answer, "%lf", &threshold);
    }
    else {
        threshold = 0.0;
    }

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), newname);

    /* get size */
    sx = Rast_window_cols();
    sy = Rast_window_rows();

    /* test output */
    /*fprintf(stderr, "TEST OUTPUT : \n");
       fprintf(stderr, "input = %s\n", oldname);
       fprintf(stderr, "output = %s\n", newname);
       fprintf(stderr, "costmap = %s\n", costname);
       fprintf(stderr, "keyval = %d\n", keyval);
       fprintf(stderr, "step_length = %d\n", step_length);
       fprintf(stderr, "n = %d\n", n);
       fprintf(stderr, "energy = %0.2f\n", energy);
       fprintf(stderr, "Stats: ");
       for(i = 0; i < stat_count; i++) {
       fprintf(stderr, statmethods[stats[i]].name);
       } */

    /* allocate map buffers */
    map = (int *)G_malloc(sx * sy * sizeof(int));
    result = Rast_allocate_c_buf();
    costmap = (DCELL *)G_malloc(sx * sy * sizeof(DCELL));
    suitmap = (DCELL *)G_malloc(sx * sy * sizeof(DCELL));
    d_res = Rast_allocate_d_buf();
    cells = (Coords *)G_malloc(sx * sy * sizeof(Coords));
    fragments = (Coords **)G_malloc(sx * sy * sizeof(Coords *));
    fragments[0] = cells;

    /* open map */
    in_fd = Rast_open_old(oldname, oldmapset);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), oldname);

    /* read map */
    G_message("Reading map:");
    for (row = 0; row < sy; row++) {
        Rast_get_c_row(in_fd, result, row);
        for (col = 0; col < sx; col++) {
            if (result[col] == keyval)
                map[row * sx + col] = 1;
        }

        G_percent(row, sy, 2);
    }
    G_percent(1, 1, 2);

    /* close map */
    Rast_close(in_fd);

    /* test output */
    /*      G_message("map:\n");
       print_buffer(map, sx, sy); */

    /* if costmap specified, read costmap */
    if (costname != NULL) {
        /* open costmap */
        in_fd = Rast_open_old(costname, costmapset);
        if (in_fd < 0)
            G_fatal_error(_("Unable to open raster map <%s>"), costname);

        /* read costmap */
        G_message("Reading costmap:");
        for (row = 0; row < sy; row++) {
            Rast_get_d_row(in_fd, d_res, row);
            for (col = 0; col < sx; col++) {
                costmap[row * sx + col] = d_res[col];
            }

            G_percent(row, sy, 2);
        }
        G_percent(1, 1, 2);

        /* close costmap */
        Rast_close(in_fd);
    }
    else {
        /* if no costmap specified, fill costmap with 1 */
        for (i = 0; i < sx * sy; i++) {
            costmap[i] = 1;
        }
    }

    /* if suitability map specified, read it */
    if (suitname != NULL) {
        /* open suitability map */
        if ((in_fd = Rast_open_old(suitname, suitmapset)) < 0)
            G_fatal_error(_("Unable to open raster map <%s>"), suitname);

        /* read suitability map */
        G_message("Reading suitability map file:\n");
        for (row = 0; row < sy; row++) {
            Rast_get_d_row(in_fd, d_res, row);
            for (col = 0; col < sx; col++) {
                suitmap[row * sx + col] = d_res[col];
            }

            G_percent(row + 1, sy, 1);
        }

        /* close suitability map */
        Rast_close(in_fd);
    }
    else {
        /* if no suitability map specified, fill it with 100 */
        for (i = 0; i < sx * sy; i++) {
            suitmap[i] = 100;
        }
    }

    /* test output */
    /*      G_message("costmap:\n");
       print_d_buffer(costmap, sx, sy); */

    /* find fragments */
    fragcount = writeFragments(fragments, map, sy, sx, neighb_count);

    /* test output */
    /*      print_fragments(); */

    /* mark each fragment with its number */
    for (i = 0; i < sx * sy; i++) {
        map[i] = -1;
    }
    for (i = 0; i < fragcount; i++) {
        for (p = fragments[i]; p < fragments[i + 1]; p++) {
            map[p->y * sx + p->x] = i;
        }
    }

    /* test output */
    /*      print_buffer(map, sx, sy); */
    G_message("Performing search runs:");

    /* allocate space for patch immigrants */
    immigrants = (int *)G_malloc(fragcount * sizeof(int));
    migrants = (int *)G_malloc(fragcount * sizeof(int));
    migrants_succ = (int *)G_malloc(fragcount * sizeof(int));
    emigrants = (int *)G_malloc(fragcount * sizeof(int));
    lost = (int *)G_malloc(fragcount * sizeof(int));

    memset(immigrants, 0, fragcount * sizeof(int));
    memset(migrants, 0, fragcount * sizeof(int));
    memset(migrants_succ, 0, fragcount * sizeof(int));
    memset(emigrants, 0, fragcount * sizeof(int));
    memset(lost, 0, fragcount * sizeof(int));

    /* perform search */
    perform_search(map, costmap, n, fragcount, sx, sy);

    /* test output */
    /*G_message("Results:");
       for(j = 0; j < stat_count; j++) {
       G_message("%s: ", statmethods[stats[j]].name);
       for(i = 0; i < fragcount; i++) {
       fprintf(stderr, "frag%d: %0.2f ", i, values[j * fragcount + i]);
       }
       fprintf(stderr, "\n");
       }
       G_message(""); */

    G_message("Writing output...");

    /* set up progress display vaiables */
    out_progress = 0;
    out_max = sy * 7;

    /* write immigrants */

    /* open the new cellfile  */
    sprintf(outname, "%s_imi", newname);
    out_fd = Rast_open_new(outname, DCELL_TYPE);
    if (out_fd < 0) {
        G_fatal_error(_("can't create new cell file <%s> in mapset %s\n"),
                      outname, G_mapset());
        exit(EXIT_FAILURE);
    }

    /* write the output file */
    for (row = 0; row < sy; row++) {
        Rast_set_d_null_value(d_res, sx);

        for (i = 0; i < fragcount; i++) {
            for (p = fragments[i]; p < fragments[i + 1]; p++) {
                if (p->y == row) {
                    d_res[p->x] = immigrants[i];
                }
            }
        }

        Rast_put_d_row(out_fd, d_res);

        G_percent(++out_progress, out_max, 1);
    }

    /* close output */
    Rast_close(out_fd);

    /* write immigrants percentual */

    /* open the new cellfile  */
    sprintf(outname, "%s_imi_percent", newname);
    out_fd = Rast_open_new(outname, DCELL_TYPE);
    if (out_fd < 0) {
        G_fatal_error(_("can't create new cell file <%s> in mapset %s\n"),
                      outname, G_mapset());
        exit(EXIT_FAILURE);
    }

    /* count all imigrants */
    sum = 0;
    for (i = 0; i < fragcount; i++) {
        sum += immigrants[i];
    }

    /* write the output file */
    for (row = 0; row < sy; row++) {
        Rast_set_d_null_value(d_res, sx);

        for (i = 0; i < fragcount; i++) {
            for (p = fragments[i]; p < fragments[i + 1]; p++) {
                if (p->y == row) {
                    d_res[p->x] =
                        sum > 0 ? 100.0 * (DCELL)immigrants[i] / (DCELL)sum : 0;
                }
            }
        }

        Rast_put_d_row(out_fd, d_res);

        G_percent(++out_progress, out_max, 1);
    }

    /* close output */
    Rast_close(out_fd);

    /* write migrants */

    /* open the new cellfile  */
    sprintf(outname, "%s_mig", newname);
    out_fd = Rast_open_new(outname, DCELL_TYPE);
    if (out_fd < 0) {
        G_fatal_error(_("can't create new cell file <%s> in mapset %s\n"),
                      outname, G_mapset());
        exit(EXIT_FAILURE);
    }

    /* write the output file */
    for (row = 0; row < sy; row++) {
        Rast_set_d_null_value(d_res, sx);

        for (i = 0; i < fragcount; i++) {
            for (p = fragments[i]; p < fragments[i + 1]; p++) {
                if (p->y == row) {
                    d_res[p->x] = migrants[i];
                }
            }
        }

        Rast_put_d_row(out_fd, d_res);

        G_percent(++out_progress, out_max, 1);
    }

    /* close output */
    Rast_close(out_fd);

    /* write successful migrants */

    /* open the new cellfile  */
    sprintf(outname, "%s_mig_succ", newname);
    out_fd = Rast_open_new(outname, DCELL_TYPE);
    if (out_fd < 0) {
        G_fatal_error(_("can't create new cell file <%s> in mapset %s\n"),
                      outname, G_mapset());
        exit(EXIT_FAILURE);
    }

    /* write the output file */
    for (row = 0; row < sy; row++) {
        Rast_set_d_null_value(d_res, sx);

        for (i = 0; i < fragcount; i++) {
            for (p = fragments[i]; p < fragments[i + 1]; p++) {
                if (p->y == row) {
                    d_res[p->x] = migrants[i] > 0
                                      ? 100.0 * (DCELL)migrants_succ[i] /
                                            (DCELL)migrants[i]
                                      : 0;
                }
            }
        }

        Rast_put_d_row(out_fd, d_res);

        G_percent(++out_progress, out_max, 1);
    }

    /* close output */
    Rast_close(out_fd);

    /* write unsuccessful migrants */

    /* open the new cellfile  */
    sprintf(outname, "%s_mig_unsucc", newname);
    out_fd = Rast_open_new(outname, DCELL_TYPE);
    if (out_fd < 0) {
        G_fatal_error(_("can't create new cell file <%s> in mapset %s\n"),
                      outname, G_mapset());
        exit(EXIT_FAILURE);
    }

    /* write the output file */
    for (row = 0; row < sy; row++) {
        Rast_set_d_null_value(d_res, sx);

        for (i = 0; i < fragcount; i++) {
            for (p = fragments[i]; p < fragments[i + 1]; p++) {
                if (p->y == row) {
                    d_res[p->x] = migrants[i] > 0
                                      ? 100.0 - 100.0 *
                                                    (DCELL)migrants_succ[i] /
                                                    (DCELL)migrants[i]
                                      : 0;
                }
            }
        }

        Rast_put_d_row(out_fd, d_res);

        G_percent(++out_progress, out_max, 1);
    }

    /* close output */
    Rast_close(out_fd);

    /* write emigrants */

    /* open the new cellfile  */
    sprintf(outname, "%s_emi", newname);
    out_fd = Rast_open_new(outname, DCELL_TYPE);
    if (out_fd < 0) {
        G_fatal_error(_("can't create new cell file <%s> in mapset %s\n"),
                      outname, G_mapset());
        exit(EXIT_FAILURE);
    }

    /* write the output file */
    for (row = 0; row < sy; row++) {
        Rast_set_d_null_value(d_res, sx);

        for (i = 0; i < fragcount; i++) {
            for (p = fragments[i]; p < fragments[i + 1]; p++) {
                if (p->y == row) {
                    d_res[p->x] =
                        n > 0 ? 100.0 * (DCELL)emigrants[i] / (DCELL)n : 0;
                }
            }
        }

        Rast_put_d_row(out_fd, d_res);

        G_percent(++out_progress, out_max, 1);
    }

    /* close output */
    Rast_close(out_fd);

    if (!setback) {
        /* write lost */

        /* open the new cellfile  */
        sprintf(outname, "%s_lost", newname);
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] =
                            n > 0 ? 100.0 * (DCELL)lost[i] / (DCELL)n : 0;
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(++out_progress, out_max, 1);
        }

        /* close output */
        Rast_close(out_fd);
    }

    /* open ASCII-file or use stdout */
    if (parm.immi_matrix->answer) {
        if (strcmp(parm.immi_matrix->answer, "-") != 0) {
            if (!(out_fp = fopen(parm.immi_matrix->answer, "w"))) {
                G_fatal_error(_("Error creating file <%s>"),
                              parm.immi_matrix->answer);
            }
        }
        else {
            out_fp = stdout;
        }

        /* write data */
        for (i = 0; i < fragcount; i++) {
            for (j = 0; j < fragcount; j++) {
                fprintf(out_fp, "%d ", immi_matrix[i * fragcount + j]);
            }
            fprintf(out_fp, "\n");
        }

        /* close file */
        if (strcmp(parm.immi_matrix->answer, "-") != 0) {
            fclose(out_fp);
        }
    }

    /* open ASCII-file or use stdout */
    if (parm.mig_matrix->answer) {
        if (strcmp(parm.mig_matrix->answer, "-") != 0) {
            if (!(out_fp = fopen(parm.mig_matrix->answer, "w"))) {
                G_fatal_error(_("Error creating file <%s>"),
                              parm.mig_matrix->answer);
            }
        }
        else {
            out_fp = stdout;
        }

        /* write data */
        for (i = 0; i < fragcount; i++) {
            for (j = 0; j < fragcount; j++) {
                fprintf(out_fp, "%d ", mig_matrix[i * fragcount + j]);
            }
            fprintf(out_fp, "\n");
        }

        /* close file */
        if (strcmp(parm.mig_matrix->answer, "-") != 0) {
            fclose(out_fp);
        }
    }

    /* write binary immigrants matrix ASCII file */
    if (parm.binary_matrix->answer) {
        if (strcmp(parm.binary_matrix->answer, "-") != 0) {
            sprintf(outname, "%s_immi", parm.binary_matrix->answer);
            if (!(out_fp = fopen(outname, "w"))) {
                G_fatal_error(_("Error creating file <%s>"), outname);
            }
        }
        else {
            out_fp = stdout;
        }

        /* write data */
        for (i = 0; i < fragcount; i++) {
            /* calculate sum of all imigrants from patch i */
            int threshold_count;

            sum = 0;
            for (j = 0; j < fragcount; j++) {
                sum += immi_matrix[j * fragcount + i];
            }

            threshold_count = (int)(threshold * (double)sum) / 100;

            for (j = 0; j < fragcount; j++) {
                if (immi_matrix[i * fragcount + j] > threshold_count) {
                    fprintf(out_fp, "1 ");
                }
                else {
                    fprintf(out_fp, "0 ");
                }
            }
            fprintf(out_fp, "\n");
        }

        /* close file */
        if (strcmp(parm.binary_matrix->answer, "-") != 0) {
            fclose(out_fp);
        }
    }

    /* write binary immigrants matrix ASCII file */
    if (parm.binary_matrix->answer) {
        if (strcmp(parm.binary_matrix->answer, "-") != 0) {
            sprintf(outname, "%s_mig", parm.binary_matrix->answer);
            if (!(out_fp = fopen(outname, "w"))) {
                G_fatal_error(_("Error creating file <%s>"), outname);
            }
        }
        else {
            out_fp = stdout;
        }

        /* write data */
        for (i = 0; i < fragcount; i++) {
            /* calculate sum of all imigrants from patch i */
            int threshold_count;

            sum = 0;
            for (j = 0; j < fragcount; j++) {
                sum += mig_matrix[j * fragcount + i];
            }

            threshold_count = (int)(threshold * (double)sum) / 100;

            for (j = 0; j < fragcount; j++) {
                if (mig_matrix[i * fragcount + j] > threshold_count) {
                    fprintf(out_fp, "1 ");
                }
                else {
                    fprintf(out_fp, "0 ");
                }
            }
            fprintf(out_fp, "\n");
        }

        /* close file */
        if (strcmp(parm.binary_matrix->answer, "-") != 0) {
            fclose(out_fp);
        }
    }

    /* write diversity maps */
    if (flag.diversity->answer) {
        /* calculate diversity */
        DCELL *values = (DCELL *)G_malloc(fragcount * sizeof(DCELL));

        for (i = 0; i < fragcount; i++) {
            /* calculate sum of all imigrants in patch i */
            int threshold_count;
            DCELL value;

            sum = 0;
            for (j = 0; j < fragcount; j++) {
                sum += immi_matrix[j * fragcount + i];
            }

            /* calculate threshold count */
            threshold_count = (int)(threshold * (double)sum) / 100;

            value = 0;

            for (j = 0; j < fragcount; j++) {
                if (immi_matrix[j * fragcount + i] > threshold_count) {
                    value++;
                }
            }

            values[i] = value;
        }

        /* diversity */
        /* open the new cellfile  */
        sprintf(outname, "%s_%s_immi", newname, "diversity");
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = values[i];
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(row + 1, sy, 1);
        }

        /* close output */
        Rast_close(out_fd);

        /* diversity percentual */
        /* open the new cellfile  */
        sprintf(outname, "%s_%s_immi_percentual", newname, "diversity");
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] =
                            values[i] / (DCELL)(fragcount - 1) * 100.0;
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(row + 1, sy, 1);
        }

        /* close output */
        Rast_close(out_fd);
    }

    /* write antidiversity maps */
    if (flag.diversity->answer) {
        /* calculate antidiversity */
        DCELL *values = (DCELL *)G_malloc(fragcount * sizeof(DCELL));

        for (i = 0; i < fragcount; i++) {
            /* calculate sum of all imigrants from patch i */
            int threshold_count;
            DCELL value;

            sum = 0;
            for (j = 0; j < fragcount; j++) {
                sum += immi_matrix[i * fragcount + j];
            }

            /* calculate threshold count */
            threshold_count = (int)(threshold * (double)sum) / 100;

            value = 0;

            for (j = 0; j < fragcount; j++) {
                if (immi_matrix[i * fragcount + j] > threshold_count) {
                    value++;
                }
            }

            values[i] = value;
        }

        /* antidiversity */
        /* open the new cellfile  */
        sprintf(outname, "%s_%s", newname, "antidiversity");
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = values[i];
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(row + 1, sy, 1);
        }

        /* close output */
        Rast_close(out_fd);

        /* antidiversity percentual */
        /* open the new cellfile  */
        sprintf(outname, "%s_%s", newname, "antidiversity");
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] =
                            values[i] / (DCELL)(fragcount - 1) * 100.0;
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(row + 1, sy, 1);
        }

        /* close output */
        Rast_close(out_fd);
    }

    /* write diversity map for migrants */
    if (flag.diversity->answer) {
        /* open the new cellfile  */
        sprintf(outname, "%s_%s_mig", newname, "diversity");
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                /* calculate sum of all migrants from patch i */
                int threshold_count;
                DCELL value;

                sum = 0;
                for (j = 0; j < fragcount; j++) {
                    sum += mig_matrix[j * fragcount + i];
                }

                /* calculate threshold count */
                threshold_count = (int)(threshold * (double)sum) / 100;

                value = 0;

                for (j = 0; j < fragcount; j++) {
                    if (mig_matrix[j * fragcount + i] > threshold_count) {
                        value++;
                    }
                }

                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = value;
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(row + 1, sy, 1);
        }

        /* close output */
        Rast_close(out_fd);
    }

    /* write indices for immigrants */
    if (flag.indices->answer) {
        DCELL *values;

        /* SHANNON */
        /* open the new cellfile  */
        sprintf(outname, "%s_%s", newname, "shannon");
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        fprintf(stderr, "Immigrant matrix:\n");
        for (i = 0; i < fragcount; i++) {
            for (j = 0; j < fragcount; j++) {
                fprintf(stderr, " %d", immi_matrix[j * fragcount + i]);
            }
            fprintf(stderr, "\n");
        }
        fprintf(stderr, "\n");

        /* calculate indices */
        values = (DCELL *)G_malloc(fragcount * sizeof(DCELL));

        for (i = 0; i < fragcount; i++) {
            int N = 0;
            DCELL dsum = 0.0;

            for (j = 0; j < fragcount; j++) {
                int immi = immi_matrix[i * fragcount + j];

                if (immi > 0) {
                    N += immi;
                    dsum += (DCELL)immi * log((DCELL)immi);
                }
            }

            values[i] = log((DCELL)N) - dsum / (DCELL)N;
        }

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = values[i];
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(row + 1, sy, 1);
        }

        /* close output */
        Rast_close(out_fd);

        /* SIMPSON */
        /* open the new cellfile  */
        sprintf(outname, "%s_%s", newname, "simpson");
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* calculate indices */
        for (i = 0; i < fragcount; i++) {
            int N = 0;

            sum = 0;

            for (j = 0; j < fragcount; j++) {
                int immi = immi_matrix[j * fragcount + i];

                N += immi;
                sum += immi * (immi - 1);
            }

            values[i] = (DCELL)sum / (DCELL)(N * (N - 1));
        }

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = values[i];
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(row + 1, sy, 1);
        }

        G_free(values);

        /* close output */
        Rast_close(out_fd);
    }

    /* free allocated resources */
    G_free(map);
    G_free(costmap);
    G_free(cells);
    G_free(fragments);
    G_free(immigrants);
    G_free(migrants);
    G_free(migrants_succ);
    G_free(emigrants);
    G_free(lost);
    G_free(immi_matrix);
    G_free(mig_matrix);

    exit(EXIT_SUCCESS);
}
