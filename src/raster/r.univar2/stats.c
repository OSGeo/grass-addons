/*
 *  Calculates univariate statistics from the non-null cells
 *
 *   Copyright (C) 2004-2007 by the GRASS Development Team
 *   Author(s): Hamish Bowman, University of Otago, New Zealand
 *              Martin Landa and Soeren Gebbert
 *
 *      This program is free software under the GNU General Public
 *      License (>=v2). Read the file COPYING that comes with GRASS
 *      for details.
 *
 */

#include "globals.h"
/*
#include "../../lib/raster/rasterlib.dox"
*/
#define I 0
#define J 1

/* *************************************************************** */
/* **** univar_stat constructor ********************************** */
/* *************************************************************** */
univar_stat *create_univar_stat_struct()
{
    univar_stat *stats;
    int z;
    int n_zones = zone_info.n_zones;

    if (n_zones == 0)
        n_zones = 1;

    stats = (univar_stat *)G_calloc(n_zones, sizeof(univar_stat));

    for (z = 0; z < n_zones; z++) {
        stats[z].zone = 0;
        stats[z].cat = NULL;
        stats[z].null_cells = 0;
        stats[z].sum = 0.0;
        stats[z].sum2 = 0.0;
        stats[z].sum3 = 0.0;
        stats[z].sum4 = 0.0;
        stats[z].sum_abs = 0.0;
        stats[z].min = 0.0 / 0.0; /* set to nan as default */
        stats[z].max = 0.0 / 0.0; /* set to nan as default */

        stats[z].range = 0.0 / 0.0;   /* set to nan as default */
        stats[z].mean = 0.0 / 0.0;    /* set to nan as default */
        stats[z].meandev = 0.0 / 0.0; /* set to nan as default */

        stats[z].variance = 0.0 / 0.0; /* set to nan as default */
        stats[z].stddev = 0.0 / 0.0;   /* set to nan as default */
        stats[z].var_coef = 0.0 / 0.0; /* set to nan as default */

        stats[z].skewness = 0.0 / 0.0; /* set to nan as default */
        stats[z].kurtosis = 0.0 / 0.0; /* set to nan as default */

        stats[z].variance2 = 0.0 / 0.0; /* set to nan as default */
        stats[z].stddev2 = 0.0 / 0.0;   /* set to nan as default */
        stats[z].var_coef2 = 0.0 / 0.0; /* set to nan as default */

        stats[z].skewness2 = 0.0 / 0.0; /* set to nan as default */
        stats[z].kurtosis2 = 0.0 / 0.0; /* set to nan as default */

        stats[z].quartile_25 = 0.0 / 0.0; /* set to nan as default */
        stats[z].median = 0.0 / 0.0;      /* set to nan as default */
        stats[z].quartile_75 = 0.0 / 0.0; /* set to nan as default */
        stats[z].mode = 0.0 / 0.0;        /* set to nan as default */
        stats[z].occurrences = 0;

        stats[z].n = 0;
        stats[z].size = 0;
        stats[z].map_type = 0;
        stats[z].array = NULL;
        stats[z].nextp = NULL;
        stats[z].n_alloc = 0;
    }

    return stats;
}

/* *************************************************************** */
/* **** univar_stat destructor *********************************** */
/* *************************************************************** */
void free_univar_stat_struct(univar_stat *stats)
{
    /*int z, n_zones = zone_info.n_zones;

    for (z = 0; z < n_zones; z++){
        if (stats[z].perc != NULL)
            G_free(&stats[z].perc);
    } */

    return;
}

int factorial(int n)
{
    int res = 1;

    while (n > 1)
        res *= n--;
    return res;
}

int num_combinations(int n, int k)
{
    return factorial(n) / (factorial(k) * factorial(n - k));
}

void index_combinations(int n, int **indexes)
{
    int i, j;

    for (i = 0; i < n; i++)
        for (j = i + 1; j < n; j++)
            indexes[i][I] = i;
    indexes[i][J] = j;
    return;
}

void sort_mode_double(double *array, int n, double tol, double *mode,
                      int *occurrences)
{
    int previous = array[0];
    int i = 1, counter = 1;
    *mode = (double)array[0];
    *occurrences = 1;

    if (n > 1) {
        while (i < n) {
            if ((double)fabs(array[i] - previous) > tol) {
                if (counter > *occurrences) {
                    *occurrences = counter;
                    *mode = (double)previous;
                }
                previous = array[i];
                counter = 1;
            }
            else {
                counter += 1;
            }
            i += 1;
        }
    }
    return;
}

