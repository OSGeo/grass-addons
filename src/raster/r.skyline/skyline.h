/***********************************************************************/
/*
   skyline.h

   Written by Mark Lake, 28/07/20017, for r.skyline in GRASS 7.x

 */

/***********************************************************************/

#ifndef SKYLINE_H
#define SKYLINE_H

#include <math.h>
#include "global_vars.h"
#include "list.h"
#include "azimuth.h"
#include "raster_file.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

double compute_skyline_index(int, int, double, struct node *, struct node *,
                             struct node *, struct node *, struct node *);

double compute_skyline_index_simple(int, int, double, struct node *);
#endif
