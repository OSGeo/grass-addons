/*
   The following routines are written and tested by Stefano Merler

   for

   structure Pca management
 */


#include <grass/gis.h>
#include "global.h"
#include <stdlib.h>
#include <string.h>


void inizialize_pca(pca, dim)
     /* 
        alloc memory for Pca structure pca of dimension dim
      */
     Pca *pca;
     int dim;
{
    int i;

    pca->n = dim;
    pca->mean = (double *)G_calloc(dim, sizeof(double));
    pca->sd = (double *)G_calloc(dim, sizeof(double));
    pca->covar = (double **)G_calloc(dim, sizeof(double *));
    for (i = 0; i < dim; i++)
	pca->covar[i] = (double *)G_calloc(dim, sizeof(double));
    pca->eigmat = (double **)G_calloc(dim, sizeof(double *));
    for (i = 0; i < dim; i++)
	pca->eigmat[i] = (double *)G_calloc(dim, sizeof(double));
    pca->eigval = (double *)G_calloc(dim, sizeof(double));
}

void write_pca(fp, pca)
     /* write a pca structure into the file pointed */
     FILE *fp;
     Pca *pca;
{
    int i, j;

    fprintf(fp, "eigenvalues:\n");
    fprintf(fp, "%f", pca->eigval[0]);
    for (i = 1; i < pca->n; i++) {
	fprintf(fp, "\t%f", pca->eigval[i]);
    }
    fprintf(fp, "\n");
    fprintf(fp, "eigenvectors (by column):\n");
    for (i = 0; i < pca->n; i++) {
	fprintf(fp, "%f", pca->eigmat[i][0]);
	for (j = 1; j < pca->n; j++)
	    fprintf(fp, "\t%f", pca->eigmat[i][j]);
	fprintf(fp, "\n");
    }
}

void read_pca(fp, pca)
     /* raed a pca structure from the file pointed */
     FILE *fp;
     Pca *pca;
{
    int i, j;
    char *line = NULL;

    pca->eigval = (double *)G_calloc(pca->n, sizeof(double));
    pca->eigmat = (double **)G_calloc(pca->n, sizeof(double *));
    for (i = 0; i < pca->n; i++) {
	pca->eigmat[i] = (double *)G_calloc(pca->n, sizeof(double));
    }

    line = GetLine(fp);
    line = GetLine(fp);
    line = GetLine(fp);
    for (i = 0; i < pca->n; i++) {
	sscanf(line, "%lf", &(pca->eigval[i]));
	line = (char *)strchr(line, '\t');
	*line++;
    }
    line = GetLine(fp);
    for (j = 0; j < pca->n; j++) {
	line = GetLine(fp);
	for (i = 0; i < pca->n; i++) {
	    sscanf(line, "%lf", &(pca->eigmat[j][i]));
	    line = (char *)strchr(line, '\t');
	    *line++;
	}
    }
}
