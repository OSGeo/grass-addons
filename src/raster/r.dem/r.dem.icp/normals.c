/****************************************************************************
 *
 * MODULE:       r.dem.icp
 * AUTHOR(S):    Corey T. White <smortopahri@gmail.com>
 * PURPOSE:      Compute per-cell surface normals and slope from a DEM
 * COPYRIGHT:    (C) 2025-2026 by Corey T. White and the GRASS Development
 *               Team
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 *
 *****************************************************************************/

#include <math.h>
#include <stdlib.h>

#include "rdemicp.h"

static inline void norm3(float *x, float *y, float *z)
{
    double n =
        sqrt((double)(*x) * (*x) + (double)(*y) * (*y) + (double)(*z) * (*z));
    if (n < 1e-12) {
        *x = 0;
        *y = 0;
        *z = 1;
        return;
    }
    *x /= (float)n;
    *y /= (float)n;
    *z /= (float)n;
}

void compute_normals_from_dem(const RasterD *dem, const Grid *grid, Normals *N)
{
    int rows = dem->rows, cols = dem->cols;
    float *nx = (float *)G_malloc(sizeof(float) * rows * cols);
    float *ny = (float *)G_malloc(sizeof(float) * rows * cols);
    float *nz = (float *)G_malloc(sizeof(float) * rows * cols);
    float *slope = (float *)G_malloc(sizeof(float) * rows * cols);

    double dx = grid->ewres;
    double dy = grid->nsres;

    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) {
            long idx = (long)r * cols + c;
            double zc = dem->z[idx];
            if (isnan(zc)) {
                nx[idx] = 0;
                ny[idx] = 0;
                nz[idx] = 0;
                slope[idx] = NAN;
                continue;
            }

            int c0 = (c > 0) ? c - 1 : c;
            int c1 = (c < cols - 1) ? c + 1 : c;
            int r0 = (r > 0) ? r - 1 : r;
            int r1 = (r < rows - 1) ? r + 1 : r;

            double zl = dem->z[(long)r * cols + c0];
            double zr = dem->z[(long)r * cols + c1];
            double zu = dem->z[(long)r0 * cols + c];
            double zd = dem->z[(long)r1 * cols + c];

            /* central differences; handle NaNs by fallback */
            if (isnan(zl))
                zl = zc;
            if (isnan(zr))
                zr = zc;
            if (isnan(zu))
                zu = zc;
            if (isnan(zd))
                zd = zc;

            double dzdx = (zr - zl) / (2.0 * dx);
            /* Note: row increases southwards; northing decreases with row,
            so dz/dy uses (zu - zd) / (2*dy) */
            double dzdy = (zu - zd) / (2.0 * dy);

            float vx = (float)(-dzdx);
            float vy = (float)(-dzdy);
            float vz = 1.0f;
            norm3(&vx, &vy, &vz);

            nx[idx] = vx;
            ny[idx] = vy;
            nz[idx] = vz;
            double tanS = sqrt(dzdx * dzdx + dzdy * dzdy);
            slope[idx] = (float)rad2deg(atan(tanS));
        }
    }

    N->nx = nx;
    N->ny = ny;
    N->nz = nz;
    N->slope = slope;
    N->rows = rows;
    N->cols = cols;
}

void free_normals(Normals *N)
{
    if (!N)
        return;
    if (N->nx)
        G_free(N->nx);
    if (N->ny)
        G_free(N->ny);
    if (N->nz)
        G_free(N->nz);
    if (N->slope)
        G_free(N->slope);
    N->nx = N->ny = N->nz = N->slope = NULL;
    N->rows = N->cols = 0;
}
