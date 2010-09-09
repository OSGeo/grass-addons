#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#include "local_proto.h"

#define SCALE   100.

/* value and count */
#define TOTAL 0
#define WARM  1
#define COLD  2
#define SNOW  3
#define SOIL  4

/* signa */
#define COVER       1
#define SUM_COLD    0
#define SUM_WARM    1
#define KMEAN       2
#define KMAX        3
#define KMIN        4

/* re-use value */
#define KLOWER      0
#define KUPPER      1
#define MEAN        2
#define SKEW        3
#define VARI        4

/*
    Con Landsat-7 funciona bien pero con Landsat-5 falla
    la primera pasada metiendo terreno desertico como nube fría
    y luego se equivoca en resolver los ambiguos en áreas
    con mucha humedad ambiental.

    Habría que reajustar las constantes para Landsat-5
*/




/**********************************************************
 *
 * Automatic Cloud Cover Assessment (ACCA): Irish 2000
 *
 **********************************************************/

/*--------------------------------------------------------
  CONSTANTS
  Usar esta forma para que via extern puedan modificarse
  como opciones desde el programa main.
 ---------------------------------------------------------*/

double th_1   = 0.08;            /* Band 3 Brightness Threshold */
double th_1_b = 0.07;
double th_2[] = { -0.25, 0.70 }; /* Normalized Snow Difference Index */
double th_2_b = 0.8;
double th_3   = 300.;            /* Band 6 Temperature Threshold */
double th_4   = 225.;            /* Band 5/6 Composite */
double th_4_b = 0.08;
double th_5   = 2.35;            /* Band 4/3 Ratio */
double th_6   = 2.16248;         /* Band 4/2 Ratio */
double th_7   = 1.0;             /* Band 4/5 Ratio */;
double th_8   = 210.;            /* Band 5/6 Composite */

extern int hist_n;

#define K_BASE  240.

