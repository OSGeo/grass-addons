
/*****************************************************************************
*
* MODULE:	r.evapo.MH
* AUTHOR:	Yann Chemin yann.chemin@gmail.com 
*
* PURPOSE:	To estimate the reference evapotranspiration by means
*		of Modified Hargreaves method (2001).
*		Also has a switch for original Hargreaves (1985),
*		and for Hargreaves-Samani (1985).
*
* COPYRIGHT:	(C) 2007 by the GRASS Development Team
*
*		This program is free software under the GNU General Public
*		Licence (>=2). Read the file COPYING that comes with GRASS
*		for details.
*
***************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

double mh_original(double ra, double tavg, double tmax, double tmin,
		   double p);
double mh_eto(double ra, double tavg, double tmax, double tmin, double p);

double mh_samani(double ra, double tavg, double tmax, double tmin);

int main(int argc, char *argv[])
{
    /* buffer for input-output rasters */
    void *inrast_TEMPKAVG, *inrast_TEMPKMIN, *inrast_TEMPKMAX, *inrast_RNET,
	*inrast_P;

    DCELL *outrast;

    /* pointers to input-output raster files */
    int infd_TEMPKAVG, infd_TEMPKMIN, infd_TEMPKMAX, infd_RNET, infd_P;

    int outfd;

    /* mapsets for input raster files */
    char *mapset_TEMPKAVG, *mapset_TEMPKMIN, *mapset_TEMPKMAX, *mapset_RNET,
	*mapset_P;

    /* names of input-output raster files */
    char *RNET, *TEMPKAVG, *TEMPKMIN, *TEMPKMAX, *P;

    char *ETa;

    /* input-output cell values */
    DCELL d_tempkavg, d_tempkmin, d_tempkmax, d_rnet, d_p;

    DCELL d_daily_et;


    /* region informations and handler */
    struct Cell_head cellhd;

    int nrows, ncols;

    int row, col;

    /* parser stuctures definition */
    struct GModule *module;

    struct Option *input_RNET, *input_TEMPKAVG, *input_TEMPKMIN;

    struct Option *input_TEMPKMAX, *input_P;

    struct Option *output;

    struct Flag *zero, *original, *samani;

    struct Colors color;

    struct History history;

    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;

    RASTER_MAP_TYPE data_type_tempkavg;

    RASTER_MAP_TYPE data_type_tempkmin;

    RASTER_MAP_TYPE data_type_tempkmax;

    RASTER_MAP_TYPE data_type_rnet;

    RASTER_MAP_TYPE data_type_p;

    RASTER_MAP_TYPE data_type_eta;

    /* Initialize the GIS calls */
    G_gisinit(argv[0]);

    module = G_define_module();
    module->description =
	_("Evapotranspiration Calculation "
	  "Modified Hargreaves formulation, 2001."
	  "Flag for Original Hargreaves (1985).");

    /* Define different options */
    input_RNET = G_define_standard_option(G_OPT_R_INPUT);
    input_RNET->key = "rnetd";
    input_RNET->key_desc = "[W/m2/d]";
    input_RNET->description = _("Name of Diurnal Net Radiation raster map");

    input_TEMPKAVG = G_define_standard_option(G_OPT_R_INPUT);
    input_TEMPKAVG->key = "tempkavg";
    input_TEMPKAVG->key_desc = "[C]";
    input_TEMPKAVG->description = _("Name of avg air temperature raster map");

    input_TEMPKMIN = G_define_standard_option(G_OPT_R_INPUT);
    input_TEMPKMIN->key = "tempkmin";
    input_TEMPKMIN->key_desc = "[C]";
    input_TEMPKMIN->description = _("Name of min air temperature raster map");

    input_TEMPKMAX = G_define_standard_option(G_OPT_R_INPUT);
    input_TEMPKMAX->key = "TEMPKMAX";
    input_TEMPKMAX->key_desc = "[C]";
    input_TEMPKMAX->description = _("Name of max air temperature raster map");

    input_P = G_define_standard_option(G_OPT_R_INPUT);
    input_P->key = "p";
    input_P->key_desc = "[mm/month]";
    input_P->description =
	_("Name of precipitation raster map, disabled if original Hargreaves (1985) is enabled.");

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->key_desc = "[mm/d]";
    output->description = _("Name of output Ref Evapotranspiration layer");

    /* Define the different flags */
    zero = G_define_flag();
    zero->key = 'z';
    zero->description = _("set negative ETa to zero");

    original = G_define_flag();
    original->key = 'h';
    original->description = _("set to original Hargreaves (1985)");

    samani = G_define_flag();
    samani->key = 's';
    samani->description = _("set to Hargreaves-Samani (1985)");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* get entered parameters */
    RNET = input_RNET->answer;
    TEMPKAVG = input_TEMPKAVG->answer;
    TEMPKMIN = input_TEMPKMIN->answer;
    TEMPKMAX = input_TEMPKMAX->answer;
    P = input_P->answer;

    ETa = output->answer;

    /* find maps in mapset */
    mapset_RNET = G_find_cell2(RNET, "");
    if (mapset_RNET == NULL)
	G_fatal_error(_("cell file [%s] not found"), RNET);
    mapset_TEMPKAVG = G_find_cell2(TEMPKAVG, "");
    if (mapset_TEMPKAVG == NULL)
	G_fatal_error(_("cell file [%s] not found"), TEMPKAVG);
    mapset_TEMPKMIN = G_find_cell2(TEMPKMIN, "");
    if (mapset_TEMPKMIN == NULL)
	G_fatal_error(_("cell file [%s] not found"), TEMPKMIN);
    mapset_TEMPKMAX = G_find_cell2(TEMPKMAX, "");
    if (mapset_TEMPKMAX == NULL)
	G_fatal_error(_("cell file [%s] not found"), TEMPKMAX);
    if (!original->answer) {
	mapset_P = G_find_cell2(P, "");
	if (mapset_P == NULL)
	    G_fatal_error(_("cell file [%s] not found"), P);
    }
    /* check legal output name */
    if (G_legal_filename(ETa) < 0)
	G_fatal_error(_("[%s] is an illegal name"), ETa);

    /* determine the input map type (CELL/FCELL/DCELL) */
    data_type_rnet = G_raster_map_type(RNET, mapset_RNET);
    data_type_tempkavg = G_raster_map_type(TEMPKAVG, mapset_TEMPKAVG);
    data_type_tempkmin = G_raster_map_type(TEMPKMIN, mapset_TEMPKMIN);
    data_type_tempkmax = G_raster_map_type(TEMPKMAX, mapset_TEMPKMAX);
    if (!original->answer) {
	data_type_p = G_raster_map_type(P, mapset_P);
    }
    /* open pointers to input raster files */
    if ((infd_RNET = G_open_cell_old(RNET, mapset_RNET)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), RNET);
    if ((infd_TEMPKAVG = G_open_cell_old(TEMPKAVG, mapset_TEMPKAVG)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), TEMPKAVG);
    if ((infd_TEMPKMIN = G_open_cell_old(TEMPKMIN, mapset_TEMPKMIN)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), TEMPKMIN);
    if ((infd_TEMPKMAX = G_open_cell_old(TEMPKMAX, mapset_TEMPKMAX)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), TEMPKMAX);
    if (!original->answer) {
	if ((infd_P = G_open_cell_old(P, mapset_P)) < 0)
	    G_fatal_error(_("Cannot open cell file [%s]"), P);
    }
    /* read headers of raster files */
    if (G_get_cellhd(RNET, mapset_RNET, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), RNET);
    if (G_get_cellhd(TEMPKAVG, mapset_TEMPKAVG, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), TEMPKAVG);
    if (G_get_cellhd(TEMPKMIN, mapset_TEMPKMIN, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), TEMPKMIN);
    if (G_get_cellhd(TEMPKMAX, mapset_TEMPKMAX, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), TEMPKMAX);
    if (!original->answer) {
	if (G_get_cellhd(P, mapset_P, &cellhd) < 0)
	    G_fatal_error(_("Cannot read file header of [%s]"), P);
    }
    /* Allocate input buffer */
    inrast_RNET = G_allocate_raster_buf(data_type_rnet);
    inrast_TEMPKAVG = G_allocate_raster_buf(data_type_tempkavg);
    inrast_TEMPKMIN = G_allocate_raster_buf(data_type_tempkmin);
    inrast_TEMPKMAX = G_allocate_raster_buf(data_type_tempkmax);
    if (!original->answer) {
	inrast_P = G_allocate_raster_buf(data_type_p);
    }
    /* get rows and columns number of the current region */
    nrows = G_window_rows();
    ncols = G_window_cols();

    /* allocate output buffer */
    outrast = G_allocate_raster_buf(data_type_output);

    /* open pointers to output raster files */
    if ((outfd = G_open_raster_new(ETa, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), ETa);


    /* start the loop through cells */
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);
	/* read input raster row into line buffer */
	if (G_get_raster_row(infd_RNET, inrast_RNET, row, data_type_rnet) < 0)
	    G_fatal_error(_("Could not read from <%s>"), RNET);
	if (G_get_raster_row
	    (infd_TEMPKAVG, inrast_TEMPKAVG, row, data_type_tempkavg) < 0)
	    G_fatal_error(_("Could not read from <%s>"), TEMPKAVG);
	if (G_get_raster_row
	    (infd_TEMPKMIN, inrast_TEMPKMIN, row, data_type_tempkmin) < 0)
	    G_fatal_error(_("Could not read from <%s>"), TEMPKMIN);
	if (G_get_raster_row
	    (infd_TEMPKMAX, inrast_TEMPKMAX, row, data_type_tempkmax) < 0)
	    G_fatal_error(_("Could not read from <%s>"), TEMPKMAX);
	if (!original->answer) {
	    if (G_get_raster_row(infd_P, inrast_P, row, data_type_p) < 0)
		G_fatal_error(_("Could not read from <%s>"), P);
	}
	for (col = 0; col < ncols; col++) {
	    /* read current cell from line buffer */
	    switch (data_type_rnet) {
	    case CELL_TYPE:
		d_rnet = (double)((CELL *) inrast_RNET)[col];
		break;
	    case FCELL_TYPE:
		d_rnet = (double)((FCELL *) inrast_RNET)[col];
		break;
	    case DCELL_TYPE:
		d_rnet = ((DCELL *) inrast_RNET)[col];
		break;
	    }
	    switch (data_type_tempkavg) {
	    case CELL_TYPE:
		d_tempkavg = (double)((CELL *) inrast_TEMPKAVG)[col];
		break;
	    case FCELL_TYPE:
		d_tempkavg = (double)((FCELL *) inrast_TEMPKAVG)[col];
		break;
	    case DCELL_TYPE:
		d_tempkavg = ((DCELL *) inrast_TEMPKAVG)[col];
		break;
	    }
	    switch (data_type_tempkmin) {
	    case CELL_TYPE:
		d_tempkmin = (double)((CELL *) inrast_TEMPKMIN)[col];
		break;
	    case FCELL_TYPE:
		d_tempkmin = (double)((FCELL *) inrast_TEMPKMIN)[col];
		break;
	    case DCELL_TYPE:
		d_tempkmin = ((DCELL *) inrast_TEMPKMIN)[col];
		break;
	    }
	    switch (data_type_tempkmax) {
	    case CELL_TYPE:
		d_tempkmax = (double)((CELL *) inrast_TEMPKMAX)[col];
		break;
	    case FCELL_TYPE:
		d_tempkmax = (double)((FCELL *) inrast_TEMPKMAX)[col];
		break;
	    case DCELL_TYPE:
		d_tempkmax = ((DCELL *) inrast_TEMPKMAX)[col];
		break;
	    }
	    if (!original->answer) {
		switch (data_type_p) {
		case CELL_TYPE:
		    d_p = (double)((CELL *) inrast_P)[col];
		    break;
		case FCELL_TYPE:
		    d_p = (double)((FCELL *) inrast_P)[col];
		    break;
		case DCELL_TYPE:
		    d_p = ((DCELL *) inrast_P)[col];
		    break;
		}
	    }
	    if (G_is_d_null_value(&d_rnet) ||
		G_is_d_null_value(&d_tempkavg) ||
		G_is_d_null_value(&d_tempkmin) ||
		G_is_d_null_value(&d_tempkmax) || G_is_d_null_value(&d_p)) {
		G_set_d_null_value(&outrast[col], 1);
	    }
	    else {
		if (original->answer) {
		    d_daily_et =
			mh_original(d_rnet, d_tempkavg, d_tempkmax,
				    d_tempkmin, d_p);
		}
		else if (samani->answer) {
		    d_daily_et =
			mh_samani(d_rnet, d_tempkavg, d_tempkmax, d_tempkmin);
		}
		else {
		    d_daily_et =
			mh_eto(d_rnet, d_tempkavg, d_tempkmax, d_tempkmin,
			       d_p);
		}
		if (zero->answer && d_daily_et < 0)
		    d_daily_et = 0.0;
		/* write calculated ETP to output line buffer */
		outrast[col] = d_daily_et;
	    }
	}


	/* write output line buffer to output raster file */
	if (G_put_raster_row(outfd, outrast, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to <%s>"), ETa);

    }
    /* free buffers and close input maps */

    G_free(inrast_RNET);
    G_free(inrast_TEMPKAVG);
    G_free(inrast_TEMPKMIN);
    G_free(inrast_TEMPKMAX);
    if (!original->answer) {
	G_free(inrast_P);
    }
    G_close_cell(infd_RNET);
    G_close_cell(infd_TEMPKAVG);
    G_close_cell(infd_TEMPKMIN);
    G_close_cell(infd_TEMPKMAX);
    if (!original->answer) {
	G_close_cell(infd_P);
    }
    /* generate color table between -20 and 20 */
    G_make_rainbow_colors(&color, -20, 20);
    G_write_colors(ETa, G_mapset(), &color);

    G_short_history(ETa, "raster", &history);
    G_command_history(&history);
    G_write_history(ETa, &history);

    /* free buffers and close output map */
    G_free(outrast);
    G_close_cell(outfd);

    return 0;
}
