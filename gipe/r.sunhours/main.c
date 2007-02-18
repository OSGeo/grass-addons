/****************************************************************************
 *
 * MODULE:       r.sunhours
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the sunshine hours (also called daytime period)
 * 		 under a perfect clear sky condition.
 * 		 Called generally "N" in meteorology. 
 *
 * COPYRIGHT:    (C) 2007 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#define PI 3.1415927

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	struct GModule *module;
	struct Option *input1, *input2, *output1;
	
	struct Flag *flag1;	
	struct History history; //metadata
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   // input raster name
	char *result1; //output raster name
	//File Descriptors
	int infd_lat, infd_doy;
	int outfd1;
	
	char *lat, *doy;
	int i=0,j=0;

	void *inrast_lat, *inrast_doy;
	unsigned char *outrast1;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_lat;
	RASTER_MAP_TYPE data_type_doy;
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("sunshine, hours, daytime");
	module->description = _("creates a sunshine hours map");

	/* Define the different options */
	input1 = G_define_option() ;
	input1->key	   = _("doy");
	input1->type       = TYPE_STRING;
	input1->required   = YES;
	input1->gisprompt  =_("old,cell,raster") ;
	input1->description=_("Name of the latitude input map");
	input1->answer     =_("doy");

	input2 = G_define_option() ;
	input2->key	   = _("lat");
	input2->type       = TYPE_STRING;
	input2->required   = YES;
	input2->gisprompt  =_("old,cell,raster") ;
	input2->description=_("Name of the latitude input map");
	input2->answer     =_("latitude");

	output1 = G_define_option() ;
	output1->key        =_("sunh");
	output1->type       = TYPE_STRING;
	output1->required   = YES;
	output1->gisprompt  =_("new,cell,raster");
	output1->description=_("Name of the output sunshine hours layer");
	output1->answer     =_("sunh");

	
	flag1 = G_define_flag();
	flag1->key = 'q';
	flag1->description = _("Quiet");

	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	lat	 	= input1->answer;
	doy	 	= input2->answer;
		
	result1  = output1->answer;
	verbose = (!flag1->answer);
	/***************************************************/
	mapset = G_find_cell2(doy, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), doy);
	}
	data_type_doy = G_raster_map_type(doy,mapset);
	if ( (infd_doy = G_open_cell_old (doy,mapset)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), doy);
	if (G_get_cellhd (doy, mapset, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s])"), doy);
	inrast_doy = G_allocate_raster_buf(data_type_doy);
	/***************************************************/
	mapset = G_find_cell2(lat, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), lat);
	}
	data_type_lat = G_raster_map_type(lat,mapset);
	if ( (infd_lat = G_open_cell_old (lat,mapset)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), lat);
	if (G_get_cellhd (lat, mapset, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s])"), lat);
	inrast_lat = G_allocate_raster_buf(data_type_lat);
	/***************************************************/
	G_debug(3, "number of rows %d",cellhd.rows);
	G_debug(3, "number of rows %d",cellhd.rows);

	nrows = G_window_rows();
	ncols = G_window_cols();
	
	outrast1 = G_allocate_raster_buf(data_type_output);
	if ( (outfd1 = G_open_raster_new (result1,data_type_output)) < 0)
		G_fatal_error(_("Could not open <%s>"),result1);
	for (row = 0; row < nrows; row++)
	{
		DCELL d;
		DCELL d_da;
		DCELL d_E0;
		DCELL d_delta;
		DCELL d_Ws;
		DCELL d_N;
		DCELL d_lat;
		DCELL d_doy;
		if(verbose)
			G_percent(row,nrows,2);
		if(G_get_raster_row(infd_doy,inrast_doy,row,data_type_doy)<0)
			G_fatal_error(_("Could not read from <%s>"),doy);
		if(G_get_raster_row(infd_lat,inrast_lat,row,data_type_lat)<0)
			G_fatal_error(_("Could not read from <%s>"),lat);


		for (col=0; col < ncols; col++)
		{
			
			switch(data_type_doy){
				case CELL_TYPE:
					d_doy = (double) ((CELL *) inrast_doy)[col];
					break;
				case FCELL_TYPE:
					d_doy = (double) ((FCELL *) inrast_doy)[col];
					break;
				case DCELL_TYPE:
					d_doy	= ((DCELL *) inrast_doy)[col];
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
					d_lat	= ((DCELL *) inrast_lat)[col];
					break;
			}
			d_da = 2 * PI * ( d_doy - 1 ) / 365.0;
			d_E0 = 1.00011+0.034221*cos(d_da)+0.00128*sin(d_da)+0.000719*cos(2*d_da)+0.000077*sin(2*d_da);
			d_delta = 0.006918-0.399912*cos(d_da)+0.070257*sin(d_da)-0.006758*cos(2*d_da)+0.000907*sin(2*d_da)-0.002697*cos(3*d_da)+0.00148*sin(3*d_da);
			d_Ws = 1.0/(cos(-tan(d_lat)*tan(d_delta)));
			d_N = ( 360.0 / ( 15.0 * PI ) ) * d_Ws;
			((DCELL *) outrast1)[col] = d_N;
		}
		if (G_put_raster_row (outfd1, outrast1, data_type_output) < 0)
			G_fatal_error(_("Cannot write to output raster file"));
	}

	G_free (inrast_lat);
	G_free (inrast_doy);
	G_close_cell (infd_lat);
	G_close_cell (infd_doy);
	
	G_free (outrast1);
	G_close_cell (outfd1);
	
	G_short_history(result1, "raster", &history);
	G_command_history(&history);
	G_write_history(result1,&history);

	exit(EXIT_SUCCESS);
}

