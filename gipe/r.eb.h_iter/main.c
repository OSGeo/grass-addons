/****************************************************************************
 *
 * MODULE:       r.eb.h_iter
 * AUTHOR(S):    Yann Chemin - ychemin@gmail.com
 * PURPOSE:      Calculates sensible heat flux by SEBAL iteration
 *               if your DeltaT (or eq. to make it from surf.temp) is validated.
 *               ! Delta T will not be reassessed in the iterations !
 *               A flag allows the Bastiaanssen (1995) affine transform 
 *               of surface temperature as used in his SEBAL model.
 *               This has been seen in Pawan (2004).
 *
 * COPYRIGHT:    (C) 2006 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 * CHANGELOG:	28 October: Added u2m input (wind speed at 2 meters height)
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>


double fixed_deltat(double u2m, double roh_air,double cp,double dt,double disp,double z0m,double z0h,double tempk);
double h0(double roh_air, double cp, double rah, double dtair);

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	//If !sebal then use Delta T input file
	int sebal=0;//SEBAL Flag for affine transform of surf. temp.
	struct GModule *module;
	struct Option *input1, *input2, *input3, *input4, *input5;
	struct Option *input6, *input7, *input8, *input9, *input10, *output1;
	
	struct Flag *flag1, *flag2;	
	struct History history; //metadata
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   // input raster name
	char *result; //output raster name
	//File Descriptors
	int infd_rohair, infd_tempk, infd_dtair;
	int infd_disp, infd_z0m, infd_z0h, infd_u2m;
	int outfd;
	
	char *rohair,*tempk,*dtair, *disp, *z0m, *z0h, *u2m;

	double cp; //air specific heat	
	int i=0,j=0;
	double a,b; //SEBAL slope and intercepts of surf. temp.
	
	void *inrast_rohair, *inrast_tempk, *inrast_dtair;
	void *inrast_disp, *inrast_z0m, *inrast_z0h, *inrast_u2m;
	unsigned char *outrast;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_rohair;
	RASTER_MAP_TYPE data_type_dtair;
	RASTER_MAP_TYPE data_type_tempk;
	RASTER_MAP_TYPE data_type_disp;
	RASTER_MAP_TYPE data_type_z0m;
	RASTER_MAP_TYPE data_type_z0h;
	RASTER_MAP_TYPE data_type_u2m;
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("sensible heat flux, energy balance, SEBAL");
	module->description = _("sensible heat flux equation as in Pawan (2004), including flags for delta T affine transform from surf. temp.");

	/* Define the different options */
	input1 = G_define_option() ;
	input1->key	   = _("rohair");
	input1->type       = TYPE_STRING;
	input1->required   = YES;
	input1->gisprompt  =_("old,cell,raster") ;
	input1->description=_("Name of the air density map ~[0.9;1.5], Pawan (2004) use 1.12 constant value");
	input1->answer     =_("rohair");

	input2 = G_define_option() ;
	input2->key        =_("cp");
	input2->type       = TYPE_DOUBLE;
	input2->required   = YES;
	input2->gisprompt  =_("parameter, float number");
	input2->description=_("Value of the air specific heat [1000.0;1020.0]");
	input2->answer     =_("1004.16");

	input3 = G_define_option() ;
	input3->key        =_("dtair");
	input3->type       = TYPE_STRING;
	input3->required   = NO;
	input3->gisprompt  =_("old,cell,raster");
	input3->description=_("Name of the skin-air Surface temperature difference map ~[0.0-80.0]");
