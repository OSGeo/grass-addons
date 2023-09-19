/*****************************************************************************
 *
 * MODULE:       r.pi.searchtime
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Individual-based dispersal model for connectivity analysis -
 *               time-based
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

struct statmethod {
    f_statmethod *method; /* routine to compute new value */
    char *name;           /* method name */
    char *text;           /* menu display - full description */
    char *suffix;         /* output suffix */
};

static struct statmethod statmethods[] = {
    {average, "average", "average of values", "avg"},
    {variance, "variance", "variance of values", "var"},
    {std_deviat, "standard deviation", "standard deviation of values", "dev"},
    {median, "median", "median of values", "med"},
    {min, "min", "minimum of values", "min"},
    {max, "max", "maximum of values", "max"},
    {0, 0, 0, 0}};

int main(int argc, char *argv[])
{
    /* input */
    char *oldname;
    const char *oldmapset;

    /* costmap */
    char *costname;
    const char *costmapset;

    /* in and out file pointers */
    int in_fd, out_fd;
    FILE *out_fp;

    /* parameters */
    int stats[GNAME_MAX];
    f_statmethod **methods;
    int stat_count;
    DCELL threshold;

    /* maps */
    int *map;
    DCELL *costmap;

    /* helper variables */
    int row, col;
    int sx, sy;
    CELL *result;
    DCELL *d_res;
    DCELL *values;
    int nbr_count;
    int i, j;
    Coords *p;
    char *str;
    int method;
    char outname[GNAME_MAX];
    int fragcount;
    int n;

    struct GModule *module;
    struct {
        struct Option *input, *costmap, *output, *out_immi;
        struct Option *keyval, *step_length, *step_range, *perception,
            *multiplicator, *n;
        struct Option *percent, *stats, *maxsteps, *out_freq, *immi_matrix,
            *binary_matrix;
        struct Option *threshold, *title;
    } parm;
    struct {
        struct Flag *adjacent, *cost, *diversity, *indices;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("landscape structure analysis"));
    G_add_keyword(_("connectivity analysis"));
    module->description = _("Individual-based dispersal model for connectivity "
                            "analysis (time-based)");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.costmap = G_define_option();
    parm.costmap->key = "suitability";
    parm.costmap->type = TYPE_STRING;
    parm.costmap->required = NO;
    parm.costmap->gisprompt = "old,cell,raster";
    parm.costmap->description = _("Name of the costmap with values from 0-100");
    parm.costmap->guisection = "Optional";

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

    parm.binary_matrix = G_define_option();
    parm.binary_matrix->key = "binary_matrix";
    parm.binary_matrix->type = TYPE_STRING;
    parm.binary_matrix->required = NO;
    parm.binary_matrix->gisprompt = "new_file,file,output";
    parm.binary_matrix->description =
        _("Name for binary immigrants matrix ASCII-file");
    parm.binary_matrix->guisection = "Optional";

    parm.threshold = G_define_option();
    parm.threshold->key = "threshold";
    parm.threshold->type = TYPE_DOUBLE;
    parm.threshold->required = NO;
    parm.threshold->description =
        _("Percentage of individuals which must have immigrated"
          " successfully to be considered for the binary immigrants matrix");
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

    parm.percent = G_define_option();
    parm.percent->key = "percent";
    parm.percent->type = TYPE_DOUBLE;
    parm.percent->required = YES;
    parm.percent->description =
        _("Percentage of individuals which must have arrived successfully"
          " to stop the model-run");
    parm.percent->guisection = "Required";

    parm.stats = G_define_option();
    parm.stats->key = "stats";
    parm.stats->type = TYPE_STRING;
    parm.stats->required = YES;
    parm.stats->multiple = YES;
    str = G_malloc(1024);
    for (n = 0; statmethods[n].name; n++) {
        if (n)
            strcat(str, ",");
        else
            *str = 0;
        strcat(str, statmethods[n].name);
    }
    parm.stats->options = str;
    parm.stats->description = _("Statistical method to perform on the values");
    parm.stats->guisection = "Required";

    parm.maxsteps = G_define_option();
    parm.maxsteps->key = "maxsteps";
    parm.maxsteps->type = TYPE_INTEGER;
    parm.maxsteps->required = NO;
    parm.maxsteps->description = _("Maximum steps for each individual");
    parm.maxsteps->guisection = "Optional";

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

    flag.cost = G_define_flag();
    flag.cost->key = 'c';
    flag.cost->description =
        _("Include cost of the path in the calculation of steps");

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

    /* test input files existance */
    oldmapset = G_find_raster2(oldname, "");
    if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

    /* get name of costmap */
    costname = parm.costmap->answer;
    costmapset = NULL;

    /* test costmap existance */
    if (costname && (costmapset = G_find_raster2(costname, "")) == NULL)
        G_fatal_error(_("Raster map <%s> not found"), costname);
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

    /* get percent */
    sscanf(parm.percent->answer, "%lf", &percent);

    /* get threshold */
    if (parm.threshold->answer) {
        sscanf(parm.threshold->answer, "%lf", &threshold);
    }
    else {
        threshold = 0.0;
    }

    /* get number of cell-neighbors */
    nbr_count = flag.adjacent->answer ? 8 : 4;

    /* get include_cost */
    include_cost = flag.cost->answer;

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), newname);

    /* check if the immigrants file name is correct */
    iminame = parm.out_immi->answer;
    if (iminame && G_legal_filename(iminame) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), iminame);
    imimapset = G_mapset();

    /* get size */
    sx = Rast_window_cols();
    sy = Rast_window_rows();

    /* get maxsteps */
    if (parm.maxsteps->answer != NULL) {
        sscanf(parm.maxsteps->answer, "%d", &maxsteps);
    }
    else {
        maxsteps = 10 * sqrt(sx * sx + sy * sy) / step_length;
    }

    /* get out_freq */
    if (parm.out_freq->answer != NULL) {
        sscanf(parm.out_freq->answer, "%d", &out_freq);
    }
    else {
        out_freq = 0;
    }

    /* scan all statmethod answers */
    stat_count = 0;
    while (parm.stats->answers[stat_count] != NULL) {
        /* get actual method */
        for (method = 0; (str = statmethods[method].name); method++)
            if (strcmp(str, parm.stats->answers[stat_count]) == 0)
                break;
        if (!str) {
            G_warning(_("<%s=%s> unknown %s"), parm.stats->key,
                      parm.stats->answers[stat_count], parm.stats->key);
            G_usage();
            exit(EXIT_FAILURE);
        }

        stats[stat_count] = method;

        stat_count++;
    }

    /* test output */
    /*      fprintf(stderr, "TEST OUTPUT : \n");
       fprintf(stderr, "input = %s\n", oldname);
       fprintf(stderr, "output = %s\n", newname);
       fprintf(stderr, "costmap = %s\n", costname);
       fprintf(stderr, "keyval = %d\n", keyval);
       fprintf(stderr, "step_length = %d\n", step_length);
       fprintf(stderr, "n = %d\n", n);
       fprintf(stderr, "percent = %0.2f\n", percent);
       fprintf(stderr, "maxsteps = %d\n", maxsteps);
       fprintf(stderr, "Stats: ");
       for(i = 0; i < stat_count; i++) {
       fprintf(stderr, statmethods[stats[i]].name);
       } */

    /* allocate map buffers */
    map = (int *)G_malloc(sx * sy * sizeof(int));
    result = Rast_allocate_c_buf();
    costmap = (DCELL *)G_malloc(sx * sy * sizeof(DCELL));
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
        /* if no costmap specified, fill costmap with 100 */
        for (i = 0; i < sx * sy; i++) {
            costmap[i] = 100;
        }
    }

    /* test output */
    /*      G_message("costmap:\n");
       print_d_buffer(costmap, sx, sy); */

    /* find fragments */
    fragcount = writeFragments(fragments, map, sy, sx, nbr_count);

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
    patch_imi = (int *)G_malloc(fragcount * sizeof(int));

    /* fill methods array */
    methods = (f_statmethod **)G_malloc(stat_count * sizeof(f_statmethod *));
    for (method = 0; method < stat_count; method++) {
        methods[method] = statmethods[stats[method]].method;
    }

    /* perform search */
    values = (DCELL *)G_malloc(fragcount * stat_count * sizeof(DCELL));
    perform_search(values, map, costmap, methods, stat_count, n, fragcount, sx,
                   sy);

    /* test output */
    G_message("Results:");
    for (j = 0; j < stat_count; j++) {
        G_message("%s: ", statmethods[stats[j]].name);
        for (i = 0; i < fragcount; i++) {
            fprintf(stderr, "frag%d: %0.2f ", i, values[j * fragcount + i]);
        }
        fprintf(stderr, "\n");
    }
    G_message(" ");

    G_message("Writing output...");
    for (method = 0; method < stat_count; method++) {

        /* open the new cellfile  */
        sprintf(outname, "%s_%s", newname, statmethods[stats[method]].suffix);
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = values[method * fragcount + i];
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(method * sy + row + 1, sy * stat_count, 1);
        }

        /* close output */
        Rast_close(out_fd);
    }

    /* open the new cellfile  */
    if (iminame) {
        out_fd = Rast_open_new(iminame, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), iminame);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = patch_imi[i];
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(row, sy, 2);
        }

        G_percent(100, 100, 2);

        /* close output */
        Rast_close(out_fd);
    }

    /* write immigrants matrix ASCII file */
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

    /* write binary immigrants matrix ASCII file */
    if (parm.binary_matrix->answer) {
        if (strcmp(parm.binary_matrix->answer, "-") != 0) {
            if (!(out_fp = fopen(parm.binary_matrix->answer, "w"))) {
                G_fatal_error(_("Error creating file <%s>"),
                              parm.binary_matrix->answer);
            }
        }
        else {
            out_fp = stdout;
        }

        /* write data */
        for (i = 0; i < fragcount; i++) {
            /* calculate sum of all imigrants from patch i */
            int sum = 0;
            int threshold_count;

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

    /* write diversity maps */
    if (flag.diversity->answer) {
        /* calculate diversity */
        DCELL *valuest = (DCELL *)G_malloc(fragcount * sizeof(DCELL));

        for (i = 0; i < fragcount; i++) {
            /* calculate sum of all imigrants in patch i */
            int sum = 0;
            int threshold_count;
            DCELL value = 0;

            for (j = 0; j < fragcount; j++) {
                sum += immi_matrix[j * fragcount + i];
            }

            /* calculate threshold count */
            threshold_count = (int)(threshold * (double)sum) / 100;

            /* count patches with immigrant count exceeding threshold */
            for (j = 0; j < fragcount; j++) {
                if (immi_matrix[j * fragcount + i] > threshold_count) {
                    value++;
                }
            }

            valuest[i] = value;
        }

        /* antidiversity */
        /* open the new cellfile  */
        sprintf(outname, "%s_%s", newname, "diversity");
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = valuest[i];
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
        sprintf(outname, "%s_%s_percent", newname, "diversity");
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
                            valuest[i] / (DCELL)(fragcount - 1) * 100.0;
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
        DCELL *valuest = (DCELL *)G_malloc(fragcount * sizeof(DCELL));

        for (i = 0; i < fragcount; i++) {
            /* calculate sum of all imigrants from patch i */
            int sum = 0;
            int threshold_count;
            DCELL value = 0;

            for (j = 0; j < fragcount; j++) {
                sum += immi_matrix[i * fragcount + j];
            }

            /* calculate threshold count */
            threshold_count = (int)(threshold * (double)sum) / 100;

            /* count all patches with emigrant count exceeding threshold */
            for (j = 0; j < fragcount; j++) {
                if (immi_matrix[i * fragcount + j] > threshold_count) {
                    value++;
                }
            }

            valuest[i] = value;
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
                        d_res[p->x] = valuest[i];
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
        sprintf(outname, "%s_%s_percent", newname, "antidiversity");
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
                            valuest[i] / (DCELL)(fragcount - 1) * 100.0;
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
        DCELL *valuest;

        /* SHANNON */
        /* open the new cellfile  */
        sprintf(outname, "%s_%s", newname, "shannon");
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* calculate indices */
        valuest = (DCELL *)G_malloc(fragcount * sizeof(DCELL));

        for (i = 0; i < fragcount; i++) {
            int N = 0;
            DCELL sum = 0.0;

            for (j = 0; j < fragcount; j++) {
                int immi = immi_matrix[j * fragcount + i];

                if (immi > 0) {
                    N += immi;
                    sum += (DCELL)immi * log((DCELL)immi);
                }
            }

            valuest[i] = log((DCELL)N) - sum / (DCELL)N;
        }

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = valuest[i];
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
            int sum = 0;

            for (j = 0; j < fragcount; j++) {
                int immi = immi_matrix[j * fragcount + i];

                N += immi;
                sum += immi * (immi - 1);
            }

            valuest[i] = (DCELL)sum / (DCELL)(N * (N - 1));
        }

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (i = 0; i < fragcount; i++) {
                for (p = fragments[i]; p < fragments[i + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = valuest[i];
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(row + 1, sy, 1);
        }

        G_free(valuest);

        /* close output */
        Rast_close(out_fd);
    }

    /* free allocated resources */
    G_free(map);
    G_free(costmap);
    G_free(cells);
    G_free(fragments);
    G_free(patch_imi);

    exit(EXIT_SUCCESS);
}
