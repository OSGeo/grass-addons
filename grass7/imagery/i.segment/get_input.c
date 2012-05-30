/****************************************************************************
 *
 * MODULE:       i.segment
 * AUTHOR(S):    Eric Momsen <eric.momsen at gmail com>
 * PURPOSE:      Parse and validate the input
 * COPYRIGHT:    (C) 2012 by Eric Momsen, and the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the COPYING file that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

//Should this type of comment block go at the beginning of all sub files?

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "segment.h"

int get_input(int argc, char *argv[])
{
	//reference: http://grass.osgeo.org/programming7/gislib.html#Command_Line_Parsing
	
	input = G_define_standard_option(G_OPT_R_INPUT);   /* Request a pointer to memory for each option */
	input->key = "input"; /* TODO: update to allow groups.  Maybe this needs a group/subgroup variables, or we can check if the input is group/subgroup/raster */
	input->type = TYPE_STRING;
	input->required = YES;
	input->description = _("Raster map to be segmented.");
	
	seeds = G_define_standard_option(G_OPT_V_INPUT);
	seeds->key = "seeds";
	seeds->type = TYPE_STRING;
	seeds->required = NO;
	seeds->description = _("Optional vector map with starting seeds.");
	
	output = G_define_standard_option(G_OPT_R_OUTPUT);
	output->key = "output";
	output->type = TYPE_STRING;
	output->required = YES;
	output->description = _("Name of output raster map.");
//TODO: when put in a new raster map, error message:
//~ Command 'd.rast map=testing@samples' failed
//~ Details: Raster map <testing@samples> not found

//Also, that error seems to be accumulated, putting in a new output map names results in:
//~ Command 'd.rast map=testing@samples' failed
//~ Details: Raster map <testing@samples> not found
//~ Command 'd.rast map=test2@samples' failed
//~ Details: Raster map <test2@samples> not found
	
	method = G_define_option();
	method->key = "method";
	method->type = TYPE_STRING;
	method->required = NO;
	method->answer = _("region growing");
	method->options = "region growing, mean shift";
	method->description = _("Segmentation method.");
	
	threshold = G_define_option();
	threshold->key = "threshold";
	threshold->type = TYPE_DOUBLE;
	threshold->required = YES;
	threshold->description = _("Similarity threshold.");
	
	//use checker for any of the data validation steps!?
	
	if (G_parser(argc, argv))
        exit (EXIT_FAILURE);

	return 0;
}
