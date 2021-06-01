
/****************************************************************************
 *
 * MODULE:       r.soilusda2tex
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Transforms USDA 1951 (p209) soil classes into
 * 		 maps of percentage of texture (sand/clay/silt).
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
#include <grass/glocale.h>
    
#define POLYGON_DIMENSION 20
double usda2psand(int texture);

double usda2psilt(int texture);

double usda2pclay(int texture);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/* mapset name */

    int nrows, ncols;

    int row, col;

    struct GModule *module;

    struct Option *input1, *output1, *output2, *output3, *output4;

    struct Flag *flag1;

    struct History history;	/*metadata */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/* input raster name */

    char *result1, *result2, *result3;	/*output raster name */

    
	/*File Descriptors */ 
    int infd_soilusda;

    int outfd1, outfd2, outfd3;

    char *soilusda;

    int i = 0, j = 0;

    void *inrast_soilusda;

    DCELL * outrast1, *outrast2, *outrast3;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_soilusda;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("soil, USDA, classification");
    module->description =
	_("USDA Soil classes conversion to texture fractions");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("soilusda");
    input1->description =
	_("Name of the USDA Soil classes reclassified [1-12]");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->key = _("pclay");
    output1->description =
	_("Name of the Soil clay fraction layer [0.0-1.0]");
    output1->answer = _("pclay");
    output2 = G_define_standard_option(G_OPT_R_OUTPUT);
    output2->key = _("psilt");
    output2->description =
	_("Name of the Soil silt fraction layer [0.0-1.0]");
    output2->answer = _("psilt");
    output3 = G_define_standard_option(G_OPT_R_OUTPUT);
    output3->key = _("psand");
    output3->description =
	_("Name of the Soil sand fraction layer [0.0-1.0]");
    output3->answer = _("psand");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    soilusda = input1->answer;
    result1 = output1->answer;
    result2 = output2->answer;
    result3 = output3->answer;
    

	/***************************************************/ 
	mapset = G_find_cell2(soilusda, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), soilusda);
    }
    data_type_soilusda = G_raster_map_type(soilusda, mapset);
    if ((infd_soilusda = G_open_cell_old(soilusda, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), soilusda);
    if (G_get_cellhd(soilusda, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), soilusda);
    inrast_soilusda = G_allocate_raster_buf(data_type_soilusda);
    

	/***************************************************/ 
	G_debug(3, "number of rows %d", cellhd.rows);
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast1 = G_allocate_raster_buf(data_type_output);
    outrast2 = G_allocate_raster_buf(data_type_output);
    outrast3 = G_allocate_raster_buf(data_type_output);
    
	/* Create New raster files */ 
	if ((outfd1 = G_open_raster_new(result1, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), result1);
    if ((outfd2 = G_open_raster_new(result2, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), result2);
    if ((outfd3 = G_open_raster_new(result3, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), result3);
    
	/* Process pixels */ 
	for (row = 0; row < nrows; row++)
	 {
	DCELL d;
	DCELL d_sand;
	DCELL d_clay;
	DCELL d_silt;
	DCELL d_soilusda;
	G_percent(row, nrows, 2);
	
	    /* read soil classes [0-11] input map */ 
	    if (G_get_raster_row
		(infd_soilusda, inrast_soilusda, row, data_type_soilusda) < 0)
	    G_fatal_error(_("Could not read from <%s>"), soilusda);
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
	    switch (data_type_soilusda) {
	    case CELL_TYPE:
		d_soilusda = (double)((CELL *) inrast_soilusda)[col];
		break;
	    case FCELL_TYPE:
		d_soilusda = (double)((FCELL *) inrast_soilusda)[col];
		break;
	    case DCELL_TYPE:
		d_soilusda = ((DCELL *) inrast_soilusda)[col];
		break;
	    }
	    if (G_is_d_null_value(&d_soilusda)) {
		G_set_d_null_value(&outrast1[col], 1);
		G_set_d_null_value(&outrast2[col], 1);
		G_set_d_null_value(&outrast3[col], 1);
	    }
	    else {
		

				/************************************/ 
		    /* convert to prct                  */ 
		    d_clay = usda2pclay(d_soilusda);
		d_silt = usda2psilt(d_soilusda);
		d_sand = usda2psand(d_soilusda);
		

				/************************************/ 
		    outrast1[col] = d_clay;
		outrast2[col] = d_silt;
		outrast3[col] = d_sand;
	    }
	    }
	if (G_put_raster_row(outfd1, outrast1, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file clay"));
	if (G_put_raster_row(outfd2, outrast2, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file silt"));
	if (G_put_raster_row(outfd3, outrast3, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file sand"));
	}
    G_free(inrast_soilusda);
    G_close_cell(infd_soilusda);
    G_free(outrast1);
    G_close_cell(outfd1);
    G_free(outrast2);
    G_close_cell(outfd2);
    G_free(outrast3);
    G_close_cell(outfd3);
    G_short_history(result1, "raster", &history);
    G_command_history(&history);
    G_write_history(result1, &history);
    G_short_history(result2, "raster", &history);
    G_command_history(&history);
    G_write_history(result2, &history);
    G_short_history(result3, "raster", &history);
    G_command_history(&history);
    G_write_history(result3, &history);
    exit(EXIT_SUCCESS);
}


