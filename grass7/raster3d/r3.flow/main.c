
/****************************************************************************
 * 
 * MODULE:       r3.flow     
 * AUTHOR(S):    Anna Petrasova kratochanna <at> gmail <dot> com
 * PURPOSE:      Computes 3D flow lines and flow accumulation based on 3D raster map(s)
 * COPYRIGHT:    (C) 2014 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/raster3d.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/vector.h>
#include <grass/glocale.h>

#include "r3flow_structs.h"
#include "flowline.h"


static void check_vector_input_maps(struct Option *vector_opt,
				    struct Option *seed_opt)
{
    int i;

    /* Check for velocity components maps. */
    if (vector_opt->answers != NULL) {
	for (i = 0; i < 3; i++) {
	    if (vector_opt->answers[i] != NULL) {
		if (NULL == G_find_raster3d(vector_opt->answers[i], ""))
		    Rast3d_fatal_error(_("3D raster map <%s> not found"),
				       vector_opt->answers[i]);
	    }
	    else {
		Rast3d_fatal_error(_("Please provide three 3D raster maps"));
	    }
	}
    }

    if (seed_opt->answer != NULL) {
	if (NULL == G_find_vector2(seed_opt->answer, ""))
	    G_fatal_error(_("Vector seed map <%s> not found"),
			  seed_opt->answer);
    }

}

static void load_input_velocity_maps(struct Option *vector_opt,
				     RASTER3D_Map ** velocity_field,
				     RASTER3D_Region * region)
{
    int i;

    for (i = 0; i < 3; i++) {
	velocity_field[i] =
	    Rast3d_open_cell_old(vector_opt->answers[i],
				 G_find_raster3d(vector_opt->answers[i], ""),
				 region, RASTER3D_TILE_SAME_AS_FILE,
				 RASTER3D_USE_CACHE_DEFAULT);

	if (!velocity_field[i])
	    Rast3d_fatal_error(_("Unable to open 3D raster map <%s>"),
			       vector_opt->answers[i]);
    }
}

