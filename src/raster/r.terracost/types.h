/* 

   Copyright (C) 2006 Thomas Hazel, Laura Toma, Jan Vahrenhold and
   Rajiv Wickremesinghe

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

*/

#ifndef _types_H
#define _types_H

#include <limits.h>
#include <float.h>
#include <iostream>

using namespace std;


/* represent dimension of the grid */ 

/* this can deal with grids of dimensions up to 32767 */
typedef short dim_t; 
static const dim_t dimension_type_max = (SHRT_MAX - 2);

/* this can deal with grids of dimensions up to 65536 */
/* typedef unsigned short dim_t; */ 
/* static const dim_t dimension_type_max = (USHRT_MAX - 2); */




typedef int signed_dim_t;		/* should ONLY be used temp structures */

typedef dim_t dimension_type;
static const dim_t dim_undef = USHRT_MAX;

/*  typedef int dimension_type; */ /* represent dimension of the grid */
/* static const dimension_type dimension_type_max=INT_MAX; */



typedef  float cost_type;  /* represent the cost of a cell */
static const cost_type cost_type_max=FLT_MAX;


typedef float dist_type; /* represent the sp(shortest path) of a cell */

#endif

