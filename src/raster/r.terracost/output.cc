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


#include "output.h"

#define UNREACHABLE_VALUE 99999999


int isUnreachable(float dist) {
  //if (dist == cost_type_max) return 1; 
  if ((cost_type_max -dist) < 1000) return 1; 
  return 0;
}


/*
void 
mergeStream(AMI_STREAM<ijCost> *instr, BoundaryType<cost_type> *inbnd, 
	    AMI_STREAM<ijCost> *outstr) {
  
  //cout << "In Merge\n";cout.flush();

  AMI_err ae;
  ijCostType *point = &ijCostType();
  
  int count = 0;
  cout << "Post Decs\n";cout.flush();
  for (int i = 0; i<nrowsPad;i++) {
    for (int j = 0; j<ncolsPad;j++) {
      if (inbnd->isBoundary(i,j)) {
	inbnd->get(i,j,point);
      }
      else {
	ae = instr->read_item(&point);
	assert (ae == AMI_ERROR_NO_ERROR || ae == AMI_ERROR_END_OF_STREAM);
      }
      ae = outstr->write_item(*point);
      assert (ae == AMI_ERROR_NO_ERROR);
      if (ae == AMI_ERROR_NO_ERROR)
	count++;
    }
  }

  cout << "Num Merges: " << count << "\n"; cout.flush();
  }*/


/* This is a method which takes a 2D array as input and outputs a
GRASS rasted file. IT also takes the number of rows and cols and a
file name as input*/
void 
grid2Grass(cost_type ** grid, dimension_type rows, dimension_type cols,
	   char* cellname) { 
  assert(grid && cellname);


  int outfd;
  if ( (outfd = G_open_raster_new (cellname, FCELL_TYPE)) < 0) {
    G_fatal_error ("Could not open <%s>", cellname);
  }
  
  cout << "Opened raster file " << cellname << " for writing.\n";cout.flush();

  /* Allocate output buffer */
  unsigned char *outrast;
  outrast = (unsigned char *)G_allocate_raster_buf(FCELL_TYPE);
  assert(outrast);


  for (int i=0; i< rows; i++) {
    for (int j=0; j< cols; j++) {

      /* WRITE VALUE */
      if (grid[i][j] == NODATA || grid[i][j] == cost_type_max) {
		G_set_f_null_value( &( ((FCELL *) outrast)[j]), 1);
      } else { 
		((FCELL *) outrast)[j] = (FCELL)(grid[i][j]);
		//cout << "(" << i << "," << j << "): " << grid[i][j] << "\n";
      }
	  
      
    } /* for j*/
    if (G_put_raster_row (outfd, outrast, FCELL_TYPE) < 0) {
      G_fatal_error ("Cannot write to <%s>",cellname);
    }
  }/* for i */
  
  fprintf(stderr, "\n");

  G_free(outrast);
  G_close_cell (outfd);
  return;
}





void 
stream2ascii(AMI_STREAM<ijCost> *instr, BoundaryType<cost_type> *inbnd, 
			 const char* fname) {
  
  cout << "stream2ascii: start\n";cout.flush();
  assert(instr && inbnd && fname);
  
  FILE* fp = fopen(fname, "w"); 
  if (!fp) {
	fprintf(stderr, "cannot open file %s\n", fname); 
	exit(1); 
  }
  cout << "writing grid ascii file " << fname << endl;cout.flush();

  //write header
  fprintf(fp, "rows: %d\n", nrows); 
  fprintf(fp, "cols: %d\n", ncols); 
  fprintf(fp, "nodata: %d\n", NODATA);

  AMI_err ae; 
  ijCost *elt, temp;
  cost_type eltVal;

  ae = instr->seek(0);
  assert(ae == AMI_ERROR_NO_ERROR || ae == AMI_ERROR_END_OF_STREAM);
  
  int readNewItem = 1;
  for (int i=0; i< nrows; i++) {
    for (int j=0; j< ncols; j++) {
	  
	  //get value
      if (inbnd->isBoundary(i,j)) {
	//boundary
	inbnd->get(i, j, &temp);
	eltVal = temp.getCost();
	assert(temp.getI() == i && temp.getJ() == j);
      }
      else { 
	//internal point
	if (readNewItem) {
	  ae = instr->read_item(&elt);
	  assert(ae == AMI_ERROR_NO_ERROR || ae == AMI_ERROR_END_OF_STREAM);
	}
	if(ae == AMI_ERROR_NO_ERROR && elt->getI() == i && elt->getJ() == j) {
	  eltVal = elt->getCost();
	  readNewItem = 1;
	} else {
	  //fill in value with NODATA
	  readNewItem = 0;
	  eltVal = NODATA;
	}
      }
	//the value is not noData, but it can be unreachable, if its
	//cost value is equal to the initial value (infinity, in this
	//case cost_type_max; in this case set it to some smaller
	//LARGE value
	if (isUnreachable(eltVal)) {
	  eltVal = UNREACHABLE_VALUE;
	}
	assert(eltVal <= UNREACHABLE_VALUE); 

      /* WRITE VALUE */
      fprintf(fp, "%.1f ", eltVal); 
      
    } /* for j*/
    fprintf(fp, "\n"); 
	
	G_percent(i, nrows, 2);
  }/* for i */
  
  fclose(fp); 
  instr->seek(0);
  cout << "stream2ascii: done...\n"; cout.flush();
  return;
}




