/***********************************************************************/
/*
   sort.h

   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 15/07/2002, for r.horizon in GRASS 5.x

   NOTES

   Mergesort uses algorithm from R. Sedgewick, 1990, 'Algorithms in C',
   Reading, MA: Addison Wesley

   When used with the functions in list.c, the mergesort functions
   require that the first data node in the list be passed as the 'head'
   and they return a pointer to the first data node.  Do not pass the
   address of the head node to the mergesort functions.  Similarly, do
   not attempt to set a pointer to the head node to the value returned
   by the mergesort functions.

 */

/***********************************************************************/

#ifndef SORT_H
#define SORT_H

#include "list.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

struct node *Mergesort_increasing_smallest_azimuth(struct node *,
                                                   struct node *);
/* Mergesort_increasing_smallest_azimuth (pointer to first data node
   in 'next smallest' list, pointer to tail)
   Returns pointer to first data node in 'next smallest' list */

void Pseudo_sort_decreasing_smallest_azimuth(struct node *head,
                                             struct node *tail);
/* Pseudo_sort_decreasing_smallest_azimuth (pointer to head,
   pointer to tail) */

struct node *Mergesort_increasing_largest_azimuth(struct node *, struct node *);
/* Mergesort_increasing_largest_azimuth (pointer to first data node
   in 'next largest' list, pointer to tail)
   Returns pointer to first data node in 'next largest' list */

void Pseudo_sort_decreasing_largest_azimuth(struct node *head,
                                            struct node *tail);
/* Pseudo_sort_decreasing_largest_azimuth (pointer to head,
   pointer to tail) */

struct node *Mergesort_increasing_centre_horizon_azimuth(struct node *,
                                                         struct node *);
/* Mergesort_increasing_centre_horizon_azimuth  (pointer to first data node
   in 'next horizon' list, pointer to tail)
   Returns pointer to first data node in 'next horizon' list */

#endif
