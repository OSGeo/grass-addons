
/****************************************************************************
 *
 * MODULE:       r.clump2
 *
 * AUTHOR(S):    Markus Metz
 *
 * PURPOSE:      Recategorizes data in a raster map layer by grouping cells
 *		 that form physically discrete areas into unique categories.
 *
 * COPYRIGHT:    (C) 2009 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 ***************************************************************************/

#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <math.h>
#include "local_proto.h"
#include <grass/glocale.h>

CELL *clump_id;
long pqsize;

int main(int argc, char *argv[])
{
    struct Colors colr;
    struct Range range;
    CELL min, max;
    int in_fd, out_fd;
    char title[512];
    char name[GNAME_MAX];
    struct GModule *module;
    struct Option *opt_in;
    struct Option *opt_out;
    struct Option *opt_title;
    struct Flag *sides_flag;
    CELL clump_no, *out_buf;
    struct Cell_head window, cellhd;
    int nrows, ncols, r, c;
    long ncells, counter;
    void *in_ptr, *in_buf;
    int map_type, in_size;
    FLAG *inlist;
    int ramseg;
    long index, index_nbr;
    int sides, s, r_nbr, c_nbr;
    int nextdr[8] = { 1, -1, 0, 0, -1, 1, 1, -1 };
    int nextdc[8] = { 0, 0, -1, 1, 1, -1, 1, -1 };

    G_gisinit(argv[0]);

    /* Define the different options */

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("statistics"));
    G_add_keyword(_("reclass"));
    module->description =
	_("Recategorizes data in a raster map by grouping cells "
	  "that form physically discrete areas into unique categories.");

    opt_in = G_define_standard_option(G_OPT_R_INPUT);

    opt_out = G_define_standard_option(G_OPT_R_OUTPUT);

    opt_title = G_define_option();
    opt_title->key = "title";
    opt_title->type = TYPE_STRING;
    opt_title->required = NO;
    opt_title->description = _("Title");

    sides_flag = G_define_flag();
    sides_flag->key = 'e';
    sides_flag->description = _("Ignore diagonal cells");


    /* parse options */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    in_fd = Rast_open_old(opt_in->answer, "");
    if (in_fd < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), opt_in->answer);

    out_fd = Rast_open_c_new(opt_out->answer);
    if (out_fd < 0)
	G_fatal_error(_("Unable to create raster map <%s>"), opt_out->answer);

    if (sides_flag->answer)
	sides = 4;
    else
	sides = 8;

    /* some checks */
    G_get_set_window(&window);
    Rast_get_cellhd(opt_in->answer, "", &cellhd);

    if (fabs(window.ew_res - cellhd.ew_res) > GRASS_EPSILON ||
	fabs(window.ns_res - cellhd.ns_res) > GRASS_EPSILON) {
	G_warning(_("Current region resolution and raster map resolution mismatch!"));
	G_warning(_("Real clumps may not be presented"));
	G_warning("ew diff %e", window.ew_res - cellhd.ew_res);
	G_warning("ns diff %e", window.ns_res - cellhd.ns_res);
    }

    nrows = window.rows;
    ncols = window.cols;

    if ((double)nrows * ncols > LONG_MAX)
	G_fatal_error(_("Current region is too large, can't process raster map <%s>"),
		      opt_in->answer);

    /* allocate space */
    clump_id =
	(CELL *) G_malloc(size_array(&ramseg, nrows, ncols) * sizeof(CELL));

    /* read input */
    map_type = Rast_get_map_type(in_fd);
    in_size = Rast_cell_size(map_type);
    in_buf = Rast_allocate_buf(map_type);

    inlist = flag_create(nrows, ncols);

    G_message(_("load input map ..."));
    for (r = 0; r < nrows; r++) {
	Rast_get_row(in_fd, in_buf, r, map_type);
	in_ptr = in_buf;
	G_percent(r, nrows, 2);
	for (c = 0; c < ncols; c++) {
	    index = SEG_INDEX(ramseg, r, c);
	    if (Rast_is_null_value(in_ptr, map_type))
		clump_id[index] = 0;
	    else
		clump_id[index] = 1;

	    FLAG_UNSET(inlist, r, c);

	    in_ptr = G_incr_void_ptr(in_ptr, in_size);
	}
    }
    G_percent(nrows, nrows, 2);

    Rast_close(in_fd);
    G_free(in_buf);

    /* determine clumps */
    G_message(_("determine clumps ..."));

    ncells = nrows * ncols;
    counter = 1;

    /* initialize priority queue */
    init_pq(nrows * ncols * 0.02);

    clump_no = 1;
    index = SEG_INDEX(ramseg, 0, 0);
    if (clump_id[index] != 0)
	clump_id[index] = clump_no++;
    add_pnt(index);
    FLAG_SET(inlist, 0, 0);

    while (pqsize > 0) {
	int start_new = 1;

	G_percent(counter++, ncells, 2);

	index = drop_pnt();
	seg_index_rc(ramseg, index, &r, &c);

	for (s = 0; s < sides; s++) {
	    r_nbr = r + nextdr[s];
	    c_nbr = c + nextdc[s];
	    if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 && c_nbr < ncols) {

		if ((FLAG_GET(inlist, r_nbr, c_nbr)) == 0) {

		    index_nbr = SEG_INDEX(ramseg, r_nbr, c_nbr);

		    /* not in clump, start new clump */
		    if (clump_id[index] == 0 && clump_id[index_nbr] != 0) {
			/* skip other neighbors of same or other clump */
			if (start_new) {
			    clump_id[index_nbr] = clump_no++;
			    add_pnt(index_nbr);
			    FLAG_SET(inlist, r_nbr, c_nbr);
			    start_new = 0;
			}
		    }
		    else if (clump_id[index] == 0 && clump_id[index_nbr] == 0) {
			add_pnt(index_nbr);
			FLAG_SET(inlist, r_nbr, c_nbr);
		    }
		    else if (clump_id[index] != 0) {
			if (clump_id[index_nbr] != 0)
			    clump_id[index_nbr] = clump_id[index];

			add_pnt(index_nbr);
			FLAG_SET(inlist, r_nbr, c_nbr);
		    }
		}
	    }
	}
    }
    free_pq();

    if (counter < ncells)
	G_warning("missed some cells!");

    flag_destroy(inlist);

    /* write output */
    G_message(_("write output map ..."));
    out_buf = Rast_allocate_buf(CELL_TYPE);
    for (r = 0; r < nrows; r++) {
	G_percent(r, nrows, 2);
	for (c = 0; c < ncols; c++) {
	    index = SEG_INDEX(ramseg, r, c);
	    if (clump_id[index] == 0)
		Rast_set_c_null_value(&out_buf[c], 1);
	    else
		out_buf[c] = clump_id[index];

	}
	Rast_put_row(out_fd, out_buf, CELL_TYPE);
    }
    G_percent(nrows, nrows, 2);
    G_free(out_buf);
    Rast_close(out_fd);
    G_free(clump_id);

    G_debug(1, "Creating support files...");

    /* build title */
    if (opt_title->answer != NULL)
	strcpy(title, opt_title->answer);
    else
	sprintf(title, "clump of <%s@%s>", name, G_mapset());

    Rast_put_cell_title(opt_out->answer, title);
    Rast_read_range(opt_out->answer, G_mapset(), &range);
    Rast_get_range_min_max(&range, &min, &max);
    Rast_make_random_colors(&colr, min, max);
    Rast_write_colors(opt_out->answer, G_mapset(), &colr);

    G_done_msg(_("%d clumps."), range.max);

    exit(EXIT_SUCCESS);
}
