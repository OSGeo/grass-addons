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


/*C
 * Original project: Lars Arge, Jeff Chase, Pat Halpin, Laura Toma, Dean
 *		     Urban, Jeff Vitter, Rajiv Wickremesinghe 1999
 * 
 * GRASS Implementation: Lars Arge, Helena Mitasova, Laura Toma 2002
 *
 * Copyright (c) 2002 Duke University -- Laura Toma 
 *
 * Copyright (c) 1999-2001 Duke University --
 * Laura Toma and Rajiv Wickremesinghe
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. All advertising materials mentioning features or use of this software
 *    must display the following acknowledgement:
 *      This product includes software developed by Duke University
 * 4. Neither the name of the University nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE TRUSTEES AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE TRUSTEES OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *C*/


#ifndef SORTUTILS_H
#define SORTUTILS_H

#include <sys/types.h>
#include <sys/stat.h>

#include <fstream>
using namespace std;

#include <grass/iostream/ami.h>
#include "common.h"


#define sort(A,B) ((*stats<< "sort at " << __FILE__ << ":" << __LINE__ << endl), _sort(A,B) )


/* ********************************************************************** */
/* deletes input stream *str and replaces it by the sorted stream */

template<class T, class FUN>
void
_sort(AMI_STREAM<T> **str, FUN fo) {
  //Rtimer rt;
  AMI_STREAM<T> *sortedStr;
  /*
  stats->recordLength("pre-sort", *str);
  rt_start(rt);
  */

  /* let AMI_sort create its output stream and delete the inout stream */
  int eraseInputStream = 1;
  AMI_sort(*str,&sortedStr, &fo, eraseInputStream);
  /*rt_stop(rt);

  stats->recordLength("sort", sortedStr);
  stats->recordTime("sort", rt);
  */

  sortedStr->seek(0);
  *str = sortedStr;

}





/* ********************************************************************** */

/* warning - creates a new stream and returns it !! */
template<class T, class FUN>
AMI_STREAM<T> *
_sort(AMI_STREAM<T> *strIn, FUN fo) {
  //Rtimer rt;
  AMI_STREAM<T> *strOut;
  /*
  stats->recordLength("pre-sort", strIn);
  rt_start(rt);
  */

  AMI_sort(strIn, &strOut, &fo);
  assert(strOut);
  /*
  rt_stop(rt);
  stats->recordLength("sort", strOut);
  stats->recordTime("sort", rt);
  */
  strOut->seek(0);
  return strOut;
}



/* ********************************************************************** */
/* deletes input stream *str and replaces it by the sorted stream */
template<class T, class FUN>
void
  cachedSort(AMI_STREAM<T> **str, FUN fo) {
  AMI_STREAM<T> *sortedStr;
  
  
  char *unsortedName = strdup((*str)->name());
  char sortedName[BUFSIZ];
  sprintf(sortedName, "%s.sorted", unsortedName);
  
  /* check if file exists */
  struct stat sb;
  if(stat(sortedName, &sb) == 0) {
    /* if file exists */
    sortedStr = new AMI_STREAM<T>(sortedName, AMI_READ_STREAM);
    /* now see if stream is right length */
    if(sortedStr->stream_len() == (*str)->stream_len()) {
      fprintf(stderr, "Guessing that %s is sorted version of %s (skipping sort)\n",
  	      sortedName, unsortedName);
      *stats << "Guessing that " << sortedName
  	     << " is sorted version of " << unsortedName << " (skipping sort)\n";
      delete *str;
      *str = sortedStr;
      return;
    }
  }
  
  /* not found; got to sort now */
  int eraseInputStream = 1;
  AMI_sort_withpath(*str, &sortedStr, &fo, eraseInputStream, sortedName);
  sortedStr->persist(PERSIST_PERSISTENT); /* might leave streams lying around... */
  fprintf(stderr, "Saving %s as sorted version of %s\n",sortedName, unsortedName);
  sortedStr->seek(0);
  *str = sortedStr;
  free(unsortedName);
}



#endif

