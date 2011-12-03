
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


#include "dijkstra.h"
#include "dijkstraAbs.h"
#include "pq.h"
#include "formatNumber.h"

#define PQ_TIMER
#define UPDATE_TIMER

#define DEBUG if(0)
#define VERBOSE 0

//define this to print all the sources in the grid as they are
//encountered in tiles
// #define PRINT_SOURCES

void 
normalDijkstra(char* cellname, char* sourcename, long* nodata_count) {
  costStructure cs;
  cost_type cp;
  dimension_type pqI, pqJ;

  cost_type** costGrid;
  cost_type** distGrid;
  costGrid = new cost_type*[nrows];
  distGrid = new cost_type*[nrows];
  assert(costGrid);
  assert(distGrid);
  for (int i=0; i<nrows; i++) {
    costGrid[i] = new cost_type[ncols];
    distGrid[i] = new cost_type[ncols];
    assert(costGrid[i]);
    assert(distGrid[i]);
  }

  pqheap_ijCost *pq =  new pqheap_ijCost(nrows*ncols);

  loadNormalGrid (cellname, sourcename, nodata_count, costGrid, distGrid, pq);

  while (!pq->empty()) {
    pq->extract_min(&cs);
    pqI = cs.getI();
    pqJ = cs.getJ();
    cp = cs.getPriority();
    assert(cp >= 0);
    if (distGrid[pqI][pqJ] >= cp) {
      distGrid[pqI][pqJ] = cp;
      normalUpdateNeighbors(cs, pq, distGrid, costGrid);
    }
  }
  grid2Grass(distGrid, nrows, ncols, opt->out_grid);

  // cleanup
  for (int i=0; i<nrows; i++) {
    delete [] costGrid[i];
    delete [] distGrid[i];
  }
  delete [] costGrid;
  delete [] distGrid;
}


/* compute SP from each boundary point to ANY source point and writes
   the output distances to s2bstr

invariant: sourceDist is 0 for all sources and inf for the
   other points; all source points have been inserted in spq by
   boundaryTileDijkstra */
void
sourceTileDijkstra(const Tile *tile, AMI_STREAM<ijCost> *s2bstr, 
		   const TileFactory *tf, cost_type** dist, 
		   pqheap_ijCost *pq) {

  //DEBUG { cout << "sourceTileDijkstra::start" << endl; cout.flush(); }
#ifndef NO_STATS
  stats->comment("sourceTileDijkstra::start", VERBOSE);
#endif 
  costStructure sourceCS;
  dimension_type sourceI, sourceJ;
  dimension_type tileSizeRows, tileSizeCols, absI, absJ;
  cost_type sourcePrio;
  ijCostSource tempCT;

  tileSizeRows = tile->getNumRows();
  tileSizeCols = tile->getNumCols();

  // *stats << "sourceTileDijkstra: pq size = " << pq->size() << endl; // debug

  // print the sources; this should be taken out maybe
#ifdef PRINT_SOURCES
  if(!pq->empty()) {
    cout << "hello: sources at " << *pq << endl; 
  }
#endif

  while (!pq->empty()) {  
    pq->extract_min(&sourceCS);
    sourceI = sourceCS.getI();
    sourceJ = sourceCS.getJ();
    sourcePrio = sourceCS.getPriority();
    assert(sourcePrio >= 0);
    
    ((Tile *)tile)->s2bPQCount++; // debug
    
    if (dist[sourceI][sourceJ] >= sourcePrio) {
      if (tf->isBoundary(sourceI, sourceJ)) {
		tempCT = tile->getComplex(sourceI, sourceJ);
		absI = tempCT.getI();
		absJ = tempCT.getJ();
		writeToCostTypeStream(absI, absJ, sourcePrio, s2bstr);
		((Tile *)tile)->s2bWriteCount++; // debug
      }

      updateNeighbors(tile, sourceCS, pq, dist);
    }
  }
#ifndef NO_STATS
  //DEBUG { cerr << "sourceTileDijkstra::end" << endl; cerr.flush(); }
  stats->comment("sourceTileDijkstra::end", VERBOSE);
  //stats->recordTime("source tile dijkstra");
#endif
}





