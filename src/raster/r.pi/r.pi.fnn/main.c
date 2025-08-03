/*****************************************************************************
 *
 * MODULE:       r.pi.fnn
 * AUTHOR(S):    Elshad Shirinov, Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Analysis of n-th functional/ecological nearest neighbour
 *               distance and spatial attributes of nearest neighbour patches
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

int recur_test(int, int, int);

struct menu {
    f_func *method;
    char *name;
    char *text;
};

struct statmethod {
    f_statmethod *method; /* routine to compute new value */
    char *name;           /* method name */
    char *text;           /* menu display - full description */
};

static struct menu menu[] = {
    {f_dist, "distance", "distance to the patch"},
    {f_path_dist, "path_distance", "path distance from patch to patch"},
    {f_area, "area", "area of the patch"},
    {f_perim, "perimeter", "perimeter of the patch"},
    {f_shapeindex, "shapeindex", "shapeindex of the patch"},
    {0, 0, 0}};

static struct statmethod statmethods[] = {
    {average, "average", "average of values"},
    {variance, "variance", "variance of values"},
    {std_deviat, "standard deviation", "standard deviation of values"},
    {value, "value", "according value for the patch"},
    {sum, "sum", "sum of values"},
    {0, 0, 0}};

int main(int argc, char *argv[])
{
    /* result */
    int exitres = 0;

    /* input */
    char *newname, *oldname;
    const char *oldmapset;
    char *costname;
    const char *costmapset;
    char fullname[GNAME_MAX];
    char title[1024];

    /* in and out file pointers */
    int in_fd, in_cost;
    int out_fd;
    DCELL *result;

    /* categories */
    struct Categories cats;

    int statmethod;
    int method;
    int methods[GNAME_MAX];
    f_func *compute_values;
    f_statmethod *compute_stat;

    char *p;

    /* neighbors count */
    int nbr_count;

    int row, col, i, j, m;
    int method_count;
    int keyval;

    int n;
    int copycolr;
    struct Colors colr;
    struct GModule *module;
    struct {
        struct Option *input, *costmap, *output;
        struct Option *keyval, *method;
        struct Option *number, *statmethod;
        struct Option *dmout, *adj_matrix, *title;
    } parm;
    struct {
        struct Flag *adjacent;
    } flag;

    DCELL *values;
    Coords *cells;
    int fragcount = 0;
    int parseres[1024];
    int number;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("landscape structure analysis"));
    G_add_keyword(_("patch index"));
    module->description = _("Determines patches of given value and performs "
                            "a nearest-neighbor analysis.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.costmap = G_define_option();
    parm.costmap->key = "costmap";
    parm.costmap->type = TYPE_STRING;
    parm.costmap->required = YES;
    parm.costmap->gisprompt = "old,cell,raster";
    parm.costmap->description =
        _("Name of existing raster file with path-cost information");

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->description = _("Key value");

    parm.method = G_define_option();
    parm.method->key = "method";
    parm.method->type = TYPE_STRING;
    parm.method->required = YES;
    p = G_malloc(1024);
    for (n = 0; menu[n].name; n++) {
        if (n)
            strcat(p, ",");
        else
            *p = 0;
        strcat(p, menu[n].name);
    }
    parm.method->options = p;
    parm.method->multiple = YES;
    parm.method->description = _("Operation to perform on fragments");

    parm.number = G_define_option();
    parm.number->key = "number";
    parm.number->key_desc = "num[-num]";
    parm.number->type = TYPE_STRING;
    parm.number->required = YES;
    parm.number->multiple = YES;
    parm.number->description = _("Number of nearest neighbors to analyse");

    parm.statmethod = G_define_option();
    parm.statmethod->key = "statmethod";
    parm.statmethod->type = TYPE_STRING;
    parm.statmethod->required = YES;
    p = G_malloc(1024);
    for (n = 0; statmethods[n].name; n++) {
        if (n)
            strcat(p, ",");
        else
            *p = 0;
        strcat(p, statmethods[n].name);
    }
    parm.statmethod->options = p;
    parm.statmethod->description =
        _("Statistical method to perform on the values");

    parm.dmout = G_define_option();
    parm.dmout->key = "dmout";
    parm.dmout->type = TYPE_STRING;
    parm.dmout->required = NO;
    parm.dmout->gisprompt = "new,cell,raster";
    parm.dmout->description = _(
        "Output name for distance matrix and id-map (performed if not empty)");

    parm.adj_matrix = G_define_option();
    parm.adj_matrix->key = "adj_matrix";
    parm.adj_matrix->type = TYPE_STRING;
    parm.adj_matrix->required = NO;
    parm.adj_matrix->gisprompt = "new,cell,raster";
    parm.adj_matrix->description =
        _("Output name for adjacency matrix (performed if not empty)");

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

    /* get names of input files */
    oldname = parm.input->answer;

    /* test input files existance */
    oldmapset = G_find_raster2(oldname, "");
    if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

    /* get name of costmap */
    costname = parm.costmap->answer;

    /* test costmap existance */
    costmapset = G_find_raster2(costname, "");
    if (costmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), costname);

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), newname);

    /* get size */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* open cell files */
    in_fd = Rast_open_old(oldname, oldmapset);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), oldname);

    /* open costmap file */
    in_cost = Rast_open_old(costname, costmapset);
    if (in_cost < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), costname);

    /* copy color table */
    copycolr = (Rast_read_colors(oldname, oldmapset, &colr) > 0);

    /* get key value */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get number of nearest neighbors to analyse */
    for (i = 0, number = 0; parm.number->answers[i] != NULL; i++) {
        number += parseToken(parseres, number, parm.number->answers[i]);
    }
    /*      sscanf(parm.number->answer, "%d", &number); */

    /* scan all method answers */
    method_count = 0;
    while (parm.method->answers[method_count] != NULL) {
        /* get actual method */
        for (method = 0; (p = menu[method].name); method++)
            if ((strcmp(p, parm.method->answers[method_count]) == 0))
                break;
        if (!p) {
            G_warning(_("<%s=%s> unknown %s"), parm.method->key,
                      parm.method->answers[method_count], parm.method->key);
            G_usage();
            exit(EXIT_FAILURE);
        }

        methods[method_count] = method;

        method_count++;
    }

    /* get the statmethod */
    for (statmethod = 0; (p = statmethods[statmethod].name); statmethod++)
        if ((strcmp(p, parm.statmethod->answer) == 0))
            break;
    if (!p) {
        G_warning(_("<%s=%s> unknown %s"), parm.statmethod->key,
                  parm.statmethod->answer, parm.statmethod->key);
        G_usage();
        exit(EXIT_FAILURE);
    }

    /* establish the stat routine */
    compute_stat = statmethods[statmethod].method;

    /* get number of cell-neighbors */
    nbr_count = flag.adjacent->answer ? 8 : 4;

    /* allocate the cell buffers */
    costmap = (DCELL *)G_malloc(nrows * ncols * sizeof(DCELL));
    cells = (Coords *)G_malloc(nrows * ncols * sizeof(Coords));
    actpos = cells;
    fragments = (Coords **)G_malloc(nrows * ncols * sizeof(Coords *));
    fragments[0] = cells;
    flagbuf = (int *)G_malloc(nrows * ncols * sizeof(int));
    result = Rast_allocate_d_buf();

    /* get title, initialize the category and stat info */
    if (parm.title->answer)
        strcpy(title, parm.title->answer);
    else
        sprintf(title, "Fragmentation of file: %s", oldname);

    G_message("Loading patches...");

    /* read costmap */
    for (row = 0; row < nrows; row++) {
        Rast_get_d_row(in_cost, result, row);
        for (col = 0; col < ncols; col++) {
            costmap[row * ncols + col] = result[col];
        }
    }
    Rast_close(in_cost);

    /* find fragments */
    for (row = 0; row < nrows; row++) {
        Rast_get_d_row(in_fd, result, row);
        for (col = 0; col < ncols; col++) {
            if (result[col] == keyval)
                flagbuf[row * ncols + col] = 1;
        }

        G_percent(row, nrows, 2);
    }
    Rast_close(in_fd);
    G_percent(nrows, nrows, 2);

    /* find fragments */
    fragcount = writeFragments(fragments, flagbuf, nrows, ncols, nbr_count);

    /* generate the distance matrix */
    get_dist_matrix(fragcount);

    /* replace 0 count with (all - 1) patches */
    for (i = 0; i < number; i++) {
        if (parseres[i] == 0)
            parseres[i] = fragcount - 1;
    }

    /* get indices of the nearest n patches (where n is the maximum number of
     * patches to analyse) */
    get_nearest_indices(fragcount, parseres, number);

    /* for each method */
    for (m = 0; m < method_count; m++) {

        /* establish the newvalue routine */
        compute_values = menu[methods[m]].method;

        /* perform actual function on the patches */
        G_message("Performing operation %s ... ", menu[methods[m]].name);
        values = (DCELL *)G_malloc(fragcount * number * sizeof(DCELL));
        compute_values(values, fragcount, parseres, number, compute_stat);

        G_percent(fragcount, fragcount, 2);

        /* write output files */
        G_message("Writing output...");

        /* for all requested patches */
        for (j = 0; j < number; j++) {

            /* open the new cellfile */
            sprintf(fullname, "%s.ENN%d.%s", newname, parseres[j],
                    menu[methods[m]].name);
            out_fd = Rast_open_new(fullname, DCELL_TYPE);
            if (out_fd < 0)
                G_fatal_error(_("Cannot create raster map <%s>"), fullname);

            /* write data */
            for (row = 0; row < nrows; row++) {
                Rast_set_d_null_value(result, ncols);

                for (i = 0; i < fragcount; i++) {
                    for (actpos = fragments[i]; actpos < fragments[i + 1];
                         actpos++) {
                        if (actpos->y == row) {
                            result[actpos->x] = values[i + j * fragcount];
                        }
                    }
                }

                Rast_put_d_row(out_fd, result);

                G_percent(row + nrows * j + nrows * number * m,
                          nrows * number * method_count, 2);
            }

            Rast_close(out_fd);
        }

    } /* for each method */
    G_percent(100, 100, 2);

    if (parm.dmout->answer) {
        exitres =
            writeDistMatrixAndID(parm.dmout->answer, fragments, fragcount);
    }

    if (parm.adj_matrix->answer) {
        exitres = writeAdjacencyMatrix(parm.adj_matrix->answer, fragments,
                                       fragcount, parseres, number);
    }

    G_free(cells);
    G_free(fragments);
    G_free(flagbuf);

    G_free(distmatrix);
    G_free(nearest_indices);

    Rast_init_cats(title, &cats);
    Rast_write_cats(newname, &cats);

    if (copycolr)
        Rast_write_colors(newname, G_mapset(), &colr);

    exit(exitres);
}
