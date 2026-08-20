/****************************************************************************
 *
 * MODULE:       r.dem.nk
 *
 * AUTHOR(S):    Corey T. White <smortopahri gmail.com>
 *
 * PURPOSE:      Co-register an SfM DSM to a LiDAR DSM using a Nuth &
 *               Kaab-style model.
 *
 * COPYRIGHT:    (C) 2025-2026 by Corey T. White and the GRASS Development
 *               Team
 *
 *               SPDX-License-Identifier: GPL-2.0-or-later
 *
 *****************************************************************************/

#include <math.h>
#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>

typedef struct {
    struct Cell_head win;
    int rows, cols;
    double north, south, east, west;
    double nsres, ewres;
} Grid;

typedef struct {
    double *z; /* rows*cols; NAN for NULL */
    int rows, cols;
} RasterD;

static void grid_init(Grid *g)
{
    Rast_get_window(&g->win);
    g->rows = Rast_window_rows();
    g->cols = Rast_window_cols();
    g->north = g->win.north;
    g->south = g->win.south;
    g->east = g->win.east;
    g->west = g->win.west;
    g->nsres = g->win.ns_res;
    g->ewres = g->win.ew_res;
}

static double rad2deg(double r)
{
    return r * 180.0 / M_PI;
}

static int read_raster_as_double(const char *name, RasterD *out)
{
    int fd = Rast_open_old(name, "");
    if (fd < 0)
        G_fatal_error(_("Cannot open raster map <%s>."), name);

    int rows = Rast_window_rows();
    int cols = Rast_window_cols();

    DCELL *row = Rast_allocate_d_buf();
    double *arr = (double *)G_malloc((size_t)rows * cols * sizeof(double));

    for (int r = 0; r < rows; r++) {
        Rast_get_d_row(fd, row, r);
        for (int c = 0; c < cols; c++) {
            if (Rast_is_d_null_value(&row[c]))
                arr[(size_t)r * cols + c] = NAN;
            else
                arr[(size_t)r * cols + c] = (double)row[c];
        }
    }

    Rast_close(fd);
    G_free(row);

    out->z = arr;
    out->rows = rows;
    out->cols = cols;
    return 0;
}

static int read_mask_as_bitmap(const char *name, unsigned char **mask_out)
{
    int fd = Rast_open_old(name, "");
    if (fd < 0)
        G_fatal_error(_("Cannot open raster map <%s>."), name);

    int rows = Rast_window_rows();
    int cols = Rast_window_cols();

    DCELL *row = Rast_allocate_d_buf();
    unsigned char *mask = (unsigned char *)G_malloc((size_t)rows * cols);

    for (int r = 0; r < rows; r++) {
        Rast_get_d_row(fd, row, r);
        for (int c = 0; c < cols; c++) {
            if (Rast_is_d_null_value(&row[c]))
                mask[(size_t)r * cols + c] = 0;
            else
                mask[(size_t)r * cols + c] = (row[c] != 0.0) ? 1 : 0;
        }
    }

    Rast_close(fd);
    G_free(row);

    *mask_out = mask;
    return 0;
}

static inline double det3(const double m[3][3])
{
    return m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) -
           m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) +
           m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
}

static void solve_normal_equations(double n, double SP, double SQ, double SPP,
                                   double SPQ, double SQQ, double Sdh,
                                   double SPdh, double SQdh, double *b0,
                                   double *b1, double *b2)
{
    double A[3][3] = {{n, SP, SQ}, {SP, SPP, SPQ}, {SQ, SPQ, SQQ}};
    double y[3] = {Sdh, SPdh, SQdh};

    double D = det3(A);
    if (fabs(D) < 1e-12)
        G_fatal_error(_("Normal equation matrix is near-singular; check "
                        "mask/slope range."));

    double A0[3][3] = {{y[0], A[0][1], A[0][2]},
                       {y[1], A[1][1], A[1][2]},
                       {y[2], A[2][1], A[2][2]}};

    double A1[3][3] = {{A[0][0], y[0], A[0][2]},
                       {A[1][0], y[1], A[1][2]},
                       {A[2][0], y[2], A[2][2]}};

    double A2[3][3] = {{A[0][0], A[0][1], y[0]},
                       {A[1][0], A[1][1], y[1]},
                       {A[2][0], A[2][1], y[2]}};

    *b0 = det3(A0) / D;
    *b1 = det3(A1) / D;
    *b2 = det3(A2) / D;
}

