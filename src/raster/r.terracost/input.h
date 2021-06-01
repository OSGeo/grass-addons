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


#ifndef _INPUT_H
#define _INPUT_H

//#include "common.h"
#include "types.h"
#include "config.h"
#include <assert.h>

#define NO_SOURCE 0
#define SOURCE 1

#define NODATA -9999


//int isNull( const cost_type x);
//int isNull(const costSourceType x);
//int isNull(const dimension_type x);


class costSourceType {
 private:
  cost_type cost;
#ifndef sHACKS
  char source;
#endif
 public:

#ifdef sHACKS
  costSourceType(cost_type inCost, bool inSource) : {
    cost = (inSource ? cost : -cost);
  }
  costSourceType() : cost(cost_type_max) {}; /* no illegal value... */
#else
  costSourceType(cost_type inCost, char source): 
    cost(inCost), source(source) {};
#if 0
  costSourceType(const costSourceType &a):
    cost(a.cost), source(a.source) {};
#endif
  costSourceType(): cost(-1), source('n') {};
#endif

#if 0
  ~costSourceType(){};
#endif
  
  cost_type getCost() const {
#ifdef sHACKS
    return cost < 0 ? -cost : cost;
#else
    return cost;
#endif
  };
  char getSource() const {
    return source;
  };

  int isSource() const {
    return (source == 'y');
  };
  
  int isNull() const {
    return cost == NODATA;
  };
  
  void print() {
    cout << *this;
  };

  friend ostream& operator << (ostream& s, const costSourceType &ct) {
    s << "(" << ct.cost  << ", isSource=" << ct.source<< ")";
    return s;
  };
  
  friend int operator == (const costSourceType &a, const costSourceType &b) {
    return (a.cost == b.cost) && (a.source == b.source);
  };

};




/* typedef float cost_type */


static int isNull( const cost_type x) {
  return x == NODATA;
};

static int isNull(const costSourceType x) {
  return x.getCost() == NODATA;
};

/* static int isNull(const dimension_type x) { */
/*   return x == NODATA; */
/* }; */


class distanceType;

class basicIJType {
  dimension_type val_i, val_j; 

  friend class distanceType;
public:
  basicIJType(dim_t i, dim_t j) : val_i(i), val_j(j) {};
  basicIJType() : val_i(dim_undef), val_j(dim_undef) {};

  dim_t getI() const { assert(val_i != dim_undef); return val_i; };
  dim_t getJ() const { assert(val_j != dim_undef); return val_j; };
  void setI(dim_t gi) {
    val_i = gi;
  }
  void setJ(dim_t gj) {
    val_j = gj;
  }
  


  void transpose() {		/* flip row & col */
    dim_t tmp = val_i;
    val_i = val_j;
    val_j = tmp;
  }

  friend ostream& operator << (ostream& s, const basicIJType &ct) {
    s << "(" << ct.val_i << "," << ct.val_j << ")";
    return s;
  };

  friend int operator == (const basicIJType &a, const basicIJType &b) {
    return (a.val_i == b.val_i && a.val_j == b.val_j);
  };
  friend int operator != (const basicIJType &a, const basicIJType &b) {
    return (a.val_i != b.val_i || a.val_j != b.val_j);
  };
};


template <class T>
class ijCostType : public basicIJType {
 private:
  T cs; 
  
 public:

  ijCostType(dim_t inI, dim_t inJ, T x): 
    basicIJType(inI, inJ), cs(x) {};

#if 0
  ijCostType(const ijCostType &a):
    basicIJType(a), cs (a.cs) {};
#endif

  ijCostType(): basicIJType(-1, -1), cs() {};

#if 0
  ~ijCostType(){};
#endif
  
  T getCost() const{
    return cs;
  };
  
  void setCost(T cost) {
    cs = cost;
  }

  int isNull() const {
    //return isNull(cs);
    return cs.isNull();
  };

  void print() {
    cout << *this;
  };

  friend ostream& operator << (ostream& s, const ijCostType<T> &ct) {
    s << "(" << ct.getI() << "," << ct.getJ() << ": " << ct.cs << ")";
    return s;
  };

  friend int operator == (const ijCostType<T> &a, const ijCostType<T> &b) {
    return (basicIJType(a) == basicIJType(b) && a.cs == b.cs);
  };
  
};


typedef ijCostType<cost_type> ijCost;
typedef ijCostType<costSourceType> ijCostSource;

