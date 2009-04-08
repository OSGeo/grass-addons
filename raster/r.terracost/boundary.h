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


#ifndef __boundary_h
#define __boundary_h

#include <grass/iostream/ami.h>

#include "types.h"
#include "common.h"
#include "input.h"
#include "distanceType.h"
#include "sortutils.h"

#include <math.h>
#include <assert.h>

#define BND_ARRAY 0
#define BND_STREAM  1

//controls print statements
//#define DEBUG_BND

#define CHECK_AE(ae,stream)											\
if((ae) != AMI_ERROR_NO_ERROR) {									\
  cerr << "ami error at " << __FILE__ << ":" << __LINE__ << endl;	\
  cerr << "ae=" << ami_str_error[(ae)] << endl;						\
  cerr << "path=" << (stream)->name() << endl;						\
  assert(0);														\
  exit(1);															\
}


size_t memForNormalDijkstra(dimension_type rows, dimension_type cols);

/* sets tileSizeRows, tileSizeCols, nrowsPad, ncolsPad given the
   memory to be used by a tile; the size of a tile is chosen so that
   a tile uses at most maxmem memory; in order that boundary tiles
   have same size as internal tiles we pad the grid we extra rows and
   columns; the size of the grid is thus (nrowsPad, ncolsPad) */
void initializeTileSize(dimension_type *tileSizeRows, 
			dimension_type *tileSizeCols, 
			size_t maxmem);

void initializeTileSize(dimension_type *tileSizeRows, 
			dimension_type *tileSizeCols, 
			int numTiles);

void optimizeTileSizeUser(dimension_type *tileSizeRows, 
			  dimension_type *tileSizeCols, 
			  int baseSizeRows, int baseSizeCols, 
			  int tileRows, int tileCols);

void  optimizeTileSize(dimension_type *tileSizeRows, 
		       dimension_type *tileSizeCols, 
		       int baseTileSize);


/* Computes either the number of boundary rows or columns in a grid 
  depending on the input.*/
dimension_type computeNumBoundaries(dimension_type dIn, int tsIn);

dimension_type lastTileSizeRow(dimension_type d, int trIn);
dimension_type lastTileSizeCol(dimension_type d, int tcIn);

/* A structure that handles the boundary points of a grid; boundary
   points are the points on the boundary of the subgrids (tile); The
   points stored in the structure are of the type CostSourceType (if
   mode==ARRAY) or ijCostType (if mode==STR).

   If the size of the grid is N and the size of a tile is R, there are
   order N/sqrt(R) boundary points.

   The structure can work in one of two modes: it stores the boundary
   points in an array in internal memory (BND_ARRAY mode), or, it
   stores the boundary points in a stream on disk (BND_STREAM mode).

   The mode is chosen by the structure depending on how much memory is
   available: if there is enough nemory available to store the
   boundary the mode is set to BND_ARRAY; otherwise it is set to
   BND_STREAM

*/

template <class T>
class BoundaryType {

  /* 
     GLOBALLY DEFINED
     dimension_tye nrows, ncols, nrowsPad, ncolsPad;

     Size of the entire grid before and after padding.
  */


  /* the number of boundary rows/columns in the grid  */
  dimension_type bndrows, bndcols; 

  /* the number of boundary points in the structure */
  int size;

  /* the dimension of a tile */
  dimension_type tileSizeRows, tileSizeCols; 

  int mode; /* mode can be BND_ARRAY or BND_STREAM */
  AMI_STREAM< ijCostType<T> > *bndstr;
  T ** bndGridRows, ** bndGridCols;
 
  int isSorted; 


 protected: 
  int isIBoundary(dimension_type i) const;

  int isJBoundary(dimension_type j) const;

  dimension_type iToArrayBnd(dimension_type i) const;
  dimension_type jToArrayBnd(dimension_type j) const;

  //sorts bnd structure if structure is a stream
  void sortBnd();

  void decBnd();
 public: 
  
  /* allocates a BoundaryType structure and finds the optimal tile
     size; it also sets the mode as BND_ARRAY or BND_STREAM. 
     rows and cols are the tile size */
  BoundaryType(dimension_type rows, dimension_type cols, size_t mem);
  BoundaryType(dimension_type rows, dimension_type cols, int inMode);
  BoundaryType(dimension_type rows, dimension_type cols, const char* bndPath);
  
