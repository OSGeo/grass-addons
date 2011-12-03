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

#ifndef COMMON_H
#define COMMON_H

#include <sys/types.h>
#include <iostream>

#include "stats.h"
#include "option.h"
#include "types.h"
#include "config.h"		/* for convenience */

extern "C" {
#include <grass/gis.h>
}

using namespace std;


//#define VTMPDIR "/var/tmp/" USER "/"
#ifndef USER
#define USER "user"
#endif

//#define VTMPDIR "/var/tmp/gis/" USER "/"
#define VTMPDIR "VTMPDIR"


extern statsRecorder *stats;     /* stats file */
extern userOptions *opt;          /* command-line options */



template<class T>
void
printStream(AMI_STREAM<T> *s) {
  T* elt;
  AMI_err ae;
  assert(s);
  ae = s->seek(0);
  assert(ae == AMI_ERROR_NO_ERROR);

  while ((ae = s->read_item(&elt)) == AMI_ERROR_NO_ERROR) {
    *stats << *elt << " ";
  }
  *stats << "\n";
  ae = s->seek(0);
  assert(ae == AMI_ERROR_NO_ERROR);
};



const char *resolvePath(const char *name);


#endif

