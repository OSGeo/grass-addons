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
	char *mapset; // mapset name
	
	/* buffer for in out raster */
	DCELL *inrast_T,*inrast_ndvi,*inrast_u2,*inrast_DEM;
	DCELL *inrast_Rn,*inrast_g0,*inrast_albedo,*outrast;
	unsigned char *h0;
	
	int nrows, ncols;
	int row, col;
	int row_wet, col_wet;
	int row_dry, col_dry;
	int infd_T,infd_ndvi,infd_u2,infd_DEM,infd_Rn,infd_g0,infd_albedo;
	int outfd;
	
	char *mapset_T,*mapset_ndvi,*mapset_u2,*mapset_DEM;
	char *mapset_Rn,*mapset_g0,*mapset_albedo;
	char *T, *ndvi, *u2, *DEM, *Rn, *g0, *albedo; 
	
        struct History history;
	struct GModule *module;
	struct Option *input_T, *input_ndvi, *input_u2, *input_DEM;
	struct Option *input_Rn, *input_g0, *input_albedo, *output;
	struct Option *input_row_wet, *input_col_wet;
	struct Option *input_row_dry, *input_col_dry;
	struct Flag *flag1, *day, *zero;
	/*******************************/
	RASTER_MAP_TYPE data_type_T;
	RASTER_MAP_TYPE data_type_ndvi;
	RASTER_MAP_TYPE data_type_u2;
	RASTER_MAP_TYPE data_type_DEM;
	RASTER_MAP_TYPE data_type_Rn;
	RASTER_MAP_TYPE data_type_g0;
	RASTER_MAP_TYPE data_type_albedo;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	/*******************************/
	/********************************/
	/* Stats for Senay equation	*/
	double t0dem_min=400.0,t0dem_max=200.0;
	double tempk_min=400.0,tempk_max=200.0;
	/********************************/
	G_gisinit(argv[0]);
	
	module = G_define_module();
	module->description = _("Sensible Heat Flux iteration from SEBAL 95");
	
	/* Define different options */
	input_T = G_define_standard_option(G_OPT_R_INPUT);
	input_T->key	= "T";
	input_T->description = _("Name of Surface Skin Temperature input map [K]");
	input_T->guisection = _("Required");

	input_u2 = G_define_standard_option(G_OPT_R_INPUT);
	input_u2->key	= "u2m";
	input_u2->description = _("Name of Wind Speed input map [m/s]");
	input_u2->guisection = _("Required");
		
	input_DEM = G_define_standard_option(G_OPT_R_INPUT);
	input_DEM->key	= "DEM";
	input_DEM->description = _("Name of DEM input map [m a.s.l.]");
	input_DEM->guisection = _("Required");
	
	input_ndvi = G_define_standard_option(G_OPT_R_INPUT);
	input_ndvi->key	= "ndvi";
	input_ndvi->description = _("Name of NDVI input map [%]");
	input_ndvi->guisection = _("Required");
	
	input_Rn = G_define_standard_option(G_OPT_R_INPUT);
	input_Rn->key	= "Rn";
	input_Rn->description = _("Name of Diurnal Net Solar Radiation input map [W/m2]");
	input_Rn->guisection = _("Required");
	
	input_g0 = G_define_standard_option(G_OPT_R_INPUT);
	input_g0->key	= "g0";
	input_g0->description = _("Name of Soil Heat Flux input map [W/m2]");
	input_g0->guisection = _("Required");
	
	input_albedo = G_define_standard_option(G_OPT_R_INPUT);
	input_albedo->key	= "albedo";
	input_albedo->required	= NO;
	input_albedo->description = _("With Flag \"-a\": Name of Albedo input map [-]");
	input_albedo->guisection = _("Optional");
	
	input_row_wet 			= G_define_option();
	input_row_wet->key		= "row_wet";
	input_row_wet->type 		= TYPE_INTEGER;
	input_row_wet->required 	= NO;
	input_row_wet->gisprompt 	= "old,value";
	input_row_wet->description 	= _("Row value of the wet pixel");
	input_row_wet->guisection	= _("Optional");
	
	input_col_wet 			= G_define_option();
	input_col_wet->key		= "col_wet";
	input_col_wet->type 		= TYPE_INTEGER;
	input_col_wet->required 	= NO;
	input_col_wet->gisprompt 	= "old,value";
	input_col_wet->description 	= _("Column value of the wet pixel");
	input_col_wet->guisection	= _("Optional");
	
	input_row_dry 			= G_define_option();
	input_row_dry->key		= "row_dry";
	input_row_dry->type 		= TYPE_INTEGER;
	input_row_dry->required 	= NO;
	input_row_dry->gisprompt 	= "old,value";
	input_row_dry->description 	= _("Row value of the dry pixel");
	input_row_dry->guisection	= _("Optional");
	
	input_col_dry 			= G_define_option();
	input_col_dry->key		= "col_dry";
	input_col_dry->type 		= TYPE_INTEGER;
	input_col_dry->required 	= NO;
	input_col_dry->gisprompt 	= "old,value";
	input_col_dry->description 	= _("Column value of the dry pixel");
	input_col_dry->guisection	= _("Optional");

	output = G_define_standard_option(G_OPT_R_OUTPUT) ;
	output->key        = "h0";
	output->description= _("Name of output Actual Evapotranspiration layer [mm/d]");
	output->guisection	= _("Required");
	
	/* Define the different flags */
	flag1 = G_define_flag() ;
	flag1->key         = 'a' ;
	flag1->description = _("Automatic wet/dry pixel (careful!)") ;
	
	zero = G_define_flag() ;
	zero->key         = 'z' ;
	zero->description = _("set negative evapo to zero");
	
	if (G_parser(argc, argv))
		exit(EXIT_FAILURE);
	
	/* get entered parameters */
	T	= input_T->answer;
	u2	= input_u2->answer;
	DEM	= input_DEM->answer;
	ndvi	= input_ndvi->answer;
	Rn	= input_Rn->answer;
	g0	= input_g0->answer;
	albedo	= input_albedo->answer;
	h0	= output->answer;

	if(input_row_wet->answer){
		row_wet = atoi(input_row_wet->answer);
		col_wet = atoi(input_col_wet->answer);
		row_dry = atoi(input_row_dry->answer);
		col_dry = atoi(input_col_dry->answer);
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
	if(flag1->answer){
		mapset_albedo = G_find_cell2 (albedo, "");
		if (mapset_albedo == NULL)
			G_fatal_error(_("cell file [%s] not found"),albedo);
	}
	
	/* check legal output name */ 
	if (G_legal_filename (h0) < 0)
			G_fatal_error (_("[%s] is an illegal name"), h0);
		
	/* determine the input map type (CELL/FCELL/DCELL) */
	data_type_T = G_raster_map_type(T, mapset_T);
	data_type_u2 = G_raster_map_type(u2, mapset_u2);
	data_type_DEM = G_raster_map_type(DEM, mapset_DEM);
	data_type_ndvi = G_raster_map_type(ndvi, mapset_ndvi);
	data_type_Rn = G_raster_map_type(Rn, mapset_Rn);
	data_type_g0 = G_raster_map_type(g0, mapset_g0);
	if(flag1->answer){
		data_type_albedo = G_raster_map_type(albedo, mapset_albedo);
	}
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
	if(flag1->answer){
		if((infd_albedo=G_open_cell_old (albedo,mapset_albedo)) < 0)
			G_fatal_error(_("Cannot open cell file [%s]"),albedo);
	}	
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
	if(flag1->answer){
		if (G_get_cellhd (albedo, mapset_albedo, &cellhd) < 0)
			G_fatal_error (_("Cannot read file header of [%s]"), albedo);
	}
	/* Allocate input buffer */
	inrast_T  = G_allocate_d_raster_buf();
	inrast_u2 = G_allocate_d_raster_buf();
	inrast_DEM = G_allocate_d_raster_buf();
	inrast_ndvi = G_allocate_d_raster_buf();
	inrast_Rn = G_allocate_d_raster_buf();
	inrast_g0 = G_allocate_d_raster_buf();
	if(flag1->answer){
		inrast_albedo = G_allocate_d_raster_buf();
	}
	/* Allocate output buffer */
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast = G_allocate_d_raster_buf();

	if((outfd = G_open_raster_new (h0,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),h0);

	DCELL d_ndvi; 		/* Input raster */
	DCELL d_ndvi_max = 0.0;	/* Generated here */
	/* THREAD 1 */
	/* NDVI Max */
	for (row = 0; row < nrows; row++)
	{
		if (G_get_d_raster_row (infd_ndvi, inrast_ndvi, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),ndvi);
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
					d_ndvi = (double) ((DCELL *) inrast_ndvi)[col];
					break;
			}
			//d_ndvi	= ((DCELL *) inrast_ndvi)[col];
			if(G_is_d_null_value(&d_ndvi)){
				/* do nothing */ 
			} else if ((d_ndvi)>d_ndvi_max&&(d_ndvi)<0.98){
				d_ndvi_max	= d_ndvi;
			}
		}
	}
	G_message("ndvi_max=%f\n",d_ndvi_max);
	/* FLAG1 */
	if(flag1->answer){
		/* THREAD 2 */
		/* Process tempk min / max pixels for SENAY Evapfr */
		for (row = 0; row < nrows; row++){
			DCELL d;
			DCELL d_albedo;
			DCELL d_tempk;
			DCELL d_dem;
			DCELL d_t0dem;
			G_percent(row,nrows,2);
			if(G_get_raster_row(infd_albedo,inrast_albedo,row,data_type_albedo)<0)
				G_fatal_error(_("Could not read from <%s>"),albedo);
			if(G_get_raster_row(infd_T,inrast_T,row,data_type_T)<0)
				G_fatal_error(_("Could not read from <%s>"),T);
			if(G_get_raster_row(infd_DEM,inrast_DEM,row,data_type_DEM)<0)
				G_fatal_error(_("Could not read from <%s>"),DEM);
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
				switch(data_type_T){
					case CELL_TYPE:
						d_tempk = (double) ((CELL *) inrast_T)[col];
						break;
					case FCELL_TYPE:
						d_tempk = (double) ((FCELL *) inrast_T)[col];
						break;
					case DCELL_TYPE:
						d_tempk = (double) ((DCELL *) inrast_T)[col];
						break;
				}
				switch(data_type_DEM){
					case CELL_TYPE:
						d_dem = (double) ((CELL *) inrast_DEM)[col];
						break;
					case FCELL_TYPE:
						d_dem = (double) ((FCELL *) inrast_DEM)[col];
						break;
					case DCELL_TYPE:
						d_dem = (double) ((DCELL *) inrast_DEM)[col];
						break;
				}
				if(G_is_d_null_value(&d_albedo)||
				G_is_d_null_value(&d_tempk)||
				G_is_d_null_value(&d_dem)){
					/* do nothing */ 
				}else{
					d_t0dem = d_tempk + 0.00649*d_dem;
					if(d_t0dem<0.0){
						/* do nothing */ 
					} else {
						if(d_t0dem<t0dem_min&&d_albedo<0.1){
							t0dem_min=d_t0dem;
							tempk_min=d_tempk;
							col_wet=col;
							row_wet=row;
						}else if(d_t0dem>t0dem_max){
							t0dem_max=d_t0dem;
							tempk_max=d_tempk;
							col_dry=col;
							row_dry=row;
						}
					}
				}
			}
		}
		G_message("tempk_min=%f\ntempk_max=%f\n",tempk_min,tempk_max);
		G_message("row_wet=%d\tcol_wet=%d\n",row_wet,col_wet);
		G_message("row_dry=%d\tcol_dry=%d\n",row_dry,col_dry);
	} /* END OF FLAG1 */
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
	switch(data_type_T){
		case CELL_TYPE:
			d_tempk_wet = (double) ((CELL *) inrast_T)[col_wet];
			break;
		case FCELL_TYPE:
			d_tempk_wet = (double) ((FCELL *) inrast_T)[col_wet];
			break;
		case DCELL_TYPE:
			d_tempk_wet = (double) ((DCELL *) inrast_T)[col_wet];
			break;
	}
	//d_tempk_wet	= ((DCELL *) inrast_T)[col_wet];
	/*Process dry pixel values*/
	if (G_get_d_raster_row (infd_T, inrast_T, row_dry) < 0)
		G_fatal_error (_("Could not read from <%s>"),T);
	if (G_get_d_raster_row (infd_DEM, inrast_DEM, row_dry) < 0)
		G_fatal_error (_("Could not read from <%s>"),DEM);
	if (G_get_d_raster_row (infd_Rn, inrast_Rn, row_dry) < 0)
		G_fatal_error (_("Could not read from <%s>"),Rn);
	if (G_get_d_raster_row (infd_g0, inrast_g0, row_dry) < 0)
		G_fatal_error (_("Could not read from <%s>"),g0);
	switch(data_type_T){
		case CELL_TYPE:
			d_tempk_dry = (double) ((CELL *) inrast_T)[col_dry];
			break;
		case FCELL_TYPE:
			d_tempk_dry = (double) ((FCELL *) inrast_T)[col_dry];
			break;
		case DCELL_TYPE:
			d_tempk_dry = (double) ((DCELL *) inrast_T)[col_dry];
			break;
	}
	switch(data_type_DEM){
		case CELL_TYPE:
			d_dem_dry = (double) ((CELL *) inrast_DEM)[col_dry];
			break;
		case FCELL_TYPE:
			d_dem_dry = (double) ((FCELL *) inrast_DEM)[col_dry];
			break;
		case DCELL_TYPE:
			d_dem_dry = (double) ((DCELL *) inrast_DEM)[col_dry];
			break;
	}
	switch(data_type_Rn){
		case CELL_TYPE:
			d_rnet_dry = (double) ((CELL *) inrast_Rn)[col_dry];
			break;
		case FCELL_TYPE:
			d_rnet_dry = (double) ((FCELL *) inrast_Rn)[col_dry];
			break;
		case DCELL_TYPE:
			d_rnet_dry = (double) ((DCELL *) inrast_Rn)[col_dry];
			break;
	}
	switch(data_type_g0){
		case CELL_TYPE:
			d_g0_dry = (double) ((CELL *) inrast_g0)[col_dry];
			break;
		case FCELL_TYPE:
			d_g0_dry = (double) ((FCELL *) inrast_g0)[col_dry];
			break;
		case DCELL_TYPE:
			d_g0_dry = (double) ((DCELL *) inrast_g0)[col_dry];
			break;
	}
