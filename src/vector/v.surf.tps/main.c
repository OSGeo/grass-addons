/**********************************************************************
 *
 * MODULE:       v.surf.tps
 *
 * AUTHOR(S):    Markus Metz
 *
 * PURPOSE:      Thin Plate Spline interpolation with covariables
 *
 * COPYRIGHT:    (C) 2016 by by the GRASS Development Team
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
#include <grass/raster.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include "tps.h"

static int cmp_pnts(const void *a, const void *b)
{
    struct tps_pnt *aa = (struct tps_pnt *)a;
    struct tps_pnt *bb = (struct tps_pnt *)b;

    if (aa->r == bb->r)
        return (aa->c - bb->c);

    return (aa->r - bb->r);
}

int main(int argc, char *argv[])
{
    int i, j;
    const char *mapset, *outname;
    int out_fd, mask_fd;

    struct Map_info In;
    struct History history;

    struct GModule *module;
    struct Option *in_opt, *var_opt, *out_opt, *minpnts_opt, *thin_opt,
        *reg_opt, *ov_opt, *dfield_opt, *col_opt, *mask_opt, *mem_opt;
    struct Flag *c_flag;
    struct Cell_head dstwindow;

    int cur_row;
    int n_vars;
    int n_points, min_points;
    int use_z;
    int cat;
    int val_field;
    char *val_column;
    double val;
    struct field_info *Fi;
    dbDriver *driver;
    dbColumn *dbcolumn;
    dbValue dbval;
    int sqltype = 0, ctype = 0;

    struct line_pnts *Points;
    struct line_cats *Cats;
    struct tps_pnt *pnts;
    int type, cnt;
    double valsum;
    int r, c, nrows, ncols;
    int *var_fd;
    DCELL **dbuf;
    double regularization, overlap;
    double pthin;
    int segs_mb;

    /*----------------------------------------------------------------*/
    /* Options declarations */
    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("surface"));
    G_add_keyword(_("interpolation"));
    G_add_keyword(_("TPS"));
    module->description = _("Performs thin plate spline interpolation with "
                            "regularization and covariables.");

    in_opt = G_define_standard_option(G_OPT_V_INPUT);
    in_opt->label = _("Name of input vector point map");

    dfield_opt = G_define_standard_option(G_OPT_V_FIELD);
    dfield_opt->guisection = _("Settings");

    col_opt = G_define_standard_option(G_OPT_DB_COLUMN);
    col_opt->required = NO;
    col_opt->label = _("Name of the attribute column with values to be used "
                       "for interpolation");
    col_opt->description = _("If not given, z-coordinates are used.");
    col_opt->guisection = _("Settings");

    reg_opt = G_define_option();
    reg_opt->key = "smooth";
    reg_opt->type = TYPE_DOUBLE;
    reg_opt->required = NO;
    reg_opt->answer = "0";
    reg_opt->description = _("Smoothing factor");
    reg_opt->guisection = _("Settings");

    ov_opt = G_define_option();
    ov_opt->key = "overlap";
    ov_opt->type = TYPE_DOUBLE;
    ov_opt->required = NO;
    ov_opt->answer = "0.1";
    ov_opt->label = _("Overlap factor <= 1");
    ov_opt->description = _("A larger value increase the tile overlap");
    ov_opt->guisection = _("Settings");

    minpnts_opt = G_define_option();
    minpnts_opt->key = "min";
    minpnts_opt->type = TYPE_DOUBLE;
    minpnts_opt->required = NO;
    minpnts_opt->answer = "20";
    minpnts_opt->description =
        _("Minimum number of points to use for TPS interpolation");
    minpnts_opt->guisection = _("Settings");

    var_opt = G_define_standard_option(G_OPT_R_INPUTS);
    var_opt->key = "covars";
    var_opt->required = NO;
    var_opt->label = _("Name of input raster map(s) to use as covariables");
    var_opt->guisection = _("Settings");

    thin_opt = G_define_option();
    thin_opt->key = "thin";
    thin_opt->type = TYPE_DOUBLE;
    thin_opt->required = NO;
    thin_opt->answer = "1.5";
    thin_opt->label = _(
        "Point cloud thinning factor in number of cells of the current region");
    thin_opt->description = _("Minimum distance between neighboring points for "
                              "local TPS interpolation");
    minpnts_opt->guisection = _("Settings");

    out_opt = G_define_standard_option(G_OPT_R_OUTPUT);
    out_opt->key = "output";
    out_opt->required = YES;

    mask_opt = G_define_standard_option(G_OPT_R_INPUT);
    mask_opt->key = "mask";
    mask_opt->label = _("Raster map to use for masking");
    mask_opt->description =
        _("Only cells that are not NULL and not zero are interpolated");
    mask_opt->required = NO;

    mem_opt = G_define_option();
    mem_opt->key = "memory";
    mem_opt->type = TYPE_INTEGER;
    mem_opt->required = NO;
    mem_opt->answer = "300";
    mem_opt->description = _("Memory in MB");

    c_flag = G_define_flag();
    c_flag->key = 'c';
    c_flag->description =
        _("Input points are dense clusters separated by empty areas");

    /* Parsing */
    G_gisinit(argv[0]);
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    outname = out_opt->answer;

    /* open input vector without topology */
    if ((mapset = G_find_vector2(in_opt->answer, "")) == NULL)
        G_fatal_error(_("Vector map <%s> not found"), in_opt->answer);

    Vect_set_open_level(1); /* WITHOUT TOPOLOGY */
    if (1 > Vect_open_old(&In, in_opt->answer, mapset))
        G_fatal_error(_("Unable to open vector map <%s>"), in_opt->answer);

    val_field = 0; /* assume 3D input */
    val_column = col_opt->answer;

    use_z = !val_column && Vect_is_3d(&In);

    if (Vect_is_3d(&In)) {
        if (!use_z)
            G_verbose_message(_("Input is 3D: using attribute values instead "
                                "of z-coordinates for approximation"));
        else
            G_verbose_message(
                _("Input is 3D: using z-coordinates for approximation"));
    }
    else { /* 2D */
        if (!val_column)
            G_fatal_error(_("Input vector map is 2D. Parameter <%s> required."),
                          col_opt->key);
    }

    if (!use_z) {
        val_field = Vect_get_field_number(&In, dfield_opt->answer);
    }

    n_vars = 0;
    if (var_opt->answer) {
        while (var_opt->answers[n_vars])
            n_vars++;
    }

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    Rast_get_window(&dstwindow);
    nrows = dstwindow.rows;
    ncols = dstwindow.cols;

    /* count points */
    Vect_rewind(&In);
    n_points = 0;
    while (1) {
        /* register line */
        type = Vect_read_next_line(&In, Points, Cats);

        /* Note: check for dead lines is not needed, because they are skipped by
         * V1_read_next_line_nat() */
        if (type == -1) {
            G_fatal_error(_("Unable to read vector map"));
        }
        else if (type == -2) {
            break;
        }

        if (type & GV_POINTS) {
            n_points++;

            if (n_vars) {
                r = (dstwindow.north - Points->y[0]) / dstwindow.ns_res;
                c = (Points->x[0] - dstwindow.west) / dstwindow.ew_res;

                if (r < 0 || r >= nrows || c < 0 || c >= ncols)
                    n_points--;
            }
        }
    }
    if (!n_points)
        G_fatal_error(_("No points in input vector <%s>"), in_opt->answer);

    /* check memory */
    pnts = G_malloc(n_points * sizeof(struct tps_pnt));
    if (!pnts)
        G_fatal_error(_("Too many points, out of memory"));

    if (n_vars) {
        pnts[0].vars = G_malloc(sizeof(double) * n_points * n_vars);
        if (!pnts[0].vars)
            G_fatal_error(_("Too many points, out of memory"));
        G_free(pnts[0].vars);
    }

    /* load points */
    driver = NULL;
    Fi = NULL;
    ctype = 0;
    if (!use_z) {
        Fi = Vect_get_field(&In, val_field);
        if (Fi == NULL)
            G_fatal_error(_("Cannot read layer info"));

        driver = db_start_driver_open_database(Fi->driver, Fi->database);

        if (db_get_column(driver, Fi->table, val_column, &dbcolumn) != DB_OK) {
            db_close_database_shutdown_driver(driver);
            G_fatal_error(_("Unable to get column <%s>"), val_column);
        }
        sqltype = db_get_column_sqltype(dbcolumn);
        ctype = db_sqltype_to_Ctype(sqltype);

        if (ctype != DB_C_TYPE_INT && ctype != DB_C_TYPE_DOUBLE) {
            db_close_database_shutdown_driver(driver);
            G_fatal_error(_("Column <%s> must be numeric"), val_column);
        }
    }

    G_message(_("Loading %d points..."), n_points);
    Vect_rewind(&In);
    i = 0;
    j = 0;
    while (1) {

        i++;

        /* register line */
        type = Vect_read_next_line(&In, Points, Cats);

        /* Note: check for dead lines is not needed, because they are skipped by
         * V1_read_next_line_nat() */
        if (type == -1) {
            G_fatal_error(_("Unable to read vector map"));
        }
        else if (type == -2) {
            break;
        }

        if (!(type & GV_POINTS))
            continue;

        Rast_set_d_null_value(&val, 1);
        if (driver) {
            if (!Vect_cat_get(Cats, val_field, &cat))
                G_fatal_error(_("No category for point %d in layer %d"), i,
                              val_field);

            db_select_value(driver, Fi->table, Fi->key, cat, val_column,
                            &dbval);
            switch (ctype) {
            case DB_C_TYPE_INT: {
                val = db_get_value_int(&dbval);
                break;
            }
            case DB_C_TYPE_DOUBLE: {
                val = db_get_value_double(&dbval);
                break;
            }
            default: {
                Rast_set_d_null_value(&val, 1);
                break;
            }
            }
        }
        else {
            val = Points->z[0];
        }
        r = pnts[j].r = (dstwindow.north - Points->y[0]) / dstwindow.ns_res;
        c = pnts[j].c = (Points->x[0] - dstwindow.west) / dstwindow.ew_res;

        if (n_vars && (r < 0 || r >= nrows || c < 0 || c >= ncols)) {
            Rast_set_d_null_value(&val, 1);
        }

        if (!Rast_is_d_null_value(&val)) {
            /* add point */
            G_percent(j, n_points, 4);

            pnts[j].val = val;
            j++;
        }
    }
    G_percent(1, 1, 1);

    if (driver)
        db_close_database_shutdown_driver(driver);
    Vect_close(&In);

    if (j != n_points)
        n_points = j;

    /* sort points */
    qsort(pnts, n_points, sizeof(struct tps_pnt), cmp_pnts);

    /* combine duplicates */
    valsum = pnts[0].val;
    cnt = 1;
    j = 1;
    for (i = 1; i < n_points; i++) {
        if (pnts[i - 1].r == pnts[i].r && pnts[i - 1].c == pnts[i].c) {
            valsum += pnts[i].val;
            cnt++;
        }
        else {
            if (cnt > 1) {
                pnts[j - 1].val = valsum / cnt;
                valsum = pnts[i].val;
                cnt = 1;
            }
            pnts[j].r = pnts[i].r;
            pnts[j].c = pnts[i].c;
            pnts[j].val = pnts[i].val;
            j++;
        }
    }
    if (j != n_points) {
        G_verbose_message(_("%d duplicate points pruned"), n_points - j);
        n_points = j;
    }

    if (n_vars) {
        pnts[0].vars = G_malloc(sizeof(double) * n_points * n_vars);
        if (!pnts[0].vars)
            G_fatal_error(_("Too many points, out of memory"));

        for (i = 1; i < n_points; i++)
            pnts[i].vars = pnts[i - 1].vars + n_vars;
    }

    /* load covariables */
    var_fd = NULL;
    dbuf = NULL;
    if (n_vars) {
        int ii, isnull;

        G_message(_("Loading %d covariables..."), n_vars);

        cur_row = -1;

        var_fd = G_malloc(n_vars * sizeof(int));
        dbuf = G_malloc(n_vars * sizeof(DCELL *));
        for (i = 0; var_opt->answers[i]; i++) {
            var_fd[i] = Rast_open_old(var_opt->answers[i], "");
            dbuf[i] = Rast_allocate_d_buf();
        }

        ii = 0;
        for (i = 0; i < n_points; i++) {
            G_percent(i, n_points, 4);
            if (pnts[i].r >= 0 && pnts[i].r < nrows && pnts[i].c >= 0 &&
                pnts[i].c < ncols) {
                if (cur_row != pnts[i].r) {
                    cur_row = pnts[i].r;
                    for (j = 0; j < n_vars; j++)
                        Rast_get_d_row(var_fd[j], dbuf[j], cur_row);
                }
                isnull = 0;
                for (j = 0; j < n_vars; j++) {
                    if (Rast_is_d_null_value(&dbuf[j][pnts[i].c]))
                        isnull = 1;
                    pnts[ii].vars[j] = dbuf[j][pnts[i].c];
                }
                if (!isnull) {
                    pnts[ii].r = pnts[i].r;
                    pnts[ii].c = pnts[i].c;
                    pnts[ii].val = pnts[i].val;
                    ii++;
                }
            }
        }
        G_percent(1, 1, 1);
        n_points = ii;
    }
    if (n_vars) {
        for (i = 0; i < n_vars; i++) {
            G_free(dbuf[i]);
        }
        G_free(dbuf);
    }

    out_fd = Rast_open_new(outname, DCELL_TYPE);

    min_points = atoi(minpnts_opt->answer);
    if (min_points < 3 + n_vars) {
        min_points = 3 + n_vars;
        G_warning(_("Minimum number of points is too small, set to %d"),
                  min_points);
    }

    regularization = atof(reg_opt->answer);
    if (regularization < 0)
        regularization = 0;

    overlap = atof(ov_opt->answer);
    if (overlap < 0)
        overlap = 0;
    if (overlap > 1)
        overlap = 1;

    mask_fd = -1;
    if (mask_opt->answer)
        mask_fd = Rast_open_old(mask_opt->answer, "");

    segs_mb = atoi(mem_opt->answer);
    if (segs_mb < 10)
        segs_mb = 10;

    pthin = atof(thin_opt->answer);
    if (pthin < 0)
        pthin = 0;

    if (n_points <= min_points) {
        if (global_tps(out_fd, var_fd, n_vars, mask_fd, pnts, n_points,
                       regularization) != 1) {
            G_fatal_error(_("TPS interpolation failed"));
        }
    }
    else {
        if (local_tps(out_fd, var_fd, n_vars, mask_fd, pnts, n_points,
                      min_points, regularization, overlap, pthin,
                      c_flag->answer, segs_mb) != 1) {
            G_fatal_error(_("TPS interpolation failed"));
        }
    }

    if (n_vars) {
        for (i = 0; i < n_vars; i++) {
            Rast_close(var_fd[i]);
        }
        G_free(var_fd);
    }

    if (mask_fd >= 0)
        Rast_close(mask_fd);

    /* write map history */
    Rast_close(out_fd);
    Rast_short_history(outname, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(outname, &history);

    G_done_msg(" ");

    exit(EXIT_SUCCESS);
} /*END MAIN */
