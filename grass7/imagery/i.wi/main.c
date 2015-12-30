
/****************************************************************************
 *
 * MODULE:       i.wi
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates water indices 
 *
 * COPYRIGHT:    (C) 2008-2016 by the GRASS Development Team
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
#include <grass/raster.h>
#include <grass/glocale.h>
double ls_wi(double nirchan, double swirchan);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */
    char *mapset;		/*mapset name */
    int nrows, ncols;
    int row, col;
    char *wiflag;		/*Switch for particular index */
    struct GModule *module;
    struct Option *input1, *input2, *input3, *output;
    struct Flag *flag1;
    struct History history;	/*metadata */
    struct Colors colors;	/*Color rules */
    char *name;			/*input raster name */
    char *result;		/*output raster name */
    int infd_nirchan, infd_swirchan;
    int outfd;
    char *nirchan, *swirchan;
    int i = 0, j = 0;
    void *inrast_nirchan, *inrast_swirchan;

    DCELL * outrast;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_nirchan;
    RASTER_MAP_TYPE data_type_swirchan;
    /************************************/ 
    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("water"));
    G_add_keyword(_("index"));
    G_add_keyword(_("biophysical"));
    module->description =
	_("Water indices from nir and swir for the time being");
    
    /* Define the different options */ 
    input1 = G_define_option();
    input1->key = _("winame");
    input1->type = TYPE_STRING;
    input1->required = YES;
    input1->gisprompt = _("Name of WI");
    input1->description = _("Name of WI: lswi");
    input1->answer = _("lswi");
    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = _("nir");
    input2->description =
	_("Name of the NIR Channel surface reflectance map [0.0;1.0]");
    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = _("swir");
    input3->description =
	_("Name of the SWIR Channel surface reflectance map [0.0;1.0]");
    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->description = _("Name of the output wi layer");
    
    /********************/ 
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    wiflag = input1->answer;
    nirchan = input2->answer;
    swirchan = input3->answer;
    result = output->answer;

    /***************************************************/ 
    data_type_nirchan = Rast_map_type(nirchan, mapset);
    if ((infd_nirchan = Rast_open_old(nirchan, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), nirchan);
    Rast_get_cellhd(nirchan, mapset, &cellhd);
    inrast_nirchan = Rast_allocate_buf(data_type_nirchan);
    /***************************************************/ 
    data_type_swirchan = Rast_map_type(swirchan, mapset);
    infd_swirchan = Rast_open_old(swirchan, mapset);
	G_fatal_error(_("Cannot open cell file [%s]"), swirchan);
    Rast_get_cellhd(swirchan, mapset, &cellhd);
    inrast_swirchan = Rast_allocate_buf(data_type_swirchan);
    /***************************************************/ 
    G_debug(3, "number of rows %d", cellhd.rows);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    outrast = Rast_allocate_buf(data_type_output);
   
    /* Create New raster files */ 
    outfd = Rast_open_new(result, data_type_output);
    /* Process pixels */ 
    for (row = 0; row < nrows; row++)
    {
	DCELL d;
	DCELL d_nirchan;
	DCELL d_swirchan;
	G_percent(row, nrows, 2);
	Rast_get_row
	     (infd_nirchan, inrast_nirchan, row, data_type_nirchan);
	Rast_get_row
	     (infd_swirchan, inrast_swirchan, row, data_type_swirchan);
	/*process the data */ 
	for (col = 0; col < ncols; col++)
	{
	    switch (data_type_nirchan) {
	    case CELL_TYPE:
		d_nirchan = (double)((CELL *) inrast_nirchan)[col];
		break;
	    case FCELL_TYPE:
		d_nirchan = (double)((FCELL *) inrast_nirchan)[col];
		break;
	    case DCELL_TYPE:
		d_nirchan = ((DCELL *) inrast_nirchan)[col];
		break;
	    }
	    switch (data_type_swirchan) {
	    case CELL_TYPE:
		d_swirchan = (double)((CELL *) inrast_swirchan)[col];
		break;
	    case FCELL_TYPE:
		d_swirchan = (double)((FCELL *) inrast_swirchan)[col];
		break;
	    case DCELL_TYPE:
		d_swirchan = ((DCELL *) inrast_swirchan)[col];
		break;
	    }
	    if (Rast_is_d_null_value(&d_nirchan) ||
		 Rast_is_d_null_value(&d_swirchan)) {
		Rast_set_d_null_value(&outrast[col], 1);
	    }
	    else {
                /*calculate lswi                    */ 
		if (!strcoll(wiflag, "lswi")) {
		if (d_nirchan + d_swirchan < 0.001) {
			Rast_set_d_null_value(&outrast[col], 1);
		}
		else {
			d = ls_wi(d_nirchan, d_swirchan);
			((DCELL *) outrast)[col] = d;
		    }
		}
	    }
	}
        Rast_put_row(outfd, outrast, data_type_output);
	}
    free(inrast_nirchan);
    Rast_close(infd_nirchan);
    free(inrast_swirchan);
    Rast_close(infd_swirchan);
    free(outrast);
    Rast_close(outfd);
    /* Color from -1.0 to +1.0 in grey */ 
    Rast_short_history(result, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result, &history);
    exit(EXIT_SUCCESS);
}


