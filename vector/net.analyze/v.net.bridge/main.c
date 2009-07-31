
/****************************************************************
 *
 * MODULE:     v.net.bridge
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    Computes bridges and articulation points
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
#include <grass/neta.h>

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
    int i, bridges, articulations;
    struct ilist *bridge_list, *articulation_list;

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("network, bridges, articulation points");
    module->description = _("Computes bridges and articulation points.");

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
    method_opt->options = "bridge,articulation";
    method_opt->descriptions = _("bridge;Finds bridges;"
				 "articulation;Finds articulation points;");
    method_opt->description = _("Feature type");

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
    chcat =
	(neta_initialise_varray
	 (&In, layer, mask_type, where_opt->answer, cat_opt->answer,
	  &varray) == 1);

    Vect_net_build_graph(&In, mask_type, 0, 0, NULL, NULL, NULL, 0, 0);
    graph = &(In.graph);

    Vect_copy_head_data(&In, &Out);
    Vect_hist_copy(&In, &Out);
    Vect_hist_command(&Out);

    if (method_opt->answer[0] == 'b') {
	bridge_list = Vect_new_list();
	bridges = neta_compute_bridges(graph, bridge_list);

	G_debug(3, "Bridges: %d", bridges);

	for (i = 0; i < bridges; i++) {
	    int type =
		Vect_read_line(&In, Points, Cats, abs(bridge_list->value[i]));
	    Vect_write_line(&Out, type, Points, Cats);
	}
	Vect_destroy_list(bridge_list);
    }
    else {
	articulation_list = Vect_new_list();
	articulations = neta_articulation_points(graph, articulation_list);
	G_debug(3, "Articulation points: %d", articulations);

	for (i = 0; i < articulations; i++) {
	    double x, y, z;
	    Vect_get_node_coor(&In, articulation_list->value[i], &x, &y, &z);
	    Vect_reset_line(Points);
	    Vect_append_point(Points, x, y, z);
	    Vect_write_line(&Out, GV_POINT, Points, Cats);
	}

	Vect_destroy_list(articulation_list);
    }

    Vect_build(&Out);

    Vect_close(&In);
    Vect_close(&Out);

    exit(EXIT_SUCCESS);
}
