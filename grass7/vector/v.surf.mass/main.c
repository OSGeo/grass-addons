
/**********************************************************************
 *
 * MODULE:       v.surf.mass
 *
 * AUTHOR(S):    Markus Metz
 *
 * PURPOSE:      Mass-preserving area interpolation
 *               (Smooth Pycnophylactic Interpolation after Tobler 1979)
 *
 * COPYRIGHT:    (C) 2013 by by the GRASS Development Team
 *
 *               This program is free software under the
 *               GNU General Public License (>=v2).
 *               Read the file COPYING that comes with GRASS
 *               for details.
 *
 **********************************************************************/

#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include "globals.h"

#define SEGSIZE 64

int main(int argc, char *argv[])
{
    const char *mapset, *column;
    int row, col, nrows, ncols, rrow, ccol, nrow, ncol;

    SEGMENT out_seg;
    int out_fd;
    DCELL *drastbuf;
    double seg_size;
    int seg_mb, segments_in_memory;
    int doit, iter, maxiter;
    double threshold, maxadj;
    int negative = 0, have_neg;

    int layer;
    int i, j, nareas;
    struct marea *areas;

    struct Map_info In;
    struct line_pnts *Points;
    struct line_cats *Cats;
    struct Cell_head window;
    struct History history;

    struct lcell thiscell;
    double outside_val, value, interp, avgdiff;

    struct GModule *module;
    struct Option *in_opt, *out_opt, *dfield_opt, *col_opt,
	*memory_opt, *iter_opt, *threshold_opt;
	/* border condition */
    struct Flag *withz_flag; /* allow negative */

    int more, sqltype = 0, ctype = 0;
    struct field_info *Fi;
    dbDriver *driver;
    dbColumn *dbcolumn;
    dbCursor cursor;
    dbTable *dbtable;
    dbValue *dbvalue;
    dbString dbstring;
    char *buf = NULL;
    size_t bufsize = 0;

    /*----------------------------------------------------------------*/
    /* Options declarations */
    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("surface"));
    G_add_keyword(_("interpolation"));
    G_add_keyword(_("pycnophylactic interpolation"));
    module->description =
	_("Performs mass-preserving area interpolation.");

    in_opt = G_define_standard_option(G_OPT_V_INPUT);
    in_opt->label = _("Name of input vector point map");
    
    dfield_opt = G_define_standard_option(G_OPT_V_FIELD);

    col_opt = G_define_standard_option(G_OPT_DB_COLUMN);
    col_opt->key = "column";
    col_opt->required = NO;
    col_opt->description =
	_("Name of attribute column with values to approximate");
    col_opt->guisection = _("Settings");

    out_opt = G_define_standard_option(G_OPT_R_OUTPUT);
    out_opt->required = YES;

    iter_opt = G_define_option();
    iter_opt->key = "iterations";
    iter_opt->type = TYPE_INTEGER;
    iter_opt->answer = "100";
    iter_opt->required = NO;

    threshold_opt = G_define_option();
    threshold_opt->key = "threshold";
    threshold_opt->type = TYPE_DOUBLE;
    threshold_opt->answer = "1e-8";
    threshold_opt->required = NO;

    memory_opt = G_define_option();
    memory_opt->key = "memory";
    memory_opt->type = TYPE_INTEGER;
    memory_opt->required = NO;
    memory_opt->answer = "300";
    memory_opt->description = _("Maximum memory to be used for raster output (in MB)");

    withz_flag = G_define_flag();
    withz_flag->key = 'z';
    withz_flag->description = _("Use centroid z coordinates for approximation (3D vector maps only)");
    withz_flag->guisection = _("Settings");


    G_gisinit(argv[0]);
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    maxiter = atoi(iter_opt->answer);
    threshold = atof(threshold_opt->answer);
    
    outside_val = .0;

    /* Open input vector */
    if ((mapset = G_find_vector2(in_opt->answer, "")) == NULL)
	G_fatal_error(_("Vector map <%s> not found"), in_opt->answer);

    Vect_set_open_level(2);	/* WITH TOPOLOGY */
    if (1 > Vect_open_old(&In, in_opt->answer, mapset))
	G_fatal_error(_("Unable to open vector map <%s> at the topological level"),
		      in_opt->answer);

    nareas = Vect_get_num_areas(&In);
    if (nareas == 0)
	G_fatal_error(_("No areas in input vector <%s>"), in_opt->answer);

    layer = Vect_get_field_number(&In, dfield_opt->answer);
    column = col_opt->answer;

    /* check availability of z values */
    if (withz_flag->answer && !Vect_is_3d(&In)) {
	G_fatal_error(_("Input vector is not 3D, can not use z coordinates"));
    }
    else if (!withz_flag->answer && (layer <= 0 || column == NULL))
	G_fatal_error(_("Option '%s' with z values or '-%c' flag must be given"),
                      col_opt->key, withz_flag->key);

    if (withz_flag->answer)
	layer = 0;

    /* raster output */
    out_fd = Rast_open_new(out_opt->answer, DCELL_TYPE);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    Rast_get_window(&window);

    /* Alloc raster matrix */
    seg_mb = atoi(memory_opt->answer);
    if (seg_mb < 3)
	G_fatal_error(_("Memory in MB must be >= 3"));

    seg_size = sizeof(struct lcell);

    seg_size = (seg_size * SEGSIZE * SEGSIZE) / (1 << 20);
    segments_in_memory = seg_mb / seg_size + 0.5;
    G_debug(1, "%d %dx%d segments held in memory", segments_in_memory, SEGSIZE, SEGSIZE);

    if (segment_open(&out_seg, G_tempfile(),
		     nrows, ncols, SEGSIZE, SEGSIZE,
		     sizeof(struct lcell), segments_in_memory) != 1)
	G_fatal_error(_("Can not create temporary file"));

    /* initialize */
    G_message(_("Initializing..."));

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    db_init_string(&dbstring);

    areas = G_malloc(sizeof(struct marea) * (nareas + 1));
    if (!areas)
	G_fatal_error(_("Out of memory"));

    G_message(_("Reading values..."));
    /* read values from attribute table or z */
    driver = NULL;
    if (layer > 0) {
	
	Fi = Vect_get_field(&In, layer);
	if (Fi == NULL)
	    G_fatal_error(_("Cannot read layer info"));

	driver = db_start_driver_open_database(Fi->driver, Fi->database);

	if (driver == NULL)
	    G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
			  Fi->database, Fi->driver);

	if (db_get_column(driver, Fi->table, column, &dbcolumn) != DB_OK) {
	    db_close_database_shutdown_driver(driver);
	    G_fatal_error(_("Unable to get column <%s>"), column);
	}
	sqltype = db_get_column_sqltype(dbcolumn);
	ctype = db_sqltype_to_Ctype(sqltype);
	
	if (ctype != DB_C_TYPE_INT && ctype != DB_C_TYPE_DOUBLE) {
	    db_close_database_shutdown_driver(driver);
	    G_fatal_error(_("Column <%s> must be numeric"), column);
	}
    }

    i = 0;
    areas[i].count = 0;
    areas[i].value = outside_val;
    areas[i].interp = 0;
    areas[i].adj = 0;
    areas[i].avgdiff = 0;

    for (i = 1; i <= nareas; i++) {

	areas[i].count = 0;
	areas[i].value = outside_val;
	areas[i].interp = 0;
	areas[i].adj = 0;
	areas[i].avgdiff = 0;

	if (driver) {
	    if (Vect_get_area_cats(&In, i, Cats) == 0) {
		int found = 0;

		value = .0;
		for (j = 0; j < Cats->n_cats; j++) {
		    if (Cats->field[j] != layer)
			continue;

		    G_rasprintf(&buf, &bufsize, "SELECT %s FROM %s WHERE %s = %d",
			        column, Fi->table, Fi->key, Cats->cat[j]);
		    db_set_string(&dbstring, buf);

		    if (db_open_select_cursor
				    (driver, &dbstring, &cursor, DB_SEQUENTIAL) != DB_OK) {
			db_close_database(driver);
			db_shutdown_driver(driver);
			G_fatal_error(_("Cannot select attributes for cat = %d"),
			              Cats->cat[j]);
		    }
		    if (db_fetch(&cursor, DB_NEXT, &more) != DB_OK) {
			db_close_database(driver);
			db_shutdown_driver(driver);
			G_fatal_error(_("Unable to fetch data from table"));
		    }

		    dbtable = db_get_cursor_table(&cursor);
		    dbcolumn = db_get_table_column(dbtable, 0);
		    dbvalue = db_get_column_value(dbcolumn);

		    if (!db_test_value_isnull(dbvalue)) {
			switch (ctype) {
			case DB_C_TYPE_INT: {
			    value += db_get_value_int(dbvalue);
			    break;
			    }
			case DB_C_TYPE_DOUBLE: {
			    value += db_get_value_double(dbvalue);
			    break;
			    }
			}
			found = 1;
		    }
		    db_close_cursor(&cursor);
		}
		
		G_debug(1, "value from table: %g", value);
		
		if (found)
		    areas[i].value = value;
	    }
	}
	else {
	    int centroid = 0;
	    
	    centroid = Vect_get_area_centroid(&In, i);
	    
	    if (centroid > 0) {
		Vect_read_line(&In, Points, Cats, centroid);
		areas[i].value = Points->z[0];
	    }
	}
    }

    if (driver)
	db_close_database_shutdown_driver(driver);

    G_message(_("Find area id for each cell"));
    for (row = 0; row < nrows; row++) {
	double x, y;

	G_percent(row, nrows, 2);

	y = Rast_row_to_northing(row + 0.5, &window);

	for (col = 0; col < ncols; col++) {
	    
	    x = Rast_col_to_easting(col + 0.5, &window);
	    
	    value = outside_val;
	    thiscell.interp = value;
	    thiscell.adj = 0.0;
	    thiscell.area = Vect_find_area(&In, x, y);

	    if (thiscell.area > 0) {
		thiscell.interp = areas[thiscell.area].value;
		areas[thiscell.area].count++;
	    }

	    segment_put(&out_seg, &thiscell, row, col);
	}
    }
    G_percent(row, nrows, 2);
    Vect_close(&In);

    G_message(_("Adjust cell values"));
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);
	for (col = 0; col < ncols; col++) {

	    segment_get(&out_seg, &thiscell, row, col);
	    if (areas[thiscell.area].count > 0 &&
	        !Rast_is_d_null_value(&thiscell.interp)) {

		value = thiscell.interp / areas[thiscell.area].count;
		thiscell.interp = value;
		segment_put(&out_seg, &thiscell, row, col);
	    }
	}
    }
    G_percent(row, nrows, 2);
    
    G_message(_("Mass-preserving interpolation"));
    doit = 1;
    iter = 0;
    while (doit) {
	int l_row = -1, l_col = -1;
	maxadj = 0;
	iter++;

	G_message(_("Pass %d"), iter);
	
	for (i = 1; i <= nareas; i++) {
	    areas[i].interp = .0;
	    areas[i].adj = .0;
	    areas[i].avgdiff = .0;
	    
	}
	/* Step 1 */
	for (row = 0; row < nrows; row++) {
	    G_percent(row, nrows, 2);
	    for (col = 0; col < ncols; col++) {
		int count = 0;

		value = .0;
		interp = .0;

		for (rrow = -1; rrow < 2; rrow++) {
		    nrow = row + rrow;
		    for (ccol = -1; ccol < 2; ccol++) {
			ncol = col + ccol;
			if (nrow >= 0 && nrow < nrows &&
			    ncol >= 0 && ncol < ncols) {
			    
			    if (nrow == row && ncol == col)
				continue;

			    segment_get(&out_seg, &thiscell, nrow, ncol);
			    if (!Rast_is_d_null_value(&thiscell.interp)) {
				value += thiscell.interp;
				count++;
			    }
			}
		    }
		}
		if (count) {
		    segment_get(&out_seg, &thiscell, row, col);

		    if (!Rast_is_d_null_value(&thiscell.interp)) {
			value /= count;
			value -= thiscell.interp;
			/* relax */
			/* value /= 8; */
			thiscell.adj = value;
			if (thiscell.area && !negative &&
			    areas[thiscell.area].value == 0) {

			    thiscell.adj = 0;
			}
			segment_put(&out_seg, &thiscell, row, col);
			if (thiscell.area)
			    areas[thiscell.area].adj += value;

		    }
		}
	    }	
	}
	G_percent(row, nrows, 2);

	/* Step 2 */
	for (i = 1; i <= nareas; i++) {
	    if (areas[i].count)
		areas[i].adj = -areas[i].adj / areas[i].count;
	    areas[i].interp = 0;
	    areas[i].avgdiff = 0;
	    areas[i].count_neg = 0;
	}

	/* Step 3 */
	for (row = 0; row < nrows; row++) {
	    G_percent(row, nrows, 2);
	    for (col = 0; col < ncols; col++) {
		segment_get(&out_seg, &thiscell, row, col);
		if (!Rast_is_d_null_value(&thiscell.interp)) {

		    interp = thiscell.interp + thiscell.adj + areas[thiscell.area].adj;
		    if (negative || (!negative && interp >= 0)) {
			thiscell.interp = interp;

			segment_put(&out_seg, &thiscell, row, col);

			value = thiscell.adj + areas[thiscell.area].adj;
			if (maxadj < value * value) {
			    maxadj = value * value;
			    l_row = row;
			    l_col = col;
			}
		    }
		    if (!negative && interp < 0)
			have_neg = 1;

		    if (thiscell.area) {
			areas[thiscell.area].interp += thiscell.interp;
		    }
		}
	    }
	}
	G_percent(row, nrows, 2);

	/* Step 4 */
	for (i = 1; i <= nareas; i++) {
	    areas[i].avgdiff = (areas[i].value - areas[i].interp) / 
	                       areas[i].count;
	    G_debug(3, "Area %d difference: %g", i, areas[i].value - areas[i].interp);
	}

	/* Step 5 */
	for (row = 0; row < nrows; row++) {
	    G_percent(row, nrows, 2);
	    for (col = 0; col < ncols; col++) {
		segment_get(&out_seg, &thiscell, row, col);
		if (!Rast_is_d_null_value(&thiscell.interp)) {

		    interp = thiscell.interp + areas[thiscell.area].avgdiff;
		    if (!negative && interp < 0) {
			areas[thiscell.area].count_neg++;
		    }
		}
	    }
	}
	G_percent(row, nrows, 2);

	for (row = 0; row < nrows; row++) {
	    G_percent(row, nrows, 2);
	    for (col = 0; col < ncols; col++) {
		segment_get(&out_seg, &thiscell, row, col);
		if (!Rast_is_d_null_value(&thiscell.interp)) {
		    
		    avgdiff = areas[thiscell.area].avgdiff;

		    interp = thiscell.interp + avgdiff;
		    if (negative || (!negative && interp >= 0)) {
			if (areas[thiscell.area].count_neg > 0) {

			    if (areas[thiscell.area].count > areas[thiscell.area].count_neg) {
				avgdiff = avgdiff * areas[thiscell.area].count / 
					  (areas[thiscell.area].count - areas[thiscell.area].count_neg);

				interp = thiscell.interp + avgdiff;
			    }
			}

			if (negative || (!negative && interp >= 0))
			    thiscell.interp = interp;
		    }
		    segment_put(&out_seg, &thiscell, row, col);
		}
	    }
	}
	G_percent(row, nrows, 2);

	G_verbose_message(_("Largest squared adjustment: %g"), maxadj);
	G_verbose_message(_("Largest row, col: %d %d"), l_row, l_col);
	if (iter >= maxiter || maxadj < threshold)
	    doit = 0;
    }

    /* write output */
    G_message(_("Writing output <%s>"), out_opt->answer);
    drastbuf = Rast_allocate_d_buf();
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);
	for (col = 0; col < ncols; col++) {
	    segment_get(&out_seg, &thiscell, row, col);
	    drastbuf[col] = thiscell.interp;
	}
	Rast_put_d_row(out_fd, drastbuf);
    }
    G_percent(row, nrows, 2);

    Rast_close(out_fd);
    Rast_short_history(out_opt->answer, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(out_opt->answer, &history);

    G_done_msg(" ");

    exit(EXIT_SUCCESS);
}
