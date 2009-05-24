
/****************************************************************************
 *
 * MODULE:       i.landsat.toar
 *
 * AUTHOR(S):    E. Jorge Tizado - ej.tizado@unileon.es
 *
 * PURPOSE:      Calculate TOA Radiance or Reflectance and Kinetic Temperature
 *               for Landsat 1/2/3/4/5 MS, 4/5 TM or 7 ETM+
 *
 * COPYRIGHT:    (C) 2002, 2005 2008 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#include "local_proto.h"

int main(int argc, char *argv[])
{
	struct History history;
	struct GModule *module;

	struct Cell_head cellhd, window;
	char *mapset;

	void *inrast, *outrast;
	int infd, outfd;
	void *ptr;
	int nrows, ncols, row, col;

	RASTER_MAP_TYPE in_data_type;

	int verbose = 1;
	struct Option *input, *metfn,
				*adate, *pdate, *elev, *bgain, *metho, *perc, *dark,
				*satz, *atmo;
	char *name, *met;
	struct Flag *sat1, *sat2, *sat3, *sat4, *sat5, *sat7, *msss,
				*verbo, *frad;

	lsat_data lsat;
	char band_in[127], band_out[127];
	int i, j, q, method, pixel, dn_dark[MAX_BANDS], dn_mode[MAX_BANDS];
	double qcal, rad, ref, percent, ref_mode, sat_zenith, rayleigh;

	unsigned long hist[256], h_max;

    /* initialize GIS environment */
    G_gisinit(argv[0]);

    /* initialize module */
    module = G_define_module();
    module->description = _("Calculates top-of-atmosphere radiance or reflectance and temperature for Landsat MSS/TM/ETM+");
    module->keywords = _("Top-Of-Atmosphere Radiance or Reflectance.\n Landsat-1 MSS, Landsat-2 MSS, Landsat-3 MSS, Landsat-4 MSS, Landsat-5 MSS,\n Landsat-4 TM, Landsat-5 TM,\n Landsat-7 ETM+");

    /* It defines the different parameters */
    input = G_define_option();
    input->key         = _("band_prefix");
    input->type        = TYPE_STRING;
    input->required    = YES;
    input->gisprompt   = _("input,cell,raster");
    input->description = _("Base name of the landsat band rasters (.#)");

    metfn = G_define_option();
    metfn->key         = _("metfile");
    metfn->type        = TYPE_STRING;
    metfn->required    = NO;
    metfn->gisprompt   = _(".met file");
    metfn->description = _("Landsat ETM+ or TM5 header file (.met)");

    adate = G_define_option();
    adate->key         = _("date");
    adate->type        = TYPE_STRING;
    adate->required    = NO;
    adate->gisprompt   = _("image acquisition date");
    adate->description = _("Image acquisition date (yyyy-mm-dd)");

    elev = G_define_option();
    elev->key         = _("solar_elevation");
    elev->type        = TYPE_DOUBLE;
    elev->required    = NO;
    elev->gisprompt   = _("solar elevation");
    elev->description = _("Solar elevation in degrees");

    bgain = G_define_option();
    bgain->key         = _("gain");
    bgain->type        = TYPE_STRING;
    bgain->required    = NO;
    bgain->gisprompt   = _("band gain");
    bgain->description = _("Gain (H/L) of all Landsat ETM+ bands (1-5,61,62,7,8)");

    pdate = G_define_option();
    pdate->key         = _("product_date");
    pdate->type        = TYPE_STRING;
    pdate->required    = NO;
    pdate->gisprompt   = _("image production date");
    pdate->description = _("Image creation date (yyyy-mm-dd)");

    metho = G_define_option();
    metho->key         = _("method");
    metho->type        = TYPE_STRING;
    metho->required    = NO;
    metho->options     = "uncorrected,corrected,dos1,dos2,dos2b,dos3,dos4";
    metho->gisprompt   = _("atmosferic correction method");
    metho->description = _("Atmosferic correction method");
    metho->answer      = "uncorrected";

	perc = G_define_option();
	perc->key         = _("percent");
	perc->type        = TYPE_DOUBLE;
	perc->required    = NO;
	perc->gisprompt   = _("percent of solar radiance in path radiance");
	perc->description = _("Percent of solar radiance in path radiance");
	perc->answer      = "0.01";

	dark = G_define_option();
	dark->key         = _("pixel");
	dark->type        = TYPE_INTEGER;
	dark->required    = NO;
	dark->gisprompt   = _("pixels to dark object");
	dark->description = _("Minimum pixels to consider digital number as dark object");
	dark->answer      = "1000";

	satz = G_define_option();
	satz->key         = _("sat_zenith");
	satz->type        = TYPE_DOUBLE;
	satz->required    = NO;
	satz->gisprompt   = _("satellite zenith");
	satz->description = _("Satellite zenith in degrees");
	satz->answer      = "8.2000";

	atmo = G_define_option();
	atmo->key         = _("rayleigh");
	atmo->type        = TYPE_DOUBLE;
	atmo->required    = NO;
	atmo->gisprompt   = _("Rayleigh atmosphere");
	atmo->description = _("Rayleigh atmosphere");
	atmo->answer      = "0.0";

	/* It defines the different flags */
    frad = G_define_flag();
    frad->key         = 'r';
    frad->description = _("Output at-sensor radiance for all bands");
	frad->answer      = 0;

    sat1 = G_define_flag();
	sat1->key         = '1';
    sat1->description = _("Landsat-1 MSS");
	sat1->answer      = 0;

    sat2 = G_define_flag();
	sat2->key         = '2';
    sat2->description = _("Landsat-2 MSS");
	sat2->answer      = 0;

    sat3 = G_define_flag();
	sat3->key         = '3';
    sat3->description = _("Landsat-3 MSS");
	sat3->answer      = 0;

    sat4 = G_define_flag();
	sat4->key         = '4';
    sat4->description = _("Landsat-4 TM");
	sat4->answer      = 0;

    sat5 = G_define_flag();
	sat5->key         = '5';
    sat5->description = _("Landsat-5 TM");
	sat5->answer      = 0;

    sat7 = G_define_flag();
	sat7->key         = '7';
    sat7->description = _("Landsat-7 ETM+");
	sat7->answer      = 0;

    msss = G_define_flag();
	msss->key         = 's';
    msss->description = _("Set sensor of Landsat-4/5 to MSS");
	msss->answer      = 0;

    verbo = G_define_flag();
	verbo->key         = 'v';
    verbo->description = _("Show parameters applied");
    verbo->answer      = 0;

    /* options and afters parser */
    if (G_parser(argc, argv))
		exit(EXIT_FAILURE);

    /*****************************************
     * ---------- START --------------------
     * Stores options and flag to variables
     *****************************************/
	met = metfn->answer;
	name = input->answer;

	if (adate->answer != NULL) {
		strncpy(lsat.date, adate->answer, 11);
		lsat.date[10] = '\0';
	}
	else
		lsat.date[0] = '\0';

	if (pdate->answer != NULL) {
		strncpy(lsat.creation, pdate->answer, 11);
		lsat.creation[10] = '\0';
	}
	else
		lsat.creation[0] = '\0';

	lsat.sun_elev = elev->answer == NULL ? 0. : atof(elev->answer);
	percent       = atof(perc->answer);
	pixel         = atoi(dark->answer);
	sat_zenith    = atof(satz->answer);
	rayleigh      = atof(atmo->answer);

	if (met == NULL &&
		(sat1->answer + sat2->answer + sat3->answer +
		 sat4->answer + sat5->answer + sat7->answer) != 1)
		G_fatal_error(_("Select one and only one type of satellite"));

    /* Data from MET file: only Landsat-7 ETM+ and Landsat-5 TM  */
	if (met != NULL) {
		if (sat7->answer) met_ETM(met, &lsat); else met_TM5(met, &lsat);
		G_message("Landsat-%d %s with data set in met file [%s]", lsat.number, lsat.sensor, met);
		if (elev->answer != NULL)
			lsat.sun_elev = atof(elev->answer);         /* Overwrite solar elevation of met file */
	}
	/* Data from date and solar elevation */
	else if (adate->answer == NULL || elev->answer == NULL) {
		G_fatal_error(_("Lacking date or solar elevation for this satellite"));
	}
    else {
		if (sat7->answer) { /* Need gain */
	    	if (bgain->answer != NULL && strlen(bgain->answer) == 9) {
				set_ETM(&lsat, bgain->answer);
				G_message("Landsat 7 ETM+");
	    	}
	    	else {
				G_fatal_error(_("For Landsat-7 is necessary band gain with 9 (H/L) data"));
	    	}
		}
		else { /* Not need gain */
			if (sat5->answer) {
				if (msss->answer) set_MSS5(&lsat); else set_TM5 (&lsat);
				G_message("Landsat-5 %s", lsat.sensor);
			}
			else if (sat4->answer) {
				if (msss->answer) set_MSS4(&lsat); else set_TM4 (&lsat);
				G_message("Landsat-4 %s", lsat.sensor);
			}
			else if (sat3->answer) {
				set_MSS3(&lsat);
				G_message("Landsat-3 MSS");
			}
			else if (sat2->answer) {
				set_MSS2(&lsat);
				G_message("Landsat-2 MSS");
			}
			else if (sat1->answer) {
				set_MSS1(&lsat);
				G_message("Landsat-1 MSS");
			}
			else {
				G_fatal_error(_("Lacking satellite type"));
			}
		}
	}

	/*****************************************
	* ------------ PREPARATION --------------
	*****************************************/
	if (G_strcasecmp(metho->answer, "corrected") == 0)	method = CORRECTED;
	else if (G_strcasecmp(metho->answer, "dos1") == 0)	method = DOS1;
	else if (G_strcasecmp(metho->answer, "dos2") == 0)	method = DOS2;
	else if (G_strcasecmp(metho->answer, "dos2b") == 0)	method = DOS2b;
	else if (G_strcasecmp(metho->answer, "dos3") == 0)	method = DOS3;
	else if (G_strcasecmp(metho->answer, "dos4") == 0)	method = DOS4;
	else method = UNCORRECTED;
