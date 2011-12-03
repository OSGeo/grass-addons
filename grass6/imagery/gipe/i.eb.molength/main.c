
/****************************************************************************
 *
 * MODULE:       i.eb.molength
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the Monin-Obukov Length
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
double mo_length(double roh_air, double cp, double ustar, double tempk,
		  double h0);
int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    struct GModule *module;

    struct Option *input1, *input2, *input3, *input4, *input5;

    struct Option *output1;

    struct Flag *flag1;

    struct History history;	/*metadata */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result;		/*output raster name */

    
	/*File Descriptors */ 
    int infd_rohair, infd_tempk, infd_ustar, infd_h0;

    int outfd;

    char *rohair, *tempk, *ustar, *h0;

    double cp;		/*air specific heat */

    int i = 0, j = 0;

    void *inrast_rohair, *inrast_tempk, *inrast_ustar, *inrast_h0;

    DCELL * outrast;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_rohair;
    RASTER_MAP_TYPE data_type_tempk;
    RASTER_MAP_TYPE data_type_ustar;
    RASTER_MAP_TYPE data_type_h0;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("Monin-Obukov Length, energy balance, SEBAL");
    module->description = _("Monin-Obukov Length");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("rohair");
    input1->description = _("Name of the air density map ~[0.9;1.5]");
    input2 = G_define_option();
    input2->key = _("cp");
    input2->type = TYPE_DOUBLE;
    input2->required = YES;
    input2->gisprompt = _("parameter, float number");
    input2->description =
	_("Value of the air specific heat [1000.0;1020.0]");
    input2->answer = _("1004.0");
    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = _("ustar");
    input3->description = _("Name of the ustar map");
    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = _("tempk");
    input4->description =
	_("Name of the surface skin temperature map [degrees Kelvin]");
    input5 = G_define_standard_option(G_OPT_R_INPUT);
    input5->key = _("h0");
    input5->description = _("Name of the sensible heat flux map");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the output Monin-Obukov Length layer");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    rohair = input1->answer;
    cp = atof(input2->answer);
    ustar = input3->answer;
    tempk = input4->answer;
    h0 = input5->answer;
    result = output1->answer;
    

	/***************************************************/ 
	mapset = G_find_cell2(rohair, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), rohair);
    }
    data_type_rohair = G_raster_map_type(rohair, mapset);
    if ((infd_rohair = G_open_cell_old(rohair, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), rohair);
    if (G_get_cellhd(rohair, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), rohair);
    inrast_rohair = G_allocate_raster_buf(data_type_rohair);
    

	/***************************************************/ 
	mapset = G_find_cell2(ustar, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), ustar);
    }
    data_type_ustar = G_raster_map_type(ustar, mapset);
    if ((infd_ustar = G_open_cell_old(ustar, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), ustar);
    if (G_get_cellhd(ustar, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), ustar);
    inrast_ustar = G_allocate_raster_buf(data_type_ustar);
    

	/***************************************************/ 
	mapset = G_find_cell2(tempk, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), tempk);
    }
    data_type_tempk = G_raster_map_type(tempk, mapset);
    if ((infd_tempk = G_open_cell_old(tempk, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), tempk);
    if (G_get_cellhd(tempk, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), tempk);
    inrast_tempk = G_allocate_raster_buf(data_type_tempk);
    

	/***************************************************/ 
	mapset = G_find_cell2(h0, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), h0);
    }
    data_type_h0 = G_raster_map_type(h0, mapset);
    if ((infd_h0 = G_open_cell_old(h0, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), h0);
    if (G_get_cellhd(h0, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), h0);
    inrast_h0 = G_allocate_raster_buf(data_type_h0);
    

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
	DCELL d_rohair;
	DCELL d_ustar;
	DCELL d_tempk;
	DCELL d_h0;
	G_percent(row, nrows, 2);
	
	    /* read input maps */ 
	    if (G_get_raster_row
		(infd_rohair, inrast_rohair, row, data_type_rohair) < 0)
	    G_fatal_error(_("Could not read from <%s>"), rohair);
	if (G_get_raster_row(infd_ustar, inrast_ustar, row, data_type_ustar)
	     < 0)
	    G_fatal_error(_("Could not read from <%s>"), ustar);
	if (G_get_raster_row(infd_tempk, inrast_tempk, row, data_type_tempk)
	     < 0)
	    G_fatal_error(_("Could not read from <%s>"), tempk);
	if (G_get_raster_row(infd_h0, inrast_h0, row, data_type_h0) < 0)
	    G_fatal_error(_("Could not read from <%s>"), h0);
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
	    switch (data_type_rohair) {
	    case CELL_TYPE:
		d_rohair = (double)((CELL *) inrast_rohair)[col];
		break;
	    case FCELL_TYPE:
		d_rohair = (double)((FCELL *) inrast_rohair)[col];
		break;
	    case DCELL_TYPE:
		d_rohair = ((DCELL *) inrast_rohair)[col];
		break;
	    }
	    switch (data_type_ustar) {
	    case CELL_TYPE:
		d_ustar = (double)((CELL *) inrast_ustar)[col];
		break;
	    case FCELL_TYPE:
		d_ustar = (double)((FCELL *) inrast_ustar)[col];
		break;
	    case DCELL_TYPE:
		d_ustar = ((DCELL *) inrast_ustar)[col];
		break;
	    }
	    switch (data_type_tempk) {
	    case CELL_TYPE:
		d_tempk = (double)((CELL *) inrast_tempk)[col];
		break;
	    case FCELL_TYPE:
		d_tempk = (double)((FCELL *) inrast_tempk)[col];
		break;
	    case DCELL_TYPE:
		d_tempk = ((DCELL *) inrast_tempk)[col];
		break;
	    }
	    switch (data_type_h0) {
	    case CELL_TYPE:
		d_h0 = (double)((CELL *) inrast_h0)[col];
		break;
	    case FCELL_TYPE:
		d_h0 = (double)((FCELL *) inrast_h0)[col];
		break;
	    case DCELL_TYPE:
		d_h0 = ((DCELL *) inrast_h0)[col];
		break;
	    }
	    if (G_is_d_null_value(&d_rohair) || G_is_d_null_value(&d_ustar)
		 || G_is_d_null_value(&d_tempk) ||
		 G_is_d_null_value(&d_h0)) {
		G_set_d_null_value(&outrast[col], 1);
	    }
	    else {
		

				/************************************/ 
		    /* calculate Monin-Obukov Length    */ 
		    d = mo_length(d_rohair, cp, d_ustar, d_tempk, d_h0);
		outrast[col] = d;
	    }
	    }
	if (G_put_raster_row(outfd, outrast, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
	}
    G_free(inrast_rohair);
    G_free(inrast_ustar);
    G_free(inrast_tempk);
    G_free(inrast_h0);
    G_close_cell(infd_rohair);
    G_close_cell(infd_ustar);
    G_close_cell(infd_tempk);
    G_close_cell(infd_h0);
    G_free(outrast);
    G_close_cell(outfd);
    G_short_history(result, "raster", &history);
    G_command_history(&history);
    G_write_history(result, &history);
    exit(EXIT_SUCCESS);
}


