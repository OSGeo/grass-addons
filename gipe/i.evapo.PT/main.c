/*****************************************************************************
*
* MODULE:	r.evapo.PT
* AUTHOR:	Yann Chemin (2007)
* 		yann.chemin_AT_gmail.com 
*
* PURPOSE:	To estimate the daily evapotranspiration by means
*		of Prestley and Taylor method (1972).
*
* COPYRIGHT:	(C) 2007 by the GRASS Development Team
*
*		This program is free software under the GNU General Public
*		Licence (>=2). Read the file COPYING that comes with GRASS
*		for details.
*
***************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>


//proto Delta_pt and Ghamma_pt
double pt_delta(double tempka);
double pt_ghamma(double tempka, double p_atm);

//proto ET
double pt_daily_et(double alpha_pt, double delta_pt, double ghamma_pt, double rnet, double g0 );


int main(int argc, char *argv[])
{	
	/* buffer for input-output rasters */
	void *inrast_TEMPKA,*inrast_PATM,*inrast_RNET,*inrast_G0;
	
	unsigned char *outrast;
	
	/* pointers to input-output raster files */
	int infd_TEMPKA,infd_PATM,infd_RNET,infd_G0;
	
	int outfd;

	/* mapsets for input raster files */
	char *mapset_TEMPKA,*mapset_PATM,*mapset_RNET,*mapset_G0;

	/* names of input-output raster files */
	char *RNET, *TEMPKA, *PATM, *G0;
	
	char *ETa; 

	/* input-output cell values */
	DCELL d_tempka,d_pt_patm,d_rnet,d_g0;
	DCELL d_pt_alpha, d_pt_delta, d_pt_ghamma, d_daily_et;


	/* region informations and handler */
	struct Cell_head cellhd;
	int nrows, ncols;
	int row, col;

	/* parser stuctures definition */
	struct GModule *module;
	struct Option *input_RNET,*input_TEMPKA, *input_PATM, *input_G0, *input_PT;
	struct Option *output;
	struct Flag *flag1, *zero;
	struct Colors color;
	struct History history;

	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_tempka;
	RASTER_MAP_TYPE data_type_patm;
	RASTER_MAP_TYPE data_type_rnet;
	RASTER_MAP_TYPE data_type_g0;
	RASTER_MAP_TYPE data_type_eta;

	/* Initialize the GIS calls */
	G_gisinit(argv[0]);
	
	module = G_define_module();
	module->description =
		_("Evapotranspiration Calculation "
		"Prestley and Taylor formulation, 1972.");
	
	/* Define different options */
	input_RNET = G_define_option();
	input_RNET->key			= "RNET";
	input_RNET->key_desc		= "[W/m2]";
	input_RNET->type 		= TYPE_STRING;
	input_RNET->required 		= YES;
	input_RNET->gisprompt 		= "old,cell,raster";
	input_RNET->description 	= _("Name of Net Radiation raster map");
	
	input_G0 = G_define_option();
	input_G0->key			= "G0";
	input_G0->key_desc		= "[W/m2]";
	input_G0->type			= TYPE_STRING;
	input_G0->required		= YES;
	input_G0->gisprompt		= "old,cell,raster";
	input_G0->description		= _("Name of Soil Heat Flux raster map");
		
	input_TEMPKA = G_define_option();
	input_TEMPKA->key		= "TEMPKA";
	input_TEMPKA->key_desc		= "[K]";
	input_TEMPKA->type		= TYPE_STRING;
	input_TEMPKA->required		= YES;
	input_TEMPKA->gisprompt		= "old,cell,raster";
	input_TEMPKA->description	= _("Name of air temperature raster map");
		
	input_PATM = G_define_option();
	input_PATM->key			= "PATM";
	input_PATM->key_desc		= "[millibars]";
	input_PATM->type		= TYPE_STRING;
	input_PATM->required		= YES;
	input_PATM->gisprompt		= "old,cell,raster";
	input_PATM->description		= _("Name of Atmospheric Pressure raster map");
	
	input_PT = G_define_option();
	input_PT->key			= "PT";
	input_PT->key_desc		= "[-]";
	input_PT->type			= TYPE_DOUBLE;
	input_PT->required		= YES;
	input_PT->gisprompt		= "old,cell,raster";
	input_PT->description		= _("Prestley-Taylor Coefficient");
	input_PT->answer		= "1.26";
	
	output = G_define_option() ;
	output->key			= "output";
	output->key_desc		= "[mm/d]";
	output->type			= TYPE_STRING;
	output->required		= YES;
	output->gisprompt		= "new,cell,raster" ;
	output->description		= _("Name of output Evapotranspiration layer");
	
	/* Define the different flags */
	flag1 = G_define_flag() ;
	flag1->key			= 'q' ;
	flag1->description		= _("quiet");
	
	zero = G_define_flag() ;
	zero->key			= 'z' ;
	zero->description		= _("set negative ETa to zero");
	
	if (G_parser(argc, argv))
		exit(EXIT_FAILURE);
	
	/* get entered parameters */
	RNET	= input_RNET->answer;
	TEMPKA	= input_TEMPKA->answer;
	PATM	= input_PATM->answer;
	G0	= input_G0->answer;
	d_pt_alpha = atof(input_PT->answer);
	
	ETa	= output->answer;
	
	/* find maps in mapset */
	mapset_RNET = G_find_cell2 (RNET, "");
	if (mapset_RNET == NULL)
	        G_fatal_error (_("cell file [%s] not found"), RNET);
	mapset_TEMPKA = G_find_cell2 (TEMPKA, "");
	if (mapset_TEMPKA == NULL)
	        G_fatal_error (_("cell file [%s] not found"), TEMPKA);
	mapset_PATM = G_find_cell2 (PATM, "");
	if (mapset_PATM == NULL)
	        G_fatal_error (_("cell file [%s] not found"), PATM);
	mapset_G0 = G_find_cell2 (G0, "");
	if (mapset_G0 == NULL)
	        G_fatal_error (_("cell file [%s] not found"), G0);
	
	/* check legal output name */ 
	if (G_legal_filename (ETa) < 0)
			G_fatal_error (_("[%s] is an illegal name"), ETa);
		
	/* determine the input map type (CELL/FCELL/DCELL) */
	data_type_rnet = G_raster_map_type(RNET,mapset_RNET);
	data_type_tempka = G_raster_map_type(TEMPKA,mapset_TEMPKA);
	data_type_patm = G_raster_map_type(PATM,mapset_PATM);
	data_type_g0 = G_raster_map_type(G0,mapset_G0);
	
	/* open pointers to input raster files */
	if ( (infd_RNET = G_open_cell_old (RNET, mapset_RNET)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), RNET);
	if ( (infd_TEMPKA = G_open_cell_old (TEMPKA, mapset_TEMPKA)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), TEMPKA);
	if ( (infd_PATM = G_open_cell_old (PATM, mapset_PATM)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), PATM);
	if ( (infd_G0 = G_open_cell_old (G0, mapset_G0)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), G0);

	/* read headers of raster files */
	if (G_get_cellhd (RNET, mapset_RNET, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), RNET);
	if (G_get_cellhd (TEMPKA, mapset_TEMPKA, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), TEMPKA);
	if (G_get_cellhd (PATM, mapset_PATM, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), PATM);
	if (G_get_cellhd (G0, mapset_G0, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), G0);

	/* Allocate input buffer */
	inrast_RNET  = G_allocate_raster_buf(data_type_rnet);
	inrast_TEMPKA = G_allocate_raster_buf(data_type_tempka);
	inrast_PATM = G_allocate_raster_buf(data_type_patm);
	inrast_G0 = G_allocate_raster_buf(data_type_g0);
	
	/* get rows and columns number of the current region */
	nrows = G_window_rows();
	ncols = G_window_cols();

	/* allocate output buffer */
	outrast = G_allocate_raster_buf(data_type_output);

	/* open pointers to output raster files */
	if ( (outfd = G_open_raster_new (ETa,data_type_output)) < 0)
		G_fatal_error (_("Could not open <%s>"),ETa);
	

	/* start the loop through cells */
	for (row = 0; row < nrows; row++)
	{
				
		/* read input raster row into line buffer*/	
		if (G_get_raster_row (infd_RNET, inrast_RNET, row,data_type_rnet) < 0)
			G_fatal_error (_("Could not read from <%s>"),RNET);
		if (G_get_raster_row (infd_TEMPKA, inrast_TEMPKA, row,data_type_tempka) < 0)
			G_fatal_error (_("Could not read from <%s>"),TEMPKA);
		if (G_get_raster_row (infd_PATM, inrast_PATM, row,data_type_patm) < 0)
			G_fatal_error (_("Could not read from <%s>"),PATM);
		if (G_get_raster_row (infd_G0, inrast_G0, row,data_type_g0) < 0)
			G_fatal_error (_("Could not read from <%s>"),G0);
		
		for (col=0; col < ncols; col++)
		{
			/* read current cell from line buffer */
			switch(data_type_rnet){
				case CELL_TYPE:
					d_rnet	= (double) ((CELL *) inrast_RNET)[col];
					break;
				case FCELL_TYPE:
					d_rnet	= (double) ((FCELL *) inrast_RNET)[col];
					break;
				case DCELL_TYPE:
					d_rnet	= ((DCELL *) inrast_RNET)[col];
					break;
			}
			switch(data_type_tempka){
				case CELL_TYPE:
					d_tempka = (double) ((CELL *) inrast_TEMPKA)[col];
					break;
				case FCELL_TYPE:
					d_tempka = (double) ((FCELL *) inrast_TEMPKA)[col];
					break;
				case DCELL_TYPE:
					d_tempka = ((DCELL *) inrast_TEMPKA)[col];
					break;
			}
			switch(data_type_patm){
				case CELL_TYPE:
					d_pt_patm = (double) ((CELL *) inrast_PATM)[col];
					break;
				case FCELL_TYPE:
					d_pt_patm = (double) ((FCELL *) inrast_PATM)[col];
					break;
				case DCELL_TYPE:
					d_pt_patm = ((DCELL *) inrast_PATM)[col];
					break;
			}
			switch(data_type_g0){
				case CELL_TYPE:
					d_g0	= (double) ((CELL *) inrast_G0)[col];
					break;
				case FCELL_TYPE:
					d_g0	= (double) ((FCELL *) inrast_G0)[col];
					break;
				case DCELL_TYPE:
					d_g0	= ((DCELL *) inrast_G0)[col];
					break;
			}

			//Delta_pt and Ghamma_pt
			d_pt_delta = pt_delta( d_tempka);
			d_pt_ghamma = pt_ghamma(d_tempka, d_pt_patm);
			
			//Calculate ET
			d_daily_et	= pt_daily_et( d_pt_alpha, d_pt_delta, d_pt_ghamma, d_rnet, d_g0 );
			if (zero->answer && d_daily_et<0)
				d_daily_et=0.0;
			
			/* write calculated ETP to output line buffer */
			((DCELL *) outrast)[col] = d_daily_et;
		}
		
		if (!flag1->answer) G_percent(row, nrows, 2);

		/* write output line buffer to output raster file */
		if (G_put_raster_row (outfd, outrast, data_type_output) < 0)
			G_fatal_error (_("Cannot write to <%s>"), ETa);
			
	}
	/* free buffers and close input maps */

	G_free(inrast_RNET);
	G_free(inrast_TEMPKA);
	G_free(inrast_PATM);
	G_free(inrast_G0);
	G_close_cell (infd_RNET);
	G_close_cell (infd_TEMPKA);
	G_close_cell (infd_PATM);
	G_close_cell (infd_G0);
	
	/* generate color table between -20 and 20 */
	G_make_rainbow_colors(&color, -20, 20);
	G_write_colors(ETa,G_mapset(),&color);

	G_short_history(ETa,"raster", &history);
	G_command_history(&history);
	G_write_history(ETa, &history);

	/* free buffers and close output map */
	G_free(outrast);
	G_close_cell (outfd);

	return (0);
}