/* ---------------------------------------------------------------------- */
/* compute SP from all bnd vertices of the tile and writes the outputs
   to b2bstr; while scanning the tile it sets sourceDist of the points
   which are sources to 0 and inserts them in spq*/
int
boundaryTileDijkstra(Tile *tile, AMI_STREAM<distanceType> *b2bstr, 
		     const TileFactory *tf, cost_type** dist, 
		     pqheap_ijCost *spq,
		     cost_type** sourceDist) {
#ifndef NO_STATS
  //DEBUG { cerr << "boundaryTileDijkstra::start\n"; }
  stats->comment("boundaryTileDijkstra::start", VERBOSE);
#endif
  /* all these are inputs and must exist */
  assert(tile && b2bstr && tf && dist && spq && sourceDist);

  costStructure tempCS;
  dimension_type tileSizeRows = tf->getRows();
  dimension_type tileSizeCols = tf->getCols();


  //this pq is to be used for  sssp
  unsigned int heap_size_estimate = tileSizeRows * tileSizeCols;
  // JV: Removed the "/ 8"; to match standard Dijkstra.// xxx
  //  heap_size_estimate |= 256;
  // JV: Not necessary due to removing "/ 8".

  pqheap_ijCost *costpq =  new pqheap_ijCost(heap_size_estimate);
  //stats->comment("boundaryTileDijkstra::Created PQ in boundaryTileDijkstra()");
    
  size_t mma = MM_manager.memory_available();
  char memBuf[100];
#ifndef NO_STATS
  *stats << "boundaryTileDijkstra::Memory Available: " 
	 << formatNumber(memBuf, mma) << ".\n"; 
#endif
  int count = 1;
  int nullCount = 0;
  int numBnd = 0;
  int numNull = 0;              // number of (unseen) nulls
  int realNull = 0;
  int bndCount = 0;
  int bndShutoff = 0;
  int totalNumBnd = (tileSizeRows-1)*2 + (tileSizeCols-1)*2;
  int totalWrites = 0;
  int expectedWrites = totalNumBnd*totalNumBnd;
  int isNullPoint = 0;
  long extracts = 0;
  long updateCalls = 0;
  int sourceCount = 0;

  /* Need to compute the number of boundary points that are null in
     the tile */
  for (int l = 0, m = 0; l < tileSizeRows; l++) {
    if(tile->get(l,m).isNull())	// first col
      numNull++;
    if (tile->get(l,m+tileSizeCols-1).isNull())	// last col
      numNull++;
  }
  for (int l = 0, m = 1; m < tileSizeCols-1; m++) {
    if(tile->get(l,m).isNull())	// first row
      numNull++;
    if (tile->get(l+tileSizeRows-1,m).isNull())	// last row
      numNull++;
  }
#ifndef NO_STATS
  *stats << "  Num nulls on boundary: " << numNull << endl;
#endif

  for (int i = 0; i<tileSizeRows; i++) {
    for (int j = 0; j < tileSizeCols; j++) {

      if (tf->isBoundary(i,j)) {

#if 1
		numBnd++;				// reporting only
		assert(costpq->empty());
		if (tile->get(i,j).isNull()) {
		  realNull++;			// reporting only
		  numNull--;			// numNullRemaining? -RW
		  isNullPoint = 1;
		} else{
		  isNullPoint = 0;
		}
	
		totalNumBnd--;			// numBndRemaining? -RW
		bndShutoff = totalNumBnd - numNull; // =num of points to process? -RW
		dijkstraAbs(tile, i, j, costpq, dist, bndShutoff, &extracts, &updateCalls);

#else
		/* run dijkstra now */
		bndCount = 0;
		ijCostSource startPoint = tile->get(i,j);
		numBnd++;

		assert(costpq->empty());
		if (startPoint.isNull()) {
		  realNull++;
		  numNull--;			// numNullRemaining? -RW
		  isNullPoint = 1;
		  //continue; 
		} else{
		  assert(!startPoint.isNull());
		  isNullPoint = 0;
		  //initialize dist grid
		  for (int l=0; l<tileSizeRows; l++) {
			for (int m=0; m<tileSizeCols; m++) {
			  dist[l][m] = cost_type_max;
			}
		  }
		  dist[i][j] = 0;
		  costpq->insert(costStructure(0.0, i, j));	// start point
		}
	
		totalNumBnd--;			// numBndRemaining? -RW
		bndShutoff = totalNumBnd - numNull; // =num of points to process? -RW
	
		while (!costpq->empty() && bndCount <= bndShutoff) {
		  costpq->extract_min(&tempCS);
		  assert(tempCS.getPriority() >= 0);
		  extracts++;
		  if (dist[tempCS.getI()][tempCS.getJ()] >= tempCS.getPriority()) {
			updateCalls++;
			dist[tempCS.getI()][tempCS.getJ()] = tempCS.getPriority();
			updateNeighbors(tile, tempCS, costpq, dist);
			if (tf->isBoundary(tempCS.getI(),tempCS.getJ()) 
				&& tempCS.getI() >= i && tempCS.getJ() >=j) {
			  bndCount++;
			}
		  }
		} //	while (!costpq->empty())
		/* dijkstra done; save boundaries to stream */
#endif

		/*
		 * save the result to file. We only save 'forward' results;
		 * i.e. dist[i'][j'] where i'>=i and j'>=j -RW
		 */

		ijCostSource startPoint = tile->getComplex(i,j);

		/*  row 0 */
		if (i == 0) {
		  for (int l = 0, m = j; m <tileSizeCols; m++) {
			assert(tf->isBoundary(l, m));
			cost_type d = ((dist[l][m] < cost_type_max) && !isNullPoint)? 
			  dist[l][m]: NODATA; 
			totalWrites += doubleWriteToDistStream(startPoint, tile->getComplex(l,m),
												   d, b2bstr);
		  }
		}
		//column 0
		for (int l=i+(j==tileSizeCols-1?1:0),m = 0; l<tileSizeRows-1; l++) {
		  if (l == 0) continue; 
		  assert(tf->isBoundary(l, m));
		  cost_type d = ((dist[l][m] < cost_type_max) && !isNullPoint)? 
			dist[l][m]: NODATA; 
		  totalWrites += doubleWriteToDistStream(startPoint, tile->getComplex(l,m), 
												 d,b2bstr);
		}
		//column tilesizeCols-1
		for (int l = i, m = tileSizeCols-1; l < tileSizeRows-1; l++) {
		  if (l == 0) continue;
		  assert(tf->isBoundary(l, m));
		  cost_type d = ((dist[l][m] < cost_type_max) && !isNullPoint)? 
			dist[l][m]: NODATA; 
		  totalWrites += doubleWriteToDistStream(startPoint, tile->getComplex(l,m),
												 d,b2bstr);
		}
		//row tileSizeRoows-1
		for (int l = tileSizeRows-1, m = (i<(tileSizeRows-1)?0:j);
			 m < tileSizeCols; m++) {
		  assert(tf->isBoundary(l, m));
		  cost_type d = ((dist[l][m] < cost_type_max) && !isNullPoint)? 
			dist[l][m]: NODATA; 
		  totalWrites += doubleWriteToDistStream(startPoint, tile->getComplex(l,m),
												 d,b2bstr);
		}

		costpq->clear();  
      } //if  (tf->isBoundary(i,j))


      /* check for sources for next stage.
       * if the point is not a bnd vertex check if it is a source and
       * if so insert it in spq */
      if (tile->get(i,j).isSource()) {
		DEBUG { cerr << "Source found: " << tile->getComplex(i,j) << "\n";cerr.flush(); }
		spq->insert( costStructure(0.0, i, j));
		sourceDist[i][j] = 0;
		sourceCount++;
      }
    } //for j
  } //for i

#ifndef NO_STATS
  *stats << "  Total updates/extracts: " << updateCalls << "/" << extracts << endl;
  //cerr << "Total updates/extracts: " << updateCalls << "/" << extracts << endl;  
  *stats << "  Total Writes: " << totalWrites
		 << " Expected Writes: " << expectedWrites << endl;
  *stats << "  Non-Null Boundaries: " << numBnd-realNull << "\n";
  *stats << "  Estimated Nulls Left: " << numNull << "\n";
  *stats << "  Boundary inserts: " << count << "\n";
  *stats << "  Source count: " << sourceCount << "\n";
  stats->comment("BoundaryTileDijkstra:end", VERBOSE);
  stats->flush();
#endif
  delete costpq;
  return numBnd;
}




