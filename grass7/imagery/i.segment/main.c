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
#include <grass/raster.h>
#include "segment.h"

//~ (for my reference, order for headers), adding them only as needed...
//~ 1. Core system headers (stdio.h, ctype.h, ...)
//~ 2. Headers for non-core system components (X11, libraries).
//~ 3. Headers for core systems of the package being compiled (grass/gis.h, grass/glocale.h, ...)
//~ 4. Headers for the specific library/program being compiled (geodesic.h, ...)

struct GModule *module;
struct Option *input, *seeds, *output, *method, *threshold;       /* Establish an Option pointer for each option */
struct Flag *diagonal;        /* Establish a Flag pointer for each option */
int in_fd, out_fd;

RASTER_MAP_TYPE data_type;
int row, col, nrows, ncols;
void *inbuf;

// ? Any reasons not to use "modular global" variables for this application?

int main(int argc, char *argv[])
{
	G_gisinit(argv[0]);
		
	module = G_define_module();
	G_add_keyword(_("imagery"));
	G_add_keyword(_("segmentation"));
	module->description = _("Segments an image.");

	get_input(argc, argv);
	
	G_debug(1, "For the option <%s> you chose: <%s>",
		  input->description, input->answer);
	 
	G_debug(1, "For the option <%s> you chose: <%s>",
		  seeds->description, seeds->answer);
	
	G_debug(1, "For the option <%s> you chose: <%s>",
		  output->description, output->answer);
	
	G_debug(1, "For the option <%s> you chose: <%s>",
		  method->description, method->answer);
		  
	G_debug(1, "For the option <%s> you chose: <%s>",
		  threshold->description, threshold->answer);
	
    G_debug(1, "The value of the diagonal flag is: %d", diagonal->answer);
    
    
    
    in_fd = Rast_open_old(input->answer, "");
    data_type = Rast_get_map_type(in_fd);  /*TODO: when add group/subgroup, need to check if all input are same data_type*/
	out_fd = Rast_open_new(output->answer, data_type);
	inbuf = Rast_allocate_buf(data_type);
	
	nrows = Rast_window_rows();
	ncols = Rast_window_cols();

	for (row = 0; row < nrows; row++) {
		Rast_get_row(in_fd, inbuf, row, data_type);
		//~ for (col = 0; col < ncols; col++) {
			//~ 
		//~ }
		
		Rast_put_row(out_fd, inbuf, data_type);
	}

	G_free(inbuf);
	Rast_close(in_fd);
    Rast_close(out_fd);
    
	G_done_msg("Number of segments created: ");
	
	exit(EXIT_SUCCESS);
}
