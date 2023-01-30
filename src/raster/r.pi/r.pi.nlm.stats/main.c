/*
 ****************************************************************************
 *
 * MODULE:       r.pi.nlm.stats
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Generation of Neutral Landscapes and statistical analysis
 *                               of fragmentation indices
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

struct method {
    f_func *method;
    char *name;
    char *text;
};

struct statmethod {
    f_statmethod *method; /* routine to compute new value */
    char *name;           /* method name */
    char *text;           /* menu display - full description */
};

static struct method methodlist[] = {
    {f_nearest_dist, "distance", "distance to the patch"},
    {f_area, "area", "area of the patch"},
    {f_perim, "perimeter", "perimeter of the patch"},
    {f_shapeindex, "shapeindex", "shapeindex of the patch"},
    {f_frac_dim, "fractal", "fractal index of the patch"},
    {0, 0, 0}};

static struct statmethod statmethodlist[] = {
    {average, "average", "average of values"},
    {mode, "mode", "mode of values"},
    {median, "median", "median of values"},
    {variance, "variance", "variance of values"},
    {min, "min", "minimum of values"},
    {max, "max", "maximum of values"},
    {0, 0, 0}};

int main(int argc, char *argv[])
{
    /* input */
    char *oldname;
    const char *oldmapset;

    /* in and out file pointers */
    int in_fd;    /* raster - input */
    FILE *out_fp; /* ASCII - output */
    FILE *out_rl; /* ASCII - output for real landscape */

    /* parameters */
    int n;
    int keyval, nullval;
    int pixel_count;
    int rand_seed;
    int methods[GNAME_MAX];
    int statmethods[GNAME_MAX];
    int nbr_count;

    /* helper variables */
    int i, j;
    int row, col;
    CELL *result;
    int pos;

    int *real_landscape;
    DCELL *real_values;
    DCELL *res_values;
    int save_fragcount;
    int *fragcounts;
    int fragcount;
    int size;

    int *resmap;

    int method, method_count;
    int m, sm;
    int statmethod, statmethod_count;
    char *actname;

    struct GModule *module;
    struct {
        struct Option *input, *output, *size, *nullval;
        struct Option *keyval, *landcover, *sharpness;
        struct Option *n, *method, *statmethod;
        struct Option *randseed, *title;
    } parm;
    struct {
        struct Flag *adjacent;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    module->description = _("Neutral Landscape Generator - index statistics");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);
    parm.input->key = "input1";
    parm.input->required = NO;

    parm.output = G_define_option();
    parm.output->key = "output";
    parm.output->type = TYPE_STRING;
    parm.output->required = YES;
    parm.output->gisprompt = "new_file,file,output";
    parm.output->description =
        _("Name for output ASCII-file (use out=- for stdout)");

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = NO;
    parm.keyval->description = _(
        "Value of a category from the input file to measure desired landcover");

    parm.nullval = G_define_option();
    parm.nullval->key = "nullval";
    parm.nullval->type = TYPE_INTEGER;
    parm.nullval->required = NO;
    parm.nullval->multiple = YES;
    parm.nullval->description = _("Values marking areas from the input file, "
                                  "which are to be NULL in the resulting map");

    parm.landcover = G_define_option();
    parm.landcover->key = "landcover";
    parm.landcover->type = TYPE_DOUBLE;
    parm.landcover->required = NO;
    parm.landcover->description = _("Landcover in percent");

    parm.sharpness = G_define_option();
    parm.sharpness->key = "sharpness";
    parm.sharpness->type = TYPE_DOUBLE;
    parm.sharpness->required = NO;
    parm.sharpness->description =
        _("Small values produce smooth structures, great values"
          " produce sharp, edgy structures - Range [0-1]");

    parm.n = G_define_option();
    parm.n->key = "n";
    parm.n->type = TYPE_INTEGER;
    parm.n->required = YES;
    parm.n->description = _("Number of maps to generate");

    parm.method = G_define_option();
    parm.method->key = "method";
    parm.method->type = TYPE_STRING;
    parm.method->required = YES;
    actname = G_malloc(1024);
    for (n = 0; methodlist[n].name != NULL; n++) {
        if (n)
            strcat(actname, ",");
        else
            *actname = 0;
        strcat(actname, methodlist[n].name);
    }
    parm.method->options = actname;
    parm.method->multiple = YES;
    parm.method->description = _("Operation to perform on fragments");

    parm.statmethod = G_define_option();
    parm.statmethod->key = "statmethod";
    parm.statmethod->type = TYPE_STRING;
    parm.statmethod->required = YES;
    actname = G_malloc(1024);
    for (n = 0; statmethodlist[n].name != NULL; n++) {
        if (n)
            strcat(actname, ",");
        else
            *actname = 0;
        strcat(actname, statmethodlist[n].name);
    }
    parm.statmethod->options = actname;
    parm.statmethod->multiple = YES;
    parm.statmethod->description =
        _("Statistical method to perform on the values");

    parm.randseed = G_define_option();
    parm.randseed->key = "seed";
    parm.randseed->type = TYPE_INTEGER;
    parm.randseed->required = NO;
    parm.randseed->description = _("Seed for random number generator");

    parm.title = G_define_option();
    parm.title->key = "title";
    parm.title->key_desc = "\"phrase\"";
    parm.title->type = TYPE_STRING;
    parm.title->required = NO;
    parm.title->description = _("Title for resultant raster map");

    flag.adjacent = G_define_flag();
    flag.adjacent->key = 'a';
    flag.adjacent->description =
        _("Set for 8 cell-neighbors. 4 cell-neighbors are default");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* get name of input file */
    oldname = parm.input->answer;
    oldmapset = NULL;

    /* test input files existance */
    if (oldname && NULL == (oldmapset = G_find_raster2(oldname, "")))
        G_fatal_error(_("Raster map <%s> not found"), oldname);

    /* if input specified get keyval */
    if (oldname) {
        if (parm.keyval->answer) {
            sscanf(parm.keyval->answer, "%d", &keyval);
        }
    }

    /* get size */
    sx = Rast_window_cols();
    sy = Rast_window_rows();

    size = 1;
    power = 0;
    while (size < sx - 1 || size < sy - 1) {
        size <<= 1;
        power++;
    }
    size++;

    /* get n */
    sscanf(parm.n->answer, "%d", &n);

    /* get random seed and init random */
    if (parm.randseed->answer) {
        sscanf(parm.randseed->answer, "%d", &rand_seed);
    }
    else {
        rand_seed = time(NULL);
    }
    srand(rand_seed);

    /* get landcover from user input */
    if (parm.landcover->answer) {
        sscanf(parm.landcover->answer, "%lf", &landcover);
        landcover /= 100;
    }
    else {
        landcover = Randomf();
    }

    /* get sharpness */
    if (parm.sharpness->answer) {
        sscanf(parm.sharpness->answer, "%lf", &sharpness);
    }
    else {
        sharpness = Randomf();
    }

    /* get number of cell-neighbors */
    nbr_count = flag.adjacent->answer ? 8 : 4;

    /* scan all method answers */
    for (method_count = 0; parm.method->answers[method_count] != NULL;
         method_count++) {
        /* get actual method */
        for (method = 0; (actname = methodlist[method].name); method++)
            if ((strcmp(actname, parm.method->answers[method_count]) == 0))
                break;
        if (!actname) {
            G_warning(_("<%s=%s> unknown %s"), parm.method->key,
                      parm.method->answers[method_count], parm.method->key);
            G_usage();
            exit(EXIT_FAILURE);
        }
        methods[method_count] = method;
    }

    /* scan all statmethod answers */
    for (statmethod_count = 0;
         parm.statmethod->answers[statmethod_count] != NULL;
         statmethod_count++) {
        /* get the actual statmethod */
        for (statmethod = 0; (actname = statmethodlist[statmethod].name);
             statmethod++)
            if ((strcmp(actname, parm.statmethod->answers[statmethod_count]) ==
                 0))
                break;
        if (!actname) {
            G_warning(_("<%s=%s> unknown %s"), parm.statmethod->key,
                      parm.statmethod->answer, parm.statmethod->key);
            G_usage();
            exit(EXIT_FAILURE);
        }
        statmethods[statmethod_count] = statmethod;
    }

    /* allocate cell buffers */
    buffer = (int *)G_malloc(sx * sy * sizeof(int));
    bigbuf = (double *)G_malloc(size * size * sizeof(double));
    resmap = (int *)G_malloc(sx * sy * sizeof(int));
    result = Rast_allocate_c_buf();
    cells = (Coords *)G_malloc(sx * sy * sizeof(Coords));
    fragments = (Coords **)G_malloc(sx * sy * sizeof(Coords *));
    /* res_values = (method1(statmethod1(1..n))(statmethod2(1..n))) */
    res_values =
        (DCELL *)G_malloc(method_count * statmethod_count * n * sizeof(DCELL));
    real_values =
        (DCELL *)G_malloc(method_count * statmethod_count * sizeof(DCELL));
    fragcounts = (int *)G_malloc(n * sizeof(int));

    /* init fragments structure */
    fragments[0] = cells;

    /* init buffers */
    memset(bigbuf, 0, size * size * sizeof(double));
    memset(buffer, 0, sx * sy * sizeof(int));

    /* load values from input file */
    if (oldname) {
        DCELL *res;

        real_landscape = (int *)G_malloc(sx * sy * sizeof(int));
        memset(real_landscape, 0, sx * sy * sizeof(int));

        pixel_count = 0;

        /* open cell files */
        in_fd = Rast_open_old(oldname, oldmapset);
        if (in_fd < 0)
            G_fatal_error(_("Unable to open raster map <%s>"), oldname);

        /* init buffer with values from input and get landcover */
        for (row = 0; row < sy; row++) {
            Rast_get_c_row(in_fd, result, row);
            for (col = 0; col < sx; col++) {
                if (parm.nullval->answers) {
                    real_landscape[row * sx + col] = 1;
                    for (i = 0; parm.nullval->answers[i] != NULL; i++) {
                        sscanf(parm.nullval->answers[i], "%d", &nullval);
                        if (result[col] == nullval) {
                            buffer[row * sx + col] = 1;
                            real_landscape[row * sx + col] = 0;
                        }
                    }
                }

                if (parm.keyval->answer) {
                    /* count pixels for landcover */
                    if (result[col] == keyval) {
                        pixel_count++;
                        real_landscape[row * sx + col] = 1;
                    }
                    else
                        real_landscape[row * sx + col] = 0;
                }
                if (Rast_is_c_null_value(&result[col]))
                    real_landscape[row * sx + col] = 0;
            }
        }
        Rast_close(in_fd);

        /* test output */
        /*              G_message("real landscape");
           for(row = 0; row < sy; row++) {
           for(col = 0; col < sx; col++) {
           fprintf(stderr, "%d", real_landscape[row * sx + col]);
           }
           fprintf(stderr, "\n");
           } */

        /* calculate landcover */
        if (parm.keyval->answer)
            landcover = (double)pixel_count / ((double)sx * (double)sy);

        /* resample to bigbuf */
        for (col = 0; col < size; col++) {
            for (row = 0; row < size; row++) {
                bigbuf[row * size + col] =
                    UpSample(buffer, col, row, sx, sy, size);
            }
        }

        /* apply methods to real landscape */
        fragcount =
            writeFragments(fragments, real_landscape, sy, sx, nbr_count);

        /* allocate memory for result */
        res = (DCELL *)G_malloc(fragcount * sizeof(DCELL));

        /* calculate requested values */
        for (m = 0; m < method_count; m++) {
            f_func *calculate;

            method = methods[m];
            calculate = methodlist[method].method;

            calculate(res, fragments, fragcount);

            for (sm = 0; sm < statmethod_count; sm++) {
                f_statmethod *calcstat;
                DCELL val;

                statmethod = statmethods[sm];
                calcstat = statmethodlist[statmethod].method;

                val = calcstat(res, fragcount);

                real_values[m * statmethod_count + sm] = val;
            }
        }

        /* save fragment count */
        save_fragcount = fragcount;

        G_free(res);
        G_free(real_landscape);
    } /* if(oldname) */

    /* generate n fractal maps */
    for (i = 0; i < n; i++) {
        DCELL *res;

        G_percent(i, n, 1);

        create_map(resmap, size);

        fragcount = writeFragments(fragments, resmap, sy, sx, nbr_count);

        /* save fragcount */
        fragcounts[i] = fragcount;

        /* allocate memory */
        res = (DCELL *)G_malloc(fragcount * sizeof(DCELL));

        /* calculate requested values */
        for (m = 0; m < method_count; m++) {

            f_func *calculate;

            method = methods[m];
            calculate = methodlist[method].method;

            calculate(res, fragments, fragcount);

            for (sm = 0; sm < statmethod_count; sm++) {
                f_statmethod *calcstat;
                DCELL val;

                statmethod = statmethods[sm];
                calcstat = statmethodlist[statmethod].method;

                val = calcstat(res, fragcount);

                res_values[m * statmethod_count * n + sm * n + i] = val;
            }
        }

        G_free(res);
    }
    G_percent(1, 1, 1);

    /* open ASCII-file or use stdout */
    if (parm.output->answer && strcmp(parm.output->answer, "-") != 0) {
        char rlname[GNAME_MAX];

        if (!(out_fp = fopen(parm.output->answer, "w"))) {
            G_fatal_error(_("Error creating file <%s>"), parm.output->answer);
        }

        if (oldname) {
            strcpy(rlname, parm.output->answer);
            strcat(rlname, "_RL");
            if (!(out_rl = fopen(rlname, "w"))) {
                G_fatal_error(_("Error creating file <%s>"),
                              parm.output->answer);
            }
        }
    }
    else {
        out_fp = stdout;
        out_rl = stdout;
    }

    /* write method names */
    for (m = 0; m < method_count; m++) {
        method = methods[m];
        for (sm = 0; sm < statmethod_count; sm++) {
            statmethod = statmethods[sm];
            fprintf(out_fp, "NLM_%s.%s ", methodlist[method].name,
                    statmethodlist[statmethod].name);
        }
    }
    fprintf(out_fp, "Number ");
    /* write method names for real landscape */
    if (oldname) {
        for (m = 0; m < method_count; m++) {
            method = methods[m];
            for (sm = 0; sm < statmethod_count; sm++) {
                statmethod = statmethods[sm];
                fprintf(out_rl, "RL_%s.%s ", methodlist[method].name,
                        statmethodlist[statmethod].name);
            }
        }
        fprintf(out_rl, "RL_Number");
    }

    fprintf(out_fp, "\n");
    if (oldname && out_fp != out_rl) {
        fprintf(out_rl, "\n");
    }

    /* print first data line */
    for (j = 0, pos = 0; j < method_count * statmethod_count; j++, pos += n) {
        fprintf(out_fp, "%f ", res_values[pos]);
    }
    if (method_count > 0) {
        fprintf(out_fp, "%d ", fragcounts[0]);
    }
    if (oldname) {
        for (j = 0; j < method_count * statmethod_count; j++) {
            fprintf(out_rl, "%f ", real_values[j]);
        }
        fprintf(out_rl, "%d", save_fragcount);
    }
    fprintf(out_fp, "\n");

    for (i = 1; i < n; i++) {
        /* print data line */
        for (j = 0, pos = i; j < method_count * statmethod_count;
             j++, pos += n) {
            fprintf(out_fp, "%f ", res_values[pos]);
        }
        fprintf(out_fp, "%d\n", fragcounts[i]);
    }

    /* close files */
    fclose(out_fp);
    if (oldname) {
        fclose(out_rl);
    }

    /* free buffers */
    G_free(buffer);
    G_free(bigbuf);
    G_free(resmap);
    G_free(result);
    G_free(fragments);
    G_free(res_values);
    G_free(real_values);
    G_free(fragcounts);

    exit(EXIT_SUCCESS);
}
