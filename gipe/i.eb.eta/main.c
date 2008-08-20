/****************************************************************************
 *
 * MODULE:       i.eb.eta
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the actual evapotranspiration for diurnal period
 *               as seen in Bastiaanssen (1995) 
 *
 * COPYRIGHT:    (C) 2002-2007 by the GRASS Development Team
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

double et_a(double r_net_day, double evap_fr, double tempk);

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; /*region+header info*/
	char *mapset; /*mapset name*/
	int nrows, ncols;
	int row,col;

	struct GModule *module;
	struct Option *input1, *input2, *input3, *output1;
	
	struct Flag *flag1;	
	struct History history; /*metadata*/
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   /*input raster name*/
	char *result1; /*output raster name*/
	/*File Descriptors*/
	int infd_rnetday, infd_evapfr, infd_tempk;
	int outfd1;
	
	char *rnetday,*evapfr,*tempk;
	int i=0,j=0;
	
	void *inrast_rnetday, *inrast_evapfr, *inrast_tempk;
	DCELL *outrast1;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_rnetday;
	RASTER_MAP_TYPE data_type_evapfr;
	RASTER_MAP_TYPE data_type_tempk;
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("actual evapotranspiration, energy balance, SEBAL");
	module->description = _("actual evapotranspiration for diurnal period (Bastiaanssen, 1995)");

	/* Define the different options */
	input1 = G_define_standard_option(G_OPT_R_INPUT) ;
	input1->key	   = _("rnetday");
	input1->description=_("Name of the diurnal Net Radiation map [W/m2]");
	input1->answer     =_("rnetday");

	input2 = G_define_standard_option(G_OPT_R_INPUT) ;
	input2->key        =_("evapfr");
	input2->description=_("Name of the evaporative fraction map [-]");
	input2->answer     =_("evapfr");

	input3 = G_define_standard_option(G_OPT_R_INPUT) ;
	input3->key        =_("tempk");
	input3->description=_("Name of the surface skin temperature [K]");
	input3->answer     =_("tempk");

	output1 = G_define_standard_option(G_OPT_R_OUTPUT) ;
	output1->key        =_("eta");
	output1->description=_("Name of the output actual diurnal evapotranspiration layer");
	output1->answer     =_("eta");
	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	rnetday	 	= input1->answer;
	evapfr	 	= input2->answer;
	tempk		= input3->answer;
	
	result1  = output1->answer;
	/***************************************************/
	mapset = G_find_cell2(rnetday, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), rnetday);
	}
	data_type_rnetday = G_raster_map_type(rnetday,mapset);
	if ( (infd_rnetday = G_open_cell_old (rnetday,mapset)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), rnetday);
	if (G_get_cellhd (rnetday, mapset, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s])"), rnetday);
	inrast_rnetday = G_allocate_raster_buf(data_type_rnetday);
	/***************************************************/
	mapset = G_find_cell2 (evapfr, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"),evapfr);
	}
	data_type_evapfr = G_raster_map_type(evapfr,mapset);
	if ( (infd_evapfr = G_open_cell_old (evapfr,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), evapfr);
	if (G_get_cellhd (evapfr, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), evapfr);
	inrast_evapfr = G_allocate_raster_buf(data_type_evapfr);
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
	G_debug(3, "number of rows %d",cellhd.rows);
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast1 = G_allocate_raster_buf(data_type_output);
	/* Create New raster files */
	if ( (outfd1 = G_open_raster_new (result1,data_type_output)) < 0)
		G_fatal_error(_("Could not open <%s>"),result1);
	/* Process pixels */
	for (row = 0; row < nrows; row++)
	{
		DCELL d;
		DCELL d_rnetday;
		DCELL d_evapfr;
		DCELL d_tempk;
		G_percent(row,nrows,2);
		/* read input maps */	
		if(G_get_raster_row(infd_rnetday,inrast_rnetday,row,data_type_rnetday)<0)
			G_fatal_error(_("Could not read from <%s>"),rnetday);
		if(G_get_raster_row(infd_evapfr,inrast_evapfr,row,data_type_evapfr)<0)
			G_fatal_error(_("Could not read from <%s>"),evapfr);
		if(G_get_raster_row(infd_tempk,inrast_tempk,row,data_type_tempk)<0)
			G_fatal_error(_("Could not read from <%s>"),tempk);
		/*process the data */
		for (col=0; col < ncols; col++)
		{
			switch(data_type_rnetday){
				case CELL_TYPE:
					d_rnetday = (double) ((CELL *) inrast_rnetday)[col];
					break;
				case FCELL_TYPE:
					d_rnetday = (double) ((FCELL *) inrast_rnetday)[col];
					break;
				case DCELL_TYPE:
					d_rnetday = ((DCELL *) inrast_rnetday)[col];
					break;
			}
			switch(data_type_evapfr){
				case CELL_TYPE:
					d_evapfr = (double) ((CELL *) inrast_evapfr)[col];
					break;
				case FCELL_TYPE:
					d_evapfr = (double) ((FCELL *) inrast_evapfr)[col];
					break;
				case DCELL_TYPE:
					d_evapfr = ((DCELL *) inrast_evapfr)[col];
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
			if(G_is_d_null_value(&d_rnetday)||
			G_is_d_null_value(&d_evapfr)||
			G_is_d_null_value(&d_tempk)){
				G_set_d_null_value(&outrast1[col],1);
			}else {
				/************************************/
				/* calculate soil heat flux	    */
				d = et_a(d_rnetday,d_evapfr,d_tempk);
				outrast1[col] = d;
			}
		}
		if (G_put_raster_row (outfd1, outrast1, data_type_output) < 0)
			G_fatal_error(_("Cannot write to output raster file"));
	}

	G_free (inrast_rnetday);
	G_free (inrast_evapfr);
	G_free (inrast_tempk);
	G_close_cell (infd_rnetday);
	G_close_cell (infd_evapfr);
	G_close_cell (infd_tempk);
	
	G_free (outrast1);
	G_close_cell (outfd1);

	G_short_history(result1, "raster", &history);
	G_command_history(&history);
	G_write_history(result1,&history);

	exit(EXIT_SUCCESS);
}

