#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>

#include "local_proto.h"

int process_coors(char **answers)
{

    int n, outlets_num;
    double X, Y;
    struct Cell_head window;

    if (!answers)
	G_fatal_error(_("At least one pair of coordinates must be send"));

    G_get_window(&window);

    for (n = 0, outlets_num = 0; answers[n] != NULL; n += 2, outlets_num++) ;

    outlets = (OUTLET *) G_malloc(outlets_num * sizeof(OUTLET));

    for (n = 0, outlets_num = 0; answers[n] != NULL; n += 2, outlets_num++) {

	if (!G_scan_easting(answers[n], &X, G_projection()))
            G_fatal_error(_("Wrong coordinate '%s'"), answers[n]);

	if (!answers[n + 1])
	    G_fatal_error(_("Missing north coordinate for east %g"), X);

	if (!G_scan_northing(answers[n + 1], &Y, G_projection()))
	    G_fatal_error(_("Wrong coordinate '%s'"), answers[n + 1]);

	if (X < window.west || X > window.east ||
	    Y < window.south || Y > window.north)
	    G_fatal_error(_("Coordinates outside window"));

	outlets[outlets_num].r = (window.north - Y) / window.ns_res;
	outlets[outlets_num].c = (X - window.west) / window.ew_res;
	outlets[outlets_num].val = outlets_num + 1;
    }

    return outlets_num;
}

int process_vector(char *in_point)
{
    struct Cell_head window;
    struct Map_info Map;
    struct bound_box box;
    int num_point = 0;
    int type, i, cat;
    struct line_pnts *sites;
    struct line_cats *cats;

    sites = Vect_new_line_struct();
    cats = Vect_new_cats_struct();

    Vect_open_old(&Map, in_point, "");

    G_get_window(&window);
    Vect_region_box(&window, &box);

    while ((type = Vect_read_next_line(&Map, sites, cats)) > -1) {
	if (type != GV_POINT)
	    continue;
	if (Vect_point_in_box(sites->x[0], sites->y[0], sites->z[0], &box)) {
	    num_point++;
	}
    }

    outlets = (OUTLET *) G_malloc(num_point * sizeof(OUTLET));

    Vect_rewind(&Map);
    i = 0;
    while ((type = Vect_read_next_line(&Map, sites, cats)) > -1) {
	if (type != GV_POINT)
	    continue;

	if (!Vect_point_in_box(sites->x[0], sites->y[0], sites->z[0], &box))
	    continue;

	Vect_cat_get(cats, 1, &cat);

	outlets[i].r = (int)Rast_northing_to_row(sites->y[0], &window);
	outlets[i].c = (int)Rast_easting_to_col(sites->x[0], &window);
	outlets[i].val = cat;
	i++;
    }

    return num_point;
}

int ram_process_streams(char **cat_list, CELL **streams,
			int number_of_streams, CELL **dirs, int lasts,
			int cats)
{
    int i, cat;
    int r, c, d;		/* d: direction */
    int outlets_num = 0;
    int next_stream = -1, cur_stream;
    int out_max = ncols + nrows;

    categories = NULL;

    if (cat_list) {		/* only if there are at least one category */
	categories = G_malloc((number_of_streams) * sizeof(int));
	memset(categories, -1, (number_of_streams) * sizeof(int));

	for (i = 0; cat_list[i] != NULL; ++i) {
	    cat = atoi(cat_list[i]);
	    if (cat < 1 || cat > number_of_streams)
		G_fatal_error(_("Stream categories must be > 0 and < maximum stream category"));
	    categories[cat] = cat;
	}
    }

    G_message("Finding nodes...");
    outlets = (OUTLET *) G_malloc((out_max) * sizeof(OUTLET));

    for (r = 0; r < nrows; ++r)
	for (c = 0; c < ncols; ++c)
	    if (streams[r][c] > 0) {
		if (outlets_num > 6 * (out_max - 1))
		    G_fatal_error(_("Stream and direction maps probably do not match"));

		if (outlets_num > (out_max - 1))
		    outlets =
			(OUTLET *) G_realloc(outlets,
					     out_max * 6 * sizeof(OUTLET));

		d = abs(dirs[r][c]);	/* r.watershed */

		if (NOT_IN_REGION(d))
		    next_stream = -1;	/* border */
		else
		    next_stream = (streams[NR(d)][NC(d)] > 0) ?
			streams[NR(d)][NC(d)] : -1;

		if (d == 0)
		    next_stream = -1;

		cur_stream = streams[r][c];

		if (lasts) {
		    if (next_stream < 0) {	/* is outlet! */

			if (categories)
			    if (categories[cur_stream] == -1)	/* but not in list */
				continue;

			outlets[outlets_num].r = r;
			outlets[outlets_num].c = c;
			outlets[outlets_num].val =
			    (cats) ? outlets_num + 1 : streams[r][c];
			outlets_num++;
		    }
		}
		else {		/* not lasts */

		    if (cur_stream != next_stream) {	/* is node or outlet! */

			if (categories)
			    if (categories[cur_stream] == -1)	/* but not in list */
				continue;

			outlets[outlets_num].r = r;
			outlets[outlets_num].c = c;
			outlets[outlets_num].val =
			    (cats) ? outlets_num + 1 : streams[r][c];
			outlets_num++;
		    }
		}		/* end if else lasts */
	    }			/* end if streams */

    return outlets_num;
}

