/****************************************************************************
 *
 * MODULE:       r.dem.icp
 * AUTHOR(S):    Corey T. White <smortopahri@gmail.com>
 * PURPOSE:      Robust multi-scale point-to-plane ICP solver
 * COPYRIGHT:    (C) 2025-2026 by Corey T. White and the GRASS Development
 *               Team
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 *
 *****************************************************************************/

#include <math.h>
#include <stdlib.h>
#include <string.h>

#include <grass/gis.h>
#include <grass/glocale.h>

#include "rdemicp.h"

/* thread-local residual buffer size */
#define RES_CHUNK 8192

/* Bilinear sample helpers (for target z and normals) */
static inline int bilinear_sample_xy_all(const RasterD *ras, const Normals *N,
                                         const Grid *g, double x, double y,
                                         double *z, float *nx, float *ny,
                                         float *nz, float *slope)
{
    double colf = (x - g->west) / g->ewres - 0.5;
    double rowf = (g->north - y) / g->nsres - 0.5;
    int c0 = (int)floor(colf);
    int r0 = (int)floor(rowf);
    double u = colf - c0;
    double v = rowf - r0;
    if (c0 < 0 || r0 < 0 || c0 + 1 >= g->cols || r0 + 1 >= g->rows)
        return 0;
    long i00 = (long)r0 * g->cols + c0;
    long i10 = i00 + 1;
    long i01 = i00 + g->cols;
    long i11 = i01 + 1;

    double z00 = ras->z[i00], z10 = ras->z[i10], z01 = ras->z[i01],
           z11 = ras->z[i11];
    if (isnan(z00) || isnan(z10) || isnan(z01) || isnan(z11))
        return 0;

    double z0 = (1.0 - u) * z00 + u * z10;
    double z1 = (1.0 - u) * z01 + u * z11;
    *z = (1.0 - v) * z0 + v * z1;

    /* normals and slope (lerp components) */
    float nx00 = N->nx[i00], nx10 = N->nx[i10], nx01 = N->nx[i01],
          nx11 = N->nx[i11];
    float ny00 = N->ny[i00], ny10 = N->ny[i10], ny01 = N->ny[i01],
          ny11 = N->ny[i11];
    float nz00 = N->nz[i00], nz10 = N->nz[i10], nz01 = N->nz[i01],
          nz11 = N->nz[i11];
    float sl00 = N->slope[i00], sl10 = N->slope[i10], sl01 = N->slope[i01],
          sl11 = N->slope[i11];

    float nx0 = (1.0 - u) * nx00 + u * nx10;
    float nx1 = (1.0 - u) * nx01 + u * nx11;
    *nx = (1.0 - v) * nx0 + v * nx1;
    float ny0 = (1.0 - u) * ny00 + u * ny10;
    float ny1 = (1.0 - u) * ny01 + u * ny11;
    *ny = (1.0 - v) * ny0 + v * ny1;
    float nz0 = (1.0 - u) * nz00 + u * nz10;
    float nz1 = (1.0 - u) * nz01 + u * nz11;
    *nz = (1.0 - v) * nz0 + v * nz1;
    float sl0 = (1.0 - u) * sl00 + u * sl10;
    float sl1 = (1.0 - u) * sl01 + u * sl11;
    *slope = (1.0 - v) * sl0 + v * sl1;
    return 1;
}

static inline void rot_apply_xy(const Transform *T, int dof, double cx,
                                double cy, double x, double y, double z,
                                double *xo, double *yo, double *zo)
{
    /* rotate about (cx,cy), then translate; include roll/pitch only in 6DoF */
    double xr = x - cx, yr = y - cy;
    double sy = sin(T->yaw), cyaw = cos(T->yaw);

    if (dof == 6) {
        double sr = sin(T->roll), cr = cos(T->roll);
        double sp = sin(T->pitch), cp = cos(T->pitch);
        /* forward Rz(yaw)*Rx(roll)*Ry(pitch) on (xr,yr,z) (z from DEM height
         * used in residual) */
        double x1 = xr * cyaw - yr * sy;
        double y1 = xr * sy + yr * cyaw;
        double z1 = z; /* vertical stays as is here; roll/pitch will mix */
        /* Rx(roll) */
        double x2 = x1;
        double y2 = cr * y1 - sr * z1;
        double z2 = sr * y1 + cr * z1;
        /* Ry(pitch) */
        double x3 = cp * x2 + sp * z2;
        double y3 = y2;
        double z3 = -sp * x2 + cp * z2;
        *xo = x3 + cx + T->tx;
        *yo = y3 + cy + T->ty;
        *zo = z3 + T->tz;
    }
    else {
        double x1 = xr * cyaw - yr * sy;
        double y1 = xr * sy + yr * cyaw;
        *xo = x1 + cx + T->tx;
        *yo = y1 + cy + T->ty;
        *zo = z + T->tz;
    }
}

