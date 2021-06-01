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


#ifndef CONFIG_H
#define CONFIG_H

#include "types.h"

extern struct g_t {
  int inited;  // must be first
  /* other globals follow */
  dimension_type ntiles;
} g;


/* do all these really need to be globals??? XXX-RW */
extern dimension_type nrows, ncols, nrowsPad, ncolsPad, tsr, tsc;

void readConfigFile (const char* fileName);
void writeConfigFile (const char* fileName);


#endif
