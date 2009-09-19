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

    if (mapname != in_accum) {
	if (G_raster_map_type(mapname, mapset) != CELL_TYPE)	/* checking if the input maps type is CELL */
	    G_fatal_error(_("<%s> is not of type CELL"), mapname);
    }

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
    CELL *r_dirs=NULL, *r_streams=NULL;
    DCELL *r_accum=NULL;
    int in_dir_fd=0, in_stm_fd=0, in_acc_fd=0;	/* input file descriptors: indir_fd - direction.... etc */

    in_dir_fd = open_raster(in_dirs);
    in_stm_fd = open_raster(in_streams);
    if (in_accum)
	in_acc_fd = open_raster(in_accum);

    dirs = (CELL **) G_malloc(sizeof(CELL *) * nrows);
    streams = (CELL **) G_malloc(sizeof(CELL *) * nrows);
    if (in_accum)
	accum = (DCELL **) G_malloc(sizeof(DCELL *) * nrows);

    r_dirs = (CELL *) G_malloc(sizeof(CELL) * ncols);
    r_streams = (CELL *) G_malloc(sizeof(CELL) * ncols);
    if (in_accum)
	r_accum = (DCELL *) G_malloc(sizeof(DCELL) * ncols);

    G_message(_("Reading maps..."));

    for (r = 0; r < nrows; ++r) {
	G_percent(r, nrows, 2);
	/* dirs & streams */
	dirs[r] = G_malloc(sizeof(CELL) * ncols);
	streams[r] = G_malloc(sizeof(CELL) * ncols);

	if (G_get_c_raster_row(in_dir_fd, r_dirs, r) < 0 ||
	    G_get_c_raster_row(in_stm_fd, r_streams, r) < 0) {
	    G_close_cell(in_dir_fd);
	    G_close_cell(in_stm_fd);
	    G_fatal_error(_("Unable to read raster maps at row <%d>"), r);
	}

	if (in_accum) {
	    accum[r] = (DCELL *) G_malloc(sizeof(DCELL) * ncols);
	    if (G_get_d_raster_row(in_acc_fd, r_accum, r) < 0) {
		G_close_cell(in_acc_fd);
		G_fatal_error(_("Unable to read raster maps at row <%d>"), r);
	    }
	}

	for (c = 0; c < ncols; ++c) {
	    if (G_is_c_null_value(&r_dirs[c])) {
		dirs[r][c] = 0;
	    }
	    else {
		dirs[r][c] = r_dirs[c];
	    }
	    if (G_is_c_null_value(&r_streams[c])) {
		streams[r][c] = 0;
	    }
	    else {
		streams[r][c] = r_streams[c];
	    }

	    if (in_accum) {
		if (G_is_d_null_value(&r_accum[c])) {
		    accum[r][c] = 0;
		}
		else {
		    accum[r][c] = r_accum[c];
		}
	    }			/* end if accum */

	}			/* end for c */
    }
    G_free(r_streams);
    G_free(r_dirs);
    	if (in_accum) 
		G_free(r_accum);
    G_percent(r, nrows, 2);
    G_close_cell(in_dir_fd);
    G_close_cell(in_stm_fd);
    	if (in_accum) 
    G_close_cell(in_acc_fd);
    return 0;
}				/* end create base maps */

int stream_number(void)
{
	char *cur_mapset;
	CELL c_min, c_max;
	struct Range *stream_range;
	G_init_range(stream_range);
	cur_mapset = G_find_cell2(in_streams, "");
	G_read_range(in_streams,cur_mapset,stream_range);
	G_get_range_min_max(stream_range, &c_min, &c_max);
	return c_max;
}

