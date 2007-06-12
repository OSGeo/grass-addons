/* Created by Anjuta version 1.0.2 */
/*	This file will not be overwritten */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <grass/gis.h>
#include <math.h>
#include "local_proto.h"
#include <grass/glocale.h>


int main(int argc, char *argv[])
{	
	struct Cell_head cellhd;
	
	/* buffer for in out raster */
	DCELL *inrast_T,*inrast_RH,*inrast_u2,*inrast_Rn,*inrast_DEM,*inrast_hc,*outrast;
	unsigned char *EPo;
	
	int nrows, ncols;
	int row, col;
	int infd_T,infd_RH,infd_u2,infd_Rn,infd_DEM,infd_hc;
	int outfd;
	
	char *mapset_T,*mapset_RH,*mapset_u2,*mapset_Rn,*mapset_DEM,*mapset_hc;
	char *T, *RH, *u2, *Rn, *DEM, *hc; 
	DCELL d_T,d_RH,d_u2,d_Rn,d_Z,d_hc;
	DCELL d_EPo;
	
	int d_night;
	
        struct History history;
	struct GModule *module;
	struct Option *input_DEM, *input_T, *input_RH, *input_u2, *input_Rn, *input_hc, *output;
	struct Flag *flag1, *day, *zero;
	
	
	G_gisinit(argv[0]);
	
	module = G_define_module();
	module->description = _("Potontial Evapotranspiration Calculation with hourly Penman-Monteith");
	
	/* Define different options */
	input_DEM = G_define_option();
	input_DEM->key	= "DEM";
	input_DEM->type = TYPE_STRING;
	input_DEM->required = YES;
	input_DEM->gisprompt = "old,cell,raster";
	input_DEM->description = _("Name of DEM raster map [m a.s.l.]");
	
	input_T = G_define_option();
	input_T->key	= "T";
	input_T->type = TYPE_STRING;
	input_T->required = YES;
	input_T->gisprompt = "old,cell,raster";
	input_T->description = _("Name of Temperature raster map [°C]");
		
	input_RH = G_define_option();
	input_RH->key	= "RU";
	input_RH->type = TYPE_STRING;
	input_RH->required = YES;
	input_RH->gisprompt = "old,cell,raster";
	input_RH->description = _("Name of Relative Umidity raster map [%]");
		
	input_u2 = G_define_option();
	input_u2->key	= "WS";
	input_u2->type = TYPE_STRING;
	input_u2->required = YES;
	input_u2->gisprompt = "old,cell,raster";
	input_u2->description = _("Name of Wind Speed raster map [m/s]");
	
	input_Rn = G_define_option();
	input_Rn->key	= "NSR";
	input_Rn->type = TYPE_STRING;
	input_Rn->required = YES;
	input_Rn->gisprompt = "old,cell,raster";
	input_Rn->description = _("Name of Net Solar Radiation raster map [MJ/m2/h]");
	
	input_hc = G_define_option();
	input_hc->key	= "Vh";
	input_hc->type = TYPE_STRING;
	input_hc->required = YES;
	input_hc->gisprompt = "old,cell,raster";
	input_hc->description = _("Name of crop height raster map [m]");	
	
	output = G_define_option() ;
	output->key        = "EPo";
	output->type       = TYPE_STRING;
	output->required   = YES;
	output->gisprompt  = "new,cell,raster" ;
	output->description= _("Name of output Reference Potential Evapotranspiration layer [mm/h]");
	
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
	RH=input_RH->answer;
	u2=input_u2->answer;
	Rn=input_Rn->answer;
	EPo=output->answer;
	DEM=input_DEM->answer;
	hc=input_hc->answer;
	
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
	mapset_RH = G_find_cell2 (RH, "");
	if (mapset_RH == NULL)
	        G_fatal_error (_("cell file [%s] not found"), RH);
	mapset_u2 = G_find_cell2 (u2, "");
	if (mapset_u2 == NULL)
	        G_fatal_error (_("cell file [%s] not found"), u2);
	mapset_Rn = G_find_cell2 (Rn, "");
	if (mapset_Rn == NULL)
	        G_fatal_error (_("cell file [%s] not found"), Rn);
	mapset_DEM = G_find_cell2 (DEM, "");
	if (mapset_DEM == NULL)
	        G_fatal_error (_("cell file [%s] not found"), DEM);
	mapset_hc = G_find_cell2 (hc, "");
	if (mapset_hc == NULL)
	        G_fatal_error (_("cell file [%s] not found"), hc);


	
	/* check legal output name */ 
	if (G_legal_filename (EPo) < 0)
			G_fatal_error (_("[%s] is an illegal name"), EPo);
		
	/* determine the input map type (CELL/FCELL/DCELL) */
	//data_type = G_raster_map_type(T, mapset);

	if ( (infd_T = G_open_cell_old (T, mapset_T)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), T);
	if ( (infd_RH = G_open_cell_old (RH, mapset_RH)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),RH);
	if ( (infd_u2 = G_open_cell_old (u2, mapset_u2)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),u2);
	if ( (infd_Rn = G_open_cell_old (Rn, mapset_Rn)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),Rn);
	if ( (infd_DEM = G_open_cell_old (DEM, mapset_DEM)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),DEM);
	if ( (infd_hc = G_open_cell_old (hc, mapset_hc)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),hc);
	
	if (G_get_cellhd (T, mapset_T, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), T);
	if (G_get_cellhd (RH, mapset_RH, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), RH);
	if (G_get_cellhd (u2, mapset_u2, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), u2);
	if (G_get_cellhd (Rn, mapset_Rn, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), Rn);
	if (G_get_cellhd (DEM, mapset_DEM, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), DEM);
	if (G_get_cellhd (hc, mapset_hc, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), hc);

	/* Allocate input buffer */
	inrast_T  = G_allocate_d_raster_buf();
	inrast_RH = G_allocate_d_raster_buf();
	inrast_u2 = G_allocate_d_raster_buf();
	inrast_Rn = G_allocate_d_raster_buf();
	inrast_DEM = G_allocate_d_raster_buf();
	inrast_hc = G_allocate_d_raster_buf();
	
	/* Allocate output buffer */
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast = G_allocate_d_raster_buf();

	if ( (outfd = G_open_raster_new (EPo,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),T);
	
	for (row = 0; row < nrows; row++)
	{
				
		/* read a line input maps into buffers*/	
		if (G_get_d_raster_row (infd_T, inrast_T, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),T);
		if (G_get_d_raster_row (infd_RH, inrast_RH, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),RH);
		if (G_get_d_raster_row (infd_u2, inrast_u2, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),u2);
		if (G_get_d_raster_row (infd_Rn, inrast_Rn, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),Rn);
		if (G_get_d_raster_row (infd_DEM, inrast_DEM, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),DEM);
		if (G_get_d_raster_row (infd_hc, inrast_hc, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),hc);
		
		/* read every cell in the line buffers */
		for (col=0; col < ncols; col++)
		{
			d_T	= ((DCELL *) inrast_T)[col];
			d_RH	= ((DCELL *) inrast_RH)[col];
			d_u2	= ((DCELL *) inrast_u2)[col];
			d_Rn	= ((DCELL *) inrast_Rn)[col];
			d_Z	= ((DCELL *) inrast_DEM)[col];
			d_hc	= ((DCELL *) inrast_hc)[col];
			
			//calculate evapotranspiration
			if (d_hc<0){
				//calculate evaporation
				d_EPo=calc_openwaterETp(d_T,d_Z,d_u2,d_Rn,d_night,d_RH,d_hc);
			}
			else {
				//calculate evapotranspiration
				d_EPo=calc_ETp(d_T,d_Z,d_u2,d_Rn,d_night,d_RH,d_hc);
			}
			
			if (zero->answer && d_EPo<0)
				d_EPo=0;
			
			((DCELL *) outrast)[col] = d_EPo;
		}
		
		if (G_put_d_raster_row (outfd, outrast) < 0)
			G_fatal_error (_("Cannot write to <%s>"),EPo);
			
	}	
	G_free(inrast_T);
	G_free(inrast_RH);
	G_free(inrast_u2);
	G_free(inrast_Rn);
	G_free(inrast_DEM);
	G_free(inrast_hc);
	G_free(outrast);
	G_close_cell (infd_T);
	G_close_cell (infd_RH);
	G_close_cell (infd_u2);
	G_close_cell (infd_Rn);
	G_close_cell (infd_DEM);
	G_close_cell (infd_hc);
	G_close_cell (outfd);
	
        /* add command line incantation to history file */
        G_short_history(output, "raster", &history);
        G_command_history(&history);
        G_write_history(output, &history);

	exit(EXIT_SUCCESS);
}
