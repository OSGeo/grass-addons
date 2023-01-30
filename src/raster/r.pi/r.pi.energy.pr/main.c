/*
 ****************************************************************************
 *
 * MODULE:       r.pi.energy.pr
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Individual-based dispersal model for connectivity analysis -
 *               energy-based - iterative removal of patches for patch
 *               relevance analysis
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

    /* suitability map */
    char *suitname;
    const char *suitmapset;

    /* in and out file pointers */
    int in_fd, out_fd;

    /* maps */
    int *map;
    DCELL *costmap;
    DCELL *suitmap;

    /* parameters */
    int stats[GNAME_MAX];
    int stat_count;
    int percentual;
    int remove_indi;
    int seed;

    /* helper variables */
    int row, col;
    int sx, sy;
    CELL *result;
    DCELL *d_res;
    int neighb_count;
    int i;
    Coords *p;
    char *str;
    int method;
    int out_progress, out_max;
    int frag;
    int fragcount;
    int n;

    int *dif_immi;
    int *dif_mig;
    int *dif_mig_succ;
    int *dif_emi;
    int *dif_lost;

    DCELL *out_immi;
    DCELL *out_mig;
    DCELL *out_mig_succ;
    DCELL *out_emi;
    DCELL *out_lost;

    DCELL *dummy;
    DCELL *ref;

    struct GModule *module;
    struct {
        struct Option *input, *costmap, *suitability, *output;
        struct Option *keyval, *step_length, *perception, *multiplicator, *n;
        struct Option *energy, *percent, *stats, *out_freq, *seed;
        struct Option *title;
    } parm;
    struct {
        struct Flag *adjacent, *setback;
        struct Flag *percentual, *remove_indi;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    module->description =
        _("Individual-based dispersal model for connectivity analysis (energy "
          "based) using iterative patch removal.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.costmap = G_define_option();
    parm.costmap->key = "costmap";
    parm.costmap->type = TYPE_STRING;
    parm.costmap->required = NO;
    parm.costmap->gisprompt = "old,cell,raster";
    parm.costmap->guisection = "Optional";
    parm.costmap->description = _("Name of the costmap");

    parm.suitability = G_define_option();
    parm.suitability->key = "suitability";
    parm.suitability->type = TYPE_STRING;
    parm.suitability->required = NO;
    parm.suitability->gisprompt = "old,cell,raster";
    parm.suitability->guisection = "Optional";
    parm.suitability->description =
        _("Name of the suitability raster with values from 0-100");

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->guisection = "Required";
    parm.keyval->description = _("Category value of the patches");

    parm.step_length = G_define_option();
    parm.step_length->key = "step_length";
    parm.step_length->type = TYPE_INTEGER;
    parm.step_length->required = YES;
    parm.step_length->guisection = "Required";
    parm.step_length->description =
        _("Length of a single step measured in pixels");

    parm.perception = G_define_option();
    parm.perception->key = "perception";
    parm.perception->type = TYPE_INTEGER;
    parm.perception->required = NO;
    parm.perception->guisection = "Optional";
    parm.perception->description = _("Perception range");

    parm.multiplicator = G_define_option();
    parm.multiplicator->key = "multiplicator";
    parm.multiplicator->type = TYPE_DOUBLE;
    parm.multiplicator->required = NO;
    parm.multiplicator->guisection = "Optional";
    parm.multiplicator->description = _("Attractivity of patches [1-inf]");

    parm.n = G_define_option();
    parm.n->key = "n";
    parm.n->type = TYPE_INTEGER;
    parm.n->required = YES;
    parm.n->guisection = "Required";
    parm.n->description = _("Number of individuals");

    parm.energy = G_define_option();
    parm.energy->key = "energy";
    parm.energy->type = TYPE_DOUBLE;
    parm.energy->required = YES;
    parm.energy->guisection = "Required";
    parm.energy->description = _("Initial energy of the individuals");

    parm.percent = G_define_option();
    parm.percent->key = "percent";
    parm.percent->type = TYPE_DOUBLE;
    parm.percent->required = YES;
    parm.percent->guisection = "Required";
    parm.percent->description =
        _("Percentage of finished individuals desired before simulation ends");

    parm.stats = G_define_option();
    parm.stats->key = "stats";
    parm.stats->type = TYPE_STRING;
    parm.stats->required = YES;
    parm.stats->multiple = YES;
    str = G_malloc(1024);
    for (method = 0; statmethods[method].name; method++) {
        if (method)
            strcat(str, ",");
        else
            *str = 0;
        strcat(str, statmethods[method].name);
    }
    parm.stats->options = str;
    parm.stats->description = _(
        "Statistical method to perform on the pathlengths of the individuals");
    parm.stats->guisection = _("Required");

    parm.out_freq = G_define_option();
    parm.out_freq->key = "out_freq";
    parm.out_freq->type = TYPE_INTEGER;
    parm.out_freq->required = NO;
    parm.out_freq->guisection = "Optional";
    parm.out_freq->description =
        _("Output an intermediate state of simulation each [out_freq] steps");

    parm.seed = G_define_option();
    parm.seed->key = "seed";
    parm.seed->type = TYPE_INTEGER;
    parm.seed->required = NO;
    parm.seed->guisection = "Optional";
    parm.seed->description = _("Seed for random number generator");

    parm.title = G_define_option();
    parm.title->key = "title";
    parm.title->key_desc = "\"phrase\"";
    parm.title->type = TYPE_STRING;
    parm.title->required = NO;
    parm.title->guisection = "Optional";
    parm.title->description = _("Title for resultant raster map");

    flag.adjacent = G_define_flag();
    flag.adjacent->key = 'a';
    flag.adjacent->guisection = "Required";
    flag.adjacent->description =
        _("Set for 8 cell-neighbors. 4 cell-neighbors are default");

    flag.setback = G_define_flag();
    flag.setback->key = 'b';
    flag.setback->guisection = "Required";
    flag.setback->description =
        _("Set if individuals should be set back after leaving area");

    flag.remove_indi = G_define_flag();
    flag.remove_indi->key = 'r';
    flag.remove_indi->guisection = "Required";
    flag.remove_indi->description =
        _("Set to remove individuals which start in the deleted patch");

    flag.percentual = G_define_flag();
    flag.percentual->key = 'p';
    flag.percentual->guisection = "Required";
    flag.percentual->description = _("Set to output values as percentual of "
                                     "the value from the reference run");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* initialize random generator */
    if (parm.seed->answer) {
        sscanf(parm.seed->answer, "%d", &seed);
    }
    else {
        seed = time(NULL);
    }
    srand(seed);

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

    /* test suitmap existance */
    if (suitname && (suitmapset = G_find_raster2(suitname, "")) == NULL)
        G_fatal_error(_("Raster map <%s> not found"), suitname);

    /* get keyval */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get step_length */
    sscanf(parm.step_length->answer, "%d", &step_length);

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

    remove_indi = flag.remove_indi->answer;
    percentual = flag.percentual->answer;

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
       }
       fprintf(stderr, "\n"); */

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
        in_fd = Rast_open_old(suitname, suitmapset);
        if (in_fd < 0)
            G_fatal_error(_("Unable to open raster map <%s>"), suitname);

        /* read suitability map */
        G_message("Reading suitability map file:");
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

    /* allocate arrays */
    immigrants = (int *)G_malloc(fragcount * sizeof(int));
    migrants = (int *)G_malloc(fragcount * sizeof(int));
    migrants_succ = (int *)G_malloc(fragcount * sizeof(int));
    emigrants = (int *)G_malloc(fragcount * sizeof(int));
    lost = (int *)G_malloc(fragcount * sizeof(int));
    deleted_arr = (char *)G_malloc(fragcount * sizeof(char));

    memset(deleted_arr, 0, fragcount * sizeof(char));

    /* allocate difference arrays */
    dif_immi = (int *)G_malloc((fragcount + 1) * fragcount * sizeof(int));
    dif_mig = (int *)G_malloc((fragcount + 1) * fragcount * sizeof(int));
    dif_mig_succ = (int *)G_malloc((fragcount + 1) * fragcount * sizeof(int));
    dif_emi = (int *)G_malloc((fragcount + 1) * fragcount * sizeof(int));
    dif_lost = (int *)G_malloc((fragcount + 1) * fragcount * sizeof(int));

    /* perform first reference search run */
    perform_search(map, costmap, remove_indi, n, fragcount, sx, sy);

    /* test output */
    /* G_message("Reference run:");
       print_int_array("immigrants", immigrants, fragcount);
       print_int_array("migrants", migrants, fragcount);
       print_int_array("migrants successful", migrants_succ, fragcount);
       print_int_array("emigrants", emigrants, fragcount);
       print_int_array("lost", lost, fragcount);
       G_message(""); */

    /* copy values */
    memcpy(dif_immi, immigrants, fragcount * sizeof(int));
    memcpy(dif_mig, migrants, fragcount * sizeof(int));
    memcpy(dif_mig_succ, migrants_succ, fragcount * sizeof(int));
    memcpy(dif_emi, emigrants, fragcount * sizeof(int));
    memcpy(dif_lost, lost, fragcount * sizeof(int));

    /* perform test runs */
    for (frag = 0; frag < fragcount; frag++) {
        deleted_arr[frag] = 1;
        perform_search(map, costmap, remove_indi, n, fragcount, sx, sy);
        deleted_arr[frag] = 0;

        /* G_message("Frag %d deleted:", frag);
           print_int_array("immigrants", immigrants, fragcount);
           print_int_array("migrants", migrants, fragcount);
           print_int_array("migrants successful", migrants_succ, fragcount);
           print_int_array("emigrants", emigrants, fragcount);
           print_int_array("lost", lost, fragcount);
           G_message(""); */

        /* calculate differences */
        for (i = 0; i < fragcount; i++) {
            dif_immi[(frag + 1) * fragcount + i] = immigrants[i] - dif_immi[i];
            dif_mig[(frag + 1) * fragcount + i] = migrants[i];
            dif_mig_succ[(frag + 1) * fragcount + i] = migrants_succ[i];
            dif_emi[(frag + 1) * fragcount + i] = emigrants[i] - dif_emi[i];
            dif_lost[(frag + 1) * fragcount + i] = lost[i] - dif_lost[i];
        }
    }

    /* allolcate output arrays */
    out_immi = (DCELL *)G_malloc(stat_count * fragcount * sizeof(DCELL));
    out_mig = (DCELL *)G_malloc(stat_count * fragcount * sizeof(DCELL));
    out_mig_succ = (DCELL *)G_malloc(stat_count * fragcount * sizeof(DCELL));
    out_emi = (DCELL *)G_malloc(stat_count * fragcount * sizeof(DCELL));
    out_lost = (DCELL *)G_malloc(stat_count * fragcount * sizeof(DCELL));
    dummy = (DCELL *)G_malloc(5 * (fragcount - 1) * sizeof(DCELL));
    ref = (DCELL *)G_malloc(5 * (fragcount - 1) * sizeof(DCELL));

    /* calculate output results */
    for (frag = 0; frag < fragcount; frag++) {
        int offset = (frag + 1) * fragcount;
        int index = 0;

        for (i = 0; i < fragcount; i++) {
            if (i != frag) {
                dummy[index] = dif_immi[offset + i];
                dummy[fragcount - 1 + index] = dif_mig[offset + i] - dif_mig[i];
                dummy[2 * (fragcount - 1) + index] =
                    dif_mig[offset + i] > 0
                        ? 100.0 * ((DCELL)dif_mig_succ[offset + i] /
                                       (DCELL)dif_mig[offset + i] -
                                   (DCELL)dif_mig_succ[i] / (DCELL)dif_mig[i])
                        : 0;
                dummy[3 * (fragcount - 1) + index] =
                    n > 0 ? 100.0 * (DCELL)dif_emi[offset + i] / (DCELL)n : 0;
                dummy[4 * (fragcount - 1) + index] =
                    n > 0 ? 100.0 * (DCELL)dif_lost[offset + i] / (DCELL)n : 0;

                ref[index] = dif_immi[i];
                ref[fragcount - 1 + index] = dif_mig[i];
                ref[2 * (fragcount - 1) + index] =
                    dif_mig[i] > 0
                        ? 100.0 * (DCELL)dif_mig_succ[i] / (DCELL)dif_mig[i]
                        : 0;
                ref[3 * (fragcount - 1) + index] =
                    n > 0 ? 100.0 * (DCELL)dif_emi[i] / (DCELL)n : 0;
                ref[4 * (fragcount - 1) + index] =
                    n > 0 ? 100.0 * (DCELL)dif_lost[i] / (DCELL)n : 0;
                index++;
            }
        }
        for (method = 0; method < stat_count; method++) {
            f_statmethod *func = statmethods[stats[method]].method;

            index = method * fragcount + frag;

            out_immi[index] = func(dummy, fragcount - 1);
            out_mig[index] = func(dummy + fragcount - 1, fragcount - 1);
            out_mig_succ[index] =
                func(dummy + 2 * (fragcount - 1), fragcount - 1);
            out_emi[index] = func(dummy + 3 * (fragcount - 1), fragcount - 1);
            out_lost[index] = func(dummy + 4 * (fragcount - 1), fragcount - 1);

            if (percentual) {
                DCELL ref_immi = func(ref, fragcount - 1);
                DCELL ref_mig = func(ref + fragcount - 1, fragcount - 1);
                DCELL ref_mig_succ =
                    func(ref + 2 * (fragcount - 1), fragcount - 1);
                DCELL ref_emi = func(ref + 3 * (fragcount - 1), fragcount - 1);
                DCELL ref_lost = func(ref + 4 * (fragcount - 1), fragcount - 1);

                out_immi[index] = out_immi[index] * 100.0 / ref_immi;
                out_mig[index] = out_mig[index] * 100.0 / ref_mig;
                out_mig_succ[index] =
                    out_mig_succ[index] * 100.0 / ref_mig_succ;
                out_emi[index] = out_emi[index] * 100.0 / ref_emi;
                out_lost[index] = out_lost[index] * 100.0 / ref_lost;
            }
        }
    }

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
    out_max = stat_count * sy * (setback ? 4 : 5);

    /* write immigrants */

    for (method = 0; method < stat_count; method++) {
        /* open the new cellfile  */
        sprintf(outname, "%s_imi_%s", newname,
                statmethods[stats[method]].suffix);
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (frag = 0; frag < fragcount; frag++) {
                for (p = fragments[frag]; p < fragments[frag + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = out_immi[method * fragcount + frag];
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(++out_progress, out_max, 1);
        }

        /* close output */
        Rast_close(out_fd);
    }

    /* write migrants */

    for (method = 0; method < stat_count; method++) {
        /* open the new cellfile  */
        sprintf(outname, "%s_mig_%s", newname,
                statmethods[stats[method]].suffix);
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (frag = 0; frag < fragcount; frag++) {
                for (p = fragments[frag]; p < fragments[frag + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = out_mig[method * fragcount + frag];
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(++out_progress, out_max, 1);
        }

        /* close output */
        Rast_close(out_fd);
    }

    /* write successful migrants */

    for (method = 0; method < stat_count; method++) {
        /* open the new cellfile  */
        sprintf(outname, "%s_mig_succ_%s", newname,
                statmethods[stats[method]].suffix);
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (frag = 0; frag < fragcount; frag++) {
                for (p = fragments[frag]; p < fragments[frag + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = out_mig_succ[method * fragcount + frag];
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(++out_progress, out_max, 1);
        }

        /* close output */
        Rast_close(out_fd);
    }

    /* write emigrants */

    for (method = 0; method < stat_count; method++) {
        /* open the new cellfile  */
        sprintf(outname, "%s_emi_%s", newname,
                statmethods[stats[method]].suffix);
        out_fd = Rast_open_new(outname, DCELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), outname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_d_null_value(d_res, sx);

            for (frag = 0; frag < fragcount; frag++) {
                for (p = fragments[frag]; p < fragments[frag + 1]; p++) {
                    if (p->y == row) {
                        d_res[p->x] = out_emi[method * fragcount + frag];
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);

            G_percent(++out_progress, out_max, 1);
        }

        /* close output */
        Rast_close(out_fd);
    }

    if (!setback) {
        /* write lost */

        for (method = 0; method < stat_count; method++) {
            /* open the new cellfile  */
            sprintf(outname, "%s_lost_%s", newname,
                    statmethods[stats[method]].suffix);
            out_fd = Rast_open_new(outname, DCELL_TYPE);
            if (out_fd < 0)
                G_fatal_error(_("Cannot create raster map <%s>"), outname);

            /* write the output file */
            for (row = 0; row < sy; row++) {
                Rast_set_d_null_value(d_res, sx);

                for (frag = 0; frag < fragcount; frag++) {
                    for (p = fragments[frag]; p < fragments[frag + 1]; p++) {
                        if (p->y == row) {
                            d_res[p->x] = out_lost[method * fragcount + frag];
                        }
                    }
                }

                Rast_put_d_row(out_fd, d_res);

                G_percent(++out_progress, out_max, 1);
            }

            /* close output */
            Rast_close(out_fd);
        }
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
    G_free(dif_immi);
    G_free(dif_mig);
    G_free(dif_mig_succ);
    G_free(dif_emi);
    G_free(dif_lost);
    G_free(out_immi);
    G_free(out_mig);
    G_free(out_mig_succ);
    G_free(out_emi);
    G_free(out_lost);

    exit(EXIT_SUCCESS);
}
