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

#include "types.h"
#include "input.h"
#include "pqueue.h"
#include "tileAbs.h"
#include "updateAbs.h"
#include "dijkstraAbs.h"

#include <assert.h>


/*
 * run dijkstra on a tile, starting at point start_i, start_j
 * use the (empty) costpq; use the dist array
 * expect to see bndExpect boundary points
 */
void
dijkstraAbs(Tile *tile, int start_i, int start_j,
			pqheap_ijCost *costpq, cost_type** dist,
			int bndExpected,
			long *extractsIn, long *updatesIn) {
  long extracts = 0;
  long updates = 0;

  if (tile->get(start_i, start_j).isNull()) {
	return;
  }

  costStructure currentVertex;
  dim_t tileSizeRows = tile->getNumRows();
  dim_t tileSizeCols = tile->getNumCols();

  //initialize dist grid
  for (int l=0; l<tileSizeRows; l++) {
	for (int m=0; m<tileSizeCols; m++) {
	  dist[l][m] = cost_type_max;
	}
  }
  dist[start_i][start_j] = 0;
  assert(costpq->empty());
  costpq->insert(costStructure(0.0, start_i, start_j));	// start point
	
  while (!costpq->empty() && bndExpected > 0) {
	costpq->extract_min(&currentVertex);
	assert(currentVertex.getPriority() >= 0);
	extracts++;

	dim_t i, j;
	i = currentVertex.getI();
	j = currentVertex.getJ();
    cost_type *dp = &dist[i][j]; // current estimate

	// skip if NODATA
	if(tile->get(i,j).getCost() == NODATA) {
	  continue;
	}

	if (*dp >= currentVertex.getPriority()) {
	  updates++;
	  *dp = currentVertex.getPriority();
	  updateNeighbors(tile, currentVertex, costpq, dist);
	  // optimization - break out when we see all non-null boundaries
	  if (tile->isBoundary(i,j) && i >= start_i && j >= start_j) {
		bndExpected--;
	  }
	}
  } //	while (!costpq->empty())

  *extractsIn += extracts;
  *updatesIn += updates;
}

