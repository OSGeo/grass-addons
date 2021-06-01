/*
 ****************************************************************************
 *
 * MODULE:       r.pi.enn
 * AUTHOR(S):    Elshad Shirinov, Martin Wegmann
 * PURPOSE:      Analysis of n-th euclidean nearest neighbour distance
 *                               and spatial attributes of nearest neighbour patches
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

int recur_test(int, int, int);

struct menu
{
    f_func *method;
    char *name;
    char *text;
};

struct statmethod
{
    f_statmethod *method;	/* routine to compute new value */
    char *name;			/* method name */
    char *text;			/* menu display - full description */
};

static struct menu menu[] = {
    {f_dist, "distance", "distance to the patch"},
    {f_path_dist, "path_distance", "path distance from patch to patch"},
    {f_area, "area", "area of the patch"},
    {f_perim, "perimeter", "perimeter of the patch"},
    {f_shapeindex, "shapeindex", "shapeindex of the patch"},
    {0, 0, 0}
};

static struct statmethod statmethods[] = {
    {average, "average", "average of values"},
    {variance, "variance", "variance of values"},
    {std_deviat, "standard deviation", "standard deviation of values"},
    {value, "value", "according value for the patch"},
    {sum, "sum", "sum of values"},
    {0, 0, 0}
};