static void compute_slope_aspect_pq(const RasterD *lidar, const Grid *g,
                                    double *slope_deg, double *aspect_deg,
                                    double *P, double *Q)
{
    int rows = g->rows;
    int cols = g->cols;
    const double ns = g->nsres;
    const double ew = g->ewres;

    for (size_t i = 0; i < (size_t)rows * (size_t)cols; i++) {
        slope_deg[i] = NAN;
        aspect_deg[i] = NAN;
        P[i] = NAN;
        Q[i] = NAN;
    }

    for (int r = 1; r < rows - 1; r++) {
        for (int c = 1; c < cols - 1; c++) {
            size_t idx = (size_t)r * cols + c;

            double z1 = lidar->z[(size_t)(r - 1) * cols + (c - 1)];
            double z2 = lidar->z[(size_t)(r - 1) * cols + c];
            double z3 = lidar->z[(size_t)(r - 1) * cols + (c + 1)];
            double z4 = lidar->z[(size_t)r * cols + (c - 1)];
            double z5 = lidar->z[(size_t)r * cols + c];
            double z6 = lidar->z[(size_t)r * cols + (c + 1)];
            double z7 = lidar->z[(size_t)(r + 1) * cols + (c - 1)];
            double z8 = lidar->z[(size_t)(r + 1) * cols + c];
            double z9 = lidar->z[(size_t)(r + 1) * cols + (c + 1)];

            if (isnan(z1) || isnan(z2) || isnan(z3) || isnan(z4) || isnan(z5) ||
                isnan(z6) || isnan(z7) || isnan(z8) || isnan(z9))
                continue;

            double dzdx =
                ((z3 + 2.0 * z6 + z9) - (z1 + 2.0 * z4 + z7)) / (8.0 * ew);

            double dzdy =
                ((z1 + 2.0 * z2 + z3) - (z7 + 2.0 * z8 + z9)) / (8.0 * ns);

            double slope_rad = atan(sqrt(dzdx * dzdx + dzdy * dzdy));
            slope_deg[idx] = rad2deg(slope_rad);

            double vx = -dzdx;
            double vy = -dzdy;
            if (vx == 0.0 && vy == 0.0)
                continue;

            double aspect_rad = atan2(vy, vx);
            if (aspect_rad < 0.0)
                aspect_rad += 2.0 * M_PI;
            aspect_deg[idx] = rad2deg(aspect_rad);

            double t = tan(slope_rad);
            P[idx] = t * cos(aspect_rad);
            Q[idx] = t * sin(aspect_rad);
        }
    }
}

static inline bool base_valid(const RasterD *sfm, const RasterD *lidar,
                              const unsigned char *stable_mask,
                              const double *slope_deg, const double *P,
                              const double *Q, size_t idx, double slope_min,
                              double slope_max)
{
    if (!stable_mask[idx])
        return false;
    if (isnan(sfm->z[idx]) || isnan(lidar->z[idx]))
        return false;
    if (isnan(slope_deg[idx]) || isnan(P[idx]) || isnan(Q[idx]))
        return false;
    if (slope_deg[idx] < slope_min || slope_deg[idx] > slope_max)
        return false;
    return true;
}

