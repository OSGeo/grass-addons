/* ROWCACHE.H */

/* Part of the GRASS Toolkit (GT) functions collection */
/* Purpose:	provide a raster cache that retrieves rows from memory instead of disk, if possible. */
/*         	This should speed up operations where the same row has to be read more than once. */

/* Usage:	1. use GT_RC_open () to attach a row cache to any type of GRASS raster map */
/*		2. instead of G_get_raster_row (), use GT_RC_get to get a row of raster data from the cache */
/*		3. call GT_RC_done () instead of G_close () when done with raster operations */


/* This file is licensed under the GPL (version 2) */
/* see: http://www.gnu.org/copyleft/gpl.html */

/* (c) Benjamin Ducke 2004 */
/* benducke@compuserve.de */

#ifndef GT_ROWCACHE_H
#define GT_ROWCACHE_H

#include <grass/gis.h>

typedef struct
{
	long max;      /* nax index of row in cache */
	long allocated; /* number of rows currently in cache */
	int fd;     /* file descriptor: points to cached GRASS rast map */
	long worst; /* index of the row that has had the most cache misses */
	long region_rows; /* stores extent of current region for faster access */
	long region_cols;
	RASTER_MAP_TYPE data_type; /* CELL, DCELL or FCELL */
	CELL **c_cache_area; /* n pointers to a row of FCELL, DCELL or CELL data */
	DCELL **d_cache_area; /* n pointers to a row of FCELL, DCELL or CELL data */
	FCELL **f_cache_area; /* n pointers to a row of FCELL, DCELL or CELL data */
	long *misses; /* records the number of cache misses for each row */
	long *allocated_lookup; /* contains row numbers of all rows currently in cache */
	short int off;
} GT_Row_cache_t;

/* initialise row cache. */
/* n is the number of rows to keep in cache */
/* fd is the file to be cached */
/* 0 = success */
/* -1 = failure */
int GT_RC_open (GT_Row_cache_t *cache, long n, int fd, RASTER_MAP_TYPE data_type);

/* retreives a row from the cache */
void* GT_RC_get (GT_Row_cache_t *cache, long i);

/* closes cache, frees allocated memory */
void GT_RC_close (GT_Row_cache_t *cache);

#endif /* GT_ROWCACHE_H */
