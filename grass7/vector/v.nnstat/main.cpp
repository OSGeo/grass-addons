
/****************************************************************
 *
 * MODULE:	v.nnstat
 * 
 * AUTHOR(S):	Eva Stopková
 *              functionsin files mbr.cpp and mbb.cpp are mostly taken 
 *              from the module 
 *              v.hull (Aime, A., Neteler, M., Ducke, B., Landa, M.)
 *			   
 * PURPOSE:	Module indicates clusters, separations or random distribution of point set in 2D or 3D space.
 *			   
 * COPYRIGHT:	(C) 2013-2014 by Eva Stopková and the GRASS Development Team
 *
 *			   This program is free software under the 
 *			   GNU General Public License (>=v2). 
 *			   Read the file COPYING that comes with GRASS
 *			   for details.
 *
 **************************************************************/
#include "local_proto.h"

extern "C" {
  int main(int argc, char *argv[])
  {
    /* Vector layer and module */
    struct Map_info map; /* input vector map */
    struct GModule *module;
    struct nna_par xD; /* 2D or 3D NNA */
    struct points pnts;
    union dat ifs; /* integer/float/string value */

    struct nearest nna;
    int field, pass;

    struct {
      struct Option *map, *A, *type, *field, *lyr, *desc, *zcol; /* A - area (minimum enclosing rectangle or specified by user) */
    } opt;

    struct {
      struct Flag *d23;
    } flg;

    /* Module creation */
    module = G_define_module();
    G_add_keyword(_("Vector"));
    G_add_keyword(_("Nearest Neighbour Analysis"));
    module->description = _("Indicates clusters, separations or random distribution of point set in 2D or 3D space.");
	
    /* Setting options */
    opt.map = G_define_standard_option(G_OPT_V_INPUT);   /* vector input layer */
    opt.map->label = _("Name of input vector map");

    flg.d23 = G_define_flag();	/* to process 2D or 3D Nearest Neighbour Analysis */
    flg.d23->key = '2';
    flg.d23->description =
      _("Force 2D NNA  even if input is 3D");

    opt.A = G_define_option();
    opt.A->key = "A";
    opt.A->type = TYPE_DOUBLE;
    opt.A->description = _("2D: Area. If not specified, area of Minimum Enclosing Rectangle will be used.\n3D: Volume. If not specified, volume of Minimum Enclosing Box will be used.");
    opt.A->required = NO;

    opt.field = G_define_standard_option(G_OPT_V_FIELD);

    opt.zcol = G_define_standard_option(G_OPT_DB_COLUMN);
    opt.zcol->key = "zcol";
    opt.zcol->required = NO;
    opt.zcol->guisection = _("Fields");
    opt.zcol->description = _("Column with z coordinate (set for 2D vectors only)");

    G_gisinit(argv[0]);

    if (G_parser(argc, argv))
      exit(EXIT_FAILURE);

    /* get parameters from the parser */
    field = opt.field->answer ? atoi(opt.field->answer) : -1;
	
    /* open input vector map */
    Vect_set_open_level(2);

    if (0 > Vect_open_old2(&map, opt.map->answer, "", opt.field->answer))
      G_fatal_error(_("Unable to open vector map <%s>"), opt.map->answer);
    Vect_set_error_handler_io(&map, NULL);

    /* perform 2D or 3D NNA ? */
    xD.v3 = Vect_is_3d(&map);
    xD.i3 = (flg.d23->answer || xD.v3 == FALSE) ? FALSE : TRUE;

    if (xD.i3 == TRUE) { /* 3D */
      if (xD.v3 == FALSE) { /* 2D input */
	if (opt.zcol->answer == NULL)
	  G_fatal_error(_("To process 3D Nearest Neighbour Analysis based on 2D input, "
			  "please set attribute column containing z coordinates "
			  "or switch to 2D NNA."));
      }
    }

    read_points(&map, field, &xD, opt.zcol->answer, &ifs, &pnts);

    /* Nearest Neighbour Analysis */
    pass = nn_average_distance_real(&pnts, &nna);  // Average distance (AD) between NN in pointset
    density(&pnts, &xD, opt.A->answer, &nna);      // Number of points per area/volume unit
    nn_average_distance_expected(&xD, &nna); // Expected AD of NN in a randomly distributed pointset  
    nna.R = nna.rA / nna.rE;                 // Ratio of real and expected AD
    nn_statistics(&pnts, &xD, &nna);         // Student's t-test of significance of the mean
  
    Vect_close(&map);
    exit(EXIT_SUCCESS);
  }    
}
