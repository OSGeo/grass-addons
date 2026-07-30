/****************************************************************************
 *
 * MODULE:       r.dem.icp
 * AUTHOR(S):    Corey T. White <smortopahri@gmail.com>
 * PURPOSE:      Apply final transform and resample source DEM onto the
 *               reference grid
 * COPYRIGHT:    (C) 2025-2026 by Corey T. White and the GRASS Development
 *               Team
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 *
 *****************************************************************************/

#include <math.h>

#include <grass/gis.h>
#include <grass/raster.h>

#include "rdemicp.h"

/* Bilinear sample from raster in world coords (x,y) to z; returns NAN if
 * outside/NaN */
static inline double bilinear_sample_xy(const RasterD *ras, const Grid *g,
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
    long i00 = (long)r0 * g->cols + c0;
    long i10 = i00 + 1;
    long i01 = i00 + g->cols;
    long i11 = i01 + 1;
    double z00 = ras->z[i00], z10 = ras->z[i10], z01 = ras->z[i01],
           z11 = ras->z[i11];
    if (isnan(z00) || isnan(z10) || isnan(z01) || isnan(z11))
        return NAN;
    double z0 = (1.0 - u) * z00 + u * z10;
    double z1 = (1.0 - u) * z01 + u * z11;
    return (1.0 - v) * z0 + v * z1;
}

/* Inverse-warp: for each target cell center, map back to source, sample, write
 */
void apply_transform_and_resample(const RasterD *src, const Grid *g,
                                  const Transform *T, int dof,
                                  const char *out_name)
{
    int rows = g->rows, cols = g->cols;
    struct History hist;
    int outfd = Rast_open_new(out_name, FCELL_TYPE);

    /* rotate about region center to reduce numeric error */
    double cx = 0.5 * (g->west + g->east);
    double cy = 0.5 * (g->south + g->north);

    double sy = sin(T->yaw), cyaw = cos(T->yaw);
    double sr = sin(T->roll), cr = cos(T->roll);
    double sp = sin(T->pitch), cp = cos(T->pitch);

    /* Allocate full target buffer so threads do not race */
    FCELL *row = (FCELL *)G_malloc((size_t)rows * cols * sizeof(FCELL));
#pragma omp parallel for schedule(static)
    for (int r = 0; r < rows; r++) {
        FCELL *rowp = row + (size_t)r * cols;
        for (int c = 0; c < cols; c++) {
            double x = g->west + (c + 0.5) * g->ewres;
            double y = g->north - (r + 0.5) * g->nsres;

            /* Inverse transform for 4/6 DoF */
            double xi = x - T->tx;
            double yi = y - T->ty;
            double zi = 0.0; /* xy inverse translation */
            /* subtract pivot */
            xi -= cx;
            yi -= cy;

            if (dof == 6) {
                /* full inverse rotation R^{-1} approx. R^T of yaw(z), roll(x),
                 * pitch(y) in Z*X*Y order */
                /* compose forward R = Rz(yaw) * Rx(roll) * Ry(pitch), so
                 * inverse is Ry(-pitch)*Rx(-roll)*Rz(-yaw) */
                double syi = -sy,
                       cyi = cyaw; /* cos(-a)=cos a; sin(-a)=-sin a */
                double sri = -sr, cri = cr;
                double spi = -sp, cpi = cp;
                /* Apply inverse rotations around pivot in XY only (Z is height;
                 * rotations can mix Z if roll/pitch) */
                /* First undo pitch (around Y) */
                double x1 = cpi * xi + 0.0 * yi + spi * zi;
                double y1 = yi;
                double z1 = -spi * xi + 0.0 * yi + cpi * zi;
                /* Undo roll (around X) */
                double x2 = x1;
                double y2 = cri * y1 + (-sri) * z1;
                double z2 = sri * y1 + cri * z1;
                /* Undo yaw (around Z): inverse of forward Rz(yaw) is Rz(-yaw).
                 */
                double x3 = cyi * x2 - syi * y2;
                double y3 = syi * x2 + cyi * y2;
                xi = x3;
                yi = y3;
                zi = z2;
            }
            else {
                /* 4-DoF: only yaw. Inverse of forward Rz(yaw) is Rz(-yaw). */
                double x2 = cyaw * xi + sy * yi;
                double y2 = -sy * xi + cyaw * yi;
                xi = x2;
                yi = y2;
                zi = 0.0;
            }

            /* add pivot back */
            xi += cx;
            yi += cy;

            /* Sample source z, then add tz (and roll/pitch effect negligible
             * for z in 4DoF) */
            double zs = bilinear_sample_xy(src, g, xi, yi);
            double outz = NAN;
            if (!isnan(zs)) {
                if (dof == 6)
                    outz = zs + T->tz + zi;
                else
                    outz = zs + T->tz;
            }
            if (isnan(outz)) {
                Rast_set_f_null_value(&rowp[c], 1);
            }
            else {
                rowp[c] = (FCELL)outz;
            }
        }
    }
    /* Write rows in order (serial) */
    for (int r = 0; r < rows; r++) {
        Rast_put_row(outfd, row + (size_t)r * cols, FCELL_TYPE);
    }
    Rast_close(outfd);
    G_free(row);

    Rast_short_history(out_name, "raster", &hist);
    Rast_command_history(&hist);
    Rast_write_history(out_name, &hist);
}