void mode_double(double *array, int n, double tol, double *mode,
                 int *occurrences, int **indexes)
{
    int i, i_previous = 0, counter = 0, num_comb = 0;
    *mode = 0;
    *occurrences = 0;

    num_comb = num_combinations(n, 2);
    index_combinations(n, indexes);
    for (i = 0; i < num_comb; i++)
        if (array[indexes[i][I]] != i_previous) {
            if (counter > *occurrences) {
                *occurrences = counter;
                *mode = (double)i_previous;
            }
            i_previous = array[indexes[i][I]];
            counter = 0;
        }
    if (fabs((double)array[indexes[i][I]] - (double)array[indexes[i][J]]) < tol)
        counter += 1;
    return;
}

int stats_extend(univar_stat *stat)
{
    int p, qind_25, qind_75;
    int n = stat->n;

    for (p = 0; p < param.n_perc; p++) {
        param.index_perc[p] = (int)(n * 1e-2 * param.perc[p] - 0.5);
        stat->perc[p] = stat->array[param.index_perc[p]];
    }
    qind_25 = (int)(n * 0.25 - 0.5);
    qind_75 = (int)(n * 0.75 - 0.5);

    heapsort_double(stat->array, n);

    stat->quartile_25 = stat->array[qind_25];
    /*               odd ?     odd                              : even   */
    stat->median =
        ((n % 2) ? (stat->array[(int)(n / 2)])
                 : (stat->array[n / 2 - 1] + stat->array[n / 2]) / 2.0);
    stat->quartile_75 = stat->array[qind_75];

    sort_mode_double(stat->array, n, param.tol, &stat->mode,
                     &stat->occurrences);

    /* free the memory after compute the extended statistics */
    G_free(stat->array);
    stat->array = NULL;
    stat->n_alloc = 0;
    return 0;
}

int stats_general(univar_stat *s)
{
    double n = s->n;

    s->null_cells = s->size - s->n;
    s->range = s->max - s->min;
    s->mean = s->sum / n;
    s->meandev = s->sum_abs / n;

    s->variance = (s->sum2 - s->sum * s->sum / n) / (n - 1);
    if (s->variance < GRASS_EPSILON)
        s->variance = 0.0;
    s->stddev = sqrt(s->variance);
    s->var_coef = (s->stddev / s->mean) * 100.;

    s->skewness =
        (s->sum3 / n - 3 * s->sum * s->sum2 / (n * n) +
         2 * s->sum * s->sum * s->sum / (n * n * n) / (pow(s->variance, 1.5)));
    s->kurtosis = ((s->sum4 / n - 4 * s->sum * s->sum3 / (n * n) +
                    6 * s->sum * s->sum * s->sum2 / (n * n * n) -
                    3 * s->sum * s->sum * s->sum * s->sum / (n * n * n * n)) /
                       (s->variance * s->variance) -
                   3);

    s->variance2 = s->sum2 / (n - 1);
    if (s->variance2 < GRASS_EPSILON)
        s->variance2 = 0.0;
    s->stddev2 = sqrt(s->variance2);
    s->var_coef2 = (s->stddev2 / s->mean) * 100.;

    s->skewness2 = (s->sum3 / (s->stddev2 * s->stddev2 * s->stddev2) / n);
    s->kurtosis2 = (s->sum4 / (s->variance2 * s->variance2) / (n - 3));
    return 0;
}

int compute_stats(univar_stat *stat, double val, int len)
{
    stat->sum += val;
    stat->sum2 += val * val;
    stat->sum3 += val * val * val;
    stat->sum4 += val * val * val * val;
    stat->sum_abs += fabs(val);
    stat->min = (isnan(stat->min) || val < stat->min) ? val : stat->min;
    stat->max = (isnan(stat->max) || val > stat->max) ? val : stat->max;

    if (stat->array != NULL)
        G_debug(3, "Compute_stats, zone: %d, val=%f, %d/%d, n_alloc:%d",
                stat->zone, val, stat->n, stat->size, stat->n_alloc);
    stat->array[stat->n] = val;

    stat->n++;

    if (stat->n == stat->size) {
        G_debug(3, "    Finish the zone: %d, sum=%f", stat->zone, stat->sum);
        /* finish this zone */
        stats_general(stat);
        if (stat->array != NULL) {
            stats_extend(stat);
            return 1;
        }
    }
    return 0;
}

/* *************************************************************** */
/* **** compute and print univar statistics to stdout ************ */
/* *************************************************************** */

