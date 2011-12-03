
/****************************************************************************
 *
 * MODULE:			 r.stream.angle
 * AUTHOR(S):		 Jarek Jasiewicz jarekj amu.edu.pl
 *							 
 * PURPOSE:			 Calculate streams orientation and angles between streams and its
 *               tributuaries. For stream direction it use algorithim to divide
 *               particular streams of same order  into near-stright line
 *               segments.
 * 				
 *							
 *
 * COPYRIGHT:		 (C) 2002,2009 by the GRASS Development Team
 *
 *							 This program is free software under the GNU General Public
 *							 License (>=v2). Read the file COPYING that comes with GRASS
 *							 for details.
 *
 *****************************************************************************/
#define MAIN
#include <grass/glocale.h>
#include "global.h"

/*
 * main function *
 */
int main(int argc, char *argv[])
{
    struct GModule *module;	/* GRASS module for parsing arguments */
    struct Option *in_dir_opt, *in_stm_opt,	/* streams */
     *in_elev_opt,		/* streams */
     *in_length, *in_outlet, *in_threshold, *in_ordering, *out_segments;	/* options */
    struct Flag *out_rad, *out_ext;

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("stream topology, route azimuth, route direction");
    module->description =
	_("Route azimuth, direction and relation to streams of higher order");

    /*input option direction is reqired, acummulation is optional */

    in_stm_opt = G_define_option();
    in_stm_opt->key = "stream";
    in_stm_opt->type = TYPE_STRING;
    in_stm_opt->required = YES;
    in_stm_opt->gisprompt = "old,cell,raster";
    in_stm_opt->description =
	"Name of stream mask input map (r.watershed or r.stream.extract)";

    in_dir_opt = G_define_option();	/* input directon file */
    in_dir_opt->key = "dirs";
    in_dir_opt->type = TYPE_STRING;
    in_dir_opt->required = YES;
    in_dir_opt->gisprompt = "old,cell,raster";
    in_dir_opt->description =
	"Name of direction input map (r.watershed or r.stream.extract)";

    in_elev_opt = G_define_option();	/* input directon file */
    in_elev_opt->key = "elev";
    in_elev_opt->type = TYPE_STRING;
    in_elev_opt->required = NO;
    in_elev_opt->gisprompt = "old,cell,raster";
    in_elev_opt->answer = NULL;
    in_elev_opt->description = "Name of elevation input map";

    in_ordering = G_define_option();
    in_ordering->key = "order";
    in_ordering->description = "Stream ordering method";
    in_ordering->type = TYPE_STRING;
    in_ordering->required = YES;
    in_ordering->options = "none,hack,horton,strahler";
    in_ordering->answer = "none";

    in_length = G_define_option();
    in_length->key = "length";
    in_length->label = _("Search length to calculat direction");
    in_length->description = _("Must be > 0");
    in_length->required = YES;
    in_length->answer = "15";
    in_length->type = TYPE_INTEGER;

    in_outlet = G_define_option();
    in_outlet->key = "skip";
    in_outlet->label = _("Skip segments shorter than");
    in_outlet->description = _("Must be >= 0");
    in_outlet->required = YES;
    in_outlet->answer = "5";
    in_outlet->type = TYPE_INTEGER;

    in_threshold = G_define_option();
    in_threshold->key = "treshold";
    in_threshold->label =
	_("Max angle (degrees) beetwen stream segments to ");
    in_threshold->description = _("Must be > 0");
    in_threshold->required = YES;
    in_threshold->answer = "150";
    in_threshold->type = TYPE_DOUBLE;

    out_segments = G_define_option();
    out_segments->key = "seg_vector";
    out_segments->label = _("Vector to store new network with segments");
    out_segments->required = YES;
    out_segments->answer = NULL;
    out_segments->gisprompt = "new,vector,vector";

    out_rad = G_define_flag();
    out_rad->key = 'r';
    out_rad->description = _("Output angles in radians (default: degrees)");

    out_ext = G_define_flag();
    out_ext->key = 'e';
    out_ext->description =
	_("Extended topology (default: calculate direction only)");

    if (G_parser(argc, argv))	/* parser */
	exit(EXIT_FAILURE);

    G_get_window(&window);

    /* stores input options to variables */
    in_dirs = in_dir_opt->answer;
    in_streams = in_stm_opt->answer;
    in_elev = in_elev_opt->answer;

    out_vector = out_segments->answer;

    seg_length = atoi(in_length->answer);
    seg_treshold = atof(in_threshold->answer);
    seg_outlet = atoi(in_outlet->answer);

    radians = (out_rad->answer != 0);
    extended = (out_ext->answer != 0);

    if (seg_length <= 0)
	G_fatal_error("Search's length must be > 0");
    if (seg_treshold < 0 || seg_treshold > 180)
	G_fatal_error("Treshold must be between 0 and 180");
    if (seg_outlet < 0)
	G_fatal_error("Segment's length must be >= 0");
    if (extended && !in_elev)
	G_fatal_error("For extended topology elevation map is required");

    seg_treshold = deg2rad(seg_treshold);

    /* stores output options to variables */

    if (!strcmp(in_ordering->answer, "none"))
	ordering = NONE;
    else if (!strcmp(in_ordering->answer, "hack"))
	ordering = HACK;
    else if (!strcmp(in_ordering->answer, "horton"))
	ordering = HORTON;
    else if (!strcmp(in_ordering->answer, "strahler"))
	ordering = STRAHLER;

    nrows = G_window_rows();
    ncols = G_window_cols();

    create_base_maps();
    stream_number();

    stack_max = stream_num;	/* stack's size depends on number of streams */
    G_begin_distance_calculations();
    init_streams();
    find_nodes();
    do_cum_length();
    strahler();
    if (ordering == HORTON)
	horton();
    if (ordering == HACK)
	hack();

    if (extended) {
	G_message("Calculate tangents at stream joins...");
	calc_tangent(ordering);
    }

    G_message("Calculate segments...");
    do_segments(seg_common, ordering);
    if (extended)
	add_missing_dirs(ordering);
    close_vector();

    exit(EXIT_SUCCESS);
}
