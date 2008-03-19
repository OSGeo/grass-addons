/****************************************************************************
 *
 * MODULE:       r.out.vic_mask
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Creates a VIC watershed mask input ascii file.
 * 		 Not NULL() and not "0" data is made "1",
 * 		 which is valid grid cell for VIC processing.
 * 		 NULL() and 0 data are set to "0",
 * 		 which tells VIC not to process it.
 * 		 This is used by gstation.c and select_station.c to grid
 * 		 meteorological station daily data.
 * 		 http://www.hydro.washington.edu/Lettenmaier/Data/PRCP.html#A4.5
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

int veglib(char *filename);

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	struct GModule *module;
	struct Option *input1, *output1;
	
	struct History history; //metadata
	
	struct pj_info iproj;
	struct pj_info oproj;
	/************************************/
	/* FMEO Declarations*****************/
	char 	*name;		// input raster name
	char 	*result1; 	//output raster name
	//File Descriptors
	int 	infd;

	int 	i=0,j=0;
	double xp, yp;
	double xmin, ymin;
	double xmax, ymax;
	double stepx,stepy;
	double latitude, longitude;
	int not_ll=0;//if proj is not lat/long, it will be 1.

	void 			*inrast;
	RASTER_MAP_TYPE 	data_type_inrast;

	FILE	*f; 		// output ascii file
	int 	grid_count; 	// grid cell count
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("VIC, hydrology, mask");
	module->description = _("creates a watershed mask ascii file \
			from any binary map. \
			NULL() and '0' will be switch off for VIC.");

	/* Define the different options */
	input1 = G_define_standard_option(G_OPT_R_INPUT) ;
	input1->key	   = _("input");
	input1->description=_("Name of the binary input map");
	
	output1 = G_define_option() ;
	output1->key        =_("output");
	output1->description=_("Name of the output vic watershed \
				mask ascii file");
	output1->answer     =_("vic_mask.asc");
	
	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	name		 	= input1->answer;
	result1 	 	= output1->answer;
	/************************************************/
	/* LOADING REQUIRED BINARY MAP			*/
	mapset = G_find_cell2(name, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), name);
	}
	data_type_inrast = G_raster_map_type(name,mapset);
	if ( (infd = G_open_cell_old (name,mapset)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), name);
	if (G_get_cellhd (name, mapset, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s])"), name);
	inrast = G_allocate_raster_buf(data_type_inrast);
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
	
	latitude = ymax;
	longitude = xmin;
	if(not_ll){
		if (pj_do_proj(&longitude, &latitude, &iproj, &oproj) < 0) {
			G_fatal_error(_("Error in pj_do_proj"));
		}
	}else{
		//Do nothing
	}	
	/*Initialize grid cell process switch*/
	f=fopen(result1,"w");

	/*Print to ascii file*/
	/*NORTHWEST LATITUDE*/
	fprintf(f,"%d\n", latitude);
	/*NORTHWEST LONGITUDE*/
	fprintf(f,"%d\n", longitude);
	fprintf(f,"%d\n", nrows);
	fprintf(f,"%d\n", ncols);

	for (row = 0; row < nrows; row++){
		CELL c;
		G_percent(row,nrows,2);
		if(G_get_raster_row(infd,inrast,row,data_type_inrast)<0)
			G_fatal_error(_("Could not read from <%s>"),name);
		for (col=0; col < ncols; col++){
			/*Extract data*/
			switch(data_type_inrast){
				case CELL_TYPE:
					c=  ((CELL *) inrast)[col];
					break;
				case FCELL_TYPE:
					c= (int) ((FCELL *) inrast)[col];
					break;
				case DCELL_TYPE:
					c= (int) ((DCELL *) inrast)[col];
					break;
			}
			if(G_is_c_null_value(&c)){
				c = 0;
			}
			/*Print to ascii file*/
			/*Grid cell value in that grid cell*/
			if(c==0){
				fprintf(f,"%d ",c);
			} else {
				fprintf(f,"1 ");
			}
		}
		fprintf(f,"\n");
	}
	G_free (inrast);
	G_close_cell (infd);
	fclose(f);
	exit(EXIT_SUCCESS);
}

