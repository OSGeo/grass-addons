/***********************************************************************/
/*
   find_horizon.h

   Revised by Mark Lake, 28/07/20017, for r.skyline in GRASS 7.x
   Revised by Mark Lake, 28/07/20017, for r.skyline in GRASS 7.x
   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 15/07/2002, for r.horizon in GRASS 5.x

   NOTES
   To debug this file #define DEBUG in global_vars.h because you also
   need debug-only functions in list.c

 */

/***********************************************************************/

#ifndef FIND_HORIZON_H
#define FIND_HORIZON_H

#include "list.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

int Find_horizon(struct node *, struct node *);

/* Find_horizon (pointer to head, pointer to tail)
   returns 1 on success, 0 if no edges in list */

#endif