void acca_algorithm(int verbose, Gfile * out, Gfile band[],
                    int two_pass, int with_shadow)
{
    int i, count[5], hist_cold[hist_n], hist_warm[hist_n];
    double x, value[5], signa[5], idesert, warm_ambiguous, shift;

    /* Initialized varibles ... */
    for (i = 0; i < 5; i++)
    {
        count[i] = 0;
        value[i] = 0.;
    }
    for (i = 0; i < hist_n; i++)
    {
        hist_cold[i] = hist_warm[i] = 0;
    }

    /* FIRST FILTER ... */
    acca_first(verbose, out, band, with_shadow,
               count, hist_cold, hist_warm, signa);
    /* CATEGORIES: NO_DEFINED, WARM_CLOUD, COLD_CLOUD, NULL (= NO_CLOUD) */

    value[WARM] = (double)count[WARM] / (double)count[TOTAL];
    value[COLD] = (double)count[COLD] / (double)count[TOTAL];
    value[SNOW] = (double)count[SNOW] / (double)count[TOTAL];
    value[SOIL] = (double)count[SOIL] / (double)count[TOTAL];

    value[0] = (double)(count[WARM] + count[COLD]);
    idesert = (value[0] == 0. ? 0. : value[0] /
                                    (value[0] + (double)count[SOIL]));

    /* BAND-6 CLOUD SIGNATURE DEVELOPMENT */
    if (value[SNOW] > 0.01)
    {
        /* Only the cold clouds are used
           if snow or desert soil is present */
        warm_ambiguous = 1;
    }
    else
    {
        /* The cold and warm clouds are combined
           and treated as a single population */
        warm_ambiguous = 0;
        count[COLD] += count[WARM];
        value[COLD] += value[WARM];
        signa[SUM_COLD] += signa[SUM_WARM];
        for (i = 0; i < hist_n; i++) hist_cold[i] += hist_warm[i];
    }

    signa[KMEAN] = (signa[SUM_COLD] / (double)count[COLD]) * SCALE;
    signa[COVER] = (double)count[COLD] / (double)count[TOTAL];

    fprintf(stdout, "  PRELIMINARY SCENE ANALYSIS\n");
    fprintf(stdout, "    Desert index:  %.3lf\n", idesert);
    fprintf(stdout, "    Snow cover  :  %.3lf %%\n", 100.*value[SNOW]);
    fprintf(stdout, "    Cloud cover :  %.3lf %%\n", 100.*signa[COVER]);
    fprintf(stdout, "    Temperature of %s clouds\n", (warm_ambiguous ? "cold" : "all"));
    fprintf(stdout, "      Maximum: %.2lf K\n", signa[KMAX]);
    fprintf(stdout, "      Mean   : %.2lf K\n", signa[KMEAN]);
    fprintf(stdout, "      Minimum: %.2lf K\n", signa[KMIN]);

    /* WARNING: variable 'value' reutilizada con nuevos valores */

    if (idesert > 0.5 && signa[COVER] > 0.004 && signa[KMEAN] < 295.)
    {
        value[KUPPER] = quantile( 0.975, hist_cold ) + K_BASE;
        value[KLOWER] = quantile( 0.835, hist_cold ) + K_BASE;
        value[MEAN]   = mean(hist_cold) + K_BASE;
        value[VARI]   = moment( 2, hist_cold );
        value[SKEW]   = moment( 3, hist_cold );

        if (value[SKEW] > 0.)
        {
            shift = value[SKEW];
            if (shift > 1.) shift = 1.;
            shift *= sqrt( value[VARI] );

            x = quantile( 0.9875, hist_cold ) + K_BASE;
            if ((value[KUPPER] + shift) > x)
            {
                value[KUPPER] = x;
                value[KLOWER] = x - shift; /** ??? COMPROBAR ***/
            }
            else
            {
                value[KUPPER] += shift;
                value[KLOWER] += shift;
            }
        }

        fprintf(stdout, "  HISTOGRAM CLOUD SIGNATURE\n");
        fprintf(stdout, "      Histogram classes:  %d\n", hist_n);
        fprintf(stdout, "      Mean temperature:   %.2lf K\n", value[MEAN]);
        fprintf(stdout, "      Standard deviation: %.2lf\n", sqrt(value[VARI]));
        fprintf(stdout, "      Skewness:           %.2lf\n", value[SKEW]);
        fprintf(stdout, "      97.50 percentile:   %.2lf K\n", value[KUPPER]);
        fprintf(stdout, "      83.50 percentile:   %.2lf K\n", value[KLOWER]);
//         fprintf(stdout, "      50.00 percentile:   %.2lf K\n", quantile(0.5,hist_cold) + K_BASE);
    }
    else
    {
        if (signa[KMEAN] < 295.)
        {
            /* Retained warm and cold clouds */
            fprintf(stdout, "    Scene with clouds\n");
            warm_ambiguous = 0;
            value[KUPPER] = 0.;
            value[KLOWER] = 0.;
        }
        else
        {
            /* Retained cold clouds */
            fprintf(stdout, "    Scene cloud free\n");
            warm_ambiguous = 1;
            value[KUPPER] = 0.;
            value[KLOWER] = 0.;
        }
    }

    /* SECOND FILTER ... */
    /* By-pass two processing by retains warm and cold clouds */
    if (two_pass == 0)
    {
        warm_ambiguous = 0;
        value[KUPPER] = 0.;
        value[KLOWER] = 0.;
    }
    acca_second(verbose, out, band[BAND6],
                warm_ambiguous, value[KUPPER], value[KLOWER]);
    /* CATEGORIES: WARM_CLOUD, COLD_CLOUD, NULL (= NO_CLOUD) */

    return;
}


