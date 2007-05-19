/*****************************************************************************
*
* MODULE:	i.evapo.PM
* AUTHOR:	Massimiliano Cannata - massimiliano.cannata@supsi.ch (2005)
* 		included in GIPE by Yann Chemin - ychemin_AT_gmail.com (2006)
*
* PURPOSE:	To estimate the hourly potential evapotranspiration by means
*		of Penman-Monteith equations.
*
* COPYRIGHT:	(C) 2006 by Istituto Scienze della Terra
*
*		This program is free software under the GNU General Public
*		Licence (>=2). Read the file COPYING that cames with GRASS
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
#include "local_proto.h"

int main(int argc, char *argv[])
{	
	/* buffer for input-output rasters */
	DCELL *inrast_T,*inrast_RH,*inrast_u2,*inrast_Rn,*inrast_DEM,*inrast_hc;
	DCELL *outrast;
	
	/* pointers to input-output raster files */
	int infd_T,infd_RH,infd_u2,infd_Rn,infd_DEM,infd_hc;
	int outfd;

	/* mapsets for input raster files */
	char *mapset_T,*mapset_RH,*mapset_u2,*mapset_Rn,*mapset_DEM,*mapset_hc;

	/* names of input-output raster files */
	char *T, *RH, *u2, *Rn, *DEM, *hc;
	char *EPo; /* unsigned char *EPo; */

	/* input-output cell values */
	DCELL d_T,d_RH,d_u2,d_Rn,d_Z,d_hc;
	DCELL d_EPo;

	/* region informations and handler */
	struct Cell_head cellhd;
	int nrows, ncols;
	int row, col;

	/* parser stuctures definition */
	struct GModule *module;
	struct Option *input_DEM, *input_T, *input_RH, *input_u2, *input_Rn, *input_hc, *output;
	struct Flag *flag1, *day, *zero;
	struct Colors color;
	struct History history;
			
	int d_day;

	/* Initialize the GIS calls */
	G_gisinit(argv[0]);
	
	module = G_define_module();
	module->description =
		_("Potontial Evapotranspiration Calculation "
		"Penman-Monteith formulation");
	
	/* Define different options */
	input_DEM = G_define_option();
	input_DEM->key	= "DEM";
	input_DEM->type = TYPE_STRING;
	input_DEM->required = YES;
	input_DEM->gisprompt = "old,cell,raster";
	input_DEM->description = _("Name of DEM raster map");
	
	input_T = G_define_option();
	input_T->key			= "T";
	input_T->key_desc		= "[°C]";
	input_T->type			= TYPE_STRING;
	input_T->required		= YES;
	input_T->gisprompt		= "old,cell,raster";
	input_T->description	= _("Name of Temperature raster map");
		
	input_RH = G_define_option();
	input_RH->key			= "RH";
	input_RH->key_desc		= "[%]";
	input_RH->type			= TYPE_STRING;
	input_RH->required		= YES;
	input_RH->gisprompt		= "old,cell,raster";
	input_RH->description	= _("Name of Relative Humidity raster map");
		
	input_u2 = G_define_option();
	input_u2->key			= "WS";
	input_u2->key_desc		= "[m/s]";
	input_u2->type			= TYPE_STRING;
	input_u2->required		= YES;
	input_u2->gisprompt		= "old,cell,raster";
	input_u2->description	= _("Name of Wind Speed raster map");
	
	input_Rn = G_define_option();
	input_Rn->key			= "NSR";
	input_Rn->key_desc		= "[MJ/(m2*h)]";
	input_Rn->type			= TYPE_STRING;
	input_Rn->required		= YES;
	input_Rn->gisprompt		= "old,cell,raster";
	input_Rn->description	= _("Name of Net Solar Radiation raster map");
	
	input_hc = G_define_option();
	input_hc->key			= "Vh";
	input_hc->key_desc		= "[m]";
	input_hc->type			= TYPE_STRING;
	input_hc->required		= YES;
	input_hc->gisprompt		= "old,cell,raster";
	input_hc->description	= _("Name of crop height raster map");	
	
	output = G_define_option() ;
	output->key			= "ETP";
	output->key_desc		= "[mm/h]";
	output->type			= TYPE_STRING;
	output->required		= YES;
	output->gisprompt		= "new,cell,raster" ;
	output->description		= _("Name of output Reference Potential Evapotranspiration layer");
	
	/* Define the different flags */
	flag1 = G_define_flag() ;
	flag1->key			= 'q' ;
	flag1->description	= _("quiet");
	
	zero = G_define_flag() ;
	zero->key			= 'z' ;
	zero->description	= _("set negative ETP to zero");
	
	day = G_define_flag() ;
	day->key			= 'd' ;
	day->description	= _("daytime");
	
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
		d_day = TRUE;
	}
	else {
		d_day = FALSE;
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

	/* open pointers to input raster files */
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

	/* read headers of raster files */
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
	
	/* get rows and columns number of the current region */
	nrows = G_window_rows();
	ncols = G_window_cols();

	/* allocate output buffer */
	outrast = G_allocate_d_raster_buf();

	/* open pointers to output raster files */
	if ( (outfd = G_open_raster_new (EPo,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),T);
	

	/* start the loop through cells */
	for (row = 0; row < nrows; row++)
	{
				
		/* read input raster row into line buffer*/	
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
		
		for (col=0; col < ncols; col++)
		{
			/* read current cell from line buffer */
			d_T		= ((DCELL *) inrast_T)[col];
			d_RH	= ((DCELL *) inrast_RH)[col];
			d_u2	= ((DCELL *) inrast_u2)[col];
			d_Rn	= ((DCELL *) inrast_Rn)[col];
			d_Z		= ((DCELL *) inrast_DEM)[col];
			d_hc	= ((DCELL *) inrast_hc)[col];
			
			/* calculate potential evapotranspiration */
			if (d_hc<0){
				/* calculate evaporation (Penman)*/
				d_EPo=calc_openwaterETp(d_T,d_Z,d_u2,d_Rn,d_day,d_RH,d_hc);
			}
			else {
				/* calculate evapotranspiration (Penman-Monteith)*/
				d_EPo=calc_ETp(d_T,d_Z,d_u2,d_Rn,d_day,d_RH,d_hc);
			}
			
			if (zero->answer && d_EPo<0)
				d_EPo=0;
			
			/* write calculated ETP to output line buffer */
			((DCELL *) outrast)[col] = d_EPo;
		}
		
		if (!flag1->answer) G_percent(row, nrows, 2);

		/* write output line buffer to output raster file */
		if (G_put_d_raster_row (outfd, outrast) < 0)
			G_fatal_error (_("Cannot write to <%s>"),EPo);
			
	}
	/* free buffers and close input maps */
	G_free(inrast_T);
	G_free(inrast_RH);
	G_free(inrast_u2);
	G_free(inrast_Rn);
	G_free(inrast_DEM);
	G_free(inrast_hc);
	G_close_cell (infd_T);
	G_close_cell (infd_RH);
	G_close_cell (infd_u2);
	G_close_cell (infd_Rn);
	G_close_cell (infd_DEM);
	G_close_cell (infd_hc);
	
	
	/* generate color table between -20 and 20 */
	G_make_rainbow_colors(&color, -20, 20);
	G_write_colors(outrast,G_mapset(),&color);

	G_short_history(outrast,"raster", &history);
	G_command_history(&history);
	G_write_history(outrast, &history);

	/* free buffers and close output map */
	G_free(outrast);
	G_close_cell (outfd);

	return (0);
}
