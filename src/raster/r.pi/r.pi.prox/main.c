/*****************************************************************************
 *
 * MODULE:       r.pi.prox
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Proximity analysis - values of patches within a defined range
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

int recur_test(int, int, int);

typedef int(f_func)(DCELL *, Coords **, int, int, int);

struct menu {
    f_func *method; /* routine to compute new value */
    char *name;     /* method name */
    char *text;     /* menu display - full description */
};

static struct menu menu[] = {
    {f_proximity, "proximity index",
     "proximity index for every patch within certain range"},
    {f_modified_prox, "modified proximity index",
     "modified proximity index for every patch within certain range"},
    {f_neighborhood, "neighborhood index",
     "number of patches within certain range"},
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

    char *p;

    /* neighbors count */
    int nbr_count;

    int row, col, i;
    int nrows, ncols;
    int keyval;
    int min = 0;
    int max = MAX_DOUBLE;
    int *flagbuf;

    int n;
    int copycolr;
    struct Colors colr;
    struct GModule *module;
    struct {
        struct Option *input, *output;
        struct Option *keyval, *method;
        struct Option *min, *max, *title;
    } parm;
    struct {
        struct Flag *adjacent;
    } flag;

    DCELL *values;
    Coords *cells;
    int fragcount = 0;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    module->description =
        _("Calculates correlation of two raster maps "
          "by calculating correlation function of two "
          "corresponding rectangular areas for each "
          "raster point and writing the result into a new raster map.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

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
    parm.method->description = _("Operation to perform on fragments");

    parm.min = G_define_option();
    parm.min->key = "min";
    parm.min->type = TYPE_INTEGER;
    parm.min->required = NO;
    parm.min->description =
        _("Minimum range for the operation measured by pixels, default 0");

    parm.max = G_define_option();
    parm.max->key = "max";
    parm.max->type = TYPE_INTEGER;
    parm.max->required = NO;
    parm.max->description = _("Maximum Range for the operation measured by "
                              "pixels, default copmlete map");

    flag.adjacent = G_define_flag();
    flag.adjacent->key = 'a';
    flag.adjacent->description =
        _("Set for 8 cell-neighbors. 4 cell-neighbors are default");

    parm.title = G_define_option();
    parm.title->key = "title";
    parm.title->key_desc = "\"phrase\"";
    parm.title->type = TYPE_STRING;
    parm.title->required = NO;
    parm.title->description = _("Title for resultant raster map");

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

    /* copy color table */
    copycolr = (Rast_read_colors(oldname, oldmapset, &colr) > 0);

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

    /* get min */
    if (parm.min->answer)
        sscanf(parm.min->answer, "%d", &min);

    /* get max */
    if (parm.max->answer)
        sscanf(parm.max->answer, "%d", &max);

    /* get title */
    if (parm.title->answer)
        strcpy(title, parm.title->answer);
    else
        sprintf(title, "Fragmentation of file: %s", oldname);

    /* open the new cellfile  */
    out_fd = Rast_open_new(newname, map_type);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    G_message(_("Percent complete ... "));

    /* find fragments */
    for (row = 0; row < nrows; row++) {
        Rast_get_d_row(in_fd, result, row);
        for (col = 0; col < ncols; col++) {
            if (result[col] == keyval)
                flagbuf[row * ncols + col] = 1;
        }
    }
    Rast_close(in_fd);

    /* find fragments */
    fragcount = writeFragments(fragments, flagbuf, nrows, ncols, nbr_count);

    /* perform actual function on the patches */
    values = (DCELL *)G_malloc(fragcount * sizeof(DCELL));
    compute_values(values, fragments, fragcount, min, max);

    /* write the output file */
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
    }

    G_percent(row, nrows, 2);

    Rast_close(out_fd);

    G_free(cells);
    G_free(fragments);
    G_free(flagbuf);

    Rast_init_cats(title, &cats);
    Rast_write_cats(newname, &cats);

    if (copycolr)
        Rast_write_colors(newname, G_mapset(), &colr);

    exit(EXIT_SUCCESS);
}
