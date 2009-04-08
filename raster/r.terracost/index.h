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


#ifndef __index_H
#define __index_H

#include "common.h"
#include "types.h"
#include "tile.h"


off_t getFromIndex(dimension_type iFrom, dimension_type jFrom, const TileFactory *tf);

/* int getToIndex(dimension_type iFrom, dimension_type jFrom, dimension_type iTo, */
/* 	       dimension_type jTo, const TileFactory *tf); */

ijCost getNeighborRegionMarker(dimension_type i, dimension_type j, 
			       const TileFactory *tf);

int getSettledIndex(dimension_type i, dimension_type j, const TileFactory *tf);







#endif
