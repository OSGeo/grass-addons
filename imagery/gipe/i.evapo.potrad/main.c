
/****************************************************************************
 *
 * MODULE:       i.evapo.potrad
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Creates a map of potential evapotranspiration following
 *               the condition that all net radiation becomes ET
 *               (thus it can be called a "radiative ET pot")
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
double solar_day(double lat, double doy, double tsw);

double solar_day_3d(double lat, double doy, double tsw, double slope,
		     double aspect);
double r_net_day(double bbalb, double solar, double tsw);

double r_net_day_bandara98(double surface_albedo, double solar_day,
			    double apparent_atm_emissivity,
			    double surface_emissivity,
			    double air_temperature);
double et_pot_day(double rnetd, double tempk, double roh_w);

int main(int argc, char *argv[]) 
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    struct GModule *module;

    struct Option *input1, *input2, *input3, *input4;

    struct Option *input5, *input6, *input7, *input8;

    struct Option *input9, *input10, *input11;

    struct Option *output1, *output2;

    struct Flag *flag1, *flag2, *flag3, *flag4;

    struct History history;	/*metadata */

    struct Colors colors;	/*Color rules */

    

	/************************************/ 
	/* FMEO Declarations**************** */ 
    char *name;			/*input raster name */

    char *result1, *result2;	/*output raster name */

    
	/*File Descriptors */ 
    int infd_albedo, infd_tempk, infd_lat, infd_doy, infd_tsw;

    int infd_slope, infd_aspect;

    int infd_tair, infd_e0;

    int outfd1, outfd2;

    char *albedo, *tempk, *lat, *doy, *tsw, *slope, *aspect, *tair, *e0;

    double roh_w, e_atm;

    int i = 0, j = 0;

    void *inrast_albedo, *inrast_tempk, *inrast_lat;

    void *inrast_doy, *inrast_tsw;

    void *inrast_slope, *inrast_aspect;

    void *inrast_tair, *inrast_e0;

    DCELL * outrast1, *outrast2;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_albedo;
    RASTER_MAP_TYPE data_type_tempk;
    RASTER_MAP_TYPE data_type_lat;
    RASTER_MAP_TYPE data_type_doy;
    RASTER_MAP_TYPE data_type_tsw;
    RASTER_MAP_TYPE data_type_slope;
    RASTER_MAP_TYPE data_type_aspect;
    RASTER_MAP_TYPE data_type_tair;
    RASTER_MAP_TYPE data_type_e0;
    

	/************************************/ 
	G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("Potential ET, evapotranspiration");
    module->description =
	_("Potential evapotranspiration, radiative method after Bastiaanssen (1995)");
    
	/* Define the different options */ 
	input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("albedo");
    input1->description = _("Name of the Albedo layer [0.0-1.0]");
    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = _("tempk");
    input2->description = _("Name of the temperature layer [Degree Kelvin]");
    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = _("lat");
    input3->description = _("Name of the degree latitude layer [dd.ddd]");
    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = _("doy");
    input4->description = _("Name of the Day of Year layer [0.0-366.0]");
    input5 = G_define_standard_option(G_OPT_R_INPUT);
    input5->key = _("tsw");
    input5->description =
	_("Name of the single-way transmissivity layer [0.05-1.0], defaults to 1.0 if no input file");
    input6 = G_define_option();
    input6->key = _("roh_w");
    input6->type = TYPE_DOUBLE;
    input6->required = YES;
    input6->gisprompt = _("value, parameter");
    input6->description =
	_("Value of the density of fresh water ~[1000-1020]");
    input6->answer = _("1005.0");
    input7 = G_define_standard_option(G_OPT_R_INPUT);
    input7->key = _("slope");
    input7->required = NO;
    input7->description = _("Name of the Slope layer ~[0-90]");
    input7->guisection = _("Optional");
    input8 = G_define_standard_option(G_OPT_R_INPUT);
    input8->key = _("aspect");
    input8->required = NO;
    input8->description = _("Name of the Aspect layer ~[0-360]");
    input8->guisection = _("Optional");
    input9 = G_define_option();
    input9->key = _("e_atm");
    input9->type = TYPE_DOUBLE;
    input9->required = NO;
    input9->gisprompt = _("value, parameter");
    input9->description =
	_("Value of the apparent atmospheric emissivity (Bandara, 1998 used 0.845 for Sri Lanka)");
    input9->answer = _("0.845");
    input9->guisection = _("Optional");
    input10 = G_define_standard_option(G_OPT_R_INPUT);
    input10->key = _("t_air");
    input10->required = NO;
    input10->description =
	_("Name of the Air Temperature layer [Kelvin], use with -b");
    input10->guisection = _("Optional");
    input11 = G_define_standard_option(G_OPT_R_INPUT);
    input11->key = _("e0");
    input11->required = NO;
    input11->description =
	_("Name of the Surface Emissivity layer [-], use with -b");
    input11->guisection = _("Optional");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("OUTPUT: Name of the Potential ET layer");
    output2 = G_define_standard_option(G_OPT_R_OUTPUT);
    output2->key = _("rnetd");
    output2->required = NO;
    output2->description =
	_("OUTPUT: Name of the Diurnal Net Radiation layer");
    output2->guisection = _("Optional");
    flag1 = G_define_flag();
    flag1->key = 'r';
    flag1->description = _("Output Diurnal Net Radiation (for i.eb.eta)");
    flag2 = G_define_flag();
    flag2->key = 'd';
    flag2->description = _("Slope/Aspect correction");
    flag3 = G_define_flag();
    flag3->key = 'b';
    flag3->description =
	_("Net Radiation Bandara (1998), generic Longwave calculation, need apparent atmospheric emissivity, Air temperature and surface emissivity inputs");
    

	/********************/ 
	if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    albedo = input1->answer;
    tempk = input2->answer;
    lat = input3->answer;
    doy = input4->answer;
    tsw = input5->answer;
    roh_w = atof(input6->answer);
    slope = input7->answer;
    aspect = input8->answer;
    e_atm = atof(input9->answer);
    tair = input10->answer;
    e0 = input11->answer;
    result1 = output1->answer;
    result2 = output2->answer;
    

	/***************************************************/ 
	mapset = G_find_cell2(albedo, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), albedo);
    }
    data_type_albedo = G_raster_map_type(albedo, mapset);
    if ((infd_albedo = G_open_cell_old(albedo, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), albedo);
    if (G_get_cellhd(albedo, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s])"), albedo);
    inrast_albedo = G_allocate_raster_buf(data_type_albedo);
    

	/***************************************************/ 
	mapset = G_find_cell2(tempk, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), tempk);
    }
    data_type_tempk = G_raster_map_type(tempk, mapset);
    if ((infd_tempk = G_open_cell_old(tempk, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), tempk);
    if (G_get_cellhd(tempk, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), tempk);
    inrast_tempk = G_allocate_raster_buf(data_type_tempk);
    

	/***************************************************/ 
	mapset = G_find_cell2(lat, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), lat);
    }
    data_type_lat = G_raster_map_type(lat, mapset);
    if ((infd_lat = G_open_cell_old(lat, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), lat);
    if (G_get_cellhd(lat, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), lat);
    inrast_lat = G_allocate_raster_buf(data_type_lat);
    

	/***************************************************/ 
	mapset = G_find_cell2(doy, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), doy);
    }
    data_type_doy = G_raster_map_type(doy, mapset);
    if ((infd_doy = G_open_cell_old(doy, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), doy);
    if (G_get_cellhd(doy, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), doy);
    inrast_doy = G_allocate_raster_buf(data_type_doy);
    

	/***************************************************/ 
	mapset = G_find_cell2(tsw, "");
    if (mapset == NULL) {
	G_fatal_error(_("Cell file [%s] not found"), tsw);
    }
    data_type_tsw = G_raster_map_type(tsw, mapset);
    if ((infd_tsw = G_open_cell_old(tsw, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), tsw);
    if (G_get_cellhd(tsw, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), tsw);
    inrast_tsw = G_allocate_raster_buf(data_type_tsw);
    

	/***************************************************/ 
	if (flag2->answer) {
	mapset = G_find_cell2(slope, "");
	if (mapset == NULL) {
	    G_fatal_error(_("Cell file [%s] not found"), slope);
	}
	data_type_slope = G_raster_map_type(slope, mapset);
	if ((infd_slope = G_open_cell_old(slope, mapset)) < 0)
	    G_fatal_error(_("Cannot open cell file [%s]"), slope);
	if (G_get_cellhd(slope, mapset, &cellhd) < 0)
	    G_fatal_error(_("Cannot read file header of [%s]"), slope);
	inrast_slope = G_allocate_raster_buf(data_type_slope);
    }
    

	/***************************************************/ 
	if (flag2->answer) {
	mapset = G_find_cell2(aspect, "");
	if (mapset == NULL) {
	    G_fatal_error(_("Cell file [%s] not found"), aspect);
	}
	data_type_aspect = G_raster_map_type(aspect, mapset);
	if ((infd_aspect = G_open_cell_old(aspect, mapset)) < 0)
	    G_fatal_error(_("Cannot open cell file [%s]"), aspect);
	if (G_get_cellhd(aspect, mapset, &cellhd) < 0)
	    G_fatal_error(_("Cannot read file header of [%s]"), aspect);
	inrast_aspect = G_allocate_raster_buf(data_type_aspect);
    }
    

	/***************************************************/ 
	if (flag3->answer) {
	mapset = G_find_cell2(tair, "");
	if (mapset == NULL) {
	    G_fatal_error(_("Cell file [%s] not found"), tair);
	}
	data_type_tair = G_raster_map_type(tair, mapset);
	if ((infd_tair = G_open_cell_old(tair, mapset)) < 0)
	    G_fatal_error(_("Cannot open cell file [%s]"), tair);
	if (G_get_cellhd(tair, mapset, &cellhd) < 0)
	    G_fatal_error(_("Cannot read file header of [%s]"), tair);
	inrast_tair = G_allocate_raster_buf(data_type_tair);
    }
    

	/***************************************************/ 
	if (flag3->answer) {
	mapset = G_find_cell2(e0, "");
	if (mapset == NULL) {
	    G_fatal_error(_("Cell file [%s] not found"), e0);
	}
	data_type_e0 = G_raster_map_type(e0, mapset);
	if ((infd_e0 = G_open_cell_old(e0, mapset)) < 0)
	    G_fatal_error(_("Cannot open cell file [%s]"), e0);
	if (G_get_cellhd(e0, mapset, &cellhd) < 0)
	    G_fatal_error(_("Cannot read file header of [%s]"), e0);
	inrast_e0 = G_allocate_raster_buf(data_type_e0);
    }
    

	/***************************************************/ 
	G_debug(3, "number of rows %d", cellhd.rows);
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast1 = G_allocate_raster_buf(data_type_output);
    if (result2) {
	outrast2 = G_allocate_raster_buf(data_type_output);
    }
    
	/* Create New raster files */ 
	if ((outfd1 = G_open_raster_new(result1, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), result1);
    if (result2) {
	if ((outfd2 = G_open_raster_new(result2, data_type_output)) < 0)
	    G_fatal_error(_("Could not open <%s>"), result2);
    }
    
	/* Process pixels */ 
	for (row = 0; row < nrows; row++)
	 {
	DCELL d;
	DCELL d_albedo;
	DCELL d_tempk;
	DCELL d_lat;
	DCELL d_doy;
	DCELL d_tsw;
	DCELL d_solar;
	DCELL d_rnetd;
	DCELL d_slope;
	DCELL d_aspect;
	DCELL d_tair;
	DCELL d_e0;
	G_percent(row, nrows, 2);
	
	    /* read input maps */ 
	    if (G_get_raster_row
		(infd_albedo, inrast_albedo, row, data_type_albedo) < 0)
	    G_fatal_error(_("Could not read from <%s>"), albedo);
	if (G_get_raster_row(infd_tempk, inrast_tempk, row, data_type_tempk)
	     < 0)
	    G_fatal_error(_("Could not read from <%s>"), tempk);
	if (G_get_raster_row(infd_lat, inrast_lat, row, data_type_lat) < 0)
	    G_fatal_error(_("Could not read from <%s>"), lat);
	if (G_get_raster_row(infd_doy, inrast_doy, row, data_type_doy) < 0)
	    G_fatal_error(_("Could not read from <%s>"), doy);
	if (G_get_raster_row(infd_tsw, inrast_tsw, row, data_type_tsw) < 0)
	    G_fatal_error(_("Could not read from <%s>"), tsw);
	if (flag2->answer) {
	    if (G_get_raster_row
		 (infd_slope, inrast_slope, row, data_type_slope) < 0)
		G_fatal_error(_("Could not read from <%s>"), slope);
	    if (G_get_raster_row
		 (infd_aspect, inrast_aspect, row, data_type_aspect) < 0)
		G_fatal_error(_("Could not read from <%s>"), aspect);
	}
	if (flag3->answer) {
	    if (G_get_raster_row(infd_tair, inrast_tair, row, data_type_tair)
		 < 0)
		G_fatal_error(_("Could not read from <%s>"), tair);
	    if (G_get_raster_row(infd_e0, inrast_e0, row, data_type_e0) < 0)
		G_fatal_error(_("Could not read from <%s>"), e0);
	}
	
	    /*process the data */ 
	    for (col = 0; col < ncols; col++)
	     {
	    switch (data_type_albedo) {
	    case CELL_TYPE:
		d_albedo = (double)((CELL *) inrast_albedo)[col];
		break;
	    case FCELL_TYPE:
		d_albedo = (double)((FCELL *) inrast_albedo)[col];
		break;
	    case DCELL_TYPE:
		d_albedo = (double)((DCELL *) inrast_albedo)[col];
		break;
	    }
	    switch (data_type_tempk) {
	    case CELL_TYPE:
		d_tempk = (double)((CELL *) inrast_tempk)[col];
		break;
	    case FCELL_TYPE:
		d_tempk = (double)((FCELL *) inrast_tempk)[col];
		break;
	    case DCELL_TYPE:
		d_tempk = (double)((DCELL *) inrast_tempk)[col];
		break;
	    }
	    switch (data_type_lat) {
	    case CELL_TYPE:
		d_lat = (double)((CELL *) inrast_lat)[col];
		break;
	    case FCELL_TYPE:
		d_lat = (double)((FCELL *) inrast_lat)[col];
		break;
	    case DCELL_TYPE:
		d_lat = (double)((DCELL *) inrast_lat)[col];
		break;
	    }
	    switch (data_type_doy) {
	    case CELL_TYPE:
		d_doy = (double)((CELL *) inrast_doy)[col];
		break;
	    case FCELL_TYPE:
		d_doy = (double)((FCELL *) inrast_doy)[col];
		break;
	    case DCELL_TYPE:
		d_doy = (double)((DCELL *) inrast_doy)[col];
		break;
	    }
	    switch (data_type_tsw) {
	    case CELL_TYPE:
		d_tsw = (double)((CELL *) inrast_tsw)[col];
		break;
	    case FCELL_TYPE:
		d_tsw = (double)((FCELL *) inrast_tsw)[col];
		break;
	    case DCELL_TYPE:
		d_tsw = (double)((DCELL *) inrast_tsw)[col];
		break;
	    }
	    if (flag2->answer) {
		switch (data_type_slope) {
		case CELL_TYPE:
		    d_slope = (double)((CELL *) inrast_slope)[col];
		    break;
		case FCELL_TYPE:
		    d_slope = (double)((FCELL *) inrast_slope)[col];
		    break;
		case DCELL_TYPE:
		    d_slope = (double)((DCELL *) inrast_slope)[col];
		    break;
		}
		switch (data_type_aspect) {
		case CELL_TYPE:
		    d_aspect = (double)((CELL *) inrast_aspect)[col];
		    break;
		case FCELL_TYPE:
		    d_aspect = (double)((FCELL *) inrast_aspect)[col];
		    break;
		case DCELL_TYPE:
		    d_aspect = (double)((DCELL *) inrast_aspect)[col];
		    break;
		}
	    }
	    if (flag3->answer) {
		switch (data_type_tair) {
		case CELL_TYPE:
		    d_tair = (double)((CELL *) inrast_tair)[col];
		    break;
		case FCELL_TYPE:
		    d_tair = (double)((FCELL *) inrast_tair)[col];
		    break;
		case DCELL_TYPE:
		    d_tair = (double)((DCELL *) inrast_tair)[col];
		    break;
		}
		switch (data_type_e0) {
		case CELL_TYPE:
		    d_e0 = (double)((CELL *) inrast_e0)[col];
		    break;
		case FCELL_TYPE:
		    d_e0 = (double)((FCELL *) inrast_e0)[col];
		    break;
		case DCELL_TYPE:
		    d_e0 = (double)((DCELL *) inrast_e0)[col];
		    break;
		}
	    }
	    if (G_is_d_null_value(&d_albedo) || G_is_d_null_value(&d_tempk)
		 || (d_tempk < 10.0) || G_is_d_null_value(&d_lat) ||
		 G_is_d_null_value(&d_doy) || G_is_d_null_value(&d_tsw) ||
		 ((flag2->answer) && G_is_d_null_value(&d_slope)) ||
		 ((flag2->answer) && G_is_d_null_value(&d_aspect)) ||
		 ((flag3->answer) && G_is_d_null_value(&d_tair)) ||
		 ((flag3->answer) && G_is_d_null_value(&d_e0))) {
		G_set_d_null_value(&outrast1[col], 1);
		if (result2)
		    G_set_d_null_value(&outrast2[col], 1);
	    }
	    else {
		if (flag2->answer) {
		    d_solar =
			solar_day_3d(d_lat, d_doy, d_tsw, d_slope, d_aspect);
		}
		else {
		    d_solar = solar_day(d_lat, d_doy, d_tsw);
		}
		if (flag3->answer) {
		    d_rnetd =
			r_net_day_bandara98(d_albedo, d_solar, e_atm, d_e0,
					    d_tair);
		}
		else {
		    d_rnetd = r_net_day(d_albedo, d_solar, d_tsw);
		}
		if (result2) {
		    outrast2[col] = d_rnetd;
		}
		d = et_pot_day(d_rnetd, d_tempk, roh_w);
		d = d * d_tsw;
		outrast1[col] = d;
	    }
	    }
	if (G_put_raster_row(outfd1, outrast1, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
	if (result2) {
	    if (G_put_raster_row(outfd2, outrast2, data_type_output) < 0)
		G_fatal_error(_("Cannot write to output raster file"));
	}
	}
    G_free(inrast_albedo);
    G_free(inrast_tempk);
    G_free(inrast_lat);
    G_free(inrast_doy);
    G_close_cell(infd_albedo);
    G_close_cell(infd_tempk);
    G_close_cell(infd_lat);
    G_close_cell(infd_doy);
    G_free(inrast_tsw);
    G_close_cell(infd_tsw);
    if (flag3->answer) {
	G_free(inrast_tair);
	G_close_cell(infd_tair);
	G_free(inrast_e0);
	G_close_cell(infd_e0);
    }
    G_free(outrast1);
    G_close_cell(outfd1);
    if (result2) {
	G_free(outrast2);
	G_close_cell(outfd2);
	
	    /* Color rule */ 
	    G_init_colors(&colors);
	G_add_color_rule(0, 0, 0, 0, 400, 255, 255, 255, &colors);
	
	    /* Metadata */ 
	    G_short_history(result2, "raster", &history);
	G_command_history(&history);
	G_write_history(result2, &history);
    }
    
	/* Color rule */ 
	G_init_colors(&colors);
    G_add_color_rule(0, 0, 0, 0, 10, 255, 255, 255, &colors);
    
	/* Metadata */ 
	G_short_history(result1, "raster", &history);
    G_command_history(&history);
    G_write_history(result1, &history);
    exit(EXIT_SUCCESS);
}


