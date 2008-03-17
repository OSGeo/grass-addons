/****************************************************************************
 *
 * MODULE:       r.vic_soil
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Creates a VIC soil input file.
 * 		 Filling only elevation and lat/long.
 * 		 Add remaining as dummy data from VIC website.
 * 		 Will add more like data that can be processed from 
 * 		 elevation/lat/longraster or specific raster layer
 * 		 inputs as they become available later.
 * 		 Like:
 * 		 	- Time zone offset from GMT,
 * 		 	etc...
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

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	int not_ll=0;//if proj is not lat/long, it will be 1.
	struct GModule *module;
	struct Option *input1, *output1;
	
	struct Flag *flag1;	
	struct History history; //metadata
	
	struct pj_info iproj;
	struct pj_info oproj;
	/************************************/
	/* FMEO Declarations*****************/
	char 	*name;   	// input raster name
	char 	*result1; 	//output raster name
	//File Descriptors
	int 	infd;
	//Raster pointer
	DCELL 	*inrast_elevation;

	char 	*in;
	int 	i=0,j=0;
	double 	xp, yp;
	double 	xmin, ymin;
	double 	xmax, ymax;
	double 	stepx,stepy;
	double 	latitude, longitude;

	void 			*inrast;
	RASTER_MAP_TYPE 	data_type_inrast;

	FILE	*f; 		// output ascii file
	int 	process; 	// process grid cell switch
	int 	grid_count; 	// grid cell count
	char 	*dummy_data1; 	// dummy data part 1
	char 	*dummy_data2; 	// dummy data part 2
	double	elevation;	// average evevation of grid cell
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("VIC, hydrology, soil");
	module->description = _("creates a soil ascii file taking lat/long from a map");

	/* Define the different options */
	input1 = G_define_standard_option(G_OPT_R_INPUT) ;
	input1->key	   = _("input");
	input1->description=_("Name of the elevation input map");
	input1->answer     =_("input");

	output1 = G_define_option() ;
	output1->key        =_("output");
	output1->description=_("Name of the output vic soil ascii file");
	output1->answer     =_("vic_soil");
	
	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	in	 	= input1->answer;
	result1  	= output1->answer;
	/***************************************************/
	mapset = G_find_cell2(in, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), in);
	}
	data_type_inrast = G_raster_map_type(in,mapset);
	if ( (infd = G_open_cell_old (in,mapset)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), in);
	if (G_get_cellhd (in, mapset, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s])"), in);
	inrast = G_allocate_raster_buf(data_type_inrast);
	/***************************************************/
	G_debug(3, "number of rows %d",cellhd.rows);

	stepx=cellhd.ew_res;
	stepy=cellhd.ns_res;

	xmin=cellhd.west;
	xmax=cellhd.east;
	ymin=cellhd.south;
	ymax=cellhd.north;

	/*Allocate input buffer*/
	inrast_elevation	= G_allocate_d_raster_buf();

	nrows = G_window_rows();
	ncols = G_window_cols();

	/*Initialize grid cell process switch*/
	f=fopen(result1,"w");
	/*Initialize grid cell process switch*/
	/*If =1 then process, if =0 then skip*/
	process = 1; 

	/*Initialize grid cell count*/
	grid_count = 1;
	/*Initialize output file */
	fprintf(f,"#RUN\tGRID\tLAT\tLNG\tINFILT\tDs\tDs_MAX\tWs\tC\tEXPT_1\tEXPT_2\tEXPT_3\tKsat_1\tKsat_2\tKsat_3\tPHI_1\tPHI_2\tPHI_3\tMOIST_1\tMOIST_2\tMOIST_3\tELEV\tDEPTH_1\tDEPTH_2\tDEPTH_3\tAVG_T\tDP\tBUBLE1\tBUBLE2\tBUBLE3\tQUARZ1\tQUARZ2\tQUARZ3\tBULKDN1\tBULKDN2\tBULKDN3\tPARTDN1\tPARTDN2\tPARTDN3\tOFF_GMT\tWcrFT1\tWcrFT2\tWcrFT3\tWpFT1\tWpFT2\tWpFT3\tZ0_SOIL\tZ0_SNOW\tPRCP\tRESM1\tRESM2\tRESM3\tFS_ACTV\tJULY_TAVG\n");

	/*Initialize dummy data*/
	dummy_data1 = "0.010\t1.e-4\t3.05\t0.93\t2\t4.0\t4.0\t4.0\t250.0\t250.0\t250.0\t-999\t-999\t-999\t0.4\t0.4\t0.4";
	dummy_data2 = "0.1\t6.90\t2.000\t14.0\t4.0\t75.0\t75.0\t75.0\t0.24\t0.24\t0.24\t1306\t1367\t1367\t2650\t2650\t2650\t-6\t0.330\t0.330\t0.330\t0.133\t0.133\t0.133\t0.001\t0.010\t500\t0.02\t0.02\t0.02\t1\t18.665\n";
	
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
	
	for (row = 0; row < nrows/100; row++)
	{
		DCELL d_elevation;
		G_percent(row,nrows,2);
		if(G_get_raster_row(infd,inrast,row,data_type_inrast)<0)
			G_fatal_error(_("Could not read from <%s>"),in);
		for (col=0; col < ncols; col++)
		{
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
			/*Extract elevation data*/
			switch(data_type_inrast){
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
			/*Print to ascii file*/
			fprintf(f,"%d\t%d\t%6.3f\t%7.3f\t%s\t%7.2f\t%s\n", process, grid_count, latitude, longitude, dummy_data1, d_elevation, dummy_data2);
			grid_count=grid_count+1;
		}
	}
	G_free (inrast);
	G_close_cell (infd);
	fclose(f);
	exit(EXIT_SUCCESS);
}

