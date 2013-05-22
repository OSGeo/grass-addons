/****************************************************************************
 *
 * MODULE:       r.findtheriver
 * AUTHOR(S):    Brian Miles - brian_miles@unc.edu
 *               with hints from: Glynn Clements - glynn gclements.plus.com
 * PURPOSE:      Finds the nearest stream pixel to a coordinate pair using
 * 				 an upstream accumulating area map.
 *
 * COPYRIGHT:    (C) 2013 by the University of North Carolina at Chapel Hill
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/

#ifndef __POINT_LIST_H__
#define __POINT_LIST_H__

#include <stdio.h>

typedef struct PointNode {
	int col;
	int row;
	struct PointNode *next;
} PointList_t;

PointList_t *create_list(int col, int row);
PointList_t *append_point(PointList_t * const head, int col, int row);
void destroy_list(PointList_t *head);
PointList_t *find_nearest_point(PointList_t * const head, int col, int row);
void print_list(FILE *fp, PointList_t * const head, const char* const sep);
#endif