  ~BoundaryType(); 

  void initialize(const T val);
  
  dimension_type lastTileSizeRow(dimension_type d, int trIn);
  dimension_type lastTileSizeCol(dimension_type d, int tcIn);

  void markAsSorted() { isSorted = 1; }

  //point (i,j) should be a boundary point;insert cost of point (i,j)
  //into the structure

  void insert(ijCostType<T> x);

  /* 
     point (i,j) should be a boundary point; returns ijCostType stored
     at point (i,j); assume space for r is allocated
  */ 
  void get(dimension_type i, dimension_type j, ijCostType<T> *r); 
  int canGetFast(dim_t i, dim_t j) const { return mode == BND_ARRAY; };

  //return nb of boundaries stored in the structure
  int getSize();

  dimension_type getTileSizeRows();

  dimension_type getTileSizeCols();

  dimension_type getBndrows();

  dimension_type getBndcols();

  int isBoundary(dimension_type i, dimension_type j) const;

  /* Hasn't been written yet, but should print something */
  void print();

  off_t length();		/* number of objects in boundary */

  //checks points on an input stream against boundary points
  // exit if error is found
  void testBoundary(AMI_STREAM< ijCostType<T> >* debugstr);

  //how much memory does it use? 
  long memoryUsage() {
	if (mode== BND_ARRAY) {
	  return (bndrows*(ncolsPad)+bndcols*(nrowsPad))*sizeof(T);
	} else {
	  return 0; 
	} 
  }

  /* write the boundary to a file */
  void serialize(const char* path) {

	if (mode != BND_ARRAY) {
	  cerr << "Method supported only for BND_ARRAY\n";
	  exit(1); 
	}
	AMI_err ae;
	AMI_STREAM<T> *stream;
	
	*stats << "serializing boundary: " << path << endl;
	
	stream = new AMI_STREAM<T>(path, AMI_WRITE_STREAM);
	stream->persist(PERSIST_PERSISTENT);

	//first write out size
	ae = stream->write_item(size);
	CHECK_AE(ae, stream); 

	//save rows
	assert(bndGridRows );
    for (int i=0; i< bndrows; i++) {
	  assert(bndGridRows[i]);
	  for (int j=0; j < ncolsPad; j++) {
		ae = stream->write_item(bndGridRows[i][j]);
		CHECK_AE(ae, stream); 
	  }
    }
	//save cols
    assert(bndGridCols);
    for (int i=0; i< bndcols; i++) {
	  assert(bndGridCols[i]);
	  for (int j=0; j< nrowsPad; j++) {
		ae = stream->write_item(bndGridCols[i][j]);
		CHECK_AE(ae, stream); 
	  }
	} 

	delete stream;
  }
  
  //reconstruct from file */
  void reconstruct(const char *path) {
	
	
	AMI_err ae;
	AMI_STREAM<T> *stream;
	
	stream = new AMI_STREAM<T>(path, AMI_READ_STREAM);
	stream->persist(PERSIST_PERSISTENT);
	
	assert(stream->stream_len() == (bndrows*ncolsPad + bndcols*nrowsPad + 1)); 

	//first read out size
	T* tmp; 
	ae = stream->read_item(&tmp);
	CHECK_AE(ae, stream); 
	size = (int) (*tmp);

	//read rows
	assert(bndGridRows );
    for (int i=0; i< bndrows; i++) {
	  assert(bndGridRows[i]);
	  for (int j=0; j < ncolsPad; j++) {
		ae = stream->read_item(&tmp); 
		bndGridRows[i][j] = *tmp;
		CHECK_AE(ae, stream); 
	  }
    }

	//read cols
    assert(bndGridCols);
    for (int i=0; i< bndcols; i++) {
	  assert(bndGridCols[i]);
	  for (int j=0; j< nrowsPad; j++) {
		ae = stream->read_item(&tmp); 
		bndGridCols[i][j] = *tmp;
		CHECK_AE(ae, stream); 
	  }
	} 

	delete stream;
  };


};







/* ************************************************************ */
/* allocates a BoundaryType structure based on a previously computed
   optimal size; it also sets the mode as BND_ARRAY or BND_STREAM 
   depending on mem */
