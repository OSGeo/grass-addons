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

#if 0
/* Initializes the 2D array and the rows and cols variables */
OldTile::OldTile(dimension_type inRows, dimension_type inCols) {
  
  rows = inRows;
  cols = inCols;

  grid = new ijCostSource*[rows];
  assert(grid);
  for (int i=0; i<rows; i++) {
    grid[i] = new ijCostSource[cols];
    assert(grid[i]);
  }
}

/* Should I use some sort of grid copying function here or is the
   pointer OK? */
OldTile::OldTile(ijCostSource** inGrid, dimension_type inRows, 
		 dimension_type inCols) {

  rows = inRows;
  cols = inCols;

  grid = inGrid;

}

OldTile::~OldTile() {

  assert(grid);

 
  for (int i=0; i<rows; i++) {
    //cout << i << endl; cout.flush();
    assert(grid[i]);
    delete [] grid[i];
  }

  assert(grid);
  delete [] grid;

}

void
OldTile::insert(dimension_type i, dimension_type j, ijCostSource cost) {
  grid[i][j] = cost;
}



void
OldTile::printTile() {
  cout << "Rows: " << rows << " Cols: " << cols << "\n";
  for (int i = 0; i<rows; i++) {
    for (int j = 0; j<cols; j++) {

      cout << grid[i][j].getCost() << " ";
    
      //checking i,j values
      ijCostSource stored = grid[i][j];


      //dimension_type storedI = stored.getI();
      //dimension_type storedJ = stored.getJ();
      //cout << "(" << storedI << "," << storedJ << ") ";

    }
    cout << "\n";
  }
}
#endif


#include "formatNumber.h"

void 
Tile::printStats(ostream& str) {

  str << "Tile: " 
      << rows  << " x "<< cols << ", total=" << rows * cols
      << ", elem size =" << sizeof(ijCost)
      << ", total tile size "
      << formatNumber(NULL, rows * cols * sizeof(ijCost)) << endl;
}

void
Tile::init(Tile *tile) {
  tile->valid = 0;
  tile->s2bWriteCount = 0;
  tile->s2bPQCount = 0;
}

void
Tile::dump() {
  printStats(cout);
  cout << "Tile: s2bWriteCount = " << s2bWriteCount << endl;
  cout << "Tile: s2bPQCount = " << s2bPQCount << endl;
}
