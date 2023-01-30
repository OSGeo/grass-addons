/****************************************************************************
 *
 * MODULE:       i.gravity
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the Bouguer anomaly of a gravity dataset
 *
 * COPYRIGHT:    (C) 2002-2013 by the GRASS Development Team
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

/* International Gravity Formula (For Latitude correction)*/
double g_lambda(double lambda);
/* Eotvos Correction*/
double delta_g_eotvos(double alpha, double lambda, double v);
/* Free air Correction*/
double free_air(h);
/* Bouguer Correction*/
double delta_g_bouguer(double rho, double h);
/* bouguer anomaly */
double bouguer_anomaly(double g_obs, double freeair_corr, double bouguer_corr,
                       double terrain_corr, double latitude_corr,
                       double eotvos_corr);

int main(int argc, char *argv[])
{
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *in0, *in1, *in2, *in3, *in4, *in5, *in6, *output1;
    struct History history; /*metadata */
    char *result1;          /*output raster name */
    int infd_g_obs, infd_elevation, infd_latitude;
    int infd_flight_azimuth, infd_flight_velocity;
    int infd_rho, infd_terrain_corr;
    int outfd1;
    char *g_obs, *elevation, *latitude;
    char *flight_azimuth, *flight_velocity, *rho, *terrain_corr;
    void *inrast_g_obs, *inrast_elevation, *inrast_latitude;
    void *inrast_flight_azimuth, *inrast_flight_velocity;
    void *inrast_rho, *inrast_terrain_corr;

    DCELL *outrast1;
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("gravity"));
    G_add_keyword(_("Bouguer"));
    G_add_keyword(_("Eotvos"));
    G_add_keyword(_("Free Air"));
    module->description = _("Bouguer gravity anomaly computation (full slab).");

    /* Define the different options */
    in0 = G_define_standard_option(G_OPT_R_INPUT);
    in0->key = "gravity_obs";
    in0->description = _("Name of the observed gravity map [mGal]");
    in0->answer = "gravity_obs";

    in1 = G_define_standard_option(G_OPT_R_INPUT);
    in1->key = "elevation";
    in1->description = _("Name of the elevation map [m]");
    in1->answer = "dem";

    in2 = G_define_standard_option(G_OPT_R_INPUT);
    in2->key = "latitude";
    in2->description = _("Name of the latitude map [dd.ddd]");
    in2->answer = "lat";

    in3 = G_define_standard_option(G_OPT_R_INPUT);
    in3->key = "flight_azimuth";
    in3->description =
        _("Name of the flight azimuth map (clockwise from North) [dd.ddd]");
    in3->answer = "flight_azimuth";

    in4 = G_define_standard_option(G_OPT_R_INPUT);
    in4->key = "flight_velocity";
    in4->description = _("Name of the flight velocity [kph]");
    in4->answer = "flight_velocity";

    in5 = G_define_standard_option(G_OPT_R_INPUT);
    in5->key = "slab_density";
    in5->description = _("Name of the slab density [kg/m3]");
    in5->answer = "slab_density";

    in6 = G_define_standard_option(G_OPT_R_INPUT);
    in6->key = "terrain_corr";
    in6->description = _("Name of the terrain correction map []");
    in6->answer = "terrain_corr";

    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the Bouguer gravity anomaly [mGal]");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    g_obs = in0->answer;
    elevation = in1->answer;
    latitude = in2->answer;
    flight_azimuth = in3->answer;
    flight_velocity = in4->answer;
    rho = in5->answer;
    terrain_corr = in6->answer;
    result1 = output1->answer;

    infd_g_obs = Rast_open_old(g_obs, "");
    inrast_g_obs = Rast_allocate_d_buf();

    infd_elevation = Rast_open_old(elevation, "");
    inrast_elevation = Rast_allocate_d_buf();

    infd_latitude = Rast_open_old(latitude, "");
    inrast_latitude = Rast_allocate_d_buf();

    infd_flight_azimuth = Rast_open_old(flight_azimuth, "");
    inrast_flight_azimuth = Rast_allocate_d_buf();

    infd_flight_velocity = Rast_open_old(flight_velocity, "");
    inrast_flight_velocity = Rast_allocate_d_buf();

    infd_rho = Rast_open_old(rho, "");
    inrast_rho = Rast_allocate_d_buf();

    infd_terrain_corr = Rast_open_old(terrain_corr, "");
    inrast_terrain_corr = Rast_allocate_d_buf();

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    outrast1 = Rast_allocate_d_buf();

    outfd1 = Rast_open_new(result1, DCELL_TYPE);

    /* Process pixels */
    for (row = 0; row < nrows; row++) {
        DCELL d;
        DCELL d_g_obs;
        DCELL d_elevation;
        DCELL d_latitude;
        DCELL d_flight_azimuth;
        DCELL d_flight_velocity;
        DCELL d_rho;
        DCELL d_terrain_corr;
        DCELL latitude_corr;
        DCELL eotvos_corr;
        DCELL freeair_corr;
        DCELL bouguer_corr;
        G_percent(row, nrows, 2);

        /* read in maps */
        Rast_get_d_row(infd_g_obs, inrast_g_obs, row);
        Rast_get_d_row(infd_elevation, inrast_elevation, row);
        Rast_get_d_row(infd_latitude, inrast_latitude, row);
        Rast_get_d_row(infd_flight_azimuth, inrast_flight_azimuth, row);
        Rast_get_d_row(infd_flight_velocity, inrast_flight_velocity, row);
        Rast_get_d_row(infd_rho, inrast_rho, row);
        Rast_get_d_row(infd_terrain_corr, inrast_terrain_corr, row);

        /*process the data */
        for (col = 0; col < ncols; col++) {
            d_g_obs = ((DCELL *)inrast_g_obs)[col];
            d_elevation = ((DCELL *)inrast_elevation)[col];
            d_latitude = ((DCELL *)inrast_latitude)[col];
            d_flight_azimuth = ((DCELL *)inrast_flight_azimuth)[col];
            d_flight_velocity = ((DCELL *)inrast_flight_velocity)[col];
            d_rho = ((DCELL *)inrast_rho)[col];
            d_terrain_corr = ((DCELL *)inrast_terrain_corr)[col];
            if (Rast_is_d_null_value(&d_g_obs) ||
                Rast_is_d_null_value(&d_elevation) ||
                Rast_is_d_null_value(&d_latitude) ||
                Rast_is_d_null_value(&d_flight_azimuth) ||
                Rast_is_d_null_value(&d_flight_velocity) ||
                Rast_is_d_null_value(&d_rho) ||
                Rast_is_d_null_value(&d_terrain_corr))
                Rast_set_d_null_value(&outrast1[col], 1);
            else {
                /* International Gravity Formula (For Latitude correction)*/
                latitude_corr = g_lambda(d_latitude);
                /* Eotvos Correction*/
                eotvos_corr = delta_g_eotvos(d_flight_azimuth, d_latitude,
                                             d_flight_velocity);
                /* Free air Correction*/
                freeair_corr = free_air(d_elevation);
                /* Bouguer Correction*/
                bouguer_corr = delta_g_bouguer(d_rho, d_elevation);
                /* bouguer anomaly */
                d = bouguer_anomaly(d_g_obs, freeair_corr, bouguer_corr,
                                    d_terrain_corr, latitude_corr, eotvos_corr);
                outrast1[col] = d;
            }
        }
        Rast_put_d_row(outfd1, outrast1);
    }
    G_free(inrast_elevation);
    G_free(inrast_latitude);
    G_free(inrast_flight_azimuth);
    G_free(inrast_flight_velocity);
    G_free(inrast_rho);
    G_free(inrast_terrain_corr);
    Rast_close(infd_elevation);
    Rast_close(infd_latitude);
    Rast_close(infd_flight_azimuth);
    Rast_close(infd_flight_velocity);
    Rast_close(infd_rho);
    Rast_close(infd_terrain_corr);
    G_free(outrast1);
    Rast_close(outfd1);
    Rast_short_history(result1, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result1, &history);
    exit(EXIT_SUCCESS);
}
