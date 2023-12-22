/***********************************************************************/
/*
   percolate.h

   Revised by Mark Lake, 20/02/2018, for r.percolate in GRASS 7.x
   Written by Mark Lake and Theo Brown

   NOTES

 */

/***********************************************************************/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/vector.h>

#include "global_vars.h"
#include "node.h"
#include "groups.h"
#include "edge_array.h"
#include "file.h"

#ifndef PERCOLATE_H
#define PERCOLATE_H

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

void percolate(float, float, float, long int, char *, char *, int);

/* void percolateOneDistance (mindist, interval, maxdist, numpoints,
   text_file_name, group_text_file_name, Modulo) */
#endif