static inline double bilinear_sample_xy(const double *z, const Grid *g,
                                        double x, double y)
{
    double colf = (x - g->west) / g->ewres - 0.5;
    double rowf = (g->north - y) / g->nsres - 0.5;
    int c0 = (int)floor(colf);
    int r0 = (int)floor(rowf);
    double u = colf - c0;
    double v = rowf - r0;

    if (c0 < 0 || r0 < 0 || c0 + 1 >= g->cols || r0 + 1 >= g->rows)
        return NAN;

    size_t i00 = (size_t)r0 * g->cols + (size_t)c0;
    size_t i10 = i00 + 1;
    size_t i01 = i00 + (size_t)g->cols;
    size_t i11 = i01 + 1;
    double z00 = z[i00], z10 = z[i10], z01 = z[i01], z11 = z[i11];
    if (isnan(z00) || isnan(z10) || isnan(z01) || isnan(z11))
        return NAN;
    double z0 = (1.0 - u) * z00 + u * z10;
    double z1 = (1.0 - u) * z01 + u * z11;
    return (1.0 - v) * z0 + v * z1;
}

static inline double nearest_sample_xy(const double *z, const Grid *g, double x,
                                       double y)
{
    double colf = (x - g->west) / g->ewres - 0.5;
    double rowf = (g->north - y) / g->nsres - 0.5;
    int c = (int)floor(colf + 0.5);
    int r = (int)floor(rowf + 0.5);
    if (c < 0 || r < 0 || c >= g->cols || r >= g->rows)
        return NAN;
    return z[(size_t)r * g->cols + (size_t)c];
}

static inline double cubic_weight(double t)
{
    const double a = -0.5;
    t = fabs(t);
    if (t <= 1.0)
        return (a + 2.0) * t * t * t - (a + 3.0) * t * t + 1.0;
    if (t < 2.0)
        return a * t * t * t - 5.0 * a * t * t + 8.0 * a * t - 4.0 * a;
    return 0.0;
}

static inline double bicubic_sample_xy(const double *z, const Grid *g, double x,
                                       double y)
{
    double colf = (x - g->west) / g->ewres - 0.5;
    double rowf = (g->north - y) / g->nsres - 0.5;
    int c1 = (int)floor(colf);
    int r1 = (int)floor(rowf);
    double sum = 0.0;
    double wsum = 0.0;

    for (int j = -1; j <= 2; j++) {
        int rr = r1 + j;
        if (rr < 0 || rr >= g->rows)
            return NAN;
        double wy = cubic_weight((double)rr - rowf);
        for (int i = -1; i <= 2; i++) {
            int cc = c1 + i;
            if (cc < 0 || cc >= g->cols)
                return NAN;
            double wx = cubic_weight((double)cc - colf);
            double w = wx * wy;
            double vv = z[(size_t)rr * g->cols + (size_t)cc];
            if (isnan(vv))
                return NAN;
            sum += w * vv;
            wsum += w;
        }
    }

    if (wsum == 0.0)
        return NAN;
    return sum / wsum;
}

static double sample_xy(const double *z, const Grid *g, double x, double y,
                        const char *method)
{
    if (strcmp(method, "nearest") == 0)
        return nearest_sample_xy(z, g, x, y);
    if (strcmp(method, "bicubic") == 0)
        return bicubic_sample_xy(z, g, x, y);
    return bilinear_sample_xy(z, g, x, y);
}

/* Apply the accumulated NK transform to the original SfM at map coords (x, y):
 * sample the SfM at (x + b1, y + b2) and subtract the vertical bias b0. Shared
 * by the per-pass re-warp and the final output so the surface the solver
 * converged on cannot drift from the surface written out. */
static inline double warp_sfm_xy(const double *sfm_z, const Grid *g, double x,
                                 double y, double b0, double b1, double b2,
                                 const char *interp)
{
    double zs = sample_xy(sfm_z, g, x + b1, y + b2, interp);
    return isnan(zs) ? NAN : zs - b0;
}

/* Height difference dh = work - lidar at idx, and whether the pixel takes part
 * in the current solve. Returns false (leaving *dh_out untouched) when the
 * warped SfM is undefined or the pixel is rejected by the previous iteration's
 * sigma clip. base_valid() must already hold for idx. */
