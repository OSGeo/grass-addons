
/****************************************************************************
 *
 * MODULE:       i.eb.rohair
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the standard air density as seen in Pawan (2004)
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
#include <grass/glocale.h>
double roh_air(double dem, double tempka);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    struct GModule *module;

    struct Option *input1, *input2, *output1;

    struct History history;	/*metadata */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result1;		/*output raster name */

    
	/*File Descriptors */ 
    int infd_dem, infd_tempka;

    int outfd1;

    char *rohair;

    char *dem, *tempka;

    int i = 0, j = 0;

    void *inrast_dem, *inrast_tempka;

    DCELL * outrast1;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_dem;
    RASTER_MAP_TYPE data_type_tempka;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("rohair, energy balance, SEBAL");
    module->description =
	_("Standard height-based Air Density as seen in Pawan (2004).");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("dem");
    input1->description = _("Name of the DEM map [m]");
    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = _("tempka");
    input2->description = _("Name of the Air Temperature map [K]");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->key = _("rohair");
    output1->description = _("Name of the output rohair layer");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    dem = input1->answer;
    tempka = input2->answer;
    result1 = output1->answer;
    

	/***************************************************/ 
	mapset = G_find_cell2(dem, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), dem);
    }
    data_type_dem = G_raster_map_type(dem, mapset);
    if ((infd_dem = G_open_cell_old(dem, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), dem);
    if (G_get_cellhd(dem, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), dem);
    inrast_dem = G_allocate_raster_buf(data_type_dem);
    

	/***************************************************/ 

	/***************************************************/ 
	mapset = G_find_cell2(tempka, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), tempka);
    }
    data_type_tempka = G_raster_map_type(tempka, mapset);
    if ((infd_tempka = G_open_cell_old(tempka, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), tempka);
    if (G_get_cellhd(tempka, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), tempka);
    inrast_tempka = G_allocate_raster_buf(data_type_tempka);
    

	/***************************************************/ 
	G_debug(3, "number of rows %d", cellhd.rows);
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast1 = G_allocate_raster_buf(data_type_output);
    
	/* Create New raster files */ 
	if ((outfd1 = G_open_raster_new(result1, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), result1);
    
	/* Process pixels */ 
	for (row = 0; row < nrows; row++)
	 {
	DCELL d;
	DCELL d_dem;
	DCELL d_tempka;
	
	    /* read input maps */ 
	    if (G_get_raster_row(infd_dem, inrast_dem, row, data_type_dem) <
		0)
	    G_fatal_error(_("Could not read from <%s>"), dem);
	if (G_get_raster_row
	     (infd_tempka, inrast_tempka, row, data_type_tempka) < 0)
	    G_fatal_error(_("Could not read from <%s>"), tempka);
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
	    switch (data_type_dem) {
	    case CELL_TYPE:
		d_dem = (double)((CELL *) inrast_dem)[col];
		break;
	    case FCELL_TYPE:
		d_dem = (double)((FCELL *) inrast_dem)[col];
		break;
	    case DCELL_TYPE:
		d_dem = ((DCELL *) inrast_dem)[col];
		break;
	    }
	    switch (data_type_tempka) {
	    case CELL_TYPE:
		d_tempka = (double)((CELL *) inrast_tempka)[col];
		break;
	    case FCELL_TYPE:
		d_tempka = (double)((FCELL *) inrast_tempka)[col];
		break;
	    case DCELL_TYPE:
		d_tempka = ((DCELL *) inrast_tempka)[col];
		break;
	    }
	    if (G_is_d_null_value(&d_dem) || G_is_d_null_value(&d_tempka)) {
		G_set_d_null_value(&outrast1[col], 1);
	    }
	    else {
		

				/********************/ 
		    /* calculate rohair */ 
		    d = roh_air(d_dem, d_tempka);
		outrast1[col] = d;
	    }
	    }
	if (G_put_raster_row(outfd1, outrast1, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
	}
    G_free(inrast_dem);
    G_free(inrast_tempka);
    G_close_cell(infd_dem);
    G_close_cell(infd_tempka);
    G_free(outrast1);
    G_close_cell(outfd1);
    G_short_history(result1, "raster", &history);
    G_command_history(&history);
    G_write_history(result1, &history);
    exit(EXIT_SUCCESS);
}


