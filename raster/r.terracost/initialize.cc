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

/* The initialize module deals with the loading of a raster map from
   GRASS formatting and changing it into an AMI_STREAM and boundary
   structure to be used by the tile factory. */

#include "stats.h"
#include "formatNumber.h"
#include "initialize.h"

//#define DEBUG_LOADGRID

/* ---------------------------------------------------------------------- */
cost_type
loadCell (void *inrast, RASTER_MAP_TYPE data_type, int *isnull, 
	  dimension_type j) {
  FCELL f;
  DCELL d;
  CELL c;
  cost_type x;
  ijCost out;
  cost_type T_max_value = cost_type_max;
  cost_type T_min_value = -T_max_value;

  switch (data_type) {
  case CELL_TYPE:
    c = ((CELL *) inrast)[j];
    //cout << "C: " << c << ".\n";
    *isnull = G_is_c_null_value(&c);
    if (!(*isnull)) {
      x = (cost_type)c; d = (DCELL)c;
    }
    else x = NODATA;
    break;
  case FCELL_TYPE:
    f = ((FCELL *) inrast)[j];
    //cout << "F1: " << f << ".\n";
    *isnull = G_is_f_null_value(&f);
    //cout << "F2: " << f << ".\n";
    if (!(*isnull)) {
      x = (cost_type)f; d = (DCELL)f;
    }
    else x = NODATA;
    break;
  case DCELL_TYPE:
    d = ((DCELL *) inrast)[j];
    //cout << "D: " << d << ".\n";
    *isnull = G_is_d_null_value(&d);
    if (!(*isnull)) {		
      x = (cost_type)d;
    }
    else x = NODATA;
    break;
  default:
    G_fatal_error("raster type not implemented");
    x = NODATA;
    break;
  }

  if (d > (DCELL)T_max_value)
    G_fatal_error("value out of range.");
  
  return x;
  
}

/* ---------------------------------------------------------------------- */

int
checkSource (void *inrastSource, RASTER_MAP_TYPE data_type_source, 
	     dimension_type j) {
  FCELL f;
  DCELL d;
  CELL c;
  cost_type x;
  int isnull = 0;
  ijCost out;

  switch (data_type_source) {
  case CELL_TYPE:
    c = ((CELL *) inrastSource)[j];
    isnull = G_is_c_null_value(&c);
    if (isnull) return 0;
    break;
  case FCELL_TYPE:
    f = ((FCELL *) inrastSource)[j];
    isnull = G_is_f_null_value(&f);
    if (isnull) return 0;
    break;
  case DCELL_TYPE:
    d = ((DCELL *) inrastSource)[j];
    isnull = G_is_d_null_value(&d);
    if (isnull) return 0;
    break;
  default:
    G_fatal_error("raster type not implemented");		
  }
  return 1;

}

/* ---------------------------------------------------------------------- */
void 
loadGrid (char* cellname, char* sourcename, long* nodata_count, 
	  TileFactory *tf) {

  AMI_err ae;
  *nodata_count = 0;
  int isnull = 0;
  cost_type cost;
  char s;
  ijCostSource out;
  FCELL f;
  
  /* Find cost map raster file */
  const char *mapset;
  mapset = G_find_cell (cellname, "");
  if (mapset == NULL)
    G_fatal_error ("cell file [%s] not found", cellname);

  int infd;
  if ( (infd = G_open_cell_old (cellname, mapset)) < 0)
    G_fatal_error ("Cannot open cell file [%s]", cellname);
  
  //Added by tom hazel 7 July 2004
  /* Find source map raster file */
  const char *mapsetSource;
  mapsetSource = G_find_cell (sourcename, "");
  if (mapsetSource == NULL)
    G_fatal_error ("cell file [%s] not found", sourcename);

  //Added by tom hazel 7 July 2004
  int infdSource;
  if ( (infdSource = G_open_cell_old (sourcename, mapsetSource)) < 0)
    G_fatal_error ("Cannot open cell file [%s]", sourcename);


  /* determine map type (CELL/FCELL/DCELL) */
  RASTER_MAP_TYPE data_type;
  data_type = G_raster_map_type(cellname, mapset);

  RASTER_MAP_TYPE data_type_source;
  data_type_source = G_raster_map_type(sourcename, mapsetSource);
  
  /* Allocate input buffer */
  void *inrast;
  inrast = G_allocate_raster_buf(data_type);

  void *inrastSource;
  inrastSource = G_allocate_raster_buf(data_type_source);

#ifdef DEBUG_LOADGRID
  AMI_STREAM<ijCostSource>* debugstr;
  debugstr = new AMI_STREAM<ijCostSource>();
#endif
  for (dimension_type i = 0; i< nrows; i++) {
	
    /* read input map */
    if (G_get_raster_row (infd, inrast, i, data_type) < 0)
      G_fatal_error ("Could not read from <%s>, row=%d",cellname,i);

    /* read source map */
    if (G_get_raster_row (infdSource, inrastSource, i, data_type_source) < 0)
      G_fatal_error ("Could not read from <%s>, row=%d",sourcename,i);
  
    for (dimension_type j=0; j<ncols; j++) {

      /* the cost of point i,j is read from the raster file 
	 if i,j is null, isnull=1 else isnull=0 */
      cost = loadCell(inrast, data_type, &isnull, j);

	  if  (cost < 0 && cost != NODATA) {
		printf("reading  (i=%d,j=%d) value=%.1f\n", i, j, cost);  
		printf("Negative cost detected. This algorithm requires all non-netative costs\n"); 
		fflush(stdout);
		exit(1);
	  }

      if (isnull > 0) {
	cost = NODATA;
	(*nodata_count)++;
	//cout << "No Data at: (" << i << "," << j << ")\n";
	//cout.flush();
      }


      /* If point i,j is a source s=1 else s=0 */
      s = checkSource(inrastSource, data_type_source, j);

#ifdef PRINT_SOURCES
      if (s) {
	*stats << "loadGrid:: Source found at (" << i << "," << j << ")\n";
      }
#endif
      
	  // why is there a cast on the following line? -RW
      costSourceType tempCST = costSourceType((cost_type)cost, s? 'y':'n');


      /* out is the ijCostType to be written to the grid in tf */
      out = ijCostSource(i, j, tempCST);

      tf->insert(out);
	  
#ifdef DEBUG_LOADGRID
      ae = debugstr->write_item(out);
      assert(ae == AMI_ERROR_NO_ERROR); 	  
#endif
    } /* for j */
	
    if (opt->verbose) G_percent(i, nrows, 2);
  }/* for i */
  
  if (opt->verbose)  fprintf(stderr, "\n");
  /* delete buffers */
  G_free(inrast);
  /* close map files */
  G_close_cell (infd);

  //cout << "rows: " << nrows << " cols: " << ncols 
  //<< endl;cout.flush();
  
  //assert(nrows * ncols == tf->getTotalPoints());

  *stats << "loadGrid:: Number of null points: " << formatNumber(NULL, *nodata_count) << "\n";
  
  //rt_stop(rt);
  //stats->recordTime("reading cell file", rt);

#ifdef DEBUG_LOADGRID
  bnd->testBoundary(debugstr); 
#endif


}
/* ---------------------------------------------------------------------- */