void print_cols_table()
{
    int i;

    fprintf(stdout, "zone");
    fprintf(stdout, "%slabel", zone_info.sep);
    fprintf(stdout, "%sall_cells", zone_info.sep);
    fprintf(stdout, "%snon_null_cells", zone_info.sep);
    fprintf(stdout, "%snull_cells", zone_info.sep);

    fprintf(stdout, "%ssum", zone_info.sep);
    fprintf(stdout, "%ssum_abs", zone_info.sep);
    fprintf(stdout, "%smin", zone_info.sep);
    fprintf(stdout, "%smax", zone_info.sep);

    fprintf(stdout, "%srange", zone_info.sep);
    fprintf(stdout, "%smean", zone_info.sep);
    fprintf(stdout, "%smean_of_abs", zone_info.sep);

    fprintf(stdout, "%svariance", zone_info.sep);
    fprintf(stdout, "%sstddev", zone_info.sep);
    fprintf(stdout, "%scoeff_var", zone_info.sep);

    fprintf(stdout, "%sskewness", zone_info.sep);
    fprintf(stdout, "%skurtosis", zone_info.sep);

    fprintf(stdout, "%svariance2", zone_info.sep);
    fprintf(stdout, "%sstddev2", zone_info.sep);
    fprintf(stdout, "%scoeff_var2", zone_info.sep);

    fprintf(stdout, "%sskewness2", zone_info.sep);
    fprintf(stdout, "%skurtosis2", zone_info.sep);

    if (param.extended->answer) {
        fprintf(stdout, "%sfirst_quart", zone_info.sep);
        fprintf(stdout, "%smedian", zone_info.sep);
        fprintf(stdout, "%sthird_quart", zone_info.sep);
        for (i = 0; i < param.n_perc; i++) {

            if (param.perc[i] == (int)param.perc[i]) {
                /* percentile is an exact integer */
                fprintf(stdout, "%sperc_%d", zone_info.sep, (int)param.perc[i]);
            }
            else {
                /* percentile is not an exact integer */
                char buf[24];
                sprintf(buf, "%.15g", param.perc[i]);
                G_strchg(buf, '.', '_');
                fprintf(stdout, "%sperc_%s", zone_info.sep, buf);
            }
        }

        fprintf(stdout, "%smode", zone_info.sep);
        fprintf(stdout, "%soccurrences", zone_info.sep);
    }
    fprintf(stdout, "\n");
    return;
}

int print_row(univar_stat *stat, char *sep)
{
    int i;
    char sum_str[100];

    /* zone number */
    fprintf(stdout, "%d", stat->zone);
    /* zone label */
    fprintf(stdout, "%s%s", sep, stat->cat);
    /* zone all_cells */
    fprintf(stdout, "%s%d", sep, stat->size);
    /* non-null cells */
    fprintf(stdout, "%s%d", sep, stat->n);
    /* null cells */
    fprintf(stdout, "%s%d", sep, stat->null_cells);

    sprintf(sum_str, "%.15g", stat->sum);
    G_trim_decimal(sum_str);
    fprintf(stdout, "%s%s", sep, sum_str);
    sprintf(sum_str, "%.15g", stat->sum_abs);
    G_trim_decimal(sum_str);
    fprintf(stdout, "%s%s", sep, sum_str);
    fprintf(stdout, "%s%.15g", sep, stat->min);
    fprintf(stdout, "%s%.15g", sep, stat->max);

    fprintf(stdout, "%s%.15g", sep, stat->range);
    fprintf(stdout, "%s%.15g", sep, stat->mean);
    fprintf(stdout, "%s%.15g", sep, stat->meandev);

    fprintf(stdout, "%s%.15g", sep, stat->variance);
    fprintf(stdout, "%s%.15g", sep, stat->stddev);
    fprintf(stdout, "%s%.15g", sep, stat->var_coef);

    fprintf(stdout, "%s%g", sep, stat->skewness);
    fprintf(stdout, "%s%g", sep, stat->kurtosis);

    fprintf(stdout, "%s%.15g", sep, stat->variance2);
    fprintf(stdout, "%s%.15g", sep, stat->stddev2);
    fprintf(stdout, "%s%.15g", sep, stat->var_coef2);

    fprintf(stdout, "%s%g", sep, stat->skewness2);
    fprintf(stdout, "%s%g", sep, stat->kurtosis2);

    if (param.extended->answer) {
        fprintf(stdout, "%s%g", sep, stat->quartile_25);
        fprintf(stdout, "%s%g", sep, stat->median);
        fprintf(stdout, "%s%g", sep, stat->quartile_75);
        for (i = 0; i < param.n_perc; i++) {
            fprintf(stdout, "%s%g", sep, stat->perc[i]);
        }

        fprintf(stdout, "%s%g", sep, stat->mode);
        fprintf(stdout, "%s%d", sep, stat->occurrences);
    }
    fprintf(stdout, "\n");
    return 0;
}

int print_stats_table(univar_stat *stats)
{
    int z, n_zones = zone_info.n_zones;

    /* print column headers */
    print_cols_table();

    /* print stats */
    for (z = 0; z < n_zones; z++) {
        /* stats collected for this zone? */
        if (!stats[z].n == 0)
            print_row(&stats[z], zone_info.sep);
    }
    return 1;
}
