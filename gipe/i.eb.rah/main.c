
/****************************************************************************
 *
 * MODULE:       i.eb.rah
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates aerodynamic resistance to heat transport
 *               This has been seen in Pawan (2004).
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
double ra_h(double disp, double z0h, double psih, double ustar, double hu);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    struct GModule *module;

    struct Option *input1, *input2, *input3, *input4;

    struct Option *input5, *output1;

    struct Flag *flag1;

    struct History history;	/*metadata */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result;		/*output raster name */

    
	/*File Descriptors */ 
    int infd_disp, infd_z0h, infd_psih, infd_ustar;

    int infd_hu, outfd;

    char *disp, *z0h, *psih, *ustar, *hu;

    double cp;		/*air specific heat */

    int i = 0, j = 0;

    double a, b;		/*SEBAL slope and intercepts of surf. temp. */

    void *inrast_disp, *inrast_z0h, *inrast_psih;

    void *inrast_hu, *inrast_ustar;

    DCELL * outrast;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_disp;
    RASTER_MAP_TYPE data_type_z0h;
    RASTER_MAP_TYPE data_type_psih;
    RASTER_MAP_TYPE data_type_ustar;
    RASTER_MAP_TYPE data_type_hu;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("rah, energy balance, SEBAL");
    module->description =
	_("aerodynamic resistance to heat transport as in Pawan (2004).");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("disp");
    input1->description = _("Name of the displacement height map");
    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = _("z0h");
    input2->description =
	_("Name of the height of heat flux roughness length map");
    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = _("psih");
    input3->description =
	_("Name of the psichrometric parameter for heat flux map");
    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = _("ustar");
    input4->description = _("Name of the nominal wind speed map");
    input5 = G_define_standard_option(G_OPT_R_INPUT);
    input5->key = _("hu");
    input5->description =
	_("Name of the height of wind measurement (typically 2 m) map");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the output rah layer");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    disp = input1->answer;
    z0h = input2->answer;
    psih = input3->answer;
    ustar = input4->answer;
    hu = input5->answer;
    result = output1->answer;
    

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
	mapset = G_find_cell2(z0h, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), z0h);
    }
    data_type_z0h = G_raster_map_type(z0h, mapset);
    if ((infd_z0h = G_open_cell_old(z0h, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), z0h);
    if (G_get_cellhd(z0h, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), z0h);
    inrast_z0h = G_allocate_raster_buf(data_type_z0h);
    

	/***************************************************/ 
	mapset = G_find_cell2(psih, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), psih);
    }
    data_type_psih = G_raster_map_type(psih, mapset);
    if ((infd_psih = G_open_cell_old(psih, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), psih);
    if (G_get_cellhd(psih, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), psih);
    inrast_psih = G_allocate_raster_buf(data_type_psih);
    

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
	mapset = G_find_cell2(hu, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), hu);
    }
    data_type_hu = G_raster_map_type(hu, mapset);
    if ((infd_ustar = G_open_cell_old(ustar, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), hu);
    if (G_get_cellhd(hu, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), hu);
    inrast_hu = G_allocate_raster_buf(data_type_hu);
    

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
	DCELL d_rah;
	DCELL d_disp;
	DCELL d_z0h;
	DCELL d_psih;
	DCELL d_ustar;
	DCELL d_hu;
	G_percent(row, nrows, 2);
	
	    /* read input maps */ 
	    if (G_get_raster_row(infd_disp, inrast_disp, row, data_type_disp)
		< 0)
	    G_fatal_error(_("Could not read from <%s>"), disp);
	if (G_get_raster_row(infd_z0h, inrast_z0h, row, data_type_z0h) < 0)
	    G_fatal_error(_("Could not read from <%s>"), z0h);
	if (G_get_raster_row(infd_psih, inrast_psih, row, data_type_psih) <
	     0)
	    G_fatal_error(_("Could not read from <%s>"), psih);
	if (G_get_raster_row(infd_ustar, inrast_ustar, row, data_type_ustar)
	     < 0)
	    G_fatal_error(_("Could not read from <%s>"), ustar);
	if (G_get_raster_row(infd_hu, inrast_hu, row, data_type_hu) < 0)
	    G_fatal_error(_("Could not read from <%s>"), hu);
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
	    switch (data_type_disp) {
	    case CELL_TYPE:
		d_disp = (double)((CELL *) inrast_disp)[col];
		break;
	    case FCELL_TYPE:
		d_disp = (double)((FCELL *) inrast_disp)[col];
		break;
	    case DCELL_TYPE:
		d_disp = (double)((DCELL *) inrast_disp)[col];
		break;
	    }
	    switch (data_type_disp) {
	    case CELL_TYPE:
		d_z0h = (double)((CELL *) inrast_z0h)[col];
		break;
	    case FCELL_TYPE:
		d_z0h = (double)((FCELL *) inrast_z0h)[col];
		break;
	    case DCELL_TYPE:
		d_z0h = (double)((DCELL *) inrast_z0h)[col];
		break;
	    }
	    switch (data_type_disp) {
	    case CELL_TYPE:
		d_psih = (double)((CELL *) inrast_psih)[col];
		break;
	    case FCELL_TYPE:
		d_psih = (double)((FCELL *) inrast_psih)[col];
		break;
	    case DCELL_TYPE:
		d_psih = (double)((DCELL *) inrast_psih)[col];
		break;
	    }
	    switch (data_type_disp) {
	    case CELL_TYPE:
		d_ustar = (double)((CELL *) inrast_ustar)[col];
		break;
	    case FCELL_TYPE:
		d_ustar = (double)((FCELL *) inrast_ustar)[col];
		break;
	    case DCELL_TYPE:
		d_ustar = (double)((DCELL *) inrast_ustar)[col];
		break;
	    }
	    switch (data_type_disp) {
	    case CELL_TYPE:
		d_hu = (double)((CELL *) inrast_hu)[col];
		break;
	    case FCELL_TYPE:
		d_hu = (double)((FCELL *) inrast_hu)[col];
		break;
	    case DCELL_TYPE:
		d_hu = (double)((FCELL *) inrast_hu)[col];
		break;
	    }
	    if (G_is_d_null_value(&d_disp) || G_is_d_null_value(&d_z0h) ||
		 G_is_d_null_value(&d_psih) || G_is_d_null_value(&d_ustar)
		 || G_is_d_null_value(&d_hu)) {
		G_set_d_null_value(&outrast[col], 1);
	    }
	    else {
		

				/************************************/ 
		    /* calculate rah   */ 
		    d_rah = ra_h(d_disp, d_z0h, d_psih, d_ustar, d_hu);
		outrast[col] = d;
	    }
	    }
	if (G_put_raster_row(outfd, outrast, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
	}
    G_free(inrast_disp);
    G_free(inrast_z0h);
    G_free(inrast_psih);
    G_free(inrast_ustar);
    G_free(inrast_hu);
    G_close_cell(infd_disp);
    G_close_cell(infd_z0h);
    G_close_cell(infd_psih);
    G_close_cell(infd_ustar);
    G_close_cell(infd_hu);
    G_free(outrast);
    G_close_cell(outfd);
    G_short_history(result, "raster", &history);
    G_command_history(&history);
    G_write_history(result, &history);
    exit(EXIT_SUCCESS);
}


