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


#ifndef __DISTANCE_H
#define __DISTANCE_H


#include "types.h"
//#include "common.h"
#include "input.h"

#define DST_ARRAY 0
#define DST_STREAM  1


class distanceType {
  basicIJType source;
  basicIJType dest;
  cost_type dist;

 public: 

  distanceType(const basicIJType& inSource,
			   const basicIJType& inDest,
			   cost_type inDist) {
    source = inSource;
    dest = inDest;
    dist = inDist;
  };
  
  distanceType () {};

  dim_t getFromI() const { return source.val_i; };
  dim_t getFromJ() const { return source.val_j; };
  dim_t getToI() const { return dest.val_i; };
  dim_t getToJ() const { return dest.val_j; };

  const basicIJType& getSource() const { return source; };
  const basicIJType& getDest() const { return dest; };

  cost_type getDistance() const { return dist; };
  
  friend ostream& operator << (ostream& s, const distanceType &dt) {
    s << "(" << dt.source << "," << dt.dest << "): " << dt.dist;
    return s;
  };

  friend bool operator == (distanceType &d1, distanceType &d2) {
    return (d1.getFromI() == d2.getFromI()) &&
      (d1.getFromJ() == d2.getFromJ()) &&
      (d1.getToI() == d2.getToI()) &&
      (d1.getToJ() == d2.getToJ());
  }

  friend bool operator < (distanceType &d1, distanceType &d2) {
    if (d1.getFromI() >= d2.getFromI())
      return false;
    if (d1.getFromJ() >= d2.getFromJ())
      return false;
    if (d1.getToI() >= d2.getToI())
      return false;
    if (d1.getToJ() >= d2.getToJ())
      return false;
    return true;
  }

    friend bool operator > (distanceType &d1, distanceType &d2) {
    if (d1.getFromI() <= d2.getFromI())
      return false;
    if (d1.getFromJ() <= d2.getFromJ())
      return false;
    if (d1.getToI() <= d2.getToI())
      return false;
    if (d1.getToJ() <= d2.getToJ())
      return false;
    return true;
  }

};



class distanceIJCompareType {

 public:

  // Returns -1 if a is less than b (tile order)
  // Returns 0 if equal
  // Returns 1 if b is less than a
  static int compare (const distanceType &a, const distanceType &b) {
    if (a.getFromI() < b.getFromI()){
      return -1;				/* a <i b */
    } else if (a.getFromI() == b.getFromI()) {
      if (a.getFromJ() < b.getFromJ()) {
		return -1;				/* a <j b */
      } else if (a.getFromJ() == b.getFromJ()) {
		if (a.getToI() < b.getToI()) {
		  return -1;			/* a i< b */
		} else if (a.getToI() == b.getToI()) {
		  if (a.getToJ() < b.getToJ()) {
			return -1;			/* a j< b */
		  } else if (a.getToJ() == b.getToJ()) {
			return 0;
		  }
		}
      }
    }
    return 1;
  };
  
};



#endif
