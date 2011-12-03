
/****************************************************************************
 *
 * MODULE:			r.stream.pos
 * AUTHOR(S):		Jarek Jasiewicz jarekj amu.edu.pl
 *							 
 * PURPOSE:			Helper module to calculate pixel positon (downstream) on stream route. Pr
 *							It use r.stream.extract or r.watershed output files: stream and direction. 
 * 							Usefull in statistical computation with R.
 *
 * COPYRIGHT:		 (C) 2002,2009 by the GRASS Development Team
 *
 *								 This program is free software under the GNU General Public
 *								 License (>=v2). Read the file COPYING that comes with GRASS
 *								 for details.
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
    struct Option *in_dir_opt, *in_stm_opt, *in_multipier, *out_str_length, *out_str;	/* options */
    struct Flag *out_seq;	/* flags */

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("stream, order, route azimuth, route direction");
    module->description =
	_("Route azimuth, direction and relation to streams of higher order");

    /*input option direction is reqired, acummulation is optional */

    in_stm_opt = G_define_option();	/* input stream mask file - optional */
    in_stm_opt->key = "stream";	/* required if strahler stream order is calculated for existing stream network */
    in_stm_opt->type = TYPE_STRING;
    in_stm_opt->required = YES;	/* for now; TO DO: is planned to be optional */
    in_stm_opt->gisprompt = "old,cell,raster";
    in_stm_opt->description =
	"Name of stream mask input map (r.watershed or r.stream.extract)";

    in_dir_opt = G_define_option();	/* input directon file */
    in_dir_opt->key = "dir";
    in_dir_opt->type = TYPE_STRING;
    in_dir_opt->required = YES;
    in_dir_opt->gisprompt = "old,cell,raster";
    in_dir_opt->description =
	"Name of direction input map (r.watershed or r.stream.extract)";

    in_multipier = G_define_option();
    in_multipier->key = "multipier";
    in_multipier->label = _("Multipier to store stream index value");
    in_multipier->description = _("Must be > 0");
    in_multipier->required = YES;
    in_multipier->answer = "1000";
    in_multipier->type = TYPE_INTEGER;

    out_str = G_define_option();
    out_str->key = "cells";
    out_str->label = _("File to store pixel's position");
    out_str->required = NO;
    out_str->answer = NULL;
    out_str->type = TYPE_STRING;
    out_str->gisprompt = "new,cell,raster";

    out_str_length = G_define_option();
    out_str_length->key = "lengths";
    out_str_length->label = _("File to store current stream length");
    out_str_length->required = NO;
    out_str_length->answer = NULL;
    out_str_length->type = TYPE_STRING;
    out_str_length->gisprompt = "new,cell,raster";

    out_seq = G_define_flag();
    out_seq->key = 's';
    out_seq->description = _("Create new stream category sequence");

    if (G_parser(argc, argv))	/* parser */
	exit(EXIT_FAILURE);

    if (!out_str->answer && !out_str_length->answer)
	G_fatal_error
	    ("You must select one or more output maps: cells or lengths or both ");

    G_get_window(&window);

    /* stores input options to variables */
    in_dirs = in_dir_opt->answer;
    in_streams = in_stm_opt->answer;
    out_streams_length = out_str_length->answer;
    out_streams = out_str->answer;
    seq_cats = (out_seq->answer == 0);

    multipier = atoi(in_multipier->answer);
    if (multipier <= 0)
	G_fatal_error("Multipier must be > 0");

    /* stores output options to variables */

    nrows = G_window_rows();
    ncols = G_window_cols();

    create_base_maps();
    find_inits();
    calculate();

    if (out_streams_length) {
	set_null_f(streams_length);
	write_maps_f(out_streams_length, streams_length);
    }

    if (out_streams) {
	set_null_c(streams);
	write_maps_c(out_streams, streams);
    }
    exit(EXIT_SUCCESS);
}