/* ---------------------------------------------------------------------- */
/*
    Run Dijkstra on each tile and compute bnd2bnd SP; these will be
  stored in b2bstr; also, for each point on the bnd of the tile,
  compute SP to any source point in the tile; store this in s2bstr.
    */
void 
computeSubstituteGraph(TileFactory* tf, AMI_STREAM<distanceType> *b2bstr, 
	    AMI_STREAM<ijCost> *s2bstr) {


  //DEBUG { cerr << "Compute Substitute graph..\n";cerr.flush(); }
  stats->comment("ComputeSubstitute graph", VERBOSE);
  size_t mma = MM_manager.memory_available();
  *stats << "ComputeSubstitute graph::Memory Available :" 
       << formatNumber(NULL, mma) << ".\n";

  assert(tf);
  assert(b2bstr);
  assert(s2bstr);

  dimension_type tileSizeRows = tf->getRows();
  dimension_type tileSizeCols = tf->getCols();
  AMI_err ae;

  Tile *tile = new Tile(tileSizeRows, tileSizeCols);
  assert(tile);
  tile->printStats(*stats);

  mma = MM_manager.memory_available();
  *stats << "ComputeSubstitute graph::Memory Available after TileFactory: " 
       << formatNumber(NULL, mma) << ".\n";

  /*
   * dist stores the current SP from a bnd vertex during Dijkstra
   */
  cost_type** dist; 
  dist = new cost_type*[tileSizeRows];
  assert(dist);
  for (int i=0; i<tileSizeRows; i++) {
    dist[i] = new cost_type[tileSizeCols];
    assert(dist[i]);
  }


   mma = MM_manager.memory_available();
  //formatNumber(NULL, mma);
//   DEBUG { cerr << "ComputeSubstitute graph::Memory Available after dist grid: " 
// 	       << memBuf << ".\n"; }
  *stats << "ComputeSubstitute graph::Memory Available after dist grid: " 
       << formatNumber(NULL, mma) << ".\n";

  /*
   * sourceDist stores the SP from a source vertex during Dijkstra
   */
  cost_type** sourceDist; 
  sourceDist = new cost_type*[tileSizeRows];
  assert(sourceDist);
  for (int i=0; i<tileSizeRows; i++) {
    sourceDist[i] = new cost_type[tileSizeCols];
    assert(sourceDist[i]);
  }

  mma = MM_manager.memory_available();
  //formatNumber(NULL, mma);
//   DEBUG{cerr<<"ComputeSubstitute graph::Memory Avail after sourcedist grid: " 
// 	     <<  memBuf << ".\n"; }
  *stats <<"ComputeSubstitute graph::Memory Available after sourcedist grid: " 
	 <<  formatNumber(NULL, mma) << ".\n";
  
  long spq_estimate = tileSizeRows * tileSizeCols; // * 8;
  // JV: Removed the "* 8"; to match standard Dijkstra.// xxx
  pqheap_ijCost *spq =  new pqheap_ijCost(spq_estimate);
  assert(spq);

  mma = MM_manager.memory_available();
  //formatNumber(memBuf, mma);
//   DEBUG { cerr << "ComputeSubstitute graph::Memory Available after PQ: " 
// 	       << memBuf << "\n"; }
  *stats << "ComputeSubstitute graph::Memory Available after PQ: " 
	 <<  formatNumber(NULL, mma) << "\n";

  *stats << "sizeof(costStructure) = " << sizeof(costStructure) << ".\n";
  //#ifndef NDEBUG
  int k = 1; /* For debugging only */
  //#endif
  int insertCount = 0;
  tf->reset();

  while (tf->getNextTile(tile)) {
#ifndef NO_STATS    
    *stats << "ComputeSubstitute graph::Working with tile " << k << "...\n";
#endif
#ifndef NDEBUG
    cerr << "ComputeSubstitute graph::Working with tile " << k << "...\n";
#endif

    /* set all points to inf; the sources will be set to 0 in
       boundaryTileDijkstra  */
    for (int i=0; i<tileSizeRows; i++) {
      for (int j = 0; j<tileSizeCols; j++) {
		sourceDist[i][j] = cost_type_max;
      }
    }
    
    insertCount += boundaryTileDijkstra(tile, b2bstr, tf, dist, spq, sourceDist);
    
    /* invariant: sourceDist is 0 for all sources and inf for the
       other points; all source points have been inserted in spq by
       boundaryTileDijkstra */
    sourceTileDijkstra(tile, s2bstr, tf, sourceDist, spq);
    
    //spq should be empty
    assert(spq->empty());
	//#ifndef NDEBUG
#ifndef NO_STATS
    stats->timestamp("ComputeSubstitute graph::");
    *stats << "Leaving tile " << k << ".\n";
#endif
    k++;

    //tile->dump();		// debug
	//#endif
  }
  
  delete tile;
  delete spq;
  for (int i=0; i<tileSizeRows; i++) {
    assert(dist[i] && sourceDist[i]);
    delete [] dist[i];
    delete [] sourceDist[i];
  }
  delete [] dist;
  delete [] sourceDist;

  //printGrid(*s2bstr);

  *stats << "computeSubstituteGraph::Total Boundaries: " << insertCount 
	<< endl;
  stats->recordLength("******b2bstr ", b2bstr);
  stats->recordLength("******s2bstr ", s2bstr);
  *stats << "ComputeSubstitute graph::done\n"; stats->flush();
  //stats->recordTime("computing substitute graph");
  //DEBUG { cerr << "ComputeSubstitute graph::done\n"; cerr.flush(); }
}


