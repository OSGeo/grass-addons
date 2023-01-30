/*****************************************************************************
 *
 * MODULE:       r.pi.nlm
 * AUTHOR(S):    Elshad Shirinov, Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Generation of Neutral Landscapes (fractal landscapes), similar
 *               to r.pi.nlm, but fractal landscapes instead of circular growth
 *
 * COPYRIGHT:    (C) 2009-2011,2017 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include "local_proto.h"

int main(int argc, char *argv[])
{
    /* input */
    char *oldname;
    const char *oldmapset;

    /* output */
    char *newname;

    /* in and out file pointers */
    int in_fd, out_fd;

    /* parameters */
    int sx, sy;
    int keyval, nullval;
    double landcover;
    int pixel_count;
    double sharpness;
    int rand_seed;

    /* helper variables */
    RASTER_MAP_TYPE map_type;
    int *buffer;
    double *bigbuf;
    int i, j;
    int row, col;
    int cnt;
    CELL *result;
    int size, n;
    double edge;
    double min, max;

    struct GModule *module;
    struct {
        struct Option *input, *output, *size, *nullval;
        struct Option *keyval, *landcover, *sharpness;
        struct Option *randseed, *title;
    } parm;
    struct {
        struct Flag *report;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    module->description = _("Creates a random generated map with values 0 or 1"
                            "by given landcover and fragment count.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);
    parm.input->key = "input";
    parm.input->required = NO;

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

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

    flag.report = G_define_flag();
    flag.report->key = 'r';
    flag.report->description = _("Print report to stdout");

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
        else if (!parm.landcover->answer) {
            G_fatal_error("Specify either landcover or an input file with key "
                          "value for landcover to be acquired!");
        }
    }

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), newname);

    map_type = CELL_TYPE;

    /* get size */
    sx = Rast_window_cols();
    sy = Rast_window_rows();

    size = 1;
    n = 0;
    while (size < sx - 1 || size < sy - 1) {
        size <<= 1;
        n++;
    }
    size++;

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
        if (!oldname || !parm.keyval->answer)
            G_fatal_error("Specify either landcover or an input file with key "
                          "value for landcover to be acquired!");
    }

    /* get sharpness */
    if (parm.sharpness->answer) {
        sscanf(parm.sharpness->answer, "%lf", &sharpness);
    }
    else {
        sharpness = Randomf();
    }

    /* allocate the cell buffer */
    buffer = (int *)G_malloc(sx * sy * sizeof(int));
    bigbuf = (double *)G_malloc(size * size * sizeof(double));
    result = Rast_allocate_c_buf();

    /* init buffers */
    memset(bigbuf, 0, size * size * sizeof(double));
    memset(buffer, 0, sx * sy * sizeof(int));

    /* load values from input file */
    if (oldname) {
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
                    for (i = 0; parm.nullval->answers[i] != NULL; i++) {
                        sscanf(parm.nullval->answers[i], "%d", &nullval);
                        if (result[col] == nullval)
                            buffer[row * sx + col] = 1;
                    }
                }

                if (parm.keyval->answer) {
                    /* count pixels for landcover */
                    if (result[col] == keyval)
                        pixel_count++;
                }
            }
        }
        Rast_close(in_fd);

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
    }

    /* create fractal */
    FractalIter(bigbuf, 1, pow(2, -sharpness), n, size);

    /* replace nan values with min value */
    MinMax(bigbuf, &min, &max, size * size);

    for (i = 0; i < size * size; i++)
        if (Rast_is_d_null_value(&bigbuf[i]))
            bigbuf[i] = min;

    /* find edge */
    edge = CutValues(bigbuf, landcover, size * size);

    /* resample map to desired size */
    for (i = 0; i < sx; i++) {
        for (j = 0; j < sy; j++) {
            double val = DownSample(bigbuf, min, i, j, sx, sy, size);
            double old = buffer[i + j * sx];

            if (val >= edge && old == 0) {
                buffer[i + j * sx] = 1;
            }
            else {
                buffer[i + j * sx] = 0;
            }
        }
    }

    /* write output file */
    out_fd = Rast_open_new(newname, map_type);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    for (j = 0; j < sy; j++) {
        for (i = 0; i < sx; i++) {
            int cell = buffer[i + j * sx];

            if (cell > 0) {
                result[i] = 1;
            }
            else {
                Rast_set_c_null_value(result + i, 1);
            }
        }
        Rast_put_c_row(out_fd, result);
    }

    Rast_close(out_fd);

    /* print report */
    if (flag.report->answer) {
        fprintf(stdout, "report:\n");
        fprintf(stdout, "written file: <%s>\n", newname);

        cnt = 0;
        for (i = 0; i < sx * sy; i++)
            if (buffer[i] == 1)
                cnt++;
        landcover = (double)cnt / ((double)sx * (double)sy) * 100;
        fprintf(stdout, "landcover: %0.2f%%\n", landcover);
    }

    G_free(buffer);
    G_free(bigbuf);
    G_free(result);

    exit(EXIT_SUCCESS);
}
