
/****************************************************************************
 *
 * MODULE:       r.stream.stats
 * AUTHOR(S):    Jarek Jasiewicz jarekj amu.edu.pl
 *               
 * PURPOSE:      Calculate Horton's statistics according stream network and elevation map.
 *               Program calculates: Bifuarcation ratio, length ratio, area ratio, 
 *               slope ratio and drainage density
 *               It uses r.stream.order stream map map, r.watershed  direction map. and DEM
 *               Stram input map shall contains streams ordered according Strahler's or Horton's 
 *               orders. It also can calculate Hack's laws as an option.
 *               If input stream comes from r.stream.exteract direction map 
 *               from r.stream.extract dir map must be patched with that of r.watersheed.
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
    struct Option *in_dir_opt, *in_stm_opt, *in_elev_opt;	/* options */
    struct Flag *out_hack;	/* flags */

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords =
	_("stream, order, Strahler, Horton, Hack, statisctics");
    module->description =
	_("Calculate Horton's and optionally Hack's statistics according to user input.");

    in_stm_opt = G_define_option();	/* input stream mask file - optional */
    in_stm_opt->key = "stream";
    in_stm_opt->type = TYPE_STRING;
    in_stm_opt->required = YES;	/* for now; TO DO: is planned to be optional */
    in_stm_opt->gisprompt = "old,cell,raster";
    in_stm_opt->description = "Name of streams mask input map";

    in_dir_opt = G_define_option();	/* input directon file */
    in_dir_opt->key = "dir";
    in_dir_opt->type = TYPE_STRING;
    in_dir_opt->required = YES;
    in_dir_opt->gisprompt = "old,cell,raster";
    in_dir_opt->description = "Name of flow direction input map";

    in_elev_opt = G_define_option();	/* input stream mask file - optional */
    in_elev_opt->key = "dem";
    in_elev_opt->type = TYPE_STRING;
    in_elev_opt->required = YES;
    in_elev_opt->gisprompt = "old,cell,raster";
    in_elev_opt->description = "Name of elevation map";

    /* Define the different flags */
    /*
       out_hack = G_define_flag();
       out_hack->key = 'h';
       out_hack->description = _("Calculate Hack's statistic instead of Horton's");
     */

    if (G_parser(argc, argv))	/* parser */
	exit(EXIT_FAILURE);

    /* stores input options to variables */
    in_dirs = in_dir_opt->answer;
    in_streams = in_stm_opt->answer;
    in_elev = in_elev_opt->answer;
    /*    hack = (out_hack->answer != 0); */

    nrows = G_window_rows();
    ncols = G_window_cols();
    G_get_window(&window);

    create_maps();
    init_streams();
    calculate_streams();
    calculate_basins();
    stats();
    print_stats();

    exit(EXIT_SUCCESS);
}
