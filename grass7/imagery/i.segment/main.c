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

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/glocale.h> /* message translation */
#include "iseg.h"

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

	parse_args(argc, argv, &files, &functions);
	/* Write Segmentation Function Next Week !!! */
    write_output(&files);
    
	G_done_msg("Number of segments created: ");
	
	exit(EXIT_SUCCESS);
}
