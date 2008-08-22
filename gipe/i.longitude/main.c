
/****************************************************************************
 *
 * MODULE:       i.longitude
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the longitude of the pixels in the map. 
 *
 * COPYRIGHT:    (C) 2002-2008 by the GRASS Development Team
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
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    int not_ll = 0;		/*if proj is not lat/long, it will be 1. */

    struct GModule *module;

    struct Option *input1, *output1;

    struct Flag *flag1;

    struct History history;	/*metadata */

    struct pj_info iproj;

    struct pj_info oproj;

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result1;		/*output raster name */

    
	/*File Descriptors */ 
    int infd;

    int outfd1;

    char *in;

    int i = 0, j = 0;

    double xp, yp;

    double xmin, ymin;

    double xmax, ymax;

    double stepx, stepy;

    double latitude, longitude;

    void *inrast;

    DCELL * outrast1;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_inrast;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("longitude, projection");
    module->description = _("creates a longitude map");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->description = _("Name of the input map");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the output longitude layer");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    in = input1->answer;
    result1 = output1->answer;
    

	/***************************************************/ 
	mapset = G_find_cell2(in, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), in);
    }
    data_type_inrast = G_raster_map_type(in, mapset);
    if ((infd = G_open_cell_old(in, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), in);
    if (G_get_cellhd(in, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), in);
    inrast = G_allocate_raster_buf(data_type_inrast);
    

	/***************************************************/ 
	G_debug(3, "number of rows %d", cellhd.rows);
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
    }				/* End of stolen from r.sun :P */
    outrast1 = G_allocate_raster_buf(data_type_output);
    if ((outfd1 = G_open_raster_new(result1, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), result1);
    for (row = 0; row < nrows; row++)
	 {
	DCELL d;
	DCELL d_lon;
	G_percent(row, nrows, 2);
	if (G_get_raster_row(infd, inrast, row, data_type_inrast) < 0)
	    G_fatal_error(_("Could not read from <%s>"), in);
	for (col = 0; col < ncols; col++)
	     {
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
	    d_lon = longitude;
	    outrast1[col] = d_lon;
	    }
	if (G_put_raster_row(outfd1, outrast1, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
	}
    G_free(inrast);
    G_close_cell(infd);
    G_free(outrast1);
    G_close_cell(outfd1);
    G_short_history(result1, "raster", &history);
    G_command_history(&history);
    G_write_history(result1, &history);
    exit(EXIT_SUCCESS);
}


