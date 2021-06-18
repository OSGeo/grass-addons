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

#include <grass/iostream/ami.h>
#include "input.h"
#include "genericTile.h"

/* rajiv wickremesinghe 2005 */

/* NB: in this file, a boundary tile is generally the left and top sides ONLY  */




/* template <class T> */
/* class BoundaryStreamObj { */
/*   T data; */
/*  public: */
/*   BoundaryStreamObj(const ijCostType<T> &x) { data = x.getCost(); }; */
/* }; */


#define BMGR_DEBUG if(0)

#define CHECK_AE(ae,stream)											\
if((ae) != AMI_ERROR_NO_ERROR) {									\
  cerr << "ami error at " << __FILE__ << ":" << __LINE__ << endl;	\
  cerr << "ae=" << ami_str_error[(ae)] << endl;						\
  cerr << "path=" << (stream)->name() << endl;						\
  assert(0);														\
  exit(1);															\
}


#define IS_BOUNDARY(row,col) ( assert(tsr), assert(tsc), \
     ( ((row) % (tsr-1)) == 0) || ( ((col) % (tsc-1)) == 0)  )

/* ---------------------------------------------------------------------- */
/* oversee boundary data structures
 * handle the mapping from i,j to pos etc.
 */

template <class CST>
class BoundaryMgr {
 protected:
  unsigned int T, R;			/* size of tile (L,T) boundary, size of row */
  unsigned int NB;			/* size of whole boundary (plus padding) */
  dim_t tsra, tsca;			/* tsra=tsr-1 etc (tile size rows adjusted) */
  dim_t trows, tcols;			/* number of rows/cols of tiles */

 public:
  BoundaryMgr(dim_t tsr, dim_t tsc, dim_t nrows, dim_t ncols);
  int getPos(dim_t i, dim_t j, int debug=0) const;	/* map from grid pos to offset in linear arr */
  void getIJ(int pos, dim_t *ip, dim_t *jp, int debug=0) const;
  void selfcheck() const;

  /* these two functions for backward compatibility.
   * returns number of boundary rows/cols;
   * i.e., 1 more than the number of tile rows/cols */
  dim_t getBndRows() const { return trows+1; };
  dim_t getBndCols() const { return tcols+1; };
};


/* ---------------------------------------------------------------------- */
/*
 * boundary that is fully stored in memory; supports random access
 */
template <class CST>
class CachedBoundaryMgr : public BoundaryMgr<CST> {
  CST *data;

 public:
  char debug;

  CachedBoundaryMgr(dim_t tsr, dim_t tsc, dim_t nrows, dim_t ncols)
	: BoundaryMgr<CST>(tsr, tsc, nrows, ncols) {
	data = new CST [ this->NB ];
  };
  virtual ~CachedBoundaryMgr() { delete data; }

  void initialize(const CST &val) {
	for(int i=0; i< this->NB; i++) {
	  data[i] = val;
	}
  };

  /* insert one item into the boundary */
  void insert(const ijCostType<CST> &x) {
#ifndef NDEBUG
	if(debug == 'i') {
	  printf("BMGR%c %d\t%d\n", debug, x.getI(), x.getJ());
	  fflush(stdout);
	}
#endif
	int pos = getPos(x.getI(), x.getJ());
	//printf("BMGRi %d\t%d\n", x.getI(), x.getJ());
	assert(pos < this->NB);
	data[pos] = x.getCost();
  };

  const CST get(dim_t i, dim_t j) const {
#ifndef NDEBUG
	if(debug == 'g') {
	  printf("BMGR%c %d\t%d\n", debug, i, j);
	  fflush(stdout);
	}
#endif
	int pos = this->getPos(i, j);
	assert(pos < this->NB);
	return data[pos];
  };

  /* how much memory it uses */
  long memoryUsage() {
	return this->NB * sizeof(CST); 
  }

  /* write out the boundary to file */
  void serialize(const char *path) {
	AMI_err ae;
	AMI_STREAM<CST> *stream;

	*stats << "serializing boundary: " << path << endl;

	stream = new AMI_STREAM<CST>(path, AMI_WRITE_STREAM);
	stream->persist(PERSIST_PERSISTENT);

	for(int i=0; i < this->NB; i++) {
	  ae = stream->write_item(data[i]);
	  CHECK_AE(ae,stream);
	}
	delete stream;
  };

  void reconstruct(const char *path) {
	AMI_err ae;
	AMI_STREAM<CST> *stream;

	stream = new AMI_STREAM<CST>(path, AMI_READ_STREAM);
	stream->persist(PERSIST_PERSISTENT);

	for(int i=0; i < this->NB; i++) {
	  ae = stream->read_item(&data[i]);
	  CHECK_AE(ae,stream);
	}
	delete stream;
  };

};


