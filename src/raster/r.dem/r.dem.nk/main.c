/****************************************************************************
 *
 * MODULE:       r.dem.nk
 *
 * AUTHOR(S):    Corey T. White
 *
 * PURPOSE:       Co-register an SfM DSM to a LiDAR DSM using a Nuth
 *                & Kääb–style model.
 *
 *
 * COPYRIGHT:    (C) 2025-2026 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
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
                ((z7 + 2.0 * z8 + z9) - (z1 + 2.0 * z2 + z3)) / (8.0 * ns);

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

static void write_history(const char *name)
{
    struct History hist;
    Rast_short_history(name, "raster", &hist);
    Rast_command_history(&hist);
    Rast_write_history(name, &hist);
}

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *sfm_opt, *lidar_opt, *stable_opt, *out_opt;
    struct Option *interp_opt, *slope_min_opt, *slope_max_opt, *iters_opt,
        *sigma_opt;
    struct Flag *keep_flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword("raster");
    G_add_keyword("coregistration");
    G_add_keyword("DEM");
    G_add_keyword("SfM");
    G_add_keyword("LiDAR");
    module->label = _("Co-register an SfM DSM to a LiDAR DSM using a Nuth & "
                      "Kääb-style model.");
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
    iters_opt->description =
        _("Iterations of sigma-clipping refinement (0 disables)");

    sigma_opt = G_define_option();
    sigma_opt->key = "sigma";
    sigma_opt->type = TYPE_DOUBLE;
    sigma_opt->required = NO;
    sigma_opt->answer = "2.5";
    sigma_opt->description =
        _("Sigma threshold for residual clipping (|resid| <= sigma * stddev)");

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
    const bool keep = keep_flag->answer ? true : false;

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

    /* Iterative sigma clipping */
    double b0 = 0.0, b1 = 0.0, b2 = 0.0;
    double prev_b0 = 0.0, prev_b1 = 0.0, prev_b2 = 0.0;
    double prev_thresh = 0.0;
    bool prev_has_clip = false;

    for (int iter = 0; iter <= iters; iter++) {
        G_message(_("Estimating coefficients (iteration %d)..."), iter);

        double n = 0.0;
        double SP = 0.0, SQ = 0.0;
        double SPP = 0.0, SQQ = 0.0, SPQ = 0.0;
        double Sdh = 0.0, SPdh = 0.0, SQdh = 0.0;

        for (size_t idx = 0; idx < ncell; idx++) {
            if (!base_valid(&sfm, &lidar, stable_mask, slope_deg, P, Q, idx,
                            slope_min, slope_max))
                continue;

            double dh = sfm.z[idx] - lidar.z[idx];
            if (prev_has_clip) {
                double resid_prev =
                    dh - (prev_b0 + prev_b1 * P[idx] + prev_b2 * Q[idx]);
                if (fabs(resid_prev) > prev_thresh)
                    continue;
            }

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

        if (n <= 3.0)
            G_fatal_error(
                _("Not enough valid pixels in mask to estimate coefficients."));

        solve_normal_equations(n, SP, SQ, SPP, SPQ, SQQ, Sdh, SPdh, SQdh, &b0,
                               &b1, &b2);

        G_message(
            _("  dz = %.6f (vertical)  dx = %.6f (east)  dy = %.6f (north)"),
            b0, b1, b2);

        if (iter == iters)
            break;

        /* Compute residual stddev over current selection (mask + previous clip)
         */
        double mean = 0.0;
        double M2 = 0.0;
        double k = 0.0;
        for (size_t idx = 0; idx < ncell; idx++) {
            if (!base_valid(&sfm, &lidar, stable_mask, slope_deg, P, Q, idx,
                            slope_min, slope_max))
                continue;
            double dh = sfm.z[idx] - lidar.z[idx];
            if (prev_has_clip) {
                double resid_prev =
                    dh - (prev_b0 + prev_b1 * P[idx] + prev_b2 * Q[idx]);
                if (fabs(resid_prev) > prev_thresh)
                    continue;
            }
            double resid = dh - (b0 + b1 * P[idx] + b2 * Q[idx]);
            k += 1.0;
            double delta = resid - mean;
            mean += delta / k;
            double delta2 = resid - mean;
            M2 += delta * delta2;
        }

        double std = NAN;
        if (k > 0.0)
            std = sqrt(M2 / k);

        if (!(std > 0.0) || isnan(std)) {
            G_message(
                _("Residual stddev non-positive; skipping further clipping."));
            break;
        }

        prev_b0 = b0;
        prev_b1 = b1;
        prev_b2 = b2;
        prev_thresh = sigma * std;
        prev_has_clip = true;
        G_message(_("  Clipping threshold: %.6f (sigma=%.3f, stddev=%.6f)"),
                  prev_thresh, sigma, std);
    }

    /* Two-stage resampling to mimic region shift + resamp back */
    G_message(_("Applying vertical correction (dz) and horizontal translation "
                "(dx, dy)..."));

    Grid g2 = g;
    g2.north = g.north - b2;
    g2.south = g.south - b2;
    g2.east = g.east - b1;
    g2.west = g.west - b1;

    double *shifted = (double *)G_malloc(ncell * sizeof(double));
    for (int r = 0; r < g2.rows; r++) {
        for (int c = 0; c < g2.cols; c++) {
            double x = g2.west + (c + 0.5) * g2.ewres;
            double y = g2.north - (r + 0.5) * g2.nsres;
            double zs = sample_xy(sfm.z, &g, x, y, interp);
            if (isnan(zs))
                shifted[(size_t)r * g2.cols + (size_t)c] = NAN;
            else
                shifted[(size_t)r * g2.cols + (size_t)c] = zs - b0;
        }
    }

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

            double zout = sample_xy(shifted, &g2, x, y, interp);
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
    G_free(shifted);
    G_free(out_row);
    G_free(res_row);

    G_message(_("Done. Output raster map <%s>."), out_name);
    G_message(_("Residual raster map <%s>."), resid_name);
    return EXIT_SUCCESS;
}
