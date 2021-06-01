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


#ifndef _OUTPUT_H
#define _OUTPUT_H


extern "C" {
#include <grass/gis.h>
}
#include <grass/iostream/ami.h>
#include "sortutils.h"
#include "boundary.h"
#include "common.h"
#include "types.h"


void writeToGrassFile(AMI_STREAM<ijCost> *instr, 
					  BoundaryType<cost_type> *inbnd);

void stream2ascii(AMI_STREAM<ijCost> *instr, 
				  BoundaryType<cost_type> *inbnd, const char* fname);

void grid2Grass(cost_type ** grid, dimension_type rows, dimension_type cols,
				char* cellname);

class printCost {
 public:
  cost_type operator()(const ijCost &p) {
    return p.getCost();
  };
};

#endif
