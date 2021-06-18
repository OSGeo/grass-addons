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

int create_base_maps(void)
{
    int r, c;
    int elev_type;
    int in_dir_fd, in_stm_fd, in_dem_fd;
    CELL *r_dirs, *r_streams;
    FCELL *r_dem_f = NULL;
    DCELL *r_dem_d = NULL;
    CELL *r_dem_c = NULL;

    in_dir_fd = open_raster(in_dirs);
    in_stm_fd = open_raster(in_streams);

    r_dirs = (CELL *) G_malloc(sizeof(CELL) * ncols);
    r_streams = (CELL *) G_malloc(sizeof(CELL) * ncols);

    dirs = (CELL **) G_malloc(sizeof(CELL *) * nrows);
    streams = (CELL **) G_malloc(sizeof(CELL *) * nrows);

    if (extended) {
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

	if (extended) {
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
}				/* end create base maps */


int stream_number(void)
{
    char *cur_mapset;
    CELL c_min, c_max;
    struct Range stream_range;

    G_init_range(&stream_range);
    cur_mapset = G_find_cell2(in_streams, "");
    G_read_range(in_streams, cur_mapset, &stream_range);
    G_get_range_min_max(&stream_range, &c_min, &c_max);
    stream_num = c_max;
    return 0;
}


int close_vector()
{
    int i, j;
    int cur_order;
    int index_cat = 0;
    float angle, tangent;
    struct field_info *Fi;
    dbDriver *driver;
    dbHandle handle;
    dbString table_name, db_sql, val_string;
    char *cat_col_name = "cat";
    char buf[1000];

    db_init_string(&db_sql);
    db_init_string(&val_string);
    db_init_string(&table_name);
    db_init_handle(&handle);

    Fi = Vect_default_field_info(&Out, 1, NULL, GV_1TABLE);
    driver = db_start_driver_open_database(Fi->driver, Fi->database);
    if (driver == NULL) {
	G_fatal_error(_("Unable to start driver <%s>"), Fi->driver);
    }

    if (extended)		/* calculate extended topology */
	sprintf(buf, "create table %s (%s integer, \
		c_stream integer, \
		segment integer, \
		c_order integer, \
		direction double precision, \
		length double precision, \
		drop double precision, \
		ncells integer, \
		n_stream integer, \
		n_tangent double precision\
		)", Fi->table, cat_col_name);
    else			/* only simple results */
	sprintf(buf, "create table %s (%s integer, \
		c_stream integer, \
		c_order integer, \
		direction double precision, \
		length double precision \
		)", Fi->table, cat_col_name);


    db_set_string(&db_sql, buf);

    if (db_execute_immediate(driver, &db_sql) != DB_OK) {
	db_close_database(driver);
	db_shutdown_driver(driver);
	G_fatal_error("Cannot create table %s", db_get_string(&db_sql));
    }

    if (db_create_index2(driver, Fi->table, cat_col_name) != DB_OK)
	G_warning("cannot create index");

    if (db_grant_on_table(driver, Fi->table,
			  DB_PRIV_SELECT, DB_GROUP | DB_PUBLIC) != DB_OK)
	G_fatal_error("cannot grant privileges on table %s", Fi->table);

    db_begin_transaction(driver);

    for (i = 1; i < stream_num + 1; ++i) {

	for (j = 0; j < seg_common[i].seg_num; ++j) {
	    index_cat = seg_common[i].cats[j];

	    angle =
		(radians) ? seg_common[i].angles[j] : rad2deg(seg_common[i].
							      angles[j]);
	    tangent =
		(radians) ? s_streams[s_streams[i].next_stream].
		tangent_dir : rad2deg(s_streams[s_streams[i].next_stream].
				      tangent_dir);

	    cur_order =
		(ordering) ? cur_orders(s_streams[i].stream, ordering) : 0;

	    if (extended)
		sprintf(buf,
			"insert into %s  values (%d, %d, %d, %d, %f, %f, %f, %d, %d, %f)",
			Fi->table, index_cat, s_streams[i].stream, j,
			cur_order, angle, seg_common[i].lengths[j],
			seg_common[i].drops[j], seg_common[i].cellnums[j],
			s_streams[i].next_stream, tangent);
	    else
		sprintf(buf, "insert into %s  values (%d, %d, %d, %f, %f)",
			Fi->table,
			index_cat,
			s_streams[i].stream,
			cur_order, angle, seg_common[i].lengths[j]
		    );

	    db_set_string(&db_sql, buf);

	    if (db_execute_immediate(driver, &db_sql) != DB_OK) {
		db_close_database(driver);
		db_shutdown_driver(driver);
		G_fatal_error("Cannot inset new row: %s",
			      db_get_string(&db_sql));
	    }

	}
    }
    db_commit_transaction(driver);
    db_close_database_shutdown_driver(driver);

    Vect_map_add_dblink(&Out, 1, NULL, Fi->table,
			cat_col_name, Fi->database, Fi->driver);

    Vect_hist_command(&Out);
    Vect_build(&Out);
    Vect_close(&Out);

    return 0;
}
