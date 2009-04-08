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

#include "update.h"

/*                     0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
*/


void normalUpdateNeighbors(costStructure costStr, 
			   pqheap_ijCost *pq,
			   cost_type **distGrid,
			   cost_type** costGrid) {

  dimension_type thisRow = costStr.getI();
  dimension_type thisCol = costStr.getJ();
  cost_type thisCost = costGrid[thisRow][thisCol];
  cost_type thisDist = distGrid[thisRow][thisCol];

  cost_type neighborCost;
  cost_type neighborDist;
  cost_type oldNeighborDist;

  //cost_type traversalCost;
  int numNeighbors = 8; // 16 if knight's move is used.

  //Taken from original r.cost module
  //dimension_type row=dimension_type_max, col=dimension_type_max;
  for(int neighborIndex=1;neighborIndex<=numNeighbors;neighborIndex++ ) {
      
	signed_dim_t row = thisRow + deltaRow[neighborIndex];
	signed_dim_t col = thisCol + deltaCol[neighborIndex];
      
	assert(row != dimension_type_max && col != dimension_type_max);	// -RW
				
	if ( row < 0 || row >= nrows) {
	  continue ;
	}
	if( col < 0 || col >= ncols) {
	  continue;
	}

	if (costGrid[row][col] == NODATA) {
	  continue;
	}

	neighborCost = costGrid[row][col];
	// travMult already include 0.5 factor
	neighborDist = thisDist + (neighborCost + thisCost) * travMult[neighborIndex];
	oldNeighborDist = distGrid[row][col];
	
	if (neighborDist < oldNeighborDist && thisCost != NODATA) {
	  distGrid[row][col] = neighborDist;
	  pq->insert(costStructure(neighborDist,row, col));
	}
  }
}




/* ---------------------------------------------------------------------- */
	// The following cases(9-16) are only used for the knight's move
	/*
	  
	case 9:
	value = &NNW ;
	segment_get(&in_seg,value,row,col);
	fcost = (double)(N + NW + NNW + my_cost) / 4.0 ;
	min_cost = thisCell->min_cost+fcost*V_DIAG_fac ;
	break ;
	case 10:
	value = &NNE ;
	segment_get(&in_seg,value,row,col);
	fcost = (double)(N + NE + NNE + my_cost) / 4.0 ;
	min_cost = thisCell->min_cost+fcost*V_DIAG_fac ;
	break ;
	case 11:
	value = &SSE ;
	segment_get(&in_seg,value,row,col);
	fcost = (double)(S + SE + SSE + my_cost) / 4.0 ;
	min_cost = thisCell->min_cost+fcost*V_DIAG_fac ;
	break ;
	case 12:
	value = &SSW ;
	segment_get(&in_seg,value,row,col);
	fcost = (double)(S + SW + SSW + my_cost) / 4.0 ;
	min_cost = thisCell->min_cost+fcost*V_DIAG_fac ;
	break ;
	case 13:
	value = &WNW ;
	segment_get(&in_seg,value,row,col);
	fcost = (double)(W + NW + WNW + my_cost) / 4.0 ;
	min_cost = thisCell->min_cost+fcost*H_DIAG_fac ;
	break ;
	case 14:
	value = &ENE ;
	segment_get(&in_seg,value,row,col);
	fcost = (double)(E + NE + ENE + my_cost) / 4.0 ;
	min_cost = thisCell->min_cost+fcost*H_DIAG_fac ;
	break ;
	case 15:
	value = &ESE ;
	segment_get(&in_seg,value,row,col);
	fcost = (double)(E + SE + ESE + my_cost) / 4.0 ;
	min_cost = thisCell->min_cost+fcost*H_DIAG_fac ;
	break ;
	case 16:
	value = &WSW ;
	segment_get(&in_seg,value,row,col);
	fcost = (double)(W + SW + WSW + my_cost) / 4.0 ;
	min_cost = thisCell->min_cost+fcost*H_DIAG_fac ;
	break ;
	
	*/





