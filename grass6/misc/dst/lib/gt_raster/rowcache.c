/* ROWCACHE.C */

/* Part of the GRASS Toolkit (GT) functions collection */
/* Purpose:	provide a raster cache that retrieves rows from memory instead of disk, if possible. */
/*         	This should speed up operations where the same row has to be read more than once. */

/* This file is licensed under the GPL (version 2) */
/* see: http://www.gnu.org/copyleft/gpl.html */

/* (c) Benjamin Ducke 2004 */
/* benducke@compuserve.de */

#include <stdlib.h>
#include <stdio.h>

#include <grass/gis.h>
#include "gt/rowcache.h"


/* returns the slot number in the lookup table for a cached raster row */
/* should actually be a hash function instead of this */
/* return: lookup table index or -1 if row is not in cache */
long GT_RC_lookup_slot (GT_Row_cache_t *cache, long row) {
  int i = 0;
  for (i=0; i <= cache->max; i++) {
	  if (cache->allocated_lookup[i] == row) {
		  return (i);
	  }
  }
  /* raster row not currently cached */
  return (-1);
}	

void GT_RC_update_worst (GT_Row_cache_t *cache, long hit) {
	int i = 0;
	int most_misses = 0;
	
	cache->worst=cache->allocated_lookup[0];
	/* the following loops act on every slot except 'hit' */
	/* which is the only one that does not get its misses increased */	
	for ( i = 0; i <= cache->max; i++) {
		if (cache->allocated_lookup[i] != hit) {
			if (cache->data_type == CELL_TYPE) {
				if ((cache->c_cache_area[cache->allocated_lookup[i]] != NULL) &&
					(cache->allocated_lookup[i] > -1))
		    	{
			  		cache->misses[cache->allocated_lookup[i]]++;
			  		if (cache->misses[cache->allocated_lookup[i]] > most_misses) {
						most_misses = cache->misses[cache->allocated_lookup[i]];
						cache->worst = cache->allocated_lookup[i];
			  		}	
		    	}			
		  	}			
			if (cache->data_type == DCELL_TYPE) {
				if ((cache->d_cache_area[cache->allocated_lookup[i]] != NULL) &&
					(cache->allocated_lookup[i] > -1))
		    	{
			  		cache->misses[cache->allocated_lookup[i]]++;
			  		if (cache->misses[cache->allocated_lookup[i]] > most_misses) {
						most_misses = cache->misses[cache->allocated_lookup[i]];
						cache->worst = cache->allocated_lookup[i];
			  		}	
		    	}			
		  	}			
			if (cache->data_type == FCELL_TYPE) {
				if ((cache->f_cache_area[cache->allocated_lookup[i]] != NULL) &&
					(cache->allocated_lookup[i] > -1))
		    	{
			  		cache->misses[cache->allocated_lookup[i]]++;
			  		if (cache->misses[cache->allocated_lookup[i]] > most_misses) {
						most_misses = cache->misses[cache->allocated_lookup[i]];
						cache->worst = cache->allocated_lookup[i];
			  		}	
		    	}			
		  	}
		}
	}
}

long GT_RC_find_worst (GT_Row_cache_t *cache) {
	return (cache->worst);
}


/* tries to allocate a block of n cache rows */
/* no memory is actually allocated! This function */
/* frees all allocated memory before exiting */
/* returns n (same value), if enough mem is present, -1 otherwise */
int GT_RC_try_alloc (long n, RASTER_MAP_TYPE data_type ) {
	
	void *try;
	
	if ( data_type == CELL_TYPE ) {
		try = calloc ((unsigned long) n, sizeof (CELL*));
		if (try == NULL) {
			return (-1);
		} else {
			free (try);
		}
	}
	if ( data_type == FCELL_TYPE ) {
		try = calloc ((unsigned long) n, sizeof (FCELL*));
		if (try == NULL) {
			return (-1);
		} else {
			free (try);
		}
	}
	if ( data_type == DCELL_TYPE ) {
		try = calloc ((unsigned long)n, sizeof (DCELL*));
		if (try == NULL) {
			return (-1);
		} else {
			free (try);
		}
	}	
	return (0);
}

