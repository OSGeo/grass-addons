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

#include "boundary.h"
#include "sortutils.h"
#include "types.h"
#include "pq.h"
#include "pqueue.h"
#include "formatNumber.h"

#include <math.h>
/*
  The Boundary Module is used to define the BoundaryType class. This class
  stores all of the boundary points between tiles in a grid(graph).
*/

size_t
memForNormalDijkstra(dimension_type rows, dimension_type cols) {
  /* Required items for normal dijkstra
     1. Grid of costs
     2. Grid of distances
     3. PQ
  */

  size_t gridCosts = 2*rows*cols*sizeof(cost_type);
  size_t pqCost = rows*cols*sizeof(costStructure);

  return gridCosts+pqCost;
}


/************************************************************/
/* sets tileSizeRows, tileSizeCols, nrowsPad, ncolsPad given the
   memory to be used by a tile; the size of a tile is chosen so that a
   tile uses at most maxmem memory; in order that boundary tiles have
   same size as internal tiles we pad the grid we extra rows and
   columns; the size of the grid is thus (nrowsPad, ncolsPad) */
void 
initializeTileSize(dimension_type *tileSizeRows, 
		   dimension_type *tileSizeCols, 
		   size_t maxmem) {


  /* use all available memory */
  dimension_type baseTileSize;  
  baseTileSize = (dimension_type)sqrt ((float)(maxmem /(sizeof(ijCostSource) + 
							sizeof(cost_type))));
  optimizeTileSize(tileSizeRows, tileSizeCols, baseTileSize);
}

void 
initializeTileSize(dimension_type *tileSizeRows, 
		   dimension_type *tileSizeCols, 
		   int numTiles) {


  /* Find a divisor of numTiles which will be the number of tiles from
     top to bottom. Then the number of left to right tiles is computed
     by dividing the total number of tiles by the number of top to
     bottom tiles */

    int gridSize = nrows * ncols;
    int tileSize = gridSize /  numTiles;


    *tileSizeRows = (int)ceil(sqrt((float)tileSize));
    *tileSizeCols = tileSize/(*tileSizeRows);

    tileSize = (*tileSizeRows) * (*tileSizeCols);

    int tileRows = (int)ceil((float)(nrows-1)/(float)((*tileSizeRows)-1));
    int tileCols = (int)ceil((float)(ncols-1)/(float)((*tileSizeCols)-1)); 
    

    std::cout << "Grid size is: " << gridSize      << std::endl;
    std::cout << "Tile size is: " << tileSize      << std::endl;
    std::cout << "tileSizeRows: " << *tileSizeRows << std::endl;
    std::cout << "tileSizeCols: " << *tileSizeCols << std::endl;
    std::cout << "tileRows:     " << tileRows      << std::endl;
    std::cout << "tileCols:     " << tileCols      << std::endl;

    optimizeTileSizeUser(tileSizeRows, tileSizeCols,
			 *tileSizeRows, *tileSizeCols,
			 tileRows, tileCols);
}

void
optimizeTileSizeUser(dimension_type *tileSizeRows, 
		     dimension_type *tileSizeCols, 
		     int baseSizeRows, int baseSizeCols, 
		     int tileRows, int tileCols) {

  /* if the number of tiles divides evenly into the number of rows, we
     don't have to change anything and nrowsPad=nrows. If not then
     tileSizeRows*tileRows < nrows b/c of integer division. Then we
     add 1 to the size of the tile which causes tileSizeRows*tileRows
     > nrows and then we can pad the total number of rows to
     compensate. Also # padding rows < tileRows. */

  *tileSizeRows = baseSizeRows;
  if ((nrows-1)%(*tileSizeRows-1) == 0) {
    nrowsPad = nrows;
  }
  else {
    nrowsPad = (*tileSizeRows-1)*tileRows + 1;
  }

  *tileSizeCols = baseSizeCols;
  if ((ncols-1)%(*tileSizeCols-1) == 0) {
    ncolsPad = ncols;
  }
  else {
    ncolsPad = (*tileSizeCols-1)*tileCols + 1;
  }

  std::cout << "Tile Size Rows: " << *tileSizeRows << std::endl;
  std::cout.flush();
  std::cout << "Padding Rows: " << nrowsPad - nrows << std::endl;
  std::cout.flush();
  std::cout << "Num Row Tiles: " << tileRows << std::endl; 
  std::cout.flush();
  std::cout << "Tile Size Cols: " << *tileSizeCols << std::endl;
  std::cout.flush();
  std::cout << "Padding Cols: " << ncolsPad - ncols << std::endl;
  std::cout.flush();
  std::cout << "Num Col Tiles: " << tileCols << std::endl; 
  std::cout.flush();
  
}

