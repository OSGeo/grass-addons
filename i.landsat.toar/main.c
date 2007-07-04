
/****************************************************************************
 *
 * MODULE:       r.landsat.toar
 *
 * AUTHOR(S):    E. Jorge Tizado - ejtizado@unileon.es
 *
 * PURPOSE:      Calculate TOA Reflectance and Kinectic Temperature
 *               for Landsat 4/5 TM or 7 ETM+
 *
 * COPYRIGHT:    (C) 2002,2005 by the GRASS Development Team
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

#include "local_proto.h"
#include "landsat.h"

int main(int argc, char *argv[])
{
    struct Cell_head cellhd, window;
    char *mapset;		/* mapset name */

    void *inrast;		/* input buffer */
    unsigned char *outrast;	/* output buffer */
    int nrows, ncols;
    int row, col;
    int infd, outfd;		/* file descriptor */

    RASTER_MAP_TYPE in_data_type;
    RASTER_MAP_TYPE out_data_type = DCELL_TYPE;

    struct History history;	/* holds meta-data (title, comments,..) */
    struct GModule *module;	/* GRASS module for parsing arguments */

    int verbose = 1;
    struct Option *input, *output, *metfn, *date, *elev, *bgain;
    char *name;			/* band raster name */
    char *met;			/* met filename */
    double elevation;		/* solar elevation */
    struct Flag *sat4, *sat5, *sat7, *flag, *param;

    char band_in[127], band_out[127];
    int i, qcal;
    double gain, bias, cref, rad, ref;

    lsat_data lsat;
    char command[300];

    /* initialize GIS environment */
    G_gisinit(argv[0]);

    /* initialize module */
    module = G_define_module();
    module->description = _("Calculates reflectance at top of atmosphere or temperature for Landsat");

    input = G_define_option();
    input->key = _("band_prefix");
    input->type = TYPE_STRING;
    input->required = YES;
    input->gisprompt = _("input,cell,raster");
    input->description = _("Base name of the landsat band rasters (.?)");

    metfn = G_define_option();
    metfn->key = _("metfile");
    metfn->type = TYPE_STRING;
    metfn->required = NO;
    metfn->gisprompt = _(".met file");
    metfn->description = _("Header File [.met] (only ETM+)");

    bgain = G_define_option();
    bgain->key = _("gain");
    bgain->type = TYPE_STRING;
    bgain->required = NO;
    bgain->gisprompt = _("band gain");
    bgain->description = _("Gain of bands 1,2,3,4,5,61,62,7,8 (only ETM+)");
    bgain->answer = "HHHLHLHHL";

    date = G_define_option();
    date->key = _("date");
    date->type = TYPE_STRING;
    date->required = NO;
    date->gisprompt = _("image acquisition date");
    date->description = _("Image acquisition date (yyyy-mm-dd)");

    elev = G_define_option();
    elev->key = _("solar");
    elev->type = TYPE_DOUBLE;
    elev->required = NO;
    elev->gisprompt = _("solar elevation");
    elev->description = _("Solar elevation in degrees");

    /* Define the different flags */
    sat4 = G_define_flag();
    sat4->key = '4';
    sat4->description = _("Landsat-4 TM (specify date and solar)");
    sat4->answer = 0;

    sat5 = G_define_flag();
    sat5->key = '5';
    sat5->description = _("Landsat-5 TM (specify date and solar)");
    sat5->answer = 0;

    sat7 = G_define_flag();
    sat7->key = '7';
    sat7->description = _("Landsat-7 ETM+ (specify either met or date, solar, and gain)");
    sat7->answer = 0;

    flag = G_define_flag();
    flag->key = 'f';
    flag->description = _("LANDSAT-5: product creation after instead of before May 5, 2003.\n\n\tLANDSAT-7: product creation before instead of after July 1, 2000");
    flag->answer = 0;

    param = G_define_flag();
    param->key = 'v';
    param->description = _("Show parameters applied");

    /* options and flags parser */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* ----- START -------------------- */
    /* stores options and flags to variables */
    met = metfn->answer;
    name = input->answer;
    elevation = 0.;

    if( !sat4->answer && !sat5->answer && !sat7->answer)
        G_fatal_error(_("Need satellite type"));

    if (sat7->answer && met != NULL) {
	met_ETM(met, &lsat);
	fprintf(stdout, "Landsat-7 ETM+ with data in met file [%s]\n", met);
    }
    else if (date->answer == NULL || elev->answer == NULL) {
	G_fatal_error(_("Need date and solar elevation"));
    }
    else {
	elevation = atof(elev->answer);
	if (sat7->answer) {
	    if (bgain->answer && strlen(bgain->answer) > 8) {
		set_ETM(&lsat, date->answer, elevation, bgain->answer, flag->answer);
		fprintf(stdout, "Landsat 7 ETM+ %s July 1, 2000\n", ((flag->answer) ? "before" : "after"));
	    }
	    else {
		G_fatal_error(_("Need band gain with 9 (H/L) data for Landsat-7"));
	    }
	}
	else {
	    if (sat4->answer) {
		set_TM4(&lsat, date->answer, elevation);
		fprintf(stdout, "Landsat-4 TM\n");
	    }
	    else {
		set_TM5(&lsat, date->answer, elevation, flag->answer);
		fprintf(stdout, "Landsat-5 TM %s May 5, 2003\n", ((flag->answer) ? "after" : "before"));
	    }
	}
    }

    if (param->answer) {
	fprintf(stdout, " ACQUISITION_DATE %s\n", lsat.date);
	fprintf(stdout, "   earth-sun distance    = %.8lf\n", lsat.dist_es);
	fprintf(stdout, "   solar elevation angle = %.8lf\n", lsat.sun_elev);
	for (i = 0; i < lsat.bands; i++) {
	    fprintf(stdout, "-------------------\n");
	    fprintf(stdout, " BAND %d (code %d)\n", lsat.band[i].number, lsat.band[i].code);
	    if (lsat.band[i].number == 6) {
		fprintf(stdout, "   const K1 = %lf\n", lsat.K1);
		fprintf(stdout, "   const K2 = %lf\n", lsat.K2);
	    }
	    else {
                fprintf(stdout, "   calibrated digital number (QCAL): %.1lf to %.1lf\n", lsat.band[i].qcalmin,
                        lsat.band[i].qcalmax);
                fprintf(stdout, "   radiance at-detector (L): %.3lf to %.3lf  ", lsat.band[i].lmin, lsat.band[i].lmax);

		gain = (lsat.band[i].lmax - lsat.band[i].lmin) / (lsat.band[i].qcalmax - lsat.band[i].qcalmin);
		bias = lsat.band[i].lmin - gain * lsat.band[i].qcalmin;
		fprintf(stdout, "...  radiance = %.8lf DN + %.8lf\n", gain, bias);

		cref = lsat_refrad_ratio(lsat.dist_es, lsat.sun_elev, lsat.band[i].esun);
		fprintf(stdout, "   exoatmospheric irradiance (ESUN): %.5lf  ", lsat.band[i].esun);
		fprintf(stdout, "...  reflectance = %.8lf · radiance\n", cref);

                fprintf(stdout, "   atmospheric effect: a = %.8lf, b = %.8lf\n", cref * gain, cref * bias);
                fprintf(stdout, "   r.mapcalc '%s.%drc=if(%s.%dr<(%.8lf*dp+%.8lf),%.8lf,%s.%dr-%.8lf*dp)'\n",
                        name, lsat.band[i].number, name, lsat.band[i].number, cref*gain, cref*bias, cref*bias, name, lsat.band[i].number, cref*gain);
            }
	}
	fprintf(stdout, "-------------------\n");
	fflush(stdout);
    }

    G_get_window(&window);

    for (i = 0; i < lsat.bands; i++) {
	snprintf(band_in, 127, "%s.%d", name, lsat.band[i].code);
	snprintf(band_out, 127, "%s.toar.%d", name, lsat.band[i].code);

	mapset = G_find_cell2(band_in, "");
	if (mapset == NULL) {
	    G_warning(_("cell file [%s] not found"), band_in);
	    continue;
	}

	if (G_legal_filename(band_out) < 0)
	    G_fatal_error(_("[%s] is an illegal name"), band_out);

	/* determine the inputmap type (CELL/FCELL/DCELL) */
	in_data_type = G_raster_map_type(band_in, mapset);
	if ((infd = G_open_cell_old(band_in, mapset)) < 0)
	    G_fatal_error(_("Cannot open cell file [%s]"), band_in);

	/* controlling, if we can open input raster */
	if (G_get_cellhd(band_in, mapset, &cellhd) < 0)
	    G_fatal_error(_("Cannot read file header of [%s]"), band_in);

	/* set same size as original band raster */
	if (G_set_window(&cellhd) < 0)
	    G_fatal_error(_("Unable to set region"));

	/* Allocate input and output buffer */
	inrast = G_allocate_raster_buf(in_data_type);
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast = G_allocate_raster_buf(out_data_type);

	/* controlling, if we can write the raster */
	if ((outfd = G_open_raster_new(band_out, out_data_type)) < 0)
	    G_fatal_error(_("Could not open <%s>"), band_out);

	/* ================================================================= */
	/* ----- CORE ----- */
	G_message("Reflectance of %s to %s", band_in, band_out);
	for (row = 0; row < nrows; row++) {

	    if (verbose)
		G_percent(row, nrows, 2);

	    if (G_get_raster_row(infd, inrast, row, in_data_type) < 0)
		G_fatal_error(_("Could not read from <%s>"), band_in);

	    for (col = 0; col < ncols; col++) {

		qcal = (int)((CELL *) inrast)[col];

		if (qcal < lsat.band[i].qcalmin) {
		    ref = -1.;
		}
		else {
		    rad = lsat_qcal2rad(qcal, lsat.band[i].lmax, lsat.band[i].lmin, lsat.band[i].qcalmax, lsat.band[i].qcalmin);
		    if (lsat.band[i].number == 6) {
			ref = lsat_rad2temp(rad, lsat.K1, lsat.K2);
		    }
		    else {
			ref = lsat_rad2ref(rad, lsat.dist_es, lsat.sun_elev, lsat.band[i].esun);
		    }
		}
		((DCELL *) outrast)[col] = ref;
	    }

	    if (G_put_raster_row(outfd, outrast, out_data_type) < 0)
		G_fatal_error(_("Cannot write to <%s>"), band_out);
	}
	/* ----- END CORE ----- */
	/* ================================================================= */

	G_free(inrast);
	G_free(outrast);
	G_close_cell(infd);
	G_close_cell(outfd);

	/* set map color to grey */
        sprintf(command, "r.colors map=%s color=grey", band_out);
        system(command);

	/* set -1. to null */
        G_message("REMEMBER: -1 is a NULL value");
/*         sprintf(command, "r.null map=%s setnull=-1", band_out); */
/*         system(command);              */

	/* add command line incantation to history file */
	G_short_history(band_out, "raster", &history);
	G_command_history(&history);
	G_write_history(band_out, &history);
    }

    G_set_window(&window);
    exit(EXIT_SUCCESS);
}