int main(int argc, char *argv[])
{
    struct Option *vector_opt, *seed_opt, *flowlines_opt,
	*unit_opt, *step_opt, *limit_opt, *skip_opt;
    struct Flag *up_flag;
    struct GModule *module;
    RASTER3D_Region region;
    RASTER3D_Map *velocity_field[3];
    struct Integration integration;
    struct Seed seed;
    struct Map_info seed_Map;
    struct line_pnts *seed_points;
    struct line_cats *seed_cats;
    struct Map_info fl_map;
    struct line_cats *fl_cats;	/* for flowlines */
    struct line_pnts *fl_points;	/* for flowlines */
    int cat;			/* cat of flowlines */
    int i, r, c, d;
    char *desc;
    int n_seeds, seed_count, ltype;
    int skip[3];

    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("raster3d"));
    G_add_keyword(_("voxel"));
    G_add_keyword(_("flowline"));
    module->description = _("Compute flow lines.");


    vector_opt = G_define_standard_option(G_OPT_R3_INPUTS);
    vector_opt->key = "vector_field";
    vector_opt->required = YES;
    vector_opt->description = _("Names of three 3D raster maps describing "
				"x, y, z components of vector field");

    seed_opt = G_define_standard_option(G_OPT_V_INPUT);
    seed_opt->required = NO;
    seed_opt->key = "seed_points";
    seed_opt->description = _("If no map is provided, "
			      "flow lines are generated "
			      "from each cell of the input 3D raster");
    seed_opt->label = _("Name of vector map with points "
			"from which flow lines are generated");

    flowlines_opt = G_define_standard_option(G_OPT_V_OUTPUT);
    flowlines_opt->key = "flowline";
    flowlines_opt->required = YES;
    flowlines_opt->description = _("Name for vector map of flow lines");

    unit_opt = G_define_option();
    unit_opt->key = "unit";
    unit_opt->type = TYPE_STRING;
    unit_opt->required = NO;
    unit_opt->answer = "cell";
    unit_opt->options = "time,length,cell";
    desc = NULL;
    G_asprintf(&desc,
	       "time;%s;"
	       "length;%s;"
	       "cell;%s",
	       _("elapsed time"),
	       _("length in map units"), _("length in cells (voxels)"));
    unit_opt->descriptions = desc;
    unit_opt->label = _("Unit of integration step");
    unit_opt->description = _("Default unit is cell");
    unit_opt->guisection = _("Integration");

    step_opt = G_define_option();
    step_opt->key = "step";
    step_opt->type = TYPE_DOUBLE;
    step_opt->required = NO;
    step_opt->answer = "0.25";
    step_opt->label = _("Integration step in selected unit");
    step_opt->description = _("Default step is 0.25 cell");
    step_opt->guisection = _("Integration");

    limit_opt = G_define_option();
    limit_opt->key = "limit";
    limit_opt->type = TYPE_INTEGER;
    limit_opt->required = NO;
    limit_opt->answer = "2000";
    limit_opt->description = _("Maximum number of steps");
    limit_opt->guisection = _("Integration");

    skip_opt = G_define_option();
    skip_opt->key = "skip";
    skip_opt->type = TYPE_INTEGER;
    skip_opt->required = NO;
    skip_opt->multiple = YES;
    skip_opt->description =
	_("Number of cells between flow lines in x, y and z direction");

    up_flag = G_define_flag();
    up_flag->key = 'u';
    up_flag->description = _("Compute upstream flowlines "
			     "instead of default downstream flowlines");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    check_vector_input_maps(vector_opt, seed_opt);

    Rast3d_init_defaults();
    Rast3d_get_window(&region);

    /* set up integration variables */
    if (step_opt->answer) {
	integration.step = atof(step_opt->answer);
	integration.unit = unit_opt->answer;
    }
    else {
	integration.unit = "cell";
	integration.step = 0.25;
    }
    integration.limit = atof(limit_opt->answer);
    integration.direction = up_flag->answer ? 1 : -1;


    /* cell size is the diagonal */
    integration.cell_size = sqrt(region.ns_res * region.ns_res +
				 region.ew_res * region.ew_res +
				 region.tb_res * region.tb_res);

    /* set default skip if needed */
    if (skip_opt->answers) {
	for (i = 0; i < 3; i++) {
	    if (skip_opt->answers[i] != NULL) {
		skip[i] = atoi(skip_opt->answers[i]);
	    }
	    else {
		G_fatal_error
		    ("Please provide 3 integer values for skip option.");
	    }
	}
    }
    else {
	skip[0] = fmax(1, region.cols / 10);
	skip[1] = fmax(1, region.rows / 10);
	skip[2] = fmax(1, region.depths / 10);

    }

    /* open raster 3D maps of velocity components */
    load_input_velocity_maps(vector_opt, velocity_field, &region);

    /* open new vector map of flowlines */
    fl_cats = Vect_new_cats_struct();
    fl_points = Vect_new_line_struct();
    if (Vect_open_new(&fl_map, flowlines_opt->answer, TRUE) < 0)
	G_fatal_error(_("Unable to create vector map <%s>"),
		      flowlines_opt->answer);

    Vect_hist_command(&fl_map);

    n_seeds = 0;
    /* open vector map of seeds */
    if (seed_opt->answer) {
	if (Vect_open_old2(&seed_Map, seed_opt->answer, "", "1") < 0)
	    G_fatal_error(_("Unable to open vector map <%s>"),
			  seed_opt->answer);
	if (!Vect_is_3d(&seed_Map))
	    G_fatal_error(_("Vector map <%s> is not 3D"), seed_opt->answer);

	n_seeds = Vect_get_num_primitives(&seed_Map, GV_POINT);
    }
    else {
	n_seeds += ceil(region.cols / (double)skip[0]) *
	    ceil(region.rows / (double)skip[1]) *
	    ceil(region.depths / (double)skip[2]);
    }
    G_debug(1, "Number of seeds is %d", n_seeds);

    seed_count = 0;
    if (seed_opt->answer) {

	seed_points = Vect_new_line_struct();
	seed_cats = Vect_new_cats_struct();

	/* compute flowlines from vector seed map */
	while (TRUE) {
	    ltype = Vect_read_next_line(&seed_Map, seed_points, seed_cats);
	    if (ltype == -1) {
		Vect_close(&seed_Map);
		G_fatal_error(_("Error during reading seed vector map"));
	    }
	    else if (ltype == -2) {
		break;
	    }
	    else if (ltype == GV_POINT) {
		seed.x = seed_points->x[0];
		seed.y = seed_points->y[0];
		seed.z = seed_points->z[0];
		seed.flowline = TRUE;
		seed.flowaccum = FALSE;
	    }
	    G_percent(seed_count, n_seeds, 1);
	    cat = seed_count + 1;
	    compute_flowline(&region, &seed, velocity_field, &integration,
			     &fl_map, fl_cats, fl_points, cat);
	    seed_count++;
	}

	Vect_destroy_line_struct(seed_points);
	Vect_destroy_cats_struct(seed_cats);
	Vect_close(&seed_Map);
    }
    else {
	/* compute flowlines from points on grid */
	for (r = region.rows; r > 0; r--) {
	    for (c = 0; c < region.cols; c++) {
		for (d = 0; d < region.depths; d++) {
		    seed.x =
			region.west + c * region.ew_res + region.ew_res / 2;
		    seed.y =
			region.south + r * region.ns_res - region.ns_res / 2;
		    seed.z =
			region.bottom + d * region.tb_res + region.tb_res / 2;
		    seed.flowline = FALSE;
		    seed.flowaccum = FALSE;

		    if ((c % skip[0] == 0) && (r % skip[1] == 0) &&
			(d % skip[2] == 0)) {
			seed.flowline = TRUE;
			G_percent(seed_count, n_seeds, 1);
			cat = seed_count + 1;
			compute_flowline(&region, &seed, velocity_field,
					 &integration, &fl_map, fl_cats,
					 fl_points, cat);
			seed_count++;
		    }
		}
	    }
	}
    }
    Vect_destroy_line_struct(fl_points);
    Vect_destroy_cats_struct(fl_cats);
    Vect_build(&fl_map);
    Vect_close(&fl_map);


    return EXIT_SUCCESS;
}
