/***********************************************************************/
/*
   global_vars.h

   Revised by Mark Lake, 20/02/2018, for r.percolate in GRASS 7.x
   Written by Mark Lake and Theo Brown

   NOTES

 */

/***********************************************************************/

/* #define VALIDATE */

#include "node.h"
#include "groups.h"

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

GLOBAL int overwrite;
GLOBAL int exitFullyConnected;
GLOBAL int doName;
GLOBAL char input_id_col[1024];
GLOBAL char keepGroup[10];
GLOBAL int nEdges;
GLOBAL int ownGroup;
GLOBAL node *nodeList;
GLOBAL node **groupList;
GLOBAL edge *edgeList;
GLOBAL int *groupSize;
GLOBAL tGroupInfo *groupInfo;
