/***************************************************************
 *
 * MODULE:       v.ellipse
 *
 * AUTHOR(S):    Tereza Fiedlerova
 *
 * PURPOSE:      Computes the best-fitting ellipse for
 *               given vector data
 *
 * COPYRIGHT:    (C) 2015 by Tereza Fiedlerova, and the GRASS Development Team
 *
 *               This program is free software under the GNU General
 *               Public License (>=v2). Read the file COPYING that
 *               comes with GRASS for details.
 **************************************************************/

#include <stdio.h>
#include <stdlib.h>

#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>

#include "proto.h"

int main(int argc, char *argv[])
{
    /* variables */
    struct Map_info In, Out;
    static struct line_pnts *Points, *Ellipse;
    struct line_cats *Cats, *Cats2;
    struct GModule *module;
    struct Option *old, *new, *stepopt;
    struct Parameters *pars;
    double stepsize;

    /* initialize GIS environment */
    G_gisinit(argv[0]);

    /* initialize module */
    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("geometry"));
    G_add_keyword(_("best-fitting ellipse"));
    module->description =
        _("Computes the best-fitting ellipse for given vector data.");

    /* define options */
    old = G_define_standard_option(G_OPT_V_INPUT);
    new = G_define_standard_option(G_OPT_V_OUTPUT);

    stepopt = G_define_option();
    stepopt->type = TYPE_DOUBLE;
    stepopt->key = "step";
    stepopt->description = "Step size in degrees";
    stepopt->required = NO;
    stepopt->answer = "4";

    /* call parser */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* read step size */
    stepsize = atof(stepopt->answer); /* conversion to double stepopt->answer */

    G_debug(1, "step size: %f degrees", stepsize);

    /* test if input and output are different */
    Vect_check_input_output_name(old->answer, new->answer, G_FATAL_EXIT);

    /* open input vector map */
    Vect_set_open_level(2);
    if (1 > Vect_open_old(&In, old->answer, ""))
        G_fatal_error(_("Unable to open vector map <%s> on topological level"),
                      old->answer);

    /* open output vector map */
    if (0 > Vect_open_new(&Out, new->answer, WITHOUT_Z)) {
        Vect_close(&In);
        G_fatal_error(_("Unable to create vector map <%s>"), new->answer);
    }
    Vect_set_error_handler_io(&In, &Out);

    /* create and initializes structs where to store points, categories */
    Cats = Vect_new_cats_struct();
    Cats2 = Vect_new_cats_struct();
    Points = Vect_new_line_struct();
    Ellipse = Vect_new_line_struct();

    /* allocate memory */
    pars = (struct Parameters *)G_malloc(sizeof(struct Parameters));

    int ok;

    load_points(&In, Points, Cats);
    ok = fitting_ellipse(Points, pars);
    G_debug(1, "exit %d", ok);
    if (ok) {
        create_ellipse(pars, Ellipse, Cats2, stepsize);
        write_ellipse(&Out, Ellipse, Cats2);
    }

    Vect_destroy_line_struct(Points);

    G_free(pars);

    exit(EXIT_SUCCESS);
}