void acca_first(int verbose, Gfile * out, Gfile band[],
                int with_shadow,
                int count[], int cold[], int warm[], double stats[])
{
    int i, row, col, nrows, ncols;

    char code;
    double pixel[5], nsdi, rat56, rat45;

    /* Creation of output file */
    out->rast = G_allocate_raster_buf(CELL_TYPE);
    if ((out->fd = G_open_raster_new(out->name, CELL_TYPE)) < 0)
        G_fatal_error(_("Could not open <%s>"), out->name);

    /* ----- ----- */
    fprintf(stdout, "Pass one processing ... \n");

    stats[SUM_COLD] = 0.;
    stats[SUM_WARM] = 0.;
    stats[KMAX] = 0.;
    stats[KMIN] = 10000.;

    nrows = G_window_rows();
    ncols = G_window_cols();

    for (row = 0; row < nrows; row++)
    {
        if (verbose)
        {
            G_percent(row, nrows, 2);
        }
        for (i = BAND2; i <= BAND6; i++)
        {
            if (G_get_d_raster_row(band[i].fd, band[i].rast, row) < 0)
                G_fatal_error(_("Could not read row from <%s>"), band[i].name);
        }
        for (col = 0; col < ncols; col++)
        {
            code = NO_DEFINED;
            /* Null when null pixel in any band */
            for ( i = BAND2; i <= BAND6; i++ )
            {
                if (G_is_d_null_value((void *)((DCELL *) band[i].rast + col)))
                {
                    code = NO_CLOUD;
                    break;
                }
                pixel[i] = (double)((DCELL *) band[i].rast)[col];
            }
            /* Determina los pixeles de sombras */
            if (code == NO_DEFINED && with_shadow)
            {
                code = shadow_algorithm(pixel);
            }
            /* Analiza el valor de los pixeles no definidos */
            if (code == NO_DEFINED)
            {
                code = NO_CLOUD;
                count[TOTAL]++;
                nsdi = (pixel[BAND2] - pixel[BAND5]) /
                       (pixel[BAND2] + pixel[BAND5]);
                /* ----------------------------------------------------- */
                /* Brightness Threshold: Eliminates dark images */
                if (pixel[BAND3] > th_1)
                {
                    /* Normalized Snow Difference Index: Eliminates many types of snow */
                    if (nsdi > th_2[0] && nsdi < th_2[1])
                    {
                        /* Temperature Threshold: Eliminates warm image features */
                        if (pixel[BAND6] < th_3)
                        {
                            rat56 = (1 - pixel[BAND4]) * pixel[BAND6];
                            /* Band 5/6 Composite: Eliminates numerous categories including ice */
                            if (rat56 < th_4)
                            {
                                /* Eliminates growing vegetation */
                                /* Eliminates senescing vegetation */
                                if (pixel[BAND4]/pixel[BAND3] < th_5 &&
                                    pixel[BAND4]/pixel[BAND2] < th_6)
                                {
                                    rat45 = pixel[BAND4]/pixel[BAND5];
                                    /* Eliminates rocks and desert */
                                    if (rat45 > th_7)
                                    {
                                        /* Distinguishes warm clouds from cold clouds */
                                        if (rat56 < th_8)
                                        {
                                            code = COLD_CLOUD;
                                            count[COLD]++;
                                            /* for statistic */
                                            stats[SUM_COLD] += (pixel[BAND6]/SCALE);
                                            hist_put(pixel[BAND6] - K_BASE, cold);
                                        }
                                        else
                                        {
                                            code = WARM_CLOUD;
                                            count[WARM]++;
                                            /* for statistic */
                                            stats[SUM_WARM] += (pixel[BAND6]/SCALE);
                                            hist_put(pixel[BAND6] - K_BASE, warm);
                                        }
                                        if (pixel[BAND6] > stats[KMAX]) stats[KMAX] = pixel[BAND6];
                                        if (pixel[BAND6] < stats[KMIN]) stats[KMIN] = pixel[BAND6];
                                    }
                                    else { code = NO_DEFINED; count[SOIL]++; }
                                }
                                else code = NO_DEFINED;
                            }
                            else code = (pixel[BAND5] < th_4_b) ? NO_CLOUD : NO_DEFINED;
                        }
                        else code = NO_CLOUD;
                    }
                    else { code = NO_CLOUD; if (nsdi > th_2_b) count[SNOW]++; }
                }
                else code = (pixel[BAND3] < th_1_b) ? NO_CLOUD : NO_DEFINED;
            /* ----------------------------------------------------- */
            }
            if (code == NO_CLOUD)
            {
                G_set_c_null_value((CELL *) out->rast + col, 1);
            }
            else
            {
                ((CELL *) out->rast)[col] = code;
            }
        }
        if (G_put_raster_row(out->fd, out->rast, CELL_TYPE) < 0)
        {
            G_fatal_error(_("Cannot write row to <%s>"), out->name);
        }
    }
    /* ----- ----- */

    G_free(out->rast);
    G_close_cell(out->fd);

    return;
}


