
/****************************************************************************
 *
 * MODULE:       i.modis.stateqa
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Converts State Quality Assessment flags into human readable
 *		 classes for Modis surface reflectance products 500m
 * 		 (MOD09A)
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

/* 500m State QA Products in MOD09A */ 
CELL stateqa500a(CELL pixel);
CELL stateqa500b(CELL pixel);
CELL stateqa500c(CELL pixel);
CELL stateqa500d(CELL pixel);
CELL stateqa500e(CELL pixel);
CELL stateqa500f(CELL pixel);
CELL stateqa500g(CELL pixel);
CELL stateqa500h(CELL pixel);
CELL stateqa500i(CELL pixel);
CELL stateqa500j(CELL pixel);
CELL stateqa500k(CELL pixel);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */
    int nrows, ncols;
    int row, col;
    char *qcflag;		/*Switch for particular index */
    struct GModule *module;
    struct Option *input1, *input2, *output;
    struct Flag *flag1;
    struct History history;	/*metadata */
    struct Colors colors;	/*Color rules */

    /************************************/ 
    char *result;/*output raster name */

    /*File Descriptors */ 
    int infd;
    int outfd;
    char *qcchan;
    CELL *inrast;
    CELL *outrast;
    RASTER_MAP_TYPE data_type_output = CELL_TYPE;

    /************************************/ 
    G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("imagery, State QA, Quality Control, surface reflectance, Modis");
    module->description =
	_("Extract quality control parameters from Modis 500m State QA layers");

    /* Define the different options */ 
    input1 = G_define_option();
    input1->key = _("qcname");
    input1->type = TYPE_STRING;
    input1->required = YES;
    input1->gisprompt = _("Name of QC type to extract");
    input1->description = _("Name of QC");
    input1->descriptions =_("cloud_state;Cloud State;"
                            "cloud_shadow;Cloud Shadow;"
                            "land_water_flag;Land or Water Flag;"
                            "aerosol_quantity;Quantity of Aerosol;"
                            "cirrus_detected;If Cirrus Were Detected;"
                            "internal_cloud_alg_flag;Flag for Internal Cloud Algorithm;"
                            "internal_fire_alg_flag;Flag for Internal Fire Algorithm;"
                            "MOD35_snow_ice_flag;Flag for Snow and Ice from MOD35;"
                            "pixel_adjacent_to_cloud;Flag Pixel Adjacent to Cloud;"
                            "brdf_correction;Flag for Correction of BRDF;"
                            "internal_snow_mask;Internal Mask for Snow;");
    input1->answer = _("cloud_state");

    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->description =
	_("Name of the surface reflectance state QA layer [bit array]");

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->key = _("output");
    output->description =
	_("Name of the output state QA type classification layer");
    output->answer = _("qc");

    /********************/ 
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    qcflag = input1->answer;
    qcchan = input2->answer;

    result = output->answer;

    if ((infd = G_open_cell_old(qcchan, "")) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), qcchan);

    if (G_get_cellhd(qcchan, "", &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), qcchan);

    inrast = G_allocate_c_raster_buf();

    G_debug(3, "number of rows %d", cellhd.rows);
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast = G_allocate_c_raster_buf();

    /* Create New raster files */ 
    if ((outfd = G_open_raster_new(result, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), result);

    /* Process pixels */ 
    for (row = 0; row < nrows; row++)
    {
	CELL c;
	CELL qa500chan;
	G_percent(row, nrows, 2);
	if (G_get_c_raster_row(infd, inrast, row) < 0)
	    G_fatal_error(_("Could not read from <%s>"), qcchan);

	/*process the data */ 
	for (col = 0; col < ncols; col++)
	{
	    c = inrast[col];
            qa500chan = c ;

	    if (G_is_c_null_value(&c))
		G_set_c_null_value(&outrast[col], 1);
	    else if (!strcmp(qcflag, "cloud_state")) 
		/*calculate cloud state */ 
		c = stateqa500a(qa500chan);
	    else if (!strcmp(qcflag, "cloud_shadow"))
		/*calculate cloud state  */ 
		c = stateqa500b(qa500chan);
	    else if (!strcmp(qcflag, "land_water_flag")) 
		/*calculate land/water flag */ 
		c = stateqa500c(qa500chan);
	    else if (!strcmp(qcflag, "aerosol_quantity")) 
		/*calculate aerosol quantity */ 
		c = stateqa500d(qa500chan);
	    else if (!strcmp(qcflag, "cirrus_detected")) 
		/*calculate cirrus detected flag */ 
		c = stateqa500e(qa500chan);
	    else if (!strcmp(qcflag, "internal_cloud_alg_flag"))
		/*calculate internal cloud algorithm flag */ 
		c = stateqa500f(qa500chan);
	    else if (!strcmp(qcflag, "internal_fire_alg_flag"))
		/*calculate internal fire algorithm flag */ 
		c = stateqa500g(qa500chan);
	    else if (!strcmp(qcflag, "mod35_snow_ice_flag"))
		/*calculate MOD35 snow/ice flag */ 
		c = stateqa500h(qa500chan);
	    else if (!strcmp(qcflag, "pixel_adjacent_to_cloud"))
		/*calculate pixel is adjacent to cloud flag */ 
		c = stateqa500i(qa500chan);
	    else if (!strcmp(qcflag, "brdf_correction"))
		/*calculate BRDF correction performed flag */ 
		c = stateqa500j(qa500chan);
	    else if (!strcmp(qcflag, "internal_snow_mask"))
		/*calculate internal snow mask flag */ 
		c = stateqa500k(qa500chan);
	    else
		G_fatal_error(_("Unknown flag name, please check spelling"));

	    outrast[col] = c;
	}

	if (G_put_c_raster_row(outfd, outrast) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
    }

    G_free(inrast);
    G_close_cell(infd);
    G_free(outrast);
    G_close_cell(outfd);

    /* Color from 0 to 7 in grey */ 
    G_init_colors(&colors);
    G_add_color_rule(0, 0, 0, 0, 7, 255, 255, 255, &colors);
    G_short_history(result, "raster", &history);
    G_command_history(&history);
    G_write_history(result, &history);
    exit(EXIT_SUCCESS);
}


