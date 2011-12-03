
/****************************************************************************
 *
 * MODULE:       r.stream.basins
 * AUTHOR(S):    Jarek Jasiewicz jarekj amu.edu.pl
 *               
 * PURPOSE:      Calculate basins according user' input data.
 *               It uses r.stream.order or r.watershed stream  map 
 *               and r.watershed  direction map.
 *               Stream input map shall contains streams or points outlels 
 *               with or without unique own categories
 *               If input stream comes from r..stream.exteract direction map 
 *               from r.stream.extract must be patched with that of r.watersheed.
 *
 * COPYRIGHT:    (C) 2002,2009 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 	  License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 	  for details.
 *
 *****************************************************************************/
#define MAIN
#include <grass/glocale.h>
#include "global.h"

/*
 * main function
 * 
 * 
 */
int main(int argc, char *argv[])
{
    struct GModule *module;	/* GRASS module for parsing arguments */
    struct Option *in_dir_opt, *in_stm_opt, *in_threshold, *out_opt;	/* options */
    struct Flag *out_back;	/* flags */
    int num_spring, link_max;

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("stream, order, catchments");
    module->description = _("Calculate basins according user input");

    in_stm_opt = G_define_option();	/* input stream mask file - optional */
    in_stm_opt->key = "stream";
    in_stm_opt->type = TYPE_STRING;
    in_stm_opt->required = YES;	/* for now; TO DO: is planned to be optional */
    in_stm_opt->gisprompt = "old,cell,raster";
    in_stm_opt->description = "Name of stream mask input map";

    in_dir_opt = G_define_option();	/* input directon file */
    in_dir_opt->key = "dir";
    in_dir_opt->type = TYPE_STRING;
    in_dir_opt->required = YES;
    in_dir_opt->gisprompt = "old,cell,raster";
    in_dir_opt->description = "Name of flow direction input map";

    in_threshold = G_define_option();
    in_threshold->key = "threshold";
    in_threshold->label = _("Minimum number of cell in stream");
    in_threshold->description = _("Must be > 0");
    in_threshold->required = YES;
    in_threshold->type = TYPE_INTEGER;

    out_opt = G_define_option();
    out_opt->key = "reduced";
    out_opt->type = TYPE_STRING;
    out_opt->required = YES;
    out_opt->answer = NULL;
    out_opt->gisprompt = "new,cell,raster";
    out_opt->description = "Output reduced stream map";

    /* Define the different flags */
    out_back = G_define_flag();
    out_back->key = 'z';
    out_back->description = _("Create zero-value background instead of NULL");

    if (G_parser(argc, argv))	/* parser */
	exit(EXIT_FAILURE);

    /* stores input options to variables */
    in_dirs = in_dir_opt->answer;
    in_streams = in_stm_opt->answer;
    out_streams = out_opt->answer;
    zeros = (out_back->answer != 0);

    threshold = atoi(in_threshold->answer);
    if (threshold <= 0)
	G_fatal_error(_("Threshold must be > 0"));

    if (G_legal_filename(out_streams) < 0)
	G_fatal_error(_("<%s> is an illegal file name"), out_streams);

    G_get_window(&window);
    nrows = G_window_rows();
    ncols = G_window_cols();
    create_maps();
    link_max = max_link();
    num_spring = find_springs(link_max);
    delete_join(num_spring);
    if (!zeros)
	set_null();
    write_map();

    exit(EXIT_SUCCESS);
}
