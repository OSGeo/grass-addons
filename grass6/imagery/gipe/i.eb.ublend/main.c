
/****************************************************************************
 *
 * MODULE:       i.eb.ublend
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the wind speed at blendiong height
 * 		 as seen in Pawan (2004)
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
double u_blend(double u_hmoment, double disp, double hblend, double z0m,
		double hmoment);
int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    struct GModule *module;

    struct Option *input1, *input2, *input3, *input4, *input5, *output1;

    struct Flag *flag1;

    struct History history;	/*metadata */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result;		/*output raster name */

    
	/*File Descriptors */ 
    int infd_u_hmoment, infd_disp, infd_z0m;

    int outfd;

    char *u_hmoment, *disp, *z0m;

    double hblend, hmoment;

    int i = 0, j = 0;

    void *inrast_u_hmoment, *inrast_disp, *inrast_z0m;

    DCELL * outrast;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_u_hmoment;
    RASTER_MAP_TYPE data_type_disp;
    RASTER_MAP_TYPE data_type_z0m;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("ublend, energy balance, SEBAL");
    module->description = _("Wind speed at blending height.");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("u_hm");
    input1->description =
	_("Name of the wind speed at momentum height map (2.0m height in Pawan, 2004)");
    input2 = G_define_option();
    input2->key = _("hmoment");
    input2->type = TYPE_DOUBLE;
    input2->required = YES;
    input2->gisprompt = _("Value, parameter");
    input2->description =
	_("Value of the momentum height (2.0 in Pawan, 2004)");
    input2->answer = _("2.0");
    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = _("disp");
    input3->description = _("Name of the displacement height map");
    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = _("z0m");
    input4->description =
	_("Name of the surface roughness for momentum map");
    input5 = G_define_option();
    input5->key = _("hblend");
    input5->type = TYPE_DOUBLE;
    input5->required = YES;
    input5->gisprompt = _("Value, parameter");
    input5->description =
	_("Value of the blending height (100.0 in Pawan, 2004)");
    input5->answer = _("100.0");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the output ublend layer");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    u_hmoment = input1->answer;
    hmoment = atof(input2->answer);
    disp = input3->answer;
    z0m = input4->answer;
    hblend = atof(input5->answer);
    result = output1->answer;
    

	/***************************************************/ 
	mapset = G_find_cell2(u_hmoment, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), u_hmoment);
    }
    data_type_u_hmoment = G_raster_map_type(u_hmoment, mapset);
    if ((infd_u_hmoment = G_open_cell_old(u_hmoment, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), u_hmoment);
    if (G_get_cellhd(u_hmoment, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), u_hmoment);
    inrast_u_hmoment = G_allocate_raster_buf(data_type_u_hmoment);
    

	/***************************************************/ 
	mapset = G_find_cell2(disp, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), disp);
    }
    data_type_disp = G_raster_map_type(disp, mapset);
    if ((infd_disp = G_open_cell_old(disp, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), disp);
    if (G_get_cellhd(disp, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), disp);
    inrast_disp = G_allocate_raster_buf(data_type_disp);
    

	/***************************************************/ 
	mapset = G_find_cell2(z0m, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), z0m);
    }
    data_type_z0m = G_raster_map_type(z0m, mapset);
    if ((infd_z0m = G_open_cell_old(z0m, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), z0m);
    if (G_get_cellhd(z0m, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), z0m);
    inrast_z0m = G_allocate_raster_buf(data_type_z0m);
    

	/***************************************************/ 
	G_debug(3, "number of rows %d", cellhd.rows);
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast = G_allocate_raster_buf(data_type_output);
    
	/* Create New raster files */ 
	if ((outfd = G_open_raster_new(result, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), result);
    
	/* Process pixels */ 
	for (row = 0; row < nrows; row++)
	 {
	DCELL d;
	DCELL d_disp;
	DCELL d_z0m;
	DCELL d_u_hmoment;
	DCELL d_ublend;
	G_percent(row, nrows, 2);
	
	    /* read input maps */ 
	    if (G_get_raster_row
		(infd_u_hmoment, inrast_u_hmoment, row,
		 data_type_u_hmoment) < 0)
	    G_fatal_error(_("Could not read from <%s>"), u_hmoment);
	if (G_get_raster_row(infd_disp, inrast_disp, row, data_type_disp) <
	     0)
	    G_fatal_error(_("Could not read from <%s>"), disp);
	if (G_get_raster_row(infd_z0m, inrast_z0m, row, data_type_z0m) < 0)
	    G_fatal_error(_("Could not read from <%s>"), z0m);
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
	    switch (data_type_u_hmoment) {
	    case CELL_TYPE:
		d_u_hmoment = (double)((CELL *) inrast_u_hmoment)[col];
		break;
	    case FCELL_TYPE:
		d_u_hmoment = (double)((FCELL *) inrast_u_hmoment)[col];
		break;
	    case DCELL_TYPE:
		d_u_hmoment = ((DCELL *) inrast_u_hmoment)[col];
		break;
	    }
	    switch (data_type_disp) {
	    case CELL_TYPE:
		d_disp = (double)((CELL *) inrast_disp)[col];
		break;
	    case FCELL_TYPE:
		d_disp = (double)((FCELL *) inrast_disp)[col];
		break;
	    case DCELL_TYPE:
		d_disp = ((DCELL *) inrast_disp)[col];
		break;
	    }
	    switch (data_type_z0m) {
	    case CELL_TYPE:
		d_z0m = (double)((CELL *) inrast_z0m)[col];
		break;
	    case FCELL_TYPE:
		d_z0m = (double)((FCELL *) inrast_z0m)[col];
		break;
	    case DCELL_TYPE:
		d_z0m = ((DCELL *) inrast_z0m)[col];
		break;
	    }
	    if (G_is_d_null_value(&d_disp) || G_is_d_null_value(&d_z0m) ||
		 G_is_d_null_value(&d_u_hmoment)) {
		G_set_d_null_value(&outrast[col], 1);
	    }
	    else {
		

				/************************************/ 
		    /* calculate ustar   */ 
		    d_ublend =
		    u_blend(d_u_hmoment, d_disp, hblend, d_z0m, d_u_hmoment);
		outrast[col] = d_ublend;
	    }
	    }
	if (G_put_raster_row(outfd, outrast, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
	}
    G_free(inrast_u_hmoment);
    G_free(inrast_disp);
    G_free(inrast_z0m);
    G_close_cell(infd_u_hmoment);
    G_close_cell(infd_disp);
    G_close_cell(infd_z0m);
    G_free(outrast);
    G_close_cell(outfd);
    G_short_history(result, "raster", &history);
    G_command_history(&history);
    G_write_history(result, &history);
    exit(EXIT_SUCCESS);
}


