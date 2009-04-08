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


#ifndef __ITERATOR_H_
#define __ITERATOR_H_

#include "input.h"
#include "tile.h"


class Iterator {

  int iMarker;
  int jMarker;

  int tileSizeRows, tileSizeCols;

  Tile* tile;

 public:
  Iterator(Tile* inTile);

  ~Iterator();

  void reset();

  int getNext(ijCostSource *out);

};

#endif
