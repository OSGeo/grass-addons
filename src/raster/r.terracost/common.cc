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

#include <sys/types.h>
#include <sys/mman.h>
#include <ctype.h>

#include <ostream>
#include <iostream>
using namespace std;

#include "types.h"
#include "common.h"


/* globals */
statsRecorder *stats = NULL;
userOptions *opt = NULL;


const char *
resolvePath(const char *name) {
  static char buf[BUFSIZ];
  static char *vtmpdir = NULL;
  vtmpdir = getenv(VTMPDIR); 

  if(!vtmpdir){
    fprintf(stderr, "%s: environment not set\n", VTMPDIR);
    exit(1);
  }
  
  if(name[0] == '/') {		// absolute path
    strcpy(buf, name);
  } else {			// relative path - use VTMPDIR
    strcpy(buf, vtmpdir);
    int len = strlen(buf);
    // remove trailing slashes
    while(len > 0 && buf[len - 1] == '/') {
      buf[--len] = '\0';
    }
    strcat(buf, "/");
    strcat(buf, name);
  }

  return buf;
}
