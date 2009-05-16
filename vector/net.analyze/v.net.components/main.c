
/****************************************************************
 *
 * MODULE:     v.net.components
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    Computes strongly and weakly connected components
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

int weakly_connected_components(struct dglGraph_s *graph, int *component);
int strongly_connected_components(struct dglGraph_s *graph, int *component);

int main(int argc, char *argv[])
{
    struct Map_info In, Out;
    static struct line_pnts *Points;
    struct line_cats *Cats;
    char *mapset;
    struct GModule *module;	/* GRASS module for parsing arguments */
    struct Option *map_in, *map_out;
    struct Option *cat_opt, *field_opt, *where_opt, *method_opt;
    int chcat, with_z;
    int layer, mask_type;
    VARRAY *varray;
    dglGraph_s *graph;
    int *component, nnodes, type, i, nlines, components;

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("network, connected components");
    module->description =
	_("Computes strongly and weakly connected components.");

    /* Define the different options as defined in gis.h */
    map_in = G_define_standard_option(G_OPT_V_INPUT);
    map_out = G_define_standard_option(G_OPT_V_OUTPUT);

    field_opt = G_define_standard_option(G_OPT_V_FIELD);
    cat_opt = G_define_standard_option(G_OPT_V_CATS);
    where_opt = G_define_standard_option(G_OPT_WHERE);

    method_opt = G_define_option();
    method_opt->key = "method";
    method_opt->type = TYPE_STRING;
    method_opt->required = YES;
    method_opt->multiple = NO;
    method_opt->options = "weak,strong";
    method_opt->descriptions = _("weak;Weakly connected components;"
				 "strong;Strongly connected components;");
    method_opt->description = _("Type of components");

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

    Vect_net_build_graph(&In, mask_type, 0, 0, NULL, NULL, NULL, 0, 0);
    graph = &(In.graph);
    nnodes = Vect_get_num_nodes(&In);
    component = (int *)G_calloc(nnodes + 1, sizeof(int));
    if (!component) {
	G_fatal_error(_("Out of memory"));
	exit(EXIT_FAILURE);
    }
    if (method_opt->answer[0] == 'w')
	components = weakly_connected_components(graph, component);
    else
	components = strongly_connected_components(graph, component);

    G_debug(3, "Components: %d\n", components);

    Vect_copy_head_data(&In, &Out);
    Vect_hist_copy(&In, &Out);
    Vect_hist_command(&Out);

    nlines = Vect_get_num_lines(&In);
    for (i = 1; i <= nlines; i++) {
	type = Vect_read_line(&In, Points, NULL, i);
	Vect_reset_cats(Cats);
	if (type == GV_LINE || type == GV_BOUNDARY) {
	    int node1, node2;
	    Vect_get_line_nodes(&In, i, &node1, &node2);
	    if (component[node1] == component[node2]) {
		Vect_cat_set(Cats, 1, component[node1]);
	    }
	    else {
		continue;
	    }
	}
	else if (type == GV_POINT) {
	    int node;
	    Vect_get_line_nodes(&In, i, &node, NULL);
	    Vect_cat_set(Cats, 1, component[node]);
	}
	else
	    continue;
	Vect_write_line(&Out, type, Points, Cats);
    };

    Vect_build(&Out);

    Vect_close(&In);
    Vect_close(&Out);

    exit(EXIT_SUCCESS);
}
