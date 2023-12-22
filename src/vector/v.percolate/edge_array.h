/***********************************************************************/
/*
   edge_array.h

   Revised by Mark Lake, 20/02/2018, for r.percolate in GRASS 7.x
   Written by Mark Lake and Theo Brown

   NOTES

 */

/***********************************************************************/

#ifndef EDGE_ARRAY_H
#define EDGE_ARRAY_H

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
#include "file.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

edge *initialiseEdgeArray(long int);
long int constructEdgeArray(edge *, float **, long int);
void copyEdgeArrayItem(edge *, edge *);
void printEdgeArrayWithNodeIndices(edge *, long int);
void printEdgeArrayWithNodeCats(edge *, long int, node *);
void printEdgeArrayWithNodeNames(edge *, long int, node *);
void sortEdgeArray(edge *);

/*void CSVoutput (node*, long int); */

#endif
