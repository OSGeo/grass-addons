
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
#include <grass/glocale.h>	/* message translation */
#include "iseg.h"

int main(int argc, char *argv[])
{
    struct files files;		/* input and output file descriptors, data structure, buffers */
    struct functions functions;	/* function pointers and parameters for the calculations */
    struct GModule *module;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("segmentation"));
    module->description =
	_("Outputs a single segmention map (raster) based on input values in an image group.");

    if (parse_args(argc, argv, &files, &functions) != 0)
	G_debug(1, "Error in parse_args()");	/* TODO: should these be debug or G_fatal_error() or nested if statement? want to clean up mem and temp files */

    G_debug(1, "Main: starting open_files()");
    if (open_files(&files) != 0)
	G_debug(1, "Error in open_files()");

    G_debug(1, "Main: starting create_isegs()");
    if (create_isegs(&files, &functions) != 0)
	G_debug(1, "Error in create_isegs()");

    G_debug(1, "Main: starting write_output()");
    if (write_output(&files) != 0)
	G_debug(1, "Error in write_output()");

    G_debug(1, "Main: starting close_files()");
    close_files(&files);

    /* TODO - G_fatal_error() called in sub routines - do I need to run close_files() before quitting?
     * http://rackerhacker.com/2010/03/18/sigterm-vs-sigkill/
     * "Standard C applications have a header file that contains the steps that the process should follow if it receives a particular signal. "
     *  */

    G_done_msg("Number of segments created: TODO linkm");

    exit(EXIT_SUCCESS);
}
