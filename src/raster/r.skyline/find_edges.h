/***********************************************************************/
/*
   find_edges.h

   Revised by Mark Lake, 28/07/20017, for r.skyline in GRASS 7.x
   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 15/07/2002, for r.horizon in GRASS 5.x

 */

/***********************************************************************/

#ifndef FIND_EDGES_H
#define FIND_EDGES_H

#include "list.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

void find_edges(int, int, void *, struct node *);

/* find_edges (num rows, num cols, ptr to map buf, ptr to list of edges,
   terse flag) */

#endif
