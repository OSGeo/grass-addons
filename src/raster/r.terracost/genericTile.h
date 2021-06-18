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

#ifndef GENERICTILE_H
#define GENERICTILE_H

#include <ostream>
#include "types.h"
#include "input.h"


/* #ifndef NDEBUG */
/* #define ASSERT assert */
/* #else */
/* #define ASSERT(x) */
/* #endif */

/* turn on/off asserts manually until they are fixed in the rest of the code */
#define ASSERT(x) assert(x)

/* ---------------------------------------------------------------------- */

/* a basic tile type that just provices accessor methods */
template<class T>
class genericTile {
protected:
  dim_t rows, cols;
  T **data;

 public:
  genericTile(dim_t inRows, dim_t inCols);
  ~genericTile();

  const T& get(dim_t i, dim_t j) const;
  void put(dim_t i, dim_t j, const T value);
  void put(dim_t i, dim_t j, const T *value);

  int inTile(dim_t inI, dim_t inJ) const;

  int isBoundary(dim_t i, dim_t j) const {
	return ((i==0) || (j==0) || (i==rows-1) || (j==cols-1));
  }

  dim_t getNumRows() const { return rows; };
  dim_t getNumCols() const { return cols; };

  void dumpTile(ostream &os, const char *prefix) const;
};

/* ---------------------------------------------------------------------- */

/* a tile that can return a ijCostType using a given offset */
template<class T>
class mappedTile : public genericTile<T> {
  dim_t baseRow, baseCol;
 public:
  mappedTile(dim_t inRows, dim_t inCols,
			 dim_t i, dim_t j);

  /* figure out offset given the root element */
  void deriveBasis(const ijCostType<T> & root, dim_t i, dim_t j);

  const ijCostType<T> getComplex(dim_t i, dim_t j) const;
  void  put(dim_t i, dim_t j, const ijCostType<T> &val);
};

/* ---------------------------------------------------------------------- */
/* implementations */


template<class T>
genericTile<T>::genericTile(dim_t inRows, dim_t inCols) : rows(inRows), cols(inCols) {
  data = new T* [rows];
  for(dim_t i=0; i<rows; i++) {
    data[i] = new T [cols];
  }
}

template<class T>
genericTile<T>::~genericTile() {
  for(dim_t i=0; i<rows; i++) {
    delete data[i];
  }
  delete [] data;
}

template<class T>
inline
const T &
genericTile<T>::get(dim_t i, dim_t j) const {
  ASSERT(inTile(i,j));
  return data[i][j];
}

template<class T>
void
genericTile<T>::put(dim_t i, dim_t j, const T value) {
  ASSERT(inTile(i,j));
  data[i][j] = value;
}

/* template<class T> */
/* void */
/* genericTile<T>::put(dim_t i, dim_t j, const T *value) { */
/*   ASSERT(inTile(i,j)); */
/*   data[i][j] = *value; */
/* } */

template<class T>
int
genericTile<T>::inTile(dim_t i, dim_t j) const {
  //return (i < rows && j < cols && i >= 0 && j >= 0);
  return (i < rows && j < cols && i != dim_undef && j != dim_undef);
}

template<class T>
void
genericTile<T>::dumpTile(ostream &os, const char *prefix) const {
  int i, j;
  
  os.flush();
  for(i=0; i<rows; i++) {
	os << prefix;
	for(j=0; j<cols; j++) {
	  os << data[i][j];
	}
	os << endl;
  }
  os.flush();
}



#define INTILE(_tilep,_i,_j) ( ((_i) >= 0) && ((_j) >= 0) 			    \
							  && ((_i) < (_tilep)->getNumRows()) 		\
							  && ((_j) < (_tilep)->getNumCols()) )

/* ---------------------------------------------------------------------- */

template<class T>
mappedTile<T>::mappedTile(dim_t inRows, dim_t inCols,
						  dim_t i=0, dim_t j=0) 
  : genericTile<T>(inRows, inCols), baseRow(i), baseCol(j) {
}

template<class T>
void
mappedTile<T>::deriveBasis(const ijCostType<T> & ijct, dim_t i, dim_t j) {
  baseRow = ijct.getI() - i;
  baseCol = ijct.getJ() - j;
}

template<class T>
const ijCostType<T>
mappedTile<T>::getComplex(dim_t i, dim_t j) const {
  return ijCostType<T>(baseRow + i, baseCol + j, genericTile<T>::get(i, j));
}

#define DBG_ERROR() ( cerr << __FILE__ << ":" << __LINE__ << " ijmismatch: put " << val \
					  << " at i,j=" << i << "," << j << endl )
#define DBG_CHECK_I(_val,_i) ( (_val.getI() - baseRow == _i) || DBG_ERROR() )
#define DBG_CHECK_J(_val,_j) ( (_val.getJ() - baseCol == _j) || DBG_ERROR() )

template<class T>
void
mappedTile<T>::put(dim_t i, dim_t j, const ijCostType<T> &val) {
/*   assert(val.getI() >= baseRow && val.getI() < baseRow + rows); */
/*   assert(val.getJ() >= baseCol && val.getJ() < baseCol + cols); */
  ASSERT(val.getI() - baseRow == i);
  ASSERT(val.getJ() - baseCol == j);
  //DBG_CHECK_I(val, i);
  //DBG_CHECK_J(val, j);
  genericTile<T>::put(i, j, val.getCost());
}

#endif
