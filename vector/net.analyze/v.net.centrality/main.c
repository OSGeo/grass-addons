
/****************************************************************
 *
 * MODULE:     v.net.centrality
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    This module computes various cetrality measures
 *
 * COPYRIGHT:  (C) 2002-2005 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>
#include <grass/dbmi.h>
#include <grass/neta.h>

void update_record(dbDriver * driver, dbString * sql, char *table, char *key,
		   char *column, double value, int cat)
{
    char buf[2000];
    sprintf(buf, "update %s set %s=%f where %s=%d", table, column, value, key,
	    cat);
    db_set_string(sql, buf);
    G_debug(3, db_get_string(sql));
    if (db_execute_immediate(driver, sql) != DB_OK) {
	db_close_database_shutdown_driver(driver);
	G_fatal_error(_("Cannot insert new record: %s"), db_get_string(sql));
    };
}

int main(int argc, char *argv[])
{
    struct Map_info In;
    struct line_cats *Cats;
    char *mapset;
    struct GModule *module;	/* GRASS module for parsing arguments */
    struct Option *map_in;
    struct Option *cat_opt, *field_opt, *where_opt, *abcol, *afcol;
    struct Option *deg_opt, *close_opt, *betw_opt, *eigen_opt;
    struct Option *iter_opt, *error_opt;
    struct Flag *geo_f;
    int chcat, with_z;
    int layer, mask_type;
    VARRAY *varray;
    dglGraph_s *graph;
    int i, geo, nnodes, nlines;
    double *deg, *close, *betw, *eigen;

    /* Attribute table */
    dbString sql;
    dbDriver *driver;
    struct field_info *Fi;

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords =
	_
	("network, centrality measures, degree, betweeness, closeness, eigenvector");
    module->description =
	_
	("Computes degree, centrality, betweeness, closeness and eigenvector cetrality measures");

    /* Define the different options as defined in gis.h */
    map_in = G_define_standard_option(G_OPT_V_INPUT);

    field_opt = G_define_standard_option(G_OPT_V_FIELD);
    cat_opt = G_define_standard_option(G_OPT_V_CATS);
    where_opt = G_define_standard_option(G_OPT_WHERE);

    afcol = G_define_option();
    afcol->key = "afcolumn";
    afcol->type = TYPE_STRING;
    afcol->required = NO;
    afcol->description = _("Arc forward/both direction(s) cost column");

    abcol = G_define_option();
    abcol->key = "abcolumn";
    abcol->type = TYPE_STRING;
    abcol->required = NO;
    abcol->description = _("Arc backward direction cost column");

    deg_opt = G_define_option();
    deg_opt->key = "degree";
    deg_opt->type = TYPE_STRING;
    deg_opt->required = NO;
    deg_opt->description = _("Degree centrality column");

    close_opt = G_define_option();
    close_opt->key = "closeness";
    close_opt->type = TYPE_STRING;
    close_opt->required = NO;
    close_opt->description = _("Closeness centrality column");

    betw_opt = G_define_option();
    betw_opt->key = "betweenness";
    betw_opt->type = TYPE_STRING;
    betw_opt->required = NO;
    betw_opt->description = _("Betweenness centrality column");

    eigen_opt = G_define_option();
    eigen_opt->key = "eigenvector";
    eigen_opt->type = TYPE_STRING;
    eigen_opt->required = NO;
    eigen_opt->description = _("Eigenvector centrality column");

    iter_opt = G_define_option();
    iter_opt->key = "iterations";
    iter_opt->answer = "1000";
    iter_opt->type = TYPE_INTEGER;
    iter_opt->required = NO;
    iter_opt->description =
	_("Maximum number of iterations to compute eigenvector centrality");

    error_opt = G_define_option();
    error_opt->key = "error";
    error_opt->answer = "0.1";
    error_opt->type = TYPE_DOUBLE;
    error_opt->required = NO;
    error_opt->description =
	_("Cuumulative error tolerance for eigenvector centrality");


    geo_f = G_define_flag();
    geo_f->key = 'g';
    geo_f->description =
	_("Use geodesic calculation for longitude-latitude locations");

    /* options and flags parser */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    /* TODO: make an option for this */
    mask_type = GV_LINE | GV_BOUNDARY;

    Cats = Vect_new_cats_struct();

    if ((mapset = G_find_vector2(map_in->answer, "")) == NULL)
	G_fatal_error(_("Vector map <%s> not found"), map_in->answer);

    Vect_set_open_level(2);

    if (1 > Vect_open_old(&In, map_in->answer, mapset))
	G_fatal_error(_("Unable to open vector map <%s>"),
		      G_fully_qualified_name(map_in->answer, mapset));

    with_z = Vect_is_3d(&In);

    if (geo_f->answer) {
	geo = 1;
	if (G_projection() != PROJECTION_LL)
	    G_warning(_("The current projection is not longitude-latitude"));
    }
    else
	geo = 0;

    /* parse filter option and select appropriate lines */
    layer = atoi(field_opt->answer);
    if (where_opt->answer) {
	if (layer < 1)
	    G_fatal_error(_("'%s' must be > 0 for '%s'"), "layer", "where");
	if (cat_opt->answer)
	    G_warning(_
		      ("'where' and 'cats' parameters were supplied, cat will be ignored"));
	chcat = 1;
	varray = Vect_new_varray(Vect_get_num_lines(&In));
	if (Vect_set_varray_from_db
	    (&In, layer, where_opt->answer, mask_type, 1, varray) == -1) {
	    G_warning(_("Unable to load data from database"));
	}
    }
    else if (cat_opt->answer) {
	if (layer < 1)
	    G_fatal_error(_("'%s' must be > 0 for '%s'"), "layer", "cat");
	varray = Vect_new_varray(Vect_get_num_lines(&In));
	chcat = 1;
	if (Vect_set_varray_from_cat_string
	    (&In, layer, cat_opt->answer, mask_type, 1, varray) == -1) {
	    G_warning(_("Problem loading category values"));
	}
    }
    else {
	chcat = 0;
	varray = NULL;
    }

    /* Open database */
    Fi = Vect_get_field(&In, layer);
    driver = db_start_driver_open_database(Fi->driver, Fi->database);
    if (driver == NULL)
	G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
		      Fi->database, Fi->driver);
    db_begin_transaction(driver);
    db_init_string(&sql);

    Vect_net_build_graph(&In, mask_type, atoi(field_opt->answer), 0,
			 afcol->answer, abcol->answer, NULL, geo, 0);
    graph = &(In.graph);
    nnodes = dglGet_NodeCount(graph);

    deg = close = betw = eigen = NULL;

    if (deg_opt->answer) {
	deg = (double *)G_calloc(nnodes + 1, sizeof(double));
	if (!deg)
	    G_fatal_error(_("Out of memory"));
    }

    if (close_opt->answer) {
	close = (double *)G_calloc(nnodes + 1, sizeof(double));
	if (!close)
	    G_fatal_error(_("Out of memory"));
    }

    if (betw_opt->answer) {
	betw = (double *)G_calloc(nnodes + 1, sizeof(double));
	if (!betw)
	    G_fatal_error(_("Out of memory"));
    }

    if (eigen_opt->answer) {
	eigen = (double *)G_calloc(nnodes + 1, sizeof(double));
	if (!eigen)
	    G_fatal_error(_("Out of memory"));
    }


    if (deg_opt->answer) {
	G_message(_("Computing degree centrality measure"));
	neta_degree_centrality(graph, deg);
    }
    if (betw_opt->answer || close_opt->answer) {
	G_message(_
		  ("Computing betweenness and/or closeness centrality measure"));
	neta_betweenness_closeness(graph, betw, close);
    }
    if (eigen_opt->answer) {
	G_message(_("Computing eigenvector centrality measure"));
	neta_eigenvector_centrality(graph, atoi(iter_opt->answer),
				    atof(error_opt->answer), eigen);
    }

    nlines = Vect_get_num_lines(&In);
    G_message(_("Writing data into the table..."));
    G_percent_reset();
    for (i = 1; i <= nlines; i++) {
	G_percent(i, nlines, 1);
	//        if(!varray->c[i])continue;
	int type = Vect_read_line(&In, NULL, Cats, i);
	if (type == GV_POINT) {
	    int cat, node;
	    if (!Vect_cat_get(Cats, layer, &cat))
		continue;
	    Vect_get_line_nodes(&In, i, &node, NULL);
	    if (deg_opt->answer)
		update_record(driver, &sql, Fi->table, Fi->key, deg_opt->answer,
			      deg[node], cat);
	    if (close_opt->answer)
		update_record(driver, &sql, Fi->table, Fi->key,
			      close_opt->answer, close[node], cat);
	    if (betw_opt->answer)
		update_record(driver, &sql, Fi->table, Fi->key,
			      betw_opt->answer, betw[node], cat);
	    if (eigen_opt->answer)
		update_record(driver, &sql, Fi->table, Fi->key,
			      eigen_opt->answer, eigen[node], cat);
	}


    }
    db_commit_transaction(driver);
    db_close_database_shutdown_driver(driver);

    if (deg)
	G_free(deg);
    if (close)
	G_free(close);
    if (betw)
	G_free(betw);
    if (eigen)
	G_free(eigen);

    Vect_close(&In);

    exit(EXIT_SUCCESS);
}
