/* ***************************************************************************
 *
 * MODULE:       r.area
 * AUTHOR(S):    Jarek Jasiewicz <jarekj amu.edu.pl>
 * PURPOSE:      Module to calculate size of clumped areas
 * COPYRIGHT:    (C) 2010 by the GRASS Development Team
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
#include <grass/glocale.h>

int main(int argc, char *argv[])
{

    struct GModule *module;
    struct Option *input, *output, *par_treshold;
    struct Flag *flag_binary;

    struct Cell_head cellhd;
    struct Range range;
    struct History history;

    char *mapset;
    int nrows, ncols;
    int binary, treshold;
    int row, col;
    int infd, outfd;
    int *in_buf;
    int *out_buf;
    CELL c_min, c_max;
    int *ncells;
    int i;


    G_gisinit(argv[0]);

    /* Set description */
    module = G_define_module();
    module->keywords = _("raster");
    module->description = _("Calculates size of clumped areas.");

    input = G_define_standard_option(G_OPT_R_INPUT);
    input->description = _("Map created with r.clump");

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->description = _("Map with area size (in cells)");


    par_treshold = G_define_option();	/* input stream mask file - optional */
    par_treshold->key = "treshold";
    par_treshold->type = TYPE_INTEGER;
    par_treshold->answer = "0";
    par_treshold->description = _("Remove areas lower than (0 for none):");

    flag_binary = G_define_flag();
    flag_binary->key = 'b';
    flag_binary->description = _("Binary output");


    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);


    treshold = atof(par_treshold->answer);
    binary = (flag_binary->answer != 0);
    mapset = G_find_cell2(input->answer, "");

    if (mapset == NULL)
	G_fatal_error(_("Raster map <%s> not found"), input->answer);

    if ((infd = G_open_cell_old(input->answer, mapset)) < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), input->answer);

    if (G_get_cellhd(input->answer, mapset, &cellhd) < 0)
	G_fatal_error(_("Unable to read file header of <%s>"), input->answer);

    if (G_raster_map_type(input->answer, mapset) != CELL_TYPE)
	G_fatal_error(_("<%s> is not of type CELL, probably not crated with r.clump"),
		      input->answer);

    G_init_range(&range);
    G_read_range(input->answer, mapset, &range);
    G_get_range_min_max(&range, &c_min, &c_max);

    in_buf = G_allocate_raster_buf(CELL_TYPE);

    nrows = G_window_rows();
    ncols = G_window_cols();

    ncells = G_calloc(c_max + 1, sizeof(int));

    G_message(_("Reading..."));
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);

	if (G_get_raster_row(infd, in_buf, row, CELL_TYPE) < 0) {
	    G_close_cell(infd);
	    G_fatal_error(_("Cannot to read <%s> at row <%d>"),
			  output->answer, row);
	}

	for (col = 0; col < ncols; col++) {

	    if (!G_is_c_null_value(&in_buf[col])) {
		if (in_buf[col] < c_min || in_buf[col] > c_max)
		    G_fatal_error(_("Value at row %d, col %d out of range: %d"),
				  row, col, in_buf[col]);
		ncells[in_buf[col]]++;
	    }
	}
    }				/* end for row */

    if (treshold) {
	for (i = 1; i < c_max + 1; ++i)
	    if (ncells[i] < treshold)
		ncells[i] = -1;
    }

    if (binary) {
	for (i = 1; i < c_max + 1; ++i)
	    ncells[i] = ncells[i] < treshold ? -1 : 1;
    }


    if ((outfd = G_open_raster_new(output->answer, CELL_TYPE)) < 0)
	G_fatal_error(_("Unable to create raster map <%s>"), output->answer);

    out_buf = G_allocate_raster_buf(CELL_TYPE);

    G_message(_("Writing..."));
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);

	if (G_get_raster_row(infd, in_buf, row, CELL_TYPE) < 0) {
	    G_close_cell(infd);
	    G_fatal_error(_("Cannot to read <%s> at row <%d>"),
			  output->answer, row);
	}

	for (col = 0; col < ncols; col++) {
	    if (G_is_c_null_value(&in_buf[col]) || ncells[in_buf[col]] == -1)
		if (binary)
		    out_buf[col] = 0;
		else
		    G_set_c_null_value(&out_buf[col], 1);
	    else
		out_buf[col] = ncells[in_buf[col]];
	}

	if (G_put_raster_row(outfd, out_buf, CELL_TYPE) < 0)
	    G_fatal_error(_("Failed writing raster map <%s>"),
			  output->answer);
    }				/* end for row */

    G_free(ncells);
    G_free(in_buf);
    G_close_cell(infd);
    G_free(out_buf);
    G_close_cell(outfd);

    G_short_history(output->answer, "raster", &history);
    G_command_history(&history);
    G_write_history(output->answer, &history);

    G_message(_("Done!"));
    exit(EXIT_SUCCESS);
}
