/*
   The following routines are written and tested by Stefano Merler

   for

   bootstrap, probabily based, samples estraction
 */

#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <grass/gis.h>
#include "global.h"

void Bootsamples(n, prob, random_labels)
     /*
        given an array of probabilities of length n, extract a bootstrap sample
        of n elements according to the vector of probabilities
      */
     int n;
     double *prob;
     int *random_labels;

{
    int i, j;
    int *random_labels_flag;
    double *random;
    double *cumprob;
    double probtot = .0;

    for (i = 0; i < n; i++)
	probtot += prob[i];
    for (i = 0; i < n; i++)
	prob[i] /= probtot;

    random_labels_flag = (int *)calloc(n, sizeof(int));
    random = (double *)calloc(n, sizeof(double));
    cumprob = (double *)calloc(n, sizeof(double));

    for (i = 0; i < n; ++i) {
	random[i] = (double)drand48();
	random_labels[i] = n - 1;
	random_labels_flag[i] = 0;
    }


    for (i = 0; i < n; i++) {
	if (i > 0)
	    cumprob[i] = cumprob[i - 1] + prob[i];
	else
	    cumprob[0] = prob[0];

	for (j = 0; j < n; j++) {

	    if (random[j] < cumprob[i])
		if (random_labels_flag[j] == 0) {
		    random_labels[j] = i;
		    random_labels_flag[j] = 1;
		}
	}
    }

    free(random);
    free(cumprob);
    free(random_labels_flag);
}


void Bootsamples_rseed(n, prob, random_labels, idum)
     /*
        given an array of probabilities of length n, extract a bootstrap sample
        of n elements according to the vector of probabilities
      */
     int n;
     double *prob;
     int *random_labels;
     int *idum;

{
    int i, j;
    int *random_labels_flag;
    double *random;
    double *cumprob;
    double probtot = .0;

    for (i = 0; i < n; i++)
	probtot += prob[i];
    for (i = 0; i < n; i++)
	prob[i] /= probtot;

    random_labels_flag = (int *)calloc(n, sizeof(int));
    random = (double *)calloc(n, sizeof(double));
    cumprob = (double *)calloc(n, sizeof(double));

    for (i = 0; i < n; ++i) {
	random[i] = (double)ran1(idum);
	random_labels[i] = n - 1;
	random_labels_flag[i] = 0;
    }


    for (i = 0; i < n; i++) {
	if (i > 0)
	    cumprob[i] = cumprob[i - 1] + prob[i];
	else
	    cumprob[0] = prob[0];

	for (j = 0; j < n; j++) {

	    if (random[j] < cumprob[i])
		if (random_labels_flag[j] == 0) {
		    random_labels[j] = i;
		    random_labels_flag[j] = 1;
		}
	}
    }

    free(random);
    free(cumprob);
    free(random_labels_flag);
}
