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


#ifndef _TILE_H
#define _TILE_H

#include <grass/iostream/ami.h>
//#include "boundary.h"
#include "types.h"
#include "input.h"
#include "sortutils.h"
#include <ostream>

#define EXT_BND 0
#define INT_ROW 1
#define INT_COL 2
#define INT_CNR 3
#define EXT_ROW_CNR 4
#define EXT_COL_CNR 5
#define EXT_CNR 6
#define NOT_BND 7
#define NOT_IN_GRID 8


#include "tileAbs.h"
#include "boundaryMgr.h"


/*
  The TileFactory is responsible for iterating through each of the tiles
  in order. It creates a tile by combining data from the tileBnd boundary
  structure and the internalstr(internal stream) structure. 
*/
class TileFactory {
  /* cost grid = bndCost U intCost 

     The tile is useful because we can
     alias the current tile and thus have funtions which operate on
     the tile through the TileFactory this way any outside methods
     don't need to know anything about what's going on inside the
     TileFactory */
  Tile* tile;
/*   BoundaryType<costSourceType>* tileBnd; */
  CachedBoundaryMgr<costSourceType>* tileBnd;
  BoundaryTileReader<costSourceType>* tileBndR;
  AMI_STREAM<ijCostSource> *internalstr;
  
  int boundaryMarker, internalMarker, iMarker, jMarker, numTileBndPts;
  dimension_type tileSizeRows, tileSizeCols;

 protected:
  int fillTile();
  void addBoundaryPoint(dimension_type i, dimension_type j);
  int addInternalPoint(dimension_type i, dimension_type j);

 public:
  TileFactory(dimension_type gtileSizeRows, dimension_type gtileSizeCols, 
	      size_t tilemem);

  TileFactory(dimension_type gtileSizeRows, dimension_type gtileSizeCols,
	      AMI_STREAM<ijCostSource> *dataStream, /* char* internalPath, */
	      const char* bndPath);

  ~TileFactory();

  void markBoundaryAsSorted() { /* tileBnd->markAsSorted();  */}

  int getNextTile(Tile* t);

  void setIMarker(int inI);
  void setJMarker(int inJ);

  void insert(ijCostSource in);

  void sortTF();

  /*
    In order to index the b2b stream correctly each tile needs to be
    the same size. This method adds padding to both the rows and 
    columns to achieve this.
  */
  void pad();

  dimension_type getRows() const;
  dimension_type getCols() const;
  dimension_type getBndrows() const;
  dimension_type getBndcols() const;
  dimension_type getIMarker() const;
  dimension_type getJMarker() const;

  int getNumTiles() const; 
  int getNumTileBndPts() const;
  int getTotalPoints();

  int isBoundary(dimension_type i, dimension_type j) const;
  int classifyPoint(dimension_type i, dimension_type j) const;

  void printClassification(int in) const;

  int getNumNeighbors(dimension_type i, dimension_type j) const;

  void reset();

  void serialize(const char *path) { tileBnd->serialize(path); };

  /* how much memory soes it use? */
  long memoryUsage() { 
	/* we only count the boundaryMgs */
	return (tileBnd ? tileBnd->memoryUsage() : 0);
  }

};


#endif
