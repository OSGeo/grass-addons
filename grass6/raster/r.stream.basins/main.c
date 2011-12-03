
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
#include "global.h"

/*
 * main function
 * 
 * 
 */
int main(int argc, char *argv[])
{
    struct GModule *module;	/* GRASS module for parsing arguments */
    struct Option *in_dir_opt, *in_coor_opt, *in_stm_opt, *in_stm_cat_opt, *in_point_opt, *out_opt;	/* options */
    struct Flag *out_back, *out_cat, *out_last;	/* flags */
    int b_test = 0;		/* test which option have been choosed: like chmod */

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("stream, order, catchments");
    module->description = _("Calculate basins according user input");

    in_dir_opt = G_define_option();	/* input directon file */
    in_dir_opt->key = "dir";
    in_dir_opt->type = TYPE_STRING;
    in_dir_opt->required = YES;
    in_dir_opt->gisprompt = "old,cell,raster";
    in_dir_opt->description = "Name of flow direction input map";

    in_coor_opt = G_define_option();	/* input coordinates de outlet */
    in_coor_opt->key = "coors";
    in_coor_opt->type = TYPE_STRING;
    in_coor_opt->key_desc = "x,y";
    in_coor_opt->answers = NULL;
    in_coor_opt->required = NO;
    in_coor_opt->multiple = YES;
    in_coor_opt->description = "Basin's outlet's coordinates: E,N";

    in_stm_opt = G_define_option();	/* input stream mask file - optional */
    in_stm_opt->key = "stream";
    in_stm_opt->type = TYPE_STRING;
    in_stm_opt->required = NO;
    in_stm_opt->gisprompt = "old,cell,raster";
    in_stm_opt->description = "Name of stream mask input map";

    in_stm_cat_opt = G_define_option();	/* input stream mask file - optional */
    in_stm_cat_opt->key = "cats";
    in_stm_cat_opt->type = TYPE_STRING;
    in_stm_cat_opt->required = NO;
    in_stm_cat_opt->multiple = YES;
    in_stm_cat_opt->description = "Create basins only for that categories:";

    in_point_opt = G_define_option();	/* input point outputs - optional */
    in_point_opt->key = "points";
    in_point_opt->type = TYPE_STRING;
    in_point_opt->required = NO;
    in_point_opt->answer = NULL;
    in_point_opt->gisprompt = "old,vector,vector";
    in_point_opt->description = "Name of vector points map";

    /*  output option - at least one is reqired  */

    out_opt = G_define_option();
    out_opt->key = "basins";
    out_opt->type = TYPE_STRING;
    out_opt->required = YES;
    out_opt->answer = NULL;
    out_opt->gisprompt = "new,cell,raster";
    out_opt->description = "Output basin map";

    /* Define the different flags */
    out_back = G_define_flag();
    out_back->key = 'z';
    out_back->description = _("Create zero-value background instead of NULL");

    /* Define the different flags */
    out_cat = G_define_flag();
    out_cat->key = 'c';
    out_cat->description =
	_("Use unique category sequence instead of input streams");

    /* Define the different flags */
    out_last = G_define_flag();
    out_last->key = 'l';
    out_last->description = _("Create basins only for last stream links");

    if (G_parser(argc, argv))	/* parser */
	exit(EXIT_FAILURE);

    if (!in_coor_opt->answers && !in_stm_opt->answer && !in_point_opt->answer)
	G_fatal_error("Basin's outlet definition is required");

    if (in_coor_opt->answers)
	b_test += 1;
    if (in_stm_opt->answer)
	b_test += 2;
    if (in_point_opt->answer)
	b_test += 4;

    if (b_test != 1 && b_test != 2 && b_test != 4)
	G_fatal_error("Only one outlet definition is allowed");

    /* stores input options to variables */
    in_dirs = in_dir_opt->answer;
    in_streams = in_stm_opt->answer;
    name_catchments = out_opt->answer;
    in_point = in_point_opt->answer;
    zeros = (out_back->answer != 0);
    cats = (out_cat->answer != 0);
    lasts = (out_last->answer != 0);

    if (G_legal_filename(name_catchments) < 0)
	G_fatal_error(_("<%s> is an illegal basin name"), name_catchments);

    G_get_window(&window);
    nrows = G_window_rows();
    ncols = G_window_cols();
    create_maps();

    switch (b_test) {
    case 1:
	G_message("Calculate basins using coordinates...");
	outlets_num = process_coors(in_coor_opt->answers);
	break;

    case 2:
	G_message("Calculate basins using streams...");
	categories = NULL;
	process_cats(in_stm_cat_opt->answers);
	find_outlets();
	break;

    case 4:
	G_message("Calculate basins using point file...");
	outlets_num = process_vector(in_point);
	break;
    }

    {
	int j;

	reset_catchments();
	fifo_max = 4 * (nrows + ncols);
	fifo_outlet = (POINT *) G_malloc((fifo_max + 1) * sizeof(POINT));

	for (j = 0; j < outlets_num; ++j) {
	    fill_catchments(outlets[j]);
	}
	G_free(fifo_outlet);
	if (!zeros)
	    set_null();
	write_catchment();
    }

    exit(EXIT_SUCCESS);
}
