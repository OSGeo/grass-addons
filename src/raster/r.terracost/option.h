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

#ifndef option_h
#define option_h


#define RUN_NONE 0
#define RUN_S0  0x001
#define RUN_S1  0x002
#define RUN_S2  0x004
#define RUN_S3  0x008
#define RUN_S4  0x010
#define RUN_ALL (RUN_S0 | RUN_S1 | RUN_S2 | RUN_S3 | RUN_S4)



typedef struct {
  char* cost_grid;     /* name of input elevation grid */

  char* out_grid;   /* name of output filled elevation grid */

  char* source_grid; //name or source raster

  int   mem;           /* main memory, in MB */
  char* streamdir;     /* location of temposary STREAMs */
  char *vtmpdir;				/* location of intermediate streams */

  char* stats;         /* stats file */
  int verbose;         /* 1 if verbose, 0 otherwise */
  int ascii;           /* 1 if save output to ascii file */

  int runMode;			/* which step(s) to run */

  int numtiles;          /* number of tiles in the grid */
  char* s0out;         /* base name for step 1 output streams */
  //  char* s1in;
  int s1fd;	       /* file descriptor containing step 0 streams */
  char* s0bnd;
  char* s1out;
  char* s2bout;        /* base name for source to boundary output streams */
  char* config;        /* config file stores number of tiles, size of
			  tiles and total size of grid */
  char* phase2Bnd; //phase2Bnd

  double EW_fac, NS_fac, DIAG_fac, V_DIAG_fac, H_DIAG_fac;
  
  int tilesAreSorted;			/* before computing substitute graph; set if
								 * sort by tile order is not needed */

} userOptions;





#endif

