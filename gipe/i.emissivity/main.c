/****************************************************************************
 *
 * MODULE:       r.emissivity
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the emissivity from NDVI (empirical)
 *                as seen in Caselles and Colles (1997). 
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
#include <grass/gis.h>
#include <grass/glocale.h>


double emissivity_generic( double ndvi );

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	struct GModule *module;
	struct Option *input1, *output1;
	
	struct Flag *flag1, *flag2;	
	struct History history; //metadata
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   // input raster name
	char *result1; //output raster name
	//File Descriptors
	int infd_ndvi;
	int outfd1;
	
	char *ndvi;
	char *emissivity;	
	int i=0,j=0;
	
	void *inrast_ndvi;
	unsigned char *outrast1;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_ndvi;
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("emissivity, land flux, energy balance");
	module->description = _("Emissivity from NDVI, generic method for spares land.");

	/* Define the different options */
	input1 = G_define_option() ;
	input1->key	   = _("ndvi");
	input1->type       = TYPE_STRING;
	input1->required   = YES;
	input1->gisprompt  =_("old,cell,raster") ;
	input1->description=_("Name of the NDVI map [-]");
	input1->answer     =_("ndvi");

	output1 = G_define_option() ;
	output1->key        =_("emissivity");
	output1->type       = TYPE_STRING;
	output1->required   = YES;
	output1->gisprompt  =_("new,cell,raster");
	output1->description=_("Name of the output emissivity layer");
	output1->answer     =_("e0");

	
	flag1 = G_define_flag();
	flag1->key = 'q';
	flag1->description = _("Quiet");

	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	ndvi	 	= input1->answer;
		
	result1  	= output1->answer;
	verbose 	= (!flag1->answer);
	/***************************************************/
	mapset = G_find_cell2(ndvi, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), ndvi);
	}
	data_type_ndvi = G_raster_map_type(ndvi,mapset);
	if ( (infd_ndvi = G_open_cell_old (ndvi,mapset)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), ndvi);
	if (G_get_cellhd (ndvi, mapset, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s])"), ndvi);
	inrast_ndvi = G_allocate_raster_buf(data_type_ndvi);
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
		DCELL d_ndvi;
		if(verbose)
			G_percent(row,nrows,2);
//		printf("row = %i/%i\n",row,nrows);
		/* read soil input maps */	
		if(G_get_raster_row(infd_ndvi,inrast_ndvi,row,data_type_ndvi)<0)
			G_fatal_error(_("Could not read from <%s>"),ndvi);
		/*process the data */
		for (col=0; col < ncols; col++)
		{
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
			if(G_is_d_null_value(&d_ndvi)){
				((DCELL *) outrast1)[col] = -999.99;
			} else {
				/****************************/
				/* calculate emissivity	    */
				d = emissivity_generic(d_ndvi);
				
				((DCELL *) outrast1)[col] = d;
			}
		}
		if (G_put_raster_row (outfd1, outrast1, data_type_output) < 0)
			G_fatal_error(_("Cannot write to output raster file"));
	}

	G_free (inrast_ndvi);
	G_close_cell (infd_ndvi);
	
	G_free (outrast1);
	G_close_cell (outfd1);
	
	G_short_history(result1, "raster", &history);
	G_command_history(&history);
	G_write_history(result1,&history);

	exit(EXIT_SUCCESS);
}

