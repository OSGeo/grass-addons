/*****************************************************************************
 *
 * MODULE:       r.pi.corearea
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Non-linear core area analysis
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
    {median, "median", "median of values", "med"},
    {0, 0, 0, 0}};

struct propmethod {
    f_propmethod *method; /* routine to compute new value */
    char *name;           /* method name */
    char *text;           /* menu display - full description */
    char *suffix;         /* output suffix */
};

static struct propmethod propmethods[] = {
    {linear, "linear", "linear decrease of the propagation value", "lin"},
    {exponential, "exponential",
     "exponential decrease of the propagation value", "exp"},
    {0, 0, 0, 0}};

int main(int argc, char *argv[])
{
    /* input */
    const char *newname, *oldname, *oldmapset, *costname, *costmapset,
        *propname, *propmapset;
    char fullname[GNAME_MAX];

    /* in and out file pointers */
    int in_fd;
    int out_fd;

    /* parameters */
    int keyval;
    int nbr_count;
    int buffer;
    double distance;
    double angle;
    f_statmethod *method;
    f_propmethod *prop_method;
    double dist_weight;

    /* helpers */
    char *str;
    int nrows, ncols;
    int row, col, i, n;
    CELL *result;
    int *flagbuf;
    int patch;
    int fragcount;

    struct GModule *module;
    struct {
        struct Option *input, *costmap, *propmap, *output;
        struct Option *keyval, *buffer;
        struct Option *distance, *angle;
        struct Option *stats, *propmethod, *dist_weight;
    } parm;
    struct {
        struct Flag *adjacent;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    module->description = _("Variable edge effects and core area analysis");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.costmap = G_define_option();
    parm.costmap->key = "costmap";
    parm.costmap->type = TYPE_STRING;
    parm.costmap->required = YES;
    parm.costmap->gisprompt = "old,cell,raster";
    parm.costmap->description = _("Name of the cost map raster file");

    parm.propmap = G_define_option();
    parm.propmap->key = "propmap";
    parm.propmap->type = TYPE_STRING;
    parm.propmap->required = NO;
    parm.propmap->gisprompt = "old,cell,raster";
    parm.propmap->description =
        _("Name of the propagation cost map raster file");

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->description = _("Key value");

    parm.buffer = G_define_option();
    parm.buffer->key = "buffer";
    parm.buffer->type = TYPE_INTEGER;
    parm.buffer->required = YES;
    parm.buffer->description = _("Buffer size");

    parm.distance = G_define_option();
    parm.distance->key = "distance";
    parm.distance->type = TYPE_DOUBLE;
    parm.distance->required = YES;
    parm.distance->description = _("Cone of effect radius");

    parm.angle = G_define_option();
    parm.angle->key = "angle";
    parm.angle->type = TYPE_DOUBLE;
    parm.angle->required = YES;
    parm.angle->description = _("Cone of effect angle");

    parm.stats = G_define_option();
    parm.stats->key = "stats";
    parm.stats->type = TYPE_STRING;
    parm.stats->required = YES;
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

    parm.propmethod = G_define_option();
    parm.propmethod->key = "propmethod";
    parm.propmethod->type = TYPE_STRING;
    parm.propmethod->required = YES;
    str = G_malloc(1024);
    for (n = 0; propmethods[n].name; n++) {
        if (n)
            strcat(str, ",");
        else
            *str = 0;
        strcat(str, propmethods[n].name);
    }
    parm.propmethod->options = str;
    parm.propmethod->description = _("Propagation method");

    parm.dist_weight = G_define_option();
    parm.dist_weight->key = "dist_weight";
    parm.dist_weight->type = TYPE_DOUBLE;
    parm.dist_weight->required = NO;
    parm.dist_weight->description =
        _("Parameter for distance weighting. <0.5 - rapid decrease; 0.5 - "
          "linear decrease; > 0.5 - slow decrease; 1 - no decrease");

    flag.adjacent = G_define_flag();
    flag.adjacent->key = 'a';
    flag.adjacent->description =
        _("Set for 8 cell-neighbors. 4 cell-neighbors are default");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* get names of input files */
    oldname = parm.input->answer;
    costname = parm.costmap->answer;
    propname = parm.propmap->answer;

    /* test input file existance */
    oldmapset = G_find_raster2(oldname, "");
    if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

    /* test costmap file existance */
    costmapset = G_find_raster2(costname, "");
    if (costmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), costname);

    /* test propmap file existance */
    propmapset = NULL;
    if (propname && NULL == (propmapset = G_find_raster2(propname, "")))
        G_fatal_error(_("Raster map <%s> not found"), propname);

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), newname);

    /* get size */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    G_message("rows = %d, cols = %d", nrows, ncols);

    /* get key value */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get key value */
    sscanf(parm.buffer->answer, "%d", &buffer);

    /* get distance */
    sscanf(parm.distance->answer, "%lf", &distance);

    /* get angle and convert to radian */
    sscanf(parm.angle->answer, "%lf", &angle);
    angle *= M_PI / 180.0;

    /* get statistical method */
    method = NULL;
    for (i = 0; (str = statmethods[i].name) != 0; i++) {
        if (strcmp(str, parm.stats->answer) == 0) {
            method = statmethods[i].method;
            break;
        }
    }
    if (!method)
        G_fatal_error(_("Unknown method <%s> for option <%s>"),
                      parm.stats->answer, parm.stats->key);

    /* get propagation method */
    prop_method = NULL;
    for (i = 0; (str = propmethods[i].name) != 0; i++) {
        if (strcmp(str, parm.propmethod->answer) == 0) {
            prop_method = propmethods[i].method;
            break;
        }
    }
    if (!prop_method)
        G_fatal_error(_("Unknown method <%s> for option <%s>"),
                      parm.propmethod->answer, parm.propmethod->key);

    /* get distance weighting parameter */
    if (parm.dist_weight->answer) {
        sscanf(parm.dist_weight->answer, "%lf", &dist_weight);
    }
    else {
        dist_weight = 1.0;
    }

    /* get number of cell-neighbors */
    nbr_count = flag.adjacent->answer ? 8 : 4;

    /* allocate the cell buffers */
    cells = (Coords *)G_malloc(nrows * ncols * sizeof(Coords));
    fragments = (Coords **)G_malloc(nrows * ncols * sizeof(Coords *));
    fragments[0] = cells;
    flagbuf = (int *)G_malloc(nrows * ncols * sizeof(int));
    map = (DCELL *)G_malloc(nrows * ncols * sizeof(DCELL));
    valmap = (DCELL *)G_malloc(nrows * ncols * sizeof(DCELL));
    propmap = (DCELL *)G_malloc(nrows * ncols * sizeof(DCELL));
    result = Rast_allocate_c_buf();

    G_message("Loading Input files ... ");

    /* open input file */
    in_fd = Rast_open_old(oldname, oldmapset);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), oldname);

    /* read patch map */
    for (row = 0; row < nrows; row++) {
        Rast_get_c_row(in_fd, result, row);
        for (col = 0; col < ncols; col++) {
            if (result[col] == keyval) {
                flagbuf[row * ncols + col] = 1;
            }
        }

        G_percent(row + 1, nrows, 1);
    }

    /* close cell file */
    Rast_close(in_fd);

    /* open costmap file */
    in_fd = Rast_open_old(costname, oldmapset);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), costname);

    /* read cost map */
    for (row = 0; row < nrows; row++) {
        Rast_get_d_row(in_fd, &map[row * ncols], row);

        for (col = 0; col < ncols; col++) {
            if (Rast_is_d_null_value(&map[row * ncols + col])) {
                map[row * ncols + col] = 0.0;
            }
        }
    }

    /* close cell file */
    Rast_close(in_fd);

    /* open propmap file */
    if (propname) {
        in_fd = Rast_open_old(propname, propmapset);
        if (in_fd < 0)
            G_fatal_error(_("Unable to open raster map <%s>"), propname);

        /* read propagation map */
        for (row = 0; row < nrows; row++) {
            Rast_get_d_row(in_fd, &propmap[row * ncols], row);

            for (col = 0; col < ncols; col++) {
                if (Rast_is_d_null_value(&propmap[row * ncols + col])) {
                    propmap[row * ncols + col] = 0.0;
                }
            }
        }

        /* close cell file */
        Rast_close(in_fd);
    }
    else {
        for (row = 0; row < nrows; row++) {
            for (col = 0; col < ncols; col++) {
                propmap[row * ncols + col] = 1.0;
            }
        }
    }

    /*G_message("map");
       for(row = 0; row < nrows; row++) {
       for(col = 0; col< ncols; col++) {
       fprintf(stderr, "%0.2f ", map[row * ncols + col]);
       }
       fprintf(stderr, "\n");
       } */

    /* find fragments */
    fragcount = writeFragments(fragments, flagbuf, nrows, ncols, nbr_count);

    /* create a patch map */
    for (i = 0; i < fragcount; i++) {
        Coords *cell;

        for (cell = fragments[i]; cell < fragments[i + 1]; cell++) {
            int x = cell->x;
            int y = cell->y;

            flagbuf[y * ncols + x] = i + 1;
        }
    }

    /* allocate memory for border arrays */
    patch_borders =
        (PatchBorderList *)G_malloc((fragcount + 1) * sizeof(PatchBorderList));

    /* find borders */
    G_message("Identifying borders...");
    find_borders(flagbuf, nrows, ncols, fragcount);

    /* flagbuf is not needed any more */
    G_free(flagbuf);

    /* test output */

    /*G_message("Borders:");
       for(patch = 0; patch < fragcount; patch++) {
       fprintf(stderr, "patch %d\n", patch);

       PatchBorderList list = patch_borders[patch];

       int contour;
       for(contour = 0; contour < list.count; contour++) {
       fprintf(stderr, "Contour %d: ", contour);

       Position *p;
       for(p = list.borders[contour]; p < list.borders[contour + 1]; p++) {
       fprintf(stderr, "(%d, %d)", p->x, p->y);
       }
       fprintf(stderr, "\n");
       }
       fprintf(stderr, "\n");
       } */

    /* fill value map with -1 for empty space and 0 for patches */
    for (i = 0; i < nrows * ncols; i++) {
        valmap[i] = -1.0;
    }
    for (i = 0; i < fragcount; i++) {
        Coords *cell;

        for (cell = fragments[i]; cell < fragments[i + 1]; cell++) {
            int x = cell->x;
            int y = cell->y;

            valmap[y * ncols + x] = 0.0;
        }
    }

    /* initialize border values for propagation */
    init_border_values(distance, angle, buffer, method, dist_weight, nrows,
                       ncols, fragcount);

    propagate(nbr_count, prop_method, nrows, ncols, fragcount);

    /*G_message("costmap");
       for(row = 0; row < nrows; row++) {
       for(col = 0; col< ncols; col++) {
       fprintf(stderr, "%0.0f ", map[row * ncols + col]);
       }
       fprintf(stderr, "\n");
       } */

    /* test output */
    /*G_message("patch mask");
       for(row = 0; row < nrows; row++) {
       for(col = 0; col< ncols; col++) {
       if(flagbuf[row * ncols + col] >= 0) {
       fprintf(stderr, "%d", flagbuf[row * ncols + col]);
       } else {
       fprintf(stderr, "*");
       }
       }
       fprintf(stderr, "\n");
       } */

    /* OUTPUT */
    G_message("Writing Output ...");

    /* write output */
    /* open the new cellfile  */
    out_fd = Rast_open_new(newname, CELL_TYPE);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    /* write the output file */
    for (row = 0; row < nrows; row++) {
        Rast_set_c_null_value(result, ncols);

        for (i = 0; i < fragcount; i++) {
            Coords *p;

            for (p = fragments[i]; p < fragments[i + 1]; p++) {
                if (p->y == row) {
                    if (valmap[p->y * ncols + p->x] <= 0.0) {
                        result[p->x] = 1;
                    }
                }
            }
        }

        Rast_put_c_row(out_fd, result);

        G_percent(row + 1, 2 * nrows, 1);
    }

    /* close output */
    Rast_close(out_fd);

    /* write map */
    /* open the new cellfile  */
    sprintf(fullname, "%s_%s", newname, "map");
    out_fd = Rast_open_new(fullname, DCELL_TYPE);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), fullname);

    /* write the output file */
    for (row = 0; row < nrows; row++) {
        Rast_put_d_row(out_fd, &valmap[row * ncols]);

        G_percent(nrows + row + 1, 2 * nrows, 1);
    }

    /* close output */
    Rast_close(out_fd);

    /* free all buffers */
    for (patch = 0; patch < fragcount; patch++) {
        G_free(patch_borders[patch].positions);
        G_free(patch_borders[patch].borders);
    }
    G_free(patch_borders);

    G_free(cells);
    G_free(fragments);
    G_free(map);
    G_free(valmap);
    G_free(propmap);
    G_free(result);

    exit(EXIT_SUCCESS);
}
