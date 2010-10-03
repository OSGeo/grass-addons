
/****************************************************************************
 *
 * MODULE:       r.soiltex2prop
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Transforms percentage of texture (sand/clay)
 *               into USDA 1951 (p209) soil texture classes and then
 *               into USLE soil erodibility factor (K) as an output
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
    
#define POLYGON_DIMENSION 50
int point_in_triangle(double point_x, double point_y, double point_z,
		      double t1_x, double t1_y, double t1_z, double t2_x,
		      double t2_y, double t2_z, double t3_x, double t3_y,
		      double t3_z);
double prct2porosity(double sand_input, double clay_input);

double prct2ksat(double sand_input, double clay_input);

double prct2hf(double sand_input, double clay_input);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    struct GModule *module;

    struct Option *input1, *input2, *input3, *input4;

    struct Option *output1, *output2, *output3;

    struct Flag *flag1;

    struct History history;	/*metadata */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result1;		/*output porosity raster name */

    char *result2;		/*output KSat raster name */

    char *result3;		/*output Hf raster name */

    
	/*File Descriptors */ 
    int infd_psand, infd_pclay;

    int outfd1, outfd2, outfd3;

    char *psand, *pclay;

    int i = 0, j = 0;

    void *inrast_psand, *inrast_pclay;

    DCELL * outrast1, *outrast2, *outrast3;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_psand;
    RASTER_MAP_TYPE data_type_pclay;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("soil, texture, porosity, Ksat, Hf");
    module->description =
	_("Texture to soil properties (porosity, Ksat,Hf)");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("psand");
    input1->description = _("Name of the Soil sand fraction map [0.0-1.0]");
    input1->answer = _("psand");
    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = _("pclay");
    input2->description = _("Name of the Soil clay fraction map [0.0-1.0]");
    input2->answer = _("pclay");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->key = _("porosity");
    output1->description = _("Name of the output porosity layer");
    output1->answer = _("porosity");
    output2 = G_define_standard_option(G_OPT_R_OUTPUT);
    output2->key = _("ksat");
    output2->description = _("Name of the output Ksat layer");
    output2->answer = _("ksat");
    output3 = G_define_standard_option(G_OPT_R_OUTPUT);
    output3->key = _("hf");
    output3->description = _("Name of the output hf layer");
    output3->answer = _("hf");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    psand = input1->answer;
    pclay = input2->answer;
    result1 = output1->answer;
    result2 = output2->answer;
    result3 = output3->answer;
    

	/***************************************************/ 
	mapset = G_find_cell2(psand, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), psand);
    }
    data_type_psand = G_raster_map_type(psand, mapset);
    if ((infd_psand = G_open_cell_old(psand, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), psand);
    if (G_get_cellhd(psand, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), psand);
    inrast_psand = G_allocate_raster_buf(data_type_psand);
    

	/***************************************************/ 
	mapset = G_find_cell2(pclay, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), pclay);
    }
    data_type_pclay = G_raster_map_type(pclay, mapset);
    if ((infd_pclay = G_open_cell_old(pclay, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), pclay);
    if (G_get_cellhd(pclay, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), pclay);
    inrast_pclay = G_allocate_raster_buf(data_type_pclay);
    

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
	double tex[4] = { 0.0, 0.0, 0.0, 0.0 };
	G_percent(row, nrows, 2);
	
	    /* read soil input maps */ 
	    if (G_get_raster_row
		(infd_psand, inrast_psand, row, data_type_psand) < 0)
	    G_fatal_error(_("Could not read from <%s>"), psand);
	if (G_get_raster_row(infd_pclay, inrast_pclay, row, data_type_pclay)
	     < 0)
	    G_fatal_error(_("Could not read from <%s>"), pclay);
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
	    d_sand = ((DCELL *) inrast_psand)[col];
	    d_clay = ((DCELL *) inrast_pclay)[col];
	    if (G_is_d_null_value(&d_sand) || G_is_d_null_value(&d_clay)) {
		G_set_d_null_value(&outrast1[col], 1);
		G_set_d_null_value(&outrast2[col], 1);
		G_set_d_null_value(&outrast3[col], 1);
	    }
	    else {
		

				/************************************/ 
		    /* convert to porosity              */ 
		    d = prct2porosity(d_sand * 100.0, d_clay * 100.0);
		outrast1[col] = d;
		d = prct2ksat(d_sand * 100.0, d_clay * 100.0);
		outrast2[col] = d;
		d = prct2hf(d_sand * 100.0, d_clay * 100.0);
		outrast3[col] = d;
	    }
	    }
	if (G_put_raster_row(outfd1, outrast1, data_type_output) < 0)
	    G_fatal_error(_("Cannot write output raster file1"));
	if (G_put_raster_row(outfd2, outrast2, data_type_output) < 0)
	    G_fatal_error(_("Cannot write output raster file2"));
	if (G_put_raster_row(outfd3, outrast3, data_type_output) < 0)
	    G_fatal_error(_("Cannot write output raster file3"));
	}
    G_free(inrast_psand);
    G_free(inrast_pclay);
    G_close_cell(infd_psand);
    G_close_cell(infd_pclay);
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


