/****************************************************************************
 *
 * MODULE:       r.eb.rah
 * AUTHOR(S):    Yann Chemin - ychemin@gmail.com
 * PURPOSE:      Calculates aerodynamic resistance to heat transport
 *               This has been seen in Pawan (2004).
 *
 * COPYRIGHT:    (C) 2006 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>


double ra_h(double disp,double z0h,double psih,double ustar);

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	struct GModule *module;
	struct Option *input1, *input2, *input3, *input4, *output1;
	
	struct Flag *flag1;	
	struct History history; //metadata
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   // input raster name
	char *result; //output raster name
	//File Descriptors
	int infd_disp, infd_z0h,infd_psih,infd_ustar;
	int outfd;
	
	char *disp, *z0h, *psih, *ustar;

	double cp; //air specific heat	
	int i=0,j=0;
	double a,b; //SEBAL slope and intercepts of surf. temp.
	
	void *inrast_disp, *inrast_z0h, *inrast_psih, *inrast_ustar;
	unsigned char *outrast;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_disp;
	RASTER_MAP_TYPE data_type_z0h;
	RASTER_MAP_TYPE data_type_psih;
	RASTER_MAP_TYPE data_type_ustar;
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("rah, energy balance, SEBAL");
	module->description = _("aerodynamic resistance to heat transport as in Pawan (2004).");

	/* Define the different options */
	input1 = G_define_option() ;
	input1->key	   = _("disp");
	input1->type       = TYPE_STRING;
	input1->required   = YES;
	input1->gisprompt  =_("old,dcell,raster") ;
	input1->description=_("Name of the displacement height map");
	input1->answer     =_("disp");

	input2 = G_define_option() ;
	input2->key        =_("z0h");
	input2->type       = TYPE_STRING;
	input2->required   = YES;
	input2->gisprompt  =_("old,cell,raster");
	input2->description=_("Name of the height of heat flux roughness length");
	input2->answer     =_("z0h");

	input3 = G_define_option() ;
	input3->key        =_("psih");
	input3->type       = TYPE_STRING;
	input3->required   = YES;
	input3->gisprompt  =_("old,dcell,raster");
	input3->description=_("Name of the psichrometric parameter for heat flux");
	input3->answer     =_("psih");

	input4 = G_define_option() ;
	input4->key        =_("ustar");
	input4->type       = TYPE_STRING;
	input4->required   = YES;
	input4->gisprompt  =_("old,dcell,raster");
	input4->description=_("Name of the nominal wind speed");
	input4->answer     =_("ustar");
	
	output1 = G_define_option() ;
	output1->key        =_("rah");
	output1->type       = TYPE_STRING;
	output1->required   = YES;
	output1->gisprompt  =_("new,dcell,raster");
	output1->description=_("Name of the output rah layer");
	output1->answer     =_("rah");

	flag1 = G_define_flag();
	flag1->key = 'q';
	flag1->description = _("Quiet");
	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	disp	 	= input1->answer;
	z0h	 	= input2->answer;
	psih		= input3->answer;
	ustar	 	= input4->answer;
	
	result  = output1->answer;
	verbose = (!flag1->answer);
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
	mapset = G_find_cell2 (psih, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), psih);
	}
	data_type_psih = G_raster_map_type(psih,mapset);
	if ( (infd_psih = G_open_cell_old (psih,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), psih);
	if (G_get_cellhd (psih, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), psih);
	inrast_psih = G_allocate_raster_buf(data_type_psih);
	/***************************************************/
	mapset = G_find_cell2 (ustar, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), ustar);
	}
	data_type_ustar = G_raster_map_type(ustar,mapset);
	if ( (infd_ustar = G_open_cell_old (ustar,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), ustar);
	if (G_get_cellhd (ustar, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), ustar);
	inrast_ustar = G_allocate_raster_buf(data_type_ustar);
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
		DCELL d_rah;
		DCELL d_disp;
		DCELL d_z0h;
		DCELL d_psih;
		DCELL d_ustar;
		if(verbose)
			G_percent(row,nrows,2);
//		printf("row = %i/%i\n",row,nrows);
		/* read soil input maps */	
		if(G_get_raster_row(infd_disp,inrast_disp,row,data_type_disp)<0)
			G_fatal_error(_("Could not read from <%s>"),disp);
		if(G_get_raster_row(infd_z0h,inrast_z0h,row,data_type_z0h)<0)
			G_fatal_error(_("Could not read from <%s>"),z0h);
		if(G_get_raster_row(infd_psih,inrast_psih,row,data_type_psih)<0)
			G_fatal_error(_("Could not read from <%s>"),psih);
		if(G_get_raster_row(infd_ustar,inrast_ustar,row,data_type_ustar)<0)
			G_fatal_error(_("Could not read from <%s>"),ustar);
		/*process the data */
		for (col=0; col < ncols; col++)
		{
			d_disp = ((DCELL *) inrast_disp)[col];
			d_z0h = ((DCELL *) inrast_z0h)[col];
			d_psih = ((DCELL *) inrast_psih)[col];
			d_ustar = ((DCELL *) inrast_ustar)[col];
			if(G_is_d_null_value(&d_disp)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_z0h)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_psih)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_ustar)){
				((DCELL *) outrast)[col] = -999.99;
			}else {
				/************************************/
				/* calculate rah   */
				d_rah=ra_h(d_disp,d_z0h,d_psih,d_ustar);
				((DCELL *) outrast)[col] = d;
			}
		}
		if (G_put_raster_row (outfd, outrast, data_type_output) < 0)
			G_fatal_error(_("Cannot write to output raster file"));
	}
	G_free (inrast_disp);
	G_free (inrast_z0h);
	G_free (inrast_psih);
	G_free (inrast_ustar);

	G_close_cell (infd_disp);
	G_close_cell (infd_z0h);
	G_close_cell (infd_psih);
	G_close_cell (infd_ustar);
	
	G_free (outrast);
	G_close_cell (outfd);

	G_short_history(result, "raster", &history);
	G_command_history(&history);
	G_write_history(result,&history);

	exit(EXIT_SUCCESS);
}