template <class T>
BoundaryType<T>::BoundaryType(dimension_type rows, dimension_type cols, 
			      size_t mem) {
  bndstr = NULL;
  
  tileSizeRows = rows;
  tileSizeCols = cols;
  bndrows = computeNumBoundaries(nrowsPad, tileSizeRows);
  bndcols = computeNumBoundaries(ncolsPad, tileSizeCols);

  size = 0;

  //number of boundray points 
  long nb;
  nb = bndrows*(ncolsPad)+bndcols*(nrowsPad);
  
  /* 
     if the boundarys will fit into the amount of memory specified by
     the mem parameter, then they will be stored as arrays, otherwise
     they will be stored as AMI_STREAMs
  */

  if (nb*sizeof(T) <= mem) {
    mode = BND_ARRAY;
  }
  else {
    mode = BND_STREAM;
  }

  /* Declare the array/stream  to store values*/
  decBnd();
}




/* ************************************************************ */
/* allocates a BoundaryType structure and finds the optimal tile size;
   it also sets the mode as BND_ARRAY or BND_STREAM depending on the
   inMode.
*/
template <class T>
BoundaryType<T>::BoundaryType(dimension_type rows, dimension_type cols, 
			      int inMode) {
  bndstr = NULL;
  
  tileSizeRows = rows;
  tileSizeCols = cols;
  bndrows = computeNumBoundaries(nrowsPad, tileSizeRows);
  bndcols = computeNumBoundaries(ncolsPad, tileSizeCols);
  size = 0;
  //user can set mode
  mode = inMode;

  /* Declare the array/stream  to store values*/
  decBnd();
}

/* constructor set to stream mode where we can specify which stream is
   to be used. Used in parallel implementation.*/
template <class T>
BoundaryType<T>::BoundaryType(dimension_type rows, dimension_type cols, 
			      const char* bndPath) {
  
  tileSizeRows = rows;
  tileSizeCols = cols;
  bndrows = computeNumBoundaries(nrowsPad, tileSizeRows);
  bndcols = computeNumBoundaries(ncolsPad, tileSizeCols);

  mode = BND_STREAM;
  bndstr = new AMI_STREAM< ijCostType<T> >(bndPath, AMI_READ_STREAM);
  assert(bndstr);
  size = bndstr->stream_len();
  bndstr->persist(PERSIST_PERSISTENT); /* always persistent?? XXX -RW */

  cerr << "BoundaryType: created from path " << bndPath << endl;
}



/* ************************************************************ */
template <class T>
BoundaryType<T>::~BoundaryType() {
  
  
  switch (mode) {
    
  case BND_ARRAY:
    for (int i=0; i< bndcols; i++) {
      delete [] bndGridCols[i];
    }
    delete [] bndGridCols;
    for (int i=0; i< bndrows; i++) {
      delete [] bndGridRows[i];
    }
    delete [] bndGridRows;
    break;
    
  case BND_STREAM:
   
    delete bndstr;
    break;
  }

}



/* ************************************************************ */
/* 
   declares the boundary array or the boundary AMI_STREAM depending
   on the mode.
*/
template <class T>
void
BoundaryType<T>::decBnd() {

  switch (mode) {

  case BND_ARRAY:

	cerr << "bndrows=" << bndrows << endl;
	cerr << "bndcols=" << bndcols << endl;
	cerr << "ncolsPad=" << ncolsPad << endl;
	cerr << "nrowsPad=" << nrowsPad << endl;
	cerr << "memory load = " << 
	  ( ( sizeof(T*) * (bndrows+bndcols) +    
		  sizeof(T) * (ncolsPad * bndrows + nrowsPad * bndcols) ) / (1<<20) )
		 << " MB" << endl;

    /* Constructs 2 arrays for storing boundary values one indexed i,j
       the other indexed j,i */
    bndGridRows = new T* [bndrows];
    assert(bndGridRows );
    for (int i=0; i< bndrows; i++) {
      bndGridRows[i] = new T[ncolsPad];
      assert(bndGridRows[i]);
    }
    
    bndGridCols = new T* [bndcols];
    assert(bndGridCols);
    for (int i=0; i< bndcols; i++) {
      bndGridCols[i] = new T[nrowsPad];
      assert(bndGridCols[i]);
    } 
    break;
    
  case BND_STREAM:
    cout << "creating Boundary structure, stream mode.\n";
    //cout << "step0: " << opt->step0 << endl; cout.flush();

    /* the following condition should probably move to main.cc -RW */
	/* the following check should be !RUN_S1 or some such... -RW XXX */
    if (opt->runMode == RUN_S0) {
      bndstr = new AMI_STREAM< ijCostType<T> >(resolvePath(opt->s0bnd));
    } else {
      bndstr = new AMI_STREAM< ijCostType<T> >();
    }
    assert(bndstr);
    bndstr->persist(PERSIST_PERSISTENT); /* leaks temp files? XXX -RW */
    break;
  }
}

