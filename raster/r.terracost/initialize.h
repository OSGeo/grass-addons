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


/* The initialize module deals with the loading of a raster map from
   GRASS formatting and changing it into an AMI_STREAM and boundary
   structure to be used by the tile factory. */



#ifndef __INITIALIZE_H
#define __INITIALIZE_H

extern "C" {
#include <grass/gis.h>
}
#include <grass/iostream/ami.h>

#include "types.h"
#include "common.h"
#include "input.h"
#include "boundary.h"
#include "tile.h"
//#include "pq.h"
#include "pqueue.h"


/*
  loadCell takes a raser point and translates the value to a cost_type
  and returns it. loadCell also sets the isnull variable to 1 if the
  point is a null point.
*/
cost_type loadCell (void *inrast, RASTER_MAP_TYPE data_type, int *isnull, 
		    dimension_type j);

/*
  Given a source raster map row and a column coordinate, returns 1 if the
  point is a source, 0 otherwise
*/
int checkSource (void *inrastSource, RASTER_MAP_TYPE data_type_source, 
		 dimension_type j);

/*
  This method loads a raster grid for reading and then populates
  the tile factory.
*/
void  loadGrid (char* cellname, char* sourcename, long* nodata_count, 
		TileFactory *tf);

void loadNormalGrid(char* cellname, char* sourcename, long* nodata_count, 
		    cost_type** costGrid, cost_type** distGrid, 
		    pqheap_ijCost *pq);

#endif
