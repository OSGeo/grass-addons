
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

#include "tile.h"
#include "formatNumber.h"

/* ************************************************************ */

TileFactory::TileFactory(dimension_type gtileSizeRows, 
			 dimension_type gtileSizeCols, 
			 size_t tilemem) {
  
  tileSizeRows = gtileSizeRows;
  tileSizeCols = gtileSizeCols;

  tileBnd = new CachedBoundaryMgr<costSourceType>(tsr, tsc, nrowsPad, ncolsPad);
  tileBndR = new BoundaryTileReader<costSourceType>(tileBnd);

//   // this will probably create a stream based on opt->s0bnd -RW
//   tileBnd = new BoundaryType<costSourceType>(tileSizeRows, tileSizeCols, 
// 					     tilemem);
  
  /* the stream that stores the internal points in the grid */

  /* POTENTIAL PROBLEM: What happens if we make more than 1 tile
     factory?? */

  const char *s0path=resolvePath(opt->s0out);
  unlink(s0path); 
  cout << "path: " << s0path << endl; cout.flush();
  internalstr = new AMI_STREAM<ijCostSource>(s0path); 
  internalstr->persist(PERSIST_PERSISTENT);

  char* tempname;
  internalstr->name(&tempname);
  cout << "Created internalstr = " << tempname << endl;
  *stats << "Created internalstr = " << tempname << endl;
  delete [] tempname;

  iMarker = 0;
  jMarker = 0;
  numTileBndPts = 2*(tileSizeRows-1) + 2*(tileSizeCols-1);
  tile = new Tile(tileSizeRows, tileSizeCols);
  internalstr->seek(0);

  cout << "Tile Factory Sizes, row: " << tileSizeRows << "  col: " <<
    tileSizeCols << "\n";
}


/* Constructor where the stream paths are specified, used in parallel
   implementation */
TileFactory::TileFactory(dimension_type gtileSizeRows, 
			 dimension_type gtileSizeCols,
			 AMI_STREAM<ijCostSource> *dataStream, /* char* internalPath, */
			 const char* bndPath) {
  tileSizeRows = gtileSizeRows;
  tileSizeCols = gtileSizeCols;

//   tileBnd = new BoundaryType<costSourceType>(tileSizeRows, tileSizeCols, 
// 					     bndPath);
  tileBnd = NULL;
  tileBndR = new BoundaryTileReader<costSourceType>(tsr, tsc, nrowsPad, ncolsPad, bndPath);
  
  /* the stream that stores the internal points in the grid */

  /* POTENTIAL PROBLEM: What happens if we make more than 1 tile
     factory?? */

  
  //internalstr = new AMI_STREAM<ijCostSource>(internalPath); 
  internalstr = dataStream;
  internalstr->persist(PERSIST_PERSISTENT);
  internalstr->seek(0);
  {
    char* tempname;
    internalstr->name(&tempname);
    cout << "Created internalstr = " << tempname << endl;
    //cout << "StrLen: " << internalstr->stream_len() << endl;
    cout.flush();
    *stats << "Created internalstr = " << tempname << endl;
    delete [] tempname;
  }

  iMarker = 0;
  jMarker = 0;
  numTileBndPts = 2*(tileSizeRows-1) + 2*(tileSizeCols-1);
  tile = new Tile(tileSizeRows, tileSizeCols);
  /* XXX-RW is this tile deleted anywhere? */
  /* nope-TH */

  cout << "Tile Factory Sizes, row: " << tileSizeRows << "  col: " <<
    tileSizeCols << "\n";
}

/*
  adds a predetermined number of rows and columns to the grid so that
  the b2b stream can be indexed properly 
*/

TileFactory::~TileFactory() {
  //delete tile;
  if(tileBndR) { delete tileBndR; }
  if(tileBnd) { delete tileBnd; }
  delete internalstr;

}

void
TileFactory::reset() {
  internalstr->seek(0);
  iMarker = 0;
  jMarker = 0;
}