/*
	if (metho->answer[3] == 'r') 		method = CORRECTED;
	else if (metho->answer[3] == '1')	method = DOS1;
	else if (metho->answer[3] == '2')	method = (metho->answer[4] == '\0') ? DOS2 : DOS2b;
	else if (metho->answer[3] == '3')	method = DOS3;
	else if (metho->answer[3] == '4')	method = DOS4;
	else method = UNCORRECTED;
*/
	for (i = 0; i < lsat.bands; i++)
	{
		dn_mode[i] = 0;
		dn_dark[i] = (int)lsat.band[i].qcalmin;
		/* Calculate dark pixel */
		if (method > DOS && !lsat.band[i].thermal)
		{
			for (j = 0; j < 256; j++) hist[j] = 0L;

			snprintf(band_in, 127, "%s.%d", name, lsat.band[i].code);
			mapset = G_find_cell2(band_in, "");
			if (mapset == NULL) {
				G_warning(_("Raster file [%s] not found"), band_in);
				continue;
			}
			if ((infd = G_open_cell_old(band_in, mapset)) < 0)
				G_fatal_error(_("Cannot open cell file [%s]"), band_in);
			if (G_get_cellhd(band_in, mapset, &cellhd) < 0)
				G_fatal_error(_("Cannot read file header of [%s]"), band_in);
			if (G_set_window(&cellhd) < 0)
				G_fatal_error(_("Unable to set region"));

			in_data_type = G_raster_map_type(band_in, mapset);
			inrast = G_allocate_raster_buf(in_data_type);

			nrows = G_window_rows();
			ncols = G_window_cols();

			G_message("Calculating dark pixel of [%s] ... ", band_in);
			for (row = 0; row < nrows; row++)
			{
				G_get_raster_row(infd, inrast, row, in_data_type);
				for (col = 0; col < ncols; col++)
				{
					switch(in_data_type)
					{
						case CELL_TYPE:
							ptr = (void *)((CELL *)inrast + col);
							q = (int)*((CELL *)ptr);
							break;
						case FCELL_TYPE:
							ptr = (void *)((FCELL *)inrast + col);
							q = (int)*((FCELL *)ptr);
							break;
						case DCELL_TYPE:
							ptr = (void *)((DCELL *)inrast + col);
							q = (int)*((DCELL *)ptr);
							break;
					}
					if (!G_is_null_value(ptr, in_data_type) &&
						q >= lsat.band[i].qcalmin && q < 256)
						hist[q]++;
				}
			}
			/* DN of dark object */
			for (j = lsat.band[i].qcalmin; j < 256; j++)
			{
				if (hist[j] >= pixel)
				{
					dn_dark[i] = j;
					break;
				}
			}
			/* Mode of DN */
			h_max = 0L;
			for (j= lsat.band[i].qcalmin; j < 241; j++) /* Exclude ptentially saturated < 240 */
			{
				if (hist[j] > h_max)
				{
					h_max = hist[j];
					dn_mode[i] = j;
				}
			}
			G_message("... DN = %.2d [%d] : mode %.2d [%d] %s",
						dn_dark[i], hist[dn_dark[i]],
						dn_mode[i], hist[dn_mode[i]],
						hist[255] > hist[dn_mode[i]] ? ", excluding DN > 241" : "");

			G_free(inrast);
			G_close_cell(infd);
		}
		/* Calculate transformation constants */
		lsat_bandctes(&lsat, i, method, percent, dn_dark[i], sat_zenith, rayleigh);
	}

	/*****************************************
	 * ------------ VERBOSE ------------------
	 *****************************************/
	if (verbo->answer)
	{
		fprintf(stdout, " ACQUISITION DATE %s [production date %s]\n", lsat.date, lsat.creation);
		fprintf(stdout, "   earth-sun distance    = %.8lf\n", lsat.dist_es);
		fprintf(stdout, "   solar elevation angle = %.8lf\n", lsat.sun_elev);
		fprintf(stdout, "   Method of calculus = %s\n",
				(method==CORRECTED ? "CORRECTED"
								   : (method == UNCORRECTED ? "UNCORRECTED" : metho->answer)));
		if (method > DOS) {
			fprintf(stdout, "   percent of solar irradiance in path radiance = %.4lf\n", percent);
		}
		for (i = 0; i < lsat.bands; i++)
		{
			fprintf(stdout, "-------------------\n");
			fprintf(stdout, " BAND %d %s (code %d)\n",
					lsat.band[i].number, (lsat.band[i].thermal ? "thermal " : ""),
					lsat.band[i].code);
			fprintf(stdout, "   calibrated digital number (DN): %.1lf to %.1lf\n",
					lsat.band[i].qcalmin, lsat.band[i].qcalmax);
			fprintf(stdout, "   calibration constants (L): %.3lf to %.3lf\n",
					lsat.band[i].lmin, lsat.band[i].lmax);
			fprintf(stdout, "   at-%s radiance = %.5lf · DN + %.5lf\n",
					(method > DOS ? "surface" : "sensor"),
					lsat.band[i].gain, lsat.band[i].bias);
			if (lsat.band[i].thermal) {
				fprintf(stdout, "   at-sensor temperature = %.3lf / log[(%.3lf / radiance) + 1.0]\n",
						lsat.band[i].K2, lsat.band[i].K1);
			}
			else {
				fprintf(stdout, "   mean solar exoatmospheric irradiance (ESUN): %.3lf\n",
						lsat.band[i].esun);
				fprintf(stdout, "   at-%s reflectance = radiance / %.5lf\n",
						(method > DOS ? "surface" : "sensor"),
						lsat.band[i].K2);
				if (method > DOS) {
					fprintf(stdout, "   the darkness DN with a least %d pixels is %d\n", pixel, dn_dark[i] );
					fprintf(stdout, "   the mode of DN is %d\n", dn_mode[i] );
				}
			}
		}
		fprintf(stdout, "-------------------\n");
		fflush(stdout);
	}

	/*****************************************
	 * ------------ CALCULUS -----------------
	 *****************************************/

	for (i = 0; i < lsat.bands; i++)
	{
		snprintf(band_in, 127, "%s.%d", name, lsat.band[i].code);
		snprintf(band_out, 127, "%s.toar.%d", name, lsat.band[i].code);

		mapset = G_find_cell2(band_in, "");
		if (mapset == NULL) {
	    	G_warning(_("raster file [%s] not found"), band_in);
	    	continue; }

		in_data_type = G_raster_map_type(band_in, mapset);
		if ((infd = G_open_cell_old(band_in, mapset)) < 0)
	    	G_fatal_error(_("Cannot open cell file [%s]"), band_in);

		if (G_get_cellhd(band_in, mapset, &cellhd) < 0)
	    	G_fatal_error(_("Cannot read file header of [%s]"), band_in);

		/* set same size as original band raster */
		if (G_set_window(&cellhd) < 0)
	    	G_fatal_error(_("Unable to set region"));

		/* controlling, if we can write the raster */
		if (G_legal_filename(band_out) < 0)
	    	G_fatal_error(_("[%s] is an illegal name"), band_out);

		if ((outfd = G_open_raster_new(band_out, DCELL_TYPE)) < 0)
			G_fatal_error(_("Could not open <%s>"), band_out);

		/* Allocate input and output buffer */
		inrast  = G_allocate_raster_buf(in_data_type);
		outrast = G_allocate_raster_buf(DCELL_TYPE);

		nrows = G_window_rows();
		ncols = G_window_cols();
		/* ================================================================= */
		G_message("%s of %s to %s",
				  (frad->answer ? "Radiance"
			                    : (lsat.band[i].thermal) ? "Temperature" : "Reflectance"),
				   band_in, band_out);

		for (row = 0; row < nrows; row++)
		{
			if (verbose)
				G_percent(row, nrows, 2);

			G_get_raster_row(infd, inrast, row, in_data_type);
			for (col = 0; col < ncols; col++)
			{
				switch(in_data_type)
				{
					case CELL_TYPE:
							ptr = (void *)((CELL *)inrast + col);
							qcal = (double)((CELL *) inrast)[col];
							break;
					case FCELL_TYPE:
							ptr = (void *)((FCELL *)inrast + col);
							qcal = (double)((FCELL *) inrast)[col];
							break;
					case DCELL_TYPE:
							ptr = (void *)((DCELL *)inrast + col);
							qcal = (double)((DCELL *) inrast)[col];
							break;
				}
				if (G_is_null_value(ptr, in_data_type) ||
					qcal < lsat.band[i].qcalmin)
				{
					G_set_d_null_value((DCELL *)outrast + col, 1);
				}
				else
				{
					rad = lsat_qcal2rad(qcal, &lsat.band[i]);
					if (frad->answer)
					{
						ref = rad;
					}
					else
					{
						if (lsat.band[i].thermal)
						{
							ref = lsat_rad2temp(rad, &lsat.band[i]);
						}
						else
						{
							ref = lsat_rad2ref(rad, &lsat.band[i]);
							if (ref < 0. && method > DOS) ref = 0.;
						}
					}
					((DCELL *) outrast)[col] = ref;
				}
			}
			if (G_put_raster_row(outfd, outrast, DCELL_TYPE) < 0)
				G_fatal_error(_("Cannot write to <%s>"), band_out);
		}
		ref_mode = 0.;
		if (method > DOS && !lsat.band[i].thermal)
		{
			ref_mode = lsat_qcal2rad(dn_mode[i], &lsat.band[i]);
			ref_mode = lsat_rad2ref(ref_mode, &lsat.band[i]);
		}

	/* ================================================================= */

		G_free(inrast);
		G_close_cell(infd);
		G_free(outrast);
		G_close_cell(outfd);

		char command[300];
		sprintf(command, "r.colors map=%s color=grey", band_out);
		system(command);

		G_short_history(band_out, "raster", &history);

		sprintf(history.edhist[0], " %s of Landsat-%d %s (method %s)", lsat.band[i].thermal ? "Temperature": "Reflectance",
				lsat.number, lsat.sensor, metho->answer);
		sprintf(history.edhist[1], "----------------------------------------------------------------");
		sprintf(history.edhist[2], " Acquisition date ...................... %s", lsat.date);
		sprintf(history.edhist[3], " Production date ....................... %s\n", lsat.creation);
		sprintf(history.edhist[4], " Earth-sun distance (d) ................ %.8lf", lsat.dist_es);
		sprintf(history.edhist[5], " Digital number (DN) range ............. %.0lf to %.0lf", lsat.band[i].qcalmin, lsat.band[i].qcalmax);
		sprintf(history.edhist[6], " Calibration constants (Lmin to Lmax) .. %+.3lf to %+.3lf", lsat.band[i].lmin, lsat.band[i].lmax);
		sprintf(history.edhist[7], " DN to Radiance (gain and bias) ........ %+.5lf and %+.5lf", lsat.band[i].gain, lsat.band[i].bias);
		if (lsat.band[i].thermal) {
			sprintf(history.edhist[8], " Temperature (K1 and K2) ............... %.3lf and %.3lf", lsat.band[i].K1, lsat.band[i].K2);
            history.edlinecnt = 9;
		} else {
			sprintf(history.edhist[8], " Mean solar irradiance (ESUN) .......... %.3lf", lsat.band[i].esun);
			sprintf(history.edhist[9], " Reflectance = Radiance divided by ..... %.5lf", lsat.band[i].K2);
	        history.edlinecnt = 10;
			if (method > DOS) {
				sprintf(history.edhist[10], " ");
				sprintf(history.edhist[11], " Dark object (%4d pixels) DN = ........ %d", pixel, dn_dark[i]);
				sprintf(history.edhist[12], " Mode in reflectance histogram ......... %.5lf", ref_mode);
				history.edlinecnt = 13;
			}
		}
		sprintf (history.edhist[history.edlinecnt], "-----------------------------------------------------------------");
		history.edlinecnt++;

		G_command_history(&history);
		G_write_history(band_out, &history);
	}

	exit(EXIT_SUCCESS);
}
