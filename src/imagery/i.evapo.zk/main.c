/*****************************************************************************
 *
 * MODULE:       i.evapo.pt
 * AUTHOR:       Yann Chemin yann.chemin@gmail.com
 *
 * PURPOSE:      To estimate the daily evapotranspiration by means
 *               of Zhang and Kimberley.
 *
 * COPYRIGHT:    (C) 2007-2012 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               Licence (>=2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 ***************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

double zk_daily_et(double biome_type, double ndvi, double tday, double sh,
                   double patm, double Rn, double G, double dem);

int main(int argc, char *argv[])
{
    /* buffer for input-output rasters */
    void *inrast_biomt, *inrast_ndvi, *inrast_tday, *inrast_sh;
    void *inrast_patm, *inrast_rnetd, *inrast_g0, *inrast_dem;
    DCELL *outrast;

    /* pointers to input-output raster files */
    int infd_biomt, infd_ndvi, infd_tday, infd_sh;
    int infd_patm, infd_rnetd, infd_g0, infd_dem;
    int outfd;

    /* names of input-output raster files */
    char *biomt, *ndvi, *tday, *sh;
    char *patm, *rnetd, *g0, *dem;
    char *eta;

    /* input-output cell values */
    DCELL d_biomt, d_ndvi, d_tday, d_sh;
    DCELL d_patm, d_rnetd, d_g0, d_dem;
    DCELL d_daily_et;

    /* region informations and handler */
    struct Cell_head cellhd;
    int nrows, ncols;
    int row, col;

    /* parser stuctures definition */
    struct GModule *module;
    struct Option *input_biomt, *input_ndvi, *input_tday, *input_sh;
    struct Option *input_patm, *input_rnetd, *input_g0, *input_dem;
    struct Option *output;
    struct Flag *zero;
    struct Colors color;
    struct History history;

    /* Initialize the GIS calls */
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("evapotranspiration"));
    module->description =
        _("Computes global evapotranspiration calculation after Zhang, "
          "Kimball, Nemani and Running formulation, 2010.");

    /* Define different options */

    input_biomt = G_define_standard_option(G_OPT_R_INPUT);
    input_biomt->key = "biome_type";
    input_biomt->description =
        _("Name of input IGBP biome type raster map [-]");

    input_ndvi = G_define_standard_option(G_OPT_R_INPUT);
    input_ndvi->key = "ndvi";
    input_ndvi->description = _(
        "Name of input Normalized Difference Vegetation Index raster map [-]");

    input_tday = G_define_standard_option(G_OPT_R_INPUT);
    input_tday->key = "airtemperature";
    input_tday->description = _("Name of input air temperature raster map [C]");

    input_sh = G_define_standard_option(G_OPT_R_INPUT);
    input_sh->key = "specifichumidity";
    input_sh->description = _("Name of input specific humidity raster map [-]");

    input_patm = G_define_standard_option(G_OPT_R_INPUT);
    input_patm->key = "atmosphericpressure";
    input_patm->description =
        _("Name of input atmospheric pressure raster map [Pa]");

    input_rnetd = G_define_standard_option(G_OPT_R_INPUT);
    input_rnetd->key = "netradiation";
    input_rnetd->description =
        _("Name of input net radiation raster map [MJ/m2/d]");

    input_g0 = G_define_standard_option(G_OPT_R_INPUT);
    input_g0->key = "soilheatflux";
    input_g0->description =
        _("Name of input soil heat flux raster map [MJ/m2/d]");

    input_dem = G_define_standard_option(G_OPT_R_INPUT);
    input_dem->key = "elevation";
    input_dem->description = _("Name of input elevation raster map [m]");

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->description =
        _("Name of output evapotranspiration raster map [mm/d]");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* get entered parameters */
    biomt = input_biomt->answer;
    ndvi = input_ndvi->answer;
    tday = input_tday->answer;
    sh = input_sh->answer;
    patm = input_patm->answer;
    rnetd = input_rnetd->answer;
    g0 = input_g0->answer;
    dem = input_dem->answer;

    eta = output->answer;

    /* open pointers to input raster files */
    infd_biomt = Rast_open_old(biomt, "");
    infd_ndvi = Rast_open_old(ndvi, "");
    infd_tday = Rast_open_old(tday, "");
    infd_sh = Rast_open_old(sh, "");
    infd_patm = Rast_open_old(patm, "");
    infd_rnetd = Rast_open_old(rnetd, "");
    infd_g0 = Rast_open_old(g0, "");
    infd_dem = Rast_open_old(dem, "");

    /* read headers of raster files */
    Rast_get_cellhd(biomt, "", &cellhd);
    Rast_get_cellhd(ndvi, "", &cellhd);
    Rast_get_cellhd(tday, "", &cellhd);
    Rast_get_cellhd(sh, "", &cellhd);
    Rast_get_cellhd(patm, "", &cellhd);
    Rast_get_cellhd(rnetd, "", &cellhd);
    Rast_get_cellhd(g0, "", &cellhd);
    Rast_get_cellhd(dem, "", &cellhd);

    /* Allocate input buffer */
    inrast_biomt = Rast_allocate_d_buf();
    inrast_ndvi = Rast_allocate_d_buf();
    inrast_tday = Rast_allocate_d_buf();
    inrast_sh = Rast_allocate_d_buf();
    inrast_patm = Rast_allocate_d_buf();
    inrast_rnetd = Rast_allocate_d_buf();
    inrast_g0 = Rast_allocate_d_buf();
    inrast_dem = Rast_allocate_d_buf();

    /* get rows and columns number of the current region */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* allocate output buffer */
    outrast = Rast_allocate_d_buf();

    /* open pointers to output raster files */
    outfd = Rast_open_new(eta, DCELL_TYPE);

    /* start the loop through cells */
    for (row = 0; row < nrows; row++) {

        G_percent(row, nrows, 2);
        /* read input raster row into line buffer */
        Rast_get_d_row(infd_biomt, inrast_biomt, row);
        Rast_get_d_row(infd_ndvi, inrast_ndvi, row);
        Rast_get_d_row(infd_tday, inrast_tday, row);
        Rast_get_d_row(infd_sh, inrast_sh, row);
        Rast_get_d_row(infd_patm, inrast_patm, row);
        Rast_get_d_row(infd_rnetd, inrast_rnetd, row);
        Rast_get_d_row(infd_g0, inrast_g0, row);
        Rast_get_d_row(infd_dem, inrast_dem, row);

        for (col = 0; col < ncols; col++) {
            /* read current cell from line buffer */
            d_biomt = ((DCELL *)inrast_biomt)[col];
            d_ndvi = ((DCELL *)inrast_ndvi)[col];
            d_tday = ((DCELL *)inrast_tday)[col];
            d_sh = ((DCELL *)inrast_sh)[col];
            d_patm = ((DCELL *)inrast_patm)[col];
            d_rnetd = ((DCELL *)inrast_rnetd)[col];
            d_g0 = ((DCELL *)inrast_g0)[col];
            d_dem = ((DCELL *)inrast_dem)[col];

            /*Calculate ET */
            if (Rast_is_d_null_value(&d_biomt) ||
                Rast_is_d_null_value(&d_ndvi) ||
                Rast_is_d_null_value(&d_tday) || Rast_is_d_null_value(&d_sh) ||
                Rast_is_d_null_value(&d_patm) ||
                Rast_is_d_null_value(&d_rnetd) || Rast_is_d_null_value(&d_g0) ||
                Rast_is_d_null_value(&d_dem)) {
                Rast_set_d_null_value(&outrast[col], 1);
            }
            else {
                if (d_rnetd - d_g0 < 0)
                    d_g0 = d_rnetd * 0.1;
                d_daily_et = zk_daily_et(d_biomt, d_ndvi, d_tday, d_sh, d_patm,
                                         d_rnetd, d_g0, d_dem);
                //            G_message("%f %f %f %f %f %f %f %f
                //            %f",d_biomt,d_ndvi,d_tday,d_sh,d_patm,d_rnetd,d_g0,d_dem,d_daily_et);
                if (d_daily_et == -28768)
                    Rast_set_d_null_value(&outrast[col], 1);
                /* write calculated ETP to output line buffer */
                else
                    outrast[col] = d_daily_et;
            }
        }

        /* write output line buffer to output raster file */
        Rast_put_d_row(outfd, outrast);
    }
    /* free buffers and close input maps */

    G_free(inrast_biomt);
    G_free(inrast_ndvi);
    G_free(inrast_tday);
    G_free(inrast_sh);
    G_free(inrast_patm);
    G_free(inrast_rnetd);
    G_free(inrast_g0);
    G_free(inrast_dem);
    Rast_close(infd_biomt);
    Rast_close(infd_ndvi);
    Rast_close(infd_tday);
    Rast_close(infd_sh);
    Rast_close(infd_patm);
    Rast_close(infd_rnetd);
    Rast_close(infd_g0);
    Rast_close(infd_dem);

    /* generate color table between -20 and 20 */
    Rast_make_rainbow_colors(&color, -20, 20);
    Rast_write_colors(eta, G_mapset(), &color);

    Rast_short_history(eta, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(eta, &history);

    /* free buffers and close output map */
    G_free(outrast);
    Rast_close(outfd);

    return (EXIT_SUCCESS);
}