int seg_process_streams(char **cat_list, SEGMENT *streams,
			int number_of_streams, SEGMENT *dirs, int lasts,
			int cats)
{
    int i, cat;
    int r, c, d;		/* d: direction */
    int outlets_num;
    int next_stream = -1, cur_stream;
    int streams_cell, dirs_cell, streams_next_cell;
    int out_max = ncols + nrows;

    categories = NULL;

    if (cat_list) {
	categories = G_malloc((number_of_streams) * sizeof(int));
	memset(categories, -1, (number_of_streams) * sizeof(int));

	for (i = 0; cat_list[i] != NULL; ++i) {
	    cat = atoi(cat_list[i]);
	    if (cat < 1 || cat > number_of_streams)
		G_fatal_error(_("Stream categories must be > 0 and < maximum stream category"));
	    categories[cat] = cat;
	}
    }
    G_message("Finding nodes...");
    outlets = (OUTLET *) G_malloc((out_max) * sizeof(OUTLET));
    outlets_num = 0;

    for (r = 0; r < nrows; ++r)
	for (c = 0; c < ncols; ++c) {

	    segment_get(streams, &streams_cell, r, c);
	    if (streams_cell > 0) {
		if (outlets_num > 6 * (out_max - 1))
		    G_fatal_error(_("Stream and direction maps probably do not match"));

		if (outlets_num > (out_max - 1))
		    outlets =
			(OUTLET *) G_realloc(outlets,
					     out_max * 6 * sizeof(OUTLET));

		segment_get(dirs, &dirs_cell, r, c);
		d = abs(dirs_cell);	/* abs */

		if (NOT_IN_REGION(d))
		    next_stream = -1;	/* border */
		else {
		    segment_get(streams, &streams_next_cell, NR(d), NC(d));
		    next_stream =
			(streams_next_cell > 0) ? streams_next_cell : -1;
		}

		if (d == 0)
		    next_stream = -1;

		cur_stream = streams_cell;

		if (lasts) {

		    if (next_stream < 0) {	/* is outlet! */
			if (categories)
			    if (categories[cur_stream] == -1)	/* but not in list */
				continue;

			outlets[outlets_num].r = r;
			outlets[outlets_num].c = c;
			outlets[outlets_num].val =
			    (cats) ? outlets_num + 1 : cur_stream;
			outlets_num++;
		    }
		}
		else {		/* not lasts */

		    if (cur_stream != next_stream) {	/* is outlet or node! */
			if (categories)
			    if (categories[cur_stream] == -1)	/* but not in list */
				continue;

			outlets[outlets_num].r = r;
			outlets[outlets_num].c = c;
			outlets[outlets_num].val =
			    (cats) ? outlets_num + 1 : cur_stream;
			outlets_num++;
		    }
		}		/* end if else lasts */
	    }			/* end if streams */
	}			/* end for */
    return outlets_num;
}