void
addNullBnds(const SettleLookup & settled, BoundaryType<cost_type> *phase2Bnd,
	    const TileFactory* tf) {
  ijCost nullBnd;
  dimension_type r = tf->getRows();
  dimension_type c = tf->getCols();

  cerr << "addNullBnds: start..." << endl;
  
  for (int i = 0, j = 0; i < r; i++) {
    if(settled.isSettled(i,j,tf) == 0) {
      nullBnd = ijCost(i,j,NODATA);
      phase2Bnd->insert(nullBnd);
    }
    if(settled.isSettled(i,j+r-1,tf) == 0) {
      nullBnd = ijCost(i,j,NODATA);
      phase2Bnd->insert(nullBnd);
    }
  }
  for (int i = 0, j = 1; j < c; j++) {
    if(settled.isSettled(i,j,tf) == 0) {
      nullBnd = ijCost(i,j,NODATA);
      phase2Bnd->insert(nullBnd);
    }
    if(settled.isSettled(i+r-1,j,tf) == 0) {
      nullBnd = ijCost(i,j,NODATA);
      phase2Bnd->insert(nullBnd);
    }
  }
}





/* ---------------------------------------------------------------------- */

void
interTileDijkstra(AMI_STREAM<ijCost> *s2bstr, 
		  AMI_STREAM<distanceType> *b2bstr, 
		  BoundaryType<cost_type> *phase2Bnd,
		  const TileFactory *tf) {
  
  cerr << "interTileDijkstra::start\n";
  assert(s2bstr && b2bstr && phase2Bnd && tf);

  size_t testMMAvailable = MM_manager.memory_available();
  cerr << "interTileDijkstra::avail memory: " << testMMAvailable << ".\n";
  
  int c = 0;

  SettleLookup settled(nrowsPad, ncolsPad, tf);
  
  AMI_err ae, ae1;
  ae = s2bstr->seek(0);
  cerr << "s2sstr len: " << s2bstr->stream_len() << endl;cerr.flush();
  
  EMPQueueAdaptive<costStructureOld, costPriorityOld> *itpq = 
    new EMPQueueAdaptive<costStructureOld, costPriorityOld>();
  /* initialize PQ: insert all distances from bnd vertices to a source
     in the pq */
  ijCost *ct;
  costStructureOld cs;
  assert(itpq);

  ae = s2bstr->read_item(&ct);
  while (ae != AMI_ERROR_END_OF_STREAM) {
    cs = costStructureOld(*ct);
    assert(cs.getPriority().getDist() != NODATA);
    itpq->insert(cs);
    ae = s2bstr->read_item(&ct);
    assert(ae == AMI_ERROR_NO_ERROR || ae == AMI_ERROR_END_OF_STREAM);
    c++;
  }

  //#define XXX fprintf(stderr, "reached %s:%d\n", __FILE__, __LINE__);
  dimension_type tI;
  dimension_type tJ;
  ijCost extractedPoint;
  int d = 0;
  while (!itpq->is_empty()) {
    itpq->extract_min(cs);
    //*stats << "Extraxting: " << cs << "\n"; stats->flush();
    tI = cs.getI();
    tJ = cs.getJ();
    /* We used points with i,j = -1 for padding*/
    costPriorityOld cp = cs.getPriority();
 
    //assert (cp.getDist() != NODATA  && tI != NODATA && tJ != NODATA);
    assert (cp.getDist() != NODATA  && tI != dim_undef && tJ != dim_undef);
    if (!settled.isSettled(tI, tJ, tf)) {
      updateInterNeighbors(cs, settled, itpq, b2bstr, tf, phase2Bnd);
      settled.settlePoint(tI, tJ, tf);
      extractedPoint = ijCost(tI, tJ, cp.getDist());
      
      assert(phase2Bnd);
      phase2Bnd->insert(extractedPoint);
      // *stats << "Settled: " << extractedPoint << "\n"; stats->flush();
      d++;
    }
    else {
      //extractedPoint = ijCost(tI, tJ, cp.getDist());
      //cerr << "already settled: " << extractedPoint << "\n";cerr.flush();
    }
  } //while (!itpq->is_empty())

  addNullBnds(settled, phase2Bnd, tf);

  
  cerr << "Total inserts: " << c << ".\n";
  cerr << "Total settles: " << d << ".\n";
  delete itpq;
  cerr << "interTileDijkstra::done\n";
}






