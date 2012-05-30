/****************************************************************************
 *
 * MODULE:       i.segment
 * AUTHOR(S):    Eric Momsen <eric.momsen at gmail com>
 * PURPOSE:      Provide short description of module here...
 * COPYRIGHT:    (C) 2012 by Eric Momsen, and the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the COPYING file that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

// #include <grass/config.h>

#include <stdlib.h>
// #include <unistd.h>
#include <grass/gis.h>
//#include <grass/imagery.h>
#include <grass/glocale.h>   //defines _()  what exactly is that doing...(something about local language translation?) anything else in glocale.h that I should be aware of...
#include "segment.h"

//~ (for my reference, order for headers), adding them only as needed...
//~ 1. Core system headers (stdio.h, ctype.h, ...)
//~ 2. Headers for non-core system components (X11, libraries).
//~ 3. Headers for core systems of the package being compiled (grass/gis.h, grass/glocale.h, ...)
//~ 4. Headers for the specific library/program being compiled (geodesic.h, ...)

struct GModule *module;
struct Option *input, *seeds, *output, *method, *threshold;       /* Establish an Option pointer for each option */

// ? Any reasons not to use global variables for this application?

int main(int argc, char *argv[])
{
	G_gisinit(argv[0]);
		
	module = G_define_module();
	G_add_keyword(_("imagery"));
	G_add_keyword(_("segmentation"));
	module->description = _("Segments an image.");

	get_input(argc, argv);
	
	//debug/testing stuff... delete when done.
	G_message("For the option <%s> you chose: <%s>",
		  input->description, input->answer);
	 
	G_message("For the option <%s> you chose: <%s>",
		  seeds->description, seeds->answer);
	
	G_message("For the option <%s> you chose: <%s>",
		  output->description, output->answer);
	
	G_message("For the option <%s> you chose: <%s>",
		  method->description, method->answer);
		  
	G_message("For the option <%s> you chose: <%s>",
		  threshold->description, threshold->answer);
		  
	G_done_msg("Any other messages?");
	
	exit(EXIT_SUCCESS);
}
