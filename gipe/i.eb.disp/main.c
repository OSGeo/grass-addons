
/****************************************************************************
 *
 * MODULE:       i.eb.disp
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the displacement height above skin surface
 *                as seen in Pawan (2004), a flag makes savi2lai instead of
 *                direct LAI input.
 *
 * COPYRIGHT:    (C) 2002-2006 by the GRASS Development Team
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
double dis_p(double lai);

double savi_lai(double savi);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/* mapset name */

    int nrows, ncols;

    int row, col;

    struct GModule *module;

    struct Option *input1, *output1;

    struct Flag *flag1, *flag2;

    struct History history;	/*metadata */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result1;		/*output raster name */

    
	/*File Descriptors */ 
    int infd_lai;

    int outfd1;

    char *disp;

    char *lai;

    int i = 0, j = 0;

    void *inrast_lai;

    unsigned char *outrast1;

    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_lai;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("disp, energy balance, SEBAL");
    module->description =
	_("Displacement height above skin surface, as seen in Pawan (2004). A flag (-s) permits direct SAVI input using the equation in the same document, be careful using it.");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("lai");
    input1->description = _("Name of the LAI map [-]");
    input1->answer = _("lai");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->key = _("disp");
    output1->description = _("Name of the output disp layer");
    output1->answer = _("disp");
    flag2 = G_define_flag();
    flag2->key = 's';
    flag2->description = _("use savi2lai conversion (Pawan, 2004)");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    lai = input1->answer;
    result1 = output1->answer;
    

	/***************************************************/ 
	mapset = G_find_cell2(lai, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), lai);
    }
    data_type_lai = G_raster_map_type(lai, mapset);
    if ((infd_lai = G_open_cell_old(lai, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), lai);
    if (G_get_cellhd(lai, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), lai);
    inrast_lai = G_allocate_raster_buf(data_type_lai);
    

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
	DCELL d_lai;
	G_percent(row, nrows, 2);
	
	    /* read soil input maps */ 
	    if (G_get_raster_row(infd_lai, inrast_lai, row, data_type_lai) <
		0)
	    G_fatal_error(_("Could not read from <%s>"), lai);
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
	    d_lai = ((DCELL *) inrast_lai)[col];
	    if (G_is_d_null_value(&d_lai)) {
		((DCELL *) outrast1)[col] = -999.99;
	    }
	    else {
		if (flag2->answer) {
		    

					/********************/ 
			/* savi2lai()       */ 
			d = savi_lai(d_lai);
		    

					/********************/ 
			/* calculate disp   */ 
			d = dis_p(d);
		    ((DCELL *) outrast1)[col] = d;
		}
		else {
		    

					/********************/ 
			/* calculate disp   */ 
			d = dis_p(d_lai);
		    ((DCELL *) outrast1)[col] = d;
		}
	    }
	    }
	if (G_put_raster_row(outfd1, outrast1, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
	}
    G_free(inrast_lai);
    G_close_cell(infd_lai);
    G_free(outrast1);
    G_close_cell(outfd1);
    G_short_history(result1, "raster", &history);
    G_command_history(&history);
    G_write_history(result1, &history);
    exit(EXIT_SUCCESS);
}


