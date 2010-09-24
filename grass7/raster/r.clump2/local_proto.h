
/****************************************************************************
 *
 * MODULE:       r.clump
 *
 * AUTHOR(S):    Michael Shapiro - CERL
 *
 * PURPOSE:      Recategorizes data in a raster map layer by grouping cells
 *               that form physically discrete areas into unique categories.
 *
 * COPYRIGHT:    (C) 2006 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 ***************************************************************************/

#ifndef __LOCAL_PROTO_H__
#define __LOCAL_PROTO_H__

#include <grass/gis.h>
#include <grass/raster.h>
#include "flag.h"
#include "ramseg.h"

extern long pqsize;
extern CELL *clump_id;

/* pq.c */
int init_pq(long);
int free_pq(void);
int add_pnt(long);
long drop_pnt(void);


#endif /* __LOCAL_PROTO_H__ */
