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

#include <ostream>

#include "types.h"
#include "input.h"
#include "genericTile.h"
#include "config.h"

/* this class bridges the gap between a mappedTile and the original Tile interface
 * also includes some debug output
 */
class Tile : public mappedTile<costSourceType> {
  /* this is a hack - we use the first point inserted to get the base values */
  int valid;

 public:
  Tile(dim_t inRows, dim_t inCols) :
	mappedTile<costSourceType>(inRows, inCols), valid(0) {};

  /* this is only called from tile.cc, boundaryMgr */
  void insert(dim_t i, dim_t j, ijCostSource & cost) {
	if(!valid) {
	  deriveBasis(cost, i, j);
	  valid = 1;
	}
	put(i, j, cost);
  };

  /* debugging */
  static void init(Tile *);
  int s2bWriteCount;
  int s2bPQCount;
  void dump();

  void printStats(ostream& str);
  

  /*
   * helpers; -1 on error; only valid inside tile - not on boundary
   * these are currently not used; perhaps will move soon.
   */

  /* tile point belongs to; -1 if error/boundary */
  int tileNum(const basicIJType & point) const {
	dim_t sizeCols = ((ncols-1)/cols)+1;
	dim_t tileNumI = point.getI()/(rows-1);
	dim_t tileNumJ = point.getJ()/(cols-1);
	return tileNumI + tileNumJ * sizeCols;
  };

  /* row in tile */
  dim_t tileRow(const basicIJType & point) const {
	return (point.getI() % (rows - 1));
  };

  /* col in tile */
  dim_t tileCol(const basicIJType & point) const {
	return (point.getJ() % (cols - 1));
  };
			  

};