/* ---------------------------------------------------------------------- */
/* 
 * boundary that is only written to disk. wrapper around cached version for now,
 * but could be optimized. Note that the stream is only created if serialize() is called.
 */

template <class CST>
class BoundaryWriter : public CachedBoundaryMgr<CST> {
  char *path;

 public:
  BoundaryWriter(dim_t tsr, dim_t tsc, dim_t nrows, dim_t ncols, const char *pathin)
	: CachedBoundaryMgr<CST>(tsr, tsc, nrows, ncols) {
	path = strdup(pathin);
  };
  ~BoundaryWriter() { free(path); };
  void serialize() { CachedBoundaryMgr<CST>::serialize(path); }

 protected:
  void reconstruct(const char *path) {};
  const ijCostType<CST> & get(dim_t i, dim_t j) const {};
};


/* ---------------------------------------------------------------------- */
/* reader, but only load a tile at a time (actually reads 3+)
 */

template <class CST>
class BoundaryTileReader : public BoundaryMgr<CST> {
  AMI_STREAM<CST> *stream;
  CachedBoundaryMgr<CST> *cache; /* can use another mgr as a source */

 public:
  BoundaryTileReader(dim_t tsr, dim_t tsc, dim_t nrows, dim_t ncols,
				 const char *path) : BoundaryMgr<CST>(tsr, tsc, nrows, ncols) {
	*stats << "BoundaryTileReader using " << path << endl;
	stream = new AMI_STREAM<CST>(path, AMI_READ_STREAM);
	cache = NULL;
  };
  BoundaryTileReader(CachedBoundaryMgr<CST> *cr) : BoundaryMgr<CST>(*cr) {
	stream = NULL;
	cache = cr;
#ifndef NDEBUG
	this->selfcheck();
#endif
  };

  ~BoundaryTileReader() {
	if(stream) delete stream;
  };

  /* read one tile, root at i,j */
  void readTileBoundary(dim_t baseI, dim_t baseJ, genericTile<CST> *tile) {

	BMGR_DEBUG fprintf(stderr, "readTileBoundary: (%d,%d)\n", baseI, baseJ);

	if(cache) {
	  readTileBoundaryCache(baseI, baseJ, tile);
	} else {
	  readTileBoundaryStream(baseI, baseJ, tile);
	}
  }

 private:
  void readTileBoundaryCache(dim_t baseI, dim_t baseJ, genericTile<CST> *tile) {

/* 	cache->debug = 'g'; */

	for(int i=0; i < this->tsra; i++) { 	/* left */
	  tile->put(i, 0, cache->get(baseI+i, baseJ+0));
	}
	for(int j=1; j < this->tsca; j++) { /* top */
	  tile->put(0, j, cache->get(baseI+0, baseJ+j));
	}
	for(int i=0; i <  this->tsra; i++) { 	/* right */
	  tile->put(i, this->tsca, cache->get(baseI + i, baseJ + this->tsca));
	}
	for(int j=0; j <= this->tsca; j++) { /* bottom */
	  tile->put(this->tsra, j, cache->get(baseI + this->tsra, baseJ+j));
	}

/* 	cache->debug = 0; */

  };

  void readTileBoundaryStream(dim_t baseI, dim_t baseJ, genericTile<CST> *tile) {
	AMI_err ae;
	int n = this->tsca + this->tsra - 1; /* tile (boundary) size */
	int n1 = n;
	CST *item;
	int pos;
	int k=0;					/* useful items read + no. of put()s*/

	pos = this->getPos(baseI, baseJ);
	BMGR_DEBUG fprintf(stderr, "reading tile from pos=%d\n", pos);
	ae = stream->seek(pos);
	assert(ae == AMI_ERROR_NO_ERROR);
	for(int i=0; i < this->tsra; i++) { 	/* left */
	  ae = stream->read_item(&item);
	  CHECK_AE(ae,stream);
	  k++;
	  tile->put(i, 0, *item);
	}
	for(int j=1; j < this->tsca; j++) { /* top */
	  ae = stream->read_item(&item);
	  CHECK_AE(ae,stream);
	  k++;
	  tile->put(0, j, *item);
	}
	assert(k == this->T);
	for(int i=0; i < this->tsra; i++) { 	/* right */
	  ae = stream->read_item(&item);
	  CHECK_AE(ae,stream);
	  k++;
	  tile->put(i, this->tsca, *item);
	}

	ae = stream->seek(this->getPos(baseI + this->tsra, baseJ));
	CHECK_AE(ae,stream);

	{ 	/* left bottom point (only need one cell; skip rest) */
	  ae = stream->read_item(&item);
	  CHECK_AE(ae,stream);
	  k++;
	  tile->put(this->tsra, 0, *item);
/* 	  for(int i=1; i<tsra; i++) { */
/* 		ae = stream->read_item(&item); */
/* 		CHECK_AE(ae,stream); */
/* 	  } */
	}
	ae = stream->seek(getPos(baseI + this->tsra, baseJ+1));
	CHECK_AE(ae,stream);

	for(int j=1; j < this->tsca; j++) { /* bottom */
	  ae = stream->read_item(&item);
	  CHECK_AE(ae,stream);
	  k++;
	  tile->put(this->tsra, j, *item);
	}
	{ 	/* right bottom point (only need one cell; skip rest) */
	  ae = stream->read_item(&item);
	  CHECK_AE(ae,stream);
	  k++;
	  tile->put(this->tsra, this->tsca, *item);
	}

	assert(k == 2 * this->tsca + 2 * this->tsra);
  };

};


