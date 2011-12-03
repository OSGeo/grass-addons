#include "global.h"

int open_raster(char *mapname)
{
    int fd = 0;
    char *mapset;
    struct Cell_head cellhd;	/* it stores region information, and header information of rasters */

    mapset = G_find_cell2(mapname, "");	/* checking if map exist */
    if (mapset == NULL) {
	G_fatal_error("Raster map <%s> not found", mapname);
    }

    if (G_raster_map_type(mapname, mapset) != CELL_TYPE)	/* checking if the input maps type is CELL */
	G_fatal_error("<%s> is not of type CELL.", mapname);

    if ((fd = G_open_cell_old(mapname, mapset)) < 0)	/* file descriptor */
	G_fatal_error("Unable to open raster map <%s>", mapname);

    if (G_get_cellhd(mapname, mapset, &cellhd) < 0)
	G_fatal_error("Unable to read file header of <%s>", mapname);

    if (window.ew_res != cellhd.ew_res || window.ns_res != cellhd.ns_res)
	G_fatal_error
	    ("Region resolution and map %s resolution differs. Run g.region rast=%s to set proper resolution",
	     mapname, mapname);

    return fd;
}

int create_maps(void)
{
    int r, c;
    int in_dir_fd, in_stm_fd;	/* input file descriptors: indir_fd - direction.... etc */
    CELL *r_dirs, *r_streams;

    G_message("Reading maps...");

    in_dir_fd = open_raster(in_dirs);
    r_dirs = (CELL *) G_malloc(sizeof(CELL) * ncols);
    dirs = (CELL **) G_malloc(sizeof(CELL *) * nrows);

    r_streams = (CELL *) G_malloc(sizeof(CELL) * ncols);
    streams = (CELL **) G_malloc(sizeof(CELL *) * nrows);

    if (in_streams) {

	in_stm_fd = open_raster(in_streams);

	for (r = 0; r < nrows; ++r) {
	    G_percent(r, nrows, 2);
	    streams[r] = (CELL *) G_malloc(sizeof(CELL) * ncols);


	    if (G_get_c_raster_row(in_stm_fd, r_streams, r) < 0) {
		G_close_cell(in_stm_fd);
		G_fatal_error("Unable to read raster maps at row <%d>", r);
	    }

	    for (c = 0; c < ncols; ++c) {
		if (G_is_c_null_value(&r_streams[c]))
		    streams[r][c] = 0;
		else
		    streams[r][c] = r_streams[c];
	    }
	}
	G_free(r_streams);
	G_close_cell(in_stm_fd);
	G_percent(r, nrows, 2);
    }				/* end if streams */

    for (r = 0; r < nrows; ++r) {
	G_percent(r, nrows, 2);

	dirs[r] = (CELL *) G_malloc(sizeof(CELL) * ncols);
	if (!in_streams)
	    streams[r] = (CELL *) G_malloc(sizeof(CELL) * ncols);

	if (G_get_c_raster_row(in_dir_fd, r_dirs, r) < 0) {
	    G_close_cell(in_dir_fd);
	    G_fatal_error("Unable to read raster maps at row <%d>", r);
	}

	for (c = 0; c < ncols; ++c) {
	    if (G_is_c_null_value(&r_dirs[c]))
		dirs[r][c] = 0;
	    else
		dirs[r][c] = r_dirs[c];
	}
    }				/*end for r */

    G_free(r_dirs);
    G_close_cell(in_dir_fd);
    G_percent(r, nrows, 2);
    return 0;
}				/* end create maps */

int max_link(void)
{
    char *cur_mapset;
    CELL c_min, c_max;
    struct Range stream_range;

    G_init_range(&stream_range);
    cur_mapset = G_find_cell2(in_streams, "");
    G_read_range(in_streams, cur_mapset, &stream_range);
    G_get_range_min_max(&stream_range, &c_min, &c_max);
    return c_max;
}				/* end_max_link       */