//	input3->answer     =_("dtair");

	input4 = G_define_option() ;
	input4->key        =_("tempk");
	input4->type       = TYPE_STRING;
	input4->required   = NO;
	input4->gisprompt  =_("old,cell,raster");
	input4->description=_("Name of the surface skin temperature map [degrees Kelvin],if used with -s flag and affine coefs, it disables dtair input");
	input4->answer     =_("tempk");

	input5 = G_define_option() ;
	input5->key        =_("a");
	input5->type       = TYPE_DOUBLE;
	input5->required   = NO;
	input5->gisprompt  =_("parameter, float number");
	input5->description=_("-s flag: Value of the slope of the affine transform");
	
	input6 = G_define_option() ;
	input6->key        =_("b");
	input6->type       = TYPE_DOUBLE;
	input6->required   = NO;
	input6->gisprompt  =_("parameter, float number");
	input6->description=_("-s flag: Value of the intercept of the affine transform");
	
	input7 = G_define_option() ;
	input7->key        =_("disp");
	input7->type       = TYPE_STRING;
	input7->required   = YES;
	input7->gisprompt  =_("old,cell,raster");
	input7->description=_("Name of the displacement height input layer (m)");
	input7->answer     =_("disp");
	
	input8 = G_define_option() ;
	input8->key        =_("z0m");
	input8->type       = TYPE_STRING;
	input8->required   = YES;
	input8->gisprompt  =_("old,cell,raster");
	input8->description=_("Name of the z0m input layer (s/m)");
	input8->answer     =_("z0m");
	
	input9 = G_define_option() ;
	input9->key        =_("z0h");
	input9->type       = TYPE_STRING;
	input9->required   = YES;
	input9->gisprompt  =_("old,cell,raster");
	input9->description=_("Name of the z0h input layer (s/m)");
	input9->answer     =_("z0h");
	
	input10 = G_define_option() ;
	input10->key        =_("u2m");
	input10->type       = TYPE_STRING;
	input10->required   = YES;
	input10->gisprompt  =_("old,cell,raster");
	input10->description=_("Name of the wind speed at 2m height input layer (m/s)");
	input10->answer     =_("u2m");
		
	output1 = G_define_option() ;
	output1->key        =_("h0");
	output1->type       = TYPE_STRING;
	output1->required   = YES;
	output1->gisprompt  =_("new,cell,raster");
	output1->description=_("Name of the output h0 layer");
	output1->answer     =_("h0");

	flag1 = G_define_flag();
	flag1->key = 's';
	flag1->description = _("Affine transform of Surface temperature into delta T, needs input of slope and intercept (Bastiaanssen, 1995)");
	
	flag2 = G_define_flag();
	flag2->key = 'q';
	flag2->description = _("Quiet");
	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	rohair	 	= input1->answer;
	cp	 	= atof(input2->answer);
	dtair		= input3->answer;
	tempk	 	= input4->answer;
	a		= atof(input5->answer);
	b		= atof(input6->answer);
	disp	 	= input7->answer;
	z0m	 	= input8->answer;
	z0h	 	= input9->answer;
	u2m	 	= input10->answer;
	
	result  = output1->answer;
	sebal = flag1->answer;
	verbose = (!flag2->answer);
	/***************************************************/
	mapset = G_find_cell2(rohair, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), rohair);
	}
	data_type_rohair = G_raster_map_type(rohair,mapset);
	if ( (infd_rohair = G_open_cell_old (rohair,mapset)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), rohair);
	if (G_get_cellhd (rohair, mapset, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s])"), rohair);
	inrast_rohair = G_allocate_raster_buf(data_type_rohair);
	/***************************************************/
	if(!sebal){
		mapset = G_find_cell2 (dtair, "");
		if (mapset == NULL) {
			G_fatal_error(_("cell file [%s] not found"),dtair);
		}
		data_type_dtair = G_raster_map_type(dtair,mapset);
		if ( (infd_dtair = G_open_cell_old (dtair,mapset)) < 0)
			G_fatal_error(_("Cannot open cell file [%s]"), dtair);
		if (G_get_cellhd (dtair, mapset, &cellhd) < 0)
			G_fatal_error(_("Cannot read file header of [%s]"), dtair);
		inrast_dtair = G_allocate_raster_buf(data_type_dtair);
	}
	/***************************************************/
	mapset = G_find_cell2 (tempk, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), tempk);
	}
	data_type_tempk = G_raster_map_type(tempk,mapset);
	if ( (infd_tempk = G_open_cell_old (tempk,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), tempk);
	if (G_get_cellhd (tempk, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), tempk);
	inrast_tempk = G_allocate_raster_buf(data_type_tempk);
	/***************************************************/
	mapset = G_find_cell2 (disp, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), disp);
	}
	data_type_disp = G_raster_map_type(disp,mapset);
	if ( (infd_disp = G_open_cell_old (disp,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), disp);
	if (G_get_cellhd (disp, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), disp);
	inrast_disp = G_allocate_raster_buf(data_type_disp);
	/***************************************************/
	mapset = G_find_cell2 (z0m, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), z0m);
	}
	data_type_z0m = G_raster_map_type(z0m,mapset);
	if ( (infd_z0m = G_open_cell_old (z0m,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), z0m);
	if (G_get_cellhd (z0m, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), z0m);
	inrast_z0m = G_allocate_raster_buf(data_type_z0m);
	/***************************************************/
	mapset = G_find_cell2 (z0h, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), z0h);
	}
	data_type_z0h = G_raster_map_type(z0h,mapset);
	if ( (infd_z0h = G_open_cell_old (z0h,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), z0h);
	if (G_get_cellhd (z0h, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), z0h);
	inrast_z0h = G_allocate_raster_buf(data_type_z0h);
	/***************************************************/
	mapset = G_find_cell2 (u2m, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), u2m);
	}
	data_type_u2m = G_raster_map_type(u2m,mapset);
	if ( (infd_u2m = G_open_cell_old (u2m,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), u2m);
	if (G_get_cellhd (u2m, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), u2m);
	inrast_u2m = G_allocate_raster_buf(data_type_u2m);
	/***************************************************/
	G_debug(3, "number of rows %d",cellhd.rows);
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast = G_allocate_raster_buf(data_type_output);
	/* Create New raster files */
	if ( (outfd = G_open_raster_new (result,data_type_output)) < 0)
		G_fatal_error(_("Could not open <%s>"),result);
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
		DCELL d_u2m;
		if(verbose)
			G_percent(row,nrows,2);
//		printf("row = %i/%i\n",row,nrows);
		/* read soil input maps */	
		if(G_get_raster_row(infd_rohair,inrast_rohair,row,data_type_rohair)<0)
			G_fatal_error(_("Could not read from <%s>"),rohair);
		if(!sebal){
			if(G_get_raster_row(infd_dtair,inrast_dtair,row,data_type_dtair)<0)
			G_fatal_error(_("Could not read from <%s>"),dtair);
		}
		if(G_get_raster_row(infd_tempk,inrast_tempk,row,data_type_tempk)<0)
			G_fatal_error(_("Could not read from <%s>"),tempk);
		if(G_get_raster_row(infd_disp,inrast_disp,row,data_type_disp)<0)
			G_fatal_error(_("Could not read from <%s>"),disp);
		if(G_get_raster_row(infd_z0m,inrast_z0m,row,data_type_z0m)<0)
			G_fatal_error(_("Could not read from <%s>"),z0m);
		if(G_get_raster_row(infd_z0h,inrast_z0h,row,data_type_z0h)<0)
			G_fatal_error(_("Could not read from <%s>"),z0h);
		if(G_get_raster_row(infd_u2m,inrast_u2m,row,data_type_u2m)<0)
			G_fatal_error(_("Could not read from <%s>"),u2m);
		/*process the data */
		for (col=0; col < ncols; col++)
		{
			d_rohair = ((DCELL *) inrast_rohair)[col];
			if(!sebal){
				d_dtair = ((DCELL *) inrast_dtair)[col];
			}
			d_tempk = ((DCELL *) inrast_tempk)[col];
			d_disp = ((DCELL *) inrast_disp)[col];
			d_z0m = ((DCELL *) inrast_z0m)[col];
			d_z0h = ((DCELL *) inrast_z0h)[col];
			d_u2m = ((DCELL *) inrast_u2m)[col];
			if(G_is_d_null_value(&d_rohair)){
				((DCELL *) outrast)[col] = -999.99;
			}else if((!sebal)&&G_is_d_null_value(&d_dtair)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_tempk)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_disp)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_z0m)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_z0h)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_u2m)){
				((DCELL *) outrast)[col] = -999.99;
			}else {
				/************************************/
				/* calculate sensible heat flux	    */
				if(sebal){//if -s flag then calculate Delta T from Coefs
					d_affine=a*d_tempk+b;
					// Run iterations to find Rah
					d_rah=fixed_deltat(d_u2m,d_rohair,cp,d_affine,d_disp,d_z0m,d_z0h,d_tempk);
					//Process h
					d = h0(d_rohair,cp,d_rah,d_affine);
				}else{// not -s flag then take delta T map input directly
					// Run iterations to find Rah
					d_rah=fixed_deltat(d_u2m,d_rohair,cp,d_dtair,d_disp,d_z0m,d_z0h,d_tempk);
					//Process h
					d = h0(d_rohair,cp,d_rah,d_dtair);
				}
				((DCELL *) outrast)[col] = d;
			}
		}
		if (G_put_raster_row (outfd, outrast, data_type_output) < 0)
			G_fatal_error(_("Cannot write to output raster file"));
	}
	G_free (inrast_rohair);
	if(!sebal){
		G_free (inrast_dtair);
	}
	G_free (inrast_tempk);
	G_free (inrast_disp);
	G_free (inrast_z0m);
	G_free (inrast_z0h);
	G_free (inrast_u2m);

	G_close_cell (infd_rohair);
	if(!sebal){
		G_close_cell (infd_dtair);
	}
	G_close_cell (infd_tempk);
	G_close_cell (infd_disp);
	G_close_cell (infd_z0m);
	G_close_cell (infd_z0h);
	G_close_cell (infd_u2m);
	
	G_free (outrast);
	G_close_cell (outfd);

	G_short_history(result, "raster", &history);
	G_command_history(&history);
	G_write_history(result,&history);

	exit(EXIT_SUCCESS);
}