/* open a new row cache on a GRASS rast map */
/* n = number of raster rows to store in cache */
/* fd = file descriptor to associate with cache */
/* NOTE: fd must NOT be closed by caller, it will be closed automatically */
/*		  by GT_RC_close() */
/* RASTER_MAP_TYPE may be CELL, DCELL or FCELL */
int GT_RC_open (GT_Row_cache_t *cache, long n, int fd, RASTER_MAP_TYPE data_type) {
	long i;
	long rows;
	
	/* turn cache on by defult */
	cache->off = 0;
	
	/* 1: see if user requested a certain size and if we have that much mem */	
	if ( n == 0 ) {
		G_warning ("Cache has been turned off by user request.\n");
		cache->off = 1;
		n = 1; /* even a cache that was turned off needs to store one row */
	}
	
	if ( n > 0 ) {
		if ( GT_RC_try_alloc (n, data_type) == -1) {
			G_warning ("Requested cache size cannot be allocated.\n");
			/* set to auto mode */
			n = -1;
		}
	}
	/* 2: else: fall back to auto mode, try 20% of total rows, than 10%, than 5% */
	if ( n == -1 ) {		
		/* try 20 percent first */
		n = (G_window_rows()/100) * 20;
		if ( GT_RC_try_alloc (n, data_type) == -1) {
			n = (G_window_rows() / 100) * 10;
			if ( GT_RC_try_alloc (n, data_type) == -1) {
				n = (G_window_rows() / 100) * 5;
				if ( GT_RC_try_alloc (n, data_type) == -1) {
					/* it's no longer any use: just turn off the cache! */
					G_warning ("Insufficient memory for cache: turned off.\n");
					cache->off = 1;
					n = 1;
				}
			}
		}		
	}	
	
	cache->max = n-1;
	cache->allocated = 0;
	cache->fd = fd;
	cache->worst = 0;
	cache->region_rows = G_window_rows(); /* store these values for faster access */
	cache->region_cols = G_window_cols(); /* store these values for faster access */
	cache->data_type = data_type;
	
	rows = G_window_rows ();
		
	cache->misses = G_calloc (rows, sizeof(long));	
	for (i=0; i<rows;i++) {
		cache->misses[i] = 0;
	}
	/* allocate pointers according to type of raster */
	if (data_type == CELL_TYPE) {
		cache->c_cache_area = G_calloc (rows,sizeof (CELL*));
    	for (i = 0; i<n; i++) {
	  	cache->c_cache_area[i] = NULL;	
    	}
	}
	if (data_type == DCELL_TYPE) {
		cache->d_cache_area = G_calloc (rows,sizeof (DCELL*));
    	for (i = 0; i<n; i++) {
	  	cache->d_cache_area[i] = NULL;	
    	}		
	}
	if (data_type == FCELL_TYPE) {
		cache->f_cache_area = G_calloc (rows,sizeof (FCELL*));
    	for (i = 0; i<n; i++) {		  
       	cache->f_cache_area[i] = NULL;				
    	}				
	}
	
	/* if cache turned off, we cannot dynamically allocate, so do it now! */
	if ( cache->off == 1 ) {
		if (data_type == CELL_TYPE) {
			cache->c_cache_area[0] = G_allocate_raster_buf(CELL_TYPE);
		}
		if (data_type == DCELL_TYPE) {
			cache->d_cache_area[0] = G_allocate_raster_buf(DCELL_TYPE);
		}
		if (data_type == FCELL_TYPE) {
			cache->f_cache_area[0] = G_allocate_raster_buf(FCELL_TYPE);
		}		
	}
	
	cache->allocated_lookup = G_calloc (n, sizeof(long));	
   	for (i=0;i<n;i++) {
		cache->allocated_lookup[i] = -1; /* -1 marks free entry */
	}
    return (0);	
};

