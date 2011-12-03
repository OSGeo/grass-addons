#ifndef _VECTOR_H_
#define _VECTOR_H_

/* Header file: vector.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <grass/gis.h>
#include <grass/Vect.h>
#include "vareas.h"
#include "vlines.h"
#include "vpoints.h"
#include "vlabels.h"
#include "vlegend.h"


typedef struct
{
    int id;			/* rule identification */

    int count;			/* number of ranges in val_list */
    DCELL *val_list;		/* rule of numeric pertenence */

    float value;		/* associate value */
    char *label;		/* associated label */

} RULES;


typedef struct
{
    int rule;			/* identification/order of the item */
    long data;			/* data associate to the item */

} ITEMS;


typedef struct
{
    struct Map_info Map;
    VARRAY *Varray;

    char *name;			/* in Map_info also, 'none' to don't draw */
    char *mapset;		/* in Map_info also */

    int layer;			/* category layer */
    char *cats;			/* list of categories */
    char *where;		/* SQL where condition (without WHERE key word) */

    char masked;		/* masked or not by raster map */

    int id;
    int type;			/* POINTS, LINES, AREAS, LABELS */
    void *data;			/* VPOINTS, VLINES, VAREAS, VLABELS */

    /* legend management */
    char *label;		/* label */
    int lpos;			/* position */
    int cols;			/* number of columns */
    double width;		/* symbol width  */
    double xspan;		/* separation between columns */
    double yspan;		/* separation between rows */

    int n_item;
    ITEMS *item;		/* items make by the vector */

    int n_rule;
    RULES *rule;		/* rules to group items */

} VECTOR;

#endif
