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

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#include "config.h"


//struct  Cell_head *region = NULL; 
dimension_type nrows = 0;
dimension_type ncols = 0;
dimension_type ncolsPad = 0;
dimension_type nrowsPad = 0;
dimension_type tsr = 0;
dimension_type tsc = 0;

struct g_t g = { 0 };



void readConfigFile (const char* fileName) {
  FILE* fp;

  if(g.inited) { return; }

  fp = fopen(fileName, "r");
  if (!fp) {
    cout << "Cannot open config file: " << fileName << endl;;
    assert(0);
    exit(1);
  }

  char buf[20];
  fscanf(fp,"%s %hd", buf, &nrows);
  fscanf(fp,"%s %hd", buf, &ncols);
  fscanf(fp,"%s %hd", buf, &nrowsPad);
  fscanf(fp,"%s %hd", buf, &ncolsPad);
  fscanf(fp,"%s %hd", buf, &g.ntiles);
  fscanf(fp,"%s %hd", buf, &tsr);
  fscanf(fp,"%s %hd", buf, &tsc);
  fclose(fp);

  g.inited = 1;
}

void writeConfigFile (const char* fileName) {
  FILE* fp;

  cout << "writing config file " << fileName << endl;
  fp = fopen(fileName, "w");
  if (!fp) {
    cerr << "Cannot open config file: " << fileName << endl;;
    assert(0);
    exit(1);
  }

  fprintf(fp,"%s %hd ", "nrows",  nrows);
  fprintf(fp,"%s %hd ", "ncols",  ncols);
  fprintf(fp,"%s %hd ", "nrowsPad",  nrowsPad);
  fprintf(fp,"%s %hd ", "ncolsPad",  ncolsPad);
  fprintf(fp,"%s %hd ", "ntiles",  g.ntiles);
  fprintf(fp,"%s %hd ", "tsr",  tsr);
  fprintf(fp,"%s %hd ", "tsc",  tsc);
  fclose(fp);
}
