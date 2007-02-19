/****************************************************************************
 *
 * MODULE:       r.eb.g0
 * AUTHOR(S):    Yann Chemin - ychemin@gmail.com
 * PURPOSE:      Calculates an approximation of soil heat flux
 *               as seen in Bastiaanssen (1995) using time of
 *               satellite overpass.
 *
 * COPYRIGHT:    (C) 2002-2006 by the GRASS Development Team
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


double g_0(double bbalb, double ndvi, double tempk, double rnet, double time, int roerink);

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	int roerink=0;//Roerink Flag for HAPEX-Sahel conditions
	struct GModule *module;
	struct Option *input1, *input2, *input3, *input4, *input5, *output1;
	
	struct Flag *flag1, *flag2;	
	struct History history; //metadata
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   // input raster name
	char *result; //output raster name
	//File Descriptors
	int infd_albedo, infd_ndvi, infd_tempk, infd_rnet, infd_time;
	int outfd;
	
	char *albedo,*ndvi,*tempk,*rnet,*time;
	
	int i=0,j=0;
	
	void *inrast_albedo, *inrast_ndvi, *inrast_tempk, *inrast_rnet, *inrast_time;
	unsigned char *outrast;
	RASTER_MAP_TYPE data_type_albedo;
	RASTER_MAP_TYPE data_type_ndvi;
	RASTER_MAP_TYPE data_type_tempk;
	RASTER_MAP_TYPE data_type_rnet;
	RASTER_MAP_TYPE data_type_time;
	
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("soil heat flux, energy balance, SEBAL");
	module->description = _("soil heat flux approximation (Bastiaanssen, 1995)");

	/* Define the different options */
	input1 = G_define_option() ;
	input1->key	   = _("albedo");
	input1->type       = TYPE_STRING;
	input1->required   = YES;
	input1->gisprompt  =_("old,cell,raster") ;
	input1->description=_("Name of the Albedo map [0.0;1.0]");
	input1->answer     =_("albedo");

	input2 = G_define_option() ;
	input2->key        =_("ndvi");
	input2->type       = TYPE_STRING;
	input2->required   = YES;
	input2->gisprompt  =_("old,cell,raster");
	input2->description=_("Name of the ndvi map [-1.0;+1.0]");
	input2->answer     =_("ndvi");

	input3 = G_define_option() ;
	input3->key        =_("tempk");
	input3->type       = TYPE_STRING;
	input3->required   = YES;
	input3->gisprompt  =_("old,cell,raster");
	input3->description=_("Name of the Surface temperature map [degree Kelvin]");
	input3->answer     =_("tempk");

	input4 = G_define_option() ;
	input4->key        =_("rnet");
	input4->type       = TYPE_STRING;
	input4->required   = YES;
	input4->gisprompt  =_("old,cell,raster");
	input4->description=_("Name of the Net Radiation map [W/m2]");
	input4->answer     =_("rnet");

	input5 = G_define_option() ;
	input5->key        =_("time");
	input5->type       = TYPE_STRING;
	input5->required   = YES;
	input5->gisprompt  =_("old,cell,raster");
	input5->description=_("Name of the time of satellite overpass map [local UTC]");
	input5->answer     =_("time");
	
	output1 = G_define_option() ;
	output1->key        =_("g0");
	output1->type       = TYPE_STRING;
	output1->required   = YES;
	output1->gisprompt  =_("new,cell,raster");
	output1->description=_("Name of the output g0 layer");
	output1->answer     =_("g0");

	flag1 = G_define_flag();
	flag1->key = 'r';
	flag1->description = _("HAPEX-Sahel empirical correction (Roerink, 1995)");
	
	flag2 = G_define_flag();
	flag2->key = 'q';
	flag2->description = _("Quiet");

	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	albedo	 	= input1->answer;
	ndvi	 	= input2->answer;
	tempk		= input3->answer;
	rnet	 	= input4->answer;
	time	 	= input5->answer;
	
	result  = output1->answer;
	roerink = flag1->answer;
	verbose = (!flag2->answer);
	/***************************************************/
	mapset = G_find_cell2(albedo, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), albedo);
	}
	data_type_albedo = G_raster_map_type(albedo,mapset);
	if ( (infd_albedo = G_open_cell_old (albedo,mapset)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), albedo);
	if (G_get_cellhd (albedo, mapset, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s])"), albedo);
	inrast_albedo = G_allocate_raster_buf(data_type_albedo);
	/***************************************************/
	mapset = G_find_cell2 (ndvi, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"),ndvi);
	}
	data_type_ndvi = G_raster_map_type(ndvi,mapset);
	if ( (infd_ndvi = G_open_cell_old (ndvi,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), ndvi);
	if (G_get_cellhd (ndvi, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), ndvi);
	inrast_ndvi = G_allocate_raster_buf(data_type_ndvi);
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
	mapset = G_find_cell2 (rnet, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), rnet);
	}
	data_type_rnet = G_raster_map_type(rnet,mapset);
	if ( (infd_rnet = G_open_cell_old (rnet,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), rnet);
	if (G_get_cellhd (rnet, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), rnet);
	inrast_rnet = G_allocate_raster_buf(data_type_rnet);
	/***************************************************/
	mapset = G_find_cell2 (time, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), time);
	}
	data_type_time = G_raster_map_type(time,mapset);
	if ( (infd_time = G_open_cell_old (time,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), time);
	if (G_get_cellhd (time, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), time);
	inrast_time = G_allocate_raster_buf(data_type_time);
	/***************************************************/
	G_debug(3, "number of rows %d",cellhd.rows);
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast = G_allocate_raster_buf(data_type_albedo);
	/* Create New raster files */
	if ( (outfd = G_open_raster_new (result,data_type_albedo)) < 0)
		G_fatal_error(_("Could not open <%s>"),result);
	/* Process pixels */
	for (row = 0; row < nrows; row++)
	{
		DCELL d;
		DCELL d_albedo;
		DCELL d_ndvi;
		DCELL d_tempk;
		DCELL d_rnet;
		DCELL d_time;
		if(verbose)
			G_percent(row,nrows,2);
//		printf("row = %i/%i\n",row,nrows);
		/* read soil input maps */	
		if(G_get_raster_row(infd_albedo,inrast_albedo,row,data_type_albedo)<0)
			G_fatal_error(_("Could not read from <%s>"),albedo);
		if(G_get_raster_row(infd_ndvi,inrast_ndvi,row,data_type_ndvi)<0)
			G_fatal_error(_("Could not read from <%s>"),ndvi);
		if(G_get_raster_row(infd_tempk,inrast_tempk,row,data_type_tempk)<0)
			G_fatal_error(_("Could not read from <%s>"),tempk);
		if(G_get_raster_row(infd_rnet,inrast_rnet,row,data_type_rnet)<0)
			G_fatal_error(_("Could not read from <%s>"),rnet);
		if(G_get_raster_row(infd_time,inrast_time,row,data_type_time)<0)
			G_fatal_error(_("Could not read from <%s>"),time);
		/*process the data */
		for (col=0; col < ncols; col++)
		{
		//	printf("col=%i/%i ",col,ncols);
			d_albedo = ((DCELL *) inrast_albedo)[col];
 		//	printf("albedo = %5.3f", d_albedo);
			d_ndvi = ((DCELL *) inrast_ndvi)[col];
 		//	printf(" ndvi = %5.3f", d_ndvi);
			d_tempk = ((DCELL *) inrast_tempk)[col];
 		//	printf(" tempk = %5.3f", d_tempk);
			d_rnet = ((DCELL *) inrast_rnet)[col];
 		//	printf("inrast_rnet = %f\n", d_rnet);
			d_time = ((DCELL *) inrast_time)[col];
 		//	printf("inrast_time = %f\n", d_time);
			if(G_is_d_null_value(&d_albedo)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_ndvi)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_tempk)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_rnet)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_time)){
				((DCELL *) outrast)[col] = -999.99;
			}else {
				/************************************/
				/* calculate soil heat flux	    */
				d = g_0(d_albedo,d_ndvi,d_tempk,d_rnet,d_time,roerink);
		//		printf(" || d=%5.3f",d);
				((DCELL *) outrast)[col] = d;
		//		printf(" -> %5.3f\n",d);
			}
		//	if(row==50){
		//		exit(EXIT_SUCCESS);
		//	}
		}
		if (G_put_raster_row (outfd, outrast, data_type_albedo) < 0)
			G_fatal_error(_("Cannot write to output raster file"));
	}

	G_free (inrast_albedo);
	G_free (inrast_ndvi);
	G_free (inrast_tempk);
	G_free (inrast_rnet);
	G_free (inrast_time);
	G_close_cell (infd_albedo);
	G_close_cell (infd_ndvi);
	G_close_cell (infd_tempk);
	G_close_cell (infd_rnet);
	G_close_cell (infd_time);
	
	G_free (outrast);
	G_close_cell (outfd);

	G_short_history(result, "raster", &history);
	G_command_history(&history);
	G_write_history(result,&history);

	exit(EXIT_SUCCESS);
}

