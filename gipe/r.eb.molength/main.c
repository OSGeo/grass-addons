/****************************************************************************
 *
 * MODULE:       r.eb.molength
 * AUTHOR(S):    Yann Chemin - ychemin@gmail.com
 * PURPOSE:      Calculates the Monin-Obukov Length
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


double mo_length(double roh_air, double cp, double ustar, double tempk, double h0);

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	struct GModule *module;
	struct Option *input1, *input2, *input3, *input4, *input5;
	struct Option *output1;
	
	struct Flag *flag1;	
	struct History history; //metadata
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   // input raster name
	char *result; //output raster name
	//File Descriptors
	int infd_rohair, infd_tempk, infd_ustar, infd_h0;
	int outfd;
	
	char *rohair,*tempk,*ustar,*h0;

	double cp; //air specific heat	
	int i=0,j=0;
	
	void *inrast_rohair, *inrast_tempk, *inrast_ustar, *inrast_h0;
	unsigned char *outrast;
	
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_rohair;
	RASTER_MAP_TYPE data_type_tempk;
	RASTER_MAP_TYPE data_type_ustar;
	RASTER_MAP_TYPE data_type_h0;
	
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("Monin-Obukov Length, energy balance, SEBAL");
	module->description = _("Monin-Obukov Length");

	/* Define the different options */
	input1 = G_define_option() ;
	input1->key	   = _("rohair");
	input1->type       = TYPE_STRING;
	input1->required   = YES;
	input1->gisprompt  =_("old,cell,raster") ;
	input1->description=_("Name of the air density map ~[0.9;1.5]");
	input1->answer     =_("rohair");

	input2 = G_define_option() ;
	input2->key        =_("cp");
	input2->type       = TYPE_DOUBLE;
	input2->required   = YES;
	input2->gisprompt  =_("parameter, float number");
	input2->description=_("Value of the air specific heat [1000.0;1020.0]");
	input2->answer     =_("1004.0");

	input3 = G_define_option() ;
	input3->key        =_("ustar");
	input3->type       = TYPE_STRING;
	input3->required   = YES;
	input3->gisprompt  =_("old,cell,raster");
	input3->description=_("Name of the ustar map");
	input3->answer     =_("ustar");

	input4 = G_define_option() ;
	input4->key        =_("tempk");
	input4->type       = TYPE_STRING;
	input4->required   = YES;
	input4->gisprompt  =_("old,cell,raster");
	input4->description=_("Name of the surface skin temperature map [degrees Kelvin]");
	input4->answer     =_("tempk");
	
	input5 = G_define_option() ;
	input5->key        =_("h0");
	input5->type       = TYPE_STRING;
	input5->required   = YES;
	input5->gisprompt  =_("new,cell,raster");
	input5->description=_("Name of the sensible heat flux map");
	input5->answer     =_("h0");

	output1 = G_define_option() ;
	output1->key        =_("molength");
	output1->type       = TYPE_STRING;
	output1->required   = YES;
	output1->gisprompt  =_("new,cell,raster");
	output1->description=_("Name of the output Monin-Obukov Length layer");
	output1->answer     =_("molength");
	
	flag1 = G_define_flag();
	flag1->key = 'q';
	flag1->description = _("Quiet");
	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	rohair	 	= input1->answer;
	cp	 	= atof(input2->answer);
	ustar		= input3->answer;
	tempk	 	= input4->answer;
	h0	 	= input5->answer;
	
	result  = output1->answer;
	verbose = (!flag1->answer);
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
	mapset = G_find_cell2 (h0, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), h0);
	}
	data_type_h0 = G_raster_map_type(h0,mapset);
	if ( (infd_h0 = G_open_cell_old (h0,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), h0);
	if (G_get_cellhd (h0, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), h0);
	inrast_h0 = G_allocate_raster_buf(data_type_h0);
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
		DCELL d_ustar;
		DCELL d_tempk;
		DCELL d_h0;
		if(verbose)
			G_percent(row,nrows,2);
//		printf("row = %i/%i\n",row,nrows);
		/* read input maps */	
		if(G_get_raster_row(infd_rohair,inrast_rohair,row,data_type_rohair)<0)
			G_fatal_error(_("Could not read from <%s>"),rohair);
		if(G_get_raster_row(infd_ustar,inrast_ustar,row,data_type_ustar)<0)
			G_fatal_error(_("Could not read from <%s>"),ustar);
		if(G_get_raster_row(infd_tempk,inrast_tempk,row,data_type_tempk)<0)
			G_fatal_error(_("Could not read from <%s>"),tempk);
		if(G_get_raster_row(infd_h0,inrast_h0,row,data_type_h0)<0)
			G_fatal_error(_("Could not read from <%s>"),h0);
		/*process the data */
		for (col=0; col < ncols; col++)
		{
			d_rohair = ((DCELL *) inrast_rohair)[col];
			d_ustar = ((DCELL *) inrast_ustar)[col];
			d_tempk = ((DCELL *) inrast_tempk)[col];
			d_h0 = ((DCELL *) inrast_h0)[col];
			if(G_is_d_null_value(&d_rohair)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_ustar)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_tempk)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_h0)){
				((DCELL *) outrast)[col] = -999.99;
			}else {
				/************************************/
				/* calculate Monin-Obukov Length    */
				d = mo_length(d_rohair,cp,d_ustar,d_tempk, d_h0);
				((DCELL *) outrast)[col] = d;
			}
		}
		if (G_put_raster_row (outfd, outrast, data_type_output) < 0)
			G_fatal_error(_("Cannot write to output raster file"));
	}

	G_free (inrast_rohair);
	G_free (inrast_ustar);
	G_free (inrast_tempk);
	G_free (inrast_h0);

	G_close_cell (infd_rohair);
	G_close_cell (infd_ustar);
	G_close_cell (infd_tempk);
	G_close_cell (infd_h0);
	
	G_free (outrast);
	G_close_cell (outfd);

	G_short_history(result, "raster", &history);
	G_command_history(&history);
	G_write_history(result,&history);

	exit(EXIT_SUCCESS);
}

