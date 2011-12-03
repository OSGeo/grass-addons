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


#include "index.h"

// /* ---------------------------------------------------------------------- 

// This method takes in an i,j coordinate and TileFactory and then returns
// an ijCost containing the i,j of the upper leftmost point in the tile
// containing i,j. 

//  ---------------------------------------------------------------------- */
// ijCost
// getNeighborRegionMarker(dimension_type i, dimension_type j, const TileFactory *tf) {

//   int mode = tf->classifyPoint(i,j);
//   dimension_type iMarker=-1, jMarker=-1, tileSizeRows, tileSizeCols;
//   tileSizeRows = tf->getRows();
//   tileSizeCols = tf->getCols();
//   ijCost out;

//   switch (mode) {

//   case EXT_BND :
//     if (i == 0) {
//       iMarker = i;
//       jMarker = (j/(tileSizeCols-1))*(tileSizeCols-1);
//     }
//     else if (i == nrowsPad - 1){
//       iMarker = i-(tileSizeRows-1);
//       jMarker = (j/(tileSizeCols-1))*(tileSizeCols-1);
//     }
//     else if (j == 0) {
//       iMarker = (i/(tileSizeRows-1))*(tileSizeRows-1);
//       jMarker = j;
//     }
//     else if (j == ncolsPad - 1){
//       iMarker = (i/(tileSizeRows-1))*(tileSizeRows-1);
//       jMarker = j-(tileSizeCols-1);
//     }
//     break;
//   case INT_ROW:
//     iMarker = i-(tileSizeRows-1);
//     jMarker = (j/(tileSizeCols-1))*(tileSizeCols-1);
//     break;
//   case INT_COL:
//     iMarker = (i/(tileSizeRows-1))*(tileSizeRows-1);
//     jMarker = j-(tileSizeCols-1);
//     break;
//   case INT_CNR:
//     iMarker = i-(tileSizeRows-1);
//     jMarker = j-(tileSizeCols-1);
//     break;
//   case EXT_ROW_CNR:
//     if (j == 0) {
//       jMarker = j;
//       iMarker = i-(tileSizeRows-1);
//     }
//     else if (j == ncolsPad -1) {
//       jMarker = j-(tileSizeCols-1);
//       iMarker = i-(tileSizeRows-1);
//     }
//     break;
//   case EXT_COL_CNR:
//     if (i == 0) {
//       iMarker = i;
//       jMarker = j-(tileSizeCols-1);
//     }
//     else if (i == nrowsPad -1) {
//       iMarker = i-(tileSizeRows-1);
//       jMarker = j-(tileSizeCols-1);
//     }
//     break;
//   case EXT_CNR:
//     if (i == 0 && j == 0) {
//       iMarker = i;
//       jMarker = j;
//     }
//     if (i == 0 && j == ncolsPad-1) {
//       iMarker = i;
//       jMarker = j-(tileSizeCols-1);
//     }
//     if (i == nrowsPad-1 && j == 0) {
//       iMarker = i-(tileSizeRows-1);
//       jMarker = j;
//     }
//     if (i == nrowsPad-1 && j == 0) {
//       iMarker = i-(tileSizeRows-1);
//       jMarker = j-(tileSizeCols-1);
//     }
//     break;
//   case NOT_BND:
//     cout << "Not Boundary\n"; 
//     assert(0);			// is this an error? -RW
//     break;
//   case NOT_IN_GRID:
//     cout << "Not in Grid\n;";
//     assert(0);			// is this an error? -RW
//     break;
//   default:
//     assert(0);
//   }

//   /* This point is used only for its i,j coordinate so we can set its
//      caost to -1 aand is source to 'n' as default values */
//   assert(iMarker >= 0 && jMarker >= 0);	// -RW
//   out = ijCost(iMarker, jMarker, -1);
  
//   return out;
  
// }


/* ---------------------------------------------------------------------- 

This method is used for indexing the b2bstr. For any iFrom,jFrom and Tile 
Factory from a distanceType (iFrom, jFrom, iTo, jTo, Distance), this method 
returns the index in b2bstr where iFrom,jFrom starts. 

 ---------------------------------------------------------------------- */