template <class T>
class MinIOCostCompareType {
 private: 
/*   static int tileSizeRows; */
/*   static int tileSizeCols; // Check for problems! 22 June 2004 */

 public: 

  void setTileSize(dim_t r, dim_t c) {
	//    MinIOCostCompareType::tileSizeRows = r;
    //    MinIOCostCompareType::tileSizeCols = c;
	/* check against globals */
	assert(tsr == r);
	assert(tsc == c);
  };

/*   int getTileSizeRows() {  */
/*     return MinIOCostCompareType::tileSizeRows; */
/*   }; */
  
/*   int getTileSizeCols() {  */
/*     return MinIOCostCompareType::tileSizeCols; */
/*   }; */

  /* Method used in conjunction with ami_sort if a < b returns -1 if a
     == b returns 0 and if a > b returns 1 */
  static int compare(const ijCostType<T> &a, const ijCostType<T> &b) {
    dim_t ai, aj, bi, bj;
    //tsr = MinIOCostCompareType::tileSizeRows;
    ai = a.getI();
    aj = a.getJ();
    bi = b.getI();
    bj = b.getJ();

    if (ai%(tsr-1) == 0 || bi%(tsr-1) == 0) {
      if (ai < bi ) return -1;
      if (ai > bi ) return 1;
      if (ai == bi) {
	if (aj < bj) return -1;
	if (aj > bj) return 1;
	if (aj == bj) return 0;
      }
    }
    if (ai%(tsr-1) != 0 && bi%(tsr-1) != 0) {
      if ((ai/(tsr-1)) != (bi/(tsr-1))) {
	if (ai < bi ) return -1;
	if (ai > bi ) return 1;
      }
      if ((ai/(tsr-1)) == (bi/(tsr-1))) {
	if (aj < bj) return -1;
	if (aj > bj) return 1;
	if (aj == bj) {
	  if (ai < bi) return -1;
	  if (ai > bi) return 1;
	  if (ai == bi) return 0;
	}
      }
    }
    cout << "We have huge problems here!\n";
    assert(0);			// -RW
    return 0;    //-RW
  };
};


// Returns -1 if a is less than b (tile order)
// Returns 0 if equal
// Returns 1 if b is less than a
//template <class T>
class ijTileCostCompareType {
 private: 
  static int tileSizeRows;
  static int tileSizeCols; // Check for problems! 22 June 2004

 public: 

  void setTileSize(dim_t r, dim_t c) { 
    ijTileCostCompareType::tileSizeRows = r;
    ijTileCostCompareType::tileSizeCols = c;
  };


  int getTileSizeRows() { 
    return ijTileCostCompareType::tileSizeRows;
  };
  
  int getTileSizeCols() { 
    return ijTileCostCompareType::tileSizeCols;
  };

  /* what does this compare?? -RW */
  static int compare(const ijCostSource &a, const ijCostSource &b) {
    int tsr = ijTileCostCompareType::tileSizeRows;
    int tsc = ijTileCostCompareType::tileSizeCols;
    if (a.getI()/(tsr-1) < b.getI()/(tsr-1))
      return -1;

    else if (a.getI()/(tsr-1) == b.getI()/(tsr-1)) {
      if (a.getJ()/(tsc-1) < b.getJ()/(tsc-1))
	return -1;

      else if (a.getJ()/(tsc-1) == b.getJ()/(tsc-1)) {
	if (a.getI() < b.getI())
	  return -1;
	else if(a.getI() == b.getI()) {
	  if (a.getJ() < b.getJ())
	    return -1;
	  else if (a.getJ() == b.getJ())
	    return 0;
	}
      }
    }
    return 1;
  };
};


class ijCostCompareType {
 private: 
  static int tileSizeRows;
  static int tileSizeCols; // Check for problems! 22 June 2004

 public: 

  void setTileSize(dim_t r, dim_t c) { 
    ijCostCompareType::tileSizeRows = r;
    ijCostCompareType::tileSizeCols = c;
  };


  int getTileSizeRows() { 
    return ijCostCompareType::tileSizeRows;
  };
  
  int getTileSizeCols() { 
    return ijCostCompareType::tileSizeCols;
  };

  static int compare(const ijCost &a, const ijCost &b) {
    if (a.getI() < b.getI())
      return -1;

    else if (a.getI() == b.getI()) {
      if (a.getJ() < b.getJ())
	return -1;
      else if (a.getJ() == b.getJ())
	return 0;
    }
    return 1;
  };
};



#endif