/* retreives row 'i' from the cache */
void* GT_RC_get (GT_Row_cache_t *cache, long i) {

    	int error;	
	char tmp[255];
	struct Cell_head region;
	
	/* if cache was turned off: just read row from disk and return it */
	if ( cache->off == 1 ) {
		if ( cache->data_type == CELL_TYPE ) {
			error = G_get_c_raster_row (cache->fd,cache->c_cache_area[0],i);
		  	if ( error == -1 ) {
				G_get_window (&region);			  
			 	G_fatal_error ("Cache failure: could not read CELL raster row at %.2f.\n",
			  					G_row_to_northing((float) i,&region));
			}
			return (CELL*) (cache->c_cache_area[0]);
		}
		if ( cache->data_type == DCELL_TYPE ) {
			error = G_get_d_raster_row (cache->fd,cache->d_cache_area[0],i);
		  	if ( error == -1 ) {
				G_get_window (&region);			  
			 	G_fatal_error ("Cache failure: could not read CELL raster row at %.2f.\n",
			  					G_row_to_northing((float) i,&region));
			}
			return (DCELL*) (cache->d_cache_area[0]);
		}
		if ( cache->data_type == FCELL_TYPE ) {
			error = G_get_f_raster_row (cache->fd,cache->f_cache_area[0],i);
		  	if ( error == -1 ) {
				G_get_window (&region);			  
			 	G_fatal_error ("Cache failure: could not read CELL raster row at %.2f.\n",
			  					G_row_to_northing((float) i,&region));
			}
			return (FCELL*) (cache->f_cache_area[0]);			
		}		
	}
	
	if ((i < 0) || (i >= cache->region_rows)) {
		G_get_window (&region);
		sprintf (tmp,"Illegal cache request: row %i at Northing %.2f.\n",(int)i, 
			G_row_to_northing((float)i,&region));
		G_fatal_error ( "%s", (char*) tmp);
	}
	
	if (cache->data_type == CELL_TYPE) {
	  if (cache->c_cache_area[i] == NULL) {
		/* case one: cache miss */
		if (cache->allocated < (cache->max+1)) { /* still got spare slots in cache */		  
		  cache->c_cache_area[i] = G_allocate_raster_buf(CELL_TYPE);
		  /* put row into cache */
		  error = G_get_c_raster_row (cache->fd,cache->c_cache_area[i],i);
		  if ( error == -1 ) {
			  G_get_window (&region);
			  
			  G_fatal_error ("Cache failure: could not read CELL raster row at %.2f.\n",
			  				G_row_to_northing((float)i,&region));
		  }
		  cache->allocated_lookup[cache->allocated] = i;		  
		  cache->allocated ++;
		  cache->misses[i] = 0;
		  /* increase cache miss count on all other rows */	
		  GT_RC_update_worst (cache, i);
		  return (CELL*) (cache->c_cache_area[i]);
        } else {			
		  /* if max cache allocated, we have to throw out one row */
		  /* find row with most misses and de-allocate it*/
		  G_free (cache->c_cache_area[GT_RC_find_worst(cache)]);
		  cache->c_cache_area[GT_RC_find_worst(cache)] = NULL;	
		  /* put row into cache */
          cache->c_cache_area[i] = G_allocate_raster_buf(CELL_TYPE);			
		  error = G_get_c_raster_row (cache->fd,cache->c_cache_area[i],i);
		  if ( error == -1 ) {
			  G_get_window (&region);
			  G_fatal_error ("Cache failure: could not read CELL raster row at %.2f.\n",
			  				G_row_to_northing((float)i,&region));
		  }			
		  cache->allocated_lookup[GT_RC_lookup_slot(cache, GT_RC_find_worst (cache))] = i;
		  cache->misses[i] = 0;	
		  /* increase cache miss count on all other rows */
		  GT_RC_update_worst (cache, i);
		  return (CELL*) (cache->c_cache_area[i]);		
        }							
	  } else {  
		/* case two: row in cache */
		/* that's good: we have to do nothing but return a pointer to the row */
		cache->misses[i] = 0;
		/* increase cache miss count on all other rows */  
		GT_RC_update_worst (cache, i);		
		return (CELL*) (cache->c_cache_area[i]);
	  }
    }	 	

	if (cache->data_type == DCELL_TYPE) {
	  if (cache->d_cache_area[i] == NULL) {
		/* case one: cache miss */
		if (cache->allocated < (cache->max+1)) { /* still got spare slots in cache */		  
		  cache->d_cache_area[i] = G_allocate_raster_buf(DCELL_TYPE);
		  /* put row into cache */
		  error = G_get_d_raster_row (cache->fd,cache->d_cache_area[i],i);
		  if ( error == -1 ) {
			  G_get_window (&region);
			  G_fatal_error ("Cache failure: could not read DCELL raster row at %.2f.\n",
			  				G_row_to_northing((float)i,&region));
		  }			
		  cache->allocated_lookup[cache->allocated] = i;		  
		  cache->allocated ++;
		  cache->misses[i] = 0;
		  /* increase cache miss count on all other rows */	
		  GT_RC_update_worst (cache, i);
		  return (DCELL*) (cache->d_cache_area[i]);
        } else {			
		  /* if max cache allocated, we have to throw out one row */
		  /* find row with most misses and de-allocate it*/
		  G_free (cache->d_cache_area[GT_RC_find_worst(cache)]);
		  cache->d_cache_area[GT_RC_find_worst(cache)] = NULL;	
		  /* put row into cache */
          cache->d_cache_area[i] = G_allocate_raster_buf(DCELL_TYPE);			
		  error = G_get_d_raster_row (cache->fd,cache->d_cache_area[i],i);
		  if ( error == -1 ) {
			  G_get_window (&region);
			  G_fatal_error ("Cache failure: could not read DCELL raster row at %.2f.\n",
			  				G_row_to_northing((float)i,&region));
		  }			
		  cache->allocated_lookup[GT_RC_lookup_slot(cache, GT_RC_find_worst (cache))] = i;
		  cache->misses[i] = 0;	
		  /* increase cache miss count on all other rows */
		  GT_RC_update_worst (cache, i);
		  return (DCELL*) (cache->d_cache_area[i]);		
        }							
	  } else {  
		/* case two: row in cache */
		/* that's good: we have to do nothing but return a pointer to the row */
		cache->misses[i] = 0;
		/* increase cache miss count on all other rows */  
		GT_RC_update_worst (cache, i);		
		return (DCELL*) (cache->d_cache_area[i]);
	  }
    }	 	
	
	if (cache->data_type == FCELL_TYPE) {
	  if (cache->f_cache_area[i] == NULL) {
		/* case one: cache miss */
		if (cache->allocated < (cache->max+1)) { /* still got spare slots in cache */		  
		  cache->f_cache_area[i] = G_allocate_raster_buf(FCELL_TYPE);
		  /* put row into cache */
		  error = G_get_f_raster_row (cache->fd,cache->f_cache_area[i],i);
		  if ( error == -1 ) {
			  G_get_window (&region);
			  G_fatal_error ("Cache failure: could not read FCELL raster row at %.2f.\n",
			  				G_row_to_northing((float)i,&region));
		  }			
		  cache->allocated_lookup[cache->allocated] = i;		  
		  cache->allocated ++;
		  cache->misses[i] = 0;
		  /* increase cache miss count on all other rows */	
		  GT_RC_update_worst (cache, i);
		  return (FCELL*) (cache->f_cache_area[i]);
        } else {			
		  /* if max cache allocated, we have to throw out one row */
		  /* find row with most misses and de-allocate it*/
		  G_free (cache->f_cache_area[GT_RC_find_worst(cache)]);
		  cache->f_cache_area[GT_RC_find_worst(cache)] = NULL;	
		  /* put row into cache */
          cache->f_cache_area[i] = G_allocate_raster_buf(FCELL_TYPE);			
		  error = G_get_f_raster_row (cache->fd,cache->f_cache_area[i],i);
		  if ( error == -1 ) {
			  G_get_window (&region);
			  G_fatal_error ("Cache failure: could not read FCELL raster row at %.2f.\n",
			  				G_row_to_northing((float)i,&region));
		  }			
		  cache->allocated_lookup[GT_RC_lookup_slot(cache, GT_RC_find_worst (cache))] = i;
		  cache->misses[i] = 0;	
		  /* increase cache miss count on all other rows */
		  GT_RC_update_worst (cache, i);
		  return (FCELL*) (cache->f_cache_area[i]);		
        }							
	  } else {  
		/* case two: row in cache */
		/* that's good: we have to do nothing but return a pointer to the row */
		cache->misses[i] = 0;
		/* increase cache miss count on all other rows */  
		GT_RC_update_worst (cache, i);		
		return (FCELL*) (cache->f_cache_area[i]);
	  }
    }	 	
	
	return (NULL);
};

