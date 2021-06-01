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

    if (G_get_cellhd(mapname, mapset, &cellhd) < 0)
	G_fatal_error(_("Unable to read file header of <%s>"), mapname);

    if (mapname != in_elev) {
	/* checking if the input maps type is CELL and region is valid */
	if (G_raster_map_type(mapname, mapset) != CELL_TYPE)
	    G_fatal_error(_("<%s> is not of type CELL"), mapname);
	if (window.ew_res != cellhd.ew_res || window.ns_res != cellhd.ns_res)
	    G_fatal_error(_("Region resolution and map %s resolution differs. Run g.region rast=%s to set proper resolution"),
			  mapname, mapname);
    }				/* end if map not elev */

    if ((fd = G_open_cell_old(mapname, mapset)) < 0)	/* file descriptor */
	G_fatal_error(_("Unable to open raster map <%s>"), mapname);

    if (G_get_cellhd(mapname, mapset, &cellhd) < 0)
	G_fatal_error(_("Unable to read file header of <%s>"), mapname);

    return fd;
}

int create_maps(void)
{
    int r, c;
    int elev_type;
    int in_dir_fd, in_stm_fd, in_dem_fd;
    CELL *r_dirs, *r_streams;
    FCELL *r_dem_f = NULL;
    CELL *r_dem_c = NULL;
    DCELL *r_dem_d = NULL;

    in_dir_fd = open_raster(in_dirs);
    in_stm_fd = open_raster(in_streams);

    r_dirs = (CELL *) G_malloc(sizeof(CELL) * ncols);
    r_streams = (CELL *) G_malloc(sizeof(CELL) * ncols);

    dirs = (CELL **) G_malloc(sizeof(CELL *) * nrows);
    streams = (CELL **) G_malloc(sizeof(CELL *) * nrows);

    if (in_elev) {
	in_dem_fd = open_raster(in_elev);

	elev_type = G_get_raster_map_type(in_dem_fd);
	switch (elev_type) {
	case CELL_TYPE:
	    r_dem_c = (CELL *) G_malloc(sizeof(CELL) * ncols);
	    break;
	case FCELL_TYPE:
	    r_dem_f = (FCELL *) G_malloc(sizeof(FCELL) * ncols);
	    break;
	case DCELL_TYPE:
	    r_dem_d = (DCELL *) G_malloc(sizeof(DCELL) * ncols);
	    break;
	}
	elevation = (FCELL **) G_malloc(sizeof(FCELL *) * nrows);
    }

    G_message(_("Reading maps..."));

    for (r = 0; r < nrows; ++r) {
	G_percent(r, nrows, 2);

	/* dirs & streams */
	dirs[r] = (CELL *) G_malloc(sizeof(CELL) * ncols);
	streams[r] = (CELL *) G_malloc(sizeof(CELL) * ncols);

	if (G_get_c_raster_row(in_dir_fd, r_dirs, r) < 0 ||
	    G_get_c_raster_row(in_stm_fd, r_streams, r) < 0) {
	    G_close_cell(in_dir_fd);
	    G_close_cell(in_stm_fd);
	    G_fatal_error(_("Unable to read raster maps at row <%d>"), r);
	}

	if (in_elev) {
	    elevation[r] = (FCELL *) G_malloc(sizeof(FCELL) * ncols);

	    switch (elev_type) {
	    case CELL_TYPE:	/* CELL */
		if (G_get_c_raster_row(in_dem_fd, r_dem_c, r) < 0) {
		    G_close_cell(in_dem_fd);
		    G_fatal_error(_("Unable to read raster maps at row <%d>"),
				  r);
		}
		for (c = 0; c < ncols; ++c) {
		    if (G_is_c_null_value(&r_dem_c[c])) {
			G_set_f_null_value(&elevation[r][c], 1);
		    }
		    else {
			elevation[r][c] = (FCELL) r_dem_c[c];
		    }
		}		/* end for */
		break;		/* CELL */

	    case DCELL_TYPE:	/* DCELL */
		if (G_get_d_raster_row(in_dem_fd, r_dem_d, r) < 0) {
		    G_close_cell(in_dem_fd);
		    G_fatal_error(_("Unable to read raster maps at row <%d>"),
				  r);
		}
		for (c = 0; c < ncols; ++c) {
		    if (G_is_d_null_value(&r_dem_d[c])) {
			G_set_f_null_value(&elevation[r][c], 1);
		    }
		    else {
			elevation[r][c] = (FCELL) r_dem_d[c];

		    }
		}		/* end for */
		break;		/* DCELL */

	    case FCELL_TYPE:	/* FCELL */
		if (G_get_f_raster_row(in_dem_fd, elevation[r], r) < 0) {
		    G_close_cell(in_dem_fd);
		    G_fatal_error(_("Unable to read raster maps at row <%d>"),
				  r);
		}
		break;		/* FCELL */

	    }			/* end switch */
	}			/* end if elev */

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
	}			/* end for c */

	/* END dirs & streams  & accums */

    }				/*end for r */

    switch (elev_type) {
    case CELL_TYPE:
	G_free(r_dem_c);
	break;
    case DCELL_TYPE:
	G_free(r_dem_d);
	break;
    }

    G_free(r_streams);
    G_free(r_dirs);
    G_percent(r, nrows, 2);
    G_close_cell(in_dir_fd);
    G_close_cell(in_stm_fd);

    return 0;
}				/* end create maps */

void free_streams(void)
{
    int r;

    for (r = 0; r < nrows; ++r)
	G_free(streams[r]);
    G_free(streams);
}

int write_maps(char *mapname, FCELL ** map)
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

int set_null(FCELL ** map)
{
    int r, c;

    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    if (distance[r][c] == -1)
		G_set_f_null_value(&map[r][c], 1);
	}
    }
    return 0;
}
