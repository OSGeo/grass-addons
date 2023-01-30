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

/* activate to use the original algorithm of Tobler 1979
#define TOBLER_STRICT
*/

int main(int argc, char *argv[])
{
    const char *mapset, *column;
    int row, col, nrows, ncols, rrow, ccol, nrow, ncol;
    int r1, r2, c1, c2;
    int nsize, rlo, rhi;

    SEGMENT out_seg;
    int srows, scols;
    int w_fd, out_fd, have_weights;
    DCELL *drastbuf;
    double seg_size;
    int seg_mb, segments_in_memory;
    int doit, iter, maxiter;
    double threshold, maxadj;
    int negative = 0;

    int layer;
    int i, j, nareas;
    struct marea *areas, *ap;
    struct bound_box abox, *ibox;

    struct Map_info In;
    struct line_pnts *Points, **IPoints;
    int n_isles, isl_allocated;
    struct line_cats *Cats;
    struct Cell_head window;
    struct History history;

    struct lcell thiscell, ngbrcell;
    double outside_val, interp, value;

#ifdef TOBLER_STRICT
    double avgdiff;
#endif

    struct GModule *module;
    struct Option *in_opt, *w_opt, *out_opt, *dfield_opt, *col_opt, *memory_opt,
        *iter_opt, *threshold_opt;
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
    module->description = _("Performs mass-preserving area interpolation.");

    in_opt = G_define_standard_option(G_OPT_V_INPUT);
    in_opt->label = _("Name of input vector point map");

    w_opt = G_define_standard_option(G_OPT_R_INPUT);
    w_opt->label = _("Name of optional weighing raster map");
    w_opt->key = "weight";
    w_opt->required = NO;

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
    iter_opt->description = _("Maximum number of iterations");

    threshold_opt = G_define_option();
    threshold_opt->key = "threshold";
    threshold_opt->type = TYPE_DOUBLE;
    threshold_opt->answer = "1e-8";
    threshold_opt->required = NO;
    threshold_opt->description = _("Threshold for iterations");

    memory_opt = G_define_option();
    memory_opt->key = "memory";
    memory_opt->type = TYPE_INTEGER;
    memory_opt->required = NO;
    memory_opt->answer = "300";
    memory_opt->description =
        _("Maximum memory to be used for raster output (in MB)");

    withz_flag = G_define_flag();
    withz_flag->key = 'z';
    withz_flag->description =
        _("Use centroid z coordinates for approximation (3D vector maps only)");
    withz_flag->guisection = _("Settings");

    G_gisinit(argv[0]);
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    maxiter = atoi(iter_opt->answer);
    threshold = atof(threshold_opt->answer);

    /* boundary condition:
     * ignore outside or treat outside as zero */
    /* outside_val = .0; */
    Rast_set_d_null_value(&outside_val, 1);

    /* Open input vector */
    if ((mapset = G_find_vector2(in_opt->answer, "")) == NULL)
        G_fatal_error(_("Vector map <%s> not found"), in_opt->answer);

    Vect_set_open_level(2); /* WITH TOPOLOGY */
    if (1 > Vect_open_old(&In, in_opt->answer, mapset))
        G_fatal_error(
            _("Unable to open vector map <%s> at the topological level"),
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
        G_fatal_error(
            _("Option '%s' with z values or '-%c' flag must be given"),
            col_opt->key, withz_flag->key);

    if (withz_flag->answer)
        layer = 0;

    /* input weights */
    w_fd = -1;
    have_weights = 0;
    drastbuf = NULL;
    if (w_opt->answer) {
        char *mapset = (char *)G_find_raster2(w_opt->answer, "");

        if (mapset == NULL)
            G_fatal_error(_("Raster map <%s> not found"), w_opt->answer);

        have_weights = 1;
        w_fd = Rast_open_old(w_opt->answer, "");
        drastbuf = Rast_allocate_d_buf();
    }

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

    srows = 64;
    scols = 64;
    seg_size = (seg_size * srows * scols) / (1 << 20);
    segments_in_memory = seg_mb / seg_size + 0.5;
    if (segments_in_memory < 3)
        segments_in_memory = 3;
    G_debug(1, "%d %dx%d segments held in memory", segments_in_memory, srows,
            scols);

    /* initialize */
    G_message(_("Initializing..."));

    if (Segment_open(&out_seg, G_tempfile(), nrows, ncols, srows, scols,
                     sizeof(struct lcell), segments_in_memory) != 1)
        G_fatal_error(_("Can not create temporary file"));

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    db_init_string(&dbstring);

    areas = G_malloc(sizeof(struct marea) * (nareas + 1));
    if (!areas)
        G_fatal_error(_("Out of memory"));

    G_message(_("Reading area values..."));
    /* read values from attribute table or z */
    driver = NULL;
    Fi = NULL;
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
    areas[i].weight = 0;

    G_debug(1, "Starting to read from areas...");
    G_percent(0, nareas, 2);
    for (i = 1; i <= nareas; i++) {

        G_percent(i, nareas, 2);
        areas[i].count = 0;
        areas[i].value = outside_val;
        areas[i].interp = 0;
        areas[i].adj = 0;
        areas[i].avgdiff = 0;
        areas[i].weight = 0;

        if (driver) {
            if (Vect_get_area_cats(&In, i, Cats) == 0) {
                int found = 0;

                value = .0;
                for (j = 0; j < Cats->n_cats; j++) {
                    if (Cats->field[j] != layer)
                        continue;

                    G_rasprintf(&buf, &bufsize,
                                "SELECT %s FROM %s WHERE %s = %d", column,
                                Fi->table, Fi->key, Cats->cat[j]);
                    db_set_string(&dbstring, buf);

                    if (db_open_select_cursor(driver, &dbstring, &cursor,
                                              DB_SEQUENTIAL) != DB_OK) {
                        db_close_database(driver);
                        db_shutdown_driver(driver);
                        G_fatal_error(
                            _("Cannot select attributes for cat = %d"),
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

    G_message(_("Initialize output"));
    for (row = 0; row < nrows; row++) {

        G_percent(row, nrows, 2);

        if (have_weights)
            Rast_get_d_row(w_fd, drastbuf, row);

        for (col = 0; col < ncols; col++) {
            thiscell.interp = outside_val;
            thiscell.adj = 0.0;
            thiscell.area = 0;
            thiscell.weight = 1.;
            if (have_weights) {
                if (Rast_is_d_null_value(&drastbuf[col])) {
                    thiscell.weight = 0; /* OK ? was drastbuf[col] */
                }
                else {
                    thiscell.weight = drastbuf[col];
                    if (thiscell.weight < 0) {
                        G_warning(_("Weight is negative at row %d, col %d, "
                                    "using 0 instead"),
                                  row, col);
                        thiscell.weight = 0;
                    }
                }
            }
            Segment_put(&out_seg, &thiscell, row, col);
        }
    }
    G_percent(row, nrows, 2);

    G_message(_("Set area id for each cell"));
    IPoints = NULL;
    ibox = NULL;
    isl_allocated = 0;
    G_percent(0, nareas, 2);
    for (i = 1; i <= nareas; i++) {
        double x, y;
        int inside = 0;

        G_percent(i, nareas, 2);
        if (Rast_is_d_null_value(&areas[i].value))
            continue;
        Vect_get_area_box(&In, i, &abox);
        if (abox.N < window.south || abox.S > window.north ||
            abox.E < window.west || abox.W > window.east)
            continue;

        r1 = floor(Rast_northing_to_row(abox.N, &window));
        r2 = floor(Rast_northing_to_row(abox.S, &window)) + 1;
        c1 = floor(Rast_easting_to_col(abox.W, &window));
        c2 = floor(Rast_easting_to_col(abox.E, &window)) + 1;

        if (r1 < 0)
            r1 = 0;
        if (r2 > nrows)
            r2 = nrows;
        if (c1 < 0)
            c1 = 0;
        if (c2 > ncols)
            c2 = ncols;

        if (r2 < r1 || c2 < c1)
            continue;

        /* like Vect_point_in_area() */
        Vect_get_area_points(&In, i, Points);
        n_isles = Vect_get_area_num_isles(&In, i);
        if (n_isles > isl_allocated) {
            IPoints = (struct line_pnts **)G_realloc(
                IPoints, (1 + n_isles) * sizeof(struct line_pnts *));
            for (j = isl_allocated; j < n_isles; j++)
                IPoints[j] = Vect_new_line_struct();
            isl_allocated = n_isles;
            ibox = (struct bound_box *)G_realloc(
                ibox, (1 + n_isles) * sizeof(struct bound_box));
        }
        for (j = 0; j < n_isles; j++) {
            Vect_get_isle_points(&In, Vect_get_area_isle(&In, i, j),
                                 IPoints[j]);
            Vect_get_isle_box(&In, Vect_get_area_isle(&In, i, j), &ibox[j]);
            ibox[j].T = ibox[j].B = 0;
        }

        for (row = r1; row < r2; row++) {
            y = Rast_row_to_northing(row + 0.5, &window);
            for (col = c1; col < c2; col++) {
                x = Rast_col_to_easting(col + 0.5, &window);

                inside = Vect_point_in_poly(x, y, Points) > 0;
                if (inside) {
                    for (j = 0; j < n_isles; j++) {
                        if (Vect_point_in_box(x, y, 0, &ibox[j]) &&
                            Vect_point_in_poly(x, y, IPoints[j]) > 0) {
                            inside = 0;
                            break;
                        }
                    }
                }
                if (inside) {
                    Segment_get(&out_seg, &thiscell, row, col);
                    if (!Rast_is_d_null_value(&thiscell.weight)) {
                        thiscell.area = i;
                        ap = &areas[thiscell.area];
                        thiscell.interp = ap->value;
                        ap->count++;
                        if (have_weights) {
                            thiscell.interp *= thiscell.weight;
                            ap->interp += thiscell.weight;
                        }
                        if (ap->weight == 0)
                            ap->weight = thiscell.weight != 0.0;
                        Segment_put(&out_seg, &thiscell, row, col);
                    }
                }
            }
        }
    }

    Vect_set_release_support(&In);
    Vect_close(&In);

    if (have_weights) {
        G_free(drastbuf);
        Rast_close(w_fd);
    }

    G_message(_("Adjust cell values"));
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);
        for (col = 0; col < ncols; col++) {

            Segment_get(&out_seg, &thiscell, row, col);
            if (areas[thiscell.area].count > 0 &&
                !Rast_is_d_null_value(&thiscell.interp)) {

                ap = &areas[thiscell.area];
                value = thiscell.interp / ap->count;
                if (have_weights) {
                    if (ap->weight == 0) {
                        thiscell.weight = 1;
                        value = ap->value / ap->count;
                    }
                    else {
                        if (ap->interp > 0)
                            value = thiscell.interp / ap->interp;
                    }
                }
                thiscell.interp = value;
            }
            if (areas[thiscell.area].count == 0)
                thiscell.interp = outside_val;
            Segment_put(&out_seg, &thiscell, row, col);
        }
    }
    G_percent(row, nrows, 2);

    G_message(_("Mass-preserving interpolation"));
    doit = 1;
    iter = 0;
    nsize = 1;
    rlo = -nsize;
    rhi = nsize + 1;
    while (doit) {
        int l_row = -1, l_col = -1;
        maxadj = 0;
        G_percent(iter, maxiter, 1);
        iter++;

        if (have_weights && iter > 1 && iter == maxiter) {
            for (i = 1; i <= nareas; i++) {
                areas[i].interp = .0;
                areas[i].adj = .0;
                areas[i].avgdiff = .0;
                areas[i].count_neg = 0;
            }

            for (row = 0; row < nrows; row++) {
                for (col = 0; col < ncols; col++) {
                    Segment_get(&out_seg, &thiscell, row, col);
                    if (thiscell.area > 0 &&
                        !Rast_is_d_null_value(&thiscell.interp)) {

                        ap = &areas[thiscell.area];
                        thiscell.interp *= thiscell.weight;
                        ap->interp += thiscell.interp;
                        Segment_put(&out_seg, &thiscell, row, col);
                    }
                }
            }
            for (row = 0; row < nrows; row++) {
                for (col = 0; col < ncols; col++) {
                    Segment_get(&out_seg, &thiscell, row, col);
                    if (thiscell.area > 0 &&
                        !Rast_is_d_null_value(&thiscell.interp)) {

                        value = 1;
                        ap = &areas[thiscell.area];
                        if (ap->interp != 0)
                            value = ap->value / ap->interp;
                        thiscell.interp = value * thiscell.interp;
                        Segment_put(&out_seg, &thiscell, row, col);
                    }
                }
            }
        }

        for (i = 1; i <= nareas; i++) {
            areas[i].interp = .0;
            areas[i].adj = .0;
            areas[i].avgdiff = .0;
            areas[i].count_neg = 0;
        }

        /* Step 1 */
        for (row = 0; row < nrows; row++) {
            for (col = 0; col < ncols; col++) {
                int count = 0;

                Segment_get(&out_seg, &thiscell, row, col);
                if (thiscell.area == 0 ||
                    Rast_is_d_null_value(&thiscell.interp))
                    continue;

                value = .0;

                for (rrow = rlo; rrow < rhi; rrow++) {
                    nrow = row + rrow;
                    for (ccol = rlo; ccol < rhi; ccol++) {
                        ncol = col + ccol;
                        if (nrow >= 0 && nrow < nrows && ncol >= 0 &&
                            ncol < ncols) {

                            if (nrow == row && ncol == col)
                                continue;

                            Segment_get(&out_seg, &ngbrcell, nrow, ncol);
                            if (!Rast_is_d_null_value(&ngbrcell.interp)) {
                                value += ngbrcell.interp;
                                count++;
                            }
                        }
                    }
                }
                if (count != 0) {
                    value /= count;
                    value -= thiscell.interp;
                    /* relax */
                    /* value /= 8; */
                    thiscell.adj = value;
                    if (!negative) {
                        if (areas[thiscell.area].value == 0)
                            thiscell.adj = 0;
                        if (thiscell.interp + thiscell.adj < 0)
                            thiscell.adj = -thiscell.interp;
                    }
                    Segment_put(&out_seg, &thiscell, row, col);

                    areas[thiscell.area].adj += thiscell.adj;
                    areas[thiscell.area].interp +=
                        thiscell.interp + thiscell.adj;
                }
                else {
                    areas[thiscell.area].interp += thiscell.interp;
                }
            }
        }

#ifdef TOBLER_STRICT
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
            for (col = 0; col < ncols; col++) {
                Segment_get(&out_seg, &thiscell, row, col);
                if (thiscell.area > 0 &&
                    !Rast_is_d_null_value(&thiscell.interp)) {

                    interp = thiscell.interp + thiscell.adj +
                             areas[thiscell.area].adj;
                    if (negative || (!negative && interp >= 0)) {
                        thiscell.interp = interp;

                        Segment_put(&out_seg, &thiscell, row, col);

                        value = thiscell.adj + areas[thiscell.area].adj;
                        if (maxadj < value * value) {
                            maxadj = value * value;
                            l_row = row;
                            l_col = col;
                        }
                    }
                    areas[thiscell.area].interp += thiscell.interp;
                }
            }
        }

        /* Step 4 */
        for (i = 1; i <= nareas; i++) {
            if (areas[i].count > 0) {
                areas[i].avgdiff =
                    (areas[i].value - areas[i].interp) / areas[i].count;
                G_debug(3, "Area %d difference: %g", i,
                        areas[i].value - areas[i].interp);
            }
        }

        /* Step 5 */
        for (row = 0; row < nrows; row++) {
            for (col = 0; col < ncols; col++) {
                Segment_get(&out_seg, &thiscell, row, col);
                if (thiscell.area > 0 &&
                    !Rast_is_d_null_value(&thiscell.interp)) {

                    interp = thiscell.interp + areas[thiscell.area].avgdiff;
                    if (!negative && interp < 0) {
                        areas[thiscell.area].count_neg++;
                    }
                }
            }
        }

        for (row = 0; row < nrows; row++) {
            for (col = 0; col < ncols; col++) {
                Segment_get(&out_seg, &thiscell, row, col);
                if (thiscell.area > 0 &&
                    !Rast_is_d_null_value(&thiscell.interp)) {

                    avgdiff = areas[thiscell.area].avgdiff;

                    interp = thiscell.interp + avgdiff;
                    if (negative || (!negative && interp >= 0)) {
                        if (areas[thiscell.area].count_neg > 0) {

                            if (areas[thiscell.area].count >
                                areas[thiscell.area].count_neg) {
                                avgdiff = avgdiff * areas[thiscell.area].count /
                                          (areas[thiscell.area].count -
                                           areas[thiscell.area].count_neg);

                                interp = thiscell.interp + avgdiff;
                            }
                        }

                        if (negative || (!negative && interp >= 0))
                            thiscell.interp = interp;
                    }
                    Segment_put(&out_seg, &thiscell, row, col);
                }
            }
        }
#else
        /* deviation from Tobler 1979: less steps, faster convergence */

        /* Step 2 */
        for (row = 0; row < nrows; row++) {
            for (col = 0; col < ncols; col++) {
                Segment_get(&out_seg, &thiscell, row, col);
                if (thiscell.area > 0 &&
                    !Rast_is_d_null_value(&thiscell.interp)) {
                    /* multiplication with area scale factor */
                    value = 1;
                    ap = &areas[thiscell.area];
                    if (ap->interp != 0)
                        value = ap->value / ap->interp;

                    if (ap->interp == 0 && ap->value != 0)
                        interp = ap->value / ap->count;
                    else
                        interp = value * (thiscell.interp + thiscell.adj);

                    if (negative || (!negative && interp >= 0)) {
                        value = thiscell.interp - interp;
                        thiscell.interp = interp;
                        Segment_put(&out_seg, &thiscell, row, col);

                        if (maxadj < value * value) {
                            maxadj = value * value;
                            l_row = row;
                            l_col = col;
                        }
                    }
                }
            }
        }
#endif

        G_verbose_message(_("Largest squared adjustment: %g"), maxadj);
        G_verbose_message(_("Largest row, col: %d %d"), l_row, l_col);
        if (iter >= maxiter)
            doit = 0;
        if (maxadj < threshold) {
            if (have_weights)
                maxiter = iter + 1;
            else
                doit = 0;
            G_verbose_message(_("Interpolation converged after %d iterations"),
                              iter);
        }
    }
    G_percent(maxiter, maxiter, 1);

    /* write output */
    G_message(_("Writing output <%s>"), out_opt->answer);
    drastbuf = Rast_allocate_d_buf();
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);
        for (col = 0; col < ncols; col++) {
            Segment_get(&out_seg, &thiscell, row, col);
            drastbuf[col] = thiscell.interp;
        }
        Rast_put_d_row(out_fd, drastbuf);
    }
    G_percent(row, nrows, 2);

    Segment_close(&out_seg);

    Rast_close(out_fd);
    Rast_short_history(out_opt->answer, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(out_opt->answer, &history);

    G_done_msg(" ");

    exit(EXIT_SUCCESS);
}
