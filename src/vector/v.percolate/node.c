/***********************************************************************/
/*
   node.c

   Revised by Mark Lake, 20/02/2018, for r.percolate in GRASS 7.x
   Written by Mark Lake and Theo Brown

   NOTES

 */

/***********************************************************************/

#include <string.h>
#include <grass/gis.h>
#include "node.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

node *constructNodeArray(long int numpoints)
{
    node *nodes;

    nodes = (node *)G_malloc(sizeof(node) * numpoints);

    int i;

    for (i = 0; i < numpoints; i++) {
        nodes[i].cat = i; /* Will be overwritten with true values when reading
                             vector map */
        nodes[i].first_change = 0;
        nodes[i].last_change = 0;
        nodes[i].count_changes = 0;
        nodes[i].first_distance = -1.0;   /* Impossible value */
        nodes[i].last_distance = -1.0;    /* Impossible value */
        nodes[i].max_connect = -1.0;      /* Impossible value */
        nodes[i].lastGroupConnected = -1; /* Impossible value */
        strcpy(nodes[i].name, "");
        /* fprintf(stderr, "\nNode %d  x = %1.2f  y=%1.2f  group=%d",
         * nodes[i].cat, nodes[i].x, nodes[i].y, nodes[i].group); */
        /* } */
    }
    /* fprintf(stderr, "\n"); */
    /*fflush(stderr); */
    return nodes;
}

/***********************************************************************/

void getMinMaxNNdistances(node *nodes, long int numpoints, float maxdist,
                          float *minNNdist, float *maxNNdist)
{
    int i;
    float min, max;

    max = 0;
    min = maxdist;
    for (i = 0; i < numpoints; i++) {
        if ((nodes[i].first_distance < min) &&
            (nodes[i].first_distance != -1)) {
            min = nodes[i].first_distance;
        }
        if (nodes[i].first_distance > max) {
            max = nodes[i].first_distance;
        }
    }
    *minNNdist = min;
    *maxNNdist = max;
}

/***********************************************************************/

void setNodeMaxConnect(node *nodes, int node, float conCoef)
{

    if (nodes[node].max_connect < conCoef) {
        nodes[node].max_connect = conCoef;
    }
}

/***********************************************************************/

void setNodeLastGroupConnected(node *nodes, int node, int groupConnected)
{
    nodes[node].lastGroupConnected = groupConnected;
}

/***********************************************************************/

void setNodeLastDistanceConnection(node *nodes, int node,
                                   float groupConnectionDistance)
{
    nodes[node].lastDistanceConnection = groupConnectionDistance;
}
