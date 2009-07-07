
/****************************************************************
 *
 * MODULE:     v.net.connectivity
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    Vertex connectivity between two sets of nodes
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
    struct Option *map_in, *map_out;
    struct Option *cat_opt, *field_opt, *where_opt, *ncol, *set1_opt, *set2_opt;
    int chcat, with_z;
    int layer, mask_type;
    VARRAY *varray;
    dglGraph_s *graph;
    int i, nnodes, nlines, *flow, total_flow, nedges;
    struct ilist *set1_list, *set2_list, *cut;
    struct cat_list *set1_cats, *set2_cats;
    int *node_costs;

    dglGraph_s vg;

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("network, connectivity, vertex connectivity");
    module->description =
	_("Computes vertex connectivity between two sets of nodes.");

    /* Define the different options as defined in gis.h */
    map_in = G_define_standard_option(G_OPT_V_INPUT);
    map_out = G_define_standard_option(G_OPT_V_OUTPUT);

    field_opt = G_define_standard_option(G_OPT_V_FIELD);
    cat_opt = G_define_standard_option(G_OPT_V_CATS);
    where_opt = G_define_standard_option(G_OPT_WHERE);

    ncol = G_define_option();
    ncol->key = "ncolumn";
    ncol->type = TYPE_STRING;
    ncol->required = NO;
    ncol->description = _("Node capacity column");

    set1_opt = G_define_standard_option(G_OPT_V_CATS);
    set1_opt->key = "set1";
    set1_opt->required = YES;
    set1_opt->description = _("Categories of the first set");

    set2_opt = G_define_standard_option(G_OPT_V_CATS);
    set2_opt->key = "set2";
    set2_opt->required = YES;
    set2_opt->description = _("Categories of the second set");

    /* options and flags parser */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    /* TODO: make an option for this */
    mask_type = GV_LINE | GV_BOUNDARY;

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

    set1_cats = Vect_new_cat_list();
    set2_cats = Vect_new_cat_list();
    Vect_str_to_cat_list(set1_opt->answer, set1_cats);
    Vect_str_to_cat_list(set2_opt->answer, set2_cats);
    set1_list = Vect_new_list();
    set2_list = Vect_new_list();

    nlines = Vect_get_num_lines(&In);
    nnodes = Vect_get_num_nodes(&In);
    for (i = 1; i <= nlines; i++) {
	int type, cat;
	type = Vect_read_line(&In, NULL, Cats, i);
	if (type != GV_POINT)
	    continue;
	Vect_cat_get(Cats, layer, &cat);
	if (Vect_cat_in_cat_list(cat, set1_cats))
	    Vect_list_append(set1_list, i);
	if (Vect_cat_in_cat_list(cat, set2_cats))
	    Vect_list_append(set2_list, i);
    }

    if (set1_list->n_values == 0)
	G_fatal_error(_("No points with categories [%s]"), set1_opt->answer);

    if (set2_list->n_values == 0)
	G_fatal_error(_("No points with categories [%s]"), set2_opt->answer);

    neta_points_to_nodes(&In, set1_list);
    neta_points_to_nodes(&In, set2_list);

    Vect_copy_head_data(&In, &Out);
    Vect_hist_copy(&In, &Out);

    Vect_hist_command(&Out);

    Vect_net_build_graph(&In, mask_type, 0, atoi(field_opt->answer),
			 NULL, NULL, NULL, 0, 0);
    graph = &(In.graph);

    /*build new graph */
    if (ncol->answer) {
	node_costs = (int *)G_calloc(nnodes + 1, sizeof(int));
	if (!node_costs)
	    G_fatal_error(_("Out of memory"));
	neta_get_node_costs(&In, layer, ncol->answer, node_costs);
	nedges = neta_split_vertices(graph, &vg, node_costs);
	G_free(node_costs);
    }
    else
	nedges = neta_split_vertices(graph, &vg, NULL);
    graph = &vg;

    for (i = 0; i < set1_list->n_values; i++)
	set1_list->value[i] = set1_list->value[i] * 2;	/*out vertex */
    for (i = 0; i < set2_list->n_values; i++)
	set2_list->value[i] = set2_list->value[i] * 2 - 1;	/*in vertex */

    flow = (int *)G_calloc(nedges + 1, sizeof(int));
    if (!flow)
	G_fatal_error(_("Out of memory"));

    total_flow = neta_flow(graph, set1_list, set2_list, flow);
    G_debug(3, "Connectivity: %d", total_flow);
    cut = Vect_new_list();
    total_flow = neta_min_cut(graph, set1_list, set2_list, flow, cut);

    /*TODO: copy old points */
    for (i = 0; i < cut->n_values; i++)
	neta_add_point_on_node(&In, &Out, cut->value[i], Cats);

    Vect_destroy_list(cut);

    G_free(flow);
    Vect_destroy_list(set1_list);
    Vect_destroy_list(set2_list);

    Vect_build(&Out);

    Vect_close(&In);
    Vect_close(&Out);

    exit(EXIT_SUCCESS);
}