template <class T>
void
BoundaryType<T>::initialize(const T val) {

  assert(mode == BND_ARRAY);
  if(mode != BND_ARRAY) {
	cerr << "invalid call" << endl;
	exit(1);
  }

  for(int row=0; row<bndrows; row++) {
	for(int col=0; col<ncolsPad; col++) {
	  bndGridRows[row][col] = val;
	}
  }
  for(int col=0; col<bndcols; col++) {
	for(int row=0; row<nrowsPad; row++) {
	  bndGridCols[col][row] = val;
	}
  }
}


/* ************************************************************ */
template <class T>
void
BoundaryType<T>::insert(ijCostType<T> ct) {

  switch (mode) {

  case BND_STREAM:

    /* just inserting can't work! (unless it's to just create the stream) XXX-RW */

    AMI_err ae;
    ae = bndstr->write_item(ct);
    assert(ae == AMI_ERROR_NO_ERROR);
    isSorted = 0;
    break;

  case BND_ARRAY:
    dimension_type oldI, oldJ;
    dimension_type newI, newJ;

    oldI = ct.getI();
    oldJ = ct.getJ();
    T x = ct.getCost();

    if (!isIBoundary(oldI) && !isJBoundary(oldJ)) {
      cout << "Boundary::insert::Boundary ERROR at (" << oldI << "," << 
	oldJ << ")" << endl;
      cout.flush();
      *stats << "Boundary::insert::Boundary ERROR at (" << oldI << "," << 
	oldJ << ")" << endl;
      stats->flush();
      exit(0);
    }

    if (oldI == nrowsPad-1) {
      newI = iToArrayBnd(oldI);
      newJ = oldJ;
#ifdef DEBUG_BND
      cout << "insert " << ct << "at pos (" << newI << "," << newJ << ") 1\n"; 
      cout.flush();
#endif
      assert(newI < bndrows);
      bndGridRows[newI][newJ] = x;
    }

    // switch i and j here because bndGridCols is indexed [col][row]
    if (oldJ == ncolsPad-1) {
      newI  = jToArrayBnd(oldJ);
      newJ = oldI;
#ifdef DEBUG_BND
      cout << "insert " << ct << "at pos (" << newI << "," << newJ << ") 2\n"; 
      cout.flush();
#endif
      assert(newI < bndcols);
      bndGridCols[newI][newJ] = x;
    }

    if (isIBoundary(oldI) && oldI != nrowsPad-1) {
      newI = iToArrayBnd(oldI);
      newJ = oldJ;
#ifdef DEBUG_BND
      cout << "insert " << ct << "at pos (" << newI << "," << newJ << ") 3\n"; 
      cout.flush();
#endif
      assert(newI < bndrows);
      bndGridRows[newI][newJ] = x;
    }

    // switch i and j here because bndGridCols is indexed [col][row]
    if (isJBoundary(oldJ) && oldJ != ncolsPad-1) {
      newI  = jToArrayBnd(oldJ);
      newJ = oldI;
#ifdef DEBUG_BND
      cout << "insert " << ct << "at pos (" << newI << "," << newJ << ") 4\n"; 
      cout.flush();
#endif
      assert(newI < bndcols);
      bndGridCols[newI][newJ] = x;
    }

#ifndef NDEBUG
    ijCostType<T> temp;
    get(ct.getI(),ct.getJ(),&temp);
    //assert(temp == ct);
    if (!(temp == ct)) {
      cout << "BoundaryType::insert " << ct << ", extract " << temp << endl;
      exit(0);
    }
#endif
    break;
  }

  size++;
}