static inline bool nk_residual(const double *work, const RasterD *lidar,
                               const double *P, const double *Q, size_t idx,
                               bool has_clip, double cb0, double cb1,
                               double cb2, double thresh, double *dh_out)
{
    if (isnan(work[idx]))
        return false;
    double dh = work[idx] - lidar->z[idx];
    if (has_clip) {
        double resid_prev = dh - (cb0 + cb1 * P[idx] + cb2 * Q[idx]);
        if (fabs(resid_prev) > thresh)
            return false;
    }
    *dh_out = dh;
    return true;
}

static void write_history(const char *name)
{
    struct History hist;
    Rast_short_history(name, "raster", &hist);
    Rast_command_history(&hist);
    Rast_write_history(name, &hist);
}

/* Derived output rasters (<output>_resid, -k intermediates) are not parser
 * options, so enforce the overwrite check the parser would have done. */
static void check_derived_output(const char *out_name, const char *suffix)
{
    char name[GNAME_MAX];

    snprintf(name, sizeof(name), "%s%s", out_name, suffix);
    if (G_find_raster2(name, G_mapset()) && !G_get_overwrite())
        G_fatal_error(_("Raster map <%s> already exists. To overwrite, use "
                        "the --overwrite flag"),
                      name);
}

static void write_nk_transform(const char *path, double dz, double dx,
                               double dy)
{
    FILE *f = fopen(path, "w");
    if (!f) {
        G_warning(_("Unable to write transform file <%s>."), path);
        return;
    }
    fprintf(f, "# r.dem.nk transform\n");
    fprintf(f, "dz=%.10f\ndx=%.10f\ndy=%.10f\n", dz, dx, dy);
    fclose(f);
}

