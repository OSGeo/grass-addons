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
 * sort boundary stream
 *
 * rajiv wickremesinghe 2005
 */

#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

#include <grass/iostream/ami.h>

#include "input.h"
#include "config.h"
#include "sortutils.h"

void
usage() {
  fprintf(stderr, "boudarySort [options]\n"
		  "-h   this help"
		  "-i   input boundary stream"
		  "-o   output sorted stream (defaults to same as -i"
		  "-c   config file name");
		  
}

int
main(int argc, char **argv) {
  char *stream_name=NULL;
  char *config_file=NULL;
  char *sorted_name=NULL;
  AMI_STREAM< ijCostType<costSourceType> > *bndstr;
  int ch;

  while ((ch = getopt(argc, argv, "ho:i:c:")) != -1) {
    switch (ch) {
    case 'i':
	  stream_name = strdup(optarg);
      break;
	case 'o':
 	  sorted_name = strdup(optarg);
	  break;
    case 'c':
      config_file = strdup(optarg);
      break;
	case 'h':
	default:
	  usage();
	  exit(0);
    }
  }

  if(!config_file || !stream_name) {
	usage();
	exit(1);
  }
  if(! sorted_name) {
	sorted_name = stream_name;
  }

  readConfigFile(config_file);
  stats = new statsRecorder("stats.out");

  bndstr = new AMI_STREAM< ijCostType<costSourceType> >(stream_name);
  assert(bndstr);
  bndstr->persist(PERSIST_PERSISTENT);

  MinIOCostCompareType<costSourceType> sortFun = MinIOCostCompareType<costSourceType>();
  sortFun.setTileSize(tsr, tsc);

  sort(&bndstr, sortFun);

  const char *new_name = bndstr->name();
  if(strcmp(new_name, sorted_name) == 0) {
	fprintf(stderr, "output in %s\n", sorted_name);
	goto done;
  }
  fprintf(stderr, "trying to rename %s to %s\n", new_name, sorted_name);

  // try to rename
  if(rename(new_name, sorted_name) == 0) { // success
	fprintf(stderr, "output renamed to %s\n", sorted_name);
	goto done;
  }
  perror("rename failed");

  // rename failed; copy the file
  {
	fprintf(stderr, "trying to copy\n");
	char buf[BUFSIZ];
	sprintf(buf, "/bin/cp \"%s\" \"%s\"", new_name, sorted_name);
	int status = system(buf);
	if(WIFEXITED(status)) {
	  if(WEXITSTATUS(status) == 0) {
		fprintf(stderr, "output copied to %s\n", sorted_name);
		goto done;
	  }
	}
  }
  
  fprintf(stderr, "boundarySort: Failed!!!\n");
  exit(1);

 done:
  return 0;
}