/* ************************************************************ */
//return 1 if (i,j) is on tile boundary
template <class T>
int
BoundaryType<T>::isBoundary(dimension_type i, dimension_type j) const {
  if (isIBoundary(i) || isJBoundary(j))
    return 1;
  return 0;
}

/* ************************************************************ */
template <class T>
int
BoundaryType<T>::isIBoundary(dimension_type inI) const {
  if (inI == 0 || inI % (tileSizeRows-1)==0 || inI==nrowsPad-1)
    return 1;
  return 0;
} 


/* ************************************************************ */
template <class T>
int
BoundaryType<T>::isJBoundary(dimension_type inJ) const {
  if (inJ == 0 || inJ % (tileSizeCols-1)==0 || inJ==ncolsPad-1)
    return 1;
  return 0;
} 

/* ************************************************************ */
template <class T>
int
BoundaryType<T>::getSize() {
  return size;
}

/* ************************************************************ */
template <class T>
dimension_type
BoundaryType<T>::getTileSizeRows() {
  return tileSizeRows;
}

/* ************************************************************ */
template <class T>
dimension_type
BoundaryType<T>::getTileSizeCols() {
  return tileSizeCols;
}

/* ************************************************************ */
template <class T>
dimension_type
BoundaryType<T>::getBndrows() {
  return bndrows;
}

/* ************************************************************ */
template <class T>
dimension_type
BoundaryType<T>::getBndcols() {
  return bndcols;
}

/* ************************************************************ */
template <class T>
void
BoundaryType<T>::sortBnd() {
  assert(!isSorted);		/* -RW */
  MinIOCostCompareType<T> sortFun = MinIOCostCompareType<T>(); /* ij compare -RW */
  sortFun.setTileSize(tileSizeRows, tileSizeCols);
  assert(mode == BND_STREAM);
  stats->recordLength("BoundaryType: Sorting boundary stream...", bndstr);
  sort(&bndstr, sortFun);
  stats->recordLength("BoundaryType: Sorting boundary stream... done", bndstr);
  isSorted = 1;
}


/* ************************************************************ */
/* 
   point (i,j) should be a boundary point; returns ijCostType stored
   at point (i,j); assume r is allocated
*/ 
template <class T>
void
BoundaryType<T>::get(dimension_type i, dimension_type j, ijCostType<T> *r) {

  AMI_err ae;

  switch (mode) {

  case BND_STREAM:
    if (!isSorted){
      sortBnd();
    }
    ijCostType<T> *tmp;
    assert(isBoundary(i,j));
    assert(bndstr);
    if (isIBoundary(i)) {
      //stream offset where this bnd point is located
      int index = ((i/(tileSizeRows-1))*ncolsPad +
		   (i/(tileSizeRows-1))*(tileSizeRows-2)*bndcols + j);
      //cout << "I Bnd Stream: " << bndstr->stream_len() << " Index: " << 
      //	index << "\n"; cout.flush();
      //cout << "BndLen: " << bndstr->stream_len() << endl;cout.flush();

      //cout << "BndStrLen: " << bndstr->stream_len() << " index: " << index
      //	   << "  (" << i << "," << j << ")" << endl; cout.flush();

      assert(bndstr->stream_len() > index);
      ae = bndstr->seek(index);
      assert(ae==AMI_ERROR_NO_ERROR);

      ae = bndstr->read_item(&tmp);
      assert(ae==AMI_ERROR_NO_ERROR);
    } else {
      //stream offset where this bnd point is located
      int index = (i/(tileSizeRows-1)+1)*ncolsPad + 
	(i/(tileSizeRows-1))*(tileSizeRows-2)*bndcols + 
	(j/(tileSizeCols-1))*(tileSizeRows-2) +
	i%(tileSizeRows-1)-1;

      //cout << "J Bnd Stream: " << bndstr->stream_len() << " Index: " << 
      //	index << "\n"; cout.flush();

      assert(bndstr->stream_len() > index);
      ae = bndstr->seek(index);
      assert(ae == AMI_ERROR_NO_ERROR);

      ae = bndstr->read_item(&tmp);
      assert(ae==AMI_ERROR_NO_ERROR);
    }    
    *r = ijCostType<T>(*tmp);

    /* debug: error */
    if(r->getI() != i || r->getJ() != j) {
      fprintf(stderr, "ij mismatch; r.i=%d r.j=%d i=%d j=%d\n",
	      r->getI(), r->getJ(), i, j);
    }
    assert(r->getI() == i && r->getJ() == j);
    break;

  case BND_ARRAY: 
    int row_i, row_j;
    assert(isBoundary(i,j));

    if (i == nrowsPad-1) {
      row_i= bndrows - 1;
      row_j= j;
      *r = ijCostType<T>(i,j, bndGridRows[row_i][row_j]);
    }

    // switch i and j here because bndGridCols is indexed [col][row]
    else if (j == ncolsPad-1) {
      row_i= bndcols - 1;
      row_j= i;
      *r = ijCostType<T>(i,j, bndGridCols[row_i][row_j]);
    }

    else if (isIBoundary(i)) {
      row_i = iToArrayBnd(i);
      row_j = j;
      *r = ijCostType<T>(i,j, bndGridRows[row_i][row_j]);
    }

    // switch i and j here because bndGridCols is indexed [col][row]
    else if (isJBoundary(j)) {
      row_i = jToArrayBnd(j);
      row_j = i;
      *r = ijCostType<T>(i,j, bndGridCols[row_i][row_j]);
    }

    assert(r->getI() == i && r->getJ() == j);
    break;
  }
}



