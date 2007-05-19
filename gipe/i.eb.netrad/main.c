/****************************************************************************
 *
 * MODULE:       i.eb.netrad
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the instantaneous net radiation at 
 *               as seen in Bastiaanssen (1995) using time of
 *               satellite overpass.
 *
 * COPYRIGHT:    (C) 2006-2007 by the GRASS Development Team
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

double r_net( double bbalb, double ndvi, double tempk, double dtair,  double e0, double tsw, double doy, double utc, double sunzangle);

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	struct GModule *module;
	struct Option *input1, *input2, *input3, *input4, *input5;
	struct Option *input6, *input7, *input8, *input9, *output1;
	
	struct Flag *flag1;	
	struct History history; //metadata
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   // input raster name
	char *result; //output raster name
	//File Descriptors
	int infd_albedo, infd_ndvi, infd_tempk, infd_time, infd_dtair;
	int infd_emissivity, infd_tsw, infd_doy, infd_sunzangle;
	int outfd;
	
	char *albedo,*ndvi,*tempk,*time,*dtair,*emissivity,*tsw,*doy,*sunzangle;
	
	int i=0,j=0;
	
	void *inrast_albedo, *inrast_ndvi, *inrast_tempk, *inrast_rnet;
	void *inrast_time, *inrast_dtair, *inrast_emissivity, *inrast_tsw;
	void *inrast_doy, *inrast_sunzangle;

	unsigned char *outrast;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_albedo;
	RASTER_MAP_TYPE data_type_ndvi;
	RASTER_MAP_TYPE data_type_tempk;
	RASTER_MAP_TYPE data_type_time;
	RASTER_MAP_TYPE data_type_dtair;
	RASTER_MAP_TYPE data_type_emissivity;
	RASTER_MAP_TYPE data_type_tsw;
	RASTER_MAP_TYPE data_type_doy;
	RASTER_MAP_TYPE data_type_sunzangle;
	
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("net radiation, energy balance, SEBAL");
	module->description = _("net radiation approximation (Bastiaanssen, 1995)");

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
	input4->key        =_("time");
	input4->type       = TYPE_STRING;
	input4->required   = YES;
	input4->gisprompt  =_("old,cell,raster");
	input4->description=_("Name of the map of local UTC time of satellite overpass [hh.hhh]");
	input4->answer     =_("time");

	input5 = G_define_option() ;
	input5->key        =_("dtair");
	input5->type       = TYPE_STRING;
	input5->required   = YES;
	input5->gisprompt  =_("old,cell,raster");
	input5->description=_("Name of the difference of temperature from surface skin to about 2 m height [K]");
	input5->answer     =_("dtair");
	
	input6 = G_define_option() ;
	input6->key        =_("emissivity");
	input6->type       = TYPE_STRING;
	input6->required   = YES;
	input6->gisprompt  =_("old,cell,raster");
	input6->description=_("Name of the emissivity map [-]");
	input6->answer     =_("emissivity");

	input7 = G_define_option() ;
	input7->key        =_("tsw");
	input7->type       = TYPE_STRING;
	input7->required   = YES;
	input7->gisprompt  =_("old,cell,raster");
	input7->description=_("Name of the single-way atmospheric transmissivitymap [-]");
	input7->answer     =_("tsw");

	input8 = G_define_option() ;
	input8->key        =_("doy");
	input8->type       = TYPE_STRING;
	input8->required   = YES;
	input8->gisprompt  =_("old,cell,raster");
	input8->description=_("Name of the Day Of Year (DOY) map [-]");
	input8->answer     =_("doy");

	input9 = G_define_option() ;
	input9->key        =_("sunzangle");
	input9->type       = TYPE_STRING;
	input9->required   = YES;
	input9->gisprompt  =_("old,cell,raster");
	input9->description=_("Name of the sun zenith angle map [degrees]");
	input9->answer     =_("sunzangle");

	output1 = G_define_option() ;
	output1->key        =_("rnet");
	output1->type       = TYPE_STRING;
	output1->required   = YES;
	output1->gisprompt  =_("new,cell,raster");
	output1->description=_("Name of the output rnet layer");
	output1->answer     =_("rnet");

	flag1 = G_define_flag();
	flag1->key = 'q';
	flag1->description = _("Quiet");

	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	albedo	 	= input1->answer;
	ndvi	 	= input2->answer;
	tempk		= input3->answer;
	time	 	= input4->answer;
	dtair	 	= input5->answer;
	emissivity	= input6->answer;
	tsw		= input7->answer;
	doy		= input8->answer;
	sunzangle	= input9->answer;

	result  = output1->answer;
	verbose = (!flag1->answer);
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
	mapset = G_find_cell2 (dtair, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), dtair);
	}
	data_type_dtair = G_raster_map_type(dtair,mapset);
	if ( (infd_dtair = G_open_cell_old (dtair,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), dtair);
	if (G_get_cellhd (dtair, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), dtair);
	inrast_dtair = G_allocate_raster_buf(data_type_dtair);
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
	mapset = G_find_cell2 (emissivity, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), emissivity);
	}
	data_type_emissivity = G_raster_map_type(emissivity,mapset);
	if ( (infd_emissivity = G_open_cell_old (emissivity,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), emissivity);
	if (G_get_cellhd (emissivity, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), emissivity);
	inrast_emissivity = G_allocate_raster_buf(data_type_emissivity);
	/***************************************************/
	mapset = G_find_cell2 (tsw, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), tsw);
	}
	data_type_tsw = G_raster_map_type(tsw,mapset);
	if ( (infd_tsw = G_open_cell_old (tsw,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), tsw);
	if (G_get_cellhd (tsw, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), tsw);
	inrast_tsw = G_allocate_raster_buf(data_type_tsw);
	/***************************************************/
	mapset = G_find_cell2 (doy, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), doy);
	}
	data_type_doy = G_raster_map_type(doy,mapset);
	if ( (infd_doy = G_open_cell_old (doy,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), doy);
	if (G_get_cellhd (doy, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), doy);
	inrast_doy = G_allocate_raster_buf(data_type_doy);
	/***************************************************/
	mapset = G_find_cell2 (sunzangle, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), sunzangle);
	}
	data_type_sunzangle = G_raster_map_type(sunzangle,mapset);
	if ( (infd_sunzangle = G_open_cell_old (sunzangle,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), sunzangle);
	if (G_get_cellhd (sunzangle, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), sunzangle);
	inrast_sunzangle = G_allocate_raster_buf(data_type_sunzangle);
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
		DCELL d_albedo;
		DCELL d_ndvi;
		DCELL d_tempk;
		DCELL d_dtair;
		DCELL d_time;
		DCELL d_emissivity;
		DCELL d_tsw;
		DCELL d_doy;
		DCELL d_sunzangle;
		if(verbose)
			G_percent(row,nrows,2);
		/* read input maps */	
		if(G_get_raster_row(infd_albedo,inrast_albedo,row,data_type_albedo)<0)
			G_fatal_error(_("Could not read from <%s>"),albedo);
		if(G_get_raster_row(infd_ndvi,inrast_ndvi,row,data_type_ndvi)<0)
			G_fatal_error(_("Could not read from <%s>"),ndvi);
		if(G_get_raster_row(infd_tempk,inrast_tempk,row,data_type_tempk)<0)
			G_fatal_error(_("Could not read from <%s>"),tempk);
		if(G_get_raster_row(infd_dtair,inrast_dtair,row,data_type_dtair)<0)
			G_fatal_error(_("Could not read from <%s>"),dtair);
		if(G_get_raster_row(infd_time,inrast_time,row,data_type_time)<0)
			G_fatal_error(_("Could not read from <%s>"),time);
		if(G_get_raster_row(infd_emissivity,inrast_emissivity,row,data_type_emissivity)<0)
			G_fatal_error(_("Could not read from <%s>"),emissivity);
		if(G_get_raster_row(infd_tsw,inrast_tsw,row,data_type_tsw)<0)
			G_fatal_error(_("Could not read from <%s>"),tsw);
		if(G_get_raster_row(infd_doy,inrast_doy,row,data_type_doy)<0)
			G_fatal_error(_("Could not read from <%s>"),doy);
		if(G_get_raster_row(infd_sunzangle,inrast_sunzangle,row,data_type_sunzangle)<0)
			G_fatal_error(_("Could not read from <%s>"),sunzangle);
		/*process the data */
		for (col=0; col < ncols; col++)
		{
			switch(data_type_albedo){
				case CELL_TYPE:
					d_albedo = (double) ((CELL *) inrast_albedo)[col];
					break;
				case FCELL_TYPE:
					d_albedo = (double) ((FCELL *) inrast_albedo)[col];
					break;
				case DCELL_TYPE:
					d_albedo = ((DCELL *) inrast_albedo)[col];
					break;
			}
			switch(data_type_ndvi){
				case CELL_TYPE:
					d_ndvi = (double) ((CELL *) inrast_ndvi)[col];
					break;
				case FCELL_TYPE:
					d_ndvi = (double) ((FCELL *) inrast_ndvi)[col];
					break;
				case DCELL_TYPE:
					d_ndvi = ((DCELL *) inrast_ndvi)[col];
					break;
			}
			switch(data_type_tempk){
				case CELL_TYPE:
					d_tempk = (double) ((CELL *) inrast_tempk)[col];
					break;
				case FCELL_TYPE:
					d_tempk = (double) ((FCELL *) inrast_tempk)[col];
					break;
				case DCELL_TYPE:
					d_tempk = ((DCELL *) inrast_tempk)[col];
					break;
			}
			switch(data_type_dtair){
				case CELL_TYPE:
					d_dtair = (double) ((CELL *) inrast_dtair)[col];
					break;
				case FCELL_TYPE:
					d_dtair = (double) ((FCELL *) inrast_dtair)[col];
					break;
				case DCELL_TYPE:
					d_dtair = ((DCELL *) inrast_dtair)[col];
					break;
			}
			switch(data_type_time){
				case CELL_TYPE:
					d_time = (double) ((CELL *) inrast_time)[col];
					break;
				case FCELL_TYPE:
					d_time = (double) ((FCELL *) inrast_time)[col];
					break;
				case DCELL_TYPE:
					d_time = ((DCELL *) inrast_time)[col];
					break;
			}
			switch(data_type_emissivity){
				case CELL_TYPE:
					d_emissivity = (double) ((CELL *) inrast_emissivity)[col];
					break;
				case FCELL_TYPE:
					d_emissivity = (double) ((FCELL *) inrast_emissivity)[col];
					break;
				case DCELL_TYPE:
					d_emissivity = ((DCELL *) inrast_emissivity)[col];
					break;
			}
			switch(data_type_tsw){
				case CELL_TYPE:
					d_tsw = (double) ((CELL *) inrast_tsw)[col];
					break;
				case FCELL_TYPE:
					d_tsw = (double) ((FCELL *) inrast_tsw)[col];
					break;
				case DCELL_TYPE:
					d_tsw = ((DCELL *) inrast_tsw)[col];
					break;
			}
			switch(data_type_doy){
				case CELL_TYPE:
					d_doy = (double) ((CELL *) inrast_doy)[col];
					break;
				case FCELL_TYPE:
					d_doy = (double) ((FCELL *) inrast_doy)[col];
					break;
				case DCELL_TYPE:
					d_doy = ((DCELL *) inrast_doy)[col];
					break;
			}
			switch(data_type_sunzangle){
				case CELL_TYPE:
					d_sunzangle = (double) ((CELL *) inrast_sunzangle)[col];
					break;
				case FCELL_TYPE:
					d_sunzangle = (double) ((FCELL *) inrast_sunzangle)[col];
					break;
				case DCELL_TYPE:
					d_sunzangle = ((DCELL *) inrast_sunzangle)[col];
					break;
			}
			if(G_is_d_null_value(&d_albedo)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_ndvi)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_tempk)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_dtair)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_time)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_emissivity)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_tsw)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_doy)){
				((DCELL *) outrast)[col] = -999.99;
			}else if(G_is_d_null_value(&d_sunzangle)){
				((DCELL *) outrast)[col] = -999.99;
			}else {
				/************************************/
				/* calculate the net radiation	    */
				d = r_net(d_albedo,d_ndvi,d_tempk,d_dtair,d_emissivity,d_tsw,d_doy,d_time,d_sunzangle); 
		//		printf(" || d=%5.3f",d);
				((DCELL *) outrast)[col] = d;
		//		printf(" -> %5.3f\n",d);
			}
		//	if(row==50){
		//		exit(EXIT_SUCCESS);
		//	}
		}
		if (G_put_raster_row (outfd, outrast, data_type_output) < 0)
			G_fatal_error(_("Cannot write to output raster file"));
	}

	G_free (inrast_albedo);
	G_free (inrast_ndvi);
	G_free (inrast_tempk);
	G_free (inrast_dtair);
	G_free (inrast_time);
	G_free (inrast_emissivity);
	G_free (inrast_tsw);
	G_free (inrast_doy);
	G_free (inrast_sunzangle);
	G_close_cell (infd_albedo);
	G_close_cell (infd_ndvi);
	G_close_cell (infd_tempk);
	G_close_cell (infd_dtair);
	G_close_cell (infd_time);
	G_close_cell (infd_emissivity);
	G_close_cell (infd_tsw);
	G_close_cell (infd_doy);
	G_close_cell (infd_sunzangle);
	
	G_free (outrast);
	G_close_cell (outfd);

	G_short_history(result, "raster", &history);
	G_command_history(&history);
	G_write_history(result,&history);

	exit(EXIT_SUCCESS);
}

