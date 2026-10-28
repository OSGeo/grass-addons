/****************************************************************************
 *
 * MODULE:       r.dem.icp
 * AUTHOR(S):    Corey T. White <smortopahri@gmail.com>
 * PURPOSE:      Grid setup, raster I/O, and transform helpers
 * COPYRIGHT:    (C) 2025-2026 by Corey T. White and the GRASS Development
 *               Team
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 *
 *****************************************************************************/

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>

#include "rdemicp.h"

void grid_init(Grid *g)
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

double deg2rad(double d)
{
    return d * M_PI / 180.0;
}
double rad2deg(double r)
{
    return r * 180.0 / M_PI;
}

void clamp_angles(Transform *T)
{
    /* keep angles in [-pi, pi] */
    double *a[3] = {&T->yaw, &T->roll, &T->pitch};
    for (int i = 0; i < 3; i++) {
        while (*a[i] > M_PI)
            *a[i] -= 2.0 * M_PI;
        while (*a[i] < -M_PI)
            *a[i] += 2.0 * M_PI;
    }
}

void write_transform(const char *path, const Transform *T, int dof)
{
    if (!path)
        return;
    FILE *f = fopen(path, "w");
    if (!f) {
        G_warning(_("Unable to write transform file %s"), path);
        return;
    }
    fprintf(f, "# r.dem.icp transform (dof=%d)\n", dof);
    fprintf(f, "tx=%.10f\nty=%.10f\ntz=%.10f\n", T->tx, T->ty, T->tz);
    fprintf(f, "yaw=%.10f\nroll=%.10f\npitch=%.10f\n", T->yaw, T->roll,
            T->pitch);
    fclose(f);
}

/* Raster readers */
static double read_cell(DCELL v, int isnull)
{
    if (isnull)
        return NAN;
    else
        return (double)v;
}

void read_fcell_as_double(const char *name, RasterD *out)
{
    int fd = Rast_open_old(name, "");
    int rows = Rast_window_rows();
    int cols = Rast_window_cols();

    DCELL *row = Rast_allocate_d_buf();
    double *arr = (double *)G_malloc(sizeof(double) * rows * cols);

    for (int r = 0; r < rows; r++) {
        Rast_get_d_row(fd, row, r);
        for (int c = 0; c < cols; c++) {
            int isnull = Rast_is_d_null_value(&row[c]);
            arr[(long)r * cols + c] = read_cell(row[c], isnull);
        }
    }

    Rast_close(fd);
    G_free(row);

    out->z = arr;
    out->rows = rows;
    out->cols = cols;
    out->mask = NULL;
}

void read_mask_as_bitmap(const char *name, RasterD *out)
{
    int fd = Rast_open_old(name, "");
    int rows = Rast_window_rows();
    int cols = Rast_window_cols();

    CELL *row = Rast_allocate_c_buf();
    unsigned char *mask = (unsigned char *)G_malloc((size_t)rows * cols);

    for (int r = 0; r < rows; r++) {
        Rast_get_c_row(fd, row, r);
        for (int c = 0; c < cols; c++) {
            int isnull = Rast_is_c_null_value(&row[c]);
            mask[(long)r * cols + c] = (!isnull && row[c] != 0) ? 1 : 0;
        }
    }

    Rast_close(fd);
    G_free(row);

    out->z = NULL;
    out->rows = rows;
    out->cols = cols;
    out->mask = mask;
}

void free_rasterd(RasterD *r)
{
    if (!r)
        return;
    if (r->z)
        G_free(r->z);
    if (r->mask)
        G_free(r->mask);
    r->z = NULL;
    r->mask = NULL;
    r->rows = r->cols = 0;
}
