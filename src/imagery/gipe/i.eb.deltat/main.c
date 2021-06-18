
/****************************************************************************
 *
 * MODULE:       i.eb.deltat
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the difference of temperature between 2 heights
 *                as seen in Pawan (2004) 
 *                This is a SEBAL initialization parameter for sensible heat. 
 *
 * COPYRIGHT:    (C) 2006 by the GRASS Development Team
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
double delta_t(double tempk);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/* mapset name */

    int nrows, ncols;

    int row, col;

    int wim = 0;

    struct GModule *module;

    struct Option *input1, *output1;

    struct Flag *flag1, *flag2;

    struct History history;	/*metadata */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result1;		/*output raster name */

    
	/*File Descriptors */ 
    int infd_tempk;

    int outfd1;

    char *tempk;

    char *delta;

    int i = 0, j = 0;

    void *inrast_tempk;

    DCELL * outrast1;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_tempk;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("delta T, energy balance, SEBAL");
    module->description =
	_("difference of temperature between two heights as seen in Pawan (2004), this is part of sensible heat flux calculations, as in SEBAL (Bastiaanssen, 1995). A 'w' flag allows for a very generic approximation.");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("tempk");
    input1->description =
	_("Name of the surface skin temperature map [Kelvin]");
    input1->answer = _("tempk");
    output1 = G_define_standard_option(G_OPT_R_INPUT);
    output1->key = _("delta");
    output1->description = _("Name of the output delta layer");
    output1->answer = _("delta");
    flag2 = G_define_flag();
    flag2->key = 'w';
    flag2->description = _("Wim's generic table");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    tempk = input1->answer;
    result1 = output1->answer;
    wim = flag2->answer;
    

	/***************************************************/ 
	mapset = G_find_cell2(tempk, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), tempk);
    }
    data_type_tempk = G_raster_map_type(tempk, mapset);
    if ((infd_tempk = G_open_cell_old(tempk, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), tempk);
    if (G_get_cellhd(tempk, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), tempk);
    inrast_tempk = G_allocate_raster_buf(data_type_tempk);
    

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
	DCELL d_tempk;
	G_percent(row, nrows, 2);
	
	    /* read soil input maps */ 
	    if (G_get_raster_row
		(infd_tempk, inrast_tempk, row, data_type_tempk) < 0)
	    G_fatal_error(_("Could not read from <%s>"), tempk);
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
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
	    if (G_is_d_null_value(&d_tempk)) {
		G_set_d_null_value(&outrast1[col], 1);
	    }
	    else {
		

				/****************************/ 
		    /* calculate delta T        */ 
		    if (wim) {
		    d = 0.3225 * d_tempk - 91.743;
		    if (d < 1) {
			d = 1.0;
		    }
		    else if (d > 13) {
			d = 13.0;
		    }
		}
		else {
		    d = delta_t(d_tempk);
		}
		if (abs(d) > 50.0) {
		    G_set_d_null_value(&outrast1[col], 1);
		}
		outrast1[col] = d;
	    }
	    }
	if (G_put_raster_row(outfd1, outrast1, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
	}
    G_free(inrast_tempk);
    G_close_cell(infd_tempk);
    G_free(outrast1);
    G_close_cell(outfd1);
    G_short_history(result1, "raster", &history);
    G_command_history(&history);
    G_write_history(result1, &history);
    exit(EXIT_SUCCESS);
}