/* ---------------------------------------------------------------------- */
void
updateInterNeighbors(costStructureOld cs, const SettleLookup & settled,
					 EMPQueueAdaptive<costStructureOld, costPriorityOld> *pq, 
					 AMI_STREAM<distanceType> *b2bstr, const TileFactory *tf,
					 const BoundaryType<cost_type> *phase2Bnd ) {
  
  AMI_err ae;
  assert(!isNull(cs.getPriority().getDist()));

  dimension_type thisRow = cs.getI();
  dimension_type thisCol = cs.getJ();
  cost_type thisCost = cs.getPriority().getDist();
  costStructureOld outCS;
  ijCost neighbor;
  dimension_type neighborI, neighborJ;
  cost_type neighborCost, neighborDist;
  int numNeighbors = tf->getNumNeighbors(thisRow, thisCol);
  off_t marker = getFromIndex(thisRow,thisCol, tf);

  distanceType *dType;
//   if (marker >= b2bstr->stream_len()) {
//       cout << "ThisRow: " << thisRow << " ThisCol: " << thisCol << endl;
//       cout << "Marker: " << marker << endl; cout.flush();
//       cout << "Index: " << marker << " Stream length: " << 
// 	b2bstr->stream_len() << "\n";cout.flush();
//     }
//     assert (marker < b2bstr->stream_len());

  ae = b2bstr->seek(marker);
  
  

  for (int a = 0; a<numNeighbors && ae == AMI_ERROR_NO_ERROR; a++) {
//     if (a+marker >= b2bstr->stream_len()) {
//       cout << "ThisRow: " << thisRow << " ThisCol: " << thisCol << endl;
//       cout << "A: " << a << " Marker: " << marker << endl; cout.flush();
//       cout << "Index: " << a+marker << " Stream length: " << 
// 	b2bstr->stream_len() << "\n";cout.flush();
//     }
//     assert (a+marker < b2bstr->stream_len());
    ae = b2bstr->read_item(&dType);
    assert(ae == AMI_ERROR_NO_ERROR);
    neighborI = dType->getToI();
    neighborJ = dType->getToJ();

    if (dType->getFromI() != cs.getI() || dType->getFromJ() != cs.getJ()) {
      cerr << "updateInterNeighbors: ERROR Stream: " << *dType << " PQ: "
	   << cs << endl;
      assert(0);
      exit(1);
    }

    if (!isNull(neighborI) && !isNull(neighborJ) && 
		!isNull(dType->getDistance()) && 
		!settled.isSettled(neighborI, neighborJ, tf)) {
      int doInsert = 1;
	  neighborCost = thisCost + dType->getDistance();

	  // if we have an in-memory boundary, make use of it!
	  if(phase2Bnd->canGetFast(neighborI, neighborJ)) {
		ijCost curCost;
		((BoundaryType<cost_type>*)phase2Bnd)->get(neighborI, neighborJ, &curCost);
		if(curCost.getCost() <= neighborCost) {
		  doInsert = 0;			// squash insert
		}
	  }

	  if(doInsert) {
		neighbor = ijCost(neighborI, neighborJ, neighborCost);
		outCS = costStructureOld(neighbor);
		pq->insert(outCS);
		//cout << "updateInterNeighbors::inserting: " << outCS << " from " << cs 
		//	   << endl;cout.flush();
	  }

    }
  }
}


/* ---------------------------------------------------------------------- */

SettleLookup::SettleLookup(dim_t nrowsPad, dim_t ncolsPad, const TileFactory *tf) {
  /*settledSize is the size of the settled index. It is computed by
    asking for the index of the last item in the array to be inserted
    in the array*/

  size = getSettledIndex(nrowsPad-1, ncolsPad-1, tf) + 1;
  cerr << "Settle Size: " << size << " (" << nrowsPad << " x " << ncolsPad << ")" << endl;

  /*settledArray is an array of 1s or 0s depending if a point is
    settled or not respectivly */
  arr = new int[size];
  for (int i = 0; i < size; i++) {
    arr[i] = 0;
  }
}

SettleLookup::~SettleLookup() {
  delete arr;
}