int write_maps(void)
{
    int r, c;
    CELL *strahler_buf, *shreeve_buf, *hack_buf, *horton_buf;
    int out_str_fd, out_shr_fd, out_hck_fd, out_hrt_fd;	/* output file descriptors: outstr_fd - strahler... etc */
    struct History history;	/* holds meta-data (title, comments,..) */

    /* routine check if legal file names and we able to opuen files */
    if (out_strahler) {
	if ((out_str_fd = G_open_raster_new(out_strahler, CELL_TYPE)) < 0)
	    G_fatal_error(_("Unable to create raster map <%s>"),
			  out_strahler);
	strahler_buf = G_allocate_cell_buf();
    }

    if (out_shreeve) {
	if ((out_shr_fd = G_open_raster_new(out_shreeve, CELL_TYPE)) < 0)
	    G_fatal_error(_("Unable to create raster map <%s>"), out_shreeve);
	shreeve_buf = G_allocate_cell_buf();
    }

    if (out_hack) {
	if ((out_hck_fd = G_open_raster_new(out_hack, CELL_TYPE)) < 0)
	    G_fatal_error(_("Unable to create raster map <%s>"), out_hack);
	hack_buf = G_allocate_cell_buf();
    }

    if (out_horton) {
	if ((out_hrt_fd = G_open_raster_new(out_horton, CELL_TYPE)) < 0)
	    G_fatal_error(_("Unable to create raster map <%s>"), out_horton);
	horton_buf = G_allocate_cell_buf();
    }

    G_message(_("Writing maps..."));

    for (r = 0; r < nrows; ++r) {
	G_percent(r, nrows, 2);

	if (out_strahler)
	    G_set_c_null_value(strahler_buf, ncols);
	if (out_shreeve)
	    G_set_c_null_value(shreeve_buf, ncols);
	if (out_hack)
	    G_set_c_null_value(hack_buf, ncols);
	if (out_horton)
	    G_set_c_null_value(horton_buf, ncols);

	for (c = 0; c < ncols; ++c) {
	    if (!out_zero) {
		if (streams[r][c] > 0) {
		    if (out_strahler)
			strahler_buf[c] = s_streams[streams[r][c]].strahler;
		    if (out_shreeve)
			shreeve_buf[c] = s_streams[streams[r][c]].shreeve;
		    if (out_hack)
			hack_buf[c] = s_streams[streams[r][c]].hack;
		    if (out_horton)
			horton_buf[c] = s_streams[streams[r][c]].horton;
		}		/* end if streams */
	    }
	    else if (out_zero) {
		if (out_strahler)
		    strahler_buf[c] = s_streams[streams[r][c]].strahler;
		if (out_shreeve)
		    shreeve_buf[c] = s_streams[streams[r][c]].shreeve;
		if (out_hack)
		    hack_buf[c] = s_streams[streams[r][c]].hack;
		if (out_horton)
		    horton_buf[c] = s_streams[streams[r][c]].horton;
	    }
	}			/* end for cols */

	if (out_strahler)
	    G_put_c_raster_row(out_str_fd, strahler_buf);
	if (out_shreeve)
	    G_put_c_raster_row(out_shr_fd, shreeve_buf);
	if (out_hack)
	    G_put_c_raster_row(out_hck_fd, hack_buf);
	if (out_horton)
	    G_put_c_raster_row(out_hrt_fd, horton_buf);
    }				/* end for r */

    G_percent(r, nrows, 2);

    if (out_strahler) {
	G_close_cell(out_str_fd);
	G_free(strahler_buf);
	G_short_history(out_strahler, "raster", &history);
	G_write_history(out_strahler, &history);
	G_message(_("%s Done!"),out_strahler);
    }

    if (out_shreeve) {
	G_close_cell(out_shr_fd);
	G_free(shreeve_buf);
	G_short_history(out_shreeve, "raster", &history);
	G_write_history(out_shreeve, &history);
	G_message(_("%s Done!"),out_shreeve);
    }
    if (out_hack) {
	G_close_cell(out_hck_fd);
	G_free(hack_buf);
	G_short_history(out_hack, "raster", &history);
	G_write_history(out_hack, &history);
	G_message(_("%s Done!"),out_hack);
    }

    if (out_horton) {
	G_close_cell(out_hrt_fd);
	G_free(horton_buf);
	G_short_history(out_horton, "raster", &history);
	G_write_history(out_horton, &history);
	G_message(_("%s Done!"),out_horton);
    }

    return 0;

}				/* end write_maps */
