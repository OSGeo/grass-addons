/****************************************************************
 * MODULE:     v.path.obstacles
 *
 * AUTHOR(S):  Maximilian Maldacker
 *  
 *
 * COPYRIGHT:  (C) 2002-2005 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/
#ifndef VISIBILITY_H
#define VISIBILITY_H


#include <stdlib.h>
#include <assert.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/Vect.h>
#include "rotation_tree.h"

void load_lines( struct Map_info *map, struct Point ** points, int * num_points, struct Line ** lines, int * num_lines );
void process_boundary( struct line_pnts * sites, struct Point ** points, int * index_point, struct Line ** lines, int * index_line, int cat);
void process_line( struct line_pnts * sites, struct Point ** points, int * index_point, struct Line ** lines, int * index_line, int cat);

int construct_visibility( struct Point * points, int num_points, struct Line * lines, int num_lines, struct Map_info* out );
int cmp_points(struct Point * v1, struct Point* v2);

int turn_left( struct Point p1, struct Point p2, struct Point p3 );

void handle( struct Point* p, struct Point* q, struct Map_info * out );
void report( struct Point * p, struct Point * q, struct Map_info * out );

void init_vis( struct Point * points, int num_points, struct Line * lines, int num_lines );

struct Point * pop();
struct Point * top();
void push(struct Point * p);
int empty_stack();
void init_stack();

void quickSort( struct Point a[], int l, int r);
int partition( struct Point a[], int l, int r);

static int stack_index;
static struct Point ** stack;

#endif
