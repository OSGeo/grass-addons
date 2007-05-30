
/****************************************************************
 *
 * MODULE:     v.generalize
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    Definition of a point in 3D and basic operations
 *             with points 
 *
 * COPYRIGHT:  (C) 2002-2005 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#ifndef POINT_H
#define POINT_H

#include <grass/Vect.h>

typedef struct
{
    double x, y, z;
} POINT;

typedef struct Point_list
{
    POINT p;
    struct Point_list *next;
} POINT_LIST;

extern inline void point_subtract(POINT a, POINT b, POINT * res);
extern inline void point_add(POINT a, POINT b, POINT * res);
extern double point_dot(POINT a, POINT b);
extern inline double point_dist2(POINT a);
extern inline void point_assign(struct line_pnts *Points, int index, int with_z,
				POINT * res);
extern inline void point_scalar(POINT a, double k, POINT * res);
extern inline void points_copy_last(struct line_pnts *Points, int pos);
extern inline double point_dist(POINT a, POINT b);
extern POINT_LIST *point_list_new(POINT p);
extern void point_list_add(POINT_LIST * l, POINT p);
/* return 0 on success, -1 on out of memory */
extern int point_list_copy_to_line_pnts(POINT_LIST l, struct line_pnts *Points);

#endif
