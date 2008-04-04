/****************************************************************************
 *
 * MODULE:       r.out.vic_met
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Creates a VIC meteorological input file.
 * 		 Three time series of GIS data are needed:
 * 		 Precipitation (mm/d), Tmax(C) and Tmin(C)
 * 		 
 * COPYRIGHT:    (C) 2008 by the GRASS Development Team
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
#include <grass/gprojects.h>
#include <grass/glocale.h>

/************************/
/* daily one year is: 	*/
#define MAXFILES 366

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	int not_ll=0;//if proj is not lat/long, it will be 1.
	struct GModule *module;
	struct Option *input1, *input2, *input3, *input4;
	struct Option *output1, *output2;
	
	struct Flag *flag1;	
	struct History history; //metadata
	
	struct pj_info iproj;
	struct pj_info oproj;
	/************************************/
	/* FMEO Declarations*****************/
	char 	*prcp_name;// input first time-series raster files names
	char 	*tmax_name;// input second time_series raster files names
	char 	*tmin_name;// input third time_series raster files names
	char 	*result1; 	//output file base name
	char 	*result2; 	//output Soil file name
	char 	result_lat_long[50]; 	//output file name
	//File Descriptors
	int 	infd_prcp[MAXFILES], infd_tmax[MAXFILES], infd_tmin[MAXFILES];
	int	infd;
	
	int 	i=0,j=0;
	double 	xp, yp;
	double 	xmin, ymin;
	double 	xmax, ymax;
	double 	stepx,stepy;
	double 	latitude, longitude;

	void 			*inrast_prcp[MAXFILES];
	void 			*inrast_tmax[MAXFILES];
	void 			*inrast_tmin[MAXFILES];
	void 			*inrast_elevation;
	RASTER_MAP_TYPE 	data_type_inrast_prcp[MAXFILES];
	RASTER_MAP_TYPE 	data_type_inrast_tmax[MAXFILES];
	RASTER_MAP_TYPE 	data_type_inrast_tmin[MAXFILES];
	RASTER_MAP_TYPE 	data_type_inrast_elevation;

	FILE	*f; 		// output ascii file
	int 	grid_count; 	// grid cell count
	double	prcp[MAXFILES];	// Precipitation data
	double	tmax[MAXFILES];	// Tmax data
	double	tmin[MAXFILES];	// Tmin data
	char 	**prcp_ptr;	// pointer to get the input1->answers
	char 	**tmax_ptr;	// pointer to get the input2->answers
	char 	**tmin_ptr;	// pointer to get the input3->answers
	int	nfiles1, nfiles2, nfiles3, nfiles_shortest;// count no. input files
	char	**test1, **test2, **test3; // test number of input files
	char	**ptr1, **ptr2, **ptr3;	// test number of input files
	/****************************************/
	/* Elevation map 			*/
	char	*in;
	FILE	*g; 		// output soil ascii file
	int 	process; 	// process grid cell switch
	char 	*dummy_data1; 	// dummy data part 1
	char 	*dummy_data2; 	// dummy data part 2
	double	elevation;	// average evevation of grid cell
	/************************************/

	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("VIC, hydrology, precipitation, Tmax, Tmin, soil");
	module->description = _("creates a meteorological ascii file for each non-null cell from 3 time series maps: precipitation, Tmax and Tmin. Also creates a dummy soil file from elevation.");

	/* Define the different options */
	input1 = G_define_standard_option(G_OPT_R_INPUT) ;
	input1->key	   = _("prcp");
	input1->multiple   = YES;
	input1->description=_("Names of the precipitation input maps");

	input2 = G_define_standard_option(G_OPT_R_INPUT) ;
	input2->key	   = _("tmax");
	input2->multiple   = YES;
	input2->description=_("Names of the Tmax input maps");

	input3 = G_define_standard_option(G_OPT_R_INPUT) ;
	input3->key	   = _("tmin");
	input3->multiple   = YES;
	input3->description=_("Names of the Tmin input maps");
	
	input4 = G_define_standard_option(G_OPT_R_INPUT) ;
	input4->key	   = _("dem");
	input4->description=_("Name of the elevation input map");
	
	output1 = G_define_option();
	output1->key      	=_("output");
	output1->description	=_("Base Name of the output vic meteorological ascii files");
	output1->answer     	=_("data_");

	output2 = G_define_option() ;
	output2->key        =_("output_soil");
	output2->description=_("Name of the output vic soil ascii file");
	output2->answer     =_("vic_soil.asc");

	flag1 = G_define_flag() ;
	flag1->key		= 'a';
	flag1->description	=_("append meteorological data if file already exists (useful if adding additional year of data)");
	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	result1 	= output1->answer;
	in		= input4->answer;
	result2 	= output2->answer;
	/************************************************/
	/* LOADING TMAX TIME SERIES MAPS 		*/
	test1 = input1->answers;
	for (ptr1 = test1, nfiles1 = 0; *ptr1 != NULL; ptr1++, nfiles1++)
		;
	if (nfiles1 > MAXFILES){
		G_fatal_error(_("Too many inputs1, change MAXFILES, recompile."));
	}
	prcp_ptr = input1->answers;
	i=0;
	for(; *prcp_ptr != NULL; prcp_ptr++){
		prcp_name= *prcp_ptr;
		mapset = G_find_cell2(prcp_name, "");
		if (mapset == NULL) 
			G_fatal_error(_("cell file [%s] not found"), prcp_name);
		data_type_inrast_prcp[i] = G_raster_map_type(prcp_name,mapset);
		if ((infd_prcp[i] = G_open_cell_old (prcp_name,mapset)) < 0)
			G_fatal_error (_("Cannot open cell file [%s]"), prcp_name);
		if (G_get_cellhd (prcp_name, mapset, &cellhd) < 0)
			G_fatal_error (_("Cannot read file header of [%s])"), prcp_name);
		inrast_prcp[i] = G_allocate_raster_buf(data_type_inrast_prcp[i]);
		i++;
	}
	nfiles1=i;
	/************************************************/
	/* LOADING TMAX TIME SERIES MAPS 		*/
	test2 = input2->answers;
	for (ptr2 = test2, nfiles2 = 0; *ptr2 != NULL; ptr2++, nfiles2++)
		;
	if (nfiles2 > MAXFILES){
		G_fatal_error(_("Too many inputs2, change MAXFILES, recompile."));
	}
	tmax_ptr = input2->answers;
	i=0;
	for(; *tmax_ptr != NULL; tmax_ptr++){
		tmax_name = *tmax_ptr;
		mapset = G_find_cell2(tmax_name, "");
		if (mapset == NULL)
			G_fatal_error(_("cell file [%s] not found"), tmax_name);
		data_type_inrast_tmax[i] = G_raster_map_type(tmax_name,mapset);
		if ((infd_tmax[i] = G_open_cell_old (tmax_name,mapset)) < 0)
			G_fatal_error (_("Cannot open cell file [%s]"),tmax_name);
		if (G_get_cellhd (tmax_name, mapset, &cellhd) < 0)
			G_fatal_error (_("Cannot read file header of [%s])"), tmax_name);
		inrast_tmax[i] = G_allocate_raster_buf(data_type_inrast_tmax[i]);
		i++;
	}
	nfiles2=i;
	/************************************************/
	/* LOADING TMIN TIME SERIES MAPS 		*/
	test3 = input3->answers;
	for (ptr3 = test3, nfiles3 = 0; *ptr3 != NULL; ptr3++, nfiles3++)
		;
	if (nfiles3 > MAXFILES){
		G_fatal_error(_("Too many inputs3, change MAXFILES, recompile."));
	}
	tmin_ptr = input3->answers;
	i=0;
	for(; *tmin_ptr != NULL; tmin_ptr++){
		tmin_name = *tmin_ptr;
		mapset = G_find_cell2(tmin_name, "");
		if (mapset == NULL)
			G_fatal_error(_("cell file [%s] not found"), tmin_name);
		data_type_inrast_tmin[i] = G_raster_map_type(tmin_name,mapset);
		if ((infd_tmin[i] = G_open_cell_old (tmin_name,mapset)) < 0)
			G_fatal_error (_("Cannot open cell file [%s]"), tmin_name);
		if (G_get_cellhd (tmin_name, mapset, &cellhd) < 0)
			G_fatal_error (_("Cannot read file header of [%s])"), tmin_name);
		inrast_tmin[i] = G_allocate_raster_buf(data_type_inrast_tmin[i]);
		i++;
	}
	nfiles3=i;
	/************************************************/
	if(nfiles1<=nfiles2||nfiles1<=nfiles3){
		nfiles_shortest = nfiles1;
	} else if (nfiles2<=nfiles1||nfiles2<=nfiles3){
		nfiles_shortest = nfiles2;
	} else {
		nfiles_shortest = nfiles3;
	}
	/************************************************/
	/* Load Elevation file				*/
	mapset = G_find_cell2(in, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), in);
	}
	data_type_inrast_elevation = G_raster_map_type(in,mapset);
	if ( (infd = G_open_cell_old (in,mapset)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), in);
	if (G_get_cellhd (in, mapset, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s])"), in);
	inrast_elevation = G_allocate_raster_buf(data_type_inrast_elevation);
	/***************************************************/
	G_debug(3, "number of rows %d",cellhd.rows);

	stepx=cellhd.ew_res;
	stepy=cellhd.ns_res;

	xmin=cellhd.west;
	xmax=cellhd.east;
	ymin=cellhd.south;
	ymax=cellhd.north;

	nrows = G_window_rows();
	ncols = G_window_cols();

	//Shamelessly stolen from r.sun !!!!	
	/* Set up parameters for projection to lat/long if necessary */
	if ((G_projection() != PROJECTION_LL)) {
		not_ll=1;
		struct Key_Value *in_proj_info, *in_unit_info;
		if ((in_proj_info = G_get_projinfo()) == NULL)
			G_fatal_error(_("Can't get projection info of current location"));
		if ((in_unit_info = G_get_projunits()) == NULL)
			G_fatal_error(_("Can't get projection units of current location"));
		if (pj_get_kv(&iproj, in_proj_info, in_unit_info) < 0)
			G_fatal_error(_("Can't get projection key values of current location"));
		G_free_key_value(in_proj_info);
		G_free_key_value(in_unit_info);
		/* Set output projection to latlong w/ same ellipsoid */
		oproj.zone = 0;
		oproj.meters = 1.;
		sprintf(oproj.proj, "ll");
		if ((oproj.pj = pj_latlong_from_proj(iproj.pj)) == NULL)
			G_fatal_error(_("Unable to set up lat/long projection parameters"));
	}//End of stolen from r.sun :P

	/*Initialize grid cell process switch*/
	g=fopen(result2,"w");
	/*Initialize grid cell process switch*/
	/*If =1 then process, if =0 then skip*/
	process = 1; 

	/*Initialize grid cell count*/
	grid_count = 1;
	/*Initialize output file */
	fprintf(g,"#RUN\tGRID\tLAT\tLNG\tINFILT\tDs\tDs_MAX\tWs\tC\tEXPT_1\tEXPT_2\tEXPT_3\tKsat_1\tKsat_2\tKsat_3\tPHI_1\tPHI_2\tPHI_3\tMOIST_1\tMOIST_2\tMOIST_3\tELEV\tDEPTH_1\tDEPTH_2\tDEPTH_3\tAVG_T\tDP\tBUBLE1\tBUBLE2\tBUBLE3\tQUARZ1\tQUARZ2\tQUARZ3\tBULKDN1\tBULKDN2\tBULKDN3\tPARTDN1\tPARTDN2\tPARTDN3\tOFF_GMT\tWcrFT1\tWcrFT2\tWcrFT3\tWpFT1\tWpFT2\tWpFT3\tZ0_SOIL\tZ0_SNOW\tPRCP\tRESM1\tRESM2\tRESM3\tFS_ACTV\tJULY_TAVG\n");

	/*Initialize dummy data*/
	dummy_data1 = "0.010\t1.e-4\t3.05\t0.93\t2\t4.0\t4.0\t4.0\t250.0\t250.0\t250.0\t-999\t-999\t-999\t0.4\t0.4\t0.4";
	dummy_data2 = "0.1\t6.90\t2.000\t14.0\t4.0\t75.0\t75.0\t75.0\t0.24\t0.24\t0.24\t1306\t1367\t1367\t2650\t2650\t2650\t-6\t0.330\t0.330\t0.330\t0.133\t0.133\t0.133\t0.001\t0.010\t500\t0.02\t0.02\t0.02\t1\t18.665\n";
		
	for (row = 0; row < nrows; row++){
		DCELL d_prcp[MAXFILES];
		DCELL d_tmax[MAXFILES];
		DCELL d_tmin[MAXFILES];
		DCELL d_elevation;
		G_percent(row,nrows,2);
		for(i=0;i<nfiles_shortest;i++){
			if(G_get_raster_row(infd_prcp[i],inrast_prcp[i],row,data_type_inrast_prcp[i])<0)
				G_fatal_error(_("Could not read from prcp<%d>"),i+1);
			if(G_get_raster_row(infd_tmax[i],inrast_tmax[i],row,data_type_inrast_tmax[i])<0)
				G_fatal_error(_("Could not read from tmax<%d>"),i+1);
			if(G_get_raster_row(infd_tmin[i],inrast_tmin[i],row,data_type_inrast_tmin[i])<0)
				G_fatal_error(_("Could not read from tmin<%d>"),i+1);
		}
		if(G_get_raster_row(infd,inrast_elevation,row,data_type_inrast_elevation)<0)
			G_fatal_error(_("Could not read from <%s>"),in);

		for (col=0; col < ncols; col++){
			for(i=0;i<nfiles_shortest;i++){
				/*Extract prcp time series data*/
				switch(data_type_inrast_prcp[i]){
					case CELL_TYPE:
						d_prcp[i]= (double) ((CELL *) inrast_prcp[i])[col];
						break;
					case FCELL_TYPE:
						d_prcp[i]= (double) ((FCELL *) inrast_prcp[i])[col];
						break;
					case DCELL_TYPE:
						d_prcp[i]= (double) ((DCELL *) inrast_prcp[i])[col];
						break;
				}
				/*Extract tmax time series data*/
				switch(data_type_inrast_tmax[i]){
					case CELL_TYPE:
						d_tmax[i]= (double) ((CELL *) inrast_tmax[i])[col];
						break;
					case FCELL_TYPE:
						d_tmax[i]= (double) ((FCELL *) inrast_tmax[i])[col];
						break;
					case DCELL_TYPE:
						d_tmax[i]= (double) ((DCELL *) inrast_tmax[i])[col];
						break;
				}
				/*Extract tmin time series data*/
				switch(data_type_inrast_tmin[i]){
					case CELL_TYPE:
						d_tmin[i]= (double) ((CELL *) inrast_tmin[i])[col];
						break;
					case FCELL_TYPE:
						d_tmin[i]= (double) ((FCELL *) inrast_tmin[i])[col];
						break;
					case DCELL_TYPE:
						d_tmin[i]= (double) ((DCELL *) inrast_tmin[i])[col];
						break;
				}
			}
			/*Extract elevation data*/
			switch(data_type_inrast_elevation){
				case CELL_TYPE:
					d_elevation = (double) ((CELL *) inrast_elevation)[col];
					break;
				case FCELL_TYPE:
					d_elevation = (double) ((FCELL *) inrast_elevation)[col];
					break;
				case DCELL_TYPE:
					d_elevation = ((DCELL *) inrast_elevation)[col];
					break;
			}
			/*Extract lat/long data*/
			latitude = ymax - ( row * stepy );
			longitude = xmin + ( col * stepx );
			if(not_ll){
				if (pj_do_proj(&longitude, &latitude, &iproj, &oproj) < 0) {
				    G_fatal_error(_("Error in pj_do_proj"));
				}
			}else{
				//Do nothing
			}
			if(G_is_d_null_value(&prcp[0])||
			G_is_d_null_value(&d_tmax[0])||
			G_is_d_null_value(&d_tmin[0])||
			G_is_d_null_value(&d_elevation)){
				/* Do nothing */
			} else {
				/* Make the output .dat file name */
				sprintf(result_lat_long,"%s%.4f%s%.4f",result1,latitude,"_",longitude);	
				/*Open new ascii file*/
				if (flag1->answer){
					/*Initialize grid cell in append mode*/
					f=fopen(result_lat_long,"a");
				} else {
					/*Initialize grid cell in new file mode*/
					f=fopen(result_lat_long,"w");
				}
				/*Print data into the file maps data if available*/
				for(i=0;i<nfiles_shortest;i++){
					fprintf(f,"%.2f  %.2f  %.2f\n", d_prcp[i], d_tmax[i], d_tmin[i]);
				}
				fclose(f);
				/*Print to soil ascii file*/
				fprintf(g,"%d\t%d\t%6.3f\t%7.3f\t%s\t%7.2f\t%s\n", process, grid_count, latitude, longitude, dummy_data1, d_elevation, dummy_data2);
				grid_count=grid_count+1;
			}
		}
	}
	G_message(_("Created %d VIC meteorological files"),grid_count);
	G_message(_("Created %d VIC grid cells soil definitions"),grid_count);
	for(i=0;i<nfiles1;i++){
		G_free (inrast_prcp[i]);
		G_close_cell (infd_prcp[i]);
	}
	for(i=0;i<nfiles2;i++){
		G_free (inrast_tmax[i]);
		G_close_cell (infd_tmax[i]);
	}
	for(i=0;i<nfiles3;i++){
		G_free (inrast_tmin[i]);
		G_close_cell (infd_tmin[i]);
	}
	G_free (inrast_elevation);
	G_close_cell (infd);
	fclose(g);
	exit(EXIT_SUCCESS);
}