void 
optimizeTileSize(dimension_type *tileSizeRows, 
		 dimension_type *tileSizeCols, 
		 int baseTileSize) {
  
  /* set tileSizeRowsand tileSizeCols to minimize padding */
  dimension_type bndrows, bndcols, lr, lc;
  dimension_type paddingRows = 0, paddingCols = 0;
  float paddingRatio = 0.0, lastRowRatio = 0.0;

  /* optimize tileSizeRows */
  *tileSizeRows = baseTileSize;
  if (*tileSizeRows < nrows) {
    bndrows = computeNumBoundaries(nrows, *tileSizeRows);
    //cout << "BndRows: " << bndrows << endl; cout.flush();
    lr = lastTileSizeRow(bndrows, *tileSizeRows);
    paddingRatio = (float)lr/(*tileSizeRows);
    lastRowRatio = paddingRatio;
    paddingRows = (*tileSizeRows)-lr;
    //cout << "Padding Rows: " << paddingRows << " LR: " << lr << " I: " 
    //	   << *tileSizeRows << endl;cout.flush();
    //cout <<"Trying row tile size "<<*tileSizeRows << ". Padding Ratio: " << 
    // paddingRatio << ".\n";
    for (int i = *tileSizeRows;paddingRatio<.95 && 
	   lastRowRatio<=paddingRatio;i--) {
      bndrows = computeNumBoundaries(nrows, i);
      lr = lastTileSizeRow(bndrows, i);
      lastRowRatio = paddingRatio;
      paddingRatio = (float)lr/i;
      //cout << "Trying row tile size " << i << ". Padding Ratio: " << 
      //	paddingRatio << "LR: " << lr << ".\n";
      *tileSizeRows = i;
      paddingRows = i-lr;
      cout.flush();
    }
    if (lastRowRatio>paddingRatio) {
      (*tileSizeRows)++;
      lr = lastTileSizeRow(bndrows, *tileSizeRows);
      paddingRows = (*tileSizeRows)-lr;
      //cout << "IF:::::Trying row tile size " << *tileSizeRows << 
      //	" Padding Ratio: " << paddingRatio << " BndRows: " << bndrows << " LR: " << lr << ".\n";
    }
  } 
  
  else {
    cout << "#######################HERE#################" << endl; 
    cout.flush();
    *tileSizeRows = nrows;
    bndrows = computeNumBoundaries(nrows, *tileSizeRows);
    lr = lastTileSizeRow(bndrows, *tileSizeRows);
    //cout << "ELSE::::: Padding Ratio: " << paddingRatio << "LR: " << lr << ".\n";
  }


  cout << "Tile Size Rows: " << *tileSizeRows << endl;cout.flush();
  cout << "Padding Rows: " << paddingRows << " LR: " << lr << endl;cout.flush();
  cout << "Num Tiles: " << bndrows - 1 << endl; cout.flush();

  
  bndcols = computeNumBoundaries(ncols, *tileSizeCols);
  /* optimize tileSizeCols */
  *tileSizeCols = baseTileSize;
  if (*tileSizeCols < ncols) {
    bndcols = computeNumBoundaries(ncols, *tileSizeCols);
    lc = lastTileSizeCol(bndcols, *tileSizeCols);
    paddingRatio = (float)lc/(*tileSizeCols);
    paddingCols = (*tileSizeCols)-lc;
    //cout << "Trying col tile size " << tileSizeCols << ". Padding Ratio: " << 
    //  paddingRatio << ".\n";
    for (int j = *tileSizeCols; paddingRatio < .98 ;j--) {
      bndcols = computeNumBoundaries(ncols, j);
      lc = lastTileSizeCol(bndcols, j);
      paddingRatio = (float)lc/j;
      //cout << "Trying col tile size " << j << ". Padding Ratio: " << 
      //	paddingRatio << ".\n";
      *tileSizeCols = j;
      paddingCols = j-lc;
    }
  }  
  
  else {
    *tileSizeCols = ncols;
    bndcols = computeNumBoundaries(ncols, *tileSizeCols);
    lc = lastTileSizeCol(bndcols, *tileSizeCols);
    }
  
  /* set GLOBALS */
  
  nrowsPad = nrows+paddingRows;
  ncolsPad = ncols+paddingCols;

  //nrowsPad = nrows;
  //ncolsPad = ncols;

  char memBuf[100];
  formatNumber(memBuf,(*tileSizeRows)*(*tileSizeCols));
  *stats << "initializeTileSize:: Final tile size = (" << *tileSizeRows << "x" 
	 << *tileSizeCols << ") = " << memBuf << " \n";

  bndrows = computeNumBoundaries(nrowsPad, *tileSizeRows);
  bndcols = computeNumBoundaries(ncolsPad, *tileSizeCols);
  *stats << "initializeTileSize::Bnd rows=" << bndrows << 
    ", bnd cols=" << bndcols << "\n"; stats->flush();

  cout << "Padding " << nrowsPad << " x " << ncolsPad << endl;cout.flush();

  int bndPerTile = 2*(*tileSizeRows-1) + 2*(*tileSizeCols-1);
  int numTiles = (bndrows-1)*(bndcols-1);
  cout << "Col: " << bndcols << " Row: " << bndrows << " tiles: " << numTiles
       << endl;cout.flush();
  int b2bSize = bndPerTile*bndPerTile*numTiles*sizeof(distanceType);

  char buf [100] = "";
  formatNumber(buf, b2bSize);

  cout << "initializeTileSize:: estimated b2bstream size = " << buf << 
    endl;
  *stats << "initializeTileSize:: estimated b2bstream size = " << buf << 
    endl;

}


