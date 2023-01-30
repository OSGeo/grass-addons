/*
 *  Calculates univariate statistics from the non-null cells
 *
 *   Copyright (C) 2004-2010 by the GRASS Development Team
 *   Author(s): Soeren Gebbert
 *              Based on r.univar from Hamish Bowman, University of Otago, New
 * Zealand and Martin Landa zonal loop by Markus Metz
 *
 *      This program is free software under the GNU General Public
 *      License (>=v2). Read the file COPYING that comes with GRASS
 *      for details.
 *
 */

#ifndef _GLOBALS_H_
#define _GLOBALS_H_

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

/*- Parameters and global variables -----------------------------------------*/
typedef struct {
    int zone;
    char *cat;
    int null_cells;
    double sum;
    double sum2;
    double sum3;
    double sum4;
    double sum_abs;
    double min;
    double max;

    double range;
    double mean;
    double meandev;

    double variance;
    double stddev;
    double var_coef;

    double skewness;
    double kurtosis;

    double variance2;
    double stddev2;
    double var_coef2;

    double skewness2;
    double kurtosis2;

    /* extend statistics */
    double quartile_25;
    double median;
    double quartile_75;
    double *perc;
    double mode;
    int occurrences;

    /* need for processing */
    int n;
    int size;

    RASTER_MAP_TYPE map_type;
    DCELL *array;
    void *nextp;
    int n_alloc;
} univar_stat;

typedef struct {
    CELL min, max, n_zones;
    struct Categories cats;
    char *sep;
    int *len;
    int n_alloc;
} zone_type;

/* command line options are the same for raster and raster3d maps */
typedef struct {
    struct Option *inputfile, *zonefile, *percentile, *tolerance, *output_file,
        *separator;
    struct Flag *shell_style, *extended, *table;
    int n_perc;
    int *index_perc;
    double *quant_perc;
    double *perc;
    double tol;
} param_type;

extern param_type param;
extern zone_type zone_info;

/* fn prototypes */
void heapsort_double(double *data, int n);
void heapsort_float(float *data, int n);
void heapsort_int(int *data, int n);

int compute_stats(univar_stat *, double, int);

/* int print_stats(univar_stat *); */
int print_stats_table(univar_stat *);

univar_stat *create_univar_stat_struct();
void free_univar_stat_struct(univar_stat *stats);

#endif
