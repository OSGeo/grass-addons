/****************************************************************
 *
 * MODULE:       v.nnstat
 *
 * AUTHOR(S):    Eva Stopková
 *               functions in files mbr.cpp and mbb.cpp are mostly taken
 *               from the module v.hull (Aime, A., Neteler, M., Ducke, B.,
 *               Landa, M.)
 *
 * PURPOSE:      Module indicates clusters, separations or random distribution
 *               of point set in 2D or 3D space.
 *
 * COPYRIGHT:    (C) 2013-2014 by Eva Stopková and the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 **************************************************************/

#include "local_proto.h"

int main(int argc, char *argv[])
{
    /* Vector layer and module */
    struct Map_info map; // input vector map
    struct GModule *module;
    struct nna_par xD;  // 2D or 3D NNA to be performed
    struct points pnts; // points: coordinates, number etc.

    struct nearest nna; // structure to save results
    int field;

    struct {
        struct Option *map, *A, *type, *field, *lyr, *desc,
            *zcol; /* A - area (minimum enclosing rectangle or specified by
                      user) */
    } opt;

    struct {
        struct Flag *d23;
    } flg;

    /* Module creation */
    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("nearest neighbour analysis"));
    module->description = _("Indicates clusters, separations or random "
                            "distribution of point set in 2D or 3D space.");

    /* Setting options */
    opt.map = G_define_standard_option(G_OPT_V_INPUT); // vector input layer

    flg.d23 = G_define_flag(); // to process 2D or 3D Nearest Neighbour Analysis
    flg.d23->key = '2';
    flg.d23->description = _("Force 2D NNA  even if input is 3D");

    opt.A = G_define_option();
    opt.A->key = "area";
    opt.A->type = TYPE_DOUBLE;
    opt.A->description =
        _("2D: Area. If not specified, area of Minimum Enclosing Rectangle "
          "will be used.\n3D: Volume. If not specified, volume of Minimum "
          "Enclosing Box will be used.");
    opt.A->required = NO;

    opt.field = G_define_standard_option(G_OPT_V_FIELD);

    opt.zcol = G_define_standard_option(G_OPT_DB_COLUMN);
    opt.zcol->key = "zcolumn";
    opt.zcol->required = NO;
    opt.zcol->guisection = _("Fields");
    opt.zcol->description = _("Column with z coordinate (set for 2D vectors "
                              "only if 3D NNA is required to be performed)");

    G_gisinit(argv[0]);

    if (G_parser(argc, argv)) {
        exit(EXIT_FAILURE);
    }

    /* get parameters from the parser */
    field = opt.field->answer ? atoi(opt.field->answer) : -1;

    /* open input vector map */
    Vect_set_open_level(2);

    if (0 > Vect_open_old2(&map, opt.map->answer, "", opt.field->answer)) {
        G_fatal_error(_("Unable to open vector map <%s>"), opt.map->answer);
    }
    Vect_set_error_handler_io(&map, NULL);

    /* perform 2D or 3D NNA ? */
    xD.v3 = Vect_is_3d(&map); // test if vector layer is 2D or 3D
    xD.i3 = (flg.d23->answer || (xD.v3 == FALSE && opt.zcol->answer == NULL))
                ? FALSE
                : TRUE; // if -2 flag or input layer is 2D (without zcolumn),
                        // perform 2D NNA, otherwise 3D

    /* Warnings */
    if (flg.d23->answer && opt.zcol->answer) { // -2 flag (2D) vs. zcolumn (3D)
        G_warning(_("Flag -2 has higher priority than zcolumn considered in 2D "
                    "layer. 2D Nearest Neighbour Analysis will be performed "
                    "instead of 3D. If you wish to perform 3D Nearest "
                    "Neighbour Analysis, please remove flag -2."));
    }

    if (xD.v3 == TRUE && opt.zcol->answer) {
        G_warning(_("Input layer <%s> is 3D - it was not necessary to set up "
                    "attribute column. 3D Nearest Neighbour Analysis is being "
                    "performed..."),
                  opt.map->answer);
    }

    read_points(&map, field, &xD, opt.zcol->answer,
                &pnts); // read coordinates of the points

    /* Nearest Neighbour Analysis */
    nn_average_distance_real(
        &xD, &pnts, &nna); // Average distance (AD) between NN in pointset
    density(&pnts, &xD, opt.A->answer,
            &nna); // Number of points per area/volume unit
    nn_average_distance_expected(
        &xD, &nna); // Expected AD of NN in a randomly distributed pointset
    nna.R = nna.rA / nna.rE; // Ratio of real and expected AD
    nn_statistics(&pnts, &xD,
                  &nna); // Student's t-test of significance of the mean

    Vect_close(&map);
    exit(EXIT_SUCCESS);
}
