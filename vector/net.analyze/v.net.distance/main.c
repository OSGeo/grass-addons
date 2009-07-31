
/****************************************************************
 *
 * MODULE:     v.net.distance
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    Computes shortest distance via the network between
 *             the given sets of features.
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

int main(int argc, char *argv[])
{
    struct Map_info In, Out;
    static struct line_pnts *Points;
    struct line_cats *Cats;
    char *mapset;
    struct GModule *module;	/* GRASS module for parsing arguments */
    struct Option *map_in, *map_out, *abcol, *afcol;
    struct Option *catf_opt, *fieldf_opt, *wheref_opt;
    struct Option *catt_opt, *fieldt_opt, *wheret_opt;
    struct Flag *geo_f;
    int with_z, geo;
    int mask_type;
    VARRAY *varrayf, *varrayt;
    int flayer, tlayer;
    dglGraph_s *graph;
    struct ilist *nodest;
    int i, nnodes, nlines;
    int *dst, *nodes_to_features;
    dglInt32_t **prev;
    struct line_cats **on_path;
    char buf[2000];

    /* Attribute table */
    dbString sql;
    dbDriver *driver;
    struct field_info *Fi;

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("network, shortest path");
    module->description =
	_
	("Find the shortest paths from a feature 'to' to every feature 'from' and various information about this realtion are uploaded to the attribute table.");

    /* Define the different options as defined in gis.h */
    map_in = G_define_standard_option(G_OPT_V_INPUT);
    map_out = G_define_standard_option(G_OPT_V_OUTPUT);

    fieldf_opt = G_define_standard_option(G_OPT_V_FIELD);
    fieldf_opt->key = "from_layer";
    fieldf_opt->description = _("From layer");
    catf_opt = G_define_standard_option(G_OPT_V_CATS);
    catf_opt->key = "from_cats";
    catf_opt->description = _("From category values");
    wheref_opt = G_define_standard_option(G_OPT_WHERE);
    wheref_opt->key = "from_where";
    wheref_opt->description =
	_("From WHERE conditions of SQL statement without 'where' keyword");

    fieldt_opt = G_define_standard_option(G_OPT_V_FIELD);
    fieldt_opt->key = "to_layer";
    fieldt_opt->description = _("To layer");
    catt_opt = G_define_standard_option(G_OPT_V_CATS);
    catt_opt->key = "to_cats";
    catt_opt->description = _("To category values");
    wheret_opt = G_define_standard_option(G_OPT_WHERE);
    wheret_opt->key = "to_where";
    wheret_opt->description =
	_("To WHERE conditions of SQL statement without 'where' keyword");

    afcol = G_define_option();
    afcol->key = "afcolumn";
    afcol->type = TYPE_STRING;
    afcol->required = YES;
    afcol->description = _("Arc forward/both direction(s) cost column");

    abcol = G_define_option();
    abcol->key = "abcolumn";
    abcol->type = TYPE_STRING;
    abcol->required = NO;
    abcol->description = _("Arc backward direction cost column");

    geo_f = G_define_flag();
    geo_f->key = 'g';
    geo_f->description =
	_("Use geodesic calculation for longitude-latitude locations");


    /* options and flags parser */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    /* TODO: make an option for this */
    mask_type = GV_POINT | GV_LINE | GV_BOUNDARY;

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    Vect_check_input_output_name(map_in->answer, map_out->answer,
				 GV_FATAL_EXIT);

    if ((mapset = G_find_vector2(map_in->answer, "")) == NULL)
	G_fatal_error(_("Vector map <%s> not found"), map_in->answer);

    Vect_set_open_level(2);

    if (1 > Vect_open_old(&In, map_in->answer, mapset))
	G_fatal_error(_("Unable to open vector map <%s>"),
		      G_fully_qualified_name(map_in->answer, mapset));

    with_z = Vect_is_3d(&In);

    if (0 > Vect_open_new(&Out, map_out->answer, with_z)) {
	Vect_close(&In);
	G_fatal_error(_("Unable to create vector map <%s>"), map_out->answer);
    }


    if (geo_f->answer) {
	geo = 1;
	if (G_projection() != PROJECTION_LL)
	    G_warning(_("The current projection is not longitude-latitude"));
    }
    else
	geo = 0;


    nnodes = Vect_get_num_nodes(&In);
    nlines = Vect_get_num_lines(&In);

    dst = (int *)G_calloc(nnodes + 1, sizeof(int));
    prev = (dglInt32_t **) G_calloc(nnodes + 1, sizeof(dglInt32_t *));
    nodes_to_features = (int *)G_calloc(nnodes + 1, sizeof(int));
    on_path =
	(struct line_cats **)G_calloc(nlines + 1, sizeof(struct line_cats *));
    if (!dst || !prev || !nodes_to_features || !on_path)
	G_fatal_error(_("Out of memory"));

    for (i = 1; i <= nlines; i++)
	on_path[i] = Vect_new_cats_struct();

    /*initialise varrays and nodes list appropriatelly */
    flayer = atoi(fieldf_opt->answer);
    tlayer = atoi(fieldt_opt->answer);
    neta_initialise_varray(&In, flayer, GV_POINT, wheref_opt->answer,
			   catf_opt->answer, &varrayf);
    neta_initialise_varray(&In, tlayer, mask_type, wheret_opt->answer,
			   catt_opt->answer, &varrayt);

    nodest = Vect_new_list();
    neta_varray_to_nodes(&In, varrayt, nodest, nodes_to_features);

    Vect_net_build_graph(&In, mask_type, 1, 0, afcol->answer, abcol->answer,
			 NULL, geo, 0);
    graph = &(In.graph);
    neta_distance_from_points(graph, nodest, dst, prev);

    /* Create table */
    Fi = Vect_default_field_info(&Out, 1, NULL, GV_1TABLE);
    Vect_map_add_dblink(&Out, 1, NULL, Fi->table, "cat", Fi->database,
			Fi->driver);
    db_init_string(&sql);
    driver = db_start_driver_open_database(Fi->driver, Fi->database);
    if (driver == NULL)
	G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
		      Fi->database, Fi->driver);

    sprintf(buf,
	    "create table %s ( cat integer, tcat integer, dist double precision)",
	    Fi->table);

    db_set_string(&sql, buf);
    G_debug(2, db_get_string(&sql));

    if (db_execute_immediate(driver, &sql) != DB_OK) {
	db_close_database_shutdown_driver(driver);
	G_fatal_error(_("Unable to create table: '%s'"), db_get_string(&sql));
    }

    if (db_create_index2(driver, Fi->table, "cat") != DB_OK)
	G_warning(_("Cannot create index"));

    if (db_grant_on_table
	(driver, Fi->table, DB_PRIV_SELECT, DB_GROUP | DB_PUBLIC) != DB_OK)
	G_fatal_error(_("Cannot grant privileges on table <%s>"), Fi->table);

    db_begin_transaction(driver);

    Vect_copy_head_data(&In, &Out);
    Vect_hist_copy(&In, &Out);
    Vect_hist_command(&Out);


    for (i = 1; i <= nlines; i++)
	if (varrayf->c[i]) {
	    int type = Vect_read_line(&In, Points, Cats, i);
	    int node, tcat, cat;
	    double cost;
	    dglInt32_t *vertex, vertex_id;
	    if (!Vect_cat_get(Cats, flayer, &cat))
		continue;
	    Vect_get_line_nodes(&In, i, &node, NULL);
	    Vect_write_line(&Out, type, Points, Cats);
	    cost = dst[node] / (double)In.cost_multip;
	    vertex = dglGetNode(graph, node);
	    vertex_id = node;
	    while (prev[vertex_id] != NULL) {
		Vect_cat_set(on_path
			     [abs(dglEdgeGet_Id(graph, prev[vertex_id]))], 1,
			     cat);
		vertex = dglEdgeGet_Head(graph, prev[vertex_id]);
		vertex_id = dglNodeGet_Id(graph, vertex);
	    }
	    Vect_read_line(&In, NULL, Cats, nodes_to_features[vertex_id]);
	    if (!Vect_cat_get(Cats, tlayer, &tcat))
		continue;
	    sprintf(buf, "insert into %s values (%d, %d, %f)", Fi->table, cat,
		    tcat, cost);

	    db_set_string(&sql, buf);
	    G_debug(3, db_get_string(&sql));
	    if (db_execute_immediate(driver, &sql) != DB_OK) {
		db_close_database_shutdown_driver(driver);
		G_fatal_error(_("Cannot insert new record: %s"),
			      db_get_string(&sql));
	    };
	}

    for (i = 1; i <= nlines; i++)
	if (on_path[i]->n_cats > 0) {
	    int type = Vect_read_line(&In, Points, NULL, i);
	    Vect_write_line(&Out, type, Points, on_path[i]);
	}

    db_commit_transaction(driver);
    db_close_database_shutdown_driver(driver);

    Vect_build(&Out);

    Vect_close(&In);
    Vect_close(&Out);

    for (i = 1; i <= nlines; i++)
	Vect_destroy_cats_struct(on_path[i]);
    G_free(on_path);
    G_free(nodes_to_features);
    G_free(dst);
    G_free(prev);

    exit(EXIT_SUCCESS);
}