static void read_nk_transform(const char *path, double *dz, double *dx,
                              double *dy)
{
    FILE *f = fopen(path, "r");
    if (!f)
        G_fatal_error(_("Unable to read transform file <%s>."), path);
    char line[256];
    while (fgets(line, sizeof(line), f)) {
        if (line[0] == '#')
            continue;
        char key[64];
        double val;
        if (sscanf(line, "%63[^=]=%lf", key, &val) == 2) {
            if (strcmp(key, "dz") == 0)
                *dz = val;
            else if (strcmp(key, "dx") == 0)
                *dx = val;
            else if (strcmp(key, "dy") == 0)
                *dy = val;
        }
    }
    fclose(f);
}

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *sfm_opt, *lidar_opt, *stable_opt, *out_opt;
    struct Option *interp_opt, *slope_min_opt, *slope_max_opt, *iters_opt,
        *sigma_opt, *maxiter_opt, *tol_opt;
    struct Option *xfout_opt, *xfin_opt;
    struct Flag *keep_flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("coregistration"));
    G_add_keyword(_("DEM"));
    G_add_keyword(_("SfM"));
    G_add_keyword(_("LiDAR"));
    module->label = _("Co-register an SfM DSM to a LiDAR DSM using a Nuth & "
                      "Kaab-style model.");
    module->description =
        _("Estimates horizontal (dx, dy) and vertical (dz) offsets on stable "
          "terrain and applies a sub-cell translation.");

    sfm_opt = G_define_standard_option(G_OPT_R_INPUT);
    sfm_opt->key = "sfm";
    sfm_opt->description = _("Input SfM DSM raster");

    lidar_opt = G_define_standard_option(G_OPT_R_INPUT);
    lidar_opt->key = "lidar";
    lidar_opt->description = _("Input LiDAR DSM raster (reference)");

    stable_opt = G_define_standard_option(G_OPT_R_INPUT);
    stable_opt->key = "stable_mask";
    stable_opt->description =
        _("Mask raster (1 for stable terrain, NULL elsewhere)");

    out_opt = G_define_standard_option(G_OPT_R_OUTPUT);
    out_opt->key = "output";
    out_opt->description = _("Output co-registered SfM DSM");

    interp_opt = G_define_option();
    interp_opt->key = "interp";
    interp_opt->type = TYPE_STRING;
    interp_opt->required = NO;
    interp_opt->answer = "bilinear";
    interp_opt->options = "nearest,bilinear,bicubic";
    interp_opt->description = _("Interpolation for sub-cell translation");

    slope_min_opt = G_define_option();
    slope_min_opt->key = "slope_min";
    slope_min_opt->type = TYPE_DOUBLE;
    slope_min_opt->required = NO;
    slope_min_opt->answer = "2.0";
    slope_min_opt->description =
        _("Minimum slope (degrees) used for regression (avoid near-flat)");

    slope_max_opt = G_define_option();
    slope_max_opt->key = "slope_max";
    slope_max_opt->type = TYPE_DOUBLE;
    slope_max_opt->required = NO;
    slope_max_opt->answer = "85.0";
    slope_max_opt->description =
        _("Maximum slope (degrees) used for regression (avoid near-vertical)");

    iters_opt = G_define_option();
    iters_opt->key = "iters";
    iters_opt->type = TYPE_INTEGER;
    iters_opt->required = NO;
    iters_opt->answer = "2";
    iters_opt->description = _(
        "Sigma-clipping iterations per co-registration pass (0 disables clip)");

    sigma_opt = G_define_option();
    sigma_opt->key = "sigma";
    sigma_opt->type = TYPE_DOUBLE;
    sigma_opt->required = NO;
    sigma_opt->answer = "2.5";
    sigma_opt->description =
        _("Sigma threshold for residual clipping (|resid| <= sigma * stddev)");

    maxiter_opt = G_define_option();
    maxiter_opt->key = "max_iter";
    maxiter_opt->type = TYPE_INTEGER;
    maxiter_opt->required = NO;
    maxiter_opt->answer = "20";
    maxiter_opt->description =
        _("Maximum outer co-registration passes (re-warp and re-solve)");

    tol_opt = G_define_option();
    tol_opt->key = "tol";
    tol_opt->type = TYPE_DOUBLE;
    tol_opt->required = NO;
    tol_opt->answer = "0.01";
    tol_opt->description =
        _("Convergence tolerance in map units for the outer passes");

    xfout_opt = G_define_standard_option(G_OPT_F_OUTPUT);
    xfout_opt->key = "transform_output";
    xfout_opt->required = NO;
    xfout_opt->description =
        _("Write the solved transform (dz, dx, dy) to a file");

    xfin_opt = G_define_standard_option(G_OPT_F_INPUT);
    xfin_opt->key = "apply_transform";
    xfin_opt->required = NO;
    xfin_opt->description =
        _("Apply a saved transform (dz, dx, dy) instead of solving");

    keep_flag = G_define_flag();
    keep_flag->key = 'k';
    keep_flag->description = _("Keep intermediate rasters");

    if (G_parser(argc, argv))
        return EXIT_FAILURE;

    const char *sfm_name = sfm_opt->answer;
    const char *lidar_name = lidar_opt->answer;
    const char *stable_name = stable_opt->answer;
    const char *out_name = out_opt->answer;
    const char *interp = interp_opt->answer;
    const double slope_min = atof(slope_min_opt->answer);
    const double slope_max = atof(slope_max_opt->answer);
    int iters = atoi(iters_opt->answer);
    if (iters < 0)
        iters = 0;
    const double sigma = atof(sigma_opt->answer);
    int max_outer = atoi(maxiter_opt->answer);
    if (max_outer < 1)
        max_outer = 1;
    const double conv_tol = atof(tol_opt->answer);
    const bool keep = keep_flag->answer ? true : false;
    const char *xform_out = xfout_opt->answer;
    const char *xform_in = xfin_opt->answer;

    check_derived_output(out_name, "_resid");
    if (keep) {
        check_derived_output(out_name, "_slope");
        check_derived_output(out_name, "_aspect");
        check_derived_output(out_name, "_mask");
    }

    /* Set local processing region to LiDAR grid without changing user's region
     */
    struct Cell_head lidar_win;
    Rast_get_cellhd(lidar_name, "", &lidar_win);
    Rast_set_window(&lidar_win);
    Grid g;
    grid_init(&g);

    G_message(_("Reading input rasters into memory..."));
    RasterD sfm = {0}, lidar = {0};
    unsigned char *stable_mask = NULL;
    read_raster_as_double(sfm_name, &sfm);
    read_raster_as_double(lidar_name, &lidar);
    read_mask_as_bitmap(stable_name, &stable_mask);

    if (sfm.rows != g.rows || sfm.cols != g.cols || lidar.rows != g.rows ||
        lidar.cols != g.cols)
        G_fatal_error(
            _("Internal error: raster dimensions do not match region."));

    size_t ncell = (size_t)g.rows * (size_t)g.cols;
    double *slope_deg = (double *)G_malloc(ncell * sizeof(double));
    double *aspect_deg = (double *)G_malloc(ncell * sizeof(double));
    double *P = (double *)G_malloc(ncell * sizeof(double));
    double *Q = (double *)G_malloc(ncell * sizeof(double));

    G_message(_("Computing slope, aspect, and predictors..."));
    compute_slope_aspect_pq(&lidar, &g, slope_deg, aspect_deg, P, Q);

    /* Accumulated transform (sfm -> reference). */
    double b0 = 0.0, b1 = 0.0, b2 = 0.0;

    if (xform_in) {
        read_nk_transform(xform_in, &b0, &b1, &b2);
        G_message(_("Applying saved transform: dz=%.6f dx=%.6f dy=%.6f"), b0,
                  b1, b2);
    }
    else {
        /* Iterative Nuth & Kaeaeb. A single linear pass under-estimates shifts
         * larger than a pixel (dh ~ shift*grad is only first order), so solve
         * the incremental (db0,db1,db2) on a working surface, accumulate, and
         * re-warp the SfM from the original each outer pass until the increment
         * is negligible. Sigma clipping runs as the inner solve each pass. */
        double *work = (double *)G_malloc(ncell * sizeof(double));
        for (size_t i = 0; i < ncell; i++)
            work[i] = sfm.z[i];

        /* base_valid() depends only on static inputs (mask, slope, P, Q), so
         * gather the eligible cells once and reuse the list every pass. */
        size_t *valid = (size_t *)G_malloc(ncell * sizeof(size_t));
        size_t nvalid = 0;
        for (size_t idx = 0; idx < ncell; idx++)
            if (base_valid(&sfm, &lidar, stable_mask, slope_deg, P, Q, idx,
                           slope_min, slope_max))
                valid[nvalid++] = idx;
        if (nvalid <= 3)
            G_fatal_error(
                _("Not enough valid pixels in mask to estimate coefficients."));

        bool converged = false;
        for (int outer = 0; outer < max_outer; outer++) {
            double db0 = 0.0, db1 = 0.0, db2 = 0.0;
            double cb0 = 0.0, cb1 = 0.0, cb2 = 0.0;
            double thresh = 0.0;
            bool has_clip = false;
            bool starved = false;

            for (int iter = 0; iter <= iters; iter++) {
                double n = 0.0;
                double SP = 0.0, SQ = 0.0;
                double SPP = 0.0, SQQ = 0.0, SPQ = 0.0;
                double Sdh = 0.0, SPdh = 0.0, SQdh = 0.0;

                for (size_t v = 0; v < nvalid; v++) {
                    size_t idx = valid[v];
                    double dh;
                    if (!nk_residual(work, &lidar, P, Q, idx, has_clip, cb0,
                                     cb1, cb2, thresh, &dh))
                        continue;
                    double p = P[idx];
                    double q = Q[idx];
                    n += 1.0;
                    SP += p;
                    SQ += q;
                    SPP += p * p;
                    SQQ += q * q;
                    SPQ += p * q;
                    Sdh += dh;
                    SPdh += p * dh;
                    SQdh += q * dh;
                }

                if (n <= 3.0) {
                    /* Pass 0 sees the full valid set, so too few pixels is a
                     * genuine input problem. On later passes the warp has
                     * pushed the stable mask off valid data, so keep the
                     * transform solved so far instead of aborting. */
                    if (outer == 0)
                        G_fatal_error(_("Not enough valid pixels in mask to "
                                        "estimate coefficients."));
                    G_warning(_("Stable pixels exhausted after warping; "
                                "stopping at outer pass %d."),
                              outer);
                    starved = true;
                    break;
                }

                solve_normal_equations(n, SP, SQ, SPP, SPQ, SQQ, Sdh, SPdh,
                                       SQdh, &db0, &db1, &db2);

                if (iter == iters)
                    break;

                double mean = 0.0, M2 = 0.0, k = 0.0;
                for (size_t v = 0; v < nvalid; v++) {
                    size_t idx = valid[v];
                    double dh;
                    if (!nk_residual(work, &lidar, P, Q, idx, has_clip, cb0,
                                     cb1, cb2, thresh, &dh))
                        continue;
                    double resid = dh - (db0 + db1 * P[idx] + db2 * Q[idx]);
                    k += 1.0;
                    double delta = resid - mean;
                    mean += delta / k;
                    M2 += delta * (resid - mean);
                }
                double std = (k > 0.0) ? sqrt(M2 / k) : NAN;
                if (!(std > 0.0) || isnan(std))
                    break;
                cb0 = db0;
                cb1 = db1;
                cb2 = db2;
                thresh = sigma * std;
                has_clip = true;
                G_verbose_message(
                    _("  Clip threshold %.4f (sigma=%.3f, stddev=%.4f)"),
                    thresh, sigma, std);
            }

            if (starved)
                break;

            b0 += db0;
            b1 += db1;
            b2 += db2;
            G_message(_("Outer pass %d: cumulative dz=%.4f dx=%.4f dy=%.4f "
                        "(increment |dxy|=%.4f)"),
                      outer, b0, b1, b2, hypot(db1, db2));

            if (hypot(db1, db2) < conv_tol && fabs(db0) < conv_tol) {
                converged = true;
                break;
            }

            /* Re-warp the working surface from the ORIGINAL SfM by the
             * accumulated transform for the next pass:
             * work(x,y) = sfm(x+b1, y+b2) - b0. */
            for (int r = 0; r < g.rows; r++) {
                for (int c = 0; c < g.cols; c++) {
                    double x = g.west + (c + 0.5) * g.ewres;
                    double y = g.north - (r + 0.5) * g.nsres;
                    work[(size_t)r * g.cols + (size_t)c] =
                        warp_sfm_xy(sfm.z, &g, x, y, b0, b1, b2, interp);
                }
            }
        }
        G_free(work);
        G_free(valid);
        if (converged)
            G_message(_("Converged transform: dz=%.6f dx=%.6f dy=%.6f"), b0, b1,
                      b2);
        else
            G_warning(_("Did not converge within %d passes; using last "
                        "estimate: dz=%.6f dx=%.6f dy=%.6f"),
                      max_outer, b0, b1, b2);
    }

    if (xform_out)
        write_nk_transform(xform_out, b0, b1, b2);

    /* Single-stage inverse warp. The model solved sfm - lidar = b0 + b1*P +
     * b2*Q with P=-dz/dx, Q=-dz/dy, so (b1,b2) is the horizontal offset of the
     * SfM relative to the reference and b0 the vertical bias. To realign,
     * sample the SfM at (x+b1, y+b2) and subtract b0.
     * NOTE: the previous two-stage "region shift + resample back" used the same
     * shifted grid for both passes, which cancelled to a net identity and
     * applied only the vertical term, leaving the horizontal misregistration.
     */
    G_message(_("Applying vertical correction (dz) and horizontal translation "
                "(dx, dy)..."));

    int outfd = Rast_open_new(out_name, FCELL_TYPE);
    char resid_name[GNAME_MAX];
    snprintf(resid_name, sizeof(resid_name), "%s_resid", out_name);
    int residfd = Rast_open_new(resid_name, FCELL_TYPE);

    FCELL *out_row = Rast_allocate_f_buf();
    FCELL *res_row = Rast_allocate_f_buf();

    for (int r = 0; r < g.rows; r++) {
        for (int c = 0; c < g.cols; c++) {
            size_t idx = (size_t)r * g.cols + (size_t)c;
            double x = g.west + (c + 0.5) * g.ewres;
            double y = g.north - (r + 0.5) * g.nsres;

            double zout = warp_sfm_xy(sfm.z, &g, x, y, b0, b1, b2, interp);
            if (isnan(zout))
                Rast_set_f_null_value(&out_row[c], 1);
            else
                out_row[c] = (FCELL)zout;

            bool base_ok = base_valid(&sfm, &lidar, stable_mask, slope_deg, P,
                                      Q, idx, slope_min, slope_max);
            if (base_ok && !isnan(zout) && !isnan(lidar.z[idx]))
                res_row[c] = (FCELL)(zout - lidar.z[idx]);
            else
                Rast_set_f_null_value(&res_row[c], 1);
        }
        Rast_put_row(outfd, out_row, FCELL_TYPE);
        Rast_put_row(residfd, res_row, FCELL_TYPE);
    }

    Rast_close(outfd);
    Rast_close(residfd);

    write_history(out_name);
    write_history(resid_name);

    if (keep) {
        char slope_name[GNAME_MAX];
        char aspect_name[GNAME_MAX];
        char mask_name[GNAME_MAX];
        snprintf(slope_name, sizeof(slope_name), "%s_slope", out_name);
        snprintf(aspect_name, sizeof(aspect_name), "%s_aspect", out_name);
        snprintf(mask_name, sizeof(mask_name), "%s_mask", out_name);

        int slopefd = Rast_open_new(slope_name, FCELL_TYPE);
        int aspectfd = Rast_open_new(aspect_name, FCELL_TYPE);
        int maskfd = Rast_open_new(mask_name, CELL_TYPE);
        FCELL *srow = Rast_allocate_f_buf();
        FCELL *arow = Rast_allocate_f_buf();
        CELL *mrow = Rast_allocate_c_buf();

        for (int r = 0; r < g.rows; r++) {
            for (int c = 0; c < g.cols; c++) {
                size_t idx = (size_t)r * g.cols + (size_t)c;
                if (isnan(slope_deg[idx]))
                    Rast_set_f_null_value(&srow[c], 1);
                else
                    srow[c] = (FCELL)slope_deg[idx];

                if (isnan(aspect_deg[idx]))
                    Rast_set_f_null_value(&arow[c], 1);
                else
                    arow[c] = (FCELL)aspect_deg[idx];

                if (base_valid(&sfm, &lidar, stable_mask, slope_deg, P, Q, idx,
                               slope_min, slope_max))
                    mrow[c] = 1;
                else
                    Rast_set_c_null_value(&mrow[c], 1);
            }
            Rast_put_row(slopefd, srow, FCELL_TYPE);
            Rast_put_row(aspectfd, arow, FCELL_TYPE);
            Rast_put_row(maskfd, mrow, CELL_TYPE);
        }

        Rast_close(slopefd);
        Rast_close(aspectfd);
        Rast_close(maskfd);

        write_history(slope_name);
        write_history(aspect_name);
        write_history(mask_name);

        G_free(srow);
        G_free(arow);
        G_free(mrow);
    }

    /* Cleanup */
    G_free(sfm.z);
    G_free(lidar.z);
    G_free(stable_mask);
    G_free(slope_deg);
    G_free(aspect_deg);
    G_free(P);
    G_free(Q);
    G_free(out_row);
    G_free(res_row);

    G_message(_("Done. Output raster map <%s>."), out_name);
    G_message(_("Residual raster map <%s>."), resid_name);
    return EXIT_SUCCESS;
}
