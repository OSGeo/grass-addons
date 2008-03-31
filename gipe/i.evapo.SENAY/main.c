/****************************************************************************
 *
 * MODULE:       i.evapo.SENAY
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Creates a map of actual evapotranspiration following
 *               the method of Senay (2007).
 *
 * COPYRIGHT:    (C) 2008 by the GRASS Development Team
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

double solar_day(double lat, double doy, double tsw );
double solar_day_3d(double lat, double doy, double tsw, double slope, double aspect);
double et_pot_day( double bbalb, double solar, double tempk, double tsw, double roh_w );
double evapfr_senay( double t_hot, double t_cold, double tempk);

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	struct GModule *module;
	struct Option *input1, *input2, *input3, *input4;
	struct Option *input5, *input6, *input7, *input8, *input9;
	struct Option *output1, *output2;
	
	struct Flag *flag1, *flag2, *flag3;	
	struct History history; //metadata
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   // input raster name
	char *result1,*result2; //output raster name
	//File Descriptors
	int infd_albedo, infd_tempk, infd_dem;
	int infd_lat, infd_doy, infd_tsw;
	int infd_slope, infd_aspect;
	int outfd1, outfd2;
	
	char *albedo,*tempk,*dem,*lat,*doy,*tsw,*slope,*aspect;
	double roh_w;
	int i=0,j=0;
	
	void *inrast_albedo, *inrast_tempk;
	void *inrast_dem, *inrast_lat;
	void *inrast_doy, *inrast_tsw;
	void *inrast_slope, *inrast_aspect;

	unsigned char *outrast1, *outrast2;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_albedo;
	RASTER_MAP_TYPE data_type_tempk;
	RASTER_MAP_TYPE data_type_dem;
	RASTER_MAP_TYPE data_type_lat;
	RASTER_MAP_TYPE data_type_doy;
	RASTER_MAP_TYPE data_type_tsw;
	RASTER_MAP_TYPE data_type_slope;
	RASTER_MAP_TYPE data_type_aspect;
	/********************************/
	/* Stats for Senay equation	*/
	double t0dem_min=400.0,t0dem_max=200.0;
	double tempk_min=400.0,tempk_max=200.0;
	/********************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("Actual ET, evapotranspiration, Senay");
	module->description = _("Actual evapotranspiration, method after Senay (2007)");

	/* Define the different options */
	input1 = G_define_standard_option(G_OPT_R_INPUT) ;
	input1->key	   = _("albedo");
	input1->description=_("Name of the Albedo map [0.0-1.0]");
	input1->answer     =_("albedo");

	input2 = G_define_standard_option(G_OPT_R_INPUT) ;
	input2->key        =_("tempk");
	input2->description=_("Name of the temperature map [Degree Kelvin]");
	input2->answer     =_("tempk");

	input3 = G_define_standard_option(G_OPT_R_INPUT) ;
	input3->key        =_("dem");
	input3->description=_("Name of the elevation map [m]");
	input3->answer     =_("dem");

	input4 = G_define_standard_option(G_OPT_R_INPUT) ;
	input4->key        =_("lat");
	input4->description=_("Name of the degree latitude map [dd.ddd]");
	input4->answer     =_("lat");

	input5 = G_define_standard_option(G_OPT_R_INPUT) ;
	input5->key        =_("doy");
	input5->description=_("Name of the Day of Year map [0.0-366.0]");
	input5->answer     =_("doy");

	input6 = G_define_standard_option(G_OPT_R_INPUT) ;
	input6->key        =_("tsw");
	input6->description=_("Name of the single-way transmissivity map [0.0-1.0]");
	input6->answer     =_("tsw");

	input7 = G_define_option() ;
	input7->key        =_("roh_w");
	input7->type       = TYPE_DOUBLE;
	input7->required   = YES;
	input7->gisprompt  =_("value, parameter");
	input7->description=_("Value of the density of fresh water ~[1000-1020]");
	input7->answer     =_("1010.0");

	input8 = G_define_standard_option(G_OPT_R_INPUT) ;
	input8->key        =_("slope");
	input8->required   = NO;
	input8->description=_("Name of the Slope map ~[0-90]");

	input9 = G_define_standard_option(G_OPT_R_INPUT) ;
	input9->key        =_("aspect");
	input9->required   = NO;
	input9->description=_("Name of the Aspect map ~[0-360]");


	output1 = G_define_standard_option(G_OPT_R_OUTPUT) ;
	output1->key        =_("eta");
	output1->description=_("Name of the output Actual ET layer");
	output1->answer     =_("eta");

	output2 = G_define_standard_option(G_OPT_R_OUTPUT) ;
	output2->key        =_("evapfr");
	output2->required   = NO;
	output2->description=_("Name of the output evaporative fraction layer");

	flag1 = G_define_flag();
	flag1->key = 's';
	flag1->description = _("Output evaporative fraction after Senay (2007)");
	
	flag2 = G_define_flag();
	flag2->key = 'd';
	flag2->description = _("Slope/Aspect correction");
	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	albedo	 	= input1->answer;
	tempk	 	= input2->answer;
	dem	 	= input3->answer;
	lat		= input4->answer;
	doy	 	= input5->answer;
	tsw	 	= input6->answer;
	roh_w	 	= atof(input7->answer);
	slope	 	= input8->answer;
	aspect	 	= input9->answer;
	
	result1  = output1->answer;
	result2  = output2->answer;
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
	mapset = G_find_cell2 (tempk, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), tempk);
	}
	data_type_tempk = G_raster_map_type(tempk,mapset);
	if ( (infd_tempk = G_open_cell_old (tempk,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), tempk);
	if (G_get_cellhd (tempk, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), tempk);
	inrast_tempk = G_allocate_raster_buf(data_type_tempk);
	/***************************************************/
	mapset = G_find_cell2 (dem, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), dem);
	}
	data_type_dem = G_raster_map_type(dem,mapset);
	if ( (infd_dem = G_open_cell_old (dem,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), dem);
	if (G_get_cellhd (dem, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), dem);
	inrast_dem = G_allocate_raster_buf(data_type_dem);
	/***************************************************/
	mapset = G_find_cell2 (lat, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), lat);
	}
	data_type_lat = G_raster_map_type(lat,mapset);
	if ( (infd_lat = G_open_cell_old (lat,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), lat);
	if (G_get_cellhd (lat, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), lat);
	inrast_lat = G_allocate_raster_buf(data_type_lat);
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
	if(flag2->answer){
		mapset = G_find_cell2 (slope, "");
		if (mapset == NULL) {
			G_fatal_error(_("Cell file [%s] not found"), slope);
		}
		data_type_slope = G_raster_map_type(slope,mapset);
		if ( (infd_slope = G_open_cell_old (slope,mapset)) < 0)
			G_fatal_error(_("Cannot open cell file [%s]"), slope);
		if (G_get_cellhd (slope, mapset, &cellhd) < 0)
			G_fatal_error(_("Cannot read file header of [%s]"), slope);
		inrast_slope = G_allocate_raster_buf(data_type_slope);
	}
	/***************************************************/
	if(flag2->answer){
		mapset = G_find_cell2 (aspect, "");
		if (mapset == NULL) {
			G_fatal_error(_("Cell file [%s] not found"), aspect);
		}
		data_type_aspect = G_raster_map_type(aspect,mapset);
		if ( (infd_aspect = G_open_cell_old (aspect,mapset)) < 0)
			G_fatal_error(_("Cannot open cell file [%s]"), aspect);
		if (G_get_cellhd (aspect, mapset, &cellhd) < 0)
			G_fatal_error(_("Cannot read file header of [%s]"), aspect);
		inrast_aspect = G_allocate_raster_buf(data_type_aspect);
	}
	/***************************************************/
	G_debug(3, "number of rows %d",cellhd.rows);
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast1 = G_allocate_raster_buf(data_type_output);
	if(result2){
		outrast2 = G_allocate_raster_buf(data_type_output);
	}
	/* Create New raster files */
	if ( (outfd1 = G_open_raster_new (result1,data_type_output)) < 0)
		G_fatal_error(_("Could not open <%s>"),result1);
	if(result2){
		if ((outfd2 = G_open_raster_new (result2,data_type_output))< 0)
			G_fatal_error(_("Could not open <%s>"),result2);
	}
	/* Process tempk min / max pixels for SENAY Evapfr */
	for (row = 0; row < nrows; row++)
	{
		DCELL d;
		DCELL d_tempk;
		DCELL d_dem;
		DCELL d_t0dem;
		G_percent(row,nrows,2);
		if(G_get_raster_row(infd_tempk,inrast_tempk,row,data_type_tempk)<0)
			G_fatal_error(_("Could not read from <%s>"),tempk);
		if(G_get_raster_row(infd_dem,inrast_dem,row,data_type_dem)<0)
			G_fatal_error(_("Could not read from <%s>"),dem);
		/*process the data */
		for (col=0; col < ncols; col++)
		{
			switch(data_type_tempk){
				case CELL_TYPE:
					d_tempk = (double) ((CELL *) inrast_tempk)[col];
					break;
				case FCELL_TYPE:
					d_tempk = (double) ((FCELL *) inrast_tempk)[col];
					break;
				case DCELL_TYPE:
					d_tempk = (double) ((DCELL *) inrast_tempk)[col];
					break;
			}
			switch(data_type_dem){
				case CELL_TYPE:
					d_dem = (double) ((CELL *) inrast_dem)[col];
					break;
				case FCELL_TYPE:
					d_dem = (double) ((FCELL *) inrast_dem)[col];
					break;
				case DCELL_TYPE:
					d_dem = (double) ((DCELL *) inrast_dem)[col];
					break;
			}
			if(G_is_d_null_value(&d_tempk)){
				/* do nothing */ 
			}else if(G_is_d_null_value(&d_dem)){
				/* do nothing */ 
			}else{
				d_t0dem = d_tempk + 0.00649*d_dem;
				if(d_t0dem<0.0){
					/* do nothing */ 
				} else {
					if(d_t0dem<t0dem_min){
					//if(d_tempk<tempk_min){
						t0dem_min=d_t0dem;
						tempk_min=d_tempk;
					}else if(d_t0dem>t0dem_max){
					//}else if(d_tempk>tempk_max){
						t0dem_max=d_t0dem;
						tempk_max=d_tempk;
					}
				}
			}
		}
	}
	G_message("tempk_min=%f\ntempk_max=%f\n",tempk_min, tempk_max);
	/* Process pixels */
	for (row = 0; row < nrows; row++)
	{
		DCELL d;
		DCELL d_albedo;
		DCELL d_tempk;
		DCELL d_lat;
		DCELL d_doy;
		DCELL d_tsw;
//		DCELL d_roh_w;
		DCELL d_solar;
		DCELL d_rnetd;
		DCELL d_slope;
		DCELL d_aspect;
		DCELL d_etpotd;
		DCELL d_evapfr;
		G_percent(row,nrows,2);
		/* read input maps */	
		if(G_get_raster_row(infd_albedo,inrast_albedo,row,data_type_albedo)<0)
			G_fatal_error(_("Could not read from <%s>"),albedo);
		if(G_get_raster_row(infd_tempk,inrast_tempk,row,data_type_tempk)<0)
			G_fatal_error(_("Could not read from <%s>"),tempk);
		if(G_get_raster_row(infd_lat,inrast_lat,row,data_type_lat)<0)
			G_fatal_error(_("Could not read from <%s>"),lat);
		if(G_get_raster_row(infd_doy,inrast_doy,row,data_type_doy)<0)
			G_fatal_error(_("Could not read from <%s>"),doy);
		if(G_get_raster_row(infd_tsw,inrast_tsw,row,data_type_tsw)<0)
			G_fatal_error(_("Could not read from <%s>"),tsw);
		if(flag2->answer){
			if(G_get_raster_row(infd_slope,inrast_slope,row,data_type_slope)<0)
				G_fatal_error(_("Could not read from <%s>"),slope);
			if(G_get_raster_row(infd_aspect,inrast_aspect,row,data_type_aspect)<0)
				G_fatal_error(_("Could not read from <%s>"),aspect);
		}
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
					d_albedo = (double) ((DCELL *) inrast_albedo)[col];
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
					d_tempk = (double) ((DCELL *) inrast_tempk)[col];
					break;
			}
			switch(data_type_lat){
				case CELL_TYPE:
					d_lat = (double) ((CELL *) inrast_lat)[col];
					break;
				case FCELL_TYPE:
					d_lat = (double) ((FCELL *) inrast_lat)[col];
					break;
				case DCELL_TYPE:
					d_lat = (double) ((DCELL *) inrast_lat)[col];
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
					d_doy = (double) ((DCELL *) inrast_doy)[col];
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
					d_tsw = (double) ((DCELL *) inrast_tsw)[col];
					break;
			}
			if(flag2->answer){
				switch(data_type_slope){
					case CELL_TYPE:
						d_slope = (double) ((CELL *) inrast_slope)[col];
						break;
					case FCELL_TYPE:
						d_slope = (double) ((FCELL *) inrast_slope)[col];
						break;
					case DCELL_TYPE:
						d_slope = (double) ((DCELL *) inrast_slope)[col];
						break;
				}
				switch(data_type_aspect){
					case CELL_TYPE:
						d_aspect = (double) ((CELL *) inrast_aspect)[col];
						break;
					case FCELL_TYPE:
						d_aspect = (double) ((FCELL *) inrast_aspect)[col];
						break;
					case DCELL_TYPE:
						d_aspect = (double) ((DCELL *) inrast_aspect)[col];
						break;
				}
			}
			if(G_is_d_null_value(&d_albedo)){
				((DCELL *) outrast1)[col] = -999.99;
				if (result2)
				((DCELL *) outrast2)[col] = -999.99;
			}else if(G_is_d_null_value(&d_tempk)){
				((DCELL *) outrast1)[col] = -999.99;
				if (result2)
				((DCELL *) outrast2)[col] = -999.99;
			}else if(d_tempk<10.0){
				((DCELL *) outrast1)[col] = -999.99;
				if (result2)
				((DCELL *) outrast2)[col] = -999.99;
			}else if(G_is_d_null_value(&d_lat)){
				((DCELL *) outrast1)[col] = -999.99;
				if (result2)
				((DCELL *) outrast2)[col] = -999.99;
			}else if(G_is_d_null_value(&d_doy)){
				((DCELL *) outrast1)[col] = -999.99;
				if (result2)
				((DCELL *) outrast2)[col] = -999.99;
			}else if(G_is_d_null_value(&d_tsw)){
				((DCELL *) outrast1)[col] = -999.99;
				if (result2)
				((DCELL *) outrast2)[col] = -999.99;
			}else if((flag2->answer)&&G_is_d_null_value(&d_slope)){
				((DCELL *) outrast1)[col] = -999.99;
				if (result2)
					((DCELL *) outrast2)[col] = -999.99;
			}else if((flag2->answer)&&G_is_d_null_value(&d_aspect)){
				((DCELL *) outrast1)[col] = -999.99;
				if (result2)
					((DCELL *) outrast2)[col] = -999.99;
			}else {
				if(flag2->answer){
					d_solar = solar_day_3d(d_lat,d_doy,d_tsw,d_slope,d_aspect);
				}else {
					d_solar = solar_day(d_lat, d_doy, d_tsw );
				}
				d_evapfr = evapfr_senay( tempk_max, tempk_min, d_tempk);
				if(result2){
					((DCELL *) outrast2)[col] = d_evapfr;
				}
				d_etpotd = et_pot_day(d_albedo,d_solar,d_tempk,d_tsw,roh_w);
				d = d_etpotd * d_evapfr;
				((DCELL *) outrast1)[col] = d;
			}
		}
		if (G_put_raster_row (outfd1, outrast1, data_type_output) < 0)
			G_fatal_error(_("Cannot write to output raster file"));
		if(result2){
			if (G_put_raster_row (outfd2, outrast2, data_type_output) < 0)
				G_fatal_error(_("Cannot write to output raster file"));
		}
	}

	G_free (inrast_albedo);
	G_free (inrast_tempk);
	G_free (inrast_dem);
	G_free (inrast_lat);
	G_free (inrast_doy);
	G_free (inrast_tsw);
	G_close_cell (infd_albedo);
	G_close_cell (infd_tempk);
	G_close_cell (infd_dem);
	G_close_cell (infd_lat);
	G_close_cell (infd_doy);
	G_close_cell (infd_tsw);
	
	G_free (outrast1);
	G_close_cell (outfd1);
	if (result2){
		G_free (outrast2);
		G_close_cell (outfd2);
		G_short_history(result2, "raster", &history);
		G_command_history(&history);
		G_write_history(result2,&history);
	}

	G_short_history(result1, "raster", &history);
	G_command_history(&history);
	G_write_history(result1,&history);

	exit(EXIT_SUCCESS);
}

