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


typedef struct
{
    struct Map_info Map;
    VARRAY *Varray;

    char *name;         /* in Map_info also */
    char *mapset;       /* in Map_info also */

    int layer;          /* category layer */

    char *cats;			/* list of categories */
    char *where;		/* SQL where condition (without WHERE key word) */

    char masked;

    int id;
    int type;           /* POINTS, LINES, AREAS */
    void *data;         /* VPOINTS, VLINES, VAREAS */

    char *label;        /* label in legend */
    int lpos;           /* position in legend */

} VECTOR;

#endif
