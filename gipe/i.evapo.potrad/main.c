/****************************************************************************
 *
 * MODULE:       i.evapo.potrad
 * AUTHOR(S):    Yann Chemin - ychemin@gmail.com
 * PURPOSE:      Creates a map of potential evapotranspiration following
 *               the condition that all net radiation becomes ET
 *               (thus it can be called a "radiative ET pot")
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

double solar_day(double lat, double doy, double tsw );
double solar_day_3d(double lat, double doy, double tsw, double slope, double aspect);
double r_net_day( double bbalb, double solar, double tsw );
double et_pot_day( double bbalb, double solar, double tempk, double tsw, double roh_w );



int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	struct GModule *module;
	struct Option *input1, *input2, *input3, *input4;
	struct Option *input5, *input6, *input7, *input8;
	struct Option *output1, *output2;
	
	struct Flag *flag1, *flag2, *flag3;	
	struct History history; //metadata
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   // input raster name
	char *result1,*result2; //output raster name
	//File Descriptors
	int infd_albedo, infd_tempk, infd_lat, infd_doy, infd_tsw;
	int infd_slope, infd_aspect;
	int outfd1, outfd2;
	
	char *albedo,*tempk,*lat,*doy,*tsw,*slope,*aspect;
	double roh_w;
	int i=0,j=0;
	
	void *inrast_albedo, *inrast_tempk, *inrast_lat;
	void *inrast_doy, *inrast_tsw;
	void *inrast_slope, *inrast_aspect;

	unsigned char *outrast1, *outrast2;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_albedo;
	RASTER_MAP_TYPE data_type_tempk;
	RASTER_MAP_TYPE data_type_lat;
	RASTER_MAP_TYPE data_type_doy;
	RASTER_MAP_TYPE data_type_tsw;
	RASTER_MAP_TYPE data_type_slope;
	RASTER_MAP_TYPE data_type_aspect;
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("Potential ET, evapotranspiration, SEBAL");
	module->description = _("Potential evapotranspiration, radiative method after Bastiaanssen (1995)");

	/* Define the different options */
	input1 = G_define_option() ;
	input1->key	   = _("albedo");
	input1->type       = TYPE_STRING;
	input1->required   = YES;
	input1->gisprompt  =_("old,cell,raster") ;
	input1->description=_("Name of the Albedo map [0.0-1.0]");
	input1->answer     =_("albedo");

	input2 = G_define_option() ;
	input2->key        =_("tempk");
	input2->type       = TYPE_STRING;
	input2->required   = YES;
	input2->gisprompt  =_("old,cell,raster");
	input2->description=_("Name of the temperature map [Degree Kelvin]");
	input2->answer     =_("tempk");

	input3 = G_define_option() ;
	input3->key        =_("lat");
	input3->type       = TYPE_STRING;
	input3->required   = YES;
	input3->gisprompt  =_("old,cell,raster");
	input3->description=_("Name of the degree latitude map [dd.ddd]");
	input3->answer     =_("lat");

	input4 = G_define_option() ;
	input4->key        =_("doy");
	input4->type       = TYPE_STRING;
	input4->required   = YES;
	input4->gisprompt  =_("old,cell,raster");
	input4->description=_("Name of the Day of Year map [0.0-366.0]");
	input4->answer     =_("doy");

	input5 = G_define_option() ;
	input5->key        =_("tsw");
	input5->type       = TYPE_STRING;
	input5->required   = YES;
	input5->gisprompt  =_("old,cell,raster");
	input5->description=_("Name of the single-way transmissivity map [0.0-1.0]");
	input5->answer     =_("tsw");

	input6 = G_define_option() ;
	input6->key        =_("roh_w");
	input6->type       = TYPE_DOUBLE;
	input6->required   = YES;
	input6->gisprompt  =_("value, parameter");
	input6->description=_("Value of the density of fresh water ~[1000-1020]");
	input6->answer     =_("1010.0");

	input7 = G_define_option() ;
	input7->key        =_("slope");
	input7->type       = TYPE_STRING;
	input7->required   = NO;
	input7->gisprompt  =_("old,cell,raster");
	input7->description=_("Name of the Slope map ~[0-90]");
	input7->answer     =_("slope");

	input8 = G_define_option() ;
	input8->key        =_("aspect");
	input8->type       = TYPE_STRING;
	input8->required   = NO;
	input8->gisprompt  =_("old,cell,raster");
	input8->description=_("Name of the Aspect map ~[0-360]");
	input8->answer     =_("aspect");


	output1 = G_define_option() ;
	output1->key        =_("etpot");
	output1->type       = TYPE_STRING;
	output1->required   = YES;
	output1->gisprompt  =_("new,cell,raster");
	output1->description=_("Name of the output Potential ET layer");
	output1->answer     =_("etpot");

	output2 = G_define_option() ;
	output2->key        =_("rnetd");
	output2->type       = TYPE_STRING;
	output2->required   = NO;
	output2->gisprompt  =_("new,cell,raster");
	output2->description=_("Name of the output Diurnal Net Radiation layer");

	flag1 = G_define_flag();
	flag1->key = 'r';
	flag1->description = _("Output Diurnal Net Radiation (for r.eb.eta)");
	
	flag2 = G_define_flag();
	flag2->key = 'd';
	flag2->description = _("Slope/Aspect correction");

	flag3 = G_define_flag();
	flag3->key = 'q';
	flag3->description = _("Quiet");
	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	albedo	 	= input1->answer;
	tempk	 	= input2->answer;
	lat		= input3->answer;
	doy	 	= input4->answer;
	tsw	 	= input5->answer;
	roh_w	 	= atof(input6->answer);
	slope	 	= input7->answer;
	aspect	 	= input8->answer;
	
	result1  = output1->answer;
	result2  = output2->answer;
	verbose = (!flag3->answer);
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
		if(verbose)
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
			}else if(flag2->answer){
				if(G_is_d_null_value(&d_slope)){
					((DCELL *) outrast1)[col] = -999.99;
					if (result2)
					((DCELL *) outrast2)[col] = -999.99;
				}else if(G_is_d_null_value(&d_aspect)){
					((DCELL *) outrast1)[col] = -999.99;
					if (result2)
					((DCELL *) outrast2)[col] = -999.99;
				}
			}else {
				if(flag2->answer){
					d_solar = solar_day_3d(d_lat,d_doy,d_tsw,d_slope,d_aspect);
				}else {
					d_solar = solar_day(d_lat, d_doy, d_tsw );
				}
				if(result2){
					d_rnetd = r_net_day(d_albedo,d_solar,d_tsw );
					((DCELL *) outrast2)[col] = d_rnetd;
				}
				d = et_pot_day(d_albedo,d_solar,d_tempk,d_tsw,roh_w);
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
	G_free (inrast_lat);
	G_free (inrast_doy);
	G_free (inrast_tsw);
	G_close_cell (infd_albedo);
	G_close_cell (infd_tempk);
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