/* ************************************************************ */
template <class T>
dimension_type
BoundaryType<T>::iToArrayBnd(dimension_type i) const {
  assert(isIBoundary(i));

  dimension_type row_i;

  if (tileSizeRows == 2)
    return i;

  if (i == 0)
    return 0;

  if (i == nrowsPad-1) {
    row_i= bndrows-1;
    return row_i;
  }

  if (isIBoundary(i)) {
    row_i = computeNumBoundaries(i, tileSizeRows) - 1;
    return row_i;
  }

  printf("ERROR: Shouldn't have made it here BoundaryType::iToArrayBnd");
  exit(1);
  return 0;
}


/* ************************************************************ */
template <class T>
dimension_type
BoundaryType<T>::jToArrayBnd(dimension_type j) const {
  assert(isJBoundary(j));

  dimension_type col_j;

  if (tileSizeCols == 2)
    return j;

  if (j == 0)
    return 0;

  if (j == ncolsPad-1) {
    col_j = bndcols-1;
    return col_j;
  }

  if (isJBoundary(j)) {
    col_j = computeNumBoundaries(j, tileSizeCols) - 1;
    return col_j;
  }

  printf("ERROR: Shouldn't have made it here BoundaryType::iToArrayBnd");
  assert(0);
  return 0;
}


/* ************************************************************ */
template <class T>
void
BoundaryType<T>::print() {
  ijCostType<T> out;
  for (int i=0; i<nrowsPad; i++) {
    for (int j=0; j<ncolsPad; j++) {
      if (isBoundary(i,j)) {
	get(i,j,&out);
	*stats << out;
      }
      else {
	*stats << "              " ;
      }
    }
    *stats << endl;
  }
}


/* ************************************************************ */
template <class T>
off_t
BoundaryType<T>::length() {
  switch (mode) {
  case BND_ARRAY:
    assert(0);
    break;
  case BND_STREAM:
    return bndstr->tell();
    break;
  }
  assert(0);
  return -1;
}


/* ************************************************************ */
//checks points on an input stream against boundary points
// exit if error is found
template <class T>
void 
BoundaryType<T>::testBoundary(AMI_STREAM< ijCostType<T> >* debugstr) {

  cout << "testing boundary dstr\n"; cout.flush();

  AMI_err ae;
  ijCostType<T> *in, temp;
  assert(debugstr);
  assert(debugstr->stream_len() == nrowsPad*ncolsPad);
  ae = debugstr->seek(0);
  assert(ae == AMI_ERROR_NO_ERROR);

  for (int i = 0; i < nrowsPad; i++) {
    for (int j = 0; j < ncolsPad; j++) {
      ae = debugstr->read_item(&in);
      assert(ae == AMI_ERROR_NO_ERROR);
      if (isBoundary(i,j)) {
	get(i,j, &temp);
	if(in->getCost() != temp.getCost())
	  cout << "Cost Mismatch! Real Value: " << *in << "Boundary Value: " <<
	    temp->getCost() << "\n";
      }
    }
  }
}

#endif
