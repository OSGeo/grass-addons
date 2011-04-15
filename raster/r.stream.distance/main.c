
/****************************************************************************
 *
 * MODULE:       r.stream.basins
 * AUTHOR(S):    Jarek Jasiewicz jarekj amu.edu.pl
 *               
 * PURPOSE:      Calculate distance and elevation over the streams and outlets 
 *               according user's input data. The elevation and distance is calculated
 *               along watercourses
 *               It uses r.stream.order stream map map and r.watershed  direction map.
 *               Stram input map shall contains streams or points oultels with or
 *               without unique categories
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
    struct Option *in_dir_opt, *in_stm_opt, *in_elev_opt, *in_method_opt, *out_dist_opt, *out_elev_opt;	/* options */
    struct Flag *out_outs, *out_sub, *out_near;	/* flags */
    char *method_name[] = { "upstream", "downstream" };

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("stream, order, catchments");
    module->description =
	_("Calculate distance to and elevation above streams \
    and outlets according user input. It can work in stream mode where target are streams and outlets mode \
    where targets are outlets");

    in_stm_opt = G_define_option();	/* input stream mask file - optional */
    in_stm_opt->key = "stream";
    in_stm_opt->type = TYPE_STRING;
    in_stm_opt->required = YES;	/* for now; TO DO: is planned to be optional */
    in_stm_opt->gisprompt = "old,cell,raster";
    in_stm_opt->description = "Name of streams (outlets) mask input map";

    in_dir_opt = G_define_option();	/* input directon file */
    in_dir_opt->key = "dir";
    in_dir_opt->type = TYPE_STRING;
    in_dir_opt->required = YES;
    in_dir_opt->gisprompt = "old,cell,raster";
    in_dir_opt->description = "Name of flow direction input map";

    in_elev_opt = G_define_option();	/* input stream mask file - optional */
    in_elev_opt->key = "dem";
    in_elev_opt->type = TYPE_STRING;
    in_elev_opt->required = NO;
    in_elev_opt->gisprompt = "old,cell,raster";
    in_elev_opt->description = "Name of elevation map";

    in_method_opt = G_define_option();
    in_method_opt->key = "method";
    in_method_opt->description = "Calculation method";
    in_method_opt->type = TYPE_STRING;
    in_method_opt->required = YES;
    in_method_opt->options = "upstream,downstream";
    in_method_opt->answer = "downstream";

    /*  output option - at least one is reqired  */

    out_dist_opt = G_define_option();
    out_dist_opt->key = "distance";
    out_dist_opt->type = TYPE_STRING;
    out_dist_opt->required = NO;
    out_dist_opt->answer = NULL;
    out_dist_opt->gisprompt = "new,cell,raster";
    out_dist_opt->description = "Output distance map";

    out_elev_opt = G_define_option();
    out_elev_opt->key = "elevation";
    out_elev_opt->type = TYPE_STRING;
    out_elev_opt->required = NO;
    out_elev_opt->answer = NULL;
    out_elev_opt->gisprompt = "new,cell,raster";
    out_elev_opt->description = "Output elevation map";

    out_outs = G_define_flag();
    out_outs->key = 'o';
    out_outs->description =
	_("Calculate parameters for outlets (outlet mode) instead of (default) streams");

    out_sub = G_define_flag();
    out_sub->key = 's';
    out_sub->description =
	_("Calculate parameters for subbasins (ignored in stream mode)");

    out_near = G_define_flag();
    out_near->key = 'n';
    out_near->description =
	_("Calculate nearest local maximum (ignored in downstream calculation)");

    if (G_parser(argc, argv))	/* parser */
	exit(EXIT_FAILURE);

    if (!out_elev_opt->answer && !out_dist_opt->answer)
	G_fatal_error(_("You must select at least one output maps: distance and (or) elevation"));
    if (out_elev_opt->answer && !in_elev_opt->answer)
	G_fatal_error(_("If you select elevation output, DEM is required"));

    /* stores input options to variables */
    in_dirs = in_dir_opt->answer;
    in_streams = in_stm_opt->answer;
    in_elev = in_elev_opt->answer;
    out_dist = out_dist_opt->answer;
    out_elev = out_elev_opt->answer;
    outs = (out_outs->answer != 0);
    subs = (out_sub->answer != 0);
    near = (out_near->answer != 0);

    if (out_dist) {
	if (G_legal_filename(out_dist) < 0)
	    G_fatal_error(_("<%s> is an illegal file name"), out_dist);
    }
    if (out_elev) {
	if (G_legal_filename(out_elev) < 0)
	    G_fatal_error(_("<%s> is an illegal file name"), out_elev);
    }

    if (!strcmp(in_method_opt->answer, "upstream"))
	method = UPSTREAM;
    else if (!strcmp(in_method_opt->answer, "downstream"))
	method = DOWNSTREAM;

    nrows = G_window_rows();
    ncols = G_window_cols();
    G_get_window(&window);

    create_maps();
    G_begin_distance_calculations();
    find_outlets();
    reset_distance();
    free_streams();
    G_message(_("Calculate %s distance"), method_name[method]);

    if (method == UPSTREAM) {
	int j;

	fifo_max = 4 * (nrows + ncols);
	fifo_outlet = (POINT *) G_malloc((fifo_max + 1) * sizeof(POINT));

	for (j = 0; j < outlets_num; ++j) {
	    fill_catchments(outlets[j]);
	}
	G_free(fifo_outlet);
	calculate_upstream();
    }

    if (method == DOWNSTREAM) {

	/* fifo queue for contributing cell */

	fifo_max = 4 * (nrows + ncols);
	fifo_outlet = (POINT *) G_malloc((fifo_max + 1) * sizeof(POINT));
	{
	    int j;

	    for (j = 0; j < outlets_num; ++j) {
		fill_maps(outlets[j]);
	    }
	}
	G_free(fifo_outlet);
    }

    if (out_elev) {
	set_null(elevation);
	write_maps(out_elev, elevation);
    }
    if (out_dist) {
	set_null(distance);
	write_maps(out_dist, distance);
    }

    exit(EXIT_SUCCESS);
}
