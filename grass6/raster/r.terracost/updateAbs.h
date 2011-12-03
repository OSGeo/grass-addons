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

#include "types.h"

extern const int deltaRow[];
extern const int deltaCol[];
extern cost_type travMult[17]; 

void update_init(cost_type EW_fac, cost_type NS_fac, cost_type DIAG_fac);

void updateNeighbors(const Tile* inT, costStructure costStr, 
					 pqheap_ijCost *pq, cost_type **dist);