/* ---------------------------------------------------------------------- */
void
finalDijkstra(TileFactory *tf, BoundaryType<cost_type> *phase2Bnd, 
	      AMI_STREAM<ijCost> *finalstr) {
  
  cerr << "finalDijkstra::start\n"; cerr .flush();
  assert(tf && phase2Bnd && finalstr);
  cerr << "Phase2Bnd Len: " << phase2Bnd->getSize() << endl; cerr.flush();
  
  dimension_type tileSizeRows, tileSizeCols, absI, absJ;
  Tile *tile;
  cost_type **finalDist;
  cost_type finalPrio;
  ijCostSource point, initCT, tempCT;
  costStructure finalCS;

  tileSizeRows = tf->getRows();
  tileSizeCols = tf->getCols();

  tile = new Tile(tileSizeRows, tileSizeCols);

  finalDist = new cost_type*[tileSizeRows];
  assert(finalDist);
  for (int i=0; i<tileSizeRows; i++) {
    finalDist[i] = new cost_type[tileSizeCols];
    assert(finalDist[i]);
  }


  unsigned int pqsize = tileSizeRows*tileSizeCols*2;  
  pqheap_ijCost *finalpq = new pqheap_ijCost(pqsize);

  int count = 1;		// this is not being used! XXX-RW
  ijCost tempijCost;

  tf->reset();
  while(tf->getNextTile(tile)) {
   
    // "Initializing finalDist tile
    for (int i = 0; i<tileSizeRows; i++) {
      for (int j = 0; j<tileSizeCols; j++) {
	initCT = tile->getComplex(i,j);
	if (initCT.getCost().isSource()) finalDist[i][j] = 0;
	else if (tf->isBoundary(initCT.getI(),initCT.getJ())) {
	  phase2Bnd->get(initCT.getI(),initCT.getJ(),&tempijCost);
	  finalDist[i][j] = tempijCost.getCost();
	} else finalDist[i][j] = cost_type_max;
      }
    } //for
    
    for (int i = 0; i < tileSizeRows; i++) {
      for (int j = 0; j < tileSizeCols; j++) {
	point = tile->getComplex(i,j);
	
	if (isNull(point.getCost())) {
	  /* We are checking the internal null points in output.cc,
	     but the boundary nulls are still being dealt with here */
	  if (tf->isBoundary(i,j)) {
	    phase2Bnd->insert(ijCost(point.getI(), point.getJ(),
				     point.getCost().getCost()));
	  }
	  /*
	    else {
	    writeToCostTypeStream(point.getI(), point.getJ(), 
	    point.getCost().getCost(), finalstr);
	    }
	  */
	  continue;
	}
	
	if (tf->isBoundary(i,j)) {
	  /* This is necessary because of the "Puerto Rico Problem"
	     where there could be unreachable points on the
	     boundary. These points will be inserted into the
	     phase2Bnd structure, as NODATA points, but should not be
	     inserted into the PQ */	  
	  if (finalDist[i][j] == NODATA)
	    continue;
	  finalpq->insert(costStructure(finalDist[i][j], i,j));
	}
	if (point.getCost().isSource()) {
#ifdef PRINT_SOURCES
	  *stats << "finalDijkstra::Source at (" << point 
		 <<", inserting it in PQ )\n";
#endif
	  finalpq->insert(costStructure(0.0, i,j));
	}
      }
    }
    
    

    while (!finalpq->empty()) {
      
      finalpq->extract_min(&finalCS);
      finalPrio = finalCS.getPriority();
      assert(finalPrio != NODATA);
      
      //assert(absI%tileSizeRows == finalI && absJ%tileSizeCols == finalJ);
      if (finalDist[finalCS.getI()][finalCS.getJ()] >= finalPrio && 	
	  !tf->isBoundary(finalCS.getI(),finalCS.getJ())){
	tempCT = tile->getComplex(finalCS.getI(),finalCS.getJ());
	absI = tempCT.getI();
	absJ = tempCT.getJ();
	writeToCostTypeStream(absI, absJ, finalPrio, finalstr);
      }
      
      updateNeighbors(tile, finalCS, finalpq, finalDist);
    }
    count ++;
    
  } //for each tile 
  
  
  cerr << "Stream length: " << finalstr->stream_len() << "\n";cerr.flush();
  cerr << "Boundary length: " << phase2Bnd->getSize() << "\n";cerr.flush();
  
  delete tile;
  for (int i=0; i<tileSizeRows; i++) {
    delete [] finalDist[i];
  }
  delete [] finalDist;
  delete finalpq;
}