void acca_second(int verbose, Gfile * out, Gfile band,
                 int warm_ambiguous, double upper, double lower)
{
    int row, col, nrows, ncols;
    char *mapset;

    int code;
    double temp;
    Gfile tmp;

    /* Open to read */
    mapset = G_find_cell2(out->name, "");
    if (mapset == NULL)
        G_fatal_error("cell file [%s] not found", out->name);
    out->rast = G_allocate_raster_buf(CELL_TYPE);
    if ((out->fd = G_open_cell_old(out->name, mapset)) < 0)
        G_fatal_error("Cannot open cell file [%s]", out->name);

    /* Open to write */
    sprintf(tmp.name, "_%d.BBB", getpid()) ;
    tmp.rast = G_allocate_raster_buf(CELL_TYPE);
    if ((tmp.fd = G_open_raster_new(tmp.name, CELL_TYPE)) < 0)
        G_fatal_error(_("Could not open <%s>"), tmp.name);

    if (upper == 0.)
        fprintf(stdout, "Removing ambiguous pixels ... \n");
    else
        fprintf(stdout, "Pass two processing ... \n");

    nrows = G_window_rows();
    ncols = G_window_cols();

    for (row = 0; row < nrows; row++)
    {
        if (verbose)
        {
            G_percent(row, nrows, 2);
        }
        if (G_get_d_raster_row(band.fd, band.rast, row) < 0)
            G_fatal_error(_("Could not read from <%s>"), band.name);
        if (G_get_c_raster_row(out->fd, out->rast, row) < 0)
            G_fatal_error(_("Could not read from <%s>"), out->name);

        for (col = 0; col < ncols; col++)
        {
            if (G_is_c_null_value((void *)((CELL *) out->rast + col)))
            {
                G_set_c_null_value((CELL *) tmp.rast + col, 1);
            }
            else
            {
                code = (int)((CELL *) out->rast)[col];
                /* Resolve ambiguous pixels */
                if (code == NO_DEFINED ||
                   (code == WARM_CLOUD) && warm_ambiguous == 1)
                {
                    temp = (double)((DCELL *) band.rast)[col];
                    if (temp > upper)
                    {
                        G_set_c_null_value((CELL *) tmp.rast + col, 1);
                    }
                    else
                    {
                        if (temp < lower)
                            ((CELL *) tmp.rast)[col] = IS_COLD_CLOUD;
                        else
                            ((CELL *) tmp.rast)[col] = IS_WARM_CLOUD;
                    }
                }
                else
                /* Join warm (not ambiguous) and cold clouds */
                if (code == COLD_CLOUD ||
                   (code == WARM_CLOUD) && warm_ambiguous == 0)
                {
                    ((CELL *) tmp.rast)[col] = IS_COLD_CLOUD;
                }
                else
                    ((CELL *) tmp.rast)[col] = IS_SHADOW;
            }
        }
        if (G_put_raster_row(tmp.fd, tmp.rast, CELL_TYPE) < 0)
        {
            G_fatal_error(_("Cannot write to <%s>"), tmp.name);
        }
    }

    /* Finalización */

    G_free(tmp.rast);
    G_close_cell(tmp.fd);

    G_free(out->rast);
    G_close_cell(out->fd);

    G_remove("cats", out->name);
    G_remove("cell", out->name);
    G_remove("cellhd", out->name);
    G_remove("cell_misc", out->name);
    G_remove("hist", out->name);

    G_rename("cats", tmp.name, out->name);
    G_rename("cell", tmp.name, out->name);
    G_rename("cellhd", tmp.name, out->name);
    G_rename("cell_misc", tmp.name, out->name);
    G_rename("hist", tmp.name, out->name);

    return;
}

/**********************************************************
 *
 * Cloud shadows
 *
 **********************************************************/

int shadow_algorithm(double pixel[])
{
//     return NO_DEFINED;

    if( pixel[BAND3] < 0.07
        && (1 - pixel[BAND4]) * pixel[BAND6] > 240.
        && pixel[BAND4] / pixel[BAND2] > 1.         // Quita agua 1
//         && (pixel[BAND3] - pixel[BAND5]) / (pixel[BAND3] + pixel[BAND5]) < 0.10
         )
    {
        return IS_SHADOW;
    }

    return NO_DEFINED;
}
