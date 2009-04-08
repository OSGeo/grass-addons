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



#include <stdio.h>
#include "iterator.h"

Iterator::Iterator(Tile* inTile) {
  iMarker = 0;
  jMarker = 0;
  tile = inTile;
  tileSizeRows = tile->getNumRows();;
  tileSizeCols = tile->getNumCols();;
}

Iterator::~Iterator() {

}


int
Iterator::getNext (ijCostSource* out) {

  if (iMarker > tileSizeRows - 1)
    return 0;

  *out = tile->getComplex(iMarker, jMarker);

  if (iMarker == 0){
    jMarker++;
  }
  else if (iMarker > 0 && iMarker < tileSizeRows-1) {
    jMarker = jMarker + tileSizeCols-1;
  }

  else
    jMarker++;

  if (jMarker >= tileSizeCols) {
    iMarker++;
    jMarker = 0;
  }

  return 1;
}

void
Iterator::reset() {
  iMarker = 0;
  jMarker = 0;
}