// how does this differ from loadGrid?? -RW

void loadNormalGrid(char* cellname, char* sourcename, long* nodata_count, 
		    cost_type** costGrid, cost_type** distGrid, 
		    pqheap_ijCost *pq) {

  AMI_err ae;
  *nodata_count = 0;
  int isnull = 0;
  cost_type cost;
  char s;
  ijCostSource out;
  FCELL f;
  costStructure costStruct;
  
  /* Find cost map raster file */
  const char *mapset;
  mapset = G_find_cell (cellname, "");
  if (mapset == NULL)
    G_fatal_error ("cell file [%s] not found", cellname);

  int infd;
  if ( (infd = G_open_cell_old (cellname, mapset)) < 0)
    G_fatal_error ("Cannot open cell file [%s]", cellname);
  
  //Added by tom hazel 7 July 2004
  /* Find source map raster file */
  const char *mapsetSource;
  mapsetSource = G_find_cell (sourcename, "");
  if (mapsetSource == NULL)
    G_fatal_error ("cell file [%s] not found", sourcename);

  //Added by tom hazel 7 July 2004
  int infdSource;
  if ( (infdSource = G_open_cell_old (sourcename, mapsetSource)) < 0)
    G_fatal_error ("Cannot open cell file [%s]", sourcename);


  /* determine map type (CELL/FCELL/DCELL) */
  RASTER_MAP_TYPE data_type;
  data_type = G_raster_map_type(cellname, mapset);

  RASTER_MAP_TYPE data_type_source;
  data_type_source = G_raster_map_type(sourcename, mapsetSource);
  
  /* Allocate input buffer */
  void *inrast;
  inrast = G_allocate_raster_buf(data_type);

  void *inrastSource;
  inrastSource = G_allocate_raster_buf(data_type_source);

  for (dimension_type i = 0; i< nrows; i++) {
	
    /* read input map */
    if (G_get_raster_row (infd, inrast, i, data_type) < 0)
      G_fatal_error ("Could not read from <%s>, row=%d",cellname,i);

    /* read source map */
    if (G_get_raster_row (infdSource, inrastSource, i, data_type_source) < 0)
      G_fatal_error ("Could not read from <%s>, row=%d",sourcename,i);
  
    for (dimension_type j=0; j<ncols; j++) {

      distGrid[i][j] = cost_type_max;


      /* the cost of point i,j is read from the raster file 
	 if i,j is null, isnull=1 else isnull=0 */
      cost = loadCell(inrast, data_type, &isnull, j);

      if (isnull > 0) {
	cost = NODATA;
	(*nodata_count)++;
	distGrid[i][j] = NODATA;
      }


      /* If point i,j is a source s=1 else s=0 */
      s = checkSource(inrastSource, data_type_source, j);

      if (s) {
	costStruct = costStructure(0,i,j);
	pq->insert(costStruct);

	/* costGrid[i][j] = 0; setting the cost of the sources to be
	   zero is causing the neighbors of the sources to get "half"
	   weights.
	*/
	costGrid[i][j] = cost; 
	distGrid[i][j] = 0;
      }

      else {
	costGrid[i][j] = cost;
      }
      
    } /* for j */
	
    if (opt->verbose) G_percent(i, nrows, 2);
  }/* for i */
  
  if (opt->verbose)  fprintf(stderr, "\n");
  /* delete buffers */
  G_free(inrast);
  /* close map files */
  G_close_cell (infd);
  
  *stats << "loadGrid:: Number of null points: " << *nodata_count << "\n";
  


}
