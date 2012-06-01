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
 *
 *               NOTE: the word "segment" is already used by the Segmentation
 *               Library for the data files/tiling, so iseg (image segmentation)
 *               will be used to refer to the image segmentation.
 * 
 * 
 *****************************************************************************/

// #include <grass/config.h>

#include <stdlib.h>
// #include <unistd.h>
#include <grass/gis.h>
//#include <grass/imagery.h>
#include <grass/glocale.h>   //defines _()  what exactly is that doing...(something about local language translation?) anything else in glocale.h that I should be aware of...
#include <grass/raster.h>
#include "iseg.h"

//~ (for my reference, order for headers), adding them only as needed...
//~ 1. Core system headers (stdio.h, ctype.h, ...)
//~ 2. Headers for non-core system components (X11, libraries).
//~ 3. Headers for core systems of the package being compiled (grass/gis.h, grass/glocale.h, ...)
//~ 4. Headers for the specific library/program being compiled (geodesic.h, ...)

int main(int argc, char *argv[])
{
	struct files files;		/* input and output file descriptors, data structure, buffers */
	struct functions functions;		/* function pointers and parameters for the calculations */
	struct GModule *module;
		
	G_gisinit(argv[0]);
		
	module = G_define_module();
	G_add_keyword(_("imagery"));
	G_add_keyword(_("segmentation"));
	module->description = _("Segments an image.");

	get_input(argc, argv, files, functions);
	
//need to update this part still:
	G_free(inbuf);
	Rast_close(in_fd);
    Rast_close(out_fd);
//
    
	G_done_msg("Number of segments created: ");
	
	exit(EXIT_SUCCESS);
}
