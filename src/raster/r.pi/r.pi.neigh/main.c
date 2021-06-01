/*
 ****************************************************************************
 *
 * MODULE:       r.pi.neigh
 * AUTHOR(S):    Elshad Shirinov, Martin Wegmann
 * PURPOSE:      Neighbourhood analysis - value of patches within a defined range
 *
 * COPYRIGHT:    (C) 2009-2011 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#define MAIN

#include "local_proto.h"

struct menu
{
    f_func *method;		/* routine to compute new value */
    char *name;			/* method name */
    char *text;			/* menu display - full description */
};

static struct menu menu[] = {
    {min, "min", "minimum of patch-values within certain range"},
    {max, "max", "maximum of patch-values within certain range"},
    {average, "average", "average of patch-values within certain range"},
    {variance, "var", "variance of patch-values within certain range"},
    {0, 0, 0}
};

int main(int argc, char *argv[])
{
    /* input */
    char *newname, *oldname, *newmapset, *oldmapset;
    char *vals_name, *vals_mapset;
    char title[1024];

    /* in and out file pointers */
    int in_fd;
    int out_fd;
    DCELL *result, res[30];

    /* map_type and categories */
    RASTER_MAP_TYPE map_type;
    struct Categories cats;

    int method;
    f_func *stat_method;

    char *p;

    /* neighbors count */
    int neighb_count;

    int row, col, i, j;
    int readrow;
    int keyval;
    int min = 0;
    int max = MAX_DOUBLE;

    int n;
    int copycolr;
    struct Colors colr;
    struct GModule *module;
    struct
    {
	struct Option *input1, *input2, *output;
	struct Option *keyval, *method;
	struct Option *min, *max, *title;
    } parm;
    struct
    {
	struct Flag *adjacent;
    } flag;

    DCELL *values;
    Coords *cells;

    struct Cell_head ch, window;

    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords = _("raster");
    module->description =
	_("Neighbourhood analysis - value of patches within a defined range.");

    parm.input1 = G_define_standard_option(G_OPT_R_INPUT);
    parm.input1->key = "input1";
    parm.input1->gisprompt = "old,cell,raster,1";

    parm.input2 = G_define_standard_option(G_OPT_R_INPUT);
    parm.input2->key = "input2";
    parm.input2->gisprompt = "old,cell,raster,1";	/* 1? */
    parm.input2->description = _("Raster file with values of patches to use");

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
    parm.max->description =
	_("Maximum Range for the operation measured by pixels, default complete map");

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
    oldname = parm.input1->answer;
    vals_name = parm.input2->answer;

    /* get mapset */
    oldmapset = G_find_cell2(oldname, "");
    vals_mapset = G_find_cell2(vals_name, "");

    /* test input file existance */
	if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

	if (vals_mapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), vals_name);

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
	    G_fatal_error(_("<%s> is an illegal file name"), newname);
    newmapset = G_mapset();

    /* get size */
    nrows = G_window_rows();
    ncols = G_window_cols();

    /* open cell files */
    in_fd = G_open_cell_old(oldname, oldmapset);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), oldname);

    /* get map type */
    map_type = DCELL_TYPE;

    /* copy color table */
    copycolr = (G_read_colors(oldname, oldmapset, &colr) > 0);

    /* get key value */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get the method */
    for (method = 0; (p = menu[method].name); method++)
	if ((strcmp(p, parm.method->answer) == 0))
	    break;
    if (!p) {
	G_warning(_("<%s=%s> unknown %s"),
		  parm.method->key, parm.method->answer, parm.method->key);
	G_usage();
	exit(EXIT_FAILURE);
    }

    /* establish the newvalue routine */
    stat_method = menu[method].method;

    /* get number of cell-neighbors */
    neighb_count = flag.adjacent->answer ? 8 : 4;

    /* allocate the cell buffers */
    cells = (Coords *) G_malloc(nrows * ncols * sizeof(Coords));
    actpos = cells;
    fragments = (Coords **) G_malloc(nrows * ncols * sizeof(Coords *));
    fragments[0] = cells;
    flagbuf = (int *)G_malloc(nrows * ncols * sizeof(int));
    result = G_allocate_d_raster_buf();

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
    out_fd = G_open_raster_new(newname, map_type);
    if (out_fd < 0)
	    G_fatal_error(_("Cannot create raster map <%s>"), newname);

    fprintf(stderr, "Percent complete ... ");

    /* create flag buffer */
    for (row = 0; row < nrows; row++) {
	G_get_d_raster_row(in_fd, result, row);
	for (col = 0; col < ncols; col++) {
	    if (result[col] == keyval)
		flagbuf[row * ncols + col] = 1;
	}
    }

    /* close cell file */
    G_close_cell(in_fd);

    /* find fragments */
    fragcount = 0;
    for (row = 0; row < nrows; row++) {
	/* display progress */
	G_percent(row, nrows, 2);

	for (col = 0; col < ncols; col++) {
	    if (flagbuf[row * ncols + col] == 1) {
		fragcount++;
		writeFrag(row, col, neighb_count);
		fragments[fragcount] = actpos;
	    }
	}
    }

    G_percent(1, 1, 2);

    /* open patch-values file */
    in_fd = G_open_cell_old(vals_name, vals_mapset);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), vals_name);

    G_message("Read patch-values...");

    /* read patch-values */
    valsbuf = (DCELL *) G_malloc(fragcount * sizeof(DCELL));
    for (i = 0; i < fragcount; i++) {
	col = fragments[i]->x;
	row = fragments[i]->y;

	G_percent(i, fragcount, 2);

	G_get_d_raster_row(in_fd, result, row);
	valsbuf[i] = result[col];
    }

    /* perform actual function on the patches */
    values = (DCELL *) G_malloc(fragcount * sizeof(DCELL));
    compute_values(values, min, max, stat_method);

    /* write the output file */
    for (row = 0; row < nrows; row++) {
	G_set_d_null_value(result, ncols);

	for (i = 0; i < fragcount; i++) {
	    for (actpos = fragments[i]; actpos < fragments[i + 1]; actpos++) {
		if (actpos->y == row) {
		    result[actpos->x] = values[i];
		}
	    }
	}

	G_put_d_raster_row(out_fd, result);
    }

    G_percent(row, nrows, 2);

    G_close_cell(in_fd);
    G_close_cell(out_fd);

    G_free(cells);
    G_free(fragments);
    G_free(flagbuf);
    G_free(values);
    G_free(valsbuf);

    G_init_cats(0, title, &cats);
    G_write_cats(newname, &cats);

    if (copycolr)
	G_write_colors(newname, newmapset, &colr);

    exit(EXIT_SUCCESS);
}
