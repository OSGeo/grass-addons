/*
 ****************************************************************************
 *
 * MODULE:       r.pi.searchtime.mw
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Individual-based dispersal model for connectivity analysis
 *                           - time-based - within a moving window. Based on r.pi.searchtime
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

struct statmethod
{
    f_statmethod *method;	/* routine to compute new value */
    char *name;			/* method name */
    char *text;			/* menu display - full description */
    char *suffix;		/* output suffix */
};

static struct statmethod statmethods[] = {
    {average, "average", "average of values", "avg"},
    {variance, "variance", "variance of values", "var"},
    {std_deviat, "standard deviation", "standard deviation of values", "dev"},
    {median, "median", "median of values", "med"},
    {min, "min", "minimum of values", "min"},
    {max, "max", "maximum of values", "max"},
    {0, 0, 0, 0}
};

int main(int argc, char *argv[])
{
    /* input */
    char *oldname;
    const char *oldmapset;

    /* costmap */
    char *costname;
    const char *costmapset;

    /* output */
    char *newname;
    char *iminame;

    /* in and out file pointers */
    int in_fd, out_fd;

    /* parameters */
    int size;
    int stats[GNAME_MAX];
    f_statmethod **methods;
    int stat_count;
    int keyval;

    /* maps */
    int *map;
    DCELL *costmap;

    /* helper variables */
    int row, col;
    int sx, sy;
    CELL *result;
    DCELL *d_res;
    DCELL *values;
    int nbr_count;
    int i;
    Coords *p;
    char *str;
    int method;
    char outname[GNAME_MAX];
    int fragcount;
    int n;
    int nx, ny;

    struct GModule *module;
    struct
    {
	struct Option *input, *costmap, *output, *out_immi;
	struct Option *keyval, *step_length, *perception, *multiplicator, *n;
	struct Option *percent, *stats, *maxsteps, *size;
	struct Option *title;
    } parm;
    struct
    {
	struct Flag *adjacent, *cost;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    module->description =
	_("Individual-based dispersal model for connectivity analysis (time-based) using moving window");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.costmap = G_define_option();
    parm.costmap->key = "suitability";
    parm.costmap->type = TYPE_STRING;
    parm.costmap->required = NO;
    parm.costmap->gisprompt = "old,cell,raster";
    parm.costmap->description =
	_("Name of the costmap with values from 0-100");
    parm.costmap->guisection = _("Optional");

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.out_immi = G_define_option();
    parm.out_immi->key = "out_immi";
    parm.out_immi->type = TYPE_STRING;
    parm.out_immi->required = NO;
    parm.out_immi->gisprompt = "new,cell,raster";
    parm.out_immi->description =
	_("Name of the optional raster file for patch immigrants count");
    parm.out_immi->guisection = _("Optional");

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->description = _("Category value of the patches");
    parm.keyval->guisection = _("Required");

    parm.step_length = G_define_option();
    parm.step_length->key = "step_length";
    parm.step_length->type = TYPE_INTEGER;
    parm.step_length->required = YES;
    parm.step_length->description =
	_("Length of a single step measured in pixels");
    parm.step_length->guisection = _("Required");

    parm.perception = G_define_option();
    parm.perception->key = "perception";
    parm.perception->type = TYPE_INTEGER;
    parm.perception->required = NO;
    parm.perception->description = _("Perception range");
    parm.perception->guisection = _("Optional");

    parm.multiplicator = G_define_option();
    parm.multiplicator->key = "multiplicator";
    parm.multiplicator->type = TYPE_DOUBLE;
    parm.multiplicator->required = NO;
    parm.multiplicator->description = _("Attractivity of patches [1-inf]");
    parm.multiplicator->guisection = _("Optional");

    parm.n = G_define_option();
    parm.n->key = "n";
    parm.n->type = TYPE_INTEGER;
    parm.n->required = YES;
    parm.n->description = _("Number of individuals");
    parm.n->guisection = _("Required");

    parm.percent = G_define_option();
    parm.percent->key = "percent";
    parm.percent->type = TYPE_DOUBLE;
    parm.percent->required = YES;
    parm.percent->description =
	_("Percentage of individuals which must have arrived successfully"
	  " to stop the model-run");
    parm.percent->guisection = _("Required");

    parm.stats = G_define_option();
    parm.stats->key = "stats";
    parm.stats->type = TYPE_STRING;
    parm.stats->required = YES;
    parm.stats->multiple = YES;
    str = G_malloc(1024);
    for (n = 0; statmethods[n].name; n++) {
	if (n)
	    strcat(str, ",");
	else
	    *str = 0;
	strcat(str, statmethods[n].name);
    }
    parm.stats->options = str;
    parm.stats->description =
	_("Statistical method to perform on the pathlengths of the individuals");
    parm.stats->guisection = _("Required");

    parm.maxsteps = G_define_option();
    parm.maxsteps->key = "maxsteps";
    parm.maxsteps->type = TYPE_INTEGER;
    parm.maxsteps->required = NO;
    parm.maxsteps->description = _("Maximum steps for each individual");
    parm.maxsteps->guisection = _("Optional");

    parm.size = G_define_option();
    parm.size->key = "size";
    parm.size->type = TYPE_INTEGER;
    parm.size->required = NO;
    parm.size->description = _("Size of the moving window");
    parm.size->guisection = _("Optional");

    parm.title = G_define_option();
    parm.title->key = "title";
    parm.title->key_desc = "\"phrase\"";
    parm.title->type = TYPE_STRING;
    parm.title->required = NO;
    parm.title->description = _("Title for resultant raster map");
    parm.title->guisection = _("Optional");

    flag.adjacent = G_define_flag();
    flag.adjacent->key = 'a';
    flag.adjacent->description =
	_("Set for 8 cell-neighbors. 4 cell-neighbors are default");
    flag.adjacent->guisection = _("Required");

    flag.cost = G_define_flag();
    flag.cost->key = 'c';
    flag.cost->description =
	_("Include cost of the path in the calculation of steps");
    flag.cost->guisection = _("Required");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* initialize random generator */
    srand(time(NULL));

    /* get name of input file */
    oldname = parm.input->answer;

    /* test input files existance */
    oldmapset = G_find_raster2(oldname, "");
    if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

    /* get name of costmap */
    costname = parm.costmap->answer;
    costmapset = NULL;

    /* test costmap existance */
    if (costname && (costmapset = G_find_raster2(costname, "")) == NULL)
	G_fatal_error(_("Raster map <%s> not found"), costname);
    /* get keyval */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get step_length */
    sscanf(parm.step_length->answer, "%d", &step_length);

    /* get perception_range */
    if (parm.perception->answer) {
	sscanf(parm.perception->answer, "%d", &perception_range);
    }
    else {
	perception_range = step_length;
    }

    /* get multiplicator */
    if (parm.multiplicator->answer) {
	sscanf(parm.multiplicator->answer, "%lf", &multiplicator);
    }
    else {
	multiplicator = 1.0;
    }

    /* get n */
    sscanf(parm.n->answer, "%d", &n);

    /* get size */
    if (parm.size->answer) {
	sscanf(parm.size->answer, "%d", &size);
    }
    else {
	size = 0;
    }

    /* get percent */
    sscanf(parm.percent->answer, "%lf", &percent);

    /* get number of cell-neighbors */
    nbr_count = flag.adjacent->answer ? 8 : 4;

    /* get include_cost */
    include_cost = flag.cost->answer;

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
	G_fatal_error(_("<%s> is an illegal file name"), newname);

    /* check if the immigrants file name is correct */
    iminame = parm.out_immi->answer;

    if (iminame && G_legal_filename(iminame) < 0)
	G_fatal_error(_("<%s> is an illegal file name"), iminame);

    /* get size */
    sx = Rast_window_cols();
    sy = Rast_window_rows();

    /* get maxsteps */
    if (parm.maxsteps->answer != NULL) {
	sscanf(parm.maxsteps->answer, "%d", &maxsteps);
    }
    else {
	maxsteps = 10 * sqrt(sx * sx + sy * sy) / step_length;
    }

    /* scan all statmethod answers */
    stat_count = 0;
    while (parm.stats->answers[stat_count] != NULL) {
	/* get actual method */
	for (method = 0; (str = statmethods[method].name); method++)
	    if (strcmp(str, parm.stats->answers[stat_count]) == 0)
		break;
	if (!str) {
	    G_warning(_("<%s=%s> unknown %s"),
		      parm.stats->key, parm.stats->answers[stat_count],
		      parm.stats->key);
	    G_usage();
	    exit(EXIT_FAILURE);
	}

	stats[stat_count] = method;

	stat_count++;
    }

    /* test output */
    /*      fprintf(stderr, "TEST OUTPUT : \n");
       fprintf(stderr, "input = %s\n", oldname);
       fprintf(stderr, "output = %s\n", newname);
       fprintf(stderr, "costmap = %s\n", costname);
       fprintf(stderr, "keyval = %d\n", keyval);
       fprintf(stderr, "step_length = %d\n", step_length);
       fprintf(stderr, "n = %d\n", n);
       fprintf(stderr, "percent = %0.2f\n", percent);
       fprintf(stderr, "maxsteps = %d\n", maxsteps); 
       fprintf(stderr, "Difference stats: ");
       for(i = 0; i < dif_stat_count; i++) {
       if(i > 0) fprintf(stderr, ",");
       fprintf(stderr, "%s", statmethods[dif_stats[i]].name);
       }
       fprintf(stderr, "\n"); */


    /* allocate map buffers */
    map = (int *)G_malloc(sx * sy * sizeof(int));
    result = Rast_allocate_c_buf();
    costmap = (DCELL *) G_malloc(sx * sy * sizeof(DCELL));
    d_res = Rast_allocate_d_buf();
    cells = (Coords *) G_malloc(sx * sy * sizeof(Coords));
    fragments = (Coords **) G_malloc(sx * sy * sizeof(Coords *));
    fragments[0] = cells;

    /* open map */
    in_fd = Rast_open_old(oldname, oldmapset);
    if (in_fd < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), oldname);

    /* read map */
    G_message("Reading map:");
    for (row = 0; row < sy; row++) {
	Rast_get_c_row(in_fd, result, row);
	for (col = 0; col < sx; col++) {
	    if (result[col] == keyval)
		map[row * sx + col] = 1;
	}

	G_percent(row, sy, 2);
    }
    G_percent(1, 1, 2);

    /* close map */
    Rast_close(in_fd);

    /* test output */
    /*      G_message("map:\n");
       print_buffer(map, sx, sy); */

    /* if costmap specified, read costmap */
    if (costname != NULL) {
	/* open costmap */
	in_fd = Rast_open_old(costname, costmapset);
	if (in_fd < 0)
	    G_fatal_error(_("Unable to open raster map <%s>"), costname);

	/* read costmap */
	G_message("Reading costmap:");
	for (row = 0; row < sy; row++) {
	    Rast_get_d_row(in_fd, d_res, row);
	    for (col = 0; col < sx; col++) {
		costmap[row * sx + col] = d_res[col];
	    }

	    G_percent(row, sy, 2);
	}
	G_percent(1, 1, 2);

	/* close costmap */
	Rast_close(in_fd);
    }
    else {
	/* if no costmap specified, fill costmap with 100 */
	for (i = 0; i < sx * sy; i++) {
	    costmap[i] = 100;
	}
    }

    /* test output */
    /*      G_message("costmap:\n");
       print_d_buffer(costmap, sx, sy); */

    /* find fragments */
    fragcount = writeFragments(fragments, map, sy, sx, nbr_count);

    /* test output */
    /*      print_fragments(); */

    /* mark each fragment with its number */
    for (i = 0; i < sx * sy; i++) {
	map[i] = -1;
    }
    for (i = 0; i < fragcount; i++) {
	for (p = fragments[i]; p < fragments[i + 1]; p++) {
	    map[p->y * sx + p->x] = i;
	}
    }

    /* test output */
    /*      print_buffer(map, sx, sy); */
    G_message("Performing search runs:");

    /* allocate space for patch immigrants */
    patch_imi = (int *)G_malloc(fragcount * sizeof(int));

    /* fill methods array */
    methods = (f_statmethod **) G_malloc(stat_count * sizeof(f_statmethod *));
    for (method = 0; method < stat_count; method++) {
	methods[method] = statmethods[stats[method]].method;
    }

    /* determine windows number */
    nx = size > 0 ? sx - size + 1 : 1;
    ny = size > 0 ? sy - size + 1 : 1;

    /* allocate values array */
    values = (DCELL *) G_malloc(stat_count * nx * ny * sizeof(DCELL));

    /* perform search */
    perform_search(values, map, costmap, size, methods, stat_count, n, fragcount, sx, sy);

    /* free methods array */
    G_free(methods);

    /*G_message("bump");
       G_free(cells);
       G_free(fragments);
       G_message("bump"); */

    G_message("Writing output...");
    if (size == 0) {
	for (method = 0; method < stat_count; method++) {
	    fprintf(stdout, "statmethod = %s: value = %f\n",
		    statmethods[stats[method]].name, values[method]);
	}
    }
    else {
	for (method = 0; method < stat_count; method++) {

	    /* open the new cellfile  */
	    sprintf(outname, "%s_%s", newname,
		    statmethods[stats[method]].suffix);
	    out_fd = Rast_open_new(outname, DCELL_TYPE);
	    if (out_fd < 0)
		G_fatal_error(_("Cannot create raster map <%s>"), outname);

	    /* write the output file */
	    for (row = 0; row < sy; row++) {
		Rast_set_d_null_value(d_res, sx);

		if (row >= size / 2 && row < ny + size / 2) {
		    for (col = 0; col < nx; col++) {
			d_res[col + size / 2] =
			    values[(method * ny + row - size / 2) * nx + col];
		    }
		}

		Rast_put_d_row(out_fd, d_res);

		G_percent(row + 1, sy, 1);
	    }

	    /* close output */
	    Rast_close(out_fd);
	}
	G_percent(100, 100, 2);
    }

    /* open the new cellfile  */
    if (iminame) {
	out_fd = Rast_open_new(iminame, DCELL_TYPE);
	if (out_fd < 0)
	    G_fatal_error(_("Cannot create raster map <%s>"), iminame);

	/* write the output file */
	for (row = 0; row < sy; row++) {
	    Rast_set_d_null_value(d_res, sx);

	    for (i = 0; i < fragcount; i++) {
		for (p = fragments[i]; p < fragments[i + 1]; p++) {
		    if (p->y == row) {
			d_res[p->x] = patch_imi[i];
		    }
		}
	    }

	    Rast_put_d_row(out_fd, d_res);

	    G_percent(row, sy, 2);
	}

	G_percent(100, 100, 2);

	/* close output */
	Rast_close(out_fd);
    }

    /* free allocated resources */
    G_free(values);
    G_free(map);
    G_free(costmap);
    G_free(cells);
    G_free(fragments);
    G_free(patch_imi);

    exit(EXIT_SUCCESS);
}
