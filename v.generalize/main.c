
/****************************************************************
 *
 * MODULE:     v.generalize
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    Module for line simplification and smoothing
 *
 * COPYRIGHT:  (C) 2002-2005 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>
#include "misc.h"

#define DOUGLASS 0
#define LANG 1
#define VERTEX_REDUCTION 2
#define REUMANN 3
#define BOYLE 4
#define DISTANCE_WEIGHTING 5
#define CHAIKEN 6
#define HERMITE 7
#define SNAKES 8

int main(int argc, char *argv[])
{
    struct Map_info In, Out;
    static struct line_pnts *Points;
    struct line_cats *Cats;
    int i, type, cat, iter;
    char *mapset;
    struct GModule *module;	/* GRASS module for parsing arguments */
    struct Option *map_in, *map_out, *thresh_opt, *method_opt, *look_ahead_opt;
    struct Option *iterations_opt, *cat_opt, *alfa_opt, *beta_opt;
    int with_z;
    int total_input, total_output;	/* Number of points in the input/output map respectively */
    double thresh, alfa, beta;
    int method;
    int look_ahead, iterations;
    RANGE *ranges;
    int n_ranges;

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("vector, generalization, simplification, smoothing");
    module->description = _("Line simplification and smoothing");

    /* Define the different options as defined in gis.h */
    map_in = G_define_standard_option(G_OPT_V_INPUT);
    map_out = G_define_standard_option(G_OPT_V_OUTPUT);

    method_opt = G_define_option();
    method_opt->key = "method";
    method_opt->type = TYPE_STRING;
    method_opt->required = YES;
    method_opt->multiple = NO;
    method_opt->options =
	"douglas,lang,reduction,reumann,boyle,distance_weighting,chaiken,hermite,snakes";
    method_opt->answer = "douglas";
    method_opt->descriptions = _("douglas;Douglass-Peucker Algorithm;"
				 "lang;Lang Simplification Algorithm;"
				 "reduction;Vertex Reduction Algorithm eliminates points close to each other;"
				 "reumann;Reumann-Witkam Algorithm;"
				 "boyle;Boyle's Forward-Looking Algorithm;"
				 "distance_weighting;McMaster's Distance-Weighting Algorithm;"
				 "chaiken;Chaiken's Algorithm;"
				 "hermite;Interpolation by Cubic Hermite Splines;"
				 "snakes;Snakes method for line smoothing;");
    method_opt->description = _("Line simplification/smoothing algorithm");

    thresh_opt = G_define_option();
    thresh_opt->key = "threshold";
    thresh_opt->type = TYPE_DOUBLE;
    thresh_opt->required = YES;
    thresh_opt->options = "0-1000000000";
    thresh_opt->answer = "1.0";
    thresh_opt->description = _("Maximal tolerance value");

    look_ahead_opt = G_define_option();
    look_ahead_opt->key = "look_ahead";
    look_ahead_opt->type = TYPE_INTEGER;
    look_ahead_opt->required = YES;
    look_ahead_opt->answer = "7";
    look_ahead_opt->description = _("Look-ahead parameter");

    alfa_opt = G_define_option();
    alfa_opt->key = "alfa";
    alfa_opt->type = TYPE_DOUBLE;
    alfa_opt->required = YES;
    alfa_opt->answer = "1.0";
    alfa_opt->description = _("Snakes alfa parameter");

    beta_opt = G_define_option();
    beta_opt->key = "beta";
    beta_opt->type = TYPE_DOUBLE;
    beta_opt->required = YES;
    beta_opt->answer = "1.0";
    beta_opt->description = _("Snakes beta parameter");

    iterations_opt = G_define_option();
    iterations_opt->key = "iterations";
    iterations_opt->type = TYPE_INTEGER;
    iterations_opt->required = YES;
    iterations_opt->answer = "1";
    iterations_opt->description = _("Number of iterations");

    cat_opt = G_define_option();
    cat_opt->key = "category";
    cat_opt->type = TYPE_STRING;
    cat_opt->required = NO;
    cat_opt->multiple = YES;
    cat_opt->key_desc = "range";
    cat_opt->description = _("Category ranges: e.g. 1,3-8,13");

    /* options and flags parser */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    thresh = atof(thresh_opt->answer);
    look_ahead = atoi(look_ahead_opt->answer);
    alfa = atof(alfa_opt->answer);
    beta = atof(beta_opt->answer);
    iterations = atoi(iterations_opt->answer);


    /* check and store category ranges */
    if (cat_opt->answer != NULL) {
	for (i = 0; cat_opt->answers[i]; i++)
	    if (!check_range(cat_opt->answers[i])) {
		G_fatal_error(_("Bad category range in (%s)"),
			      cat_opt->answers[i]);
		exit(-1);
	    };
	get_ranges(cat_opt->answers, &ranges, &n_ranges);
    }
    else
	ranges = NULL;

    G_message(method_opt->answer);

    if (method_opt->answer[0] == 'd' && method_opt->answer[1] == 'o') {
	method = DOUGLASS;
    }
    else if (method_opt->answer[0] == 'l') {
	method = LANG;
    }
    else if (method_opt->answer[0] == 'v') {
	method = VERTEX_REDUCTION;
    }
    else if (method_opt->answer[0] == 'r') {
	method = REUMANN;
    }
    else if (method_opt->answer[0] == 'b') {
	method = BOYLE;
    }
    else if (method_opt->answer[0] == 'd') {
	method = DISTANCE_WEIGHTING;
    }
    else if (method_opt->answer[0] == 'c') {
	method = CHAIKEN;
    }
    else if (method_opt->answer[0] == 'h') {
	method = HERMITE;
    }
    else {
	method = SNAKES;
    };

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    Vect_check_input_output_name(map_in->answer, map_out->answer,
				 GV_FATAL_EXIT);

    if ((mapset = G_find_vector2(map_in->answer, "")) == NULL)
	G_fatal_error(_("Could not find input %s"), map_in->answer);

    Vect_set_open_level(2);

    if (1 > Vect_open_old(&In, map_in->answer, mapset))
	G_fatal_error(_("Could not open input"));

    with_z = Vect_is_3d(&In);

    if (0 > Vect_open_new(&Out, map_out->answer, with_z)) {
	Vect_close(&In);
	G_fatal_error(_("Could not open output"));
    }

    Vect_copy_head_data(&In, &Out);
    Vect_hist_copy(&In, &Out);
    Vect_hist_command(&Out);

    total_input = total_output = 0;

    i = 1;
    while ((type = Vect_read_next_line(&In, Points, Cats)) > 0) {
	total_input += Points->n_points;
	if ((type == GV_LINE || 1 == 1) &&
	    (ranges == NULL || cat_test(Cats, ranges, n_ranges))) {
	    int after = 0;
	    for (iter = 0; iter < iterations; iter++) {
		if (method == DOUGLASS) {
		    after = douglass_peucker(Points, thresh, with_z);
		}
		else if (method == LANG) {
		    after = lang(Points, thresh, look_ahead, with_z);
		}
		else if (method == VERTEX_REDUCTION) {
		    after = vertex_reduction(Points, thresh, with_z);
		}
		else if (method == REUMANN) {
		    after = reumann_witkam(Points, thresh, with_z);
		}
		else if (method == BOYLE) {
		    after = boyle(Points, look_ahead, with_z);
		}
		else if (method == DISTANCE_WEIGHTING) {
		    after =
			distance_weighting(Points, thresh, look_ahead, with_z);
		}
		else if (method == CHAIKEN) {
		    after = chaiken(Points, thresh, with_z);
		}
		else if (method == HERMITE) {
		    after = hermite(Points, thresh, with_z);
		}
		else {
		    after = snakes(Points, alfa, beta, with_z);
		};
	    };

	    after = Points->n_points;
	    total_output += after;
	    Vect_write_line(&Out, type, Points, Cats);

	}
	else {
	    total_output += Points->n_points;
	    Vect_write_line(&Out, type, Points, Cats);
	};
    }

    G_message("Number of vertices was reduced from %d to %d[%d%%]", total_input,
	      total_output, (total_output * 100) / total_input);

    G_free(ranges);

    Vect_build(&Out, stdout);
    Vect_close(&In);
    Vect_close(&Out);

    exit(EXIT_SUCCESS);
}
