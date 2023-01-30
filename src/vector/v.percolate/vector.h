/***********************************************************************/
/*
   vector.h

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
#include "edge_array.h"
#include "groups.h"

#ifndef VECTOR_H
#define VECTOR_H

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

long int read_input_vector(char *, char *);

#endif
