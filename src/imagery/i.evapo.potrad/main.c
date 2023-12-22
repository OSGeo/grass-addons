/****************************************************************************
 *
 * MODULE:       i.evapo.potrad
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Creates a map of potential evapotranspiration following
 *               the condition that all net radiation becomes ET
 *               (thus it can be called a "radiative ET pot")
 *
 * COPYRIGHT:    (C) 2002-2010 by the GRASS Development Team
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

int main(int argc, char *argv[])
{
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *input1, *input2, *input3, *input4;
    struct Option *input5, *input6, *input7, *input8;
    struct Option *input9, *input10, *input11;
    struct Option *output1, *output2;
    struct Flag *flag1, *flag2, *flag3;
    struct History history;  /*metadata */
    struct Colors colors;    /*Color rules */
    CELL val1, val2;         /*Color ranges */
    char *result1, *result2; /*output raster name */

    /*File Descriptors */
    int infd_albedo, infd_tempk, infd_lat, infd_doy, infd_tsw;
    int infd_slope = 0, infd_aspect = 0;
    int infd_tair = 0, infd_e0 = 0;
    int outfd1, outfd2;
    char *albedo, *tempk, *lat, *doy, *tsw, *slope, *aspect, *tair, *e0;
    double roh_w, e_atm;

    void *inrast_albedo, *inrast_tempk, *inrast_lat;
    void *inrast_doy, *inrast_tsw;
    void *inrast_slope, *inrast_aspect;
    void *inrast_tair, *inrast_e0;

    DCELL *outrast1, *outrast2;

    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("Potential ET"));
    G_add_keyword(_("evapotranspiration"));
    module->description = _("Potential evapotranspiration, radiative method "
                            "after Bastiaanssen (1995)");

    /* Define the different options */
    input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("albedo");
    input1->description = _("Name of the Albedo layer [0.0-1.0]");

    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = _("temperature");
    input2->description = _("Name of the temperature layer [Degree Kelvin]");

    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = _("latitude");
    input3->description = _("Name of the degree latitude layer [dd.ddd]");

    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = _("dayofyear");
    input4->description = _("Name of the Day of Year layer [0.0-366.0]");

    input5 = G_define_standard_option(G_OPT_R_INPUT);
    input5->key = _("transmissivitysingleway");
    input5->description = _("Name of the single-way transmissivity layer "
                            "[0.05-1.0], defaults to 1.0 if no input file");

    input6 = G_define_option();
    input6->key = _("waterdensity");
    input6->type = TYPE_DOUBLE;
    input6->required = YES;
    input6->gisprompt = _("value, parameter");
    input6->description = _("Value of the density of fresh water ~[1000-1020]");
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
    input9->key = _("atmosphericemissivity");
    input9->type = TYPE_DOUBLE;
    input9->required = NO;
    input9->gisprompt = _("value, parameter");
    input9->description = _("Value of the apparent atmospheric emissivity "
                            "(Bandara, 1998 used 0.845 for Sri Lanka)");
    input9->answer = _("0.845");
    input9->guisection = _("Optional");

    input10 = G_define_standard_option(G_OPT_R_INPUT);
    input10->key = _("airtemperature");
    input10->required = NO;
    input10->description =
        _("Name of the Air Temperature layer [Kelvin], use with -b");
    input10->guisection = _("Optional");

    input11 = G_define_standard_option(G_OPT_R_INPUT);
    input11->key = _("surfaceemissivity");
    input11->required = NO;
    input11->description =
        _("Name of the Surface Emissivity layer [-], use with -b");
    input11->guisection = _("Optional");

    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("OUTPUT: Name of the Potential ET layer");

    output2 = G_define_standard_option(G_OPT_R_OUTPUT);
    output2->key = _("rnetd");
    output2->required = NO;
    output2->description = _("OUTPUT: Name of the Diurnal Net Radiation layer");
    output2->guisection = _("Optional");

    flag1 = G_define_flag();
    flag1->key = 'r';
    flag1->description = _("Output Diurnal Net Radiation (for i.eb.eta)");

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
    infd_albedo = Rast_open_old(albedo, "");
    inrast_albedo = Rast_allocate_d_buf();

    infd_tempk = Rast_open_old(tempk, "");
    inrast_tempk = Rast_allocate_d_buf();

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

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    outrast1 = Rast_allocate_d_buf();
    if (result2)
        outrast2 = Rast_allocate_d_buf();

    /* Create New raster files */
    outfd1 = Rast_open_new(result1, DCELL_TYPE);
    if (result2)
        outfd2 = Rast_open_new(result2, DCELL_TYPE);

    /* Process pixels */
    for (row = 0; row < nrows; row++) {
        DCELL d;
        DCELL d_albedo, d_tempk;
        DCELL d_lat, d_doy, d_tsw;
        DCELL d_solar, d_rnetd;
        DCELL d_slope, d_aspect;
        DCELL d_tair = 0, d_e0 = 0;

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
                Rast_is_d_null_value(&d_tempk) || (d_tempk < 10.0) ||
                Rast_is_d_null_value(&d_lat) || Rast_is_d_null_value(&d_doy) ||
                Rast_is_d_null_value(&d_tsw) ||
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
                    d_solar =
                        solar_day_3d(d_lat, d_doy, d_tsw, d_slope, d_aspect);
                }
                else {
                    d_solar = solar_day(d_lat, d_doy, d_tsw);
                }
                if (flag3->answer) {
                    d_rnetd = r_net_day_bandara98(d_albedo, d_solar, e_atm,
                                                  d_e0, d_tair);
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
        Rast_put_row(outfd1, outrast1, DCELL_TYPE);
        if (result2)
            Rast_put_row(outfd2, outrast2, DCELL_TYPE);
    }
    G_free(inrast_albedo);
    G_free(inrast_tempk);
    G_free(inrast_lat);
    G_free(inrast_doy);
    G_free(inrast_tsw);
    Rast_close(infd_albedo);
    Rast_close(infd_tempk);
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

        /* Color rule */
        Rast_init_colors(&colors);
        val1 = 0;
        val2 = 1000;
        Rast_add_c_color_rule(&val1, 0, 0, 0, &val2, 255, 255, 255, &colors);

        /* Metadata */
        Rast_short_history(result2, "raster", &history);
        Rast_command_history(&history);
        Rast_write_history(result2, &history);
    }

    /* Color rule */
    Rast_init_colors(&colors);
    val1 = 0;
    val2 = 20;
    Rast_add_c_color_rule(&val1, 0, 0, 0, &val2, 255, 255, 255, &colors);

    /* Metadata */
    Rast_short_history(result1, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result1, &history);

    exit(EXIT_SUCCESS);
}
