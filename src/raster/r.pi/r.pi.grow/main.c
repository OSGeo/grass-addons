/*****************************************************************************
 *
 * MODULE:       r.pi.grow
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Size and landscape suitability based region growing
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
    f_method *method; /* routine to compute new value */
    char *name;       /* method name */
    char *text;       /* menu display - full description */
    char *suffix;     /* output suffix */
};

static struct method methods[] = {
    {f_circular, "circular", "random circular growth", "crc"},
    {f_random, "random", "random growth", "rnd"},
    {f_costbased, "costbased", "cost-based random growth", "cbr"},
    {0, 0, 0, 0}};

int main(int argc, char *argv[])
{
    /* input */
    char *newname, *oldname, *costname;
    const char *oldmapset, *costmapset;

    /* in and out file pointers */
    int in_fd;
    int out_fd;

    /* parameters */
    int keyval;
    int area;
    f_method *method;
    int nbr_count;

    /* helpers */
    DCELL *d_res;
    int *line;
    int *flagbuf;

    char *str;
    int n, i;
    int nrows, ncols;
    int row, col;

    Position *border_list;
    int border_count;

    struct GModule *module;
    struct {
        struct Option *input, *costmap, *output;
        struct Option *keyval, *area, *method, *seed;
    } parm;

    struct {
        struct Flag *adjacent;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("landscape structure analysis"));
    G_add_keyword(_("region growing"));
    module->description = _("Size and suitability based region growing.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.costmap = G_define_option();
    parm.costmap->key = "costmap";
    parm.costmap->type = TYPE_STRING;
    parm.costmap->required = NO;
    parm.costmap->gisprompt = "old,cell,raster";
    parm.costmap->description = _("Name of the cost map raster file");

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->description = _("Key value");

    parm.area = G_define_option();
    parm.area->key = "area";
    parm.area->type = TYPE_INTEGER;
    parm.area->required = YES;
    parm.area->description = _("Area to grow");

    parm.method = G_define_option();
    parm.method->key = "method";
    parm.method->type = TYPE_STRING;
    parm.method->required = YES;
    str = G_malloc(1024);
    for (n = 0; methods[n].name; n++) {
        if (n)
            strcat(str, ",");
        else
            *str = 0;
        strcat(str, methods[n].name);
    }
    parm.method->options = str;
    parm.method->description = _("Method of growth");

    parm.seed = G_define_option();
    parm.seed->key = "seed";
    parm.seed->type = TYPE_INTEGER;
    parm.seed->required = NO;
    parm.seed->description = _("Random number generator seed");

    flag.adjacent = G_define_flag();
    flag.adjacent->key = 'a';
    flag.adjacent->description =
        _("Set for 8 cell-neighbors. 4 cell-neighbors are default");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* get names of input files */
    oldname = parm.input->answer;
    costname = parm.costmap->answer;
    costmapset = NULL;

    /* test input file existance */
    oldmapset = G_find_raster2(oldname, "");
    if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

    /* test costmap file existance */
    if (costname) {
        if (NULL == (costmapset = G_find_raster2(costname, ""))) {
            G_fatal_error("%s: <%s> raster file not found\n", G_program_name(),
                          costname);
            exit(EXIT_FAILURE);
        }
    }

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), newname);

    /* get size */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    G_debug(1, "rows = %d, cols = %d", nrows, ncols);

    /* get key value */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get area */
    sscanf(parm.area->answer, "%d", &area);

    /* get growth method */
    method = NULL;
    for (i = 0; (str = methods[i].name) != 0; i++) {
        if (strcmp(str, parm.method->answer) == 0) {
            method = methods[i].method;
            break;
        }
    }
    if (!method) {
        G_fatal_error("<%s=%s> unknown %s", parm.method->key,
                      parm.method->answer, parm.method->key);
        exit(EXIT_FAILURE);
    }

    /* set random seed */
    if (parm.seed->answer) {
        int seed;

        sscanf(parm.seed->answer, "%d", &seed);
        srand(seed);
    }
    else {
        srand(time(NULL));
    }

    /* get number of cell-neighbors */
    nbr_count = flag.adjacent->answer ? 8 : 4;

    /* allocate the cell buffers */
    flagbuf = (int *)G_malloc(ncols * nrows * sizeof(int));
    costmap = (DCELL *)G_malloc(ncols * nrows * sizeof(DCELL));
    line = Rast_allocate_c_buf();
    d_res = Rast_allocate_d_buf();

    G_message("Loading Input file ... ");

    /* load map */
    /* open input file */
    in_fd = Rast_open_old(oldname, oldmapset);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), oldname);

    /* read patch map */
    memset(flagbuf, 0, ncols * nrows * sizeof(int));
    for (row = 0; row < nrows; row++) {
        Rast_get_c_row(in_fd, line, row);
        for (col = 0; col < ncols; col++) {
            if (line[col] == keyval) {
                flagbuf[row * ncols + col] = 1;
            }
        }

        G_percent(row + 1, nrows, 1);
    }

    /* close cell file */
    Rast_close(in_fd);

    /*G_message("map");
       for(row = 0; row < nrows; row++) {
       for(col = 0; col< ncols; col++) {
       fprintf(stderr, "%d ", flagbuf[row * ncols + col]);
       }
       fprintf(stderr, "\n");
       } */

    /* load costmap */
    /* open input file */
    if (costname) {
        in_fd = Rast_open_old(costname, costmapset);
        if (in_fd < 0)
            G_fatal_error(_("Unable to open raster map <%s>"), costname);

        /* read cost map */
        for (row = 0; row < nrows; row++) {
            Rast_get_d_row(in_fd, &costmap[row * ncols], row);

            G_percent(row + 1, nrows, 1);
        }

        /* close cell file */
        Rast_close(in_fd);
    }
    else {
        for (row = 0; row < nrows; row++) {
            for (col = 0; col < ncols; col++) {
                costmap[row * ncols + col] = 1.0;
            }
        }
    }

    /* G_message("costmap");
       for(row = 0; row < nrows; row++) {
       for(col = 0; col< ncols; col++) {
       fprintf(stderr, "%0.2f ", costmap[row * ncols + col]);
       }
       fprintf(stderr, "\n");
       } */

    /* prepare border list */
    border_list = (Position *)G_malloc(ncols * nrows * sizeof(Position));
    border_count = gather_border(border_list, nbr_count, flagbuf, nrows, ncols);

    /*G_message("border_count = %d", border_count); */

    for (i = 0; i < area && border_count > 0; i++) {
        /*G_message("border list step %d:", i);
           for(n = 0; n < border_count; n++) {
           fprintf(stderr, "(%d,%d)", border_list[n].x, border_list[n].y);
           }
           fprintf(stderr, "\n"); */

        border_count =
            method(border_list, border_count, nbr_count, flagbuf, nrows, ncols);
    }
    /*G_message("final border list:");
       for(i = 0; i < border_count; i++) {
       fprintf(stderr, "(%d,%d)", border_list[i].x, border_list[i].y);
       }
       fprintf(stderr, "\n");

       G_message("map");
       for(row = 0; row < nrows; row++) {
       for(col = 0; col< ncols; col++) {
       fprintf(stderr, "%d ", flagbuf[row * ncols + col]);
       }
       fprintf(stderr, "\n");
       } */

    /* write output */
    /* open the new cellfile  */
    out_fd = Rast_open_new(newname, DCELL_TYPE);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    /* write the output file */
    for (row = 0; row < nrows; row++) {
        Rast_set_d_null_value(d_res, ncols);

        for (col = 0; col < ncols; col++) {
            if (flagbuf[row * ncols + col] == 1) {
                d_res[col] = 1;
            }
        }
        Rast_put_d_row(out_fd, d_res);

        G_percent(row + 1, nrows, 1);
    }

    /* close output */
    Rast_close(out_fd);

    G_free(flagbuf);
    G_free(costmap);
    G_free(line);
    G_free(d_res);

    exit(EXIT_SUCCESS);
}
