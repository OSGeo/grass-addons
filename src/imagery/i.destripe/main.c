/****************************************************************************
 *
 * MODULE:       i.destripe
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Destripe a regularly striped image using Fourier
 *               Row based, works with stripes about up-down direction
 *
 * COPYRIGHT:    (C) 2014 by the GRASS Development Team
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

void fourier(DCELL *t_sim, DCELL *t_obs, int length, int harmonic_number);

int main(int argc, char *argv[])
{
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *input1, *input2;
    struct Option *output;
    struct History history; /*metadata */
    struct Colors colors;
    char *result; /*output raster name */
    int infd, outfd, ha;
    char *in;
    DCELL *inrast, *outrast;
    CELL val1, val2;

    /************************************/
    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("destripe"));
    G_add_keyword("Fourier");
    module->description =
        _("Destripes regularly, about vertical, striped image using Fourier.");

    /* Define the different options */
    input1 = G_define_standard_option(G_OPT_R_INPUT);

    input2 = G_define_option();
    input2->key = "harmonic";
    input2->type = TYPE_INTEGER;
    input2->required = YES;
    input2->description =
        _("Number of harmonics to use (less is smoother output)");
    input2->answer = "8";

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    /********************/
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    in = input1->answer;
    ha = atoi(input2->answer);
    result = output->answer;
    /***************************************************/
    infd = Rast_open_old(in, "");
    inrast = Rast_allocate_d_buf();

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    outrast = Rast_allocate_d_buf();

    /* Create New raster files */
    outfd = Rast_open_new(result, DCELL_TYPE);

    /* Process each row */
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);
        Rast_get_d_row(infd, inrast, row);
        fourier(outrast, inrast, ncols, ha);
        Rast_put_d_row(outfd, outrast);
    }

    /* Color table for biomass */
    Rast_init_colors(&colors);
    val1 = 0;
    val2 = 1;
    Rast_add_c_color_rule(&val1, 0, 0, 0, &val2, 255, 255, 255, &colors);
    G_free(inrast);
    G_free(outrast);
    Rast_close(infd);
    Rast_close(outfd);
    Rast_short_history(result, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result, &history);

    exit(EXIT_SUCCESS);
}