/************************************************************/
/*
  Computes either the number of boundary rows or columns in a grid 
  depending on the input.
*/
dimension_type 
computeNumBoundaries(dimension_type dIn, int tsIn) {
  assert(tsIn > 1);
  
  // dimension_type variable for return and adjusted values for tileSize and 
  // number of rows or columns.
  dimension_type dOut, tsAdj, dAdj;
  dAdj = dIn - 1;
  tsAdj= tsIn - 1;

  
  dOut = (dimension_type)ceil(((double)dAdj)/tsAdj) + 1;
  return dOut;
}


/************************************************************/
/* 
   Computes the size of the last tile (which might be of abnormal size)
   before padding is applied. This is used to compute the padding ratio
   which defines tile size and padding required
*/
dimension_type
lastTileSizeRow(dimension_type d, int trIn) {
  dimension_type secondToLast = (d-2)*(trIn-1) + 1;
  dimension_type rowSize = nrows - secondToLast + 1;
  return rowSize;
}


/* 
   Computes the size of the last tile (which might be of abnormal size)
   before padding is applied. This is used to compute the padding ratio
   which defines tile size and padding required
*/
/************************************************************/
dimension_type
lastTileSizeCol(dimension_type d, int tcIn) {
  
  dimension_type secondToLast = (d-2)*(tcIn-1) + 1;
  dimension_type colSize = ncols - secondToLast + 1;
  return colSize;
}