//	d_tempk_dry	= ((DCELL *) inrast_T)[col_dry];
//	d_rnet_dry	= ((DCELL *) inrast_Rn)[col_dry];
//	d_g0_dry	= ((DCELL *) inrast_g0)[col_dry];
	d_t0dem_dry	= d_dem_dry * 0.00627 + d_tempk_dry;
//	d_dem_dry	= ((DCELL *) inrast_DEM)[col_dry];
	
	for (row = 0; row < nrows; row++)
	{
		DCELL d_tempk; 		/* Input raster */
		DCELL d_u2m; 		/* Input raster */
		DCELL d_dem; 		/* Input raster */
		DCELL d;	/* Output pixel */
		DCELL d_t0dem;	/* Generated here */
		G_percent(row,nrows,2);
		/* read a line input maps into buffers*/	
		if (G_get_d_raster_row (infd_T, inrast_T, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),T);
		if (G_get_d_raster_row (infd_u2, inrast_u2, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),u2);
		if (G_get_d_raster_row (infd_DEM, inrast_DEM, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),DEM);
		if (G_get_d_raster_row (infd_ndvi, inrast_ndvi, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),ndvi);
		if (G_get_d_raster_row (infd_Rn, inrast_Rn, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),Rn);
		if (G_get_d_raster_row (infd_g0, inrast_g0, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),g0);
		/* read every cell in the line buffers */
		for (col=0; col < ncols; col++){
			switch(data_type_T){
				case CELL_TYPE:
					d_tempk = (double) ((CELL *) inrast_T)[col];
					break;
				case FCELL_TYPE:
					d_tempk = (double) ((FCELL *) inrast_T)[col];
					break;
				case DCELL_TYPE:
					d_tempk = (double) ((DCELL *) inrast_T)[col];
					break;
			}
			switch(data_type_u2){
				case CELL_TYPE:
					d_u2m = (double) ((CELL *) inrast_u2)[col];
					break;
				case FCELL_TYPE:
					d_u2m = (double) ((FCELL *) inrast_u2)[col];
					break;
				case DCELL_TYPE:
					d_u2m = (double) ((DCELL *) inrast_u2)[col];
					break;
			}
			switch(data_type_DEM){
				case CELL_TYPE:
					d_dem = (double) ((CELL *) inrast_DEM)[col_dry];
					break;
				case FCELL_TYPE:
					d_dem = (double) ((FCELL *) inrast_DEM)[col];
					break;
				case DCELL_TYPE:
					d_dem = (double) ((DCELL *) inrast_DEM)[col];
					break;
			}
			switch(data_type_ndvi){
				case CELL_TYPE:
					d_ndvi = (double) ((CELL *) inrast_ndvi)[col];
					break;
				case FCELL_TYPE:
					d_ndvi = (double) ((FCELL *) inrast_ndvi)[col];
					break;
				case DCELL_TYPE:
					d_ndvi = (double) ((DCELL *) inrast_ndvi)[col];
					break;
			}
			switch(data_type_Rn){
				case CELL_TYPE:
					d_Rn = (double) ((CELL *) inrast_Rn)[col];
					break;
				case FCELL_TYPE:
					d_Rn = (double) ((FCELL *) inrast_Rn)[col];
					break;
				case DCELL_TYPE:
					d_Rn = (double) ((DCELL *) inrast_Rn)[col];
					break;
			}
			switch(data_type_g0){
				case CELL_TYPE:
					d_g0 = (double) ((CELL *) inrast_g0)[col];
					break;
				case FCELL_TYPE:
					d_g0 = (double) ((FCELL *) inrast_g0)[col];
					break;
				case DCELL_TYPE:
					d_g0 = (double) ((DCELL *) inrast_g0)[col];
					break;
			}
			if(G_is_d_null_value(&d_tempk)||G_is_d_null_value(&d_u2m)||
			G_is_d_null_value(&d_dem)||G_is_d_null_value(&d_ndvi)||
			G_is_d_null_value(&d_Rn)||G_is_d_null_value(&d_g0)){
				G_set_d_null_value(&outrast[col],1);
			} else {
				/* Calculate T0dem */
				d_t0dem = d_dem * 0.00627 + d_tempk;
				/* Calculate sensible heat flux */
				d = sensi_h(d_tempk_wet,d_tempk_dry,d_t0dem,d_tempk,d_ndvi,d_ndvi_max,d_dem,d_rnet_dry,d_g0_dry,d_t0dem_dry,d_u2m,d_dem_dry);
				if (zero->answer && d<0.0){
					d=0.0;
				}
				((DCELL *) outrast)[col] = d;
			}
		}
		if (G_put_d_raster_row (outfd, outrast) < 0)
			G_fatal_error (_("Cannot write to <%s>"),h0);
			
	}	
	G_free(inrast_T);
	G_free(inrast_u2);
	G_free(inrast_DEM);
	G_free(inrast_ndvi);
	G_free(inrast_Rn);
	G_free(inrast_g0);
	if(flag1->answer)
		G_free(inrast_albedo);
	G_free(outrast);
	G_close_cell (infd_T);
	G_close_cell (infd_u2);
	G_close_cell (infd_DEM);
	G_close_cell (infd_ndvi);
	G_close_cell (infd_Rn);
	G_close_cell (infd_g0);
	if(flag1->answer)
		G_close_cell (infd_albedo);
	G_close_cell (outfd);
	
        /* add command line incantation to history file */
        G_short_history(h0, "raster", &history);
        G_command_history(&history);
        G_write_history(h0, &history);

	exit(EXIT_SUCCESS);
}