static int cmp_double(const void *a, const void *b)
{
    double da = *(const double *)a;
    double db = *(const double *)b;
    return (da > db) - (da < db);
}

/* Two-pass ICP iteration: pass 1 gather residuals, choose trim threshold; pass
 * 2 build normal eq. */
int icp_solve(const RasterD *ref, const Normals *Nref, const RasterD *src,
              const RasterD *mask, const Grid *g, const Params *P, Transform *T,
              FILE *stats)
{

    const int L = (P->levels < 1) ? 1 : P->levels;
    double cx = 0.5 * (g->west + g->east);
    double cy = 0.5 * (g->south + g->north);

    for (int level = L - 1; level >= 0; --level) {
        int stride = P->stride * (1 << level);
        if (stride < 1)
            stride = 1;

        double prev_rmse = 1e100;
        for (int iter = 0; iter < P->max_iter; ++iter) {
            /* Pass 1: compute residuals for all candidate points */
            long cap = 1 + (long)((src->rows / stride + 1) *
                                  (long)(src->cols / stride + 1));
            double *absres = (double *)G_malloc(sizeof(double) * cap);
            long count = 0;

#pragma omp parallel
            {
                /* thread-local buffer to avoid atomics */
                double local_abs[RES_CHUNK];
                int lc = 0;

#pragma omp for schedule(static)
                for (int r = 0; r < src->rows; r += stride) {
                    for (int c = 0; c < src->cols; c += stride) {
                        long idx = (long)r * src->cols + c;
                        if (!isnan(src->z[idx])) {
                            if (mask && mask->mask) {
                                if (!mask->mask[idx])
                                    continue;
                            }
                            double x = g->west + (c + 0.5) * g->ewres;
                            double y = g->north - (r + 0.5) * g->nsres;
                            double z = src->z[idx];
                            double xt, yt, zt;
                            rot_apply_xy(T, P->dof, cx, cy, x, y, z, &xt, &yt,
                                         &zt);

                            double zr;
                            float nx, ny, nz, slope;
                            if (!bilinear_sample_xy_all(ref, Nref, g, xt, yt,
                                                        &zr, &nx, &ny, &nz,
                                                        &slope))
                                continue;
                            if (P->slope_max < 90.0 && slope > P->slope_max)
                                continue;
                            /* point-to-plane residual */
                            double rx = 0.0;
                            double ry = 0.0; /* xt-xt == 0, yt-yt == 0 */
                            double rz = zt - zr;
                            double res = nx * rx + ny * ry + nz * rz;
                            if (P->distance_max > 0.0 &&
                                fabs(res) > P->distance_max)
                                continue;

                            if (lc < RES_CHUNK) {
                                local_abs[lc++] = fabs(res);
                            }
                            else {
/* flush */
#pragma omp critical
                                {
                                    for (int i = 0; i < lc; i++)
                                        absres[count++] = local_abs[i];
                                }
                                lc = 0;
                                local_abs[lc++] = fabs(res);
                            }
                        }
                    }
                }
/* final flush */
#pragma omp critical
                {
                    for (int i = 0; i < lc; i++)
                        absres[count++] = local_abs[i];
                }
            }

            if (count < 32) {
                G_warning(_("Too few correspondences at level %d, iter %d"),
                          level, iter);
                G_free(absres);
                break;
            }

            /* Trim threshold */
            long keep = (long)floor(P->trim * (double)count);
            if (keep < 16)
                keep = (count < 16) ? count : 16;

            /* nth-element via qsort (OK for moderate sizes) */
            qsort(absres, (size_t)count, sizeof(double), cmp_double);
            double trim_thr = absres[keep - 1];
            G_free(absres);

            /* Pass 2: build normal equations */
            int Npar = (P->dof == 6) ? 6 : 4;
            double *AtA =
                (double *)G_calloc((size_t)Npar * Npar, sizeof(double));
            double *Atb = (double *)G_calloc((size_t)Npar, sizeof(double));

            double rmse_sum = 0.0;
            long rmse_n = 0;

#pragma omp parallel
            {
                double *AtA_local =
                    (double *)G_calloc((size_t)Npar * Npar, sizeof(double));
                double *Atb_local =
                    (double *)G_calloc((size_t)Npar, sizeof(double));
                double rmse_local = 0.0;
                long n_local = 0;

#pragma omp for schedule(static)
                for (int r = 0; r < src->rows; r += stride) {
                    for (int c = 0; c < src->cols; c += stride) {
                        long idx = (long)r * src->cols + c;
                        if (!isnan(src->z[idx])) {
                            if (mask && mask->mask) {
                                if (!mask->mask[idx])
                                    continue;
                            }
                            double x = g->west + (c + 0.5) * g->ewres;
                            double y = g->north - (r + 0.5) * g->nsres;
                            double z = src->z[idx];
                            double xt, yt, zt;
                            rot_apply_xy(T, P->dof, cx, cy, x, y, z, &xt, &yt,
                                         &zt);

                            double zr;
                            float nx, ny, nz, slope;
                            if (!bilinear_sample_xy_all(ref, Nref, g, xt, yt,
                                                        &zr, &nx, &ny, &nz,
                                                        &slope))
                                continue;
                            if (P->slope_max < 90.0 && slope > P->slope_max)
                                continue;
                            double rx = 0.0, ry = 0.0;
                            double rz = zt - zr;
                            double res = nx * rx + ny * ry +
                                         nz * rz; /* = nz*(zt - zr) */
                            if (P->distance_max > 0.0 &&
                                fabs(res) > P->distance_max)
                                continue;
                            if (fabs(res) > trim_thr)
                                continue;

                            /* Huber weight */
                            double w = 1.0;
                            double ares = fabs(res);
                            if (P->huber_delta > 0.0 && ares > P->huber_delta)
                                w = P->huber_delta / ares;

                            /* Jacobian row J: [n_x, n_y, n_z, (p'_x*n_y -
                             * p'_y*n_x), roll, pitch terms if 6DoF] */
                            double J[6] = {0};
                            J[0] = nx;
                            J[1] = ny;
                            J[2] = nz; /* d/d(tx,ty,tz) */
                            double yaw_term =
                                (xt - T->tx - cx) * ny -
                                (yt - T->ty - cy) *
                                    nx; /* uses p' about pivot (approx) */
                            J[3] = yaw_term;
                            if (P->dof == 6) {
                                /* small-angle approx terms for roll (x) and
                                 * pitch (y): n^T (R (dtheta x p')) ~ (p' x n) .
                                 * dtheta */
                                double px = xt - T->tx - cx;
                                double py = yt - T->ty - cy;
                                double pz = z; /* approx */
                                double cxn =
                                    py * nz - pz * ny; /* d/d roll (x) */
                                double cyn =
                                    pz * nx - px * nz; /* d/d pitch (y) */
                                J[4] = cxn;
                                J[5] = cyn;
                            }
                            double rhs = -res;

                            /* Accumulate AtA += w*J^T J ; Atb += w*J^T*rhs */
                            for (int a = 0; a < Npar; a++) {
                                Atb_local[a] += w * J[a] * rhs;
                                for (int b = 0; b < Npar; b++)
                                    AtA_local[a * Npar + b] += w * J[a] * J[b];
                            }

                            rmse_local += res * res;
                            n_local++;
                        }
                    }
                }
#pragma omp critical
                {
                    for (int a = 0; a < Npar; a++) {
                        Atb[a] += Atb_local[a];
                        for (int b = 0; b < Npar; b++)
                            AtA[a * Npar + b] += AtA_local[a * Npar + b];
                    }
                    rmse_sum += rmse_local;
                    rmse_n += n_local;
                }
                G_free(AtA_local);
                G_free(Atb_local);
            }

            double rmse = (rmse_n > 0) ? sqrt(rmse_sum / (double)rmse_n) : NAN;

            /* Solve */
            double dT[6] = {0};
            if (solve_linear_system(Npar, AtA, Atb, dT) != 0) {
                G_warning(_("Singular normal equations at level %d iter %d"),
                          level, iter);
                G_free(AtA);
                G_free(Atb);
                break;
            }
            G_free(AtA);
            G_free(Atb);

            /* Update */
            T->tx += dT[0];
            T->ty += dT[1];
            T->tz += dT[2];
            T->yaw += dT[3];
            if (P->dof == 6) {
                T->roll += dT[4];
                T->pitch += dT[5];
            }
            clamp_angles(T);

            /* Convergence */
            double delta_norm = 0.0;
            int np = Npar;
            for (int i = 0; i < np; i++)
                delta_norm += dT[i] * dT[i];
            delta_norm = sqrt(delta_norm);
            if (stats)
                fprintf(stats,
                        "level=%d iter=%d rmse=%.6f delta=%.6g inliers=%ld\n",
                        level, iter, rmse, delta_norm, rmse_n);
            if (delta_norm < P->tolerance || (fabs(prev_rmse - rmse) < 1e-9))
                break;
            prev_rmse = rmse;
        }
    }

    return 0;
}
