
/****************************************************************************
 *
 * MODULE:       i.eb.h_iter
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates sensible heat flux by SEBAL iteration
 *               if your DeltaT (or eq. to make it from surf.temp)
 *               is validated.
 *               ! Delta T will not be reassessed in the iterations !
 *               A flag allows the Bastiaanssen (1995) affine transform 
 *               of surface temperature as used in his SEBAL model.
 *               This has been seen in Pawan (2004).
 *
 * COPYRIGHT:    (C) 2002-2007 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 * CHANGELOG:	06 June 08: 	Added iteration number input
 * 		28 October 06:  Added u2m input 
 * 				(wind speed at 2 meters height)
 * 		30 June 07: 	Debugging a Seg Fault
 *
 *****************************************************************************/
     
    
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>
double fixed_deltat(double u2m, double roh_air, double cp, double dt,
		     double disp, double z0m, double z0h, double tempk,
		     double hu, int iteration);
double h0(double roh_air, double cp, double rah, double dtair);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    
	/*If !sebal then use Delta T input file */ 
    int sebal = 0;		/*SEBAL Flag for affine transform of surf. temp. */

    struct GModule *module;

    struct Option *input1, *input2, *input3, *input4, *input5;

    struct Option *input6, *input7, *input8, *input9, *input10;

    struct Option *input11, *input_hu, *output1;

    struct Flag *flag1, *flag2;

    struct History history;	/*metadata */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result;		/*output raster name */

    
	/*File Descriptors */ 
    int infd_rohair, infd_tempk, infd_dtair;

    int infd_disp, infd_z0m, infd_z0h, infd_u_hu;

    int infd_hu, outfd;

    char *rohair, *tempk, *dtair, *disp, *z0m, *z0h, *u_hu, *hu;

    double cp;		/*air specific heat */

    int i = 0, j = 0;

    double a, b;		/*SEBAL slope and intercepts of surf. temp. */

    int iteration;

    void *inrast_rohair, *inrast_tempk, *inrast_dtair;

    void *inrast_disp, *inrast_z0m, *inrast_z0h;

    void *inrast_u_hu, *inrast_hu;

    DCELL * outrast;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_rohair;
    RASTER_MAP_TYPE data_type_dtair;
    RASTER_MAP_TYPE data_type_tempk;
    RASTER_MAP_TYPE data_type_disp;
    RASTER_MAP_TYPE data_type_z0m;
    RASTER_MAP_TYPE data_type_z0h;
    RASTER_MAP_TYPE data_type_u_hu;
    RASTER_MAP_TYPE data_type_hu;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("sensible heat flux, energy balance, SEBAL");
    module->description =
	_("sensible heat flux equation as in Pawan (2004), including flags for delta T affine transform from surf. temp.");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("rohair");
    input1->description =
	_("Name of the air density map ~[0.9;1.5], Pawan (2004) use 1.12 constant value");
    input1->answer = _("rohair");
    input2 = G_define_option();
    input2->key = _("cp");
    input2->type = TYPE_DOUBLE;
    input2->required = YES;
    input2->gisprompt = _("parameter, float number");
    input2->description =
	_("Value of the air specific heat [1000.0;1020.0]");
    input2->answer = _("1004.16");
    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = _("tempk");
    input3->description =
	_("Name of the surface skin temperature map [degrees Kelvin],if used with -s flag and affine coefs, it disables dtair input");
    input3->answer = _("tempk");
    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = _("dtair");
    input4->required = NO;
    input4->description =
	_("Name of the skin-air Surface temperature difference map ~[0.0-80.0], required unless you use -s flag (then you must give a & b coefs below)");
    input5 = G_define_option();
    input5->key = _("a");
    input5->type = TYPE_DOUBLE;
    input5->required = NO;
    input5->gisprompt = _("parameter, float number");
    input5->description =
	_("-s flag: Value of the slope of the affine transform");
    input6 = G_define_option();
    input6->key = _("b");
    input6->type = TYPE_DOUBLE;
    input6->required = NO;
    input6->gisprompt = _("parameter, float number");
    input6->description =
	_("-s flag: Value of the intercept of the affine transform");
    input7 = G_define_standard_option(G_OPT_R_INPUT);
    input7->key = _("disp");
    input7->description = _("Name of the displacement height input map (m)");
    input7->answer = _("disp");
    input8 = G_define_standard_option(G_OPT_R_INPUT);
    input8->key = _("z0m");
    input8->description = _("Name of the z0m input map (s/m)");
    input8->answer = _("z0m");
    input9 = G_define_standard_option(G_OPT_R_INPUT);
    input9->key = _("z0h");
    input9->description = _("Name of the z0h input map (s/m)");
    input9->answer = _("z0h");
    input10 = G_define_standard_option(G_OPT_R_INPUT);
    input10->key = _("u_hu");
    input10->description =
	_("Name of the wind speed at height (hu) input map (m/s)");
    input10->answer = _("u_hu");
    input_hu = G_define_standard_option(G_OPT_R_INPUT);
    input_hu->key = _("hu");
    input_hu->description =
	_("Name of the height (hu) of measurement of wind speed input map (m/s)");
    input_hu->answer = _("hu");
    input11 = G_define_option();
    input11->key = _("iteration");
    input11->type = TYPE_INTEGER;
    input11->required = NO;
    input11->gisprompt = _("parameter, integer number");
    input11->description = _("number of iteration of rah stabilization");
    input11->answer = _("3");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the output h0 layer");
    flag1 = G_define_flag();
    flag1->key = 's';
    flag1->description =
	_("Affine transform of Surface temperature into delta T, needs input of slope and intercept (Bastiaanssen, 1995)");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    rohair = input1->answer;
    cp = atof(input2->answer);
    if (input3->answer) {
	tempk = input3->answer;
    }
    if (input4->answer) {
	dtair = input4->answer;
    }
    if (input5->answer) {
	a = atof(input5->answer);
    }
    if (input6->answer) {
	b = atof(input6->answer);
    }
    disp = input7->answer;
    z0m = input8->answer;
    z0h = input9->answer;
    u_hu = input10->answer;
    hu = input_hu->answer;
    if (input11->answer) {
	iteration = atoi(input11->answer);
    }
    else {
	iteration = 3;
    }
    result = output1->answer;
    sebal = flag1->answer;
    

	/***************************************************/ 
	/* TEST FOR -s FLAG COEFS 
	 * Return error if not proper flag coefs
	 *                                                 */ 

	/***************************************************/ 
	if (sebal && !a && !b) {
	G_fatal_error(_("FATAL ERROR: -s Flag requires coefs a & b!"));
    }
    else if (!sebal && !dtair) {
	G_fatal_error(_("FATAL ERROR: No -s Flag, use DeltaT map!"));
    }
    

	/***************************************************/ 
	mapset = G_find_cell2(rohair, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), rohair);
    }
    data_type_rohair = G_raster_map_type(rohair, mapset);
    if ((infd_rohair = G_open_cell_old(rohair, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), rohair);
    if (G_get_cellhd(rohair, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), rohair);
    inrast_rohair = G_allocate_raster_buf(data_type_rohair);
    

	/***************************************************/ 
	if (!sebal) {
	mapset = G_find_cell2(dtair, "");
	if (mapset == NULL) {
	    G_fatal_error(_("cell file [%s] not found"), dtair);
	}
	data_type_dtair = G_raster_map_type(dtair, mapset);
	if ((infd_dtair = G_open_cell_old(dtair, mapset)) < 0)
	    G_fatal_error(_("Cannot open cell file [%s]"), dtair);
	if (G_get_cellhd(dtair, mapset, &cellhd) < 0)
	    G_fatal_error(_("Cannot read file header of [%s]"), dtair);
	inrast_dtair = G_allocate_raster_buf(data_type_dtair);
    }
    

	/***************************************************/ 
	mapset = G_find_cell2(tempk, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), tempk);
    }
    data_type_tempk = G_raster_map_type(tempk, mapset);
    if ((infd_tempk = G_open_cell_old(tempk, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), tempk);
    if (G_get_cellhd(tempk, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), tempk);
    inrast_tempk = G_allocate_raster_buf(data_type_tempk);
    

	/***************************************************/ 
	mapset = G_find_cell2(disp, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), disp);
    }
    data_type_disp = G_raster_map_type(disp, mapset);
    if ((infd_disp = G_open_cell_old(disp, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), disp);
    if (G_get_cellhd(disp, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), disp);
    inrast_disp = G_allocate_raster_buf(data_type_disp);
    

	/***************************************************/ 
	mapset = G_find_cell2(z0m, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), z0m);
    }
    data_type_z0m = G_raster_map_type(z0m, mapset);
    if ((infd_z0m = G_open_cell_old(z0m, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), z0m);
    if (G_get_cellhd(z0m, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), z0m);
    inrast_z0m = G_allocate_raster_buf(data_type_z0m);
    

	/***************************************************/ 
	mapset = G_find_cell2(z0h, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), z0h);
    }
    data_type_z0h = G_raster_map_type(z0h, mapset);
    if ((infd_z0h = G_open_cell_old(z0h, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), z0h);
    if (G_get_cellhd(z0h, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), z0h);
    inrast_z0h = G_allocate_raster_buf(data_type_z0h);
    

	/***************************************************/ 
	mapset = G_find_cell2(u_hu, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), u_hu);
    }
    data_type_u_hu = G_raster_map_type(u_hu, mapset);
    if ((infd_u_hu = G_open_cell_old(u_hu, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), u_hu);
    if (G_get_cellhd(u_hu, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), u_hu);
    inrast_u_hu = G_allocate_raster_buf(data_type_u_hu);
    

	/***************************************************/ 
	mapset = G_find_cell2(hu, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), hu);
    }
    data_type_hu = G_raster_map_type(hu, mapset);
    if ((infd_hu = G_open_cell_old(hu, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), hu);
    if (G_get_cellhd(hu, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), hu);
    inrast_hu = G_allocate_raster_buf(data_type_hu);
    

	/***************************************************/ 
	G_debug(3, "number of rows %d", cellhd.rows);
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast = G_allocate_raster_buf(data_type_output);
    
	/* Create New raster files */ 
	if ((outfd = G_open_raster_new(result, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), result);
    
	/* Process pixels */ 
	for (row = 0; row < nrows; row++)
	 {
	DCELL d;
	DCELL d_rohair;
	DCELL d_rah;
	DCELL d_dtair;
	DCELL d_affine;
	DCELL d_tempk;
	DCELL d_disp;
	DCELL d_z0m;
	DCELL d_z0h;
	DCELL d_u_hu;
	DCELL d_hu;
	G_percent(row, nrows, 2);
	
	    /* printf("row = %i/%i\n",row,nrows); */ 
	    /* read input maps */ 
	    if (G_get_raster_row
		(infd_rohair, inrast_rohair, row, data_type_rohair) < 0)
	    G_fatal_error(_("Could not read from <%s>"), rohair);
	if (!sebal) {
	    if (G_get_raster_row
		 (infd_dtair, inrast_dtair, row, data_type_dtair) < 0)
		G_fatal_error(_("Could not read from <%s>"), dtair);
	}
	if (G_get_raster_row(infd_tempk, inrast_tempk, row, data_type_tempk)
	     < 0)
	    G_fatal_error(_("Could not read from <%s>"), tempk);
	if (G_get_raster_row(infd_disp, inrast_disp, row, data_type_disp) <
	     0)
	    G_fatal_error(_("Could not read from <%s>"), disp);
	if (G_get_raster_row(infd_z0m, inrast_z0m, row, data_type_z0m) < 0)
	    G_fatal_error(_("Could not read from <%s>"), z0m);
	if (G_get_raster_row(infd_z0h, inrast_z0h, row, data_type_z0h) < 0)
	    G_fatal_error(_("Could not read from <%s>"), z0h);
	if (G_get_raster_row(infd_u_hu, inrast_u_hu, row, data_type_u_hu) <
	     0)
	    G_fatal_error(_("Could not read from <%s>"), u_hu);
	if (G_get_raster_row(infd_hu, inrast_hu, row, data_type_hu) < 0)
	    G_fatal_error(_("Could not read from <%s>"), hu);
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
	    switch (data_type_rohair) {
	    case CELL_TYPE:
		d_rohair = (double)((CELL *) inrast_rohair)[col];
		break;
	    case FCELL_TYPE:
		d_rohair = (double)((FCELL *) inrast_rohair)[col];
		break;
	    case DCELL_TYPE:
		d_rohair = ((DCELL *) inrast_rohair)[col];
		break;
	    }
	    if (!sebal) {
		switch (data_type_dtair) {
		case CELL_TYPE:
		    d_dtair = (double)((CELL *) inrast_dtair)[col];
		    break;
		case FCELL_TYPE:
		    d_dtair = (double)((FCELL *) inrast_dtair)[col];
		    break;
		case DCELL_TYPE:
		    d_dtair = ((DCELL *) inrast_dtair)[col];
		    break;
		}
	    }
	    switch (data_type_tempk) {
	    case CELL_TYPE:
		d_tempk = (double)((CELL *) inrast_tempk)[col];
		break;
	    case FCELL_TYPE:
		d_tempk = (double)((FCELL *) inrast_tempk)[col];
		break;
	    case DCELL_TYPE:
		d_tempk = ((DCELL *) inrast_tempk)[col];
		break;
	    }
	    switch (data_type_disp) {
	    case CELL_TYPE:
		d_disp = (double)((CELL *) inrast_disp)[col];
		break;
	    case FCELL_TYPE:
		d_disp = (double)((FCELL *) inrast_disp)[col];
		break;
	    case DCELL_TYPE:
		d_disp = ((DCELL *) inrast_disp)[col];
		break;
	    }
	    switch (data_type_z0m) {
	    case CELL_TYPE:
		d_z0m = (double)((CELL *) inrast_z0m)[col];
		break;
	    case FCELL_TYPE:
		d_z0m = (double)((FCELL *) inrast_z0m)[col];
		break;
	    case DCELL_TYPE:
		d_z0m = ((DCELL *) inrast_z0m)[col];
		break;
	    }
	    switch (data_type_z0h) {
	    case CELL_TYPE:
		d_z0h = (double)((CELL *) inrast_z0h)[col];
		break;
	    case FCELL_TYPE:
		d_z0h = (double)((FCELL *) inrast_z0h)[col];
		break;
	    case DCELL_TYPE:
		d_z0h = ((DCELL *) inrast_z0h)[col];
		break;
	    }
	    switch (data_type_u_hu) {
	    case CELL_TYPE:
		d_u_hu = (double)((CELL *) inrast_u_hu)[col];
		break;
	    case FCELL_TYPE:
		d_u_hu = (double)((FCELL *) inrast_u_hu)[col];
		break;
	    case DCELL_TYPE:
		d_u_hu = ((DCELL *) inrast_u_hu)[col];
		break;
	    }
	    switch (data_type_hu) {
	    case CELL_TYPE:
		d_hu = (double)((CELL *) inrast_hu)[col];
		break;
	    case FCELL_TYPE:
		d_hu = (double)((FCELL *) inrast_hu)[col];
		break;
	    case DCELL_TYPE:
		d_hu = ((DCELL *) inrast_hu)[col];
		break;
	    }
	    if (G_is_d_null_value(&d_rohair) || 
		 ((!sebal) && G_is_d_null_value(&d_dtair)) ||
		 G_is_d_null_value(&d_tempk) || G_is_d_null_value(&d_disp)
		 || G_is_d_null_value(&d_z0m) || G_is_d_null_value(&d_z0h)
		 || G_is_d_null_value(&d_u_hu) ||
		 G_is_d_null_value(&d_hu)) {
		G_set_d_null_value(&outrast[col], 1);
	    }
	    else {
		

				/************************************/ 
		    /* calculate sensible heat flux     */ 
		    if (sebal) {	/*if -s flag then calculate Delta T from Coefs */
		    d_affine = a * d_tempk + b;
		    
			/* Run iterations to find Rah */ 
			d_rah =
			fixed_deltat(d_u_hu, d_rohair, cp, d_affine, d_disp,
				     d_z0m, d_z0h, d_tempk, d_hu, iteration);
		    
			/*Process h */ 
			d = h0(d_rohair, cp, d_rah, d_affine);
		}
		else {		/* not -s flag then take delta T map input directly */
		    
			/* Run iterations to find Rah */ 
			d_rah =
			fixed_deltat(d_u_hu, d_rohair, cp, d_dtair, d_disp,
				     d_z0m, d_z0h, d_tempk, d_hu, iteration);
		    
			/*Process h */ 
			d = h0(d_rohair, cp, d_rah, d_dtair);
		}
		outrast[col] = d;
	    }
	    }
	if (G_put_raster_row(outfd, outrast, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
	}
    G_free(inrast_rohair);
    if (!sebal) {
	G_free(inrast_dtair);
    }
    G_free(inrast_tempk);
    G_free(inrast_disp);
    G_free(inrast_z0m);
    G_free(inrast_z0h);
    G_free(inrast_u_hu);
    G_free(inrast_hu);
    G_close_cell(infd_rohair);
    if (!sebal) {
	G_close_cell(infd_dtair);
    }
    G_close_cell(infd_tempk);
    G_close_cell(infd_disp);
    G_close_cell(infd_z0m);
    G_close_cell(infd_z0h);
    G_close_cell(infd_u_hu);
    G_close_cell(infd_hu);
    G_free(outrast);
    G_close_cell(outfd);
    G_short_history(result, "raster", &history);
    G_command_history(&history);
    G_write_history(result, &history);
    exit(EXIT_SUCCESS);
}


