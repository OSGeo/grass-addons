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


#include "tileAbs.h"
#include "pq.h"
#include "pqueue.h"
#include "types.h"
#include "distanceType.h"
#include "updateAbs.h"

const int deltaRow[] = {0, 0, 0,-1,+1,-1,-1,+1,+1,-2,-2,-1,+1,+2,+2,+1,-1};
const int deltaCol[] = {0,-1,+1, 0, 0,-1,+1,+1,-1,-1,+1,+2,+2,+1,-1,-2,-2};
cost_type travMult[17] = {};

void
update_init(cost_type EW_fac, cost_type NS_fac, cost_type DIAG_fac) {
  travMult[0] = 0;
  travMult[1] = EW_fac / 2.0;
  travMult[2] = EW_fac / 2.0;
  travMult[3] = NS_fac / 2.0;
  travMult[4] = NS_fac / 2.0;
  travMult[5] = DIAG_fac / 2.0;
  travMult[6] = DIAG_fac / 2.0;
  travMult[7] = DIAG_fac / 2.0;
  travMult[8] = DIAG_fac / 2.0;
  //to be filled with knights move
}


void
updateNeighbors(const Tile* inT, costStructure costStr, 
		pqheap_ijCost *pq,
		cost_type **dist) {

  dimension_type thisRow = costStr.getI();
  dimension_type thisCol = costStr.getJ();
  assert(thisRow != dimension_type_max && thisCol != dimension_type_max); 
  cost_type thisDist = dist[thisRow][thisCol];

  cost_type thisCost = inT->get(thisRow,thisCol).getCost();
  if (thisCost == NODATA) return; 

  //Taken from original r.cost module
  const int numNeighbors = 8; // 16 if knight's move is used.
  //dimension_type row=dimension_type_max, col=dimension_type_max;
  for(int neighborIndex=1; neighborIndex <= numNeighbors; neighborIndex++) {
    
    signed_dim_t row = thisRow + deltaRow[neighborIndex];
    signed_dim_t col = thisCol + deltaCol[neighborIndex];
    if( !(INTILE(inT,row,col)) ) {
      continue;
    }
    cost_type *dp = &dist[row][col]; // current estimate
    const costSourceType & neighbor = inT->get(row,col);
    if (neighbor.isNull()) {
      continue;
    }
    
//     neighborCost = neighbor.getCost().getCost();
//     traversalCost = (cost_type)(neighborCost + thisCost) / 2.0 ;
//     neighborDist = thisDist + traversalCost * opt->travMult[neighborIndex];

	// travMult already includes 0.5 factor
    cost_type neighborDist = thisDist + (neighbor.getCost() + thisCost) * travMult[neighborIndex];
    //At this point we have all of the information for a particular neighbor
    if (neighborDist < *dp) {
      *dp = neighborDist;
      pq->insert(costStructure( neighborDist, row, col));
    }
  } //for 
#if 0
  {
	dim_t row, col;
	cost_type *dp;
	cost_type neighborDist;

	row = thisRow;
	col = thisCol;
	dp = &dist[row][col]; // current estimate

	if(INTILE(inT,row,col)) {
	  const costSourceType & neighbor = inT->get(row,col);
	  if(!neighbor.isNull()) {
		neighborDist = thisDist + (neighbor.getCost() + thisCost) * travMult[neighborIndex];
		//At this point we have all of the information for a particular neighbor
		if (neighborDist < *dp) {
		  *dp = neighborDist;
		  pq->insert(costStructure(neighborDist, row, col));
		}
	  }
	}
  }
#endif

}

