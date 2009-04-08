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

#ifndef _DIJKSTRA_H
#define _DIJKSTRA_H


#include <grass/iostream/ami.h>
#include "types.h"
#include "common.h"
#include "input.h"
#include "boundary.h"
#include "tile.h"
#include "index.h"
#include "distanceType.h"
#include "update.h"
//#include "iterator.h"
#include "output.h"
#include "update.h"
#include "initialize.h"
#include "pqueue.h"

void normalDijkstra(char* cellname, char* sourcename, long* nodaa_count);

int boundaryTileDijkstra(Tile *tile, AMI_STREAM<distanceType> *b2bstr, 
			  const TileFactory *tf, cost_type** dist, 
			  pqheap_ijCost *spq,
			  cost_type** sourceDist);

void computeSubstituteGraph(TileFactory* inTf, 
			    AMI_STREAM<distanceType> *b2bstr, 
			    AMI_STREAM<ijCost> *s2bstr);

void addNullBnds(int settledArray[], BoundaryType<cost_type> *phase2Bnd,
		 const TileFactory* tf);

void interTileDijkstra(AMI_STREAM<ijCost> *s2bstr, 
		       AMI_STREAM<distanceType> *b2bstr, 
		       BoundaryType<cost_type> *phase2Bnd, const TileFactory *tf);

void finalDijkstra(TileFactory *tf, BoundaryType<cost_type> *phase2Bnd,
		   AMI_STREAM<ijCost> *finalstr);

int doubleWriteToDistStream(const basicIJType& source,const basicIJType& dest, 
			    cost_type dist, AMI_STREAM<distanceType> *b2bstr);

void writeToCostTypeStream(dimension_type i, dimension_type j, cost_type dist,
			   AMI_STREAM<ijCost> *str);

void writeToStreamWithDist(distanceType inDist,
			   AMI_STREAM<distanceType> *b2bstr);

#endif
