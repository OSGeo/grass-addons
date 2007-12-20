/****************************************************************************
 *
 * MODULE:       i.eb.h_SEBAL95
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates sensible heat flux by SEBAL iteration
 *               Delta T will be reassessed in the iterations !
 *               This has been seen in Bastiaanssen (1995).
 *
 * COPYRIGHT:    (C) 2002-2007 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 * CHANGELOG:	
 *
 *****************************************************************************/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <grass/gis.h>
#include <math.h>
#include "functions.h"
#include <grass/glocale.h>

int main(int argc, char *argv[])
{	
	struct Cell_head cellhd;
	
	/* buffer for in out raster */
	DCELL *inrast_T,*inrast_ndvi,*inrast_u2,*inrast_DEM,*inrast_Rn,*inrast_g0,*outrast;
	unsigned char *ETa;
	
	int nrows, ncols;
	int row, col;
	int row_wet, col_wet;
	int row_dry, col_dry;
	int infd_T,infd_ndvi,infd_u2,infd_DEM,infd_Rn,infd_g0;
	int outfd;
	
	char *mapset_T,*mapset_ndvi,*mapset_u2,*mapset_DEM,*mapset_Rn,*mapset_g0;
	char *T, *ndvi, *u2, *DEM, *Rn, *g0; 
	
	int d_night;
	
        struct History history;
	struct GModule *module;
	struct Option *input_T, *input_ndvi, *input_u2, *input_DEM, *input_Rn, *input_g0, *output;
	struct Option *input_row_wet, *input_col_wet, *input_row_dry, *input_col_dry;
	struct Flag *flag1, *day, *zero;
	
	
	G_gisinit(argv[0]);
	
	module = G_define_module();
	module->description = _("Sensible Heat Flux iteration from SEBAL 95");
	
	/* Define different options */
	input_T = G_define_option();
	input_T->key	= "T";
	input_T->type = TYPE_STRING;
	input_T->required = YES;
	input_T->gisprompt = "old,cell,raster";
	input_T->description = _("Name of Surface Skin Temperature input map [K]");
		
	input_u2 = G_define_option();
	input_u2->key	= "u2m";
	input_u2->type = TYPE_STRING;
	input_u2->required = YES;
	input_u2->gisprompt = "old,cell,raster";
	input_u2->description = _("Name of Wind Speed input map [m/s]");
		
	input_DEM = G_define_option();
	input_DEM->key	= "DEM";
	input_DEM->type = TYPE_STRING;
	input_DEM->required = YES;
	input_DEM->gisprompt = "old,cell,raster";
	input_DEM->description = _("Name of DEM input map [m a.s.l.]");
	
	input_ndvi = G_define_option();
	input_ndvi->key	= "ndvi";
	input_ndvi->type = TYPE_STRING;
	input_ndvi->required = YES;
	input_ndvi->gisprompt = "old,cell,raster";
	input_ndvi->description = _("Name of NDVI input map [%]");
	
	input_Rn = G_define_option();
	input_Rn->key	= "Rn";
	input_Rn->type = TYPE_STRING;
	input_Rn->required = YES;
	input_Rn->gisprompt = "old,cell,raster";
	input_Rn->description = _("Name of Diurnal Net Solar Radiation input map [W/m2]");
	
	input_g0 = G_define_option();
	input_g0->key	= "g0";
	input_g0->type = TYPE_STRING;
	input_g0->required = YES;
	input_g0->gisprompt = "old,cell,raster";
	input_g0->description = _("Name of Soil Heat Flux input map [W/m2]");	
	
	input_row_wet 			= G_define_option();
	input_row_wet->key		= "row_wet";
	input_row_wet->type 		= TYPE_INTEGER;
	input_row_wet->required 	= YES;
	input_row_wet->gisprompt 	= "old,value";
	input_row_wet->description 	= _("Row value of the wet pixel");	
	
	input_col_wet 			= G_define_option();
	input_col_wet->key		= "col_wet";
	input_col_wet->type 		= TYPE_INTEGER;
	input_col_wet->required 	= YES;
	input_col_wet->gisprompt 	= "old,value";
	input_col_wet->description 	= _("Column value of the wet pixel");	
	
	input_row_dry 			= G_define_option();
	input_row_dry->key		= "row_dry";
	input_row_dry->type 		= TYPE_INTEGER;
	input_row_dry->required 	= YES;
	input_row_dry->gisprompt 	= "old,value";
	input_row_dry->description 	= _("Row value of the dry pixel");	
	
	input_col_dry 			= G_define_option();
	input_col_dry->key		= "col_dry";
	input_col_dry->type 		= TYPE_INTEGER;
	input_col_dry->required 	= YES;
	input_col_dry->gisprompt 	= "old,value";
	input_col_dry->description 	= _("Column value of the dry pixel");	

	output = G_define_option() ;
	output->key        = "ETa";
	output->type       = TYPE_STRING;
	output->required   = YES;
	output->gisprompt  = "new,cell,raster" ;
	output->description= _("Name of output Actual Evapotranspiration layer [mm/d]");
	
	/* Define the different flags */
	//flag1 = G_define_flag() ;
	//flag1->key         = 'q' ;
	//flag1->description = "Quiet" ;
	
	zero = G_define_flag() ;
	zero->key         = 'z' ;
	zero->description = _("set negative evapo to zero");
	
	day = G_define_flag() ;
	day->key         = 'n' ;
	day->description = _("night-time");
	
	if (G_parser(argc, argv))
	  exit(EXIT_FAILURE);
	
	/* get entered parameters */
	T=input_T->answer;
	u2=input_u2->answer;
	DEM=input_DEM->answer;
	ndvi=input_ndvi->answer;
	Rn=input_Rn->answer;
	g0=input_g0->answer;
	ETa=output->answer;

	row_wet = atoi(input_row_wet->answer);
	col_wet = atoi(input_col_wet->answer);
	row_dry = atoi(input_row_dry->answer);
	col_dry = atoi(input_col_dry->answer);
	
	if (day->answer) {
		d_night = TRUE;
	}
	else {
		d_night=FALSE;
	}
	
	/* find maps in mapset */
	mapset_T = G_find_cell2 (T, "");
	if (mapset_T == NULL)
	        G_fatal_error (_("cell file [%s] not found"), T);
	mapset_u2 = G_find_cell2 (u2, "");
	if (mapset_u2 == NULL)
	        G_fatal_error (_("cell file [%s] not found"), u2);
	mapset_DEM = G_find_cell2 (DEM, "");
	if (mapset_DEM == NULL)
	        G_fatal_error (_("cell file [%s] not found"), DEM);
	mapset_ndvi = G_find_cell2 (ndvi, "");
	if (mapset_ndvi == NULL)
	        G_fatal_error (_("cell file [%s] not found"), ndvi);
	mapset_Rn = G_find_cell2 (Rn, "");
	if (mapset_Rn == NULL)
	        G_fatal_error (_("cell file [%s] not found"), Rn);
	mapset_g0 = G_find_cell2 (g0, "");
	if (mapset_g0 == NULL)
	        G_fatal_error (_("cell file [%s] not found"), g0);

	
	/* check legal output name */ 
	if (G_legal_filename (ETa) < 0)
			G_fatal_error (_("[%s] is an illegal name"), ETa);
		
	/* determine the input map type (CELL/FCELL/DCELL) */
	//data_type = G_raster_map_type(T, mapset);

	if ( (infd_T = G_open_cell_old (T, mapset_T)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), T);
	if ( (infd_u2 = G_open_cell_old (u2, mapset_u2)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),u2);
	if ( (infd_DEM = G_open_cell_old (DEM, mapset_DEM)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),DEM);
	if ( (infd_ndvi = G_open_cell_old (ndvi, mapset_ndvi)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),ndvi);
	if ( (infd_Rn = G_open_cell_old (Rn, mapset_Rn)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),Rn);
	if ( (infd_g0 = G_open_cell_old (g0, mapset_g0)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),g0);
	
	if (G_get_cellhd (T, mapset_T, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), T);
	if (G_get_cellhd (u2, mapset_u2, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), u2);
	if (G_get_cellhd (DEM, mapset_DEM, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), DEM);
	if (G_get_cellhd (ndvi, mapset_ndvi, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), ndvi);
	if (G_get_cellhd (Rn, mapset_Rn, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), Rn);
	if (G_get_cellhd (g0, mapset_g0, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), g0);

	/* Allocate input buffer */
	inrast_T  = G_allocate_d_raster_buf();
	inrast_u2 = G_allocate_d_raster_buf();
	inrast_DEM = G_allocate_d_raster_buf();
	inrast_ndvi = G_allocate_d_raster_buf();
	inrast_Rn = G_allocate_d_raster_buf();
	inrast_g0 = G_allocate_d_raster_buf();
	
	/* Allocate output buffer */
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast = G_allocate_d_raster_buf();

	if ( (outfd = G_open_raster_new (ETa,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),ETa);


	DCELL d_ndvi; 		/* Input raster */
	DCELL d_ndvi_max = 0.0;	/* Generated here */
	/* NDVI Max */
	for (row = 0; row < nrows; row++)
	{
		if (G_get_d_raster_row (infd_ndvi, inrast_ndvi, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),ndvi);
		for (col=0; col < ncols; col++)
		{
			d_ndvi	= ((DCELL *) inrast_ndvi)[col];
			if ((d_ndvi)>d_ndvi_max&&(d_ndvi)<0.98){
				d_ndvi_max	= d_ndvi;
			}
		}
	}

	/* Pick up wet and dry pixel values */
	DCELL d_Rn; 		/* Input raster */
	DCELL d_g0; 		/* Input raster */
	DCELL d_tempk_wet;
	DCELL d_tempk_dry;
	DCELL d_rnet_dry;
	DCELL d_g0_dry;
	DCELL d_t0dem_dry;
	DCELL d_dem_dry;

	/*Process wet pixel values*/
	if (G_get_d_raster_row (infd_T, inrast_T, row_wet) < 0)
		G_fatal_error (_("Could not read from <%s>"),T);
	d_tempk_wet	= ((DCELL *) inrast_T)[col_wet];

	/*Process dry pixel values*/
	if (G_get_d_raster_row (infd_T, inrast_T, row_dry) < 0)
		G_fatal_error (_("Could not read from <%s>"),T);
	if (G_get_d_raster_row (infd_DEM, inrast_DEM, row) < 0)
		G_fatal_error (_("Could not read from <%s>"),DEM);
	if (G_get_d_raster_row (infd_Rn, inrast_Rn, row_dry) < 0)
		G_fatal_error (_("Could not read from <%s>"),Rn);
	if (G_get_d_raster_row (infd_g0, inrast_g0, row_dry) < 0)
		G_fatal_error (_("Could not read from <%s>"),g0);
	d_tempk_dry	= ((DCELL *) inrast_T)[col_dry];
	d_rnet_dry	= ((DCELL *) inrast_Rn)[col_dry];
	d_g0_dry	= ((DCELL *) inrast_g0)[col_dry];
	d_t0dem_dry	= ((DCELL *) inrast_DEM)[col_dry];
	d_t0dem_dry	= d_t0dem_dry * 0.00627 + d_tempk_dry;
	d_dem_dry	= ((DCELL *) inrast_DEM)[col_dry];
	
	
	for (row = 0; row < nrows; row++)
	{
		DCELL d_tempk; 		/* Input raster */
		DCELL d_u2m; 		/* Input raster */
		DCELL d_dem; 		/* Input raster */
		DCELL d;	/* Output pixel */
		DCELL d_t0dem;	/* Generated here */

		/* read a line input maps into buffers*/	
		if (G_get_d_raster_row (infd_T, inrast_T, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),T);
		if (G_get_d_raster_row (infd_u2, inrast_u2, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),u2);
		if (G_get_d_raster_row (infd_DEM, inrast_DEM, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),DEM);
		if (G_get_d_raster_row (infd_ndvi, inrast_ndvi, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),ndvi);
		
		/* read every cell in the line buffers */
		for (col=0; col < ncols; col++)
		{
			d_tempk	= ((DCELL *) inrast_T)[col];
			d_u2m	= ((DCELL *) inrast_u2)[col];
			d_dem	= ((DCELL *) inrast_DEM)[col];
			d_ndvi	= ((DCELL *) inrast_ndvi)[col];
			d_Rn	= ((DCELL *) inrast_Rn)[col];
			d_g0	= ((DCELL *) inrast_g0)[col];
			
			/* Calculate T0dem */
			d_t0dem = d_dem * 0.00627 + d_tempk;
			/* Calculate sensible heat flux */
			d = sensi_h(d_tempk_wet,d_tempk_dry,d_t0dem,d_tempk,d_ndvi,d_ndvi_max,d_dem,d_rnet_dry,d_g0_dry,d_t0dem_dry,d_u2m,d_dem_dry);
			
			if (zero->answer && d<0.0){
				d=0.0;
			}
			((DCELL *) outrast)[col] = d;
		}
		
		if (G_put_d_raster_row (outfd, outrast) < 0)
			G_fatal_error (_("Cannot write to <%s>"),ETa);
			
	}	
	G_free(inrast_T);
	G_free(inrast_u2);
	G_free(inrast_DEM);
	G_free(inrast_ndvi);
	G_free(inrast_Rn);
	G_free(inrast_g0);
	G_free(outrast);
	G_close_cell (infd_T);
	G_close_cell (infd_u2);
	G_close_cell (infd_DEM);
	G_close_cell (infd_ndvi);
	G_close_cell (infd_Rn);
	G_close_cell (infd_g0);
	G_close_cell (outfd);
	
        /* add command line incantation to history file */
        G_short_history(ETa, "raster", &history);
        G_command_history(&history);
        G_write_history(ETa, &history);

	exit(EXIT_SUCCESS);
}
