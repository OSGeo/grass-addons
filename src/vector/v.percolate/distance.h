/***********************************************************************/
/*
   distance.h

   Revised by Mark Lake, 20/02/2018, for r.percolate in GRASS 7.x
   Written by Mark Lake and Theo Brown

   NOTES

 */

/***********************************************************************/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/vector.h>

#include "global_vars.h"
#include "node.h"

#ifndef DISTANCE_H
#define DISTANCE_H

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

float **initialiseDistanceMatrix(long int);

/* float** DistanceMatrix initialiseDistanceMatrix (long int numpoints) */

void freeDistanceMatrix(long int, float **);

/* float** freeDistanceMatrix (long int numpoints, float **matrix) */

float computeDistanceMatrix(float **, long int, node *);

/* float computeDistanceMatrix (float** matrix, long int numpoints, node* nodes
 */

float computeMaxDistanceToNN(float **, long int, float, node *);

/*float computeMaxDistanceToNN (float** matrix, long int numpoints,
   float maxGlobalDistance, node* nodes) */

void printDistanceMatrix(float **, long int);

/* float printDistanceMatrix (float** matrix, long int numpoints) */

void printDistanceMatrixWithNodeCats(float **, long int, node *);

/* float printDistanceMatrix (float** matrix, long int numpoints, node*
 * nodeList) */

#endif
