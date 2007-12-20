/****************************************************************************
 *
 * MODULE:       i.eb.wetdrypix
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Tries to zero in areas of potential pixel candidates for
 * 		 use in the initialisation of the sensible heat flux in SEBAL
 * 		 iteration, where Delta T is reassessed in each iteration.
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
#include <grass/glocale.h>

int main(int argc, char *argv[])
{	
	struct Cell_head cellhd;
	
	/* buffer for in out raster */
	DCELL *inrast_T,*inrast_ndvi,*inrast_alb,*inrast_DEM,*inrast_Rn,*inrast_g0,*outrast,*outrast1;
	unsigned char *wet, *dry;
	
	int nrows, ncols;
	int row, col;
	int infd_T,infd_ndvi,infd_alb,infd_DEM,infd_Rn,infd_g0;
	int outfd, outfd1;
	
	char *mapset_T,*mapset_ndvi,*mapset_alb,*mapset_DEM,*mapset_Rn,*mapset_g0;
	char *T, *ndvi, *alb, *DEM, *Rn, *g0; 
	
        struct History history;
	struct GModule *module;
	struct Option *input_T, *input_ndvi, *input_alb, *input_DEM, *input_Rn, *input_g0, *output, *output1;
	
	struct Flag *flag1, *zero;
	
	G_gisinit(argv[0]);
	
	module = G_define_module();
	module->description = _("Wet and Dry pixels candidates for SEBAL 95");
	
	/* Define different options */
	input_T = G_define_option();
	input_T->key	= "T";
	input_T->type = TYPE_STRING;
	input_T->required = YES;
	input_T->gisprompt = "old,cell,raster";
	input_T->description = _("Name of Surface Skin Temperature input map [K]");
		
	input_alb = G_define_option();
	input_alb->key	= "alb";
	input_alb->type = TYPE_STRING;
	input_alb->required = YES;
	input_alb->gisprompt = "old,cell,raster";
	input_alb->description = _("Name of Broadband Albedo input map [-]");
		
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
	input_ndvi->description = _("Name of NDVI input map [-]");
	
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
	
	output = G_define_option() ;
	output->key        = "wet";
	output->type       = TYPE_STRING;
	output->required   = YES;
	output->gisprompt  = "new,cell,raster" ;
	output->description= _("Name of output wet pixels areas layer [-]");
	
	output1 = G_define_option() ;
	output1->key        = "dry";
	output1->type       = TYPE_STRING;
	output1->required   = YES;
	output1->gisprompt  = "new,cell,raster" ;
	output1->description= _("Name of output dry pixels areas layer [-]");
	
	/* Define the different flags */
	//flag1 = G_define_flag() ;
	//flag1->key         = 'q' ;
	//flag1->description = "Quiet" ;
	
	zero = G_define_flag() ;
	zero->key         = 'z' ;
	zero->description = _("set negative to zero");
	
	if (G_parser(argc, argv))
	  exit(EXIT_FAILURE);
	
	/* get entered parameters */
	T=input_T->answer;
	alb=input_alb->answer;
	DEM=input_DEM->answer;
	ndvi=input_ndvi->answer;
	Rn=input_Rn->answer;
	g0=input_g0->answer;
	wet=output->answer;
	dry=output1->answer;
	
	/* find maps in mapset */
	mapset_T = G_find_cell2 (T, "");
	if (mapset_T == NULL)
	        G_fatal_error (_("cell file [%s] not found"), T);
	mapset_alb = G_find_cell2 (alb, "");
	if (mapset_alb == NULL)
	        G_fatal_error (_("cell file [%s] not found"), alb);
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
	if (G_legal_filename (wet) < 0)
			G_fatal_error (_("[%s] is an illegal name"), wet);
	if (G_legal_filename (dry) < 0)
			G_fatal_error (_("[%s] is an illegal name"), dry);
		
	/* determine the input map type (CELL/FCELL/DCELL) */
	//data_type = G_raster_map_type(T, mapset);

	if ( (infd_T = G_open_cell_old (T, mapset_T)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), T);
	if ( (infd_alb = G_open_cell_old (alb, mapset_alb)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),alb);
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
	if (G_get_cellhd (alb, mapset_alb, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), alb);
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
	inrast_alb = G_allocate_d_raster_buf();
	inrast_DEM = G_allocate_d_raster_buf();
	inrast_ndvi = G_allocate_d_raster_buf();
	inrast_Rn = G_allocate_d_raster_buf();
	inrast_g0 = G_allocate_d_raster_buf();
	
	/* Allocate output buffer */
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast = G_allocate_d_raster_buf();
	outrast1 = G_allocate_d_raster_buf();

	if ( (outfd = G_open_raster_new (wet,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),wet);
	if ( (outfd = G_open_raster_new (dry,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),dry);

	for (row = 0; row < nrows; row++)
	{
		DCELL d_tempk; 		/* Input raster */
		DCELL d_alb; 		/* Input raster */
		DCELL d_dem; 		/* Input raster */
		DCELL d_ndvi; 		/* Input raster */
		DCELL d_Rn;		/* Input raster */
		DCELL d_g0;		/* Input raster */
		DCELL d_wet;	/* Output pixel */
		DCELL d_dry;	/* Output pixel */
		DCELL d_t0dem;	/* Generated here */

		/* read a line input maps into buffers*/	
		if (G_get_d_raster_row (infd_T, inrast_T, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),T);
		if (G_get_d_raster_row (infd_alb, inrast_alb, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),alb);
		if (G_get_d_raster_row (infd_DEM, inrast_DEM, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),DEM);
		if (G_get_d_raster_row (infd_ndvi, inrast_ndvi, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),ndvi);
		if (G_get_d_raster_row (infd_Rn, inrast_Rn, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),Rn);
		if (G_get_d_raster_row (infd_g0, inrast_g0, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),g0);
		
		/* read every cell in the line buffers */
		for (col=0; col < ncols; col++)
		{
			d_tempk	= ((DCELL *) inrast_T)[col];
			d_alb	= ((DCELL *) inrast_alb)[col];
			d_dem	= ((DCELL *) inrast_DEM)[col];
			d_ndvi	= ((DCELL *) inrast_ndvi)[col];
			d_Rn	= ((DCELL *) inrast_Rn)[col];
			d_g0	= ((DCELL *) inrast_g0)[col];
			
			/* Initialize pixels as negative */
			d_wet = -1.0;
			d_dry = -1.0;

			/* Calculate T0dem */
			d_t0dem = d_dem * 0.00627 + d_tempk;
			/* if Albedo is high and H is positive */
			if(d_alb>0.3&&(d_Rn-d_g0)>0.0){
				d_wet = 0.0; /* Not Wet pixel Candidate */
				d_dry = 1.0; /* Dry pixel candidate */
			/* if Albedo is not high and H is negative */
			} else if (d_alb<0.3&&(d_Rn-d_g0)<=0.0){
				d_wet = 1.0; /* Wet pixel Candidate */
				d_dry = 0.0; /* Not dry pixel Candidate */
			/* if g0 is negative, then not a candidate */
			} else if (d_g0<=0.0){
				d_wet = 0.0; /* Not wet pixel candidate */
				d_dry = 0.0; /* Not dry pixel candidate */
			}
			/* if altitude corrected temperature is strange, then not a candidate */
			if (d_t0dem<=273.15||d_t0dem>340.0){
				d_wet = 0.0; /* Not wet pixel candidate */
				d_dry = 0.0; /* Not dry pixel candidate */
			}

			if (zero->answer && d_wet<0.0){
				d_wet = 0.0;
			}
			if (zero->answer && d_dry<0.0){
				d_dry = 0.0;
			}
			((DCELL *) outrast)[col] = d_wet;
			((DCELL *) outrast1)[col] = d_dry;
		}
		
		if (G_put_d_raster_row (outfd, outrast) < 0)
			G_fatal_error (_("Cannot write to <%s>"),wet);
		if (G_put_d_raster_row (outfd, outrast1) < 0)
			G_fatal_error (_("Cannot write to <%s>"),dry);
	}	
	G_free(inrast_T);
	G_free(inrast_alb);
	G_free(inrast_DEM);
	G_free(inrast_ndvi);
	G_free(inrast_Rn);
	G_free(inrast_g0);
	G_free(outrast);
	G_free(outrast1);
	G_close_cell (infd_T);
	G_close_cell (infd_alb);
	G_close_cell (infd_DEM);
	G_close_cell (infd_ndvi);
	G_close_cell (infd_Rn);
	G_close_cell (infd_g0);
	G_close_cell (outfd);
	G_close_cell (outfd1);
	
        /* add command line incantation to history file */
        G_short_history(wet, "raster", &history);
        G_command_history(&history);
        G_write_history(wet, &history);
        G_short_history(dry, "raster", &history);
        G_command_history(&history);
        G_write_history(dry, &history);

	exit(EXIT_SUCCESS);
}
