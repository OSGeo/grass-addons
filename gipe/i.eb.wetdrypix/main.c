
/****************************************************************************
 *
 * MODULE:       i.eb.wetdrypix
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Tries to zero-in areas of potential pixel candidates for
 * 		 use in the initialisation of the sensible heat flux in SEBAL
 * 		 iteration, where Delta T and rah are reassessed at each iteration.
 *
 * COPYRIGHT:    (C) 2002-2008 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 * CHANGELOG:	
 * 		 20080722: reworked the conditions as found in the automatic 
 * 		 	mode of	i.eb.h_SEBAL95.
 *
 *****************************************************************************/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <grass/gis.h>
#include <math.h>
#include <grass/glocale.h>

int main(int argc, char *argv[])
{
    struct Cell_head cellhd;

    /* buffer for in out raster */
    DCELL *inrast_T, *inrast_alb;

    DCELL *inrast_DEM, *inrast_Rn, *inrast_g0;

    CELL *outrast, *outrast1;

    int nrows, ncols;

    int row, col;

    int infd_T, infd_alb, infd_DEM, infd_Rn, infd_g0;

    int outfd, outfd1;

    char *mapset_T, *mapset_alb, *mapset_DEM, *mapset_Rn, *mapset_g0;

    char *T, *alb, *DEM, *Rn, *g0;

    char *wetF, *dryF;

    struct History history;

    struct GModule *module;

    struct Option *input_T, *input_alb;

    struct Option *input_DEM, *input_Rn, *input_g0;

    struct Option *output, *output1;

	/*******************************/
    RASTER_MAP_TYPE data_type_T;

    RASTER_MAP_TYPE data_type_DEM;

    RASTER_MAP_TYPE data_type_Rn;

    RASTER_MAP_TYPE data_type_g0;

    RASTER_MAP_TYPE data_type_albedo;

    RASTER_MAP_TYPE data_type_output = CELL_TYPE;

	/*******************************/

    struct Flag *flag1, *zero;

    G_gisinit(argv[0]);

    module = G_define_module();
    module->description = _("Wet and Dry pixels candidates for SEBAL 95");

    /* Define different options */
    input_T = G_define_standard_option(G_OPT_R_INPUT);
    input_T->key = "T";
    input_T->description =
	_("Name of Surface Skin Temperature input map [K]");

    input_alb = G_define_standard_option(G_OPT_R_INPUT);
    input_alb->key = "alb";
    input_alb->description = _("Name of Broadband Albedo input map [-]");

    input_DEM = G_define_standard_option(G_OPT_R_INPUT);
    input_DEM->key = "DEM";
    input_DEM->description = _("Name of DEM input map [m a.s.l.]");

    input_Rn = G_define_standard_option(G_OPT_R_INPUT);
    input_Rn->key = "Rn";
    input_Rn->description =
	_("Name of Diurnal Net Solar Radiation input map [W/m2]");

    input_g0 = G_define_standard_option(G_OPT_R_INPUT);
    input_g0->key = "g0";
    input_g0->description = _("Name of Soil Heat Flux input map [W/m2]");

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->key = "wet";
    output->description = _("Name of output wet pixels areas layer [-]");

    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->key = "dry";
    output1->description = _("Name of output dry pixels areas layer [-]");

    zero = G_define_flag();
    zero->key = 'z';
    zero->description = _("set negative to zero");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* get entered parameters */
    T = input_T->answer;
    alb = input_alb->answer;
    DEM = input_DEM->answer;
    Rn = input_Rn->answer;
    g0 = input_g0->answer;

    wetF = output->answer;
    dryF = output1->answer;

    /* find maps in mapset */
    mapset_T = G_find_cell2(T, "");
    if (mapset_T == NULL)
	G_fatal_error(_("cell file [%s] not found"), T);
    mapset_alb = G_find_cell2(alb, "");
    if (mapset_alb == NULL)
	G_fatal_error(_("cell file [%s] not found"), alb);
    mapset_DEM = G_find_cell2(DEM, "");
    if (mapset_DEM == NULL)
	G_fatal_error(_("cell file [%s] not found"), DEM);
    mapset_Rn = G_find_cell2(Rn, "");
    if (mapset_Rn == NULL)
	G_fatal_error(_("cell file [%s] not found"), Rn);
    mapset_g0 = G_find_cell2(g0, "");
    if (mapset_g0 == NULL)
	G_fatal_error(_("cell file [%s] not found"), g0);

    /* check legal output name */
    if (G_legal_filename(wetF) < 0)
	G_fatal_error(_("[%s] is an illegal name"), wetF);
    if (G_legal_filename(dryF) < 0)
	G_fatal_error(_("[%s] is an illegal name"), dryF);

    /* determine the input map type (CELL/FCELL/DCELL) */
    data_type_T = G_raster_map_type(T, mapset_T);
    data_type_DEM = G_raster_map_type(DEM, mapset_DEM);
    data_type_Rn = G_raster_map_type(Rn, mapset_Rn);
    data_type_g0 = G_raster_map_type(g0, mapset_g0);
    data_type_albedo = G_raster_map_type(alb, mapset_alb);

    if ((infd_T = G_open_cell_old(T, mapset_T)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), T);
    if ((infd_alb = G_open_cell_old(alb, mapset_alb)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), alb);
    if ((infd_DEM = G_open_cell_old(DEM, mapset_DEM)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), DEM);
    if ((infd_Rn = G_open_cell_old(Rn, mapset_Rn)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), Rn);
    if ((infd_g0 = G_open_cell_old(g0, mapset_g0)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), g0);

    if (G_get_cellhd(T, mapset_T, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), T);
    if (G_get_cellhd(alb, mapset_alb, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), alb);
    if (G_get_cellhd(DEM, mapset_DEM, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), DEM);
    if (G_get_cellhd(Rn, mapset_Rn, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), Rn);
    if (G_get_cellhd(g0, mapset_g0, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), g0);

    /* Allocate input buffer */
    inrast_T = G_allocate_raster_buf(data_type_T);
    inrast_DEM = G_allocate_raster_buf(data_type_DEM);
    inrast_Rn = G_allocate_raster_buf(data_type_Rn);
    inrast_g0 = G_allocate_raster_buf(data_type_g0);
    inrast_alb = G_allocate_raster_buf(data_type_albedo);

    /* Allocate output buffer */
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast = G_allocate_raster_buf(data_type_output);
    outrast1 = G_allocate_raster_buf(data_type_output);

    if ((outfd = G_open_raster_new(wetF, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), wetF);
    if ((outfd1 = G_open_raster_new(dryF, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), dryF);

    /*START Temperature minimum search */
    /* THREAD 1 */
    /*This is correcting for un-Earthly temperatures */
    /*It finds when histogram is actually starting to pull up... */
    int peak1, peak2, peak3;

    int i_peak1, i_peak2, i_peak3;

    int bottom1a, bottom1b;

    int bottom2a, bottom2b;

    int bottom3a, bottom3b;

    int i_bottom1a, i_bottom1b;

    int i_bottom2a, i_bottom2b;

    int i_bottom3a, i_bottom3b;

    int i = 0;

    int histogram[400];

    for (i = 0; i < 400; i++) {
	histogram[i] = 0;
    }
    DCELL d_T;

	/****************************/
    /* Process pixels histogram */
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);
	/* read input map */
	if ((G_get_raster_row(infd_T, inrast_T, row, data_type_T)) < 0) {
	    G_fatal_error(_("Could not read from <%s>"), T);
	}
	/*process the data */
	for (col = 0; col < ncols; col++) {
	    switch (data_type_T) {
	    case CELL_TYPE:
		d_T = (double)((CELL *) inrast_T)[col];
		break;
	    case FCELL_TYPE:
		d_T = (double)((FCELL *) inrast_T)[col];
		break;
	    case DCELL_TYPE:
		d_T = (double)((DCELL *) inrast_T)[col];
		break;
	    }
	    if (G_is_d_null_value(&d_T)) {
		/*Do nothing */
	    }
	    else {
		int temp;

		temp = (int)d_T;
		if (temp > 0) {
		    histogram[temp] = histogram[temp] + 1.0;
		}
	    }
	}
    }
    G_message
	("Histogram of Temperature map (if it has rogue values to clean)");
    peak1 = 0;
    peak2 = 0;
    peak3 = 0;
    i_peak1 = 0;
    i_peak2 = 0;
    i_peak3 = 0;
    bottom1a = 100000;
    bottom1b = 100000;
    bottom2a = 100000;
    bottom2b = 100000;
    bottom3a = 100000;
    bottom3b = 100000;
    i_bottom1a = 1000;
    i_bottom1b = 1000;
    i_bottom2a = 1000;
    i_bottom2b = 1000;
    i_bottom3a = 1000;
    i_bottom3b = 1000;
    for (i = 0; i < 400; i++) {
	/* Search for highest peak of dataset (2) */
	/* Highest Peak */
	if (histogram[i] > peak2) {
	    peak2 = histogram[i];
	    i_peak2 = i;
	}
    }
    int stop = 0;

    for (i = i_peak2; i > 5; i--) {
	if (((histogram[i] + histogram[i - 1] + histogram[i - 2] +
	      histogram[i - 3] + histogram[i - 4]) / 5) < histogram[i] &&
	    stop == 0) {
	    bottom2a = histogram[i];
	    i_bottom2a = i;
	}
	else if (((histogram[i] + histogram[i - 1] + histogram[i - 2] +
		   histogram[i - 3] + histogram[i - 4]) / 5) > histogram[i] &&
		 stop == 0) {
	    /*Search for peaks of datasets (1) */
	    peak1 = histogram[i];
	    i_peak1 = i;
	    stop = 1;
	}
    }
    stop = 0;
    for (i = i_peak2; i < 395; i++) {
	if (((histogram[i] + histogram[i + 1] + histogram[i + 2] +
	      histogram[i + 3] + histogram[i + 4]) / 5) < histogram[i] &&
	    stop == 0) {
	    bottom2b = histogram[i];
	    i_bottom2b = i;
	}
	else if (((histogram[i] + histogram[i + 1] + histogram[i + 2] +
		   histogram[i + 3] + histogram[i + 4]) / 5) > histogram[i] &&
		 stop == 0) {
	    /*Search for peaks of datasets (3) */
	    peak3 = histogram[i];
	    i_peak3 = i;
	    stop = 1;
	}
    }
    /* First histogram lower bound */
    for (i = 250; i < i_peak1; i++) {
	if (histogram[i] < bottom1a) {
	    bottom1a = histogram[i];
	    i_bottom1a = i;
	}
    }
    /* First histogram higher bound */
    for (i = i_peak2; i > i_peak1; i--) {
	if (histogram[i] <= bottom1b) {
	    bottom1b = histogram[i];
	    i_bottom1b = i;
	}
    }
    /* Third histogram lower bound */
    for (i = i_peak2; i < i_peak3; i++) {
	if (histogram[i] < bottom3a) {
	    bottom3a = histogram[i];
	    i_bottom3a = i;
	}
    }
    /* Third histogram higher bound */
    for (i = 399; i > i_peak3; i--) {
	if (histogram[i] < bottom3b) {
	    bottom3b = histogram[i];
	    i_bottom3b = i;
	}
    }

    DCELL d_tempk;		/* Input raster */

    DCELL d_albedo;		/* Input raster */

    DCELL d_dem;		/* Input raster */

    DCELL d_Rn;			/* Input raster */

    DCELL d_g0;			/* Input raster */

    CELL c_wet;			/* Output pixel */

    CELL c_dry;			/* Output pixel */

    DCELL d_dem_dry;		/* Generated here */

    DCELL d_t0dem, d_t0dem_dry;	/* Generated here */

    DCELL t0dem_min, tempk_min;	/* Generated here */

    DCELL t0dem_max, tempk_max;	/* Generated here */

    DCELL d_tempk_max, d_tempk_min;	/* Generated here */

    DCELL d_h0, d_h0_max;	/* Generated here */

    DCELL d_tempk_wet, d_tempk_dry;	/* Generated here */

    DCELL d_Rn_wet, d_Rn_dry;	/* Generated here */

    DCELL d_g0_wet, d_g0_dry;	/* Generated here */

    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);
	/* read a line input maps into buffers */
	if (G_get_raster_row(infd_T, inrast_T, row, data_type_T) < 0)
	    G_fatal_error(_("Could not read from <%s>"), T);
	if (G_get_raster_row(infd_alb, inrast_alb, row, data_type_albedo) < 0)
	    G_fatal_error(_("Could not read from <%s>"), alb);
	if (G_get_raster_row(infd_DEM, inrast_DEM, row, data_type_DEM) < 0)
	    G_fatal_error(_("Could not read from <%s>"), DEM);
	if (G_get_raster_row(infd_Rn, inrast_Rn, row, data_type_Rn) < 0)
	    G_fatal_error(_("Could not read from <%s>"), Rn);
	if (G_get_raster_row(infd_g0, inrast_g0, row, data_type_g0) < 0)
	    G_fatal_error(_("Could not read from <%s>"), g0);

	/* read every cell in the line buffers */
	for (col = 0; col < ncols; col++) {
	    switch (data_type_albedo) {
	    case CELL_TYPE:
		d_albedo = (double)((CELL *) inrast_alb)[col];
		break;
	    case FCELL_TYPE:
		d_albedo = (double)((FCELL *) inrast_alb)[col];
		break;
	    case DCELL_TYPE:
		d_albedo = (double)((DCELL *) inrast_alb)[col];
		break;
	    }
	    switch (data_type_T) {
	    case CELL_TYPE:
		d_tempk = (double)((CELL *) inrast_T)[col];
		break;
	    case FCELL_TYPE:
		d_tempk = (double)((FCELL *) inrast_T)[col];
		break;
	    case DCELL_TYPE:
		d_tempk = (double)((DCELL *) inrast_T)[col];
		break;
	    }
	    switch (data_type_DEM) {
	    case CELL_TYPE:
		d_dem = (double)((CELL *) inrast_DEM)[col];
		break;
	    case FCELL_TYPE:
		d_dem = (double)((FCELL *) inrast_DEM)[col];
		break;
	    case DCELL_TYPE:
		d_dem = (double)((DCELL *) inrast_DEM)[col];
		break;
	    }
	    switch (data_type_Rn) {
	    case CELL_TYPE:
		d_Rn = (double)((CELL *) inrast_Rn)[col];
		break;
	    case FCELL_TYPE:
		d_Rn = (double)((FCELL *) inrast_Rn)[col];
		break;
	    case DCELL_TYPE:
		d_Rn = (double)((DCELL *) inrast_Rn)[col];
		break;
	    }
	    switch (data_type_g0) {
	    case CELL_TYPE:
		d_g0 = (double)((CELL *) inrast_g0)[col];
		break;
	    case FCELL_TYPE:
		d_g0 = (double)((FCELL *) inrast_g0)[col];
		break;
	    case DCELL_TYPE:
		d_g0 = (double)((DCELL *) inrast_g0)[col];
		break;
	    }
	    if (G_is_d_null_value(&d_albedo) ||
		G_is_d_null_value(&d_tempk) ||
		G_is_d_null_value(&d_dem) ||
		G_is_d_null_value(&d_Rn) || G_is_d_null_value(&d_g0)) {
		/* do nothing */
	    }
	    else {
		d_t0dem = d_tempk + 0.001649 * d_dem;
		if (d_t0dem <= 250.0 || d_tempk <= 250.0) {
		    /* do nothing */
		}
		else {
		    d_h0 = d_Rn - d_g0;
		    if (d_t0dem < t0dem_min && d_albedo < 0.15) {
			t0dem_min = d_t0dem;
			tempk_min = d_tempk;
			d_tempk_wet = d_tempk;
			d_Rn_wet = d_Rn;
			d_g0_wet = d_g0;
		    }
		    if (d_tempk >= (double)i_peak1 - 5.0 &&
			d_tempk < (double)i_peak1 + 1.0) {
			tempk_min = d_tempk;
			d_tempk_wet = d_tempk;
			d_Rn_wet = d_Rn;
			d_g0_wet = d_g0;
		    }
		    if (d_t0dem > t0dem_max) {
			t0dem_max = d_t0dem;
			d_t0dem_dry = d_t0dem;
			tempk_max = d_tempk;
			d_tempk_dry = d_tempk;
			d_Rn_dry = d_Rn;
			d_g0_dry = d_g0;
			d_dem_dry = d_dem;
		    }
		    if (d_tempk >= (double)i_peak3 - 0.0 &&
			d_tempk < (double)i_peak3 + 7.0 &&
			d_h0 > 100.0 && d_h0 > d_h0_max &&
			d_g0 > 10.0 && d_Rn > 100.0 && d_albedo > 0.3) {
			tempk_max = d_tempk;
			d_tempk_dry = d_tempk;
			d_Rn_dry = d_Rn;
			d_g0_dry = d_g0;
			d_h0_max = d_h0;
			d_dem_dry = d_dem;
		    }
		}
	    }
	}
    }
    G_message("tempk_min=%f", tempk_min);
    G_message("tempk_max=%f", tempk_max);


    /* ALLOCATE CLASSES: WET=1 DRY=1 OTHER=NULL OR 0.0 */

    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);
	/* read a line input maps into buffers */
	if (G_get_raster_row(infd_T, inrast_T, row, data_type_T) < 0)
	    G_fatal_error(_("Could not read from <%s>"), T);
	if (G_get_raster_row(infd_alb, inrast_alb, row, data_type_albedo) < 0)
	    G_fatal_error(_("Could not read from <%s>"), alb);
	if (G_get_raster_row(infd_DEM, inrast_DEM, row, data_type_DEM) < 0)
	    G_fatal_error(_("Could not read from <%s>"), DEM);
	if (G_get_raster_row(infd_Rn, inrast_Rn, row, data_type_Rn) < 0)
	    G_fatal_error(_("Could not read from <%s>"), Rn);
	if (G_get_raster_row(infd_g0, inrast_g0, row, data_type_g0) < 0)
	    G_fatal_error(_("Could not read from <%s>"), g0);

	/* read every cell in the line buffers */
	for (col = 0; col < ncols; col++) {
	    switch (data_type_albedo) {
	    case CELL_TYPE:
		d_albedo = (double)((CELL *) inrast_alb)[col];
		break;
	    case FCELL_TYPE:
		d_albedo = (double)((FCELL *) inrast_alb)[col];
		break;
	    case DCELL_TYPE:
		d_albedo = (double)((DCELL *) inrast_alb)[col];
		break;
	    }
	    switch (data_type_T) {
	    case CELL_TYPE:
		d_tempk = (double)((CELL *) inrast_T)[col];
		break;
	    case FCELL_TYPE:
		d_tempk = (double)((FCELL *) inrast_T)[col];
		break;
	    case DCELL_TYPE:
		d_tempk = (double)((DCELL *) inrast_T)[col];
		break;
	    }
	    switch (data_type_DEM) {
	    case CELL_TYPE:
		d_dem = (double)((CELL *) inrast_DEM)[col];
		break;
	    case FCELL_TYPE:
		d_dem = (double)((FCELL *) inrast_DEM)[col];
		break;
	    case DCELL_TYPE:
		d_dem = (double)((DCELL *) inrast_DEM)[col];
		break;
	    }
	    switch (data_type_Rn) {
	    case CELL_TYPE:
		d_Rn = (double)((CELL *) inrast_Rn)[col];
		break;
	    case FCELL_TYPE:
		d_Rn = (double)((FCELL *) inrast_Rn)[col];
		break;
	    case DCELL_TYPE:
		d_Rn = (double)((DCELL *) inrast_Rn)[col];
		break;
	    }
	    switch (data_type_g0) {
	    case CELL_TYPE:
		d_g0 = (double)((CELL *) inrast_g0)[col];
		break;
	    case FCELL_TYPE:
		d_g0 = (double)((FCELL *) inrast_g0)[col];
		break;
	    case DCELL_TYPE:
		d_g0 = (double)((DCELL *) inrast_g0)[col];
		break;
	    }
	    /* Initialize pixels as negative */
	    c_wet = -1;
	    c_dry = -1;

	    if (G_is_d_null_value(&d_albedo) ||
		G_is_d_null_value(&d_tempk) ||
		G_is_d_null_value(&d_dem) ||
		G_is_d_null_value(&d_Rn) || G_is_d_null_value(&d_g0)) {
		/* do nothing */
		G_set_c_null_value(&outrast[col], 1);
		G_set_c_null_value(&outrast1[col], 1);
	    }
	    else {
		/* if Albedo is high and H is positive */
		if (d_albedo > 0.3 &&	/*(d_Rn-d_g0) > 100.0 && */
		    d_tempk >= (double)i_peak3 - 5.0 &&
		    d_tempk <= (double)i_peak3 + 5.0) {
		    c_dry = 1;	/* Dry pixel candidate */
		}

		/* if Albedo is not high and H is low */
		if (d_albedo < 0.15 &&	/*(d_Rn-d_g0) <= 100.0 && */
		    d_tempk >= (double)i_peak1 - 5.0 &&
		    d_tempk <= (double)i_peak1 + 5.0) {
		    c_wet = 1;	/* Wet pixel Candidate */
		}
		/*flag NULL -> 0 */
		if (zero->answer && c_wet < 0) {
		    c_wet = 0;
		}
		if (zero->answer && c_dry < 0) {
		    c_dry = 0;
		}
		/*results */
		outrast[col] = c_wet;
		outrast1[col] = c_dry;

		/*clean up */
		if (c_wet == -1)
		    G_set_c_null_value(&outrast[col], 1);
		if (c_dry == -1)
		    G_set_c_null_value(&outrast1[col], 1);
	    }
	}
	if (G_put_raster_row(outfd, outrast, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to <%s>"), wetF);
	if (G_put_raster_row(outfd1, outrast1, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to <%s>"), dryF);
    }
    G_free(inrast_T);
    G_free(inrast_alb);
    G_free(inrast_DEM);
    G_free(inrast_Rn);
    G_free(inrast_g0);
    G_free(outrast);
    G_free(outrast1);
    G_close_cell(infd_T);
    G_close_cell(infd_alb);
    G_close_cell(infd_DEM);
    G_close_cell(infd_Rn);
    G_close_cell(infd_g0);
    G_close_cell(outfd);
    G_close_cell(outfd1);

    /* add command line incantation to history file */
    G_short_history(wetF, "raster", &history);
    G_command_history(&history);
    G_write_history(wetF, &history);
    G_short_history(dryF, "raster", &history);
    G_command_history(&history);
    G_write_history(dryF, &history);

    exit(EXIT_SUCCESS);
}
