/***********************************************************************/
/*
   distance.c

   Revised by Mark Lake, 20/09/2018, for r.percolate in GRASS 7.x
   Written by Mark Lake and Theo Brown

   NOTES

 */

/***********************************************************************/

#include "distance.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

float **initialiseDistanceMatrix(long int numpoints)
{
    float **matrix;
    int i;

    matrix = (float **)G_malloc(sizeof(float *) * numpoints);
    for (i = 0; i < numpoints; i++) {
        matrix[i] = (float *)G_malloc(sizeof(float) * numpoints);
    }

    return matrix;
}

/***********************************************************************/

void freeDistanceMatrix(long int numpoints, float **matrix)
{
    int i;

    for (i = 0; i < numpoints; i++) {
        G_free(matrix[i]);
    }
    G_free(matrix);
}

/***********************************************************************/

float computeDistanceMatrix(float **matrix, long int numpoints, node *nodes)
{
    float mindist;
    float maxdist;
    int i, j;

#ifdef VALIDATE
    int geodesic;

    geodesic = (G_projection() == PROJECTION_LL);
    G_message(_("The projection code is %d\n"), geodesic);
#endif

    if (!G_begin_distance_calculations()) {
        G_fatal_error(_("Failed to initiate distance calculation"));
    }

    mindist = G_distance(nodes[0].x, nodes[0].y, nodes[1].x, nodes[1].y);
    maxdist = 0.0;
    for (i = 0; i < (numpoints - 1); i++) {
        for (j = i + 1; j < numpoints; j++) {
            matrix[i][j] =
                G_distance(nodes[i].x, nodes[i].y, nodes[j].x, nodes[j].y);
            if (mindist > matrix[i][j]) {
                mindist = matrix[i][j];
            }
            if (maxdist < matrix[i][j]) {
                maxdist = matrix[i][j];
            }
        }
    }

    G_message(_("Computed distance matrix, min = %1.1f, max = %1.1f"), mindist,
              maxdist);
    return maxdist;
}

/***********************************************************************/

void printDistanceMatrix(float **matrix, long int numpoints)
{
    int i, j;

    fprintf(stderr, "\n\nThe distance matrix (labelled by node indices) is:");
    fprintf(stderr, "\n    ");
    for (i = 0; i < numpoints; i++) {
        fprintf(stderr, "%6d ", i);
    }
    for (j = 0; j < numpoints; j++) {
        fprintf(stderr, "\n%3d ", j);
        for (i = 0; i < (j + 1); i++) {
            fprintf(stderr, "%6.1f ", matrix[i][j]);
        }
    }
}

/***********************************************************************/

void printDistanceMatrixWithNodeCats(float **matrix, long int numpoints,
                                     node *nodes)
{
    int i, j;

    fprintf(stderr, "\n\nThe distance matrix (labelled by node cats) is:");
    fprintf(stderr, "\n    ");
    for (i = 0; i < numpoints; i++) {
        fprintf(stderr, "%6d ", nodes[i].cat);
    }
    for (j = 0; j < numpoints; j++) {
        fprintf(stderr, "\n%3d ", nodes[j].cat);
        for (i = 0; i < (j + 1); i++) {
            fprintf(stderr, "%6.1f ", matrix[i][j]);
        }
    }
}