off_t
getFromIndex(dimension_type iFrom, dimension_type jFrom, 
	     const TileFactory *tf) {

  dimension_type nbrows, nbcols, tileSizeRows, tileSizeCols;
  off_t index;
  int numTileBndPts, factorA, factorB;
  nbrows = tf->getBndrows();
  nbcols = tf->getBndcols();
  tileSizeRows = tf->getRows();
  tileSizeCols = tf->getCols();

  numTileBndPts = tf->getNumTileBndPts();

  //cout << "numTileBndPts: " << numTileBndPts << " nbrows: " << nbrows <<
  //  " nbcols: " << nbcols << endl;cout.flush();
  //cout << "nrowsPad: " << nrowsPad << " ncolsPad: " << ncolsPad << endl;
  //cout.flush();


  factorA = (nbcols-1)*2;
  factorB = ncolsPad*2 + (nbcols-2)*2;
  index = 0;

  // (i,j) in the first row
  if (iFrom == 0) {
    //index = 0;    cout << "iFrom == 0\n";
    if (jFrom == 0)
      index = 0;
    else
      index = jFrom + (jFrom-1)/(tileSizeCols-1);
    //cout << "Index: " << index << "\n";
  }

  // (i,j) in the last row
  else if (iFrom == nrowsPad-1){
    index = 0;    //cout << "iFrom = nrowsPad-1\n";
    index = ncolsPad + nbcols-2;
    index += (iFrom/(tileSizeRows-1))*(tileSizeRows-2)*factorA;
    index += ((iFrom-1)/(tileSizeRows-1))*factorB;
    index += jFrom + (jFrom-1)/(tileSizeCols-1);
  }

  // (i,j) in a boundary row
  else if (iFrom%(tileSizeRows-1)==0) {
    //cout << "iFrom%(nbrows-1)==0\n";
    //1st row
    index = ncolsPad + nbcols-2;
    //Rows 2+3 for midTest
    index += (iFrom/(tileSizeRows-1))*(tileSizeRows-2)*factorA;
    //Row 4 for midtest
    index += ((iFrom-1)/(tileSizeRows-1))*factorB;
    //last row
    index += (jFrom + (jFrom-1)/(tileSizeCols-1))*2;
  }

  // (i,j) in a boundary column
  else if (jFrom%(tileSizeCols-1)==0) {
    //cout << "iFrom%(nbrows-1)!=0\n";
    //1st row
    index = ncolsPad + nbcols-2;
    //Rows 2+3 for midTest
    index += (iFrom/(tileSizeRows-1))*(tileSizeRows-2)*factorA;
    //Row 4 for midtest
    index += ((iFrom-1)/(tileSizeRows-1))*factorB;
    //last set of incomplete rows 
    index += ((iFrom%(tileSizeRows-1))-1) * factorA;
    //last row
    index += jFrom/(tileSizeCols-1) + (jFrom-1)/(tileSizeCols-1);
  }

  else {
    cerr << "Boundary access error: (" << iFrom << "," << jFrom 
	 << ") is not a boundary point." << endl;
    exit(1);
  }

  //cout << "Index: " << index << "\n";cout.flush();

  return index*numTileBndPts;
}


// /* ---------------------------------------------------------------------- 

// This method is used for indexing the b2bstr. For any iTo,jTo and Tile 
// Factory from a distanceType (iFrom, jFrom, iTo, jTo, Distance), this method 
// returns the offset after iFrom, jFrom where (iFrom, jFrom, iTo, jTo) can be
// found

//  ---------------------------------------------------------------------- */
// int getToIndex(dimension_type iFrom, dimension_type jFrom, dimension_type iTo, 
// 	       dimension_type jTo, const TileFactory *tf) {

//   int pointType, numTileBndPts;
//   dimension_type tileNumI, tileNumJ, tileSizeRows, tileSizeCols,
//     iMod, jMod, iMarker, jMarker;
//   ijCost markers;

//   numTileBndPts = tf->getNumTileBndPts();

//   pointType = tf->classifyPoint(iFrom, jFrom);
//   tf->printClassification(pointType);
//   tileSizeRows = tf->getRows();
//   tileSizeCols = tf->getCols();
//   tileNumI = iTo/(tileSizeRows-1);
//   tileNumJ = jTo/(tileSizeCols-1);
//   markers = getNeighborRegionMarker(iFrom, jFrom, tf);
//   iMarker = markers.getI();
//   jMarker = markers.getJ();

