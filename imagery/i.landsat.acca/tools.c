#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#include "local_proto.h"


/*--------------------------------------------------------
  HISTOGRAM ANALYSIS
  Define un factor de escala = hist_n/100 con objeto
  de dividir el entero 1 por 100/hist_n partes y
  aumentar la precision.

  Afecta al almacenamiento en el histograma pero
  modifica el calculo de quantiles y momentos.
 --------------------------------------------------------*/

/* Global variable
   allow use as parameter in the command line */
int hist_n = 100;		/* interval of real data 100/hist_n */

void hist_put(double t, int hist[])
{
    int i;

    /* scale factor */
    i = (int)(t * ((double)hist_n / 100.));

    if (i < 1)
	i = 1;
    if (i > hist_n)
	i = hist_n;

    hist[i - 1] += 1;
}

/* histogram moment */
double moment(int n, int hist[], int k)
{
    int i, j, total;
    double value, hmean, cte;

    k = 0;

    total = 0;
    hmean = 0.;
    for (i = 0; i < hist_n; i++) {
	total += hist[i];
	hmean += (double)(i * hist[i]);
    }
    hmean /= (double)total;	/* histogram mean */

    /*
       value = 0.;
       for( i = 0; i < hist_n; i++ )
       {
       cte = 1.;
       for( j = 0; j < n; j++ ) cte *= (i - hmean);
       value += cte * (double)hist[i]/(double)total;
       }

       /* remove scale factor *
       for( j = 0; j < n; j++ ) value /= ((double)hist_n/100.);
     */

    value = 0.;
    cte = 100. / ((double)hist_n * (double)(total - k));
    for (i = 0; i < hist_n; i++) {
	value += (pow((i - hmean), n) * (double)hist[i] * cte);
    }

    return value;
}

/* Real data mean */
double mean(int hist[])
{
    int i, total;
    double value, mean;

    total = 0;
    mean = 0.;
    for (i = 0; i < hist_n; i++) {
	total += hist[i];
	mean += (double)(i * hist[i]);
    }
    mean /= (double)total;

    /* remove scale factor */
    return (mean / ((double)hist_n / 100.));
}

/* Real data quantile */
double quantile(double q, int hist[])
{
    int i, total;
    double value, qmax, qmin;

    total = 0;
    for (i = 0; i < hist_n; i++) {
	total += hist[i];
    }

    qmax = 1.;
    for (i = hist_n - 1; i >= 0; i--) {
	qmin = qmax - (double)hist[i] / (double)total;
	if (q >= qmin) {
	    value = (q - qmin) / (qmax - qmin) + (i - 1);
	    break;
	}
	qmax = qmin;
    }

    /* remove scale factor */
    return (value / ((double)hist_n / 100.));
}
