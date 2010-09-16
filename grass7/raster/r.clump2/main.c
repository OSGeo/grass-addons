
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
    struct Option *opt_coord;
    struct Flag *flag_sides;
    CELL clump_no, *out_buf;
    struct Cell_head window, cellhd;
    int nrows, ncols, r, c;
    long ncells, counter;
    void *in_ptr, *in_buf;
    int map_type, in_size;
    FLAG *inlist;
    int ramseg;
    long index, index_nbr;
    int sides, s, r_nbr, c_nbr, have_seeds = 0, *id_map = NULL;
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
    
    opt_coord = G_define_option();
    opt_coord->key = "coordinate";
    opt_coord->type = TYPE_STRING;
    opt_coord->key_desc = "x,y";
    opt_coord->multiple = YES;
    opt_coord->description =
	_("Map grid coordinates of starting points (E,N)");

    flag_sides = G_define_flag();
    flag_sides->key = 'e';
    flag_sides->description = _("Ignore diagonal cells");

    /* parse options */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    in_fd = Rast_open_old(opt_in->answer, "");
    if (in_fd < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), opt_in->answer);

    out_fd = Rast_open_c_new(opt_out->answer);
    if (out_fd < 0)
	G_fatal_error(_("Unable to create raster map <%s>"), opt_out->answer);

    if (flag_sides->answer)
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

    ncells = nrows * ncols;
    counter = 1;

    /* initialize priority queue */
    init_pq(nrows * ncols * 0.02);

    clump_no = 1;
    if (opt_coord->answers) {
	int col, row, i;
	double east, north;
	char **answers = opt_coord->answers;
	struct Cell_head window;
	
	/* get start point coordinates */
	G_message(_("get start point coordinates ..."));

	G_get_window(&window);
	
	for (; *answers != NULL; answers += 2) {
	    if (!G_scan_easting(*answers, &east, G_projection()))
		G_fatal_error(_("Illegal x coordinate <%s>"), *answers);
	    if (*(answers + 1) == NULL)
		G_fatal_error(_("Missing y corrdinate"));
	    if (!G_scan_northing(*(answers + 1), &north, G_projection()))
		G_fatal_error(_("Illegal y coordinate <%s>"), *(answers + 1));

	    if (east < window.west || east > window.east ||
		north < window.south || north > window.north) {
		G_warning(_("Warning, ignoring point outside window: %.4f,%.4f"),
			  east, north);
		continue;
	    }
	    row = (window.north - north) / window.ns_res;
	    col = (east - window.west) / window.ew_res;
	    
	    index = SEG_INDEX(ramseg, row, col);
	    if (clump_id[index] != 0) {
		/* add seed points with decreasing clump ID: first point will seed first clump */
		clump_id[index] = clump_no++;
		add_pnt(index);
		FLAG_SET(inlist, row, col);
	    }
	}

	id_map = G_malloc(clump_no * sizeof(int));
	for (i = 0; i < clump_no; i++)
	    id_map[i] = i;

	have_seeds = 1;
    }
    else {
	index = SEG_INDEX(ramseg, 0, 0);
	if (clump_id[index] != 0)
	    clump_id[index] = clump_no++;
	add_pnt(index);
	FLAG_SET(inlist, 0, 0);
    }

    /* determine clumps */
    G_message(_("determine clumps ..."));

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
			if (!have_seeds) {
			    add_pnt(index_nbr);
			    FLAG_SET(inlist, r_nbr, c_nbr);
			}
		    }
		    else if (clump_id[index] != 0) {
			if (clump_id[index_nbr] != 0)
			    clump_id[index_nbr] = clump_id[index];

			if (!have_seeds ||
			    (have_seeds && clump_id[index_nbr] != 0)) {
			    add_pnt(index_nbr);
			    FLAG_SET(inlist, r_nbr, c_nbr);
			}
		    }
		}
		else if (have_seeds) {
		    /* safety check */
		    index_nbr = SEG_INDEX(ramseg, r_nbr, c_nbr);
		    if (clump_id[index] != clump_id[index_nbr]) {
			G_warning(_("%d. and %d. start point are in the same clump, ignoring %d. start point"),
			          clump_id[index], clump_id[index_nbr], clump_id[index_nbr]);
			id_map[clump_id[index_nbr]] = clump_id[index];
			clump_id[index_nbr] = clump_id[index];
		    }
		}
	    }
	}
    }
    free_pq();

    if (counter < ncells) {
	if (!have_seeds)
	    G_warning("missed some cells!");
	else
	    G_percent(ncells, ncells, 1);
    }
    
    if (have_seeds && clump_no > 1) {
	int i;
	
	for (i = 1; i < clump_no; i++) {
	    if (id_map[i] - id_map[i - 1] > 1)
		id_map[i] = id_map[i - 1] + 1;
	}
    }
    
    /* write output */
    G_message(_("write output map ..."));
    out_buf = Rast_allocate_buf(CELL_TYPE);
    for (r = 0; r < nrows; r++) {
	G_percent(r, nrows, 2);
	for (c = 0; c < ncols; c++) {
	    index = SEG_INDEX(ramseg, r, c);
	    if (have_seeds) {
		if ((FLAG_GET(inlist, r, c)) == 0) {
		    clump_id[index] = 0;
		}
		else
		    clump_id[index] = id_map[clump_id[index]];
	    }
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
    flag_destroy(inlist);
    if (id_map)
	G_free(id_map);


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
