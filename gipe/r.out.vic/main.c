
/****************************************************************************
 *
 * MODULE:       r.out.vic
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Creates VIC input files:
 * 		 1 - Meteorological: 
 * 			Three time series of GIS data are needed:
 * 		 	Precipitation (mm/d), Tmax(C) and Tmin(C)
 * 		 2 - Vegetation:
 * 		 	Filling only Land cover class, with only one class,
 * 			 and one standard root system.
 * 			 Option to add monthly LAI (12 maps).
 * 		 3 - Soil:
 *		 	Barely complete, it takes elevation data & lat/long,
 *		 	the rest is filled up with dummy soil data.
 *		 4 - Routing file from GRASS flow direction file:
 *		 	Direct AGNPS or flag for r.watershed format
 *		 	Recoding to rout input file for VIC post-processing
 *		 	of hydrological surface runoff flow.
 *		 	http://www.hydro.washington.edu/Lettenmaier/ 
 *		 	Models/VIC/Documentation/Bernt/
 *		 	rout/mainframe_rout1.htm
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
    /* daily one year is:   */ 
#define MAXFILES 366
    

/************************/ 
    /* for vegeation:       */ 
int veglib(char *filename);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    int not_ll = 0;		/*if proj is not lat/long, it will be 1. */

    struct GModule *module;

    struct Option *input1, *input2, *input3, *input4;

    struct Option *input5, *input6, *input7;

    struct Option *output1, *output2, *output3, *output4, *output5;

    struct Flag *flag1, *flag2;

    struct History history;	/*metadata */

    struct pj_info iproj;

    struct pj_info oproj;

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *prcp_name;		/* input first time-series raster files names */

    char *tmax_name;		/* input second time_series raster files names */

    char *tmin_name;		/* input third time_series raster files names */

    char *landcover_name;	/* input raster name */

    char lai_name[12];		/* input monthly raster files name */

    char *fdir_name;		/* input flow direction raster name */

    char *result1;		/*output file base name */

    char *result2;		/*output Soil file name */

    char *result3;		/*output Veg file name */

    char *result4;		/*output flow direction file name */

    char result_lat_long[50];	/*output file name */

    
	/*File Descriptors */ 
    int infd_prcp[MAXFILES], infd_tmax[MAXFILES], infd_tmin[MAXFILES];

    int infd;

    int infd_landcover, infd_lai[12], infd_fdir;

    int i = 0, j = 0;

    double xp, yp;

    double xmin, ymin;

    double xmax, ymax;

    double stepx, stepy;

    double latitude, longitude;

    void *inrast_prcp[MAXFILES];

    void *inrast_tmax[MAXFILES];

    void *inrast_tmin[MAXFILES];

    void *inrast_elevation;

    void *inrast_landcover;

    void *inrast_lai[12];

    void *inrast_fdir;

    RASTER_MAP_TYPE data_type_inrast_prcp[MAXFILES];
    RASTER_MAP_TYPE data_type_inrast_tmax[MAXFILES];
    RASTER_MAP_TYPE data_type_inrast_tmin[MAXFILES];
    RASTER_MAP_TYPE data_type_inrast_elevation;
    RASTER_MAP_TYPE data_type_inrast_landcover;
    RASTER_MAP_TYPE data_type_inrast_lai[12];
    RASTER_MAP_TYPE data_type_inrast_fdir;
    

	/****************************************/ 
	/* Meteorological maps                  */ 
	FILE * f;		/* output ascii file */
    int grid_count;		/* grid cell count */

    double prcp[MAXFILES];	/* Precipitation data */

    double tmax[MAXFILES];	/* Tmax data */

    double tmin[MAXFILES];	/* Tmin data */

    char **prcp_ptr;		/* pointer to get the input1->answers */

    char **tmax_ptr;		/* pointer to get the input2->answers */

    char **tmin_ptr;		/* pointer to get the input3->answers */

    int nfiles1, nfiles2, nfiles3, nfiles_shortest;	/* count no. input files */

    char **test1, **test2, **test3;	/* test number of input files */

    char **ptr1, **ptr2, **ptr3;	/* test number of input files */

    

	/****************************************/ 
	/* Elevation map                        */ 
    char *in;

    FILE * g;			/* output soil ascii file */
    int process;		/* process grid cell switch */

    char *dummy_data1;		/* dummy data part 1 */

    char *dummy_data2;		/* dummy data part 2 */

    double elevation;		/* average evevation of grid cell */

    

	/****************************************/ 
	/* Vegetation map                       */ 
	FILE * h;		/* output ascii file */
    char *dummy_data3;		/* dummy data part 1 */

    char *dummy_data4;		/* dummy data part 2 */

    double *lai[12];		/* lAI data for each month */

    char **lai_ptr;		/* pointer to get the input2->answers */

    int nfiles;		/* count LAI input files */

    char **test, **ptr;	/* test number of LAI input files */

    

	/****************************************/ 
	/* Flow Direction                       */ 
	FILE * ef;		/* output flow direction ascii file */
    

	/****************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("VIC, hydrology, precipitation, Tmax, Tmin, soil");
    module->description = _("* PURPOSE:      Creates VIC input files:\n \
 * 		 1 - Meteorological:\n \
 * 			Three time series of GIS data are needed:\n \
 * 		 	Precipitation (mm/d), Tmax(C) and Tmin(C)\n \
 * 		 2 - Vegetation:\n \
 * 		 	Filling only Land cover class, with only one class,\n \
 * 			 and one standard root system.\n \
 * 			 Option to add monthly LAI (12 maps).\n \
 * 		 3 - Soil:\n \
 *		 	Barely complete, it takes elevation data & lat/long,\n \
 *		 	the rest is filled up with dummy soil data.\n \
 *		 4 - Routing file from GRASS flow direction file:\n \
 *		 	Recoding to rout input file for VIC post-processing\n \
 *		 	of hydrological surface runoff flow.\n \
 *		 	http://www.hydro.washington.edu/Lettenmaier/ \n \
 *		 	Models/VIC/Documentation/Bernt/ \n \
 *		 	rout/mainframe_rout1.htm");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUTS);
    input1->key = _("prcp");
    input1->description = _("Names of the precipitation input maps");
    input1->guisection = _("Required");
    input2 = G_define_standard_option(G_OPT_R_INPUTS);
    input2->key = _("tmax");
    input2->description = _("Names of the Tmax input maps");
    input2->guisection = _("Required");
    input3 = G_define_standard_option(G_OPT_R_INPUTS);
    input3->key = _("tmin");
    input3->description = _("Names of the Tmin input maps");
    input3->guisection = _("Required");
    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = _("dem");
    input4->description = _("Name of the elevation input map");
    input4->guisection = _("Required");
    input5 = G_define_standard_option(G_OPT_R_INPUT);
    input5->key = _("landcover");
    input5->description = _("Name of the land cover input map");
    input5->guisection = _("Required");
    input6 = G_define_standard_option(G_OPT_R_INPUTS);
    input6->key = _("LAI");
    input6->required = NO;
    input6->description = _("Name of the LAI input maps (12 of them!)");
    input7 = G_define_standard_option(G_OPT_R_INPUT);
    input7->key = _("flow_dir");
    input7->description =
	_("Name of the flow direction input map (GRASS format)");
    input7->guisection = _("Required");
    output1 = G_define_option();
    output1->key = _("output");
    output1->description =
	_("Base Name of the output vic meteorological ascii files");
    output1->answer = _("data_");
    output2 = G_define_option();
    output2->key = _("output_soil");
    output2->description = _("Name of the output vic soil ascii file");
    output2->answer = _("vic_soil.asc");
    output3 = G_define_option();
    output3->key = _("output_veg");
    output3->description = _("Name of the output vic vegetation ascii file");
    output3->answer = _("vic_veg.asc");
    output4 = G_define_option();
    output4->key = _("veglib");
    output4->required = NO;
    output4->description = _("Name of a standard vegetation library file");
    output4->answer = _("veglib");
    output5 = G_define_option();
    output5->key = _("output_fdir");
    output5->description = _("Name of the output flow direction ascii file");
    output5->answer = _("vic_fdir.asc");
    flag1 = G_define_flag();
    flag1->key = 'a';
    flag1->description =
	_("append meteorological data if file already exists (useful if adding additional year of data)");
    flag2 = G_define_flag();
    flag2->key = 'b';
    flag2->description =
	_("Convert flow direction from r.watershed to AGNPS");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    in = input4->answer;
    landcover_name = input5->answer;
    fdir_name = input7->answer;
    result1 = output1->answer;
    result2 = output2->answer;
    result3 = output3->answer;
    result4 = output5->answer;
    

	/************************************************/ 
	/* STANDARD VEGLIB CREATION HERE                */ 
	if (output4->answer)
	veglib(output4->answer);
    

	/************************************************/ 
	/* LOADING TMAX TIME SERIES MAPS                */ 
	test1 = input1->answers;
    for (ptr1 = test1, nfiles1 = 0; *ptr1 != NULL; ptr1++, nfiles1++)
	;
    if (nfiles1 > MAXFILES) {
	G_fatal_error(_("Too many inputs1, change MAXFILES, recompile."));
    }
    prcp_ptr = input1->answers;
    i = 0;
    for (; *prcp_ptr != NULL; prcp_ptr++) {
	prcp_name = *prcp_ptr;
	mapset = G_find_cell2(prcp_name, "");
	if (mapset == NULL)
	    G_fatal_error(_("cell file [%s] not found"), prcp_name);
	data_type_inrast_prcp[i] = G_raster_map_type(prcp_name, mapset);
	if ((infd_prcp[i] = G_open_cell_old(prcp_name, mapset)) < 0)
	    G_fatal_error(_("Cannot open cell file [%s]"), prcp_name);
	if (G_get_cellhd(prcp_name, mapset, &cellhd) < 0)
	    G_fatal_error(_("Cannot read file header of [%s])"), prcp_name);
	inrast_prcp[i] = G_allocate_raster_buf(data_type_inrast_prcp[i]);
	i++;
    }
    nfiles1 = i;
    

	/************************************************/ 
	/* LOADING TMAX TIME SERIES MAPS                */ 
	test2 = input2->answers;
    for (ptr2 = test2, nfiles2 = 0; *ptr2 != NULL; ptr2++, nfiles2++)
	;
    if (nfiles2 > MAXFILES) {
	G_fatal_error(_("Too many inputs2, change MAXFILES, recompile."));
    }
    tmax_ptr = input2->answers;
    i = 0;
    for (; *tmax_ptr != NULL; tmax_ptr++) {
	tmax_name = *tmax_ptr;
	mapset = G_find_cell2(tmax_name, "");
	if (mapset == NULL)
	    G_fatal_error(_("cell file [%s] not found"), tmax_name);
	data_type_inrast_tmax[i] = G_raster_map_type(tmax_name, mapset);
	if ((infd_tmax[i] = G_open_cell_old(tmax_name, mapset)) < 0)
	    G_fatal_error(_("Cannot open cell file [%s]"), tmax_name);
	if (G_get_cellhd(tmax_name, mapset, &cellhd) < 0)
	    G_fatal_error(_("Cannot read file header of [%s])"), tmax_name);
	inrast_tmax[i] = G_allocate_raster_buf(data_type_inrast_tmax[i]);
	i++;
    }
    nfiles2 = i;
    

	/************************************************/ 
	/* LOADING TMIN TIME SERIES MAPS                */ 
	test3 = input3->answers;
    for (ptr3 = test3, nfiles3 = 0; *ptr3 != NULL; ptr3++, nfiles3++)
	;
    if (nfiles3 > MAXFILES) {
	G_fatal_error(_("Too many inputs3, change MAXFILES, recompile."));
    }
    tmin_ptr = input3->answers;
    i = 0;
    for (; *tmin_ptr != NULL; tmin_ptr++) {
	tmin_name = *tmin_ptr;
	mapset = G_find_cell2(tmin_name, "");
	if (mapset == NULL)
	    G_fatal_error(_("cell file [%s] not found"), tmin_name);
	data_type_inrast_tmin[i] = G_raster_map_type(tmin_name, mapset);
	if ((infd_tmin[i] = G_open_cell_old(tmin_name, mapset)) < 0)
	    G_fatal_error(_("Cannot open cell file [%s]"), tmin_name);
	if (G_get_cellhd(tmin_name, mapset, &cellhd) < 0)
	    G_fatal_error(_("Cannot read file header of [%s])"), tmin_name);
	inrast_tmin[i] = G_allocate_raster_buf(data_type_inrast_tmin[i]);
	i++;
    }
    nfiles3 = i;
    

	/************************************************/ 
	if (nfiles1 <= nfiles2 || nfiles1 <= nfiles3) {
	nfiles_shortest = nfiles1;
    }
    else if (nfiles2 <= nfiles1 || nfiles2 <= nfiles3) {
	nfiles_shortest = nfiles2;
    }
    else {
	nfiles_shortest = nfiles3;
    }
    

	/************************************************/ 
	/* Load Elevation file                          */ 
	mapset = G_find_cell2(in, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), in);
    }
    data_type_inrast_elevation = G_raster_map_type(in, mapset);
    if ((infd = G_open_cell_old(in, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), in);
    if (G_get_cellhd(in, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), in);
    inrast_elevation = G_allocate_raster_buf(data_type_inrast_elevation);
    

	/***************************************************/ 

	/************************************************/ 
	/* LOADING OPTIONAL LAI MONTHLY MAPS            */ 
	if (input6->answer) {
	test = input6->answers;
	for (ptr = test, nfiles = 0; *ptr != NULL; ptr++, nfiles++)
	    ;
	if (nfiles < 12)
	    G_fatal_error(_("The exact number of LAI input maps is 12"));
	lai_ptr = input6->answers;
	for (; *lai_ptr != NULL; lai_ptr++) {
	    strcpy(lai_name, *lai_ptr);
	}
	for (i = 0; i < 12; i++) {
	    mapset = G_find_cell2(&lai_name[i], "");
	    if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), lai_name[i]);
	    }
	    data_type_inrast_lai[i] =
		G_raster_map_type(&lai_name[i], mapset);
	    if ((infd_lai[i] = G_open_cell_old(&lai_name[i], mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), lai_name[i]);
	    if (G_get_cellhd(&lai_name[i], mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s])"),
			       lai_name[i]);
	    inrast_lai[i] = G_allocate_raster_buf(data_type_inrast_lai[i]);
	}
    }
    

	/************************************************/ 
	/* LOADING REQUIRED LAND COVER MAP              */ 
	mapset = G_find_cell2(landcover_name, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), landcover_name);
    }
    data_type_inrast_landcover = G_raster_map_type(landcover_name, mapset);
    if ((infd_landcover = G_open_cell_old(landcover_name, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), landcover_name);
    if (G_get_cellhd(landcover_name, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), landcover_name);
    inrast_landcover = G_allocate_raster_buf(data_type_inrast_landcover);
    

	/************************************************/ 
	/* LOADING REQUIRED BINARY MAP                  */ 
	mapset = G_find_cell2(fdir_name, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), fdir_name);
    }
    data_type_inrast_fdir = G_raster_map_type(fdir_name, mapset);
    if ((infd_fdir = G_open_cell_old(fdir_name, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), fdir_name);
    if (G_get_cellhd(fdir_name, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), fdir_name);
    inrast_fdir = G_allocate_raster_buf(data_type_inrast_fdir);
    

	/***************************************************/ 

	/***************************************************/ 
	G_debug(3, "number of rows %d", cellhd.rows);
    G_get_window(&cellhd);
    stepx = cellhd.ew_res;
    stepy = cellhd.ns_res;
    xmin = cellhd.west;
    xmax = cellhd.east;
    ymin = cellhd.south;
    ymax = cellhd.north;
    nrows = G_window_rows();
    ncols = G_window_cols();
    
	/*Shamelessly stolen from r.sun !!!!    */ 
	/* Set up parameters for projection to lat/long if necessary */ 
	if ((G_projection() != PROJECTION_LL)) {
	not_ll = 1;
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
    }				/*End of stolen from r.sun */
    
	/*Initialize soil grid cell process switch */ 
	g = fopen(result2, "w");
    
	/*Initialize grid cell process switch */ 
	/*If =1 then process, if =0 then skip */ 
	process = 1;
    
	/*Initialize grid cell count */ 
	grid_count = 1;
    
	/*Initialize output file */ 
	fprintf(g,
		"#RUN\tGRID\tLAT\tLNG\tINFILT\tDs\tDs_MAX\tWs\tC\tEXPT_1\tEXPT_2\tEXPT_3\tKsat_1\tKsat_2\tKsat_3\tPHI_1\tPHI_2\tPHI_3\tMOIST_1\tMOIST_2\tMOIST_3\tELEV\tDEPTH_1\tDEPTH_2\tDEPTH_3\tAVG_T\tDP\tBUBLE1\tBUBLE2\tBUBLE3\tQUARZ1\tQUARZ2\tQUARZ3\tBULKDN1\tBULKDN2\tBULKDN3\tPARTDN1\tPARTDN2\tPARTDN3\tOFF_GMT\tWcrFT1\tWcrFT2\tWcrFT3\tWpFT1\tWpFT2\tWpFT3\tZ0_SOIL\tZ0_SNOW\tPRCP\tRESM1\tRESM2\tRESM3\tFS_ACTV\tJULY_TAVG\n");
    
	/*Initialize dummy data */ 
	dummy_data1 =
	"0.010\t1.e-4\t3.05\t0.93\t2\t4.0\t4.0\t4.0\t250.0\t250.0\t250.0\t-999\t-999\t-999\t0.4\t0.4\t0.4";
    dummy_data2 =
	"0.1\t6.90\t2.000\t14.0\t4.0\t75.0\t75.0\t75.0\t0.24\t0.24\t0.24\t1306\t1367\t1367\t2650\t2650\t2650\t-6\t0.330\t0.330\t0.330\t0.133\t0.133\t0.133\t0.001\t0.010\t500\t0.02\t0.02\t0.02\t1\t18.665\n";
    
	/*Initialize grid cell process switch */ 
	h = fopen(result3, "w");
    
	/*Initialize dummy data */ 
	dummy_data3 = "0.10 0.1 1.00 0.65 0.50 0.25";
    dummy_data4 =
	"0.312 0.413 0.413 0.413 0.413 0.488 0.975 1.150 0.625 0.312 0.312 0.312";
    

	/***********************/ 
	/* Flow Direction File */ 
	/*Initialize grid cell process switch */ 
	ef = fopen(result4, "w");
    
	/*Print to ascii file */ 
	G_message("Your ncols,nrows for flow direction map are (%d,%d)\n",
		  ncols, nrows);
    fprintf(ef, "ncols\t%d\n", ncols);
    fprintf(ef, "nrows\t%d\n", nrows);
    
	/*NORTHWEST LONGITUDE */ 
	G_message("Your xllcorner for flow direction map is %f\n", xmin);
    fprintf(ef, "xllcorner\t%f\n", xmin);
    
	/*NORTHWEST LATITUDE */ 
	G_message("Your yllcorner for flow direction map is %f\n", ymin);
    fprintf(ef, "yllcorner\t%f\n", ymin);
     /*CELLSIZE*/ G_message("Your cellsize for flow direction map is %f\n",
			      stepx);
    fprintf(ef, "cellsize\t%f\n", stepx);
    
	/*NODATA_value */ 
	G_message("Your NODATA_value for flow direction map is 0\n");
    fprintf(ef, "NODATA_value\t0\n");
    

	/***********************/ 

	/***********************/ 
	for (row = 0; row < nrows; row++) {
	DCELL d_prcp[MAXFILES];
	DCELL d_tmax[MAXFILES];
	DCELL d_tmin[MAXFILES];
	DCELL d_elevation;
	CELL c_landcover;
	CELL c_fdir;
	DCELL d_lai[12];
	G_percent(row, nrows, 2);
	for (i = 0; i < nfiles_shortest; i++) {
	    if (G_get_raster_row
		 (infd_prcp[i], inrast_prcp[i], row,
		  data_type_inrast_prcp[i]) < 0)
		G_fatal_error(_("Could not read from prcp<%d>"), i + 1);
	    if (G_get_raster_row
		 (infd_tmax[i], inrast_tmax[i], row,
		  data_type_inrast_tmax[i]) < 0)
		G_fatal_error(_("Could not read from tmax<%d>"), i + 1);
	    if (G_get_raster_row
		 (infd_tmin[i], inrast_tmin[i], row,
		  data_type_inrast_tmin[i]) < 0)
		G_fatal_error(_("Could not read from tmin<%d>"), i + 1);
	}
	if (G_get_raster_row
	     (infd, inrast_elevation, row, data_type_inrast_elevation) < 0)
	    G_fatal_error(_("Could not read from <%s>"), in);
	if (G_get_raster_row
	     (infd_landcover, inrast_landcover, row,
	      data_type_inrast_landcover) < 0)
	    G_fatal_error(_("Could not read from <%s>"), landcover_name);
	if (input6->answer) {
	    for (i = 0; i < 12; i++) {
		if (G_get_raster_row
		     (infd_lai[i], inrast_lai[i], row,
		      data_type_inrast_lai[i]) < 0)
		    G_fatal_error(_("Could not read from <%s>"),
				   lai_name[i]);
	    }
	}
	if (G_get_raster_row
	     (infd_fdir, inrast_fdir, row, data_type_inrast_fdir) < 0)
	    G_fatal_error(_("Could not read from <%s>"), fdir_name);
	for (col = 0; col < ncols; col++) {
	    for (i = 0; i < nfiles_shortest; i++) {
		
		    /*Extract prcp time series data */ 
		    switch (data_type_inrast_prcp[i]) {
		case CELL_TYPE:
		    d_prcp[i] = (double)((CELL *) inrast_prcp[i])[col];
		    break;
		case FCELL_TYPE:
		    d_prcp[i] = (double)((FCELL *) inrast_prcp[i])[col];
		    break;
		case DCELL_TYPE:
		    d_prcp[i] = (double)((DCELL *) inrast_prcp[i])[col];
		    break;
		}
		
		    /*Extract tmax time series data */ 
		    switch (data_type_inrast_tmax[i]) {
		case CELL_TYPE:
		    d_tmax[i] = (double)((CELL *) inrast_tmax[i])[col];
		    break;
		case FCELL_TYPE:
		    d_tmax[i] = (double)((FCELL *) inrast_tmax[i])[col];
		    break;
		case DCELL_TYPE:
		    d_tmax[i] = (double)((DCELL *) inrast_tmax[i])[col];
		    break;
		}
		
		    /*Extract tmin time series data */ 
		    switch (data_type_inrast_tmin[i]) {
		case CELL_TYPE:
		    d_tmin[i] = (double)((CELL *) inrast_tmin[i])[col];
		    break;
		case FCELL_TYPE:
		    d_tmin[i] = (double)((FCELL *) inrast_tmin[i])[col];
		    break;
		case DCELL_TYPE:
		    d_tmin[i] = (double)((DCELL *) inrast_tmin[i])[col];
		    break;
		}
	    }
	    
		/*Extract elevation data */ 
		switch (data_type_inrast_elevation) {
	    case CELL_TYPE:
		d_elevation = (double)((CELL *) inrast_elevation)[col];
		break;
	    case FCELL_TYPE:
		d_elevation = (double)((FCELL *) inrast_elevation)[col];
		break;
	    case DCELL_TYPE:
		d_elevation = ((DCELL *) inrast_elevation)[col];
		break;
	    }
	    
		/*Extract landcover data */ 
		switch (data_type_inrast_landcover) {
	    case CELL_TYPE:
		c_landcover = (int)((CELL *) inrast_landcover)[col];
		break;
	    case FCELL_TYPE:
		c_landcover = (int)((FCELL *) inrast_landcover)[col];
		break;
	    case DCELL_TYPE:
		c_landcover = (int)((DCELL *) inrast_landcover)[col];
		break;
	    }
	    
		/*Extract lai monthly data */ 
		if (input6->answer) {
		for (i = 0; i < 12; i++) {
		    switch (data_type_inrast_lai[i]) {
		    case CELL_TYPE:
			d_lai[i] = (double)((CELL *) inrast_lai[i])[col];
			break;
		    case FCELL_TYPE:
			d_lai[i] = (double)((FCELL *) inrast_lai[i])[col];
			break;
		    case DCELL_TYPE:
			d_lai[i] = (double)((DCELL *) inrast_lai[i])[col];
			break;
		    }
		}
	    }
	    switch (data_type_inrast_fdir) {
	    case CELL_TYPE:
		c_fdir = ((CELL *) inrast_fdir)[col];
		break;
	    case FCELL_TYPE:
		c_fdir = (int)((FCELL *) inrast_fdir)[col];
		break;
	    case DCELL_TYPE:
		c_fdir = (int)((DCELL *) inrast_fdir)[col];
		break;
	    }
	    
		/*Extract lat/long data */ 
		latitude = ymax - (row * stepy);
	    longitude = xmin + (col * stepx);
	    if (not_ll) {
		if (pj_do_proj(&longitude, &latitude, &iproj, &oproj) < 0) {
		    G_fatal_error(_("Error in pj_do_proj"));
		}
	    }
	    else {
		
		    /*Do nothing */ 
	    }
	    if (G_is_d_null_value(&prcp[0]) || G_is_d_null_value(&d_tmax[0])
		 || G_is_d_null_value(&d_tmin[0]) ||
		 G_is_d_null_value(&d_elevation) ||
		 G_is_c_null_value(&c_landcover) ||
		 G_is_c_null_value(&c_fdir)) {
		
		    /* Do nothing */ 
		    c_fdir = -1;
	    }
	    else {
		
		    /* Make the output .dat file name */ 
		    sprintf(result_lat_long, "%s%.4f%s%.4f", result1,
			    latitude - stepy / 2.0, "_",
			    longitude - stepx / 2);
		
		    /*Open new ascii file */ 
		    if (flag1->answer) {
		    
			/*Initialize grid cell in append mode */ 
			f = fopen(result_lat_long, "a");
		}
		else {
		    
			/*Initialize grid cell in new file mode */ 
			f = fopen(result_lat_long, "w");
		}
		
		    /*Print data into the file maps data if available */ 
		    for (i = 0; i < nfiles_shortest; i++) {
		    fprintf(f, "%.2f  %.2f  %.2f\n", d_prcp[i], d_tmax[i],
			     d_tmin[i]);
		}
		fclose(f);
		
		    /*Print to soil ascii file */ 
		    fprintf(g, "%d\t%d\t%7.4f\t%8.4f\t%s\t%7.2f\t%s\n",
			    process, grid_count, latitude - stepy / 2,
			    longitude - stepx / 2, dummy_data1, d_elevation,
			    dummy_data2);
		
		    /*Print to vegetation ascii file */ 
		    /*Grid cell count and number of classes in that grid cell (=1) */ 
		    fprintf(h, "%d 1\n", grid_count);
		
		    /*Class number, percentage that this class covers in the
		     * grid cell(=1.0, full grid cell)
		     * 3 root zones with depths of 10cm, 10cm and 1.0m
		     * for those 3 root zone depths, how much root in each (%)
		     * here we have 0.65, 0.50 and 0.25
		     * */ 
		    fprintf(h, "%d 1.0 %s\n", c_landcover, dummy_data3);
		
		    /*Load monthly LAI maps data if available */ 
		    if (input6->answer) {
		    fprintf(h,
			     "%5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f\n",
			     lai[0], lai[1], lai[2], lai[3], lai[4], lai[5],
			     lai[6], lai[7], lai[8], lai[9], lai[10],
			     lai[11]);
		}
		else {
		    
			/*      fprintf(h,"%s\n", dummy_data4); */ 
		}
		grid_count = grid_count + 1;
	    }
	    
		/*Print to ascii file */ 
		/*Grid cell flow direction value in that grid cell */ 
		if (flag2->answer) {
		
		    /* Convert r.watershed flow dir to AGNPS */ 
		    if (c_fdir == 0 || c_fdir == 8) {
		    fprintf(ef, "3 ");
		}
		else if (c_fdir == 1) {
		    fprintf(ef, "2 ");
		}
		else if (c_fdir == 2) {
		    fprintf(ef, "1 ");
		}
		else if (c_fdir == 3) {
		    fprintf(ef, "8 ");
		}
		else if (c_fdir == 4) {
		    fprintf(ef, "7 ");
		}
		else if (c_fdir == 5) {
		    fprintf(ef, "6 ");
		}
		else if (c_fdir == 6) {
		    fprintf(ef, "5 ");
		}
		else if (c_fdir == 7) {
		    fprintf(ef, "4 ");
		}
		else if (c_fdir == -1) {
		    fprintf(ef, "0 ");
		}
		else {
		    fprintf(ef, "0 ");
		}
	    }
	    else {
		if (c_fdir == -1) {
		    
			/* Flow direction NODATA_value=0 */ 
			fprintf(ef, "0 ");
		}
		else {
		    
			/* Flow direction format is AGNPS */ 
			fprintf(ef, "%d ", c_fdir);
		}
	    }
	}
	fprintf(ef, "\n");
    }
    G_message(_("Created %d VIC meteorological files"), grid_count);
    G_message(_("Created %d VIC grid cells soil/vegetation definitions"),
	       grid_count);
    G_message(_("Created a routing flow direction input file"));
    for (i = 0; i < nfiles1; i++) {
	G_free(inrast_prcp[i]);
	G_close_cell(infd_prcp[i]);
    }
    for (i = 0; i < nfiles2; i++) {
	G_free(inrast_tmax[i]);
	G_close_cell(infd_tmax[i]);
    }
    for (i = 0; i < nfiles3; i++) {
	G_free(inrast_tmin[i]);
	G_close_cell(infd_tmin[i]);
    }
    G_free(inrast_elevation);
    G_close_cell(infd);
    G_free(inrast_landcover);
    G_close_cell(infd_landcover);
    if (input6->answer) {
	for (i = 0; i < 12; i++) {
	    G_free(inrast_lai[i]);
	    G_close_cell(infd_lai[i]);
	}
    }
    G_free(inrast_fdir);
    G_close_cell(infd_fdir);
    fclose(h);			/* Vegetation ascii file */
    fclose(g);			/* Soil ascii file */
    fclose(ef);		/* Flow Direction ascii file */
    exit(EXIT_SUCCESS);
}