/* ********************************************************************** */
/* implementations */


template <class CST>
BoundaryMgr<CST>::BoundaryMgr(dim_t tsrin, dim_t tscin, dim_t nrows, dim_t ncols)  {
  tsca = tscin - 1;
  tsra = tsrin - 1;

  tcols = (ncols-1) / tsca;			/* no. of (whole) tiles across */
  assert(tcols * tsca == ncols - 1);
  trows = (nrows-1) / tsra;			/* no. of (whole) tiles down */
  assert(trows * tsra == nrows - 1);

  T = tsca + tsra  - 1;
  R = T * tcols + tsra;

  NB = R * (trows + 1);			/* yes, we waste a little space... */
}

/* note: we are returning an int here, in clase dim_t is too small. need another type... */
/* mapping:
 * for each tile - left side (tsra rows), top (tsca-1) cols; 
 * end of row (tsra rows) */
template <class CST>
int
BoundaryMgr<CST>::getPos(dim_t i, dim_t j, int debug) const {
  int tnum_i = i / tsra;
  int tnum_j = j / tsca;
  int tt_i = i % tsra;
  int tt_j = j % tsca;
  int t = (tt_j ? tsra + tt_j - 1: tt_i);
  int pos = tnum_i * R + tnum_j * T + t;

#ifndef NDEBUG
  if(debug) {
	fprintf(stderr, "getPos:\n");
	fprintf(stderr, "  ts{r,c}a=%d,%d\n", tsra, tsca);
	fprintf(stderr, "  R=%d T=%d\n", R, T);
	fprintf(stderr, "  tnum=%d,%d\n", tnum_i, tnum_j);
	fprintf(stderr, "  tt=%d,%d\n", tt_i, tt_j);
	fprintf(stderr, "  t=%d\n", t);
  }
#endif

  return pos;
}

template <class CST>
void
BoundaryMgr<CST>::getIJ(int pos, dim_t *ip, dim_t *jp, int debug) const {
  int i, j;

  int tnum_i = pos / R;
  int rpos = (pos % R);
  int tnum_j = rpos / T;
  int tpos = rpos % T;
  if(tpos >= tsra) {
	i = 0;
	j = tpos - tsra + 1;
  } else {
	i = tpos;
	j = 0;
  }

#ifndef NDEBUG
 if(debug) {
	fprintf(stderr, "getIJ:\n");
	fprintf(stderr, "  ts{r,c}a=%d,%d\n", tsra, tsca);
	fprintf(stderr, "  R=%d T=%d\n", R, T);
	fprintf(stderr, "  tnum=%d,%d\n", tnum_i, tnum_j);
	fprintf(stderr, "  tt=%d,%d\n", i, j);
  }
#endif

  i += tnum_i * tsra;
  j += tnum_j * tsca;
  *ip = i;
  *jp = j;
}

template <class CST>
void
BoundaryMgr<CST>::selfcheck() const {
  dim_t vi, vj;

  fprintf(stderr, "boundaryMgr: selfcheck...\n");
  fprintf(stderr, "boundary rows,cols=%d,%d\n", trows, tcols);
  for(int p=0; p<NB; p++) {
	getIJ(p, &vi, &vj);
	int pos = getPos(vi, vj);
	//printf("BMGRC %d\t%d\n", vi, vj);
	if(p != pos) {
	  fprintf(stderr, "p=%d; pos=%d\n", p, pos);
	  fprintf(stderr, "vi,vj=%d,%d\n", vi, vj);
	  getIJ(p, &vi, &vj, 1);
	  getPos(vi, vj, 1);
	  assert(p == pos);
	}
  }
  fprintf(stderr, "boundaryMgr: selfcheck... OK\n");
}

/* ********************************************************************** */