void
TileFactory::setIMarker(int inI) {
  iMarker = inI;
}

void
TileFactory::setJMarker(int inJ) {
  jMarker = inJ;
}

/*
  Loads a tile into the t variable using the internalstr and the tilebnd 
  data structures.
*/
int
TileFactory::getNextTile(Tile* t) {
  if (iMarker <= nrowsPad-tileSizeRows &&  jMarker <= ncolsPad-tileSizeCols) {
    // *stats << "loading tile...";
    // *stats << "iMarker: " << iMarker << "  jMarker: " << jMarker << "\n";
    // *stats << "getNextTile::Internal stream length: " << 
    //  internalstr->stream_len() << endl;
    //stats->flush();

    assert(t);
    tile = t;
    Tile::init(t);
    int ok = fillTile();
    if(!ok) {
      return 0;			// error
    }
	//tile->dumpTile(*stats, "ftile ");

    //upper left point of next tile to be loaded.
    jMarker = jMarker + tileSizeCols-1;
    if (jMarker > ncolsPad - tileSizeCols) {
      jMarker = 0;
      iMarker = iMarker + tileSizeRows - 1;
    }
    return 1;
  }
  return 0;
  
} 

// returns 1 on success
int
TileFactory::fillTile() {
  int npoints=0;
  int ok;
  for (int i = 1; i < tileSizeRows-1; i++) {
    for (int j = 1; j < tileSizeCols-1; j++) {
      assert (!IS_BOUNDARY(i,j));
      ok = addInternalPoint(i,j);
      if(!ok) {
	//fprintf(stderr, "fillTile: bailing out after %d internal points\n", npoints);
	assert(npoints == 0);
	return 0;
      }
      npoints++;
    }
  }

  ijCostSource tmp = tile->getComplex(1,1);
  iMarker = tmp.getI()-1;
  jMarker = tmp.getJ()-1;
  

//   // left and right side
//   for (int i = 0, j = 0; i < tileSizeRows; i++) {
//     if (!tileBndR->isBoundary(i+iMarker, j+jMarker)) {
//       cout << "TileF: Not a Bnd: " << i << "," << j << "  " << iMarker 
// 	   << "," << jMarker << endl; cout.flush();
//     }
//     assert(tileBndR->isBoundary(i+iMarker, j+jMarker));
//     addBoundaryPoint(i,j);
//     assert(tileBnd->isBoundary(i+iMarker, j+jMarker+tileSizeCols-1));
//     addBoundaryPoint(i,j+tileSizeCols-1);
//   }
//   // top and bottom
//   for (int i = 0, j = 0; j < tileSizeCols; j++) {
//     assert(tileBndR->isBoundary(i+iMarker, j+jMarker));
//     addBoundaryPoint(i,j);
//     assert(tileBndR->isBoundary(i+iMarker+tileSizeRows-1, j+jMarker));
//     addBoundaryPoint(i + tileSizeRows-1,j);
//   }

  tileBndR->readTileBoundary(iMarker, jMarker, tile);

  //cerr << "fillTile: " << npoints << " internal points" << endl;
  return 1;
}

void
TileFactory::sortTF() {
  
  internalstr->seek(0); // is this necessary? 
  ijTileCostCompareType fun;
  fun.setTileSize(tileSizeRows, tileSizeCols);
  stats->comment("TileFactory: Sorting internalstr...");
  //sort(&internalstr, fun);
  //cachedSort(&internalstr, fun);

  AMI_STREAM<ijCostSource> *sortedInternalstr;
  AMI_sort(internalstr, &sortedInternalstr, &fun, 1);
  sortedInternalstr->seek(0);
  internalstr = sortedInternalstr;

  //internalstr->seek(0); // is this required? RW
  stats->comment("TileFactory: Sorting internalstr... done.");
}



