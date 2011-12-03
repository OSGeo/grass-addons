#include <grass/glocale.h>
#include "global.h"


int open_raster(char *mapname)
{
    int fd = 0;
    char *mapset;
    struct Cell_head cellhd;	/* it stores region information, and header information of rasters */

    mapset = G_find_cell2(mapname, "");	/* checking if map exist */

    if (mapset == NULL)
	G_fatal_error(_("Raster map <%s> not found"), mapname);

    /* checking if the input maps type is CELL */
    if (G_raster_map_type(mapname, mapset) != CELL_TYPE)
	G_fatal_error(_("<%s> is not of type CELL"), mapname);

    if ((fd = G_open_cell_old(mapname, mapset)) < 0)	/* file descriptor */
	G_fatal_error(_("Unable to open raster map <%s>"), mapname);

    if (G_get_cellhd(mapname, mapset, &cellhd) < 0)
	G_fatal_error(_("Unable to read file header of <%s>"), mapname);

    if (window.ew_res != cellhd.ew_res || window.ns_res != cellhd.ns_res)
	G_fatal_error(_("Region resolution and map %s resolution differs. Run g.region rast=%s to set proper resolution"),
		      mapname, mapname);

    return fd;
}


int create_base_maps(void)
{
    int r, c;
    CELL *r_dirs = NULL, *r_streams = NULL;
    int in_dir_fd = 0, in_stm_fd = 0;	/* input file descriptors: indir_fd - direction.... etc */

    in_dir_fd = open_raster(in_dirs);
    in_stm_fd = open_raster(in_streams);

    dirs = (CELL **) G_malloc(sizeof(CELL *) * nrows);
    streams = (CELL **) G_malloc(sizeof(CELL *) * nrows);

    if (out_streams_length)
	streams_length = (FCELL **) G_malloc(sizeof(FCELL *) * nrows);

    r_dirs = (CELL *) G_malloc(sizeof(CELL) * ncols);
    r_streams = (CELL *) G_malloc(sizeof(CELL) * ncols);

    G_message("Reading maps...");

    for (r = 0; r < nrows; ++r) {
	G_percent(r, nrows, 2);
	/* dirs & streams */
	dirs[r] = G_malloc(sizeof(CELL) * ncols);
	streams[r] = G_malloc(sizeof(CELL) * ncols);

	if (out_streams_length)
	    streams_length[r] = G_malloc(sizeof(FCELL *) * ncols);


	if (G_get_c_raster_row(in_dir_fd, r_dirs, r) < 0 ||
	    G_get_c_raster_row(in_stm_fd, r_streams, r) < 0) {
	    G_close_cell(in_dir_fd);
	    G_close_cell(in_stm_fd);

	    G_fatal_error(_("Unable to read raster maps at row <%d>"), r);
	}

	for (c = 0; c < ncols; ++c) {
	    if (G_is_c_null_value(&r_dirs[c]))
		dirs[r][c] = 0;
	    else
		dirs[r][c] = r_dirs[c];

	    if (G_is_c_null_value(&r_streams[c]))
		streams[r][c] = 0;
	    else
		streams[r][c] = r_streams[c];

	    if (out_streams_length)
		streams_length[r][c] = 0.;

	}			/* end for c */

    }				/* end for r */
    G_free(r_streams);
    G_free(r_dirs);
    G_close_cell(in_dir_fd);
    G_close_cell(in_stm_fd);
    G_percent(r, nrows, 2);
    return 0;
}				/* end create base maps */

/*
   int stream_number(void)
   {
   char *cur_mapset;
   CELL c_min, c_max;
   struct Range stream_range;
   G_init_range(&stream_range);
   cur_mapset = G_find_cell2(in_streams, "");
   G_read_range(in_streams,cur_mapset,&stream_range);
   G_get_range_min_max(&stream_range, &c_min, &c_max);
   stream_num=c_max;
   return 0;
   }
 */

int write_maps_f(char *mapname, FCELL ** map)
{
    int r;
    int fd = 0;

    if ((fd = G_open_raster_new(mapname, FCELL_TYPE)) < 0)
	G_fatal_error(_("Unable to create raster map <%s>"), mapname);

    for (r = 0; r < nrows; ++r)
	G_put_f_raster_row(fd, map[r]);

    G_close_cell(fd);
    G_short_history(mapname, "raster", &history);
    G_write_history(mapname, &history);
    G_message(_("%s Done"), mapname);
    G_free(mapname);

    return 0;
}

int write_maps_c(char *mapname, CELL ** map)
{
    int r;
    int fd = 0;

    if ((fd = G_open_raster_new(mapname, CELL_TYPE)) < 0)
	G_fatal_error(_("Unable to create raster map <%s>"), mapname);

    for (r = 0; r < nrows; ++r)
	G_put_c_raster_row(fd, map[r]);

    G_close_cell(fd);
    G_short_history(mapname, "raster", &history);
    G_write_history(mapname, &history);
    G_message(_("%s Done"), mapname);
    G_free(mapname);

    return 0;
}


int set_null_f(FCELL ** map)
{
    int r, c;

    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    if (streams[r][c] == 0)
		G_set_f_null_value(&map[r][c], 1);
	}
    }
    return 0;
}

int set_null_c(CELL ** map)
{
    int r, c;

    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    if (streams[r][c] == 0)
		G_set_c_null_value(&map[r][c], 1);
	}
    }
    return 0;
}
