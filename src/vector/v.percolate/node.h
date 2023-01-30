/***********************************************************************/
/*
   node.h

   Revised by Mark Lake, 20/02/2018, for r.percolate in GRASS 7.x
   Written by Mark Lake and Theo Brown

   NOTES

 */

/***********************************************************************/

#ifndef NODE_H
#define NODE_H

#include <stdio.h>

#define NAME_LEN 256

/***********************************************************************/
/* Types                                                               */

/***********************************************************************/

typedef struct node
    node; /* We must do this to allow type node to reference itself */
struct node {
    int cat; /* This is to store actual vector map id (the cat value) */
    int group;
    int first_change;       /* iteration when first allocated to group */
    int last_change;        /* iteration when last (re)allocated to group */
    int count_changes;      /* number of (re)allocations to group(s) */
    int nn;                 /* index of nearest neighbour */
    float first_distance;   /* distance at which first allocated to group */
    float last_distance;    /* distance at which last (re)allocated to group */
    int lastGroupConnected; /* id of other group (membership > 1) which this
                               node last connected */
    float lastDistanceConnection; /* distance at which last connected 2
                                     groups (both membershop > 1)  */
    float max_connect;            /* connection coefficient */
    node *nGroup;
    node *pGroup;
    float x; /* Might ultimately want to split coords into separate
                array so that we can delete them to save memory */
    float y;
    char name[NAME_LEN + 1];
};

typedef struct {
    int id;     /* Could save memory by omitting this; useful for
                   debugging */
    int from;   /* Array index of node (not the id) */
    int to;     /* Array index of node (not the id) */
    float dist; /* Speed things up by using squared distances */
} edge;

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

node *constructNodeArray(long int);

void getMinMaxNNdistances(node *, long int, float, float *, float *);

/* void getMinMaxNNdistances (node* nodes, long int numpoints, float maxdist,
 * float* minNNdist, float* maxNNdist) */

void setNodeMaxConnect(node *, int, float);

/* void setNodeMaxConnect (node* nodes, int node, int oldGroupSize) */

void setNodeLastGroupConnected(node *, int, int);

/* void setNodeLastConnected (node* nodes, int node, int groupConnected) */

void setNodeLastDistanceConnection(node *, int, float);

/* void setNodeLastDistanceConnection (node* nodes, int node, float
 * groupConnectionDistance) */

#endif
