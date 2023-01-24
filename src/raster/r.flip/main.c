/****************************************************************************
 *
 * MODULE:       r.flip
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Flips an image North-South, East-West (-w) or both (-b).
 *
 * COPYRIGHT:    (C) 2012 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with
 *               GRASS for details.
 *
 * Remark:
 *               Initial need for TRMM import
 *
 * Changelog:
 *               Moved from i.flip to r.flip
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

int main(int argc, char *argv[])
{
    int nrows, ncols;
    int row;
    struct GModule *module;
    struct Option *input, *output;
    struct History history;     /*Metadata */
    struct Colors colors;       /*Color rules */
    struct Flag *flag1, *flag2; /*Flags */

    char *in, *out; /*in/out raster names */
    int infd, outfd;
    DCELL *inrast, *outrast;
    RASTER_MAP_TYPE data_type_input;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("flip"));
    module->label = _("Flips an image.");
    module->description = _("Flips an image.");

    /* Define the different options */
    input = G_define_standard_option(G_OPT_R_INPUT);
    output = G_define_standard_option(G_OPT_R_OUTPUT);

    /* define the different flags */
    flag1 = G_define_flag();
    flag1->key = 'w';
    flag1->description = _("East-West flip");

    flag2 = G_define_flag();
    flag2->key = 'b';
    flag2->description = _("Both N-S and E-W flip");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    if (flag1->answer && flag2->answer)
        G_fatal_error(_("-w and -b are mutually exclusive"));

    in = input->answer;
    out = output->answer;

    /* Open input raster file */
    infd = Rast_open_old(in, "");
    data_type_input = Rast_get_map_type(infd);
    inrast = Rast_allocate_d_buf();

    /* Create New raster file */
    outfd = Rast_open_new(out, data_type_input);
    outrast = (flag1->answer || flag2->answer) ? Rast_allocate_d_buf() : inrast;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    for (row = 0; row < nrows; row++) {
        int inrow = flag1->answer ? row : nrows - 1 - row;
        G_percent(row, nrows, 2);
        /* read input map */
        Rast_get_d_row(infd, inrast, inrow);

        if (flag1->answer || flag2->answer) {
            int col;
            for (col = 0; col < ncols; col++)
                outrast[ncols - 1 - col] = inrast[col];
        }

        Rast_put_d_row(outfd, outrast);
    }

    Rast_close(infd);
    Rast_close(outfd);

    if (Rast_read_colors(in, "", &colors) > 0)
        Rast_write_colors(out, G_mapset(), &colors);

    Rast_short_history(out, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(out, &history);

    return EXIT_SUCCESS;
}
