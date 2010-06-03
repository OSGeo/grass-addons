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
    CELL *r_dirs = NULL, *r_streams = NULL;
    DCELL *r_accum = NULL;

    int in_dir_fd = 0, in_stm_fd = 0, in_acc_fd = 0;	/* input file descriptors: indir_fd - direction.... etc */

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
    struct Range stream_range;

    G_init_range(&stream_range);
    cur_mapset = G_find_cell2(in_streams, "");
    G_read_range(in_streams, cur_mapset, &stream_range);
    G_get_range_min_max(&stream_range, &c_min, &c_max);
    if (c_max < 1)
	G_fatal_error("No streams found");
    return c_max;

}

int write_maps(void)
{
    int r, c;
    CELL *strahler_buf, *shreeve_buf, *hack_buf, *horton_buf, *topo_buf;
    int out_str_fd, out_shr_fd, out_hck_fd, out_hrt_fd, out_topo_fd;	/* output file descriptors: outstr_fd - strahler... etc */
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

    if (out_topo) {
	if ((out_topo_fd = G_open_raster_new(out_topo, CELL_TYPE)) < 0)
	    G_fatal_error(_("Unable to create raster map <%s>"), out_topo);
	topo_buf = G_allocate_cell_buf();
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
	if (out_topo)
	    G_set_c_null_value(topo_buf, ncols);

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
		    if (out_topo)
			topo_buf[c] = s_streams[streams[r][c]].topo_dim;
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
		if (out_topo)
		    topo_buf[c] = s_streams[streams[r][c]].topo_dim;

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
	if (out_topo)
	    G_put_c_raster_row(out_topo_fd, topo_buf);

    }				/* end for r */

    G_percent(r, nrows, 2);

    if (out_strahler) {
	G_close_cell(out_str_fd);
	G_free(strahler_buf);
	G_short_history(out_strahler, "raster", &history);
	G_write_history(out_strahler, &history);
	G_message(_("%s Done!"), out_strahler);
    }

    if (out_shreeve) {
	G_close_cell(out_shr_fd);
	G_free(shreeve_buf);
	G_short_history(out_shreeve, "raster", &history);
	G_write_history(out_shreeve, &history);
	G_message(_("%s Done!"), out_shreeve);
    }
    if (out_hack) {
	G_close_cell(out_hck_fd);
	G_free(hack_buf);
	G_short_history(out_hack, "raster", &history);
	G_write_history(out_hack, &history);
	G_message(_("%s Done!"), out_hack);
    }

    if (out_horton) {
	G_close_cell(out_hrt_fd);
	G_free(horton_buf);
	G_short_history(out_horton, "raster", &history);
	G_write_history(out_horton, &history);
	G_message(_("%s Done!"), out_horton);
    }

    if (out_topo) {
	G_close_cell(out_topo_fd);
	G_free(topo_buf);
	G_short_history(out_topo, "raster", &history);
	G_write_history(out_topo, &history);
	G_message(_("%s Done!"), out_topo);
    }

    return 0;
}				/* end write_maps */

