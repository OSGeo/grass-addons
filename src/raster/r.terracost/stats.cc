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



#include <fcntl.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <stdio.h>
#include <errno.h>

#include "stats.h"
#include "formatNumber.h"


#ifdef HAS_UTRACE

struct ut { char buf[8]; };

void utrace __P((void *, int));

#define UTRACE(s) \
         {struct ut u; strncpy(u.buf,s,8); utrace((void*)&u, sizeof u);}
#else /* !HAS_UTRACE */
#define UTRACE(s)
#endif /* HAS_UTRACE */

#undef UTRACE

#ifdef UTRACE_ENABLE
#define UTRACE(s) utrace(s)
#else
#define UTRACE(s)
#endif

void
utrace(const char *s) {
  void *p;
  int len = strlen(s);
  assert(len < 80);

  /* cerr << "UT " << len << endl; */
  p = malloc(0);
  /* assert(p); */
  free(p);
  p = malloc(len);
  /* assert(p); */
  free(p);
  
  for(int i=0; i<len; i++) {
	p = malloc(s[i]);
	/* assert(p); */
	free(p);
  }
}



int
noclobberFile(const char * fname) {
  int fd=-1;
  
  while(fd<0) {
    fd = open(fname, O_WRONLY|O_CREAT|O_EXCL, 0644);
    if(fd < 0) {
      if(errno != EEXIST) {
	perror(fname);
	exit(1);
      } else { /* file exists */
	char buf[BUFSIZ];
	fprintf(stderr, "file %s exists - renaming.\n", fname);
	sprintf(buf, "%s.old", fname);
	if(rename(fname, buf) != 0) {
	  perror(fname);
	  exit(1);
	}
      }
    }
  }
  return fd;
}

const char* 
noclobberFileName(const char *fname) {
  int fd;
  fd = open(fname, O_WRONLY|O_CREAT|O_EXCL, 0644);
  if(fd < 0) {
    if(errno != EEXIST) {
      perror(fname);
      exit(1);
    } else { /* file exists */
      char buf[BUFSIZ];
      fprintf(stderr, "file %s exists - renaming.\n", fname);
      sprintf(buf, "%s.old", fname);
      if(rename(fname, buf) != 0) {
	perror(fname);
	exit(1);
      }
      close(fd);
    }
  }
  return fname;
}



/* ********************************************************************** */

statsRecorder::statsRecorder(const char * fname) {
  //note: in the new version of gcc there is not constructor for
  //ofstream that takes an fd; wrote another noclobber() function that
  //closes fd and returns the name;

  // try to turn off buffering
  rdbuf()->pubsetbuf(0,0);

  open(noclobberFileName(fname));
  rt_start(tm);
  bss = sbrk(0);
  char buf[BUFSIZ];
  *this << freeMem(buf) << endl;
}

/* ********************************************************************** */

long 
statsRecorder::freeMem() {
  struct rlimit rlim;
  if (getrlimit(RLIMIT_DATA, &rlim) == -1) {
	perror("getrlimit: ");
	return -1;
  } 	
  /* printf("getrlimit returns: %d \n", rlim.rlim_cur); */
  if (rlim.rlim_cur == RLIM_INFINITY) {
	/* printf("rlim is infinity\n"); */
	/* should fix this */
	return -1; 
  } 
  long freeMem = rlim.rlim_cur - ((char*)sbrk(0)-(char*)bss);
  return freeMem;
}

char *
statsRecorder::freeMem(char *buf) {
  char buf2[BUFSIZ];
  sprintf(buf, "Free Memory=%s", formatNumber(buf2, freeMem()));
  return buf;
}



/* ********************************************************************** */

char *
statsRecorder::timestamp() {
  static char buf[BUFSIZ];
  rt_stop(tm);
  sprintf(buf, "[%.1f] ", rt_seconds(tm));
  return buf;
}

void 
statsRecorder::timestamp(const char *s) {
  *this << timestamp() << s << endl;
}


void 
statsRecorder::comment(const char *s, const int verbose) {
  *this << timestamp() << s << endl;
  if (verbose) {
    cout << s << endl;
  }
  UTRACE(s);
  cout.flush();
}


void 
statsRecorder::comment(const char *s1, const char *s2) {
  char buf[BUFSIZ];
  sprintf(buf, "%s%s", s1, s2);
  comment(buf);
}

void 
statsRecorder::comment(const int n) {
  char buf[BUFSIZ];
  sprintf(buf, "%d", n);
  comment(buf);
}



void
statsRecorder::recordTime(const char *label, long secs) {
  *this << timestamp() << "TIME " << label << ": " << secs << " secs" << endl;
  this->flush();

  UTRACE(label);
}

void
statsRecorder::recordTime(const char *label, Rtimer rt) {
  char buf[BUFSIZ];
  *this << timestamp() << "TIME " << label << ": ";
  *this << rt_sprint(buf, rt) << endl;
  this->flush();

  UTRACE(label);
}

void
statsRecorder::recordLength(const char *label, off_t len, int siz,
			    char *sname) {
  UTRACE(label);
  UTRACE(sname);
  
  char lenstr[100];
  char suffix[100]="";
  if(siz) {
	formatNumber(suffix, len*siz);
	strcat(suffix, " bytes");
  }
  formatNumber(lenstr, len);  
  *this << timestamp() << "LEN " << label << ": " << lenstr << " elts "
		<< suffix;
  if(sname) *this << " " << sname;
  *this << endl;
  this->flush();
}