//   /*
//   cout << "getToIndex()\n";
//   cout << "iFrom: " << iFrom << " jFrom: " << jFrom << "\n";
//   cout << "iTo: " << iTo << " jTo: " << jTo << "\n";
//   cout << "iMarker: " << iMarker << " jMarker: " << jMarker << "\n";
//   */

//   switch (pointType) {

//   case EXT_BND :
//     if (iTo == iMarker)
//       return jTo-jMarker+1;
//     if (iTo == iMarker + tileSizeRows-1)
//       return numTileBndPts-((jMarker+tileSizeCols-1)-jTo);
//     if (jTo == jMarker)
//       return tileSizeCols + (iTo-iMarker-1)*2 + 1;
//     if (jTo == jMarker+tileSizeCols-1)
//       return tileSizeCols + (iTo-iMarker)*2;
//     cout << "Problem with EXT_BND\n";
//     break;

//   case INT_ROW :
//     if (iTo == iMarker)
//       return jTo-jMarker+1;
//     if (iTo == iMarker + tileSizeRows-1)
//       return tileSizeCols + 2*(tileSizeRows-2) + (jTo-jMarker)*2 + 1;
//     if (iTo == iMarker + (tileSizeRows-1)*2)
//       return tileSizeCols*3 + 2*2*(tileSizeRows-2) + (jTo-jMarker) + 1;
//     if (jTo == jMarker && iTo < iFrom)
//       return tileSizeCols + (iTo-iMarker-1)*2 + 1;
//     if (jTo == jMarker && iTo > iFrom)
//       return tileSizeCols*3 + (iTo-iMarker-1)*2 + 1;
//     if (jTo == jMarker+tileSizeCols-1 && iTo < iFrom)
//       return tileSizeCols + (iTo-iMarker)*2 ;
//     if (jTo == jMarker+tileSizeCols-1 && iTo > iFrom)
//       return tileSizeCols*3 + (iTo-iMarker)*2;
//     cout << "Problem with INT_ROW\n";
//     break;

//   case INT_COL :
//     if (iTo == iMarker && jTo <= jFrom)
//       return jTo-jMarker+1;
//     if (iTo == iMarker && jTo > jFrom)
//       return jTo-jMarker+2;
//     if (iTo == iMarker + tileSizeRows-1 && jTo <= jFrom)
//       return 2*tileSizeCols+(tileSizeRows-2)*4+(jTo-jMarker)+1;
//     if (iTo == iMarker + tileSizeRows-1 && jTo > jFrom)
//       return 2*tileSizeCols+(tileSizeRows-2)*4+(jTo-jMarker)+2;
//     if (jTo == jMarker)
//       return tileSizeCols*2+(iTo-iMarker-1)*2*2+1;
//     if (jTo == jMarker+tileSizeCols-1)
//       return tileSizeCols*2+(iTo-iMarker-1)*2*2+2;
//     if (jTo == jMarker+(tileSizeCols-1)*2)
//       return tileSizeCols*2+(iTo-iMarker-1)*2*2+4;
//     cout << "Problem with INT_COL\n";
//     break;

//   case INT_CNR :
//     if (iTo == iMarker && jTo <= jFrom)
//       return jTo-jMarker+1;
//     if (iTo == iMarker && jTo > jFrom)
//       return jTo-jMarker+2;
//     if (iTo == iMarker + tileSizeRows-1 && jTo <= jFrom)
//       return 2*tileSizeCols+(tileSizeRows-2)*4+(jTo-jMarker)*2+1;
//     if (iTo == iMarker + tileSizeRows-1 && jTo > jFrom)
//       return 2*tileSizeCols+(tileSizeRows-2)*4+(jTo-jMarker+2)*2+1;
//     if (iTo == iMarker + (tileSizeRows-1)*2 && jTo <= jFrom)
//       return tileSizeCols*6 + (tileSizeRows-2)*2*4 + jTo-jMarker+1;
//     if (iTo == iMarker + (tileSizeRows-1)*2 && jTo > jFrom)
//       return tileSizeCols*6 + (tileSizeRows-2)*2*4 + jTo-jMarker+2;
//     if (jTo == jMarker && iTo < iFrom)
//       return tileSizeCols*2 + (jTo-jMarker-1)*2 + 1;
//     cout << "Problem with INT_CNR\n";
//     break;
    
