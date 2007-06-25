/****************************************************************
 * MODULE:     v.path.obstacles
 *
 * AUTHOR(S):  Maximilian Maldacker
 *  
 *
 * COPYRIGHT:  (C) 2002-2005 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>
#include "visibility.h"

int main( int argc, char* argv[])
{
	struct Map_info in, out;
	struct GModule *module;     /* GRASS module for parsing arguments */
	struct Option *input, *output; /* The input map */
	char*mapset;
	
	struct Point * points;
	struct Line * lines;
	int index;
	

	
    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("vector, path, visibility");
    module->description = _("Shortest path in free vector space");

	/* define the arguments needed */
	input = G_define_standard_option(G_OPT_V_INPUT);
	output = G_define_standard_option(G_OPT_V_OUTPUT);
	
	
	/* options and flags parser */
    if (G_parser(argc, argv))
		exit(EXIT_FAILURE);

	Vect_check_input_output_name ( input->answer, output->answer, GV_FATAL_EXIT );

	Vect_set_open_level(2);

	mapset = G_find_vector2 (input->answer, NULL); 		/* finds the map */
	
	if ( mapset == NULL )
		G_fatal_error("Map <%s> not found", input->answer );
	
	if(Vect_open_old(&in, input->answer, mapset) < 1) /* opens the map */
		G_fatal_error(_("Could not open input"));

    if (Vect_open_new(&out, output->answer, WITHOUT_Z) < 0) 
	{
		Vect_close(&in);
		G_fatal_error(_("Could not open output"));
    }

	 
	if (G_projection () == PROJECTION_LL)
		G_warning("We are in LL projection");

	index = load_lines( &in, &points, &lines);
	
	construct_visibility( points, lines, index, &out );
	
	G_free(points);
	G_free(lines);
	
	Vect_build(&out, stdout);
	Vect_close(&out);
	Vect_close(&in);
	exit(EXIT_SUCCESS);
}