/* closes cache, frees allocated memory */
void GT_RC_close (GT_Row_cache_t *cache) {
	/* release all memory used to cache rows */
	int i;
	
	if (cache->off == 1) {
		for (i = 0; i < cache->region_rows;i++) {
			if (cache->data_type == CELL_TYPE) {
				if (cache->c_cache_area[i] != NULL) {
					G_free (cache->c_cache_area[i]);
					cache->c_cache_area[i] = NULL;
				}
			}
			if (cache->data_type == DCELL_TYPE) {
				if (cache->d_cache_area[i] != NULL) {
					G_free (cache->d_cache_area[i]);
					cache->d_cache_area[i] = NULL;
				}
			}		
			if (cache->data_type == FCELL_TYPE) {
				if (cache->f_cache_area[i] != NULL) {
					G_free (cache->f_cache_area[i]);
					cache->f_cache_area[i] = NULL;
				}
			}		
		}	
		if (cache->data_type == CELL_TYPE) {
			G_free (cache->c_cache_area);
		}
		if (cache->data_type == DCELL_TYPE) {
			G_free (cache->d_cache_area);
		}
		if (cache->data_type == FCELL_TYPE) {
			G_free (cache->f_cache_area);
		}	
	} else {
		if (cache->data_type == CELL_TYPE) {
			G_free (cache->c_cache_area[0]);		
			G_free (cache->c_cache_area);
		}
		if (cache->data_type == DCELL_TYPE) {
			G_free (cache->d_cache_area[0]);		
			G_free (cache->d_cache_area);
		}
		if (cache->data_type == FCELL_TYPE) {
			G_free (cache->f_cache_area[0]);		
			G_free (cache->f_cache_area);
		}			
	}
	
	G_free (cache->misses);
	G_free (cache->allocated_lookup);		
	G_close_cell (cache->fd);
};