void
TileFactory::insert(ijCostSource in) {
  AMI_err ae;
  dimension_type tempI = in.getI();
  dimension_type tempJ = in.getJ();

  if (IS_BOUNDARY(tempI,tempJ)) {
	assert(tileBnd);
    tileBnd->insert(in);
    //cout << "Boundary: " << out;
  } else {
    ae = internalstr->write_item(in);
    assert(ae == AMI_ERROR_NO_ERROR); 
    //cout << "Cost Stream: " << out;
  }
}

/* ************************************************************ */

/*
  adds a predetermined number of rows and columns to the grid so that
  the b2b stream can be indexed properly 
*/
void
TileFactory::pad() {
  ijCostSource padding;
  costSourceType dummyValue = costSourceType(NODATA, 'n');

  size_t padMem = MM_manager.memory_available();
  *stats << "TileFactory::pad::Pre Padding nrows: " << nrows 
       << "  ncols: " << ncols << "\n";
  *stats << "TileFactory::pad::Memory Available Before Padding: " 
       << formatNumber(NULL, padMem) << ".\n"; 
  *stats << "pad::Internal stream length pre Padding: " << 
      internalstr->stream_len() << endl;

  for (int i = 0; i < nrows; i++) {
    for (int j = ncols; j < ncolsPad; j++) {
      padding = ijCostSource(i,j,dummyValue);//can't have a source in padding
      insert(padding);
    }
  }

  for (int j = 0; j < ncols; j++) {
    for (int i = nrows; i < nrowsPad; i++) {
      padding = ijCostSource(i,j,dummyValue);//can't have a source in padding
      insert(padding);
    }
  }

  for (int i = nrows; i < nrowsPad; i++) {
    for (int j = ncols; j < ncolsPad; j++) {
      padding = ijCostSource(i,j,dummyValue);//can't have a source in padding
      insert(padding);
    }
  }

  padMem = MM_manager.memory_available();
  *stats << "TileFactory::pad::Post Padding nrows: " << nrowsPad 
       << "  ncols: " << ncolsPad << "\n";
  *stats << "TileFactory::pad::Memory Available After Padding: " 
       << formatNumber(NULL, padMem) << ".\n"; 
  stats->recordLength("pad::Internal stream length post Padding", internalstr);
}


/* adds a point from a boundary data structure to a tile being
   constructed. Called by the fillTile() method. */
// void
// TileFactory::addBoundaryPoint(dimension_type i, dimension_type j) {
//   ijCostSource tempijCost;
//   tileBnd->get(i+iMarker, j+jMarker, &tempijCost);
//   tile->insert(i, j, tempijCost);
// }

/* gets a point from the internal points stream and inserts in into the tile */
// returns number of points read
int
TileFactory::addInternalPoint(dimension_type i, dimension_type j) {
  ijCostSource* tempijCost;
  AMI_err ae = internalstr->read_item(&tempijCost);
  if(ae == AMI_ERROR_END_OF_STREAM) {
    return 0;
  }
  assert(ae == AMI_ERROR_NO_ERROR);
  assert(i % (tileSizeRows-1) == tempijCost->getI() % (tileSizeRows-1));
  assert(j % (tileSizeCols-1) == tempijCost->getJ() % (tileSizeCols-1));
  tile->insert(i, j, *tempijCost);

//   fprintf(stderr, "point <%d,%d> added at <%d,%d> %d\n", tempijCost->getI(), tempijCost->getJ(), 
// 	  iMarker+i, jMarker+j, sizeof(ijCostSource));
  return 1;
}

/* returns the total number of points in a grid as represented in the
   internal stream and the BoundaryType data structure */

dimension_type
TileFactory::getRows() const {
  return tileSizeRows;
}

dimension_type
TileFactory::getCols() const {
  return tileSizeCols;
}

int
TileFactory::getTotalPoints() {
  //  return internalstr->stream_len() + tileBnd->getSize();
  return -1;
}

dimension_type
TileFactory::getBndrows() const {
  return tileBndR->getBndRows();
}