int write_catchment(void)
{
    int r;
    int fdo = 0;

    if ((fdo = G_open_raster_new(name_catchments, CELL_TYPE)) < 0)
	G_fatal_error("Unable to create raster map <%s>", name_catchments);

    for (r = 0; r < nrows; ++r)
	G_put_c_raster_row(fdo, streams[r]);

    G_close_cell(fdo);
    G_short_history(name_catchments, "raster", &history);
    G_write_history(name_catchments, &history);
    G_message("%s Done!", name_catchments);

    G_free(streams);
    return 0;
}

int set_null(void)
{
    int r, c;

    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    if (streams[r][c] < 0)
		streams[r][c] = 1;

	    if (streams[r][c] == 0)
		G_set_c_null_value(&streams[r][c], 1);
	}
    }
    return 0;
}

int process_coors(char **answers)
{

    int n, n_outlets;
    double X, Y;

    if (!answers)
	return 0;

    for (n = 0, n_outlets = 0; answers[n] != NULL; n += 2, n_outlets++);

    outlets = (OUTLET *)G_malloc(n_outlets * sizeof(OUTLET));

    for (n = 0, n_outlets = 0; answers[n] != NULL; n += 2, n_outlets++) {
	if (!G_scan_easting(answers[n], &X, G_projection()))
	    G_fatal_error("Wrong coordinate <%s>", answers[n]);
	if (!answers[n + 1])
	    G_fatal_error("Missing north coordinate for east %g", X);
	if (!G_scan_northing(answers[n + 1], &Y, G_projection()))
	    G_fatal_error("Wrong coordinate <%s>", answers[n + 1]);

	if (X < window.west || X > window.east || Y < window.south ||
	    Y > window.north)
	    G_fatal_error("Coordinates outside window");

	outlets[n_outlets].r = (window.north - Y) / window.ns_res;
	outlets[n_outlets].c = (X - window.west) / window.ew_res;
	outlets[n_outlets].val = n_outlets + 1;
    }

    return n_outlets;
}

int process_cats(char **answers)
{
    int i;
    int link_max = max_link();
    int cat;

    if (!answers)
	return 1;

    categories = G_malloc((link_max + 1) * sizeof(int));

    for (i = 0; i < (link_max + 1); ++i)
	categories[i] = -1;


    for (i = 0; answers[i] != NULL; ++i) {
	cat = atoi(answers[i]);
	if (cat < 1 || cat > link_max)
	    G_fatal_error
		("Stream categories must be > 0 and < maximum stream category");
	categories[cat] = cat;
    }

    return 0;			/* success */
}


int process_vector(char *in_point)
{
    char *mapset;
    struct Map_info Map;
    struct bound_box box;
    int num_point = 0;
    int type, i, cat;
    struct line_pnts *sites;
    struct line_cats *cats;

    sites = Vect_new_line_struct();
    cats = Vect_new_cats_struct();

    mapset = G_find_vector2(in_point, "");
    if (mapset == NULL)
	G_fatal_error(_("Vector map <%s> not found"), in_point);

    if (Vect_open_old(&Map, in_point, mapset) < 0)
	G_fatal_error("Cannot open vector map <%s>", in_point);

    Vect_region_box(&window, &box);

    while ((type = Vect_read_next_line(&Map, sites, cats)) > -1) {
	if (type != GV_POINT)
	    continue;
	if (Vect_point_in_box(sites->x[0], sites->y[0], sites->z[0], &box))
	    num_point++;
    }

    outlets = (OUTLET *) G_malloc(num_point * sizeof(OUTLET));

    for (i = 0; i < num_point; ++i) {

	type = Vect_read_line(&Map, sites, cats, i + 1);
	if (type != GV_POINT)
	    continue;

	if (!Vect_point_in_box(sites->x[0], sites->y[0], sites->z[0], &box))
	    continue;

	Vect_cat_get(cats, 1, &cat);

	outlets[i].r = (int)G_northing_to_row(sites->y[0], &window);
	outlets[i].c = (int)G_easting_to_col(sites->x[0], &window);
	outlets[i].val = cat;
    }
    return num_point;
}
