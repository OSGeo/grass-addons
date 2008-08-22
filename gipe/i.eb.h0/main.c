
/****************************************************************************
 *
 * MODULE:       i.eb.h0
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates sensible heat flux
 *               a flag allows the Bastiaanssen (1995) affine transform 
 *               of surface temperature as used in his SEBAL model.
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
double h0(double roh_air, double cp, double rah, double dtair);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    int sebal = 0;		/*SEBAL Flag for affine transform of surf. temp. */

    struct GModule *module;

    struct Option *input1, *input2, *input3, *input4, *input5;

    struct Option *input6, *input7, *output1;

    struct Flag *flag1, *flag2;

    struct History history;	/*metadata */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result;		/*output raster name */

    
	/*File Descriptors */ 
    int infd_rohair, infd_tempk, infd_rah, infd_dtair;

    int outfd;

    char *rohair, *tempk, *rah, *dtair;

    double cp;		/*air specific heat */

    int i = 0, j = 0;

    double a, b;		/*SEBAL slope and intercepts of surf. temp. */

    void *inrast_rohair, *inrast_tempk, *inrast_rah, *inrast_dtair;

    DCELL * outrast;
    RASTER_MAP_TYPE data_type_rohair;
    RASTER_MAP_TYPE data_type_tempk;
    RASTER_MAP_TYPE data_type_rah;
    RASTER_MAP_TYPE data_type_dtair;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("sensible heat flux, energy balance, SEBAL");
    module->description =
	_("sensible heat flux equation, including flag for SEBAL version (Bastiaanssen, 1995)");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("rohair");
    input1->description = _("Name of the air density map ~[0.9;1.5]");
    input1->answer = _("rohair");
    input2 = G_define_option();
    input2->key = _("cp");
    input2->type = TYPE_DOUBLE;
    input2->required = YES;
    input2->gisprompt = _("parameter, float number");
    input2->description =
	_("Value of the air specific heat [1000.0;1020.0]");
    input2->answer = _("1004.0");
    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = _("dtair");
    input3->description =
	_("Name of the skin-air Surface temperature difference map ~[0.0-80.0]");
    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = _("rah");
    input4->description =
	_("Name of the aerodynamic resistance to heat transport map [s/m]");
    input4->answer = _("rah");
    input5 = G_define_standard_option(G_OPT_R_INPUT);
    input5->key = _("tempk");
    input5->required = NO;
    input5->description =
	_("Name of the surface skin temperature map [degrees Kelvin], used with -s flag and affine coefs, disables dtair input");
    input6 = G_define_option();
    input6->key = _("a");
    input6->type = TYPE_DOUBLE;
    input6->required = NO;
    input6->gisprompt = _("parameter, float number");
    input6->description = _("Value of the slope of the transform");
    input7 = G_define_option();
    input7->key = _("b");
    input7->type = TYPE_DOUBLE;
    input7->required = NO;
    input7->gisprompt = _("parameter, float number");
    input7->description = _("Value of the intercept of the transform");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the output h0 layer");
    flag1 = G_define_flag();
    flag1->key = 's';
    flag1->description =
	_("Affine transform of Surface temperature, needs input of slope and intercept (Bastiaanssen, 1995)");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    rohair = input1->answer;
    cp = atof(input2->answer);
    dtair = input3->answer;
    rah = input4->answer;
    tempk = input5->answer;
    a = atof(input6->answer);
    b = atof(input7->answer);
    result = output1->answer;
    sebal = flag1->answer;
    

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
	if (!sebal) {
	mapset = G_find_cell2(dtair, "");
	if (mapset == NULL) {
	    G_fatal_error(_("cell file [%s] not found"), dtair);
	}
	data_type_dtair = G_raster_map_type(dtair, mapset);
	if ((infd_dtair = G_open_cell_old(dtair, mapset)) < 0)
	    G_fatal_error(_("Cannot open cell file [%s]"), dtair);
	if (G_get_cellhd(dtair, mapset, &cellhd) < 0)
	    G_fatal_error(_("Cannot read file header of [%s]"), dtair);
	inrast_dtair = G_allocate_raster_buf(data_type_dtair);
    }
    

	/***************************************************/ 
	mapset = G_find_cell2(rah, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), rah);
    }
    data_type_rah = G_raster_map_type(rah, mapset);
    if ((infd_rah = G_open_cell_old(rah, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), rah);
    if (G_get_cellhd(rah, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), rah);
    inrast_rah = G_allocate_raster_buf(data_type_rah);
    

	/***************************************************/ 
	if (sebal) {
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
    }
    

	/***************************************************/ 
	G_debug(3, "number of rows %d", cellhd.rows);
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast = G_allocate_raster_buf(data_type_rah);
    
	/* Create New raster files */ 
	if ((outfd = G_open_raster_new(result, data_type_rah)) < 0)
	G_fatal_error(_("Could not open <%s>"), result);
    
	/* Process pixels */ 
	for (row = 0; row < nrows; row++)
	 {
	DCELL d;
	DCELL d_rohair;
	DCELL d_rah;
	DCELL d_dtair;
	DCELL d_affine;
	DCELL d_tempk;
	G_percent(row, nrows, 2);
	
	    /* read input maps */ 
	    if (G_get_raster_row
		(infd_rohair, inrast_rohair, row, data_type_rohair) < 0)
	    G_fatal_error(_("Could not read from <%s>"), rohair);
	if (G_get_raster_row(infd_rah, inrast_rah, row, data_type_rah) < 0)
	    G_fatal_error(_("Could not read from <%s>"), rah);
	if (!sebal) {
	    if (G_get_raster_row
		 (infd_dtair, inrast_dtair, row, data_type_dtair) < 0)
		G_fatal_error(_("Could not read from <%s>"), dtair);
	}
	else {
	    if (G_get_raster_row
		 (infd_tempk, inrast_tempk, row, data_type_tempk) < 0)
		G_fatal_error(_("Could not read from <%s>"), tempk);
	}
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
	    d_rohair = ((DCELL *) inrast_rohair)[col];
	    d_rah = ((DCELL *) inrast_rah)[col];
	    if (!sebal) {
		d_dtair = ((DCELL *) inrast_dtair)[col];
	    }
	    else {
		d_tempk = ((DCELL *) inrast_tempk)[col];
	    }
	    if (G_is_d_null_value(&d_rohair) || G_is_d_null_value(&d_rah) ||
		 (!sebal) && G_is_d_null_value(&d_dtair) || (sebal) &&
		 G_is_d_null_value(&d_tempk)) {
		G_set_d_null_value(&outrast[col], 1);
	    }
	    else {
		

				/************************************/ 
		    /* calculate sensible heat flux     */ 
		    if (!sebal) {
		    d = h0(d_rohair, cp, d_rah, d_dtair);
		}
		else {
		    d_affine = a * d_tempk + b;
		    d = h0(d_rohair, cp, d_rah, d_affine);
		}
		outrast[col] = d;
	    }
	    }
	if (G_put_raster_row(outfd, outrast, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
	}
    G_free(inrast_rohair);
    G_free(inrast_rah);
    if (!sebal) {
	G_free(inrast_dtair);
    }
    else {
	G_free(inrast_tempk);
    }
    G_close_cell(infd_rohair);
    G_close_cell(infd_rah);
    if (!sebal) {
	G_close_cell(infd_dtair);
    }
    else {
	G_close_cell(infd_tempk);
    }
    G_free(outrast);
    G_close_cell(outfd);
    G_short_history(result, "raster", &history);
    G_command_history(&history);
    G_write_history(result, &history);
    exit(EXIT_SUCCESS);
}


