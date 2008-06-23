/****************************************************************************
 *
 * MODULE:       i.eb.h_SEBAL95
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates sensible heat flux by SEBAL iteration
 *               Delta T will be reassessed in the iterations !
 *               This has been seen in Bastiaanssen (1995).
 *
 * COPYRIGHT:    (C) 2002-2009 by the GRASS Development Team
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
/*#include <omp.h>*/


double sensi_h( int iteration, double tempk_water, double tempk_desert, double t0_dem, double tempk, double ndvi, double ndvi_max, double dem, double rnet_desert, double g0_desert, double t0_dem_desert, double u2m, double dem_desert);

int main(int argc, char *argv[])
{	
	struct Cell_head cellhd;
	char *mapset; // mapset name
	
	/* buffer for in out raster */
	void *inrast_T,*inrast_ndvi,*inrast_u2,*inrast_dem;
	void *inrast_Rn,*inrast_g0,*inrast_albedo;
	DCELL *outrast;
	
	int nrows, ncols;
	int row, col;
	int row_wet, col_wet;
	int row_dry, col_dry;
	int infd_T,infd_ndvi,infd_u2,infd_dem,infd_Rn,infd_g0,infd_albedo;
	int outfd;
	
	char *mapset_T,*mapset_ndvi,*mapset_u2,*mapset_dem;
	char *mapset_Rn,*mapset_g0,*mapset_albedo;
	char *T, *ndvi, *u2, *dem, *Rn, *g0, *albedo; 
	char *h0;
	
        struct History history;
	struct GModule *module;
	struct Option *input_T, *input_ndvi, *input_u2, *input_dem;
	struct Option *input_Rn, *input_g0, *input_albedo, *output;
	struct Option *input_row_wet, *input_col_wet;
	struct Option *input_row_dry, *input_col_dry;
	struct Option *input_iter;
	struct Flag *flag1, *flag2, *flag3, *day, *zero;
	/*******************************/
	RASTER_MAP_TYPE data_type_T;
	RASTER_MAP_TYPE data_type_ndvi;
	RASTER_MAP_TYPE data_type_u2;
	RASTER_MAP_TYPE data_type_dem;
	RASTER_MAP_TYPE data_type_Rn;
	RASTER_MAP_TYPE data_type_g0;
	RASTER_MAP_TYPE data_type_albedo;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	/*******************************/
	int iteration = 10; /*SEBAL95 loop number*/
	/********************************/
	/* Stats for dry/wet pixels	*/
	double t0dem_min=400.0,t0dem_max=200.0;
	double tempk_min=400.0,tempk_max=200.0;
	/********************************/
	double xp, yp;
	double xmin, ymin;
	double xmax, ymax;
	double stepx,stepy;
	double latitude, longitude;
	/********************************/
	G_gisinit(argv[0]);
	
	module = G_define_module();
	module->description = _("Sensible Heat Flux iteration SEBAL 95");
	
	/* Define different options */
	input_T = G_define_standard_option(G_OPT_R_INPUT);
	input_T->key	= "T";
	input_T->description = _("Name of Surface Skin Temperature input map [K]");

	input_u2 = G_define_standard_option(G_OPT_R_INPUT);
	input_u2->key	= "u2m";
	input_u2->description = _("Name of Wind Speed input map [m/s]");
		
	input_dem = G_define_standard_option(G_OPT_R_INPUT);
	input_dem->key	= "dem";
	input_dem->description = _("Name of dem input map [m a.s.l.]");
	
	input_ndvi = G_define_standard_option(G_OPT_R_INPUT);
	input_ndvi->key	= "ndvi";
	input_ndvi->description = _("Name of NDVI input map [-]");
	
	input_albedo = G_define_standard_option(G_OPT_R_INPUT);
	input_albedo->key	= "albedo";
	input_albedo->description = _("Name of Albedo input map [-]");
	
	input_Rn = G_define_standard_option(G_OPT_R_INPUT);
	input_Rn->key	= "rnet";
	input_Rn->description = _("Name of instantaneous Net Solar Radiation input map [W/m2]");
	
	input_g0 = G_define_standard_option(G_OPT_R_INPUT);
	input_g0->key	= "g0";
	input_g0->description = _("Name of instantaneous Soil Heat Flux input map [W/m2]");
	
	input_iter 		= G_define_option();
	input_iter->key		= "iteration";
	input_iter->type	= TYPE_INTEGER;
	input_iter->required 	= NO;
	input_iter->gisprompt 	= "old,value";
	input_iter->description	= _("Value of the number of SEBAL95 loops (default is 10)");
	input_iter->guisection	= _("Optional");
	
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
	output->description= _("Name of output sensible heat flux layer [W/m2]");
	output->guisection	= _("Required");
	
	/* Define the different flags */
	flag1 = G_define_flag() ;
	flag1->key         = 't' ;
	flag1->description = _("Temperature histogram check (careful!)") ;

	flag2 = G_define_flag() ;
	flag2->key         = 'a' ;
	flag2->description = _("Automatic wet/dry pixel (careful!)") ;
	
	flag3 = G_define_flag() ;
	flag3->key         = 'c' ;
	flag3->description = _("Coordinates of manual dry/wet pixels are in image projection and not row/col") ;
	
	zero = G_define_flag() ;
	zero->key         = 'z' ;
	zero->description = _("set negative evapo to zero");
	
	if (G_parser(argc, argv))
		exit(EXIT_FAILURE);
	
	/* get entered parameters */
	T	= input_T->answer;
	u2	= input_u2->answer;
	dem	= input_dem->answer;
	ndvi	= input_ndvi->answer;
	Rn	= input_Rn->answer;
	g0	= input_g0->answer;
	albedo	= input_albedo->answer;
	h0	= output->answer;

	if(input_iter->answer){
		iteration=atoi(input_iter->answer);
	}
	if(input_row_wet->answer&&input_row_dry&&
	input_col_wet->answer&&input_col_dry){
		row_wet = atoi(input_row_wet->answer);
		col_wet = atoi(input_col_wet->answer);
		row_dry = atoi(input_row_dry->answer);
		col_dry = atoi(input_col_dry->answer);
		if(flag3->answer){
			G_message("Manual wet/dry pixels in image coordinates");
			G_message("Wet Pixel=> x:%i y:%i",col_wet,row_wet);
			G_message("Dry Pixel=> x:%i y:%i",col_dry,row_dry);
		} else {
			G_message("Wet Pixel=> row:%i col:%i",row_wet,col_wet);
			G_message("Dry Pixel=> row:%i col:%i",row_dry,col_dry);
		}
	}
	/* find maps in mapset */
	mapset_T = G_find_cell2 (T, "");
	if (mapset_T == NULL)
	        G_fatal_error (_("cell file [%s] not found"), T);
	mapset_u2 = G_find_cell2 (u2, "");
	if (mapset_u2 == NULL)
	        G_fatal_error (_("cell file [%s] not found"), u2);
	mapset_dem = G_find_cell2 (dem, "");
	if (mapset_dem == NULL)
	        G_fatal_error (_("cell file [%s] not found"), dem);
	mapset_ndvi = G_find_cell2 (ndvi, "");
	if (mapset_ndvi == NULL)
	        G_fatal_error (_("cell file [%s] not found"), ndvi);
	mapset_Rn = G_find_cell2 (Rn, "");
	if (mapset_Rn == NULL)
	        G_fatal_error (_("cell file [%s] not found"), Rn);
	mapset_g0 = G_find_cell2 (g0, "");
	if (mapset_g0 == NULL)
	        G_fatal_error (_("cell file [%s] not found"), g0);
	mapset_albedo = G_find_cell2 (albedo, "");
	if (mapset_albedo == NULL)
		G_fatal_error(_("cell file [%s] not found"),albedo);
	
	/* check legal output name */ 
	if (G_legal_filename (h0) < 0)
			G_fatal_error (_("[%s] is an illegal name"), h0);
		
	/* determine the input map type (CELL/FCELL/DCELL) */
	data_type_T 	= G_raster_map_type(T, mapset_T);
	data_type_u2 	= G_raster_map_type(u2, mapset_u2);
	data_type_dem 	= G_raster_map_type(dem, mapset_dem);
	data_type_ndvi 	= G_raster_map_type(ndvi, mapset_ndvi);
	data_type_Rn 	= G_raster_map_type(Rn, mapset_Rn);
	data_type_g0 	= G_raster_map_type(g0, mapset_g0);
	data_type_albedo = G_raster_map_type(albedo, mapset_albedo);
	
	if ( (infd_T = G_open_cell_old (T, mapset_T)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), T);
	if ( (infd_u2 = G_open_cell_old (u2, mapset_u2)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),u2);
	if ( (infd_dem = G_open_cell_old (dem, mapset_dem)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),dem);
	if ( (infd_ndvi = G_open_cell_old (ndvi, mapset_ndvi)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),ndvi);
	if ( (infd_Rn = G_open_cell_old (Rn, mapset_Rn)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),Rn);
	if ( (infd_g0 = G_open_cell_old (g0, mapset_g0)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),g0);
	if((infd_albedo=G_open_cell_old (albedo,mapset_albedo)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"),albedo);
	
	if (G_get_cellhd (T, mapset_T, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), T);
	if (G_get_cellhd (u2, mapset_u2, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), u2);
	if (G_get_cellhd (dem, mapset_dem, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), dem);
	if (G_get_cellhd (ndvi, mapset_ndvi, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), ndvi);
	if (G_get_cellhd (Rn, mapset_Rn, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), Rn);
	if (G_get_cellhd (g0, mapset_g0, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), g0);
	if (G_get_cellhd (albedo, mapset_albedo, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), albedo);
	
	/* Allocate input buffer */
	inrast_T  	= G_allocate_raster_buf(data_type_T);
	inrast_u2 	= G_allocate_raster_buf(data_type_u2);
	inrast_dem 	= G_allocate_raster_buf(data_type_dem);
	inrast_ndvi 	= G_allocate_raster_buf(data_type_ndvi);
	inrast_Rn 	= G_allocate_raster_buf(data_type_Rn);
	inrast_g0 	= G_allocate_raster_buf(data_type_g0);
	inrast_albedo 	= G_allocate_raster_buf(data_type_albedo);
	
	/***************************************************/
	G_debug(3, "number of rows %d",cellhd.rows);
	/***************************************************/
	/* Setup pixel location variables */
	/***************************************************/
	stepx=cellhd.ew_res;
	stepy=cellhd.ns_res;

	xmin=cellhd.west;
	xmax=cellhd.east;
	ymin=cellhd.south;
	ymax=cellhd.north;

	nrows = G_window_rows();
	ncols = G_window_cols();
	/***************************************************/
	/* Allocate output buffer */
	/***************************************************/
	outrast = G_allocate_d_raster_buf();

	if((outfd = G_open_raster_new (h0,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),h0);

	DCELL d_ndvi; 		/* Input raster */
	DCELL d_ndvi_max = 0.0;	/* Generated here */
	/* THREAD 1 */
	/* NDVI Max */
	for (row = 0; row < nrows; row++)
	{
		G_percent (row, nrows, 2);
		if (G_get_d_raster_row (infd_ndvi, inrast_ndvi, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),ndvi);
	/*	#pragma omp for parallel default (shared) \
			shared(ncols,nrows) \
			private (col,row,d_ndvi)*/
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
	/* Pick up wet and dry pixel values */
	DCELL d_Rn; 		/* Input raster */
	DCELL d_g0; 		/* Input raster */
	DCELL d_tempk_wet;
	DCELL d_tempk_dry;
	DCELL d_Rn_dry;
	DCELL d_g0_dry;
	DCELL d_t0dem_dry;
	DCELL d_dem_dry;
	/*START Temperature minimum search */
	/* THREAD 1 */
	/*This is correcting for un-Earthly temperatures*/
	/*It finds when histogram is actually starting to pull up...*/
	int peak1, peak2, peak3;
	int i_peak1, i_peak2, i_peak3;
	int bottom1a, bottom1b;
	int bottom2a, bottom2b;
	int bottom3a, bottom3b;
	int i_bottom1a, i_bottom1b;
	int i_bottom2a, i_bottom2b;
	int i_bottom3a, i_bottom3b;
	if(flag1->answer){
		int i=0;
		int histogram[400];
		for (i=0;i<400;i++){
			histogram[i]=0;
		}
		DCELL d_T;
		/****************************/
		/* Process pixels histogram */
		for (row = 0; row < nrows; row++)
		{
			G_percent (row, nrows, 2);
			/* read input map */
			if( (G_get_raster_row(infd_T,inrast_T,row,data_type_T)) < 0){
				G_fatal_error (_("Could not read from <%s>"),T);
			}
			/*process the data */
			for (col=0; col < ncols; col++)
			{
				switch(data_type_T)
				{
					case CELL_TYPE:
						d_T = (double) ((CELL *) inrast_T)[col];
						break;
					case FCELL_TYPE:
						d_T = (double) ((FCELL *) inrast_T)[col];
						break;
					case DCELL_TYPE:
						d_T = (double) ((DCELL *) inrast_T)[col];
						break;
				}
				if(G_is_d_null_value(&d_T)){
					/*Do nothing*/
				} else {
					int temp;
					temp		= (int) d_T;
					if(temp>0){
						histogram[temp]=histogram[temp]+1.0;
					}
				}
			}
		}
		int sum=0;
		double average=0.0;
		for(i=0;i<400;i++){
			sum += histogram[i];
		}
		average = (double) sum / 400.0; 
		G_message("Histogram of Temperature map (if it has rogue values to clean)");
		//int peak1, peak2, peak3;
		//int i_peak1, i_peak2, i_peak3;
		peak1=0;
		peak2=0;
		peak3=0;
		i_peak1=0;
		i_peak2=0;
		i_peak3=0;
		//int bottom1a, bottom1b;
		//int bottom2a, bottom2b;
		//int bottom3a, bottom3b;
		//int i_bottom1a, i_bottom1b;
		//int i_bottom2a, i_bottom2b;
		//int i_bottom3a, i_bottom3b;
		bottom1a=100000;
		bottom1b=100000;
		bottom2a=100000;
		bottom2b=100000;
		bottom3a=100000;
		bottom3b=100000;
		i_bottom1a=1000;
		i_bottom1b=1000;
		i_bottom2a=1000;
		i_bottom2b=1000;
		i_bottom3a=1000;
		i_bottom3b=1000;
		for(i=0;i<400;i++){
			/* Search for highest peak of dataset (2) */
			/* Highest Peak */
			if(histogram[i]>peak2){
				peak2 = histogram[i];
				i_peak2=i;
			}
		}
		int stop=0;
		for(i=i_peak2;i>5;i--){
			if(((histogram[i]+histogram[i-1]+histogram[i-2]+histogram[i-3]+histogram[i-4])/5)<histogram[i]&&stop==0){
				bottom2a = histogram[i];
				i_bottom2a = i;
			} else if(((histogram[i]+histogram[i-1]+histogram[i-2]+histogram[i-3]+histogram[i-4])/5)>histogram[i]&&stop==0){
				/*Search for peaks of datasets (1)*/
				peak1 = histogram[i];
				i_peak1=i;
				stop=1;
			}	
		}
		stop=0;
		for(i=i_peak2;i<395;i++){
			if(((histogram[i]+histogram[i+1]+histogram[i+2]+histogram[i+3]+histogram[i+4])/5)<histogram[i]&&stop==0){
				bottom2b = histogram[i];
				i_bottom2b = i;
			} else if(((histogram[i]+histogram[i+1]+histogram[i+2]+histogram[i+3]+histogram[i+4])/5)>histogram[i]&&stop==0){
				/*Search for peaks of datasets (3)*/
				peak3 = histogram[i];
				i_peak3=i;
				stop=1;
			}	
		}
		/* First histogram lower bound */
		for(i=250;i<i_peak1;i++){
			if(histogram[i]<bottom1a){
				bottom1a = histogram[i];
				i_bottom1a = i;
			}
		}
		/* First histogram higher bound */
		for(i=i_peak2;i>i_peak1;i--){
			if(histogram[i]<=bottom1b){
				bottom1b = histogram[i];
				i_bottom1b = i;
			}
		}
		/* Third histogram lower bound */
		for(i=i_peak2;i<i_peak3;i++){
			if(histogram[i]<bottom3a){
				bottom3a = histogram[i];
				i_bottom3a = i;
			}
		}	
		/* Third histogram higher bound */
		for(i=399;i>i_peak3;i--){
			if(histogram[i]<bottom3b){
				bottom3b = histogram[i];
				i_bottom3b = i;
			}
		}	
		printf("bottom1a: [%i]=>%i\n",i_bottom1a, bottom1a);
		printf("peak1: [%i]=>%i\n",i_peak1, peak1);
		printf("bottom1b: [%i]=>%i\n",i_bottom1b, bottom1b);
		printf("bottom2a: [%i]=>%i\n",i_bottom2a, bottom2a);
		printf("peak2: [%i]=>%i\n",i_peak2, peak2);
		printf("bottom2b: [%i]=>%i\n",i_bottom2b, bottom2b);
		printf("bottom3a: [%i]=>%i\n",i_bottom3a, bottom3a);
		printf("peak3: [%i]=>%i\n",i_peak3, peak3);
		printf("bottom3b: [%i]=>%i\n",i_bottom3b, bottom3b);
	}//END OF FLAG1

	/* End of processing histogram*/
	/*******************/

	/*Process wet pixel values*/
	/* FLAG2 */
	if(flag2->answer){
		/* THREAD 3 */
		/* Process tempk min / max pixels */
	/*	#pragma omp for parallel default (shared) \
			shared(ncols,nrows) \
			private (col,row,d_albedo,d_tempk,d_dem,d_t0dem,d_Rn,d_g0)*/
		for (row = 0; row < nrows; row++){
			DCELL d_albedo;
			DCELL d_tempk;
			DCELL d_dem;
			DCELL d_t0dem;
			DCELL d_h0=100.0;//for flag 1
			DCELL d_h0_max=100.0;//for flag 1
			G_percent(row,nrows,2);
			if(G_get_raster_row(infd_albedo,inrast_albedo,row,data_type_albedo)<0)
				G_fatal_error(_("Could not read from <%s>"),albedo);
			if(G_get_raster_row(infd_T,inrast_T,row,data_type_T)<0)
				G_fatal_error(_("Could not read from <%s>"),T);
			if(G_get_raster_row(infd_dem,inrast_dem,row,data_type_dem)<0)
				G_fatal_error(_("Could not read from <%s>"),dem);
			if(G_get_raster_row(infd_Rn, inrast_Rn, row,data_type_Rn) < 0)
				G_fatal_error(_("Could not read from <%s>"),Rn);
			if(G_get_raster_row(infd_g0, inrast_g0, row,data_type_g0) < 0)
				G_fatal_error(_("Could not read from <%s>"),g0);
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
				switch(data_type_dem){
					case CELL_TYPE:
						d_dem = (double) ((CELL *) inrast_dem)[col];
						break;
					case FCELL_TYPE:
						d_dem = (double) ((FCELL *) inrast_dem)[col];
						break;
					case DCELL_TYPE:
						d_dem = (double) ((DCELL *) inrast_dem)[col];
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
				if(G_is_d_null_value(&d_albedo)||
				G_is_d_null_value(&d_tempk)||
				G_is_d_null_value(&d_dem)||
				G_is_d_null_value(&d_Rn)||
				G_is_d_null_value(&d_g0)){
					/* do nothing */ 
				}else{
					d_t0dem = d_tempk + 0.001649*d_dem;
					if(d_t0dem<=250.0||d_tempk<=250.0){
						/* do nothing */ 
					} else {
						d_h0=d_Rn-d_g0;
						if(d_t0dem<t0dem_min&&d_albedo<0.15){
							t0dem_min=d_t0dem;
							tempk_min=d_tempk;
							d_tempk_wet=d_tempk;
							col_wet=col;
							row_wet=row;
						}
						if(flag1->answer&&
						d_tempk>=(double)i_peak1-5.0&&
						d_tempk<(double)i_peak1+1.0){
							tempk_min=d_tempk;
							d_tempk_wet=d_tempk;
							col_wet=col;
							row_wet=row;
						}
						if(d_t0dem>t0dem_max){
							t0dem_max=d_t0dem;
							d_t0dem_dry=d_t0dem;
							tempk_max=d_tempk;
							d_tempk_dry=d_tempk;
							d_Rn_dry=d_Rn;
							d_g0_dry=d_g0;
							d_dem_dry=d_dem;
							col_dry=col;
							row_dry=row;
						}
						if(flag1->answer&&
						d_tempk>=(double)i_peak3-0.0&&
						d_tempk<(double)i_peak3+7.0&&
						d_h0>100.0&&d_h0>d_h0_max&&
						d_g0>10.0&&d_Rn>100.0&&
						d_albedo>0.3){
							tempk_max=d_tempk;
							d_tempk_dry=d_tempk;
							d_Rn_dry=d_Rn;
							d_g0_dry=d_g0;
							d_h0_max=d_h0;
							d_dem_dry=d_dem;
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
		G_message("tempk_wet=%f\n",d_tempk_wet);
		G_message("tempk_dry=%f\n",d_tempk_dry);
		G_message("dem_dry=%f\n",d_dem_dry);
		G_message("t0dem_dry=%f\n",d_t0dem_dry);
		G_message("rnet_dry=%f\n",d_Rn_dry);
		G_message("g0_dry=%f\n",d_g0_dry);
		G_message("h0_dry=%f\n",d_Rn_dry-d_g0_dry);
	} /* END OF FLAG2 */
	/*MPI_BARRIER*/
	
	/* MANUAL WET/DRY PIXELS */
	if(input_row_wet->answer&&input_row_dry&&
	input_col_wet->answer&&input_col_dry){
		/*DRY PIXEL*/
		if(flag3->answer){
			/*Calculate coordinates of row/col from projected ones*/
			row = ( ymax - row_dry ) / stepy ;
			col = ( col_dry - xmin ) / stepx ;
			G_message("Dry Pixel | row:%i col:%i",row,col);
		} else {
			row=row_dry;
			col=col_dry;
		}
		DCELL d_tempk;
		DCELL d_dem;
		DCELL d_t0dem;
		if(G_get_raster_row(infd_T,inrast_T,row,data_type_T)<0)
			G_fatal_error(_("Could not read from <%s>"),T);
		if(G_get_raster_row(infd_dem,inrast_dem,row,data_type_dem)<0)
			G_fatal_error(_("Could not read from <%s>"),dem);
		if(G_get_raster_row(infd_Rn, inrast_Rn, row,data_type_Rn) < 0)
			G_fatal_error(_("Could not read from <%s>"),Rn);
		if(G_get_raster_row(infd_g0, inrast_g0, row,data_type_g0) < 0)
			G_fatal_error(_("Could not read from <%s>"),g0);
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
		switch(data_type_dem){
			case CELL_TYPE:
				d_dem = (double) ((CELL *) inrast_dem)[col];
				break;
			case FCELL_TYPE:
				d_dem = (double) ((FCELL *) inrast_dem)[col];
				break;
			case DCELL_TYPE:
				d_dem = (double) ((DCELL *) inrast_dem)[col];
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
		d_t0dem = d_tempk + 0.001649*d_dem;
		d_t0dem_dry=d_t0dem;
		d_tempk_dry=d_tempk;
		d_Rn_dry=d_Rn;
		d_g0_dry=d_g0;
		d_dem_dry=d_dem;
		/*WET PIXEL*/
		if(flag3->answer){
			/*Calculate coordinates of row/col from projected ones*/
			row = ( ymax - row_wet ) / stepy ;
			col = ( col_wet - xmin ) / stepx ;
			G_message("Wet Pixel | row:%i col:%i",row,col);
		} else {
			row=row_wet;
			col=col_wet;
		}
		if(G_get_raster_row(infd_T,inrast_T,row,data_type_T)<0)
			G_fatal_error(_("Could not read from <%s>"),T);
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
		d_tempk_wet=d_tempk;
	}
	/* END OF MANUAL WET/DRY PIXELS */

	for (row = 0; row < nrows; row++)
	{	
		DCELL d_albedo;
		DCELL d_tempk;
		DCELL d_dem;
		DCELL d_t0dem;
		DCELL d_u2m; 	/* Input raster */
		DCELL d;	/* Output pixel */
		G_percent(row,nrows,2);
		/* read a line input maps into buffers*/	
		if(G_get_raster_row(infd_albedo,inrast_albedo,row,data_type_albedo)<0)
			G_fatal_error(_("Could not read from <%s>"),albedo);
		if(G_get_raster_row(infd_T,inrast_T,row,data_type_T)<0)
			G_fatal_error(_("Could not read from <%s>"),T);
		if(G_get_raster_row(infd_u2,inrast_u2,row,data_type_u2) < 0)
			G_fatal_error(_("Could not read from <%s>"),u2);
		if(G_get_raster_row(infd_dem,inrast_dem,row,data_type_dem)<0)
			G_fatal_error(_("Could not read from <%s>"),dem);
		if(G_get_raster_row(infd_ndvi,inrast_ndvi,row,data_type_ndvi) < 0)
			G_fatal_error(_("Could not read from <%s>"),ndvi);
		if(G_get_raster_row(infd_Rn,inrast_Rn,row,data_type_Rn) < 0)
			G_fatal_error(_("Could not read from <%s>"),Rn);
		if(G_get_raster_row(infd_g0,inrast_g0,row,data_type_g0) < 0)
			G_fatal_error(_("Could not read from <%s>"),g0);
		/* read every cell in the line buffers */
		for (col=0; col < ncols; col++){
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
			switch(data_type_dem){
				case CELL_TYPE:
					d_dem = (double) ((CELL *) inrast_dem)[col];
					break;
				case FCELL_TYPE:
					d_dem = (double) ((FCELL *) inrast_dem)[col];
					break;
				case DCELL_TYPE:
					d_dem = (double) ((DCELL *) inrast_dem)[col];
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
			if(G_is_d_null_value(&d_tempk)||
			G_is_d_null_value(&d_u2m)||
			G_is_d_null_value(&d_dem)||
			G_is_d_null_value(&d_ndvi)||
			G_is_d_null_value(&d_Rn)||
			G_is_d_null_value(&d_g0)||
			d_g0<0.0||d_Rn<0.0||
			d_dem<=-100.0||d_dem>9000.0||
			d_tempk<200.0){
				G_set_d_null_value(&outrast[col],1);
			} else {
				/* Albedo < 0*/
				if(d_albedo<0.01){
					d_albedo=0.01;
				}
				/* Calculate T0dem */
				d_t0dem = (double)d_tempk + 0.001649*(double)d_dem;
			/*	G_message("**InLoop d_t0dem=%5.3f",d_t0dem);
				G_message(" d_dem=%5.3f",d_dem);
				G_message(" d_tempk=%5.3f",d_tempk);
				G_message(" d_albedo=%5.3f",d_albedo);
				G_message(" d_Rn=%5.3f",d_Rn);
				G_message(" d_g0=%5.3f",d_g0);
				G_message(" d_ndvi=%5.3f",d_ndvi);
				G_message(" d_u2m=%5.3f",d_u2m);
			*/	/* Calculate sensible heat flux */
				d = sensi_h(iteration,d_tempk_wet,d_tempk_dry,d_t0dem,d_tempk,d_ndvi,d_ndvi_max,d_dem,d_Rn_dry,d_g0_dry,d_t0dem_dry,d_u2m,d_dem_dry);
		//		G_message(" d_h0=%5.3f",d);
				if (zero->answer && d<0.0){
					d=0.0;
				}
				outrast[col] = d;
			}
		}
		if (G_put_d_raster_row (outfd, outrast) < 0)
			G_fatal_error (_("Cannot write to <%s>"),h0);
	}	
	G_free(inrast_T);
	G_close_cell (infd_T);
	G_free(inrast_u2);
	G_close_cell (infd_u2);
	G_free(inrast_dem);
	G_close_cell (infd_dem);
	G_free(inrast_ndvi);
	G_close_cell (infd_ndvi);
	G_free(inrast_Rn);
	G_close_cell (infd_Rn);
	G_free(inrast_g0);
	G_close_cell (infd_g0);
	G_free(inrast_albedo);
	G_close_cell (infd_albedo);
	
	G_free(outrast);
	G_close_cell (outfd);
        /* add command line incantation to history file */
        G_short_history(h0, "raster", &history);
        G_command_history(&history);
        G_write_history(h0, &history);

	exit(EXIT_SUCCESS);
}
