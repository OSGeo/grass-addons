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

/*
 * split stream into tiles
 *
 * rajiv wickremesinghe 2005
 */

#include <stdio.h>
#include <sys/types.h>
#include <sys/uio.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <assert.h>

#include <grass/iostream/ami.h>
#include "locator.h"
#include "input.h"
#include "config.h"
#include "queue.h"


static void
usage() {
  printf("usage: tileSplit [options]\n");
//   printf("  -n<arity>\n");
  printf("  -i<input> (default=stdin)\n");
  printf("  -o<outroot>\n");
  printf("  -c<config>\n");
}

#define BUFFER_SIZE (32<<10)

static int opencalls = 0;

void
file_name(char *buf, char *outroot, int id) {
  sprintf(buf, "%s-%04d", outroot, id);
}


int
open_file(char *outroot, int id, int truncate) {
  char buf[BUFSIZ];

  opencalls++;

  file_name(buf, outroot, id);
  int fd = open(buf, O_WRONLY | O_CREAT | (truncate?O_TRUNC:O_APPEND), 0666);
  if(fd < 0) {
	perror(buf);
	exit(1);
  }
  return fd;
}

typedef struct open_stream_t {
  int id;
  TAILQ_ENTRY(open_stream_t) link;
} open_stream_t;

TAILQ_HEAD(qhead, open_stream_t) qhead = TAILQ_HEAD_INITIALIZER(qhead);
#define QSIZ 200

void
qinit() {
  int i;
  for(i=0; i<QSIZ; i++) {
	open_stream_t *strm = (open_stream_t *)malloc(sizeof(open_stream_t));
	assert(strm);
	strm->id = -1;
	TAILQ_INSERT_TAIL(&qhead, strm, link);
  }
}

AMI_STREAM<ijCostSource> *
get_stream(AMI_STREAM<ijCostSource> **outstrms, char *outroot, int id) {
  int fd;
  static int inited = 0;

  if(!inited) {
	qinit();
  }
  inited = 1;

  if(!outstrms[id]) {			// must open
	open_stream_t *strm = TAILQ_FIRST(&qhead);
	if(strm->id >= 0) {			// clean head if needed
	  delete outstrms[strm->id];
	  outstrms[strm->id] = NULL;
	}
	TAILQ_REMOVE(&qhead, strm, link);
	strm->id = id;
	fd = open_file(outroot, id, 0);
	outstrms[id] = new AMI_STREAM<ijCostSource>(fd, AMI_APPEND_WRITE_STREAM);
	TAILQ_INSERT_TAIL(&qhead, strm, link);
  }
  return outstrms[id];
}


int
main(int argc, char **argv) {
  int fdin = STDIN_FILENO;
  char *path = NULL;
  int arity=0;
  int reclen;
  int off;
  AMI_STREAM<ijCostSource> **outstrms;
  char *config_file=NULL;
  char *outroot = NULL;
  int ch;
  int group = 1;

  while ((ch = getopt(argc, argv, "ho:i:c:g:n:")) != -1) {
    switch (ch) {
    case 'i':
      path = optarg;
      break;
    case 'o':
      outroot = strdup(optarg);
      break;
	case 'n':
	  arity = atoi(optarg);
	  break;
	case 'g':
	  group = atoi(optarg);
	  break;
    case 'c':
      config_file = strdup(optarg);
      break;
	case 'h':
	  usage();
	  exit(0);
    }
  }

  if(path) {
    fdin = open(path, O_RDONLY);
    if(fdin < 0) {
      perror(path);
      exit(1);
    }
  }

  if(!outroot || !config_file || group<1) {
    usage();
    exit(1);
  }

  readConfigFile(config_file);
  if(arity >= g.ntiles) {
	arity = g.ntiles;
	group = 1;
  } else if(arity) {
	// arity gets precedence
	group = (g.ntiles + arity - 1) / arity;	// roundup
  } else {
	assert(group > 0);
	arity = (g.ntiles + group - 1) / group; // roundup
  }

  off_t expectedSize = (off_t)(tsr-2) * (tsc-2) * sizeof(ijCostSource) * group;
  fprintf(stderr, "arity=%d\n", arity);
  fprintf(stderr, "sizeof(ijCostSource)=%d expected file size=%lld\n",
		  sizeof(ijCostSource), expectedSize);
  fprintf(stderr, "group=%d\n", group);

  reclen = sizeof(ijCostSource);
  assert(reclen < BUFFER_SIZE);

  outstrms = (AMI_STREAM<ijCostSource>**)malloc(sizeof(AMI_STREAM<ijCostSource>*) * arity);
  assert(outstrms);

  for(int i=0; i<arity; i++) {
	int fd = open_file(outroot, i, 1);
	close(fd);
    outstrms[i] = NULL;
  }

  IJClassifier ijcc(config_file);
  int nread = 0;
  int nwrite = 0;

  cerr << "Running split..." << endl;

  AMI_STREAM<ijCostSource> *strm = new AMI_STREAM<ijCostSource>(fdin, AMI_READ_STREAM);
  while(!strm->eof()) {
    ijCostSource *record;
    AMI_err ae;

    ae = strm->read_item(&record);
    if(ae == AMI_ERROR_END_OF_STREAM) {
      continue;
    }
    assert(ae == AMI_ERROR_NO_ERROR);
    nread++;

    off = ijcc.classify(record) % arity;
    //assert(off < arity);
    //assert(off >= 0);
    
    ae = get_stream(outstrms, outroot, off)->write_item(*record);
    assert(ae == AMI_ERROR_NO_ERROR);
    nwrite++;
  }

  for(int i=0; i<arity; i++) {
    //fprintf(stderr, "output [%d] length = %ld\n", i, (long)outstrms[i]->tell());
	char buf[BUFSIZ];
	file_name(buf, outroot, i);
	printf("%s\n", buf);
    if(outstrms[i]) {
	  delete outstrms[i];
	}
  }
#ifndef NDEBUG
  fprintf(stderr, "Checking file sizes...");
  for(int i=0; i<arity; i++) {
	char buf[BUFSIZ];
	file_name(buf, outroot, i);
	struct stat sb;
	if(stat(buf, &sb)) {
	  perror(buf);
	  exit(1);
	}
	if(sb.st_size != expectedSize) {
	  fprintf(stderr, "file size mismatch for %s\n", buf);
	  exit(1);
	}
  }
  fprintf(stderr, " done\n");
#endif
  free(outstrms);

  //fprintf(stderr, "%d records read; %d records written\n", nread, nwrite);
  assert(nread == nwrite);
  //fprintf(stderr, "input length = %ld\n", (long)strm->tell());
  
  fprintf(stderr, "open calls = %d\n", opencalls);

  return 0;
}
