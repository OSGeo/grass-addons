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
	struct Option *input1, *input2, *input3, *output1;
	
	struct Flag *flag1;	
	struct History history; //metadata
	
	struct pj_info iproj;
	struct pj_info oproj;
	/************************************/
	/* FMEO Declarations*****************/
	char 	prcp_name[MAXFILES];// input first time-series raster files names
	char 	tmax_name[MAXFILES];// input second time_series raster files names
	char 	tmin_name[MAXFILES];// input third time_series raster files names
	char 	*result1; 	//output file base name
	char 	*result_lat_long; 	//output file name
	//File Descriptors
	int 	infd_prcp[MAXFILES], infd_tmax[MAXFILES], infd_tmin[MAXFILES];
	
	int 	i=0,j=0;
	double 	xp, yp;
	double 	xmin, ymin;
	double 	xmax, ymax;
	double 	stepx,stepy;
	double 	latitude, longitude;

	void 			*inrast_prcp[MAXFILES];
	void 			*inrast_tmax[MAXFILES];
	void 			*inrast_tmin[MAXFILES];
	RASTER_MAP_TYPE 	data_type_inrast_prcp[MAXFILES];
	RASTER_MAP_TYPE 	data_type_inrast_tmax[MAXFILES];
	RASTER_MAP_TYPE 	data_type_inrast_tmin[MAXFILES];

	FILE	*f; 		// output ascii file
	int 	grid_count; 	// grid cell count
	double	*prcp[MAXFILES];	// Precipitation data
	double	*tmax[MAXFILES];	// Tmax data
	double	*tmin[MAXFILES];	// Tmin data
	char 	**prcp_ptr;	// pointer to get the input1->answers
	char 	**tmax_ptr;	// pointer to get the input2->answers
	char 	**tmin_ptr;	// pointer to get the input3->answers
	int	nfiles; 	// count number of input files
	char	**test, **ptr;	// test number of input files
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("VIC, hydrology, precipitation, Tmax, Tmin");
	module->description = _("creates a meteorological ascii file \
			from 3 time series maps: precipitation, Tmax and Tmin.");

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
	
	output1 = G_define_option() ;
	output1->key      	=_("output");
	output1->description	=_("Base Name of the output vic meteorological ascii files");
	output1->answer     	=_("data_");

	flag1 = G_define_flag() ;
	flag1->key		= 'a';
	flag1->description	=_("append data if file already exists \
				(useful if adding additional year of data)");
	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	result1 	 	= output1->answer;
	/************************************************/
	/* LOADING TMAX TIME SERIES MAPS 		*/
	test = input1->answers;
	for (ptr = test, nfiles = 0; *ptr != NULL; ptr++, nfiles++)
		;
	if (nfiles > MAXFILES)
		G_fatal_error(_("Too many input files, change MAX_FILES and recompile."));
	prcp_ptr = input2->answers;
	for(; *prcp_ptr != NULL; prcp_ptr++){
		strcpy(prcp_name,*prcp_ptr);
	}
	for(i=0;i<nfiles+1;i++){
		mapset = G_find_cell2(&prcp_name[i], "");
		if (mapset == NULL) {
			G_fatal_error(_("cell file [%s] not found"), prcp_name[i]);
		}
		data_type_inrast_prcp[i] = G_raster_map_type(&prcp_name[i],mapset);
		if ((infd_prcp[i] = G_open_cell_old (&prcp_name[i],mapset)) < 0)
			G_fatal_error (_("Cannot open cell file [%s]"), prcp_name[i]);
		if (G_get_cellhd (&prcp_name[i], mapset, &cellhd) < 0)
			G_fatal_error (_("Cannot read file header of [%s])"), prcp_name[i]);
		inrast_prcp[i] = G_allocate_raster_buf(data_type_inrast_prcp[i]);
	}
	/************************************************/
	/* LOADING TMAX TIME SERIES MAPS 		*/
	test = input2->answers;
	for (ptr = test, nfiles = 0; *ptr != NULL; ptr++, nfiles++)
		;
	if (nfiles > MAXFILES)
		G_fatal_error(_("Too many input files, change MAX_FILES and recompile."));
	tmax_ptr = input2->answers;
	for(; *tmax_ptr != NULL; tmax_ptr++){
		strcpy(tmax_name,*tmax_ptr);
	}
	for(i=0;i<nfiles+1;i++){
		mapset = G_find_cell2(&tmax_name[i], "");
		if (mapset == NULL) {
			G_fatal_error(_("cell file [%s] not found"), tmax_name[i]);
		}
		data_type_inrast_tmax[i] = G_raster_map_type(&tmax_name[i],mapset);
		if ((infd_tmax[i] = G_open_cell_old (&tmax_name[i],mapset)) < 0)
			G_fatal_error (_("Cannot open cell file [%s]"), tmax_name[i]);
		if (G_get_cellhd (&tmax_name[i], mapset, &cellhd) < 0)
			G_fatal_error (_("Cannot read file header of [%s])"), tmax_name[i]);
		inrast_tmax[i] = G_allocate_raster_buf(data_type_inrast_tmax[i]);
	}
	/************************************************/
	/* LOADING TMIN TIME SERIES MAPS 		*/
	test = input3->answers;
	for (ptr = test, nfiles = 0; *ptr != NULL; ptr++, nfiles++)
		;
	if (nfiles > MAXFILES)
		G_fatal_error(_("Too many input files, change MAX_FILES and recompile."));
	tmin_ptr = input3->answers;
	for(; *tmin_ptr != NULL; tmin_ptr++){
		strcpy(tmin_name,*tmin_ptr);
	}
	for(i=0;i<nfiles+1;i++){
		mapset = G_find_cell2(&tmin_name[i], "");
		if (mapset == NULL) {
			G_fatal_error(_("cell file [%s] not found"), tmin_name[i]);
		}
		data_type_inrast_tmin[i] = G_raster_map_type(&tmin_name[i],mapset);
		if ((infd_tmin[i] = G_open_cell_old (&tmin_name[i],mapset)) < 0)
			G_fatal_error (_("Cannot open cell file [%s]"), tmin_name[i]);
		if (G_get_cellhd (&tmin_name[i], mapset, &cellhd) < 0)
			G_fatal_error (_("Cannot read file header of [%s])"), tmin_name[i]);
		inrast_tmax[i] = G_allocate_raster_buf(data_type_inrast_tmin[i]);
	}
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
	
	/*Initialize grid cell count*/
	grid_count = 1;
	
	for (row = 0; row < nrows; row++){
		DCELL d_prcp[MAXFILES];
		DCELL d_tmax[MAXFILES];
		DCELL d_tmin[MAXFILES];
		G_percent(row,nrows,2);
		for(i=0;i<nfiles;i++){
			if(G_get_raster_row(infd_prcp[i],inrast_prcp[i],row,data_type_inrast_prcp[i])<0)
				G_fatal_error(_("Could not read from <%s>"),prcp_name[i]);
		}
		for(i=0;i<nfiles;i++){
			if(G_get_raster_row(infd_tmax[i],inrast_tmax[i],row,data_type_inrast_tmax[i])<0)
				G_fatal_error(_("Could not read from <%s>"),tmax_name[i]);
		}
		for(i=0;i<nfiles;i++){
			if(G_get_raster_row(infd_tmin[i],inrast_tmin[i],row,data_type_inrast_tmin[i])<0)
				G_fatal_error(_("Could not read from <%s>"),tmin_name[i]);
		}
		for (col=0; col < ncols; col++){
			/*Extract prcp time series data*/
			for(i=0;i<nfiles;i++){
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
			}
			/*Extract tmax time series data*/
			for(i=0;i<nfiles;i++){
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
			}
			/*Extract tmin time series data*/
			for(i=0;i<nfiles;i++){
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
			/* Make the output .dat file name */
			sprintf(result_lat_long,"%s%s%s%s%s",result1,"_",latitude,"_",longitude,".dat");	
			/*Open new ascii file*/
			if (flag1->answer){
				/*Initialize grid cell in append mode*/
				f=fopen(result_lat_long,"a");
			} else {
				/*Initialize grid cell in new file mode*/
				f=fopen(result_lat_long,"w");
			}
			/* Force clearing of file name var */
			result_lat_long=NULL;

			/*Print data into the file maps data if available*/
			for(i=0;i<nfiles;i++){
				fprintf(f,"%.2f  %.2f  %.2f\n", prcp[i], tmax[i], tmin[i]);
			}
			fclose(f);
			grid_count=grid_count+1;
		}
	}
	G_message(_("Created %d VIC meteorological files"),grid_count);
	for(i=0;i<nfiles;i++){
		G_free (inrast_prcp[i]);
		G_close_cell (infd_prcp[i]);
		G_free (inrast_tmax[i]);
		G_close_cell (infd_tmax[i]);
		G_free (inrast_tmin[i]);
		G_close_cell (infd_tmin[i]);
	}
	exit(EXIT_SUCCESS);
}

