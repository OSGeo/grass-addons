/*****************************************************************************
 *
 * MODULE:       r.pi.enn.pr
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Iterative removal of patches and analysis of patch relevance
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
    f_func *method; /* routine to compute new value */
    char *name;     /* method name */
    char *text;     /* menu display - full description */
};

struct statmethod {
    f_statmethod *statmethod; /* routine to compute new value */
    char *name;               /* method name */
    char *text;               /* menu display - full description */
};

static struct method methods[] = {
    {f_distance, "distance", "distance to the nearest patch"},
    {f_area, "area", "area of the nearest patch"},
    {0, 0, 0}};

static struct statmethod statmethods[] = {
    {sum, "sum", "sum of diferences"},
    {average, "average", "average of diferences"},
    {0, 0, 0}};

int main(int argc, char *argv[])
{
    /* input */
    char *oldname, *newname;
    const char *oldmapset;
    char outname[GNAME_MAX];

    /* in and out file pointers */
    int in_fd;  /* raster - input */
    int out_fd; /* raster - output */

    /* parameters */
    int keyval;
    int neighb_count;
    int method;
    f_func *perform_method;
    int statmethod;
    f_statmethod *perform_statmethod;

    /* other parameters */
    char title[1024];

    /* helper variables */
    RASTER_MAP_TYPE map_type;
    int i;
    int row, col;
    int nrows, ncols;
    int act_method;
    DCELL *result;
    char *p;

    int *flagbuf;
    int fragcount;
    DCELL *values;
    Coords *actpos;

    struct GModule *module;
    struct {
        struct Option *input, *output;
        struct Option *keyval, *method;
        struct Option *statmethod, *title;
    } parm;
    struct {
        struct Flag *adjacent;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    module->description =
        _("Patch relevance for Euclidean Nearest Neighbor patches.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->description = _("Key value of patches in the input file");

    parm.method = G_define_option();
    parm.method->key = "method";
    parm.method->type = TYPE_STRING;
    parm.method->required = YES;
    p = G_malloc(1024);
    for (act_method = 0; methods[act_method].name; act_method++) {
        if (act_method > 0)
            strcat(p, ",");
        else
            *p = 0;
        strcat(p, methods[act_method].name);
    }
    parm.method->options = p;
    parm.method->description = _("Aspect of the nearest patch to use.");

    parm.statmethod = G_define_option();
    parm.statmethod->key = "statmethod";
    parm.statmethod->type = TYPE_STRING;
    parm.statmethod->required = YES;
    p = G_malloc(1024);
    for (act_method = 0; statmethods[act_method].name; act_method++) {
        if (act_method > 0)
            strcat(p, ",");
        else
            *p = 0;
        strcat(p, statmethods[act_method].name);
    }
    parm.statmethod->options = p;
    parm.statmethod->description =
        _("Statistical method to perform on differences.");

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
    if (oldname && NULL == (oldmapset = G_find_raster2(oldname, ""))) {
        G_warning(_("%s: <%s> raster file not found\n"), G_program_name(),
                  oldname);
        exit(EXIT_FAILURE);
    }

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
    map_type = DCELL_TYPE;

    /* get key value */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get number of cell-neighbors */
    neighb_count = flag.adjacent->answer ? 8 : 4;

    /* get method */
    for (method = 0; (p = methods[method].name); method++)
        if ((strcmp(p, parm.method->answer) == 0))
            break;
    if (!p) {
        G_warning(_("<%s=%s> unknown %s"), parm.method->key,
                  parm.method->answer, parm.method->key);
        G_usage();
        exit(EXIT_FAILURE);
    }

    /* establish the method routine */
    perform_method = methods[method].method;

    /* get statmethod */
    for (statmethod = 0; (p = statmethods[statmethod].name); statmethod++)
        if ((strcmp(p, parm.statmethod->answer) == 0))
            break;
    if (!p) {
        G_warning(_("<%s=%s> unknown %s"), parm.statmethod->key,
                  parm.statmethod->answer, parm.statmethod->key);
        G_usage();
        exit(EXIT_FAILURE);
    }

    /* establish the statmethod routine */
    perform_statmethod = statmethods[statmethod].statmethod;

    /* get title */
    if (parm.title->answer)
        strcpy(title, parm.title->answer);
    else
        sprintf(title, "Fragmentation of file: %s", oldname);

    /* allocate the cell buffers */
    cells = (Coords *)G_malloc(nrows * ncols * sizeof(Coords));
    fragments = (Coords **)G_malloc(nrows * ncols * sizeof(Coords *));
    fragments[0] = cells;
    flagbuf = (int *)G_malloc(nrows * ncols * sizeof(int));
    result = Rast_allocate_d_buf();

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
    fragcount = writeFragments(fragments, flagbuf, nrows, ncols, neighb_count);

    /* perform actual function on the patches */
    values = (DCELL *)G_malloc(3 * fragcount * sizeof(DCELL));
    perform_method(values, fragments, fragcount, perform_statmethod);

    /* open new cellfile  */
    strcpy(outname, newname);
    strcat(outname, ".diff");
    if (module->overwrite == 0 && G_find_raster(outname, G_mapset()) != NULL)
        G_fatal_error(_("Output raster <%s> exists. To overwrite, use the "
                        "--overwrite flag"),
                      outname);
    out_fd = Rast_open_new(outname, map_type);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    /* write the output file */
    for (row = 0; row < nrows; row++) {
        Rast_set_d_null_value(result, ncols);

        for (i = 0; i < fragcount; i++) {
            for (actpos = fragments[i]; actpos < fragments[i + 1]; actpos++) {
                if (actpos->y == row) {
                    result[actpos->x] = values[3 * i];
                }
            }
        }

        Rast_put_d_row(out_fd, result);
    }
    Rast_close(out_fd);

    /* open new cellfile  */
    strcpy(outname, newname);
    strcat(outname, ".PP");
    if (module->overwrite == 0 && G_find_raster(outname, G_mapset()) != NULL)
        G_fatal_error(_("Output raster <%s> exists. To overwrite, use the "
                        "--overwrite flag"),
                      outname);
    out_fd = Rast_open_new(outname, map_type);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    /* write the output file */
    for (row = 0; row < nrows; row++) {
        Rast_set_d_null_value(result, ncols);

        for (i = 0; i < fragcount; i++) {
            for (actpos = fragments[i]; actpos < fragments[i + 1]; actpos++) {
                if (actpos->y == row) {
                    result[actpos->x] = values[3 * i + 1];
                }
            }
        }

        Rast_put_d_row(out_fd, result);
    }
    Rast_close(out_fd);

    /* open new cellfile  */
    strcpy(outname, newname);
    strcat(outname, ".PA");
    if (module->overwrite == 0 && G_find_raster(outname, G_mapset()) != NULL)
        G_fatal_error(_("Output raster <%s> exists. To overwrite, use the "
                        "--overwrite flag"),
                      outname);
    out_fd = Rast_open_new(outname, map_type);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), outname);

    /* write the output file */
    for (row = 0; row < nrows; row++) {
        Rast_set_d_null_value(result, ncols);

        for (i = 0; i < fragcount; i++) {
            for (actpos = fragments[i]; actpos < fragments[i + 1]; actpos++) {
                if (actpos->y == row) {
                    result[actpos->x] = values[3 * i + 2];
                }
            }
        }

        Rast_put_d_row(out_fd, result);
    }
    Rast_close(out_fd);

    G_free(cells);
    G_free(fragments);
    G_free(flagbuf);

    exit(EXIT_SUCCESS);
}
