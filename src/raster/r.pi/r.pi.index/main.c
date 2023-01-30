/*****************************************************************************
 *
 * MODULE:       r.pi.index
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Fragmentation analysis - basic spatial indices
 *
 * COPYRIGHT:    (C) 2009-2011,2017 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#define MAIN

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/stats.h>
#include "local_proto.h"

typedef int(f_func)(DCELL *, Coords **, int);

struct menu {
    f_func *method; /* routine to compute new value */
    char *name;     /* method name */
    char *text;     /* menu display - full description */
};

static struct menu menu[] = {
    {f_area, "area", "area of specified patches"},
    {f_perim, "perimeter", "perimeter of specified patches"},
    {f_shapeindex, "shape", "shape index of specified patches"},
    {f_borderindex, "border", "border index of specified patches"},
    {f_compactness, "compactness", "compactness of specified patches"},
    {f_asymmetry, "asymmetry", "asymmetry of specified patches"},
    {f_area_perim_ratio, "area-perimeter",
     "area-perimeter ratio of specified patches"},
    {f_frac_dim, "fractal", "fractal dimension of specified patches"},
    {f_nearest_dist, "ENN", "euclidean distance to nearest patch"},
    {0, 0, 0}};

int main(int argc, char *argv[])
{
    /* input */
    char *newname, *oldname;
    const char *oldmapset;
    char title[1024];

    /* in and out file pointers */
    int in_fd;
    int out_fd;
    DCELL *result;

    /* map_type and categories */
    RASTER_MAP_TYPE map_type;
    struct Categories cats;

    int method;
    f_func *compute_values;

    /* neighbors count */
    int nbr_count;

    char *p;

    int row, col, i;
    int nrows, ncols;
    int keyval;
    int n;
    struct Colors colr;
    struct Range range;
    CELL min, max;
    struct GModule *module;
    struct {
        struct Option *input, *output;
        struct Option *keyval, *method;
        struct Option *title;
    } parm;
    struct {
        struct Flag *adjacent;
    } flag;

    DCELL *values;
    Coords *cells;
    int fragcount = 0;
    int *flagbuf;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    module->description = _("Basic patch based indices");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);
    parm.input->description = _("Raster map containing categories");

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.output->description = _("Output patch-based result as raster map");

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->description = _("The value of the class to be analysed");

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
    parm.method->description = _("Operation to perform on fragments");

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

    /* get map type */
    map_type = DCELL_TYPE; /* G_raster_map_type(oldname, oldmapset); */

    /* get key value */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get the method */
    for (method = 0; (p = menu[method].name); method++)
        if ((strcmp(p, parm.method->answer) == 0))
            break;
    if (!p) {
        G_warning(_("<%s=%s> unknown %s"), parm.method->key,
                  parm.method->answer, parm.method->key);
        G_usage();
        exit(EXIT_FAILURE);
    }

    /* establish the newvalue routine */
    compute_values = menu[method].method;

    /* get number of cell-neighbors */
    nbr_count = flag.adjacent->answer ? 8 : 4;

    /* allocate the cell buffers */
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

    /* open the new cellfile  */
    out_fd = Rast_open_new(newname, map_type);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    G_message("Loading patches...");

    /* find fragments */
    for (row = 0; row < nrows; row++) {
        Rast_get_d_row(in_fd, result, row);
        for (col = 0; col < ncols; col++) {
            if (result[col] == keyval)
                flagbuf[row * ncols + col] = 1;
        }

        G_percent(row, nrows, 2);
    }
    G_percent(nrows, nrows, 2);

    /* find fragments */
    fragcount = writeFragments(fragments, flagbuf, nrows, ncols, nbr_count);

    /* perform actual function on the patches */
    G_message("Performing operation...");
    values = (DCELL *)G_malloc(fragcount * sizeof(DCELL));
    compute_values(values, fragments, fragcount);
    G_percent(fragcount, fragcount, 2);

    /* write the output file */
    G_message("Writing output...");
    for (row = 0; row < nrows; row++) {
        Rast_set_d_null_value(result, ncols);

        for (i = 0; i < fragcount; i++) {
            for (actpos = fragments[i]; actpos < fragments[i + 1]; actpos++) {
                if (actpos->y == row) {
                    result[actpos->x] = values[i];
                }
            }
        }

        Rast_put_d_row(out_fd, result);

        G_percent(row, nrows, 2);
    }

    G_percent(nrows, nrows, 2);

    Rast_close(out_fd);
    Rast_close(in_fd);

    G_free(cells);
    G_free(fragments);
    G_free(flagbuf);

    Rast_init_cats(title, &cats);
    Rast_write_cats(newname, &cats);

    Rast_read_range(newname, G_mapset(), &range);
    Rast_get_range_min_max(&range, &min, &max);
    Rast_make_bgyr_colors(&colr, min, max);
    Rast_write_colors(newname, G_mapset(), &colr);
    Rast_free_colors(&colr);

    exit(EXIT_SUCCESS);
}
