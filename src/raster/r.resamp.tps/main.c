/**********************************************************************
 *
 * MODULE:       r.resamp.tps
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
#include <grass/segment.h>
#include <grass/glocale.h>
#include "cache.h"
#include "tps.h"

int main(int argc, char *argv[])
{
    int i;
    const char *outname;
    int in_fd, out_fd, *var_fd;

    struct History history;
    struct Colors colors;

    struct GModule *module;
    struct Option *in_opt, *ivar_opt, *ovar_opt, *out_opt, *minpnts_opt,
        *maxpnts_opt, *radius_opt, *reg_opt, *ov_opt, *lm_opt, *ep_opt,
        *mask_opt, *mem_opt;
    struct Flag *c_flag;
    struct Cell_head cellhd, src, dst;

    int n_ivars, n_ovars, n_vars;
    off_t n_points;
    int min_points, max_points, radius;

    int r, c, nrows, ncols;
    DCELL **dbuf, *dval;
    double regularization, overlap, lm_thresh, ep_thresh;
    struct cache in_seg, var_seg, out_seg;
    int insize, varsize;
    double segsize;
    int segs_mb, nsegs, nsegs_total;

    /*----------------------------------------------------------------*/
    /* Options declarations */
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("surface"));
    G_add_keyword(_("interpolation"));
    G_add_keyword(_("TPS"));
    module->description = _("Performs thin plate spline interpolation with "
                            "regularization and covariables.");

    in_opt = G_define_standard_option(G_OPT_R_INPUT);

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
    ov_opt->answer = "0.2";
    ov_opt->label = _("Overlap factor <= 1");
    ov_opt->description = _("A larger value increase the tile overlap");
    ov_opt->guisection = _("Settings");

    minpnts_opt = G_define_option();
    minpnts_opt->key = "min";
    minpnts_opt->type = TYPE_DOUBLE;
    minpnts_opt->required = NO;
    minpnts_opt->answer = "100";
    minpnts_opt->description =
        _("Minimum number of points to use for TPS interpolation");
    minpnts_opt->guisection = _("Settings");

    maxpnts_opt = G_define_option();
    maxpnts_opt->key = "max";
    maxpnts_opt->type = TYPE_DOUBLE;
    maxpnts_opt->required = NO;
    maxpnts_opt->description =
        _("Maximum number of points to use for TPS interpolation");
    maxpnts_opt->guisection = _("Settings");

    radius_opt = G_define_option();
    radius_opt->key = "radius";
    radius_opt->type = TYPE_INTEGER;
    radius_opt->required = NO;
    radius_opt->answer = "0";
    radius_opt->label = _("Radius for moving window interpolation");
    radius_opt->description =
        _("The unit for radius is cells. If radius is > 0, moving window "
          "interpolation will be used instead of nearest neighbor search");
    radius_opt->guisection = _("Settings");

    ivar_opt = G_define_standard_option(G_OPT_R_INPUTS);
    ivar_opt->key = "icovars";
    ivar_opt->required = NO;
    ivar_opt->label = _("Name of input raster map(s) to use as covariables "
                        "matching the input raster");
    ivar_opt->guisection = _("Settings");

    ovar_opt = G_define_standard_option(G_OPT_R_INPUTS);
    ovar_opt->key = "ocovars";
    ovar_opt->required = NO;
    ovar_opt->label = _("Name of input raster map(s) to use as covariables "
                        "matching the current region");
    ovar_opt->guisection = _("Settings");

    lm_opt = G_define_option();
    lm_opt->key = "lmfilter";
    lm_opt->type = TYPE_DOUBLE;
    lm_opt->required = NO;
    lm_opt->answer = "0";
    lm_opt->label =
        _("Threshold to avoid interpolation outliers when using covariables");
    lm_opt->description = _("Disabled when set to zero, must be within [0, 1], "
                            "larger values will cause more outliers");
    lm_opt->guisection = _("Settings");

    ep_opt = G_define_option();
    ep_opt->key = "epfilter";
    ep_opt->type = TYPE_DOUBLE;
    ep_opt->required = NO;
    ep_opt->answer = "0";
    ep_opt->label =
        _("Threshold to avoid extrapolation when using covariables");
    ep_opt->description = _("Disabled when set to zero, must be > 0, smaller "
                            "values will cause more outliers");
    ep_opt->guisection = _("Settings");

    out_opt = G_define_standard_option(G_OPT_R_OUTPUT);
    out_opt->key = "output";
    out_opt->required = YES;

    mask_opt = G_define_standard_option(G_OPT_R_INPUT);
    mask_opt->key = "mask";
    mask_opt->label = _("Raster map to use for masking");
    mask_opt->description = _("Only cells where the mask map is not NULL and "
                              "not zero are interpolated");
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

    if (!minpnts_opt->answer && !radius_opt->answer)
        G_fatal_error(_("Either <%s> or <%s> must be given"), minpnts_opt->key,
                      radius_opt->key);

    outname = out_opt->answer;

    n_ivars = 0;
    if (ivar_opt->answer) {
        while (ivar_opt->answers[n_ivars])
            n_ivars++;
    }

    n_ovars = 0;
    if (ovar_opt->answer) {
        while (ovar_opt->answers[n_ovars])
            n_ovars++;
    }

    if (n_ivars != n_ovars) {
        G_fatal_error(_("Number of covariables matching the input raster "
                        "must be equal to the number of covariables "
                        "matching the current region"));
    }
    n_vars = n_ovars;

    if (!G_find_raster2(in_opt->answer, ""))
        G_fatal_error(_("Input map <%s> not found"), in_opt->answer);

    for (i = 0; i < n_vars; i++) {
        if (!G_find_raster2(ivar_opt->answers[i], ""))
            G_fatal_error(_("Input map <%s> not found"), ivar_opt->answers[i]);
        if (!G_find_raster2(ovar_opt->answers[i], ""))
            G_fatal_error(_("Input map <%s> not found"), ovar_opt->answers[i]);
    }

    if (mask_opt->answer) {
        if (!G_find_raster2(mask_opt->answer, ""))
            G_fatal_error(_("Mask map <%s> not found"), mask_opt->answer);
    }

    var_fd = NULL;
    if (n_vars)
        var_fd = G_malloc(n_vars * sizeof(int));
    dbuf = G_malloc((1 + n_vars) * sizeof(DCELL *));
    dval = G_malloc((1 + n_vars) * sizeof(DCELL));

    Rast_get_window(&dst);

    /* get cellhd of input */
    Rast_get_cellhd(in_opt->answer, "", &cellhd);

    /* align dst to cellhd  */
    src = dst;
    /*
    Rast_align_window(&src, &cellhd);
    */
    src.ns_res = cellhd.ns_res;
    src.ew_res = cellhd.ew_res;

    src.south =
        cellhd.north -
        ceil((cellhd.north - src.south) / cellhd.ns_res) * cellhd.ns_res;
    src.north =
        cellhd.north -
        floor((cellhd.north - src.north) / cellhd.ns_res) * cellhd.ns_res;
    src.east = cellhd.west +
               ceil((src.east - cellhd.west) / cellhd.ew_res) * cellhd.ew_res;
    src.west = cellhd.west +
               floor((src.west - cellhd.west) / cellhd.ew_res) * cellhd.ew_res;

    /* open segment structures for input and output */

    /* set input window */
    Rast_set_window(&src);
    nrows = src.rows;
    ncols = src.cols;

    segs_mb = atoi(mem_opt->answer);
    if (segs_mb < 10)
        segs_mb = 10;

    segsize = (1 + n_vars) * sizeof(DCELL) /* input */
              + n_vars * sizeof(DCELL)     /* covariables */
              + sizeof(struct tps_out);    /* output */

    segsize = segsize * 64. * 64. / (1024. * 1024.);
    nsegs = segs_mb / segsize;

    /* load input raster and corresponding covariables */
    G_message(_("Loading input..."));

    nsegs_total = ((nrows + 63) / 64) * ((ncols + 63) / 64);
    G_message(_("Total number of input segments %d, in memory %d"), nsegs_total,
              nsegs);

    insize = (1 + n_vars) * sizeof(DCELL);
    if (cache_create(&in_seg, nrows, ncols, 64, 64, insize, nsegs) != 1) {
        G_fatal_error("Unable to create input temporary files");
    }

    in_fd = Rast_open_old(in_opt->answer, "");
    for (i = 0; i < n_vars; i++)
        var_fd[i] = Rast_open_old(ivar_opt->answers[i], "");

    for (i = 0; i <= n_vars; i++)
        dbuf[i] = Rast_allocate_d_buf();

    n_points = 0;
    for (r = 0; r < nrows; r++) {
        G_percent(r, nrows, 5);
        Rast_get_row(in_fd, dbuf[0], r, DCELL_TYPE);
        for (i = 0; i < n_vars; i++)
            Rast_get_row(var_fd[i], dbuf[i + 1], r, DCELL_TYPE);
        for (c = 0; c < ncols; c++) {

            dval[0] = dbuf[0][c];
            if (!Rast_is_d_null_value(&dval[0])) {

                n_points++;
                for (i = 1; i <= n_vars; i++) {
                    dval[i] = dbuf[i][c];
                    if (Rast_is_d_null_value(&dval[i])) {
                        Rast_set_d_null_value(dval, 1 + n_vars);
                        n_points--;
                        break;
                    }
                }
            }
            else if (n_vars) {
                Rast_set_d_null_value(&dval[1], n_vars);
            }

            if (cache_put(&in_seg, (void *)dval, r, c) == NULL)
                G_fatal_error(_("Unable to write to temporary file"));
        }
    }
    G_percent(r, nrows, 5);

    Rast_close(in_fd);
    for (i = 0; i < n_vars; i++)
        Rast_close(var_fd[i]);

    for (i = 0; i <= n_vars; i++)
        G_free(dbuf[i]);
    if (!n_points)
        G_fatal_error(_("No valid input points"));

    G_message(_("%ld input points"), n_points);

    /* set output window */
    Rast_set_window(&dst);
    nrows = dst.rows;
    ncols = dst.cols;

    nsegs_total = ((nrows + 63) / 64) * ((ncols + 63) / 64);
    G_message(_("Total number of output segments %d, in memory %d"),
              nsegs_total, nsegs);

    if (cache_create(&out_seg, nrows, ncols, 64, 64, sizeof(struct tps_out),
                     nsegs) != 1) {
        G_fatal_error("Unable to create output temporary files");
    }

    if (n_vars) {

        /* intialize output raster and load corresponding covariables */
        G_message(_("Loading covariables for output..."));

        varsize = (n_vars) * sizeof(DCELL);
        if (cache_create(&var_seg, nrows, ncols, 64, 64, varsize, nsegs) != 1) {
            G_fatal_error("Unable to create input temporary files");
        }

        /* open segment structure */

        for (i = 0; i < n_vars; i++)
            var_fd[i] = Rast_open_old(ovar_opt->answers[i], "");

        for (i = 0; i < n_vars; i++)
            dbuf[i] = Rast_allocate_d_buf();

        for (r = 0; r < nrows; r++) {
            G_percent(r, nrows, 5);
            for (i = 0; i < n_vars; i++)
                Rast_get_row(var_fd[i], dbuf[i], r, DCELL_TYPE);
            for (c = 0; c < ncols; c++) {

                for (i = 0; i < n_vars; i++) {
                    dval[i] = dbuf[i][c];
                    if (Rast_is_d_null_value(&dval[i])) {
                        Rast_set_d_null_value(dval, n_vars);
                        break;
                    }
                }
                if (cache_put(&var_seg, (void *)dval, r, c) == NULL)
                    G_fatal_error(_("Unable to write to temporary file"));
            }
        }
        G_percent(r, nrows, 5);

        for (i = 0; i < n_vars; i++)
            Rast_close(var_fd[i]);

        for (i = 0; i < n_vars; i++)
            G_free(dbuf[i]);
    }

    out_fd = Rast_open_new(outname, DCELL_TYPE);

    min_points = 0;
    if (minpnts_opt->answer) {
        min_points = atoi(minpnts_opt->answer);
        if (min_points < 3 + n_vars) {
            min_points = 3 + n_vars;
            G_warning(_("Minimum number of points is too small, set to %d"),
                      min_points);
        }
    }
    max_points = 0;
    if (maxpnts_opt->answer) {
        max_points = atoi(maxpnts_opt->answer);
        if (max_points < min_points) {
            G_warning(_("Maximum number of points must be equal to or larger "
                        "than minimum number of points, disabling"));
            max_points = 0;
        }
    }

    radius = 0;
    if (radius_opt->answer) {
        radius = atoi(radius_opt->answer);
        if (radius < 0)
            radius = 0;
    }

    regularization = atof(reg_opt->answer);
    if (regularization < 0)
        regularization = 0;

    overlap = atof(ov_opt->answer);
    if (overlap < 0)
        overlap = 0;
    if (overlap > 1)
        overlap = 1;

    lm_thresh = 0;
    if (lm_opt->answer) {
        lm_thresh = atof(lm_opt->answer);
        if (lm_thresh < 0)
            lm_thresh = 0;
    }

    ep_thresh = 0;
    if (ep_opt->answer) {
        ep_thresh = atof(ep_opt->answer);
        if (ep_thresh < 0)
            ep_thresh = 0;
    }

    if (radius) {
        if (tps_window(&in_seg, &var_seg, n_vars, &out_seg, out_fd,
                       mask_opt->answer, &src, &dst, n_points, regularization,
                       overlap, radius, lm_thresh) != 1) {
            G_fatal_error(_("TPS interpolation failed"));
        }
    }
    else {
        if (tps_nn(&in_seg, &var_seg, n_vars, &out_seg, out_fd,
                   mask_opt->answer, &src, &dst, n_points, min_points,
                   max_points, regularization, overlap, c_flag->answer,
                   lm_thresh, ep_thresh) != 1) {
            G_fatal_error(_("TPS interpolation failed"));
        }
    }

    cache_destroy(&in_seg);
    if (n_vars)
        cache_destroy(&var_seg);
    cache_destroy(&out_seg);

    /* write map history */
    Rast_close(out_fd);
    Rast_short_history(outname, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(outname, &history);

    if (Rast_read_colors(in_opt->answer, "", &colors) == 1)
        Rast_write_colors(outname, G_mapset(), &colors);

    G_done_msg(" ");

    exit(EXIT_SUCCESS);
} /*END MAIN */
