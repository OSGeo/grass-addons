
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
                  *adate, *elev, *bgain, *pdate, *metho, * perc;
    char *name;
    char *met;
    char *atcor;
    struct Flag *sat1, *sat2, *sat3, *sat4, *sat5, *sat7, *msss,
                *verbo, *frad;

    char band_in[127], band_out[127];
    int i, method, qcal;
    double rad, ref, percent;
    lsat_data lsat;
    char command[300];

    /* initialize GIS environment */
    G_gisinit(argv[0]);

    /* initialize module */
    module = G_define_module();
    module->description = _("Calculates top-of-atmosphere radiance or reflectance and temperature for Landsat MSS/TM/ETM+");
    module->keywords = _("Top-Of-Atmosphere Radiance or Reflectance.\n Landsat-1 MSS, Landsat-2 MSS, Landsat-3 MSS, Landsat-4 MSS, Landsat-5 MSS,\n Landsat-4 TM, Landsat-5 TM,\n Landsat-7 ETM+");

    /* It defines the different parameters */
    input = G_define_option();
    input->key = _("band_prefix");
    input->type = TYPE_STRING;
    input->required = YES;
    input->gisprompt = _("input,cell,raster");
    input->description = _("Base name of the landsat band rasters (.#)");

    metfn = G_define_option();
    metfn->key = _("metfile");
    metfn->type = TYPE_STRING;
    metfn->required = NO;
    metfn->gisprompt = _(".met file");
    metfn->description = _("Landsat ETM+ or TM5 header file (.met)");

    adate = G_define_option();
    adate->key = _("date");
    adate->type = TYPE_STRING;
    adate->required = NO;
    adate->gisprompt = _("image acquisition date");
    adate->description = _("Image acquisition date (yyyy-mm-dd)");

    elev = G_define_option();
    elev->key = _("solar");
    elev->type = TYPE_DOUBLE;
    elev->required = NO;
    elev->gisprompt = _("solar elevation");
    elev->description = _("Solar elevation in degrees");

    bgain = G_define_option();
    bgain->key = _("gain");
    bgain->type = TYPE_STRING;
    bgain->required = NO;
    bgain->gisprompt = _("band gain");
    bgain->description = _("Gain (H/L) of all Landsat ETM+ bands (1-5,61,62,7,8)");

    pdate = G_define_option();
    pdate->key = _("product_date");
    pdate->type = TYPE_STRING;
    pdate->required = NO;
    pdate->gisprompt = _("image production date");
    pdate->description = _("Image creation date (yyyy-mm-dd)");

    metho = G_define_option();
    metho->key = _("method");
    metho->type = TYPE_STRING;
    metho->required = NO;
    metho->options = "uncorrected,corrected,simplified";
    metho->gisprompt = _("atmosferic correction methods");
    metho->description = _("Atmosferic correction methods");
    metho->answer = "uncorrected";

    perc = G_define_option();
    perc->key = _("percent");
    perc->type = TYPE_DOUBLE;
    perc->required = NO;
    perc->gisprompt = _("percent of solar irradiance in path radiance");
    perc->description = _("Percent of solar irradiance in path radiance");
    perc->answer = "0.01";

    /* It defines the different flags */
    frad = G_define_flag();
    frad->key = 'r';
    frad->description = _("Output at-sensor radiance for all bands");
    frad->answer = 0;

    sat1 = G_define_flag();
    sat1->key = '1';
    sat1->description = _("Landsat-1 MSS");
    sat1->answer = 0;

    sat2 = G_define_flag();
    sat2->key = '2';
    sat2->description = _("Landsat-2 MSS");
    sat2->answer = 0;

    sat3 = G_define_flag();
    sat3->key = '3';
    sat3->description = _("Landsat-3 MSS");
    sat3->answer = 0;

    sat4 = G_define_flag();
    sat4->key = '4';
    sat4->description = _("Landsat-4 TM");
    sat4->answer = 0;

    sat5 = G_define_flag();
    sat5->key = '5';
    sat5->description = _("Landsat-5 TM");
    sat5->answer = 0;

    sat7 = G_define_flag();
    sat7->key = '7';
    sat7->description = _("Landsat-7 ETM+");
    sat7->answer = 0;

    msss = G_define_flag();
    msss->key = 's';
    msss->description = _("Modify sensor of Landsat-4/5 to MSS");
    msss->answer = 0;

    verbo = G_define_flag();
    verbo->key = 'v';
    verbo->description = _("Show parameters applied");
    verbo->answer = 0;

    /* options and afters parser */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /*****************************************
     * ---------- START --------------------
     * Stores options and flag to variables
     *****************************************/
    met = metfn->answer;
    name = input->answer;
    atcor = metho->answer;

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

    percent = atof(perc->answer);

    if (met == NULL &&
        (sat1->answer + sat2->answer + sat3->answer +
         sat4->answer + sat5->answer + sat7->answer) != 1)
        G_fatal_error(_("Select one and only one type of satellite"));

    /* Data from MET file: only Landsat-7 ETM+ and Landsat-5 TM  */
    if (met != NULL) {
        if (sat7->answer) met_ETM(met, &lsat);
        else              met_TM5(met, &lsat);
        fprintf(stdout, "Landsat-%d %s with data set in met file [%s]\n",
                lsat.number, lsat.sensor, met);
        if (elev->answer != NULL)
           lsat.sun_elev = atof(elev->answer);         /* Overwrite sun elevation of met file */
    }
    /* Data from date and solar elevation */
    else if (adate->answer == NULL || elev->answer == NULL) {
	G_fatal_error(_("Lacking date or solar elevation for this satellite"));
    }
    else {
	if (sat7->answer) { /* Need gain */
	    if (bgain->answer && strlen(bgain->answer) == 9) {
		set_ETM(&lsat, bgain->answer);
		fprintf(stdout, "Landsat 7 ETM+\n");
	    }
	    else {
		G_fatal_error(_("For Landsat-7 is necessary band gain with 9 (H/L) data"));
	    }
	}
	else { /* Not need gain */
            if (sat5->answer) {
                if (msss->answer) set_MSS5(&lsat);
                else              set_TM5 (&lsat);
                fprintf(stdout, "Landsat-5 %s\n", lsat.sensor);
            }
            else if (sat4->answer) {
                if (msss->answer) set_MSS4(&lsat);
                else              set_TM4 (&lsat);
                fprintf(stdout, "Landsat-4 %s\n", lsat.sensor);
            }
            else if (sat3->answer) {
                set_MSS3(&lsat);
                fprintf(stdout, "Landsat-3 MSS\n");
            }
            else if (sat2->answer) {
                set_MSS2(&lsat);
                fprintf(stdout, "Landsat-2 MSS\n");
            }
            else if (sat1->answer) {
                set_MSS1(&lsat);
                fprintf(stdout, "Landsat-1 MSS\n");
            }
            else
            {
                G_fatal_error(_("Lacking satellite type"));
            }
	}
    }

    /* Set method and calculate band constants */
    switch(atcor[0])
    {
        case 'c':
            method = CORRECTED;
            break;
        case 's':
            method = SIMPLIFIED;
            break;
        default:
            method = UNCORRECTED;
            break;
    }
    for (i = 0; i < lsat.bands; i++)
    {
        lsat_bandctes(&lsat, i, method, 0.0, percent);
    }


    /*****************************************
     * ---------- VERBOSE ------------------
     *****************************************/
    if (verbo->answer) {
	fprintf(stdout, " ACQUISITION DATE %s [production date %s]\n", lsat.date, lsat.creation);
	fprintf(stdout, "   earth-sun distance    = %.8lf\n", lsat.dist_es);
        fprintf(stdout, "   solar elevation angle = %.8lf\n", lsat.sun_elev);
        fprintf(stdout, "   Method for at sensor values = %s\n",
            (atcor[0]=='c' ? "corrected" : (atcor[0]=='s' ? "simplified" : "uncorrected")));
        if (atcor[0] == 's')
        {
            fprintf(stdout, "   percent of solar irradiance in path radiance = %.4lf\n", percent);
        }
	for (i = 0; i < lsat.bands; i++) {
	    fprintf(stdout, "-------------------\n");
	    fprintf(stdout, " BAND %d %s (code %d)\n",
                    lsat.band[i].number, (lsat.band[i].thermal ? "thermal " : ""),
                    lsat.band[i].code);
            fprintf(stdout, "   calibrated digital number (DN): %.1lf to %.1lf\n",
                    lsat.band[i].qcalmin, lsat.band[i].qcalmax);
            fprintf(stdout, "   calibration constants (L): %.3lf to %.3lf\n",
                    lsat.band[i].lmin, lsat.band[i].lmax);
            fprintf(stdout, "   at-%s radiance = %.5lf · DN + %.5lf\n",
                    (atcor[0] == 's' ? "surface" : "sensor"),
                    lsat.band[i].gain, lsat.band[i].bias);
	    if (lsat.band[i].thermal)
            {
		fprintf(stdout, "   at-%s temperature = %.3lf / log[(%.3lf / radiance) + 1.0]\n",
                        (atcor[0] == 's' ? "surface" : "sensor"),
                        lsat.band[i].K2, lsat.band[i].K1);
	    }
	    else {
                fprintf(stdout, "   mean solar exoatmospheric irradiance (ESUN): %.3lf\n",
                        lsat.band[i].esun);
		fprintf(stdout, "   at-%s reflectance = radiance / %.5lf\n",
                        (atcor[0] == 's' ? "surface" : "sensor"),
                        lsat.band[i].K2);
            }
	}
	fprintf(stdout, "-------------------\n");
	fflush(stdout);
    }

    /*****************************************
     * ---------- CALCULUS -----------------
     *****************************************/
    G_get_window(&window);

    for (i = 0; i < lsat.bands; i++) {
	snprintf(band_in, 127, "%s.%d", name, lsat.band[i].code);
	snprintf(band_out, 127, "%s.toar.%d", name, lsat.band[i].code);

	mapset = G_find_cell2(band_in, "");
	if (mapset == NULL) {
	    G_warning(_("raster file [%s] not found"), band_in);
	    continue; }

	if (G_legal_filename(band_out) < 0)
	    G_fatal_error(_("[%s] is an illegal name"), band_out);

	in_data_type = G_raster_map_type(band_in, mapset);
	if ((infd = G_open_cell_old(band_in, mapset)) < 0)
	    G_fatal_error(_("Cannot open cell file [%s]"), band_in);

	if (G_get_cellhd(band_in, mapset, &cellhd) < 0)
	    G_fatal_error(_("Cannot read file header of [%s]"), band_in);

	/* set same size as original band raster */
	if (G_set_window(&cellhd) < 0)
	    G_fatal_error(_("Unable to set region"));

	/* Allocate input and output buffer */
	inrast = G_allocate_raster_buf(in_data_type);
	outrast = G_allocate_raster_buf(DCELL_TYPE);

	/* controlling, if we can write the raster */
	if ((outfd = G_open_raster_new(band_out, DCELL_TYPE)) < 0)
	    G_fatal_error(_("Could not open <%s>"), band_out);

	/* ================================================================= */
        G_message("%s of %s to %s",
                  (frad->answer ? "Radiance" : "Reflectance"),
                  band_in, band_out);

        nrows = G_window_rows();
        ncols = G_window_cols();
	for (row = 0; row < nrows; row++)
        {
	    if (verbose)
		G_percent(row, nrows, 2);

            if (G_get_raster_row(infd, inrast, row, in_data_type) < 0)
		G_fatal_error(_("Could not read from <%s>"), band_in);

	    for (col = 0; col < ncols; col++)
            {
                switch(in_data_type)
                {
                        case CELL_TYPE:
                                ptr = (void *)((CELL *)inrast + col);
                                qcal = (int)((CELL *) inrast)[col];
                                break;
                        case FCELL_TYPE:
                                ptr = (void *)((FCELL *)inrast + col);
                                qcal = (int)((FCELL *) inrast)[col];
                                break;
                        case DCELL_TYPE:
                                ptr = (void *)((DCELL *)inrast + col);
                                qcal = (int)((DCELL *) inrast)[col];
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
                        }
                    }
                    ((DCELL *) outrast)[col] = ref;
                }
	    }

	    if (G_put_raster_row(outfd, outrast, DCELL_TYPE) < 0)
		G_fatal_error(_("Cannot write to <%s>"), band_out);
	}
	/* ================================================================= */

	G_free(inrast);
        G_close_cell(infd);
	G_free(outrast);
	G_close_cell(outfd);

        sprintf(command, "r.colors map=%s color=grey", band_out);
        system(command);

	G_short_history(band_out, "raster", &history);
	G_command_history(&history);
	G_write_history(band_out, &history);
    }

    G_set_window(&window);
    exit(EXIT_SUCCESS);
}
