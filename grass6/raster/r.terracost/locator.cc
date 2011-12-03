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

#include <stdlib.h>
#include <stdio.h>
#if __GNUC__ > 3 || (__GNUC__ == 3 && __GNUC_MINOR__ >= 1)
#include <ostream>
#else
#include <ostream.h>
#endif
#include <iostream>
#include <math.h> 
#include <assert.h>

#include "locator.h"
#include "config.h"

// static int
// computeNumBoundaries(int total, int tile) {
//   assert(tile > 1);
//   total--;
//   tile--;

//   return (int)ceil(((double)total)/tile) + 1;
// }


#define CEIL_A_DIV_B(A,B) (((A)+(B)-1)/(B))
#define IS_BOUNDARY(row,col) (((row % (tsr-1)) == 0) || ((col % (tsc -1)) == 0))


void
IJClassifier::checker() {
  dimension_type i, j;

  int ntiles_i = CEIL_A_DIV_B(nrowsPad-1, tsr-1);
  int ntiles_j = CEIL_A_DIV_B(ncolsPad-1, tsc-1);

  fprintf(stderr, "checker running...\n");
  fprintf(stderr, "nrows,ncols = %d, %d\n", nrows, ncols);
  fprintf(stderr, "pad: nrows,ncols = %d, %d\n", nrowsPad, ncolsPad);
  fprintf(stderr, "ntiles i,j = %d, %d\n", ntiles_i, ntiles_j);
  fprintf(stderr, "tsr,tsc = %d, %d\n", tsr, tsc);

  for(int ti = 0; ti < ntiles_i; ti++) {
    for(int tj = 0; tj < ntiles_j; tj++) {
      int tnum = ti * ntiles_j + tj;
      //cerr << "Checking tile " << ti << "," << tj << " = " << tnum << endl;
      for(int i=ti*(tsr-1); i <= ti*(tsr-1)+tsr-1; i++) {
		for(int j=tj*(tsc-1); j <= tj*(tsc-1)+tsc-1; j++) {
		  if(!IS_BOUNDARY(i,j)) {
			ijCostSource val(i, j, costSourceType());
			if(classify(&val) != tnum) {
			  fprintf(stderr, "ti=%d, tj=%d, i=%d, j=%d\n", ti, tj, i, j);
			  fprintf(stderr, "classify=%d\n", classify(&val));
			  assert(0);
			}
		  }
		}
      }
    }
  }
  cerr << "Checker OK" << endl;
}


IJClassifier::IJClassifier(const char* config) {
  readConfigFile(config);

  //computeNumBoundaries(nrows, tsr);
  numITiles = (int)ceil((double)(ncolsPad - 1) / (tsc - 1));

#ifndef NDEBUG
  checker();
#endif
}
  

// return tile number
int
IJClassifier::classify(const ijCostSource *c) {
  dimension_type row, col;

  assert(numITiles > 0);

  row = c->getI();
  col = c->getJ();

  // make sure it's not a boundary point - they belong to several tiles
  assert(!IS_BOUNDARY(row,col));

//   int ipart = (row / (tsr-1)) * (numITiles);
//   int jpart = col / (tsc-1);
  int ipart = (row-1) / (tsr-1);
  int jpart = (col-1) / (tsc-1);

//   int n = ipart + jpart;
  int ntiles_j = CEIL_A_DIV_B(ncolsPad-1, tsc-1);
  int n = ipart * ntiles_j + jpart;

  if(n >= g.ntiles) {
    fprintf(stderr, "i,j = %d,%d\n", row, col);
    fprintf(stderr, "ipart=%d; jpart=%d\n", ipart, jpart);
    assert(n < g.ntiles);    
  }
  return n;
}

