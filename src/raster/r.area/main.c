/* ***************************************************************************
 *
 * MODULE:       r.area
 * AUTHOR(S):    Jarek Jasiewicz <jarekj amu.edu.pl>
 * PURPOSE:      Calculate area of clumped areas. Remove areas smaller than
 *               given threshold.
 *
 * COPYRIGHT:    (C) 1999-2010 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 ****************************************************************************
 */

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

int main(int argc, char *argv[])
{

    struct GModule *module;
    struct Option *input, *output, *lesser, *greater;
    struct Flag *flag_binary;

    struct Cell_head cellhd;
    struct Range range;
    struct History history;

    char *mapset;
    int nrows, ncols;
    int binary, les, grt, gt;
    int row, col;
    int infd, outfd;
    CELL *in_buf;
    CELL *out_buf;
    CELL c_min, c_max;
    int *ncells;
    int i;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("statistics"));
    G_add_keyword(_("area"));
    module->description = _("Calculates area of clumped areas and remove areas "
                            "smaller or greater than given threshold.");

    input = G_define_standard_option(G_OPT_R_INPUT);
    input->description =
        _("Name of cell category map, e.g., maps created with r.clump");

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->description = _("Name of output raster with categories "
                            "representing area size (in cells)");

    lesser = G_define_option(); /* input stream mask file - optional */
    lesser->key = "lesser";
    lesser->type = TYPE_INTEGER;
    lesser->answer = "0";
    lesser->description = _("Remove areas with number of cells lower than "
                            "given value (0 for none):");

    greater = G_define_option(); /* input stream mask file - optional */
    greater->key = "greater";
    greater->type = TYPE_INTEGER;
    greater->answer = "-1";
    greater->description = _("Remove areas with number of cells greater than "
                             "given value (-1 for none):");

    flag_binary = G_define_flag();
    flag_binary->key = 'b';
    flag_binary->description = _("Binary output");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    binary = (flag_binary->answer != 0);
    mapset = (char *)G_find_raster2(input->answer, "");

    if (mapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), input->answer);

    infd = Rast_open_old(input->answer, mapset);
    Rast_get_cellhd(input->answer, mapset, &cellhd);

    les = atof(lesser->answer);
    grt = atof(greater->answer);
    gt = grt > 0 ? grt : cellhd.rows * cellhd.cols;

    if (Rast_map_type(input->answer, mapset) != CELL_TYPE)
        G_fatal_error(
            _("<%s> is not of type CELL, probably not crated with r.clump"),
            input->answer);

    Rast_init_range(&range);
    Rast_read_range(input->answer, mapset, &range);
    Rast_get_range_min_max(&range, &c_min, &c_max);

    in_buf = Rast_allocate_c_buf();

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    ncells = G_calloc(c_max + 1, sizeof(int));

    G_message(_("Reading..."));
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);
        Rast_get_row(infd, in_buf, row, CELL_TYPE);

        for (col = 0; col < ncols; col++) {
            if (!Rast_is_c_null_value(&in_buf[col])) {
                if (in_buf[col] < c_min || in_buf[col] > c_max)
                    G_fatal_error(_("Value at row %d, col %d out of range: %d"),
                                  row, col, in_buf[col]);
                ncells[in_buf[col]]++;
            }
        }
    } /* end for row */

    if (les != 0 || grt != -1) {
        for (i = 1; i < c_max + 1; ++i)
            if (ncells[i] < les || ncells[i] > gt)
                ncells[i] = -1;
    }

    if (binary) {
        for (i = 1; i < c_max + 1; ++i)
            ncells[i] = ncells[i] < les ? -1 : 1;
    }

    outfd = Rast_open_new(output->answer, CELL_TYPE);
    out_buf = Rast_allocate_c_buf();

    G_message(_("Writing..."));
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        Rast_get_row(infd, in_buf, row, CELL_TYPE);

        for (col = 0; col < ncols; col++) {
            if (Rast_is_c_null_value(&in_buf[col]) || ncells[in_buf[col]] == -1)
                if (binary)
                    out_buf[col] = 0;
                else
                    Rast_set_c_null_value(&out_buf[col], 1);
            else
                out_buf[col] = ncells[in_buf[col]];
        }
        Rast_put_row(outfd, out_buf, CELL_TYPE);
    } /* end for row */

    G_free(ncells);
    G_free(in_buf);
    Rast_close(infd);
    G_free(out_buf);
    Rast_close(outfd);

    Rast_short_history(output->answer, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(output->answer, &history);

    G_message(_("Done!"));
    exit(EXIT_SUCCESS);
}
