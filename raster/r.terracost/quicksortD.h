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

#ifndef _QUICKSORT_H_
#define _QUICKSORT_H_

#include "distanceType.h"

int partitionD(distanceType array[], int start, int end) {
  distanceType x = array[start];
  int i = start - 1;
  int j = end - 1;
  while (1) {
    do {
      j--;
    } while (array[j] > x);
    do {
      i++;
    } while (array[i] < x);

    if (i < j) {
      distanceType temp = array[i];
      array[i] = array[j];
      array[j] = temp;
    }
    else return j;
  }
};


void quicksortD(distanceType array[], int start, int end) {
  if (start < end) {
    int part = partitionD(array, start, end);
    quicksortD(array, start, part);
    quicksortD(array, start+1, end);
  }
};


#endif