void
writeToGrassFile(AMI_STREAM<ijCost> *instr, BoundaryType<cost_type> *inbnd) {
  
  cout << "writeToGrassFile: start\n";cout.flush();
  
  //stolen from grass2str.h
  char* cellname = opt->out_grid;
  //cout << "Copied filename\n";cout.flush();

  AMI_err ae; 
  printCost fmp = printCost(); 
  //cout << "Initialized fmt\n";cout.flush();
  
  assert(instr && cellname);

  //cout << "stats writen\n";cout.flush();

  /* open output cell file */
  int outfd;
  if ( (outfd = G_open_raster_new (cellname, FCELL_TYPE)) < 0) {
    G_fatal_error ("Could not open <%s>", cellname);
  }
  
  cout << "Opened raster file " << cellname << " for writing\n";cout.flush();

  /* Allocate output buffer */
  unsigned char *outrast;
  outrast = (unsigned char *)G_allocate_raster_buf(FCELL_TYPE);
  assert(outrast);
  
  ijCost *elt, temp;
  ae = instr->seek(0);
  assert(ae == AMI_ERROR_NO_ERROR || ae == AMI_ERROR_END_OF_STREAM);
  int countWrites = 0, countNulls = 0, fillIn=0, countUnreachables=0;
  cost_type eltVal;

  int readNewItem = 1;
  for (int i=0; i< nrows; i++) {
    for (int j=0; j< ncols; j++) {
      //*stats << "(" << i << "," << j << ")" << endl;
	 	  
      //boundary
      if (inbnd->isBoundary(i,j)) {
		inbnd->get(i, j, &temp);
		eltVal = temp.getCost();
		assert(temp.getI() == i && temp.getJ() == j);
      }
      else { //internal point
	if (readNewItem) {
	  //cout << "writeToGrassFile::Reading New Item" << endl;
	  ae = instr->read_item(&elt);
	  assert(ae == AMI_ERROR_NO_ERROR || ae == AMI_ERROR_END_OF_STREAM);
	  //eltVal = elt->getCost();
	}
	if(ae == AMI_ERROR_NO_ERROR && elt->getI() == i && elt->getJ() == j) {
	  eltVal = elt->getCost();
	  readNewItem = 1;
	} else {
	  //fill in value with NODATA
	  readNewItem = 0;
	  eltVal = NODATA;
	  fillIn++;
	}
      }
      
      
      /* WRITE VALUE */
      if (eltVal == NODATA) {
	G_set_f_null_value( &( ((FCELL *) outrast)[j]), 1);
	countNulls++;
      } else {
	//the value is not noData, but it can be unreachable, if its
	//cost value is equal to the initial value (infinity, in this
	//case cost_type_max; in this case set it to some smaller
	//LARGE value
	if (isUnreachable(eltVal)) {
	  eltVal = UNREACHABLE_VALUE;
	  countUnreachables++;
	}
	assert(eltVal <= UNREACHABLE_VALUE); 
	
	((FCELL *) outrast)[j] = (FCELL)(eltVal);
	countWrites++;
      }
      
      
    } /* for j*/
    if (G_put_raster_row (outfd, outrast, FCELL_TYPE) < 0) {
      G_fatal_error ("Cannot write to <%s>",cellname);
    }
    
    G_percent(i, nrows, 2);
  }/* for i */
  
  cout << "Good writes: " << countWrites << "\n";
  cout << "Null (NODATA) writes: " << countNulls << "\n";
  cout << "Fillin null writes: " << fillIn << "\n";
  cout << "Unreachable writes: "  << countUnreachables << "\n";
  if (countUnreachables> 0) 
	cout << "Unreachable distance set to " << UNREACHABLE_VALUE << endl;
  cout.flush();

  G_free(outrast);
  G_close_cell (outfd);

  //rt_stop(rt);
  //stats->recordTime("writing cell file", rt);
  //cout << "After the nested for loops\n";cout.flush();
  instr->seek(0);
  cout << "writeToGrassFile: done\n"; cout.flush();
  return;
}
