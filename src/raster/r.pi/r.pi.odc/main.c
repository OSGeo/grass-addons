/*
 ****************************************************************************
 *
 * MODULE:       r.pi.odc
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 * PURPOSE:      omnidirectional connectivity analysis based on polygons
 *                               (related to voronoi for points)
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
    {0, 0, 0, 0}
};

struct compensation
{
    f_compensate *method;	/* routine to compute compensated value */
    char *name;			/* method name */
    char *suffix;		/* output suffix */
};

static struct compensation compmethods[] = {
    {none, "none", "none"},
    {odd_area, "odd_area", "odd_area"},
    {area_odd, "area_odd", "area_odd"},
    {odd_perim, "odd_perim", "odd_perim"},
    {perim_odd, "perim_odd", "perim_odd"},
    {0, 0, 0}
};

int main(int argc, char *argv[])
{
    /* input */
    char *oldname, *oldmapset;
    /* output */
    char *newname, *newmapset;
    /* mask */
    char *maskname, *maskmapset;
    /* in and out file pointers */
    int in_fd, out_fd;
    FILE *out_fp;		/* ASCII - output */
    /* parameters */
    int keyval;
    int stats[GNAME_MAX];
    int stat_count;
    int ratio;
    int diag_grow;
    int compmethod;
    int neighbor_level;
    /* maps */
    int *map;
    /* other parameters */
    char *title;
    /* helper variables */
    int row, col;
    CELL *result;
    DCELL *d_res;
    DCELL *values;
    DCELL *neighb_values;
    int neighb_count;
    int i, n;
    int x, y;
    Coords *p;
    char output_name[GNAME_MAX];
    char *str;
    int method;
    f_statmethod **method_array;
    DCELL area;
    f_compensate *compensate;

    RASTER_MAP_TYPE map_type;
    struct Cell_head ch, window;

    struct GModule *module;
    struct
    {
	struct Option *input, *output, *mask;
	struct Option *keyval, *ratio, *stats;
	struct Option *neighbor_level, *title;
    } parm;
    struct
    {
	struct Flag *adjacent, *diag_grow, *diagram, *matrix;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords = _("raster");
    module->description = _("Omnidirectional connectivity analysis");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.mask = G_define_option();
    parm.mask->key = "mask";
    parm.mask->type = TYPE_STRING;
    parm.mask->required = NO;
    parm.mask->gisprompt = "old,cell,raster";
    parm.mask->description =
	_("Name of a raster file with a mask (0,1 values)");

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->description = _("Category value of the patches");

    parm.ratio = G_define_option();
    parm.ratio->key = "ratio";
    parm.ratio->type = TYPE_STRING;
    parm.ratio->required = YES;
    str = G_malloc(1024);
    for (n = 0; compmethods[n].name; n++) {
	if (n)
	    strcat(str, ",");
	else
	    *str = 0;
	strcat(str, compmethods[n].name);
    }
    parm.ratio->options = str;
    parm.ratio->description =
	_("Compensation method to perform on the values");

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
	_("Statistical method to perform on the values");

    parm.neighbor_level = G_define_option();
    parm.neighbor_level->key = "neighbor_level";
    parm.neighbor_level->type = TYPE_INTEGER;
    parm.neighbor_level->required = NO;
    parm.neighbor_level->description = _("Level of neighbors to analyse");

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

    flag.diag_grow = G_define_flag();
    flag.diag_grow->key = 'b';
    flag.diag_grow->description = _("Allow moving on diagonals");

    flag.diagram = G_define_flag();
    flag.diagram->key = 'd';
    flag.diagram->description = _("Graphical output");

    flag.matrix = G_define_flag();
    flag.matrix->key = 'm';
    flag.matrix->description = _("Adjacency matrix output");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* get name of input file */
    oldname = parm.input->answer;

    /* test input files existance */
    oldmapset = G_find_cell2(oldname, "");
    if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

    /* get name of mask file */
    maskname = parm.mask->answer;

    /* test input files existance */
    if (maskname && (maskmapset = G_find_cell2(maskname, "")) == NULL)
        G_fatal_error(_("Raster map <%s> not found"), maskname);

    /* get keyval */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get number of cell-neighbors */
    neighb_count = flag.adjacent->answer ? 8 : 4;

    /* get neighbor level */
    if (parm.neighbor_level->answer) {
	sscanf(parm.neighbor_level->answer, "%d", &neighbor_level);
    }
    else {
	neighbor_level = 1;
    }

    /* get diagonal move flag */
    diag_grow = flag.diag_grow->answer ? 1 : 0;

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
	G_fatal_error(_("<%s> is an illegal file name"), newname);
    newmapset = G_mapset();

    map_type = DCELL_TYPE;

    /* get size */
    sx = G_window_cols();
    sy = G_window_rows();

    G_message("sx = %d, sy = %d", sx, sy);

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

    /* scan all statmethod answers */
    for (compmethod = 0; (str = compmethods[compmethod].name); compmethod++)
	if (strcmp(str, parm.ratio->answer) == 0)
	    break;
    if (!str) {
	G_warning(_("<%s=%s> unknown %s"),
		  parm.ratio->key, parm.ratio->answer, parm.ratio->key);
	G_usage();
	exit(EXIT_FAILURE);
    }
    compensate = compmethods[compmethod].method;

    /* allocate map buffers */
    map = (int *)G_malloc(sx * sy * sizeof(int));
    result = G_allocate_c_raster_buf();
    d_res = G_allocate_d_raster_buf();
    cells = (Coords *) G_malloc(sx * sy * sizeof(Coords));
    fragments = (Coords **) G_malloc(sx * sy * sizeof(Coords *));
    fragments[0] = cells;

    /* open map */
    in_fd = G_open_cell_old(oldname, oldmapset);
    if (in_fd < 0)
	    G_fatal_error(_("Unable to open raster map <%s>"), oldname);

    /* read map */
    G_message("Reading map:");
    for (row = 0; row < sy; row++) {
	G_get_c_raster_row(in_fd, result, row);
	for (col = 0; col < sx; col++) {
	    if (result[col] == keyval)
		map[row * sx + col] = 1;
	}

	G_percent(row, sy, 1);
    }
    G_percent(1, 1, 1);

    /*G_message("Map:");
       for (row = 0; row < sy; row++) {
       for (col = 0; col < sx; col++) {
       fprintf(stderr, "%d", map[row * sx + col]);
       }    
       fprintf(stderr, "\n");
       } */

    /* close map */
    G_close_cell(in_fd);

    /* find fragments */
    writeFragments(map, sy, sx, neighb_count);

    G_message("Found %d patches", fragcount);

    /* apply mask */
    if (maskname) {
	/* open mask */
	in_fd = G_open_cell_old(maskname, maskmapset);
	if (in_fd < 0)
	    G_fatal_error(_("Unable to open raster map <%s>"), maskname);

	/* read mask */
	for (row = 0; row < sy; row++) {
	    G_get_c_raster_row(in_fd, result, row);
	    for (col = 0; col < sx; col++) {
		if (result[col] == 1) {
		    map[row * sx + col] = TYPE_NOTHING;
		}
		else {
		    map[row * sx + col] = TYPE_NOGO;
		}
	    }

	}

	/* close mask */
	G_close_cell(in_fd);
    }
    else {
	for (i = 0; i < sx * sy; i++) {
	    map[i] = TYPE_NOTHING;
	}
    }

    /* mark patches */
    for (i = 0; i < fragcount; i++) {
	for (p = fragments[i]; p < fragments[i + 1]; p++) {
	    x = p->x;
	    y = p->y;
	    map[x + y * sx] = i;
	}
    }

    /* create voronoi diagram */
    G_message("Performing calculations:");

    adj_matrix = (int *)G_malloc(fragcount * fragcount * sizeof(int));
    values = (DCELL *) G_malloc(fragcount * sizeof(DCELL));

    memset(adj_matrix, 0, fragcount * fragcount * sizeof(int));

    voronoi(values, map, sx, sy, diag_grow);

    /* output skipped positions */
    G_message("Positions skipped: %d", empty_count);

    G_message("Writing output...");

    /*
       =============================== FOCAL PATCH =========================================
     */
    /* open the new cell file  */
    strcpy(output_name, newname);
    strcat(output_name, ".FP.area");

    out_fd = G_open_raster_new(output_name, map_type);
    if (out_fd < 0)
	    G_fatal_error(_("Cannot create raster map <%s>"), output_name);

    /* write area of focal patch */
    for (row = 0; row < sy; row++) {
	G_set_d_null_value(d_res, sx);

	for (i = 0; i < fragcount; i++) {
	    area = fragments[i + 1] - fragments[i];
	    for (p = fragments[i]; p < fragments[i + 1]; p++) {
		if (p->y == row) {
		    d_res[p->x] = area;
		}
	    }
	}

	G_put_d_raster_row(out_fd, d_res);
    }

    /* close output */
    G_close_cell(out_fd);

    /* open the new cell file  */
    strcpy(output_name, newname);
    strcat(output_name, ".FP.odd");

    out_fd = G_open_raster_new(output_name, map_type);
    if (out_fd < 0)
	    G_fatal_error(_("Cannot create raster map <%s>"), output_name);

    /* write ratio of focal patch */
    for (row = 0; row < sy; row++) {
	G_set_d_null_value(d_res, sx);

	for (i = 0; i < fragcount; i++) {
	    for (p = fragments[i]; p < fragments[i + 1]; p++) {
		if (p->y == row) {
		    d_res[p->x] = values[i];
		}
	    }
	}

	G_put_d_raster_row(out_fd, d_res);
    }

    /* close output */
    G_close_cell(out_fd);

    /* open the new cell file  */
    strcpy(output_name, newname);
    strcat(output_name, ".ratioFP.");
    strcat(output_name, compmethods[compmethod].suffix);

    out_fd = G_open_raster_new(output_name, map_type);
    if (out_fd < 0)
	    G_fatal_error(_("Cannot create raster map <%s>"), output_name);

    /* write odd of focal patch */
    for (row = 0; row < sy; row++) {
	G_set_d_null_value(d_res, sx);

	for (i = 0; i < fragcount; i++) {
	    area = fragments[i + 1] - fragments[i];
	    for (p = fragments[i]; p < fragments[i + 1]; p++) {
		if (p->y == row) {
		    d_res[p->x] = compensate(values[i], i);	/* ratio_flag ? values[i] / area : area / values[i]; */
		}
	    }
	}

	G_put_d_raster_row(out_fd, d_res);
    }

    /* close output */
    G_close_cell(out_fd);

    /*
       =============================== TARGET PATCHES =========================================
     */
    neighb_values =
	(DCELL *) G_malloc(3 * fragcount * stat_count * sizeof(DCELL));
    method_array =
	(f_statmethod **) G_malloc(stat_count * sizeof(f_statmethod *));
    for (i = 0; i < stat_count; i++) {
	method_array[i] = statmethods[stats[i]].method;
    }

    calc_neighbors(neighb_values, values, method_array, stat_count,
		   compensate, neighbor_level);

    /* write areas */
    for (method = 0; method < stat_count; method++) {
	/* open the new cell file  */
	strcpy(output_name, newname);
	strcat(output_name, ".TP.area.");
	strcat(output_name, statmethods[stats[method]].suffix);

	out_fd = G_open_raster_new(output_name, map_type);
	if (out_fd < 0)
	    G_fatal_error(_("Cannot create raster map <%s>"), output_name);

	/* write areas of target patches with current suffix for statmethod */
	for (row = 0; row < sy; row++) {
	    G_set_d_null_value(d_res, sx);

	    for (i = 0; i < fragcount; i++) {
		for (p = fragments[i]; p < fragments[i + 1]; p++) {
		    if (p->y == row) {
			d_res[p->x] = neighb_values[method * fragcount + i];
		    }
		}
	    }

	    G_put_d_raster_row(out_fd, d_res);
	}

	/* close output */
	G_close_cell(out_fd);
    }

    /* write odds */
    for (method = 0; method < stat_count; method++) {
	/* open the new cell file  */
	strcpy(output_name, newname);
	strcat(output_name, ".TP.odd.");
	strcat(output_name, statmethods[stats[method]].suffix);

	out_fd = G_open_raster_new(output_name, map_type);
	if (out_fd < 0)
	    G_fatal_error(_("Cannot create raster map <%s>"), output_name);

	/* write odd of target patches with current suffix for statmethod */
	for (row = 0; row < sy; row++) {
	    G_set_d_null_value(d_res, sx);

	    for (i = 0; i < fragcount; i++) {
		for (p = fragments[i]; p < fragments[i + 1]; p++) {
		    if (p->y == row) {
			d_res[p->x] =
			    neighb_values[stat_count * fragcount +
					  method * fragcount + i];
		    }
		}
	    }

	    G_put_d_raster_row(out_fd, d_res);
	}

	/* close output */
	G_close_cell(out_fd);
    }

    /* write ratios */
    for (method = 0; method < stat_count; method++) {
	/* open the new cell file  */
	strcpy(output_name, newname);
	strcat(output_name, ".ratioTP.");
	strcat(output_name, compmethods[compmethod].suffix);
	strcat(output_name, ".");
	strcat(output_name, statmethods[stats[method]].suffix);

	out_fd = G_open_raster_new(output_name, map_type);
	if (out_fd < 0)
	    G_fatal_error(_("Cannot create raster map <%s>"), output_name);

	/* write ratio of target patches with current suffix for statmethod */
	for (row = 0; row < sy; row++) {
	    G_set_d_null_value(d_res, sx);

	    for (i = 0; i < fragcount; i++) {
		for (p = fragments[i]; p < fragments[i + 1]; p++) {
		    if (p->y == row) {
			d_res[p->x] =
			    neighb_values[2 * stat_count * fragcount +
					  method * fragcount + i];
		    }
		}
	    }

	    G_put_d_raster_row(out_fd, d_res);
	}

	/* close output */
	G_close_cell(out_fd);
    }
    /*
       =============================== DIAGRAM =========================================
     */
    if (flag.diagram->answer) {
	/* open new cell file */
	strcpy(output_name, newname);
	strcat(output_name, ".diagram");

	out_fd = G_open_raster_new(output_name, map_type);
	if (out_fd < 0)
	    G_fatal_error(_("Cannot create raster map <%s>"), output_name);

	/* write diagram */
	for (row = 0; row < sy; row++) {
	    for (col = 0; col < sx; col++) {
		d_res[col] = map[row * sx + col];
	    }

	    G_put_d_raster_row(out_fd, d_res);
	}

	/* close output */
	G_close_cell(out_fd);
    }

    /*
       =============================== NUMBER OF NEIGHBORS =========================================
     */
    /* open new cell file */
    strcpy(output_name, newname);
    strcat(output_name, ".TP.no");

    out_fd = G_open_raster_new(output_name, map_type);
    if (out_fd < 0)
	    G_fatal_error(_("Cannot create raster map <%s>"), output_name);

    /* get neighbor count */
    getNeighborCount(values);

    /* write number of neighbors */
    for (row = 0; row < sy; row++) {
	G_set_d_null_value(d_res, sx);

	for (i = 0; i < fragcount; i++) {
	    for (p = fragments[i]; p < fragments[i + 1]; p++) {
		if (p->y == row) {
		    d_res[p->x] = values[i];
		}
	    }
	}

	G_put_d_raster_row(out_fd, d_res);
    }

    /* close output */
    G_close_cell(out_fd);

    /*
       =============================== DIAGRAM =========================================
     */
    if (flag.matrix->answer) {
	/* open new cell file */
	strcpy(output_name, newname);
	strcat(output_name, ".id");

	out_fd = G_open_raster_new(output_name, map_type);
	if (out_fd < 0)
	    G_fatal_error(_("Cannot create raster map <%s>"), output_name);

	/* write ids of patches */
	for (row = 0; row < sy; row++) {
	    G_set_d_null_value(d_res, sx);

	    for (i = 0; i < fragcount; i++) {
		for (p = fragments[i]; p < fragments[i + 1]; p++) {
		    if (p->y == row) {
			d_res[p->x] = i;
		    }
		}
	    }

	    G_put_d_raster_row(out_fd, d_res);
	}

	/* close output */
	G_close_cell(out_fd);

	/* output matrix */
	strcpy(output_name, newname);
	strcat(output_name, ".matrix");

	/* open ASCII-file */
	if (!(out_fp = fopen(output_name, "w"))) {
	    G_fatal_error(_("Error creating file <%s>"), output_name);
	}

	for (row = 0; row < fragcount; row++) {
	    for (col = 0; col < fragcount; col++) {
		fprintf(out_fp, "%d ", adj_matrix[row * fragcount + col]);
	    }

	    fprintf(out_fp, "\n");
	}

	/* close ASCII-file */
	fclose(out_fp);
    }

    /*
       =============================== END OUTPUT =========================================
     */

    /* free allocated resources */
    G_free(map);
    G_free(cells);
    G_free(fragments);
    G_free(values);
    G_free(adj_matrix);
    G_free(neighb_values);

    exit(EXIT_SUCCESS);
}