/* ---------------------------------------------------------------------- */

int
doubleWriteToDistStream(const basicIJType& source, const basicIJType& dest, 
			cost_type dist, AMI_STREAM<distanceType> *b2bstr) {
  
  distanceType toWrite = distanceType(source, dest, dist);
  AMI_err ae = b2bstr->write_item(toWrite);
  assert(ae == AMI_ERROR_NO_ERROR);

  if (source != dest) {
    toWrite = distanceType(dest, source, dist);
    ae = b2bstr->write_item(toWrite);
    assert(ae == AMI_ERROR_NO_ERROR);
    return 2;
  }

  return 1;

}

/* ---------------------------------------------------------------------- */
void
writeToStreamWithDist(distanceType inDist,AMI_STREAM<distanceType> *b2bstr) {
  AMI_err ae = b2bstr->write_item(inDist);
  assert(ae == AMI_ERROR_NO_ERROR);
} 

/* ---------------------------------------------------------------------- */


void
writeToCostTypeStream(dimension_type i, dimension_type j, cost_type dist,
		      AMI_STREAM<ijCost> *str) {
  
  if ((cost_type_max - dist) < 1000) {
    //if it gets close to overflow 
    printf("warning: large cost at (%d, %d, %f)\n", i, j, dist);
  }
  
  /* This Doesn't work
  ijCost toStr = ijCost(i, j, dist);*/

  /* This does */
  ijCost toStr;
  toStr = ijCost(i, j, dist);

  AMI_err ae = str->write_item(toStr);
  assert(ae == AMI_ERROR_NO_ERROR);
}

/* ---------------------------------------------------------------------- */