//   case EXT_ROW_CNR : //Same as internal row
//     if (iTo == iMarker)
//       return jTo-jMarker+1;
//     if (iTo == iMarker + tileSizeRows-1)
//       return tileSizeCols + 2*(tileSizeRows-2) + (jTo-jMarker)*2 + 1;
//     if (iTo == iMarker + (tileSizeRows-1)*2)
//       return tileSizeCols*3 + 2*2*(tileSizeRows-2) + (jTo-jMarker) + 1;
//     if (jTo == jMarker && iTo < iFrom)
//       return tileSizeCols + (iTo-iMarker-1)*2 + 1;
//     if (jTo == jMarker && iTo > iFrom)
//       return tileSizeCols*3 + (iTo-iMarker-1)*2 + 1;
//     if (jTo == jMarker+tileSizeCols-1 && iTo < iFrom)
//       return tileSizeCols + (iTo-iMarker)*2 ;
//     if (jTo == jMarker+tileSizeCols-1 && iTo > iFrom)
//       return tileSizeCols*3 + (iTo-iMarker)*2;
//     cout << "Problem with INT_ROW\n";
//     break;
    
//   case EXT_COL_CNR :
//     if (iTo == iMarker && jTo <= jFrom)
//       return jTo-jMarker+1;
//     if (iTo == iMarker && jTo > jFrom) {
//       cout << "I should be here";
//       return jTo-jMarker+2;
//     }
//     if (iTo == iMarker + tileSizeRows-1 && jTo <= jFrom)
//       return 2*tileSizeCols+(tileSizeRows-2)*4+(jTo-jMarker)+1;
//     if (iTo == iMarker + tileSizeRows-1 && jTo > jFrom)
//       return 2*tileSizeCols+(tileSizeRows-2)*4+(jTo-jMarker)+2;
//     if (jTo == jMarker)
//       return tileSizeCols*2+(iTo-iMarker-1)*2*2+1;
//     if (jTo == jMarker+tileSizeCols-1)
//       return tileSizeCols*2+(iTo-iMarker-1)*2*2+2;
//     if (jTo == jMarker+(tileSizeCols-1)*2)
//       return tileSizeCols*2+(iTo-iMarker-1)*2*2+4;
//     cout << "Problem with INT_COL\n";
//     break;

//   case EXT_CNR :
//     if (iTo == iMarker)
//       return jTo-jMarker+1;
//     if (iTo == iMarker + tileSizeRows-1)
//       return numTileBndPts-((jMarker+tileSizeCols-1)-jTo);
//     if (jTo == jMarker)
//       return tileSizeCols + (iTo-iMarker-1)*2 + 1;
//     if (jTo == jMarker+tileSizeCols-1)
//       return tileSizeCols + (iTo-iMarker)*2;
//     cout << "Problem with EXT_BND\n";
//     break;

//   case NOT_BND :
//     cout << "Problem with NOT_BND\n";
//     break;

//   case NOT_IN_GRID :
//     cout << "Problem with NOT_IN_GRID\n";
//     break;

//   }

//   assert(0);			// -RW
//   return -1;			// -RW
// }

/* ---------------------------------------------------------------------- 

This method is used for indexing the array of settled points used for 
the b2b stream. 

 ---------------------------------------------------------------------- */
int
getSettledIndex(dimension_type i, dimension_type j, const TileFactory *tf) {
  dimension_type tileSizeRows, tileSizeCols, nbrows, nbcols;
  int index = 0;
  tileSizeRows = tf->getRows();
  tileSizeCols = tf->getCols();
  nbrows = tf->getBndrows();
  nbcols = tf->getBndcols();


  if (i == 0) {
    index = j;
  }
  else if (i == nrowsPad-1) {
    index  = ncolsPad*(nbrows-1);
    index += (nbrows-1)*(tileSizeRows-2)*nbcols;
    index += j;
  }
  else if (i%(tileSizeRows-1) == 0) {
    index  = (i/(tileSizeRows-1))*ncolsPad;
    index += (i/(tileSizeRows-1))*(tileSizeRows-2)*nbcols;
    index += j;
  }
  else {
    index  = ((i/(tileSizeRows-1))+1)*ncolsPad;
    index += (i/(tileSizeRows-1))*(tileSizeRows-2)*nbcols;
    index += ((i%(tileSizeRows-1))-1)*nbcols;
    index += j/(tileSizeCols-1);
  }

  /*
  if (i == 0)
    cout << "For " << i << "," << j << " Settle Index: " << index << "\n";
  */

  return index;
}
