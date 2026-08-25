/****************************************************************************
 *
 * MODULE:       r.dem.icp
 * AUTHOR(S):    Corey T. White <smortopahri@gmail.com>
 * PURPOSE:      Shared types and declarations for r.dem.icp
 * COPYRIGHT:    (C) 2025-2026 by Corey T. White and the GRASS Development
 *               Team
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 *
 *****************************************************************************/

#ifndef RDEMICP_H
#define RDEMICP_H

#include <stdbool.h>
#include <stdio.h>

#include <grass/gis.h>
#include <grass/raster.h>

/* Region / grid mapping */
typedef struct {
    struct Cell_head win; /* current region */
    int rows, cols;
    double north, south, east, west;
    double nsres, ewres;
} Grid;

/* Parameters */
typedef struct {
    const char *ref_name;
    const char *src_name;
    const char *out_name;
    const char *mask_name;     /* optional */
    const char *transform_out; /* optional file */
    const char *stats_out;     /* optional file */

    int dof;      /* 4 or 6 */
    int levels;   /* multiscale levels */
    int stride;   /* base stride at finest level */
    int max_iter; /* per level */

    double trim;         /* keep fraction */
    double huber_delta;  /* robust weighting */
    double tolerance;    /* convergence threshold */
    double distance_max; /* meters; 0=disabled */
    double slope_max;    /* degrees; 90=disabled */

    /* initial guess */
    double tx, ty, tz;       /* meters */
    double yaw, roll, pitch; /* radians */
} Params;

/* Transform (4- or 6-DoF) */
typedef struct {
    double tx, ty, tz;       /* translation */
    double yaw, roll, pitch; /* rotations around z,x,y respectively */
} Transform;

/* Data containers */
typedef struct {
    double *z;           /* size rows*cols; NaN for NULL */
    unsigned char *mask; /* 0/1 per cell (optional) */
    int rows, cols;      /* convenience */
} RasterD;

typedef struct {
    /* per-cell unit normals (nx,ny,nz) and slope (deg) */
    float *nx;
    float *ny;
    float *nz;
    float *slope;
    int rows, cols;
} Normals;

/* grid */
void grid_init(Grid *g);

/* raster I/O */
void read_fcell_as_double(const char *name, RasterD *out);
void read_mask_as_bitmap(const char *name, RasterD *out);
void free_rasterd(RasterD *r);

/* normals */
void compute_normals_from_dem(const RasterD *dem, const Grid *grid, Normals *N);
void free_normals(Normals *N);

/* ICP */
int icp_solve(const RasterD *ref, const Normals *Nref, const RasterD *src,
              const RasterD *mask, const Grid *grid, const Params *P,
              Transform *T, FILE *stats);

/* resample */
void apply_transform_and_resample(const RasterD *src, const Grid *grid,
                                  const Transform *T, int dof,
                                  const char *out_name);

/* linalg */
int solve_linear_system(int n, double *A, double *b, double *x);

/* utils */
double deg2rad(double d);
double rad2deg(double r);
void clamp_angles(Transform *T);
void write_transform(const char *path, const Transform *T, int dof);

#endif
