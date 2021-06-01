
/****************************************************************************
 *
 * MODULE:       i.eb.z0m0
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the momentum roughness length
 *               as seen in Bastiaanssen (1995) 
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
double zom_0(double ndvi, double ndvi_max, double hv_ndvimax,
	      double hv_desert);
int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    int heat = 0;		/*Flag for surf. roughness for heat transport output */

    struct GModule *module;

    struct Option *input1, *input2, *input3, *input4;

    struct Option *output1, *output2;

    struct Flag *flag1, *flag2;

    struct History history;	/*metadata */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result1, *result2;	/*output raster name */

    
	/*File Descriptors */ 
    int infd_ndvi;

    int outfd1, outfd2;

    char *ndvi;

    char *z0m, *z0h;

    double coef_z0h, hv_max, hmr;

    int i = 0, j = 0;

    void *inrast_ndvi;

    DCELL * outrast1, *outrast2;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_ndvi;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("roughness length, energy balance, SEBAL");
    module->description =
	_("Momentum roughness length (z0m) and surface roughness for heat transport (z0h) as seen in Bastiaanssen (2004)");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("ndvi");
    input1->description = _("Name of the NDVI map [-1.0;1.0]");
    input2 = G_define_option();
    input2->key = _("coef");
    input2->type = TYPE_DOUBLE;
    input2->required = NO;
    input2->gisprompt = _("parameter,value");
    input2->description =
	_("Value of the converion factor from z0m and z0h (Bastiaanssen (2005) used 0.1)");
    input2->answer = _("0.1");
    input3 = G_define_option();
    input3->key = _("hv_max");
    input3->type = TYPE_DOUBLE;
    input3->required = YES;
    input3->gisprompt = _("parameter,value");
    input3->description =
	_("Value of the vegetation height at max(NDVI) i.e. standard C3 crop could be 1.5m");
    input3->answer = _("1.5");
    input4 = G_define_option();
    input4->key = _("hmr");
    input4->type = TYPE_DOUBLE;
    input4->required = YES;
    input4->gisprompt = _("parameter,value");
    input4->description =
	_("Value of the micro-relief height (h.m-r.) on flat bare ground, most references point to 2cm");
    input4->answer = _("0.02");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the output z0m layer");
    output2 = G_define_standard_option(G_OPT_R_OUTPUT);
    output2->key = _("z0h");
    output2->required = NO;
    output2->description = _("Name of the output z0h layer");
    flag1 = G_define_flag();
    flag1->key = 'h';
    flag1->description = _("z0h output (You have to input a coef value)");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    ndvi = input1->answer;
    if (input2->answer)
	coef_z0h = atof(input2->answer);
    hv_max = atof(input3->answer);
    hmr = atof(input4->answer);
    result1 = output1->answer;
    if (output2->answer)
	result2 = output2->answer;
    if (flag1->answer)
	heat = flag1->answer;
    

	/***************************************************/ 
	mapset = G_find_cell2(ndvi, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), ndvi);
    }
    data_type_ndvi = G_raster_map_type(ndvi, mapset);
    if ((infd_ndvi = G_open_cell_old(ndvi, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), ndvi);
    if (G_get_cellhd(ndvi, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), ndvi);
    inrast_ndvi = G_allocate_raster_buf(data_type_ndvi);
    

	/***************************************************/ 
	G_debug(3, "number of rows %d", cellhd.rows);
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast1 = G_allocate_raster_buf(data_type_output);
    if (input2->answer && output2->answer) {
	outrast2 = G_allocate_raster_buf(data_type_output);
    }
    
	/* Create New raster files */ 
	if ((outfd1 = G_open_raster_new(result1, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), result1);
    if (input2->answer && output2->answer) {
	if ((outfd2 = G_open_raster_new(result2, data_type_output)) < 0)
	    G_fatal_error(_("Could not open <%s>"), result2);
    }
    DCELL d_ndvi;		/* Input raster */
    DCELL d_ndvi_max = 0.0;	/* Generated here */
    
	/* THREAD 1 */ 
	/* NDVI Max */ 
	for (row = 0; row < nrows; row++)
	 {
	G_percent(row, nrows, 2);
	if (G_get_d_raster_row(infd_ndvi, inrast_ndvi, row) < 0)
	    G_fatal_error(_("Could not read from <%s>"), ndvi);
	for (col = 0; col < ncols; col++)
	     {
	    switch (data_type_ndvi) {
	    case CELL_TYPE:
		d_ndvi = (double)((CELL *) inrast_ndvi)[col];
		break;
	    case FCELL_TYPE:
		d_ndvi = (double)((FCELL *) inrast_ndvi)[col];
		break;
	    case DCELL_TYPE:
		d_ndvi = (double)((DCELL *) inrast_ndvi)[col];
		break;
	    }
	    if (G_is_d_null_value(&d_ndvi)) {
		
		    /* do nothing */ 
	    }
	    else if ((d_ndvi) > d_ndvi_max && (d_ndvi) < 0.98) {
		d_ndvi_max = d_ndvi;
	    }
	    }
	}
    G_message("ndvi_max=%f\n", d_ndvi_max);
    
	/* Process pixels */ 
	for (row = 0; row < nrows; row++)
	 {
	DCELL d;
	DCELL d_z0h;
	G_percent(row, nrows, 2);
	
	    /* read input maps */ 
	    if (G_get_raster_row(infd_ndvi, inrast_ndvi, row, data_type_ndvi)
		< 0)
	    G_fatal_error(_("Could not read from <%s>"), ndvi);
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
	    switch (data_type_ndvi) {
	    case CELL_TYPE:
		d_ndvi = (double)((CELL *) inrast_ndvi)[col];
		break;
	    case FCELL_TYPE:
		d_ndvi = (double)((FCELL *) inrast_ndvi)[col];
		break;
	    case DCELL_TYPE:
		d_ndvi = (double)((DCELL *) inrast_ndvi)[col];
		break;
	    }
	    if (G_is_d_null_value(&d_ndvi)) {
		G_set_d_null_value(&outrast1[col], 1);
		if (input2->answer && output2->answer) {
		    G_set_d_null_value(&outrast2[col], 1);
		}
	    }
	    else {
		

				/****************************/ 
		    /* calculate z0m            */ 
		    d = zom_0(d_ndvi, d_ndvi_max, hv_max, hmr);
		outrast1[col] = d;
		if (input2->answer && output2->answer) {
		    d_z0h = d * coef_z0h;
		    outrast2[col] = d_z0h;
		}
	    }
	    }
	if (G_put_raster_row(outfd1, outrast1, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output z0m raster file"));
	if (input2->answer && output2->answer) {
	    if (G_put_raster_row(outfd2, outrast2, data_type_output) < 0)
		G_fatal_error(_("Cannot write to output z0h raster file"));
	}
	}
    G_free(inrast_ndvi);
    G_close_cell(infd_ndvi);
    G_free(outrast1);
    G_close_cell(outfd1);
    if (input2->answer && output2->answer) {
	G_free(outrast2);
	G_close_cell(outfd2);
    }
    G_short_history(result1, "raster", &history);
    G_command_history(&history);
    G_write_history(result1, &history);
    if (input2->answer && output2->answer) {
	G_short_history(result2, "raster", &history);
	G_command_history(&history);
	G_write_history(result2, &history);
    }
    exit(EXIT_SUCCESS);
}