int create_table(void)
{
    int i;
    int max_trib = 0;
    /*
    char *mapset;
    struct Map_info Map;
    char out_table[30];
     */
    char *out_table;
    dbConnection conn;
    dbDriver *driver;
    dbHandle handle;
    dbString table_name, db_sql, val_string;
    char buf[1000];
    char ins_prev_streams[50];	/* insert */
    char *cat_col_name = "cat";
    /* table definition */
    char *tab_cat_col_name = "cat integer";
    char *tab_stream = "stream integer";
    char *tab_next_stream = "next_stream integer";
    char *tab_prev_streams;
    char *tab_strahler = "strahler integer";
    char *tab_horton = "horton integer";
    char *tab_shreve = "shreve integer";
    char *tab_hack = "hack integer";
    char *tab_length = "length double precision";
    char *tab_cumlength = "cum_length double precision";
    char *tab_stright = "stright double precision";
    char *tab_fractal = "fractal double precision";
    char *tab_distance = "out_dist double precision";
    char *tab_topo_dim = "topo_dim integer";

    G_message("Adding table...");

    /* trib num */
    for (i = 0; i < stream_num + 1; ++i) {
	if (s_streams[i].trib_num > max_trib)
	    max_trib = s_streams[i].trib_num;
    }

    /*
       mapset = G_find_vector(in_vector, "");
       if (mapset == NULL)
       G_fatal_error(_("Vector map <%s> not found"), in_vector);

       if (Vect_open_update(&Map, in_vector, mapset) < 0)
       G_fatal_error("Cannot open vector map <%s>", in_vector);

       if(in_table)
       sprintf(out_table, "%s",in_table);
       else
       sprintf(out_table, "%s_new",in_vector);
     */

    out_table = in_table;

    /* init */

    db_init_string(&db_sql);
    db_init_string(&val_string);
    db_init_string(&table_name);
    db_init_handle(&handle);

    /* string to db */

    db_get_connection(&conn);
    driver =
	db_start_driver_open_database(conn.driverName, conn.databaseName);

    if (db_table_exists(conn.driverName, conn.databaseName, out_table) > 0)
	G_fatal_error
	    ("table %s exists. Choose different table name or check and remove existing table",
	     out_table);

    /* creating table */

    switch (max_trib) {
    case 2:
	tab_prev_streams = "prev_str01 integer, prev_str02 integer";
	break;
    case 3:
	tab_prev_streams =
	    "prev_str01 integer, prev_str02 integer, prev_str03 integer";
	break;
    case 4:
	tab_prev_streams =
	    "prev_str01 integer, prev_str02 integer, prev_str03 integer prev_str04 integer";
	break;
    case 5:
	tab_prev_streams =
	    "prev_str01 integer, prev_str02 integer, prev_str03 integer prev_str04 integer, prev_str05 integer";
	break;
    default:
	G_fatal_error("Error with number of tributuaries");
	break;
    }


    sprintf(buf,
	    "create table %s (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
	    out_table, tab_cat_col_name, tab_stream, tab_next_stream,
	    tab_prev_streams, tab_strahler, tab_horton, tab_shreve, tab_hack,
	    tab_topo_dim, tab_length, tab_cumlength, tab_distance,
	    tab_stright, tab_fractal);

    db_set_string(&db_sql, buf);

    if (db_execute_immediate(driver, &db_sql) != DB_OK) {
	db_close_database(driver);
	db_shutdown_driver(driver);
	G_fatal_error("Cannot create table %s", db_get_string(&db_sql));
    }

    if (db_create_index2(driver, out_table, cat_col_name) != DB_OK)
	G_warning("cannot create index");

    if (db_grant_on_table
	(driver, out_table, DB_PRIV_SELECT, DB_GROUP | DB_PUBLIC) != DB_OK)
	G_fatal_error("cannot grant privileges on table %s", out_table);

    db_begin_transaction(driver);

    for (i = 0; i < stream_num + 1; ++i) {

	if (s_streams[i].stream < 0)
	    continue;

	switch (max_trib) {
	case 2:
	    sprintf(ins_prev_streams, "%d, %d", s_streams[i].trib[0],
		    s_streams[i].trib[1]);
	    break;
	case 3:
	    sprintf(ins_prev_streams, "%d ,%d, %d", s_streams[i].trib[0],
		    s_streams[i].trib[1], s_streams[i].trib[2]);
	    break;
	case 4:
	    sprintf(ins_prev_streams, "%d, %d, %d, %d", s_streams[i].trib[0],
		    s_streams[i].trib[1], s_streams[i].trib[2],
		    s_streams[i].trib[3]);
	    break;
	case 5:
	    sprintf(ins_prev_streams, "%d, %d, %d, %d, %d",
		    s_streams[i].trib[0], s_streams[i].trib[1],
		    s_streams[i].trib[2], s_streams[i].trib[3],
		    s_streams[i].trib[4]);
	    break;
	default:
	    G_fatal_error("Error with number of tributuaries");
	    break;
	}

	sprintf(buf, "insert into %s  values	\
			(%d, %d, %d, %s, %d, %d, %d, %d, %d, %f, %f , %f, %f, %f)", out_table, i, s_streams[i].stream, s_streams[i].next_stream, ins_prev_streams, s_streams[i].strahler, s_streams[i].horton, s_streams[i].shreeve, s_streams[i].hack, s_streams[i].topo_dim, s_streams[i].length, s_streams[i].accum, s_streams[i].distance, s_streams[i].stright, s_streams[i].fractal);

	db_set_string(&db_sql, buf);

	if (db_execute_immediate(driver, &db_sql) != DB_OK) {
	    db_close_database(driver);
	    db_shutdown_driver(driver);
	    G_fatal_error("Cannot inset new row: %s", db_get_string(&db_sql));
	}
    }

    db_commit_transaction(driver);
    db_close_database_shutdown_driver(driver);

    /*
       if(Vect_map_check_dblink(&Map,1)) 
       Vect_map_del_dblink(&Map,1);

       Vect_map_add_dblink(&Map, 1, NULL, out_table,
       tab_cat_col_name, conn.driverName, conn.databaseName);

       Vect_hist_command(&Map);
       Vect_build(&Map);
       Vect_close(&Map);
     */

    G_message("Table %s created. You can join it to vector created with r.stream.extract \
						using v.db.connect",
	      out_table);
    return 0;
}
