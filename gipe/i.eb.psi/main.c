
/****************************************************************************
 *
 * MODULE:       i.eb.psi
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the psichrometric parameter for heat,
 *               a flag permits output for momentum.
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
double psi_m(double disp, double molength, double height);

double psi_h(double disp, double molength, double height);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    int momentum = 0;		/*Flag for psim */

    struct GModule *module;

    struct Option *input1, *input2, *input3, *input4, *output1, *output2;

    struct Flag *flag1, *flag2;

    struct History history;	/*metadata */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result1, *result2;	/*output raster name */

    
	/*File Descriptors */ 
    int infd_disp, infd_molength;

    int outfd1, outfd2;

    char *disp, *molength;

    double height, height_m;	/*z height for heat and momentum */

    int i = 0, j = 0;

    void *inrast_disp, *inrast_molength;

    DCELL * outrast1, *outrast2;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_disp;
    RASTER_MAP_TYPE data_type_molength;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("psichrometric, energy balance, SEBAL");
    module->description =
	_("psichrometric paramters for heat (standard) and momentum (need flag).");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("disp");
    input1->description = _("Name of the displacement height map");
    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = _("molength");
    input2->description = _("Name of the Monin-Obukov length map");
    input3 = G_define_option();
    input3->key = _("height");
    input3->type = TYPE_DOUBLE;
    input3->required = YES;
    input3->gisprompt = _("Value, parameter");
    input3->description =
	_("Value of the height for heat flux (2.0 in Pawan,2004)");
    input3->answer = _("2.0");
    input4 = G_define_option();
    input4->key = _("height_m");
    input4->type = TYPE_DOUBLE;
    input4->required = NO;
    input4->gisprompt = _("Value, parameter");
    input4->description =
	_("Value of the blending height for momentum (100.0 in Pawan, 2004). Use with flag -m.");
    input4->answer = _("100.0");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the output psih layer");
    output2 = G_define_standard_option(G_OPT_R_OUTPUT);
    output2->key = _("psim");
    output2->description = _("Name of the output psim layer");
    flag1 = G_define_flag();
    flag1->key = 'm';
    flag1->description = _("Output psim (requires height_m parameter)");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    disp = input1->answer;
    molength = input2->answer;
    height = atof(input3->answer);
    height_m = atof(input4->answer);
    result1 = output1->answer;
    result2 = output2->answer;
    momentum = flag1->answer;
    

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
	mapset = G_find_cell2(molength, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), molength);
    }
    data_type_molength = G_raster_map_type(molength, mapset);
    if ((infd_molength = G_open_cell_old(molength, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), molength);
    if (G_get_cellhd(molength, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), molength);
    inrast_molength = G_allocate_raster_buf(data_type_molength);
    

	/***************************************************/ 
	G_debug(3, "number of rows %d", cellhd.rows);
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast1 = G_allocate_raster_buf(data_type_output);
    if (momentum) {
	outrast2 = G_allocate_raster_buf(data_type_output);
    }
    
	/* Create New raster files */ 
	if ((outfd1 = G_open_raster_new(result1, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), result1);
    if (momentum) {
	if ((outfd2 = G_open_raster_new(result2, data_type_output)) < 0)
	    G_fatal_error(_("Could not open <%s>"), result2);
    }
    
	/* Process pixels */ 
	for (row = 0; row < nrows; row++)
	 {
	DCELL d;
	DCELL d_disp;
	DCELL d_molength;
	DCELL d_psih;
	DCELL d_psim;
	G_percent(row, nrows, 2);
	
	    /* read input maps */ 
	    if (G_get_raster_row(infd_disp, inrast_disp, row, data_type_disp)
		< 0)
	    G_fatal_error(_("Could not read from <%s>"), disp);
	if (G_get_raster_row
	     (infd_molength, inrast_molength, row, data_type_molength) < 0)
	    G_fatal_error(_("Could not read from <%s>"), molength);
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
	    d_disp = ((DCELL *) inrast_disp)[col];
	    d_molength = ((DCELL *) inrast_molength)[col];
	    if (G_is_d_null_value(&d_disp) ||
		 G_is_d_null_value(&d_molength)) {
		G_set_d_null_value(&outrast1[col], 1);
		if (momentum) {
		    G_set_d_null_value(&outrast2[col], 1);
		}
	    }
	    else {
		

				/************************************/ 
		    /* calculate psih   */ 
		    d_psih = psi_h(d_disp, d_molength, height);
		outrast1[col] = d_psih;
		if (momentum) {
		    d_psim = psi_m(d_disp, d_molength, height_m);
		    outrast2[col] = d_psim;
		}
	    }
	    }
	if (G_put_raster_row(outfd1, outrast1, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
	if (momentum) {
	    if (G_put_raster_row(outfd1, outrast1, data_type_output) < 0)
		G_fatal_error(_("Cannot write to output raster file"));
	}
	}
    G_free(inrast_disp);
    G_free(inrast_molength);
    G_close_cell(infd_disp);
    G_close_cell(infd_molength);
    G_free(outrast1);
    G_close_cell(outfd1);
    G_short_history(result1, "raster", &history);
    G_command_history(&history);
    G_write_history(result1, &history);
    if (momentum) {
	G_free(outrast2);
	G_close_cell(outfd2);
	G_short_history(result2, "raster", &history);
	G_command_history(&history);
	G_write_history(result2, &history);
    }
    exit(EXIT_SUCCESS);
}