dimension_type
TileFactory::getBndcols() const {
  return tileBndR->getBndCols();
}

int
TileFactory::getNumTiles() const {
  return (getBndrows()-1) * (getBndcols()-1);
}

/* returns the i value of the upper left-hand point in the current tile */
dimension_type
TileFactory::getIMarker() const {
  return iMarker;
}

/* returns the j value of the upper left-hand point in the current tile */
dimension_type
TileFactory::getJMarker() const {
  return jMarker;
}

int
TileFactory::getNumTileBndPts() const {
  return numTileBndPts;
}


/* checks to see if point i,j lies on a bundary in the
   TileFactory. returns 1 if the point is a boundary and 0
   otherwise */
int
TileFactory::isBoundary(dimension_type i, dimension_type j) const {
  return IS_BOUNDARY(i,j);
}

/* There are 8 different types of points in any particular grid as
   defined in tile.h. this method takes a point i,j and returns its
   classification */

int
TileFactory::classifyPoint(dimension_type i, dimension_type j) const {

  //if ((i < 0) || (i >= nrowsPad) || (j < 0) || (j >= ncolsPad))
  assert(i != dim_undef && j != dim_undef);
  if ( (i >= nrowsPad) || (j >= ncolsPad))
    return NOT_IN_GRID;

  if ((i==0 && j==0) || (i == 0 && j == ncolsPad-1) || 
      (i == nrowsPad-1 && j == 0) || (i == nrowsPad-1 && j == 0))
    return EXT_CNR;

  if (i == 0 || i == nrowsPad-1) {
    if (j == 0 || j == ncolsPad-1) {
      return EXT_BND;
    }
    if (j %(tileSizeCols-1) == 0)
      return EXT_COL_CNR;
    return EXT_BND;
  }

  if (j == 0 || j == ncolsPad-1) {
    if (i%(tileSizeRows-1) == 0)
      return EXT_ROW_CNR;
    return EXT_BND;
  }

  if (i%(tileSizeRows-1) == 0) {
    if (j %(tileSizeCols-1) == 0) 
      return INT_CNR;
    return INT_ROW;
  }

  if (j %(tileSizeCols-1) == 0)
    return INT_COL;
  
  return NOT_BND;  
}


/* Each different type of boundary point has a different number of
   boundary neighbors (really this is the reason for classification in
   the first place). This method takes a point i,j and returns how
   many boundary neighbors it will have */
int
TileFactory::getNumNeighbors(dimension_type i, dimension_type j) const {
  int mode = classifyPoint(i,j);
  
  switch(mode) {

  case EXT_BND :
    return numTileBndPts;
  case INT_ROW :
    return 2*numTileBndPts;
  case INT_COL :
    return 2*numTileBndPts;
  case INT_CNR :
    return 4*numTileBndPts;
  case EXT_ROW_CNR :
    return 2*numTileBndPts;
  case EXT_COL_CNR :
    return 2*numTileBndPts;
  case EXT_CNR :
    return numTileBndPts;
  case NOT_BND :
    return 0;
  case NOT_IN_GRID :
    return -1;
  }

  return -1;
}

void
TileFactory::printClassification(int in) const {
  switch(in) {

  case EXT_BND :
    cout << "Exterior Boundary\n";
    break;
  case INT_ROW :
    cout << "Interior Row\n";
    break;
  case INT_COL :
    cout << "Interior Column\n";
    break;
  case INT_CNR :
    cout << "Interior Corner\n";
    break;
  case EXT_ROW_CNR :
    cout << "Exterior Row Corner\n";
    break;
  case EXT_COL_CNR :
    cout << "Exterior Col Corner\n";
    break;
  case EXT_CNR :
    cout << "Exterior Corner\n";
    break;
  case NOT_BND :
    cout << "Not A Boundary\n";
    break;
  case NOT_IN_GRID :
    cout << "Not In Grid\n";
    break;
  }
}
