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

#ifndef _UPDATE_H
#define _UPDATE_H

extern "C" {
#include <grass/gis.h>
}

#include <grass/iostream/ami.h>
#include "tile.h"
#include "pqueue.h"
#include "types.h"
#include "distanceType.h"
#include "pq.h"
#include "index.h"

#include "updateAbs.h"
#include "boundary.h"

class SettleLookup {
  int *arr;
  int size;

 public:
  SettleLookup(dim_t nrowsPad, dim_t ncolsPad, const TileFactory *tf);
  ~SettleLookup();


  int isSettled(dim_t i, dim_t j, const TileFactory *tf) const {
	int index = getSettledIndex(i, j, tf);
#ifndef NDEBUG
	if(index >= size) {
	  fprintf(stderr, "index (%d) out of bounds (%d)\n", index, size);
	  fprintf(stderr, "while checking point i=%d, j=%d\n", i, j);
	  fprintf(stderr, "tsr=%d, tsc=%d, nbrows=%d, nbcols=%d\n", 
		  tf->getRows(), tf->getCols(), tf->getBndrows(), tf->getBndcols());
	}
#endif
	assert(index < size);
	return arr[index];
  };

  void settlePoint(dim_t i, dim_t j, const TileFactory *tf) {
	int index = getSettledIndex(i, j, tf);
	assert(index < size);
	arr[index] = 1;
	//cout << "Point " << i << "," << j << " settled" << endl;cout.flush();
  };

};


void normalUpdateNeighbors(costStructure costStr, 
			   pqheap_ijCost *pq,
			   cost_type **distGrid, cost_type** costGrid);

void updateInterNeighbors(costStructureOld cs, const SettleLookup & ar,
						  EMPQueueAdaptive<costStructureOld, costPriorityOld> *pq, 
						  AMI_STREAM<distanceType> *b2bstr, 
						  const TileFactory *tf,
						  const BoundaryType<cost_type> *phase2Bnd );

#endif