int main(int argc, char *argv[])
{
    /* result */
    int exitres = 0;

    /* input */
    char *newname, *oldname, *newmapset, *oldmapset;
    char fullname[GNAME_MAX];
    char title[1024];

    /* in and out file pointers */
    int in_fd;
    int out_fd;
    DCELL *result;

    /* map_type and categories */
    RASTER_MAP_TYPE map_type;
    struct Categories cats;

    int statmethod;
    int method;
    int methods[GNAME_MAX];
    f_func *compute_values;
    f_statmethod *compute_stat;

    char *p;

    /* neighbors count */
    int neighb_count;

    int row, col, i, j, m;
    int method_count;
    int readrow;
    int keyval;
    DCELL range = MAX_DOUBLE;

    int n;
    int copycolr;
    struct Colors colr;
    struct GModule *module;
    struct
    {
	struct Option *input, *output;
	struct Option *keyval, *method;
	struct Option *number, *statmethod;
	struct Option *dmout, *adj_matrix, *title;
    } parm;
    struct
    {
	struct Flag *adjacent, *quiet;
    } flag;

    DCELL *values;
    Coords *cells;
    int fragcount = 0;
    int parseres[1024];
    int number;

    struct Cell_head ch, window;

    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords = _("raster");
    module->description =
	_("Analysis of n-th Euclidean Nearest Neighbor distance.");

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
    parm.dmout->description =
	_("Output name for distance matrix and id-map (performed if not empty)");

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

    flag.quiet = G_define_flag();
    flag.quiet->key = 'q';
    flag.quiet->description = _("Run quietly");

    if (G_parser(argc, argv))
	    exit(EXIT_FAILURE);

    /* get names of input files */
    oldname = parm.input->answer;

    /* test input files existance */
    oldmapset = G_find_cell2(oldname, "");
    if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

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
    map_type = DCELL_TYPE;	/* G_raster_map_type(oldname, oldmapset); */

    /* copy color table */
    copycolr = (G_read_colors(oldname, oldmapset, &colr) > 0);

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
	    G_fatal_error("<%s=%s> unknown %s", parm.method->key,
			  parm.method->answers[method_count],
			  parm.method->key);
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
	G_fatal_error("<%s=%s> unknown %s", parm.statmethod->key,
		      parm.statmethod->answer, parm.statmethod->key);
	exit(EXIT_FAILURE);
    }

    /* establish the stat routine */
    compute_stat = statmethods[statmethod].method;

    /* get number of cell-neighbors */
    neighb_count = flag.adjacent->answer ? 8 : 4;

    /* allocate the cell buffers */
    cells = (Coords *) G_malloc(nrows * ncols * sizeof(Coords));
    actpos = cells;
    fragments = (Coords **) G_malloc(nrows * ncols * sizeof(Coords *));
    fragments[0] = cells;
    flagbuf = (int *)G_malloc(nrows * ncols * sizeof(int));
    result = G_allocate_d_raster_buf();

    /* get title, initialize the category and stat info */
    if (parm.title->answer)
	strcpy(title, parm.title->answer);
    else
	sprintf(title, "Fragmentation of file: %s", oldname);

    if ((verbose = !flag.quiet->answer))
	G_message("Loading patches...");

    /* find fragments */
    for (row = 0; row < nrows; row++) {
	G_get_d_raster_row(in_fd, result, row);
	for (col = 0; col < ncols; col++) {
	    if (result[col] == keyval)
		flagbuf[row * ncols + col] = 1;
	}

	if (verbose)
	    G_percent(row, nrows, 2);
    }

    for (row = 0; row < nrows; row++) {
	for (col = 0; col < ncols; col++) {
	    if (flagbuf[row * ncols + col] == 1) {
		fragcount++;
		writeFrag(row, col, neighb_count);
		fragments[fragcount] = actpos;
	    }
	}
    }
    if (verbose)
	G_percent(nrows, nrows, 2);

    /* generate the distance matrix */
    get_dist_matrix(fragcount);

    /* replace 0 count with (all - 1) patches */
    for (i = 0; i < number; i++)
	if (parseres[i] == 0)
	    parseres[i] = fragcount - 1;

    /* get indices of the nearest n patches (where n is the maximum number of patches to analyse) */
    get_nearest_indices(fragcount, parseres, number);

    /* for each method */
    for (m = 0; m < method_count; m++) {

	/* establish the newvalue routine */
	compute_values = menu[methods[m]].method;

	/* perform current function on the patches */
	if ((verbose = !flag.quiet->answer))
	    G_message("Performing operation %s ... ", menu[methods[m]].name);
	values = (DCELL *) G_malloc(fragcount * number * sizeof(DCELL));
	compute_values(values, fragcount, parseres, number, compute_stat);

	if (verbose)
	    G_percent(fragcount, fragcount, 2);

	/* write output files */
	if ((verbose = !flag.quiet->answer))
	    G_message("Writing output...");

	/* for all requested patches */
	for (j = 0; j < number; j++) {
	    /* open the new cellfile */
	    sprintf(fullname, "%s.NN%d.%s", newname, parseres[j],
		    menu[methods[m]].name);
	    out_fd = G_open_raster_new(fullname, DCELL_TYPE);
	    if (out_fd < 0)
	        G_fatal_error(_("Cannot create raster map <%s>"), fullname);

	    /* write data */
	    for (row = 0; row < nrows; row++) {
		G_set_d_null_value(result, ncols);

		for (i = 0; i < fragcount; i++) {
		    for (actpos = fragments[i]; actpos < fragments[i + 1];
			 actpos++) {
			if (actpos->y == row) {
			    result[actpos->x] = values[i + j * fragcount];
			}
		    }
		}

		G_put_d_raster_row(out_fd, result);

		if (verbose)
		    G_percent(row + nrows * j + nrows * number * m,
			      nrows * number * method_count, 2);
	    }

	    G_close_cell(out_fd);
	}

    }				/* for each method */

    if (verbose)
	G_percent(100, 100, 2);

    if (parm.dmout->answer) {
	exitres =
	    writeDistMatrixAndID(parm.dmout->answer, fragments, fragcount);
    }

    if (parm.adj_matrix->answer) {
	exitres =
	    writeAdjacencyMatrix(parm.adj_matrix->answer, fragments,
				 fragcount, parseres, number);
    }

    G_close_cell(in_fd);

    G_free(cells);
    G_free(fragments);
    G_free(flagbuf);
    G_free(result);

    G_free(distmatrix);
    G_free(nearest_indices);

    G_init_cats(0, title, &cats);
    G_write_cats(newname, &cats);

    if (copycolr)
	G_write_colors(newname, newmapset, &colr);

    exit(exitres);
}
