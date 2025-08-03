/****************************************************************************
 *
 * MODULE:       i.evapo.senay
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Creates a map of actual evapotranspiration following
 *               the method of Senay (2007).
 *
 * COPYRIGHT:    (C) 2008-2011 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with
 *               GRASS for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

double solar_day(double lat, double doy, double tsw);
double solar_day_3d(double lat, double doy, double tsw, double slope,
                    double aspect);
double r_net_day(double bbalb, double solar, double tsw);
double r_net_day_bandara98(double surface_albedo, double solar_day,
                           double apparent_atm_emissivity,
                           double surface_emissivity, double air_temperature);
double et_pot_day(double rnetd, double tempk, double roh_w);
double evapfr_senay(double t_hot, double t_cold, double tempk);

int main(int argc, char *argv[])
{
    struct Cell_head cellhd; /*region+header info */
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *input1, *input2, *input3, *input4;
    struct Option *input5, *input6, *input7, *input8, *input9;
    struct Option *input10, *input11, *input12, *input13, *input14;
    struct Option *output1, *output2;
    struct Flag *flag1, *flag2, *flag3;
    struct History history; /*metadata */
    struct Colors colors;   /*Color rules */
    CELL val1, val2;        /*Color ranges */

    char *name;              /*input raster name */
    char *result1, *result2; /*output raster name */
    int infd_albedo, infd_tempk, infd_dem;
    int infd_lat, infd_doy, infd_tsw;
    int infd_slope, infd_aspect;
    int infd_tair, infd_e0;
    int infd_ndvi, infd_etpotd;
    int outfd1, outfd2;
    char *albedo, *tempk, *dem, *lat, *doy, *tsw;
    char *slope, *aspect, *tair, *e0, *ndvi, *etpotd;
    double roh_w, e_atm;
    int i = 0, j = 0;
    void *inrast_albedo, *inrast_tempk;
    void *inrast_dem, *inrast_lat;
    void *inrast_doy, *inrast_tsw;
    void *inrast_slope, *inrast_aspect;
    void *inrast_tair, *inrast_e0;
    void *inrast_ndvi, *inrast_etpotd;

    DCELL *outrast1, *outrast2;

    /********************************/
    /* Stats for Senay equation     */
    double t0dem_min = 400.0, t0dem_max = 200.0;
    double tempk_min = 400.0, tempk_max = 200.0;
    /********************************/

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("Actual ET"));
    G_add_keyword(_("evapotranspiration"));
    G_add_keyword(_("Senay"));
    module->description =
        _("Actual evapotranspiration, method after Senay (2007)");

    /* Define the different options */
    input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("temperature");
    input1->description = _("Name of the temperature layer [Degree Kelvin]");

    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = _("albedo");
    input2->description = _("Name of the Albedo layer [0.0-1.0]");

    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = _("elevation");
    input3->description = _("Name of the elevation layer [m]");

    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = _("latitude");
    input4->required = NO;
    input4->description = _("Name of the degree latitude layer [dd.ddd]");
    input4->guisection = _("Optional");

    input5 = G_define_standard_option(G_OPT_R_INPUT);
    input5->key = _("dayofyear");
    input5->required = NO;
    input5->description = _("Name of the Day of Year layer [0.0-366.0]");
    input5->guisection = _("Optional");

    input6 = G_define_standard_option(G_OPT_R_INPUT);
    input6->key = _("transmissivitysingleway");
    input6->required = NO;
    input6->description =
        _("Name of the single-way transmissivity layer [0.0-1.0]");
    input6->guisection = _("Optional");

    input7 = G_define_option();
    input7->key = _("waterdensity");
    input7->type = TYPE_DOUBLE;
    input7->required = NO;
    input7->description = _("Value of the density of fresh water ~[1000-1020]");
    input7->answer = _("1005.0");
    input7->guisection = _("Optional");

    input8 = G_define_standard_option(G_OPT_R_INPUT);
    input8->key = _("slope");
    input8->required = NO;
    input8->description = _("Name of the Slope layer ~[0-90]");
    input8->guisection = _("Optional");

    input9 = G_define_standard_option(G_OPT_R_INPUT);
    input9->key = _("aspect");
    input9->required = NO;
    input9->description = _("Name of the Aspect layer ~[0-360]");
    input9->guisection = _("Optional");

    input10 = G_define_option();
    input10->key = _("atmosphericemissivity");
    input10->type = TYPE_DOUBLE;
    input10->required = NO;
    input10->description = _("Value of the apparent atmospheric emissivity "
                             "(Bandara, 1998 used 0.845 for Sri Lanka)");
    input10->guisection = _("Optional");

    input11 = G_define_standard_option(G_OPT_R_INPUT);
    input11->key = _("airtemperature");
    input11->required = NO;
    input11->description =
        _("Name of the Air Temperature layer [Kelvin], use with -b");
    input11->guisection = _("Optional");

    input12 = G_define_standard_option(G_OPT_R_INPUT);
    input12->key = _("surfaceemissivity");
    input12->required = NO;
    input12->description =
        _("Name of the Surface Emissivity layer [-], use with -b");
    input12->guisection = _("Optional");

    input13 = G_define_standard_option(G_OPT_R_INPUT);
    input13->key = _("ndvi");
    input13->description = _("Name of the NDVI layer [-]");

    input14 = G_define_standard_option(G_OPT_R_INPUT);
    input14->key = _("diurnaletpotential");
    input14->required = NO;
    input14->description = _("Name of the ET Potential layer [mm/day]");
    input14->guisection = _("Optional");

    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the output Actual ET layer");

    output2 = G_define_standard_option(G_OPT_R_OUTPUT);
    output2->key = _("evapfr");
    output2->required = NO;
    output2->description = _("Name of the output evaporative fraction layer");
    output2->guisection = _("Optional");

    flag1 = G_define_flag();
    flag1->key = 'e';
    flag1->description =
        _("ET Potential Map as input (By-Pass creation of one)");

    flag2 = G_define_flag();
    flag2->key = 'd';
    flag2->description = _("Slope/Aspect correction");

    flag3 = G_define_flag();
    flag3->key = 'b';
    flag3->description = _("Net Radiation Bandara (1998), generic Longwave "
                           "calculation, need apparent atmospheric emissivity, "
                           "Air temperature and surface emissivity inputs");

    /********************/
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    tempk = input1->answer;
    albedo = input2->answer;
    ndvi = input13->answer;
    dem = input3->answer;
    if (flag1->answer)
        etpotd = input14->answer;
    else {
        lat = input4->answer;
        doy = input5->answer;
        tsw = input6->answer;
        roh_w = atof(input7->answer);
        if (flag2->answer) {
            slope = input8->answer;
            aspect = input9->answer;
        }
        if (input10->answer) {
            e_atm = atof(input10->answer);
        }
        if (flag3->answer) {
            tair = input11->answer;
            e0 = input12->answer;
        }
    }
    result1 = output1->answer;
    result2 = output2->answer;

    /***************************************************/
    infd_albedo = Rast_open_old(albedo, "");
    inrast_albedo = Rast_allocate_d_buf();
    infd_tempk = Rast_open_old(tempk, "");
    inrast_tempk = Rast_allocate_d_buf();
    infd_dem = Rast_open_old(dem, "");
    inrast_dem = Rast_allocate_d_buf();
    infd_ndvi = Rast_open_old(ndvi, "");
    inrast_ndvi = Rast_allocate_d_buf();

    if (flag1->answer) {
        infd_etpotd = Rast_open_old(etpotd, "");
        inrast_etpotd = Rast_allocate_d_buf();
    }
    else {
        infd_lat = Rast_open_old(lat, "");
        inrast_lat = Rast_allocate_d_buf();
        infd_doy = Rast_open_old(doy, "");
        inrast_doy = Rast_allocate_d_buf();
        infd_tsw = Rast_open_old(tsw, "");
        inrast_tsw = Rast_allocate_d_buf();
        if (flag2->answer) {
            infd_slope = Rast_open_old(slope, "");
            inrast_slope = Rast_allocate_d_buf();
            infd_aspect = Rast_open_old(aspect, "");
            inrast_aspect = Rast_allocate_d_buf();
        }
        if (flag3->answer) {
            infd_tair = Rast_open_old(tair, "");
            inrast_tair = Rast_allocate_d_buf();
            infd_e0 = Rast_open_old(e0, "");
            inrast_e0 = Rast_allocate_d_buf();
        }
    }
    /***************************************************/
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    outrast1 = Rast_allocate_d_buf();
    if (result2)
        outrast2 = Rast_allocate_d_buf();

    /* Create New raster files */
    outfd1 = Rast_open_new(result1, DCELL_TYPE);
    if (result2)
        outfd2 = Rast_open_new(result2, DCELL_TYPE);

    /* Process tempk min / max pixels for SENAY Evapfr */
    for (row = 0; row < nrows; row++) {
        DCELL d;
        DCELL d_albedo, d_tempk;
        DCELL d_dem, d_t0dem, d_ndvi;

        G_percent(row, nrows, 2);

        Rast_get_row(infd_albedo, inrast_albedo, row, DCELL_TYPE);
        Rast_get_row(infd_tempk, inrast_tempk, row, DCELL_TYPE);
        Rast_get_row(infd_dem, inrast_dem, row, DCELL_TYPE);
        Rast_get_row(infd_ndvi, inrast_ndvi, row, DCELL_TYPE);

        /*process the data */
        for (col = 0; col < ncols; col++) {
            d_albedo = (double)((DCELL *)inrast_albedo)[col];
            d_tempk = (double)((DCELL *)inrast_tempk)[col];
            d_dem = (double)((DCELL *)inrast_dem)[col];
            d_ndvi = (double)((DCELL *)inrast_ndvi)[col];
            if (Rast_is_d_null_value(&d_albedo) ||
                Rast_is_d_null_value(&d_tempk) ||
                Rast_is_d_null_value(&d_dem) || Rast_is_d_null_value(&d_ndvi)) {
                /* do nothing */
            }
            else {
                d_t0dem = d_tempk + 0.00649 * d_dem;
                if (d_t0dem < 0.0 || d_albedo < 0.001) {
                    /* do nothing */
                }
                else {
                    if (d_tempk < tempk_min && d_albedo < 0.1) {
                        t0dem_min = d_t0dem;
                        tempk_min = d_tempk;
                    }
                    else if (d_tempk > tempk_max && d_albedo > 0.3) {
                        t0dem_max = d_t0dem;
                        tempk_max = d_tempk;
                    }
                }
            }
        }
        G_message("tempk_min=%f\ntempk_max=%f\n", tempk_min, tempk_max);

        /**********************************************************/
        /* If ET Potential/Reference is an input compute ETa Senay*/
        if (flag1->answer) {
            /* Process pixels */
            for (row = 0; row < nrows; row++) {
                DCELL d;
                DCELL d_etpotd, d_evapfr;

                G_percent(row, nrows, 2);

                /*process the data */
                for (col = 0; col < ncols; col++) {
                    d_evapfr = evapfr_senay(tempk_max, tempk_min, d_tempk);
                    /*If water then no water stress */
                    if (d_albedo <= 0.1 && d_ndvi <= 0.0)
                        d_evapfr = 1.0;
                    /*some points are colder than selected low */
                    if (d_evapfr > 1.0)
                        d_evapfr = 1.0;
                    if (result2)
                        outrast2[col] = d_evapfr;
                    d = d_etpotd * d_evapfr;
                    outrast1[col] = d;
                }
                Rast_put_row(outfd1, outrast1, DCELL_TYPE);
                if (result2)
                    Rast_put_row(outfd2, outrast2, DCELL_TYPE);
            }
        }
        /*********************************************/
        /* If ET Potential/Reference is NOT an input */
        /* compute ETPOTD and ETa Senay*/
        else {
            /* Process pixels */
            for (row = 0; row < nrows; row++) {
                DCELL d;
                DCELL d_albedo, d_tempk, d_lat, d_doy, d_tsw, d_solar;
                DCELL d_rnetd, d_slope, d_aspect, d_tair;
                DCELL d_e0, d_ndvi, d_etpotd, d_evapfr;

                G_percent(row, nrows, 2);

                /* read input maps */
                Rast_get_row(infd_albedo, inrast_albedo, row, DCELL_TYPE);
                Rast_get_row(infd_tempk, inrast_tempk, row, DCELL_TYPE);
                Rast_get_row(infd_lat, inrast_lat, row, DCELL_TYPE);
                Rast_get_row(infd_doy, inrast_doy, row, DCELL_TYPE);
                Rast_get_row(infd_tsw, inrast_tsw, row, DCELL_TYPE);
                if (flag2->answer) {
                    Rast_get_row(infd_slope, inrast_slope, row, DCELL_TYPE);
                    Rast_get_row(infd_aspect, inrast_aspect, row, DCELL_TYPE);
                }
                if (flag3->answer) {
                    Rast_get_row(infd_tair, inrast_tair, row, DCELL_TYPE);
                    Rast_get_row(infd_e0, inrast_e0, row, DCELL_TYPE);
                }

                /*process the data */
                for (col = 0; col < ncols; col++) {
                    d_albedo = (double)((DCELL *)inrast_albedo)[col];
                    d_tempk = (double)((DCELL *)inrast_tempk)[col];
                    d_lat = (double)((DCELL *)inrast_lat)[col];
                    d_doy = (double)((DCELL *)inrast_doy)[col];
                    d_tsw = (double)((DCELL *)inrast_tsw)[col];
                    if (flag2->answer) {
                        d_slope = (double)((DCELL *)inrast_slope)[col];
                        d_aspect = (double)((DCELL *)inrast_aspect)[col];
                    }
                    if (flag3->answer) {
                        d_tair = (double)((DCELL *)inrast_tair)[col];
                        d_e0 = (double)((DCELL *)inrast_e0)[col];
                    }
                    if (Rast_is_d_null_value(&d_albedo) ||
                        Rast_is_d_null_value(&d_tempk) || d_tempk < 10.0 ||
                        Rast_is_d_null_value(&d_lat) ||
                        Rast_is_d_null_value(&d_doy) ||
                        Rast_is_d_null_value(&d_tsw) ||
                        Rast_is_d_null_value(&d_ndvi) ||
                        ((flag2->answer) && Rast_is_d_null_value(&d_slope)) ||
                        ((flag2->answer) && Rast_is_d_null_value(&d_aspect)) ||
                        ((flag3->answer) && Rast_is_d_null_value(&d_tair)) ||
                        ((flag3->answer) && Rast_is_d_null_value(&d_e0))) {
                        Rast_set_d_null_value(&outrast1[col], 1);
                        if (result2)
                            Rast_set_d_null_value(&outrast2[col], 1);
                    }
                    else {
                        if (flag2->answer) {
                            d_solar = solar_day_3d(d_lat, d_doy, d_tsw, d_slope,
                                                   d_aspect);
                        }
                        else {
                            d_solar = solar_day(d_lat, d_doy, d_tsw);
                        }
                        d_evapfr = evapfr_senay(tempk_max, tempk_min, d_tempk);
                        /*If water then no water stress */
                        if (d_albedo <= 0.1 && d_ndvi <= 0.0) {
                            d_evapfr = 1.0;
                        }
                        /*some points are colder than selected low */
                        if (d_evapfr > 1.0) {
                            d_evapfr = 1.0;
                        }
                        if (result2) {
                            outrast2[col] = d_evapfr;
                        }
                        if (flag3->answer) {
                            d_rnetd = r_net_day_bandara98(d_albedo, d_solar,
                                                          e_atm, d_e0, d_tair);
                        }
                        else {
                            d_rnetd = r_net_day(d_albedo, d_solar, d_tsw);
                        }
                        d_etpotd = et_pot_day(d_rnetd, d_tempk, roh_w);
                        d = d_etpotd * d_evapfr;
                        outrast1[col] = d;
                    }
                }
                Rast_put_row(outfd1, outrast1, DCELL_TYPE);
                if (result2)
                    Rast_put_row(outfd2, outrast2, DCELL_TYPE);
            }
        }
    }
    G_free(inrast_albedo);
    G_free(inrast_tempk);
    G_free(inrast_dem);
    G_free(inrast_lat);
    G_free(inrast_doy);
    G_free(inrast_tsw);
    Rast_close(infd_albedo);
    Rast_close(infd_tempk);
    Rast_close(infd_dem);
    Rast_close(infd_lat);
    Rast_close(infd_doy);
    Rast_close(infd_tsw);
    if (flag3->answer) {
        G_free(inrast_tair);
        Rast_close(infd_tair);
        G_free(inrast_e0);
        Rast_close(infd_e0);
    }
    G_free(outrast1);
    Rast_close(outfd1);
    if (result2) {
        G_free(outrast2);
        Rast_close(outfd2);

        /* Color table for evaporative fraction */
        Rast_init_colors(&colors);
        val1 = 0;
        val2 = 1;
        Rast_add_c_color_rule(&val1, 0, 0, 0, &val2, 255, 255, 255, &colors);
        Rast_short_history(result2, "raster", &history);
        Rast_command_history(&history);
        Rast_write_history(result2, &history);
    }

    /* Color table for evapotranspiration */
    Rast_init_colors(&colors);
    val1 = 0;
    val2 = 20;
    Rast_add_c_color_rule(&val1, 0, 0, 0, &val2, 255, 255, 255, &colors);
    Rast_short_history(result1, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result1, &history);

    exit(EXIT_SUCCESS);
}
