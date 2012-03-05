/* CAT_ENGINE.C */

/* Purpose: Provides functions for easy categorisation of GRASS raster */
/* maps in CELL, DCELL or FCELL format. */
/* FCELL maps will be treated with double precision. */

/* TODO: copy FP color tables 1:1 when using 'clean' operation on an */
/*       FP map with FP output. */

/* This file is licensed under the GPL (version 2) */
/* see: http://www.gnu.org/copyleft/gpl.html */

/* (c) Benjamin Ducke 2004 */
/* benducke@compuserve.de */


#include <stdlib.h>
#include <string.h>
#include <math.h>

#include <grass/gis.h>
#include "gt/cat_engine.h"


/* GT_get_stats () */
/* Read basic category information from any GRASS raster map.

   ARGS:	name = name of GRASS raster map
           mapset = mapset to read map from (leave empty or NULL 
		             for first matching map in search path)
			null_count = number of NULL cells
			nocat_count = number of cells that do not match a category
			              (i.e. do not lie within the range 0-highest cat num)
			print_progress = set this to '1' to have a status display
   RETURN:	number of categories, OR:
     		0 = no categories defined
			-1 = file open error
   NOTE:	this function calls GT_get_c_stats() or GT_get_f_stats(),
   		according to the type of input map
*/
int GT_get_stats (char *name, char *mapset, 
					long *null_count, long *nocat_count,
					int print_progress) {
					
	int fd;					
						
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
		
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (-1);	
  	}	
    								
	if (G_raster_map_is_fp (name, mapset)) {
		return (GT_get_f_stats (name, mapset, null_count, nocat_count, print_progress));
		
    } else {
    	return (GT_get_c_stats (name, mapset, null_count, nocat_count, print_progress));
    }
    
    return (0);	
}


/* GT_get_c_stats () */
/* Read basic category information from a grass CELL map.

   ARGS:	name = name of GRASS raster map
           mapset = mapset to read map from (leave empty or NULL 
		             for first matching map in search path)
			null_count = number of NULL cells
			nocat_count = number of cells that do not match a category
			              (i.e. do not lie within the range 0-highest cat num)
			print_progress = set this to '1' to have a status display
   RETURN:	number of categories, OR:
     		0 = no categories defined
			-1 = map not in CELL format
			-2 = general file open error
			
  NOTE:		both null_count and nocat_count will be set to -1 if no categories are defined
  			in the input map!
*/
int GT_get_c_stats (char *name, char *mapset, 
					long *null_count, long *nocat_count,
					int print_progress) {
	int fd;
	int error;
	struct Categories cats;															
	int n_cats = 0;	
	int i,j;
	int rows, cols;
	CELL *cellbuf;
	CELL value;
	
	rows = G_window_rows ();
	cols = G_window_cols ();
	*null_count = 0;
	*nocat_count = 0;
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (-2);	
  	}
    								
	if (G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (-1);
    }
		
	/* now, open map and get number of defined categories */
	G_init_cats (0, "", &cats);
	error = G_read_cats (name, mapset, &cats);
	if (error != 0) {
		/* no categories found */
		G_close_cell (fd);
		*null_count = -1;
		*nocat_count = -1;
		return (0);
	}
	
	/* this is the number of categories in the map from 0 to n_cats */
	/* note that there might be cagefories in between 0 and n_cats */
	/* which are undefined (including category 0). */
	n_cats = G_number_of_cats (name, mapset) + 1;
							
	/* now, analyse raster file */
	if (print_progress) {
		fprintf (stdout, "Gathering category information: \n");
	}
	cellbuf = G_allocate_raster_buf (CELL_TYPE);
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, cellbuf, i, CELL_TYPE);	
		for (j=0; j<cols; j++) {
			/* check for NULL value */			
			if ( G_is_c_null_value (&cellbuf[j]) == 1) {
				*null_count = *null_count + 1;
			} else {
				/* check for value outside of category range */
				value = cellbuf[j];
				if ( ( value < 0 ) || ( value > n_cats - 1) ) {
					*nocat_count = *nocat_count + 1;
				}				
			}
		}
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}
	}

	if (print_progress) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}	
	G_free (cellbuf);
	G_close_cell (fd);
	return (n_cats);
}


/* GT_get_f_stats () */
/* Read basic category information from a grass FCELL or DCELL map.

   ARGS:	name = name of GRASS raster map
           mapset = mapset to read map from (leave empty or NULL 
		             for first matching map in search path)
			null_count = number of NULL cells
			nocat_count = number of cells that do not match a category
			              (i.e. do not lie within the range 0-highest cat num)
			print_progress = set this to '1' to have a status display
   RETURN:	number of categories, OR:
     		0 = no categories defined
			-1 = map not in FCELL or DCELL format
			-2 = general file open error
*/
int GT_get_f_stats (char *name, char *mapset, 
					long *null_count, long *nocat_count,
					int print_progress) {
	int fd;
	int error;
	struct Categories cats;															
	int n_cats = 0;	
	int i,j;
	int rows, cols;
	DCELL *dcellbuf;
	DCELL dvalue;
	CELL value;	
	rows = G_window_rows ();
	cols = G_window_cols ();
	*null_count = 0;
	*nocat_count = 0;	
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (-2);	
  	}
    								
	if (!G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (-1);
    }
		
	/* now, open map and get number of defined categories */
	G_init_cats (0, "", &cats);
	error = G_read_cats (name, mapset, &cats);
	if (error != 0) {
		/* no categories found */
		G_close_cell (fd);
		*null_count = -1;
		*nocat_count = -1;
		return (0);
	}
	
	/* this is the number of defined (i.e labeled) categories in the map */
	/* if it is zero, we might just as well return to caller. */
	n_cats = G_number_of_raster_cats (&cats);
	if (n_cats == 0) {
		G_close_cell (fd);
		*null_count = -1;
		*nocat_count = -1;
		return (0);		
	}	
	
	/* now, analyse raster file */
	if (print_progress) {
		fprintf (stdout, "Gathering category information: \n");
	}
	dcellbuf = G_allocate_raster_buf (DCELL_TYPE);
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, dcellbuf, i, DCELL_TYPE);	
		for (j=0; j<cols; j++) {
			/* check for NULL value */			
			if ( G_is_d_null_value (&dcellbuf[j]) == 1) {
				*null_count = *null_count + 1;
			} else {
				/* check for value outside of category range */
				dvalue = dcellbuf[j];
				value = G_quant_get_cell_value (&cats.q, dvalue);
				if ( ( value < 0 ) || ( value > n_cats -1) ) {
					*nocat_count = *nocat_count + 1;
				}
			}
		}
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}
	}	
		
	G_free (dcellbuf);
	G_close_cell (fd);
	return (n_cats);
}

/* GT_get_range () */
/* Find minimum and maximum values in a GRASS raster map of any type.

   ARGS:	name = name of GRASS raster map
           mapset = mapset to read map from (leave empty or NULL 
		             for first matching map in search path)
			*min = stores minimum value
			*max = stores maximum value
			print_progress = set this to '1' to have a status display
   RETURN:	0 on success
			-1 = invalid map format
			-2 = general file open error
   NOTE:	min and max values in CELL maps will be returned as double values
*/
int GT_get_range (char *name, char *mapset, double *min, double *max, 
					int print_progress) {
					
	int fd;
	int imin;
	int imax;
	int error;						

	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (-1);	
  	}
    								
	if (G_raster_map_is_fp (name, mapset)) {
		return (GT_get_f_range (name, mapset, min, max, print_progress));
		
    } else {
    	error = GT_get_c_range (name, mapset, &imin, &imax, print_progress);
		*min = (double) imin;
		*max = (double) imax;		
		return (error);
    }
    
    return (0);	
}


/* GT_get_c_range () */
/* Find minimum and maximum values in a grass CELL map.

   ARGS:	name = name of GRASS raster map
           mapset = mapset to read map from (leave empty or NULL 
		             for first matching map in search path)
			*min = stores minimum value
			*max = stores maximum value
			print_progress = set this to '1' to have a status display
   RETURN:	0 on success
			-1 = map not in CELL format
			-2 = general file open error
*/
int GT_get_c_range (char *name, char *mapset, int *min, int *max, 
					int print_progress) {
	int fd;
	int error;
	int i,j;
	int rows, cols;
	CELL *cellbuf;
	CELL value;
	/* a few flags to control quantification of the output map */
	int firstpass = 1;
	
	rows = G_window_rows ();
	cols = G_window_cols ();
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {		
		return (-2);	
  	}	
    	
	if (G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (-1);
    }
		
	/* Analyse raster file and get min and max ints */
	cellbuf = G_allocate_raster_buf (CELL_TYPE);
	if (print_progress) {
		fprintf (stdout, "Finding min and max raster values: \n");
	}		
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, cellbuf, i, CELL_TYPE);	
		for (j=0; j<cols; j++) {
			/* check for NULL value and update min and max */			
			if ( !G_is_c_null_value (&cellbuf[j]) == 1) {
				value = cellbuf[j];
				if ( value < *min ) {
					*min = value;
				}
				if ( value > *max ) {
					*max = value;
				}
				if ( firstpass ) {
					*min = value;
					*max = value;
					firstpass = 0;
				}
			}
		}
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}				
	}
	
	if (print_progress) {
		fprintf (stdout,"\n");
	}
		
	G_free (cellbuf);
	G_close_cell (fd);
	return (0);	
}


/* GT_get_f_range () */
/* Find minimum and maximum values in a GRASS DCELL/FCELL map.

   ARGS:	name = name of GRASS raster map
           mapset = mapset to read map from (leave empty or NULL 
		             for first matching map in search path)
			*min = stores minimum value
			*max = stores maximum value
			print_progress = set this to '1' to have a status display
   RETURN:	0 on success
			-1 = map not in DCELL/FCELL format
			-2 = general file open error
*/
int GT_get_f_range (char *name, char *mapset, double *min, double *max, 
					int print_progress) {
	int fd;
	int error;
	int i,j;
	int rows, cols;
	DCELL *dcellbuf;
	DCELL dvalue;
	/* a few flags to control quantification of the output map */
	int firstpass = 1;
	
	rows = G_window_rows ();
	cols = G_window_cols ();
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {		
		return (-2);	
  	}	
    	
	if (!G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (-1);
    }
		
	/* Analyse raster file and get min and max ints */
	dcellbuf = G_allocate_raster_buf (DCELL_TYPE);
	if (print_progress) {
		fprintf (stdout, "Finding min and max raster values: \n");
	}		
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, dcellbuf, i, DCELL_TYPE);	
		for (j=0; j<cols; j++) {
			/* check for NULL value and update min and max */			
			if ( !G_is_d_null_value (&dcellbuf[j]) == 1) {
				dvalue = dcellbuf[j];
				if ( dvalue < *min ) {
					*min = dvalue;
				}
				if ( dvalue > *max ) {
					*max = dvalue;
				}
				if ( firstpass ) {
					*min = dvalue;
					*max = dvalue;
					firstpass = 0;
				}
			}
		}
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}				
	}
	
	if (print_progress) {
		fprintf (stdout,"\n");
	}
		
	G_free (dcellbuf);
	G_close_cell (fd);
	return (0);	
}


/* GT_get_counts () */
/* Read occurence counts of categories from any GRASS raster map.

   ARGS:	name = name of GRASS raster map
           mapset = mapset to read map from (leave empty or NULL 
		             for first matching map in search path)
			print_progress = set this to '1' to have a status display
   RETURN:	a pointer to an array of ints with category counts
         	(0 .. N)
     		NULL = no categories defined or general file error
			
	NOTE:	Number of categories in the array (i.e. array length) can
    		be obtained using get_cell_stats().
			Memory for returned int array must not be pre-allocated by caller.
			Memory must be free'd by caller!
*/
long *GT_get_counts (char *name, char *mapset, int print_progress) {
					
	int fd;					

	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (NULL);	
  	}
    								
	if (G_raster_map_is_fp (name, mapset)) {
		return (GT_get_f_counts (name, mapset, print_progress));		
    } else {
    	return (GT_get_c_counts (name, mapset, print_progress));
    }
    
    return (NULL);	
}


/* GT_get_c_counts() */
/* Read occurence counts of categories from a grass CELL map.

   ARGS:	name = name of GRASS raster map
           mapset = mapset to read map from (leave empty or NULL 
		             for first matching map in search path)
			print_progress = set this to '1' to have a status display
   RETURN:	a pointer to an array of ints with category counts
         	(0 .. N)
     		NULL = no categories defined or general file error
			
	NOTE:	Number of categories in the array, i.e. array length can
    		be obtained using get_cell_stats().
			Memory for returned int array must not be pre-allocated by caller.
			Memory must be free'd by caller!
*/
long *GT_get_c_counts (char *name, char *mapset, int print_progress) {
	int fd;
	int error;
	struct Categories cats;															
	int n_cats = 0;	
	int i,j;
	int rows, cols;
	CELL *cellbuf;
	CELL value;
	long *categories;
	
	rows = G_window_rows ();
	cols = G_window_cols ();
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (NULL);	
  	}
    	
	if (G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (NULL);
    }	

	/* now, open map and get number of defined categories */
	G_init_cats (0, "", &cats);
	error = G_read_cats (name, mapset, &cats);
	if (error != 0) {
		/* no categories found */
		G_close_cell (fd);
		return (NULL);
	}
	n_cats = G_number_of_cats (name, mapset) + 1;
		
	/* allocate mem to store category counts */
	categories = G_calloc (n_cats, sizeof (long));
	for (i=0; i < n_cats; i++) {
		categories [i] = 0;
	}
	
	/* now, analyse raster file and count category frequencies */
	cellbuf = G_allocate_raster_buf (CELL_TYPE);
	if (print_progress) {
		fprintf (stdout, "Counting category frequencies: \n");
	}	
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, cellbuf, i, CELL_TYPE);	
		for (j=0; j<cols; j++) {
			/* check for NULL value */			
			if ( G_is_c_null_value (&cellbuf[j]) == 1) {
				/* do nothing */
			} else {
				/* check for value outside of category range */
				value = cellbuf[j];
				if ( ! (( value < 0 ) || ( value > n_cats -1)) ) {
					categories[value] = categories[value] + 1;
				}				
			}
		}
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}		
	}
	
	if (print_progress) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}
	
	G_free (cellbuf);
	G_close_cell (fd);	
	return (categories);
}


/* GT_get_f_counts () */
/* Read occurence counts of categories from a grass FCELL or DCELL map.

   ARGS:	name = name of GRASS raster map
           mapset = mapset to read map from (leave empty or NULL 
		             for first matching map in search path)
			print_progress = set this to '1' to have a status display
   RETURN:	a pointer to an array of ints with category counts
         	(0 .. N)
     		NULL = no categories defined or general file error
			
	NOTE:	Number of categories in the array, i.e. array length can
    		be obtained using get_cell_stats().
			Memory for returned int array must not be pre-allocated by caller.
			Memory must be free'd by caller!
*/
long *GT_get_f_counts (char *name, char *mapset, int print_progress) {
	int fd;
	int error;
	struct Categories cats;															
	int n_cats = 0;	
	int i,j;
	int rows, cols;
	DCELL *dcellbuf;
	DCELL dvalue;
	CELL value;
	long *categories;
	
	rows = G_window_rows ();
	cols = G_window_cols ();
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (NULL);	
  	}
    	
	if (!G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (NULL);
    }	
			
	/* now, open map and get number of defined categories */
	G_init_cats (0, "", &cats);
	error = G_read_cats (name, mapset, &cats);
	if (error != 0) {
		/* no categories found */
		G_close_cell (fd);
		return (NULL);
	}
	
	/* this is the number of defined (i.e labeled) categories in the map */
	/* if it is zero, we might just as well return to caller. */
	n_cats = G_number_of_raster_cats (&cats);
	if (n_cats == 0) {
		G_close_cell (fd);
		return (NULL);		
	}
	
	/* allocate mem to store category counts */
	categories = G_calloc (n_cats, sizeof (long));
	for (i=0; i<n_cats; i++) {
		categories [i] = 0;
	}
	
	/* now, analyse raster file and count category frequencies */
	dcellbuf = G_allocate_raster_buf (DCELL_TYPE);
	if (print_progress) {
		fprintf (stdout, "Counting category frequencies: \n");
	}	
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, dcellbuf, i, DCELL_TYPE);	
		for (j=0; j<cols; j++) {
			/* check for NULL value */			
			if ( G_is_d_null_value (&dcellbuf[j]) == 0) {
				/* check for value outside of category range */
				dvalue = dcellbuf[j];
				value = G_quant_get_cell_value (&cats.q, dvalue);								
				if ( ! (( value < 0 ) || ( value > n_cats -1)) ) {
					categories[value] = categories[value] + 1;
				}				
			}
		}
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}		
	}
	
	if (print_progress) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}
	G_free (dcellbuf);
	G_close_cell (fd);
	return (categories);
}


/* GT_get_labels () */
/* Read category labels from a grass raster map of any type.

   ARGS:	name = name of GRASS raster map
           mapset = mapset to read map from (leave empty or NULL 
		             for first matching map in search path)
			print_progress = set this to '1' to have a status display
   RETURN:	a pointer to an array of *char with labels
         	(0 .. N)
     		NULL = no labels defined or general file error
			
	NOTE:	Number of categories in the array, i.e. array length can
    		be obtained using get_cell_stats().
			Memory for returned char array must not be pre-allocated by caller.
			Memory must be free'd by caller
*/
char **GT_get_labels (char *name, char *mapset) {
	
	int fd;

	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (NULL);	
  	}
    								
	if (G_raster_map_is_fp (name, mapset)) {
		return (GT_get_f_labels (name, mapset));
		
    } else {
		return (GT_get_c_labels (name, mapset));
    }
    
    return (NULL);	
}


/* GT_get_c_labels () */
/* Read category labels from a grass CELL map.

   ARGS:	name = name of GRASS raster map
           mapset = mapset to read map from (leave empty or NULL 
		             for first matching map in search path)
			print_progress = set this to '1' to have a status display
   RETURN:	a pointer to an array of *char with labels
         	(0 .. N)
     		NULL = no labels defined or general file error
			
	NOTE:	Number of categories in the array, i.e. array length can
    		be obtained using get_cell_stats().
			Memory for returned char array must not be pre-allocated by caller.
			Memory must be free'd by caller
*/
char **GT_get_c_labels (char *name, char *mapset) {
	int fd;
	int error;
	struct Categories cats;															
	int n_cats = 0;	
	int i;
	char **labels;
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (NULL);	
  	}
    								
	if (G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (NULL);
    }
				
	/* now, open map and get number of defined categories */
	G_init_cats (0, "", &cats);
	error = G_read_cats (name, mapset, &cats);
	if (error != 0) {
		/* no categories found */
		G_close_cell (fd);
		return (NULL);
	}
	n_cats = G_number_of_cats (name, mapset) + 1;
	
	/* allocate mem to store description strings for cats */
	/* every valid category also has a label. */
	/* if the user does not provide/delete a label using 'r.support', */
	/* GRASS will delete that category entry from the header */
	labels = G_calloc (n_cats, sizeof (char*));	
	for (i=0; i < n_cats; i++) {
		labels[i] = G_calloc ((signed int) strlen(G_get_c_raster_cat ((CELL*) &i, &cats)) + 1, sizeof(char));		
		strcpy (labels[i], G_get_c_raster_cat ((CELL*) &i, &cats));
	}	
	
	G_close_cell (fd);
	return (labels);
}


/* GT_get_f_labels () */
/* Read category labels from a GRASS DCELL/FCELL map.

   ARGS:	name = name of GRASS raster map
           mapset = mapset to read map from (leave empty or NULL 
		             for first matching map in search path)
			print_progress = set this to '1' to have a status display
   RETURN:	a pointer to an array of *char with labels
         	(0 .. N)
     		NULL = no labels defined or general file error
			
	NOTE:	Number of categories in the array, i.e. array length can
    		be obtained using get_cell_stats().
			Memory for returned char array must not be pre-allocated by caller.
			Memory must be free'd by caller
*/
char **GT_get_f_labels (char *name, char *mapset) {
	int fd;
	int error;
	struct Categories cats;															
	int n_cats = 0;	
	int i;
	char **labels;
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (NULL);	
  	}
    								
	if (!G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (NULL);
    }
	
	/* now, open map and get number of defined categories */
	G_init_cats (0, "", &cats);
	error = G_read_cats (name, mapset, &cats);
	if (error != 0) {
		/* no categories found */
		G_close_cell (fd);
		return (NULL);
	}
	
	/* this is the number of defined (i.e labeled) categories in the map */
	/* if it is zero, we might just as well return to caller. */
	n_cats = G_number_of_raster_cats (&cats);
	if (n_cats == 0) {
		G_close_cell (fd);
		return (NULL);		
	}	
		
	/* allocate mem to store description strings for cats */
	/* every valid category also has a label. */
	/* if the user does not provide/delete a label using 'r.support', */
	/* GRASS will delete that category entry from the header */
	labels = G_calloc (n_cats, sizeof (char*));
	for (i=0; i < n_cats; i++) {
		labels[i] = G_calloc ((signed int) strlen (cats.labels[i]) + 1, sizeof(char));		
		strcpy (labels[i], cats.labels[i]);
	}
	
	G_close_cell (fd);
	return (labels);
}


/* GT_set_cats_only () */
/* Create a new CELL raster map with categories ranging from 0 .. N
			Input map can be a partly categorised GRASS raster map of any type.
			All values in the input map that are not mapped to a
			category will be replaced by NULL values in the output map.

   ARGS:	name = name of GRASS raster map to read in
           mapset = mapset to read map from (leave empty or NULL 
		         	for first matching map in search path)
			output = name of result raster map (will always be stored
                 	in the user's current mapset).
			intout = set to '1' to create a CELL (integer) output map
			print_progress = set this to '1' to have a status display

   RETURN:	
     		0 = OK
			-1 = ivalid map format
			-2 = input map read error
			-3 = output map write error
			-4 = no categories in input map
			
	NOTE:	for the output map, it is guaranteed that each cell will
			either be within the category range 0..n or NULL.
*/
int GT_set_cats_only (char *name, char *mapset, char *output, int intout, int print_progress) {					
	int fd;
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (-1);	
  	}
    								
	if (G_raster_map_is_fp (name, mapset)) {
		return (GT_set_f_cats_only (name, mapset, output, intout, print_progress));
		
    } else {
    	return (GT_set_c_cats_only (name, mapset, output, print_progress));
    }
    
    return (0);	
}


/* GT_set_c_cats_only () */
/* Create a new CELL raster map with categories ranging from 0 .. N
			Input map must be of type CELL.
			All values in the input map that are not mapped to a
			category will be replaced by NULL values in the output map.

   ARGS:	name = name of GRASS raster map to read in
           mapset = mapset to read map from (leave empty or NULL 
		         	for first matching map in search path)
			output = name of result raster map (will always be stored
                 	in the user's current mapset).
			print_progress = set this to '1' to have a status display

   RETURN:	
     		Number of categories in output map, or:
 			0  = no categories written to output map
			-1 = input map not in CELL format
			-2 = input map read error
			-3 = output map write error
			-4 = no categories in input map
			
	NOTE:	for the output map, it is guaranteed that each cell will
			either be within the category range 0..n or NULL.
*/
int GT_set_c_cats_only (char *name, char *mapset, char *output, int print_progress) {
	int fd, outfd;
	int error;
	struct Categories cats;															
	int n_cats = 0;	
	int i,j;
	int rows, cols;
	CELL *cellbuf;
	CELL value;
	char *strbuf, *strbuf2;
	
	rows = G_window_rows ();
	cols = G_window_cols ();
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (-2);	
  	}
	
	/* try to open new CELL map for output */
	outfd = G_open_cell_new (output);
 	if ( outfd < 0 ) {
		return (-3);	
  	}		
    	
	if (G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (-1);
    }	
			
	/* now, open map and get number of defined categories */
	G_init_cats (0, "", &cats);	
	error = G_read_cats (name, mapset, &cats);
	if (error != 0) {
		/* no categories found */
		G_close_cell (fd);
		return (-4);
	}	
	n_cats = G_number_of_cats (name, mapset) + 1;	
	
	cellbuf = G_allocate_raster_buf (CELL_TYPE);
	if (print_progress) {
		fprintf (stdout, "Converting cells outside category range to NULL: \n");
	}	
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, cellbuf, i, CELL_TYPE);	
		for (j=0; j<cols; j++) {
			/* check for NULL value */			
			if ( G_is_c_null_value (&cellbuf[j]) == 1) {
				/* copy NULL value through */
				G_set_c_null_value (&cellbuf[j],1);
			} else {
				/* check for value outside of category range */
				value = cellbuf[j];
				if (  (( value < 0 ) || ( value > n_cats - 1)) ) {
					G_set_c_null_value (&cellbuf[j],1);
				}
			}
		}
		/* write one line of output map */
		G_put_c_raster_row (outfd,cellbuf);
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}		
	}	
	if (print_progress) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}
	
	G_free (cellbuf);
	G_close_cell (fd);
	G_close_cell (outfd);
		
	/* copy category file to new output map */
	G_write_cats (output, &cats);
	
	/* write some comments into the history file */
	strbuf = G_calloc (255, sizeof (char));
	strbuf2 = G_calloc (255, sizeof (char));
	sprintf (strbuf,"%s@%s",name,mapset);
	sprintf (strbuf2,"r.categorise mode=clean");
	GT_write_hist (output,strbuf,"Selected only those INT cells that match a category.",
					strbuf2);
	G_free (strbuf);
	G_free (strbuf2);
	
	return (n_cats);	
}


/* GT_set_f_cats_only () */
/* Create a new CELL raster map with categories ranging from 0 .. N
			Input map must be of type DCELL or FCELL.
			All values in the input map that are not mapped to a
			category will be replaced by NULL values in the output map.

   ARGS:	name = name of GRASS raster map to read in
           mapset = mapset to read map from (leave empty or NULL 
		         	for first matching map in search path)
			output = name of result raster map (will always be stored
                 	in the user's current mapset).
			intout = set to '1' to create a CELL (integer) output map
			print_progress = set this to '1' to have a status display

   RETURN:	
     		Number of categories in output map, or:
 			0  = no categories written to output map
			-1 = input map not in CELL format
			-2 = input map read error
			-3 = output map write error
			-4 = no categories in input map
			
	NOTE:	for the output map, it is guaranteed that each cell will
			either be within the category range 0..n or NULL.
*/
int GT_set_f_cats_only (char *name, char *mapset, char *output, int intout, int print_progress) {
	int fd, outfd;
	int error;
	struct Categories cats;
	struct Categories int_cats;
	struct Colors srcColor;
	struct Colors dstColor;		
	int n_cats = 0;	
	int n_colors = 0;
	int i,j;
	int rows, cols;
	DCELL *dcellbuf;
	DCELL dvalue;
	DCELL from, to;
	CELL *outcellbuf;
	DCELL *doutcellbuf;
	CELL value;
	char *label;
	char *strbuf, *strbuf2;
	int map_type;
	unsigned char red, green, blue;
	
	rows = G_window_rows ();
	cols = G_window_cols ();

	/* to prevent compiler warnings */
	outcellbuf = NULL;
	doutcellbuf = NULL;
	label = NULL;
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (-2);	
  	}
	    	
	/* determine default mode of output map */
	if (! G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (-1);
    }	
	map_type = G_raster_map_type (name, mapset);
	G_set_fp_type (map_type);
	
	/* open new map for output */
	if ( intout == 1 ) outfd = G_open_cell_new (output);
		else outfd = G_open_fp_cell_new (output);
 	if ( outfd < 0 ) {
		return (-3);	
  	}			
	
	/* now, open map and get number of defined categories */
	G_init_cats (0, "tmp", &cats);	 /* source categories */
	error = G_read_cats (name, mapset, &cats);
	if (error != 0) {
		/* category file cannot be opened */
		G_close_cell (fd);
		return (-4);
	}
	
	/* this is the number of defined (i.e labeled) categories in the map */
	/* if it is zero, we might just as well return to caller. */
	n_cats = G_number_of_raster_cats (&cats);
	if (n_cats == 0) {
		G_close_cell (fd);
		return (0);		
	}		

	dcellbuf = G_allocate_raster_buf (DCELL_TYPE);
	if ( intout == 1 ) outcellbuf = G_allocate_raster_buf (CELL_TYPE);
		else doutcellbuf = G_allocate_raster_buf (DCELL_TYPE);

	if (print_progress) {
		fprintf (stdout, "Converting cells outside category range to NULL: \n");
	}	
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, dcellbuf, i, DCELL_TYPE);	
		/* write entire row of output map as NULL files, first */
		if ( intout == 1 ) G_set_c_null_value (outcellbuf, cols);
			else G_set_d_null_value (doutcellbuf, cols);
			  
		for (j=0; j<cols; j++) {
			/* check for NULL value */			
			if ( !G_is_d_null_value (&dcellbuf[j]) == 1) {				
				dvalue = dcellbuf[j];
				value = G_quant_get_cell_value (&cats.q, dvalue);				
				/* write map value only, if it is within category range */
				if (  !(( value < 0 ) || ( value > n_cats - 1)) ) {
					if ( intout == 1 ) outcellbuf[j] = value;
						else doutcellbuf[j] = dvalue;
				}
			}
		}
		/* write one line of output map */
		if ( intout == 1 ) G_put_c_raster_row (outfd,outcellbuf);
			else
			{	
				G_put_d_raster_row (outfd,doutcellbuf);
			}
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}		
	}	
	if (print_progress) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}
	G_free (dcellbuf);
	if ( intout == 1 ) G_free (outcellbuf);
		else G_free (doutcellbuf);

	G_close_cell (outfd);

	/* allocate some string buffers */
	strbuf = G_calloc (255,sizeof(char));
	strbuf2 = G_calloc (255,sizeof(char));				
		
	/* copy category labels to new output map */
	G_init_cats (0, "", &int_cats); /* destination categories */
	sprintf (strbuf,"Categorised cells only, from %s@%s.",name,mapset);
	G_set_cats_title (strbuf,&int_cats);	
	for (i=0; i<n_cats; i++) {
		label = G_get_ith_d_raster_cat (&cats, i, &from, &to);
		if (intout) {
			G_set_cat (i, label, &int_cats);
		} else {
			G_set_d_raster_cat(&from, &to, label, &int_cats);
		}
	}	
	error = G_write_cats (output, &int_cats);
	
	/* copy color table if present */
	error = G_read_colors (name, mapset, &srcColor);
	n_colors = srcColor.fixed.n_rules; /* number of colors in table */
	if (error == 1) {
		/* src map has a color table: let's copy it */
		G_init_colors (&dstColor);
		for (i=0; i<n_colors; i++) {
			/* dummy calls to get limits of cat color range */
			label = G_get_ith_d_raster_cat (&cats, i, &from, &to);
			G_get_d_raster_color (&from, (int*) &red, (int*) &green, (int*) &blue, &srcColor);			
			if (intout) {
				/* integer maps: we can only copy a truncated color map, i.e.
					each integer category will be assigned only the start RGB values
					of the original FP category color range
				*/			
				G_add_color_rule (i, red, green, blue, i, red, green, blue, &dstColor);
			} else {
				/* floating point maps: copy color table 1:1 */
				/* TODO: NOT YET WORKING */
				/*
				label = G_get_ith_d_raster_cat (&cats, i, &from, &to);
				G_get_d_raster_color (&to, (int*) &red2, (int*) &green2, (int*) &blue2, &srcColor);
				fprintf (stderr,"FROM %f TO %f: %i,%i,%i - %i,%i,%i\n", from, to, red, green, blue,
																			red2, green2, blue2);
				G_add_d_raster_color_rule (&from, red, green, blue, &to, red2, green2, blue2,
											&dstColor);
				*/
			}
		}
		/* write color table to output map */			
		G_write_colors (output, mapset, &dstColor);			
	}
	
	/* write some comments into the history file */
	sprintf (strbuf,"%s@%s",name,mapset);
	sprintf (strbuf2,"r.categorise mode=clean");
	GT_write_hist (output,strbuf,"Selected only those FP cells that match a category.",
					strbuf2);
	G_free (label);
	G_free (strbuf);
	G_free (strbuf2);

	/* close input raster map */
	G_close_cell (fd);	
	return (n_cats);	
}


/* GT_set_cats_num */
/* Create a new CELL raster map with categories ranging from 0 .. N
			Let the user specify N.

   ARGS:	name = name of GRASS raster map to read in
           mapset = mapset to read map from (leave empty or NULL 
		         	for first matching map in search path)
			output = name of result raster map (will always be stored
                 	in the user's current mapset).
			min, max = set to different values to cut the output range
         			(see NOTE)
			num = number of categories (N) to generate
			intout = set to '1' to create a CELL (integer) output map
			print_progress = set this to '1' to have a status display
   RETURN:	number of categories created (N)
     		0 = no categories created
			-1 = invalid input map format
			-2 = input map read error
			-3 = output map write error
			
	NOTE:	Maps values: divides the entire range of values in the input
	  			map into a user-specified number of intervals, all of the
				same width. Each interval will become a category in the
				output map.
			Range of categories can be cut by passing 'min' and 'max'
          		paremeters != -1. All values outside the range in the input map 
				will be replaced with NULL-values in the output map.
*/
int GT_set_cats_num (char *name, char *mapset, char *output, 
					double rmin, double rmax, int num, int intout, int print_progress) {
	int fd;					

	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (-1);	
  	}
    								
	if (G_raster_map_is_fp (name, mapset)) {
		return (GT_set_f_cats_num (name, mapset, output, rmin, rmax, num, intout, print_progress));
		
    } else {
    	return (GT_set_c_cats_num (name, mapset, output, (int) rmin, (int) rmax, num, print_progress));
    }
    
    return (0);						
}


/* GT_set_c_cats_num */
/* Create a new CELL raster map with categories ranging from 0 .. N
			Let the user specify N.

   ARGS:	name = name of GRASS raster map to read in
           mapset = mapset to read map from (leave empty or NULL 
		         	for first matching map in search path)
			output = name of result raster map (will always be stored
                 	in the user's current mapset).
			min, max = set to different values to cut the output range
         			(see NOTE)
			num = number of categories (N) to generate
			print_progress = set this to '1' to have a status display
   RETURN:	number of categories created (N)
     		0 = no categories created
			-1 = input map not in CELL format
			-2 = input map error
			-3 = output map write error
			
	NOTE:	Maps values: divides the entire range of CELL values in the input
	  			map into a user-specified number of intervals, all of the
				same width. Each interval will become a category in the
				output map.
			Range of categories can be cut by passing 'min' and 'max'
          		paremeters != -1. All values outside the range in the input map 
				will be replaced with NULL-values in the output map.
*/
int GT_set_c_cats_num (char *name, char *mapset, char *output, 
						int rmin, int rmax, int num, int print_progress) {
	int fd, outfd;
	int error;
	struct Categories cats;															
	int i,j;
	int rows, cols;
	CELL *cellbuf, *outcellbuf;
	CELL value;
	int divisor;
	int min, max;
	char *strbuf, *strbuf2;
	/* a flag to control quantification of the output map */
	int cutrange = 0;
	
	rows = G_window_rows ();
	cols = G_window_cols ();
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {		
		return (-2);	
  	}
	
	/* try to open new CELL map for output */
	outfd = G_open_cell_new (output);
 	if ( outfd < 0 ) {
		return (-3);	
  	}	
    	
	if (G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		G_close_cell (outfd);
		return (-1);
    }	
	
	if ( num < 2 ) {
		G_fatal_error ("GT_set_c_cats_num(): Number of categories must be at least 2.");
	}
		
	/* FIRST PASS: analyse raster file and get min and max ints */
	GT_get_c_range (name, mapset, &min, &max, print_progress);	
	
	/* check, if user wants to cut range and if min and max have been
	   set to sane values */
	if ( rmin != rmax ) {
		cutrange = 1; /* user wants to cut. Let's check ... */
		if ( rmin > rmax ) {
			G_warning ("User specified 'min' of input range larger than 'max'. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmin < min) && (cutrange == 1)) {
			G_warning ("User specified 'min' of input range smaller than minimum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmax > max) && (cutrange == 1)) {
			G_warning ("User specified 'max' of input range larger than maximum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
	}
	
	/* SECOND PASS: remap values, create labels and write output map */
	cellbuf = G_allocate_raster_buf (CELL_TYPE);
	outcellbuf = G_allocate_raster_buf (CELL_TYPE);
	if (print_progress) {
		fprintf (stdout, "Mapping categories: \n");
	}
	divisor = (int) rint (((float)max - (float)min) / (float)num);
	if ( divisor < 2 ) {
		G_fatal_error ("GT_set_c_cats_num(): Category width must be at least 2.");
	}	
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, cellbuf, i, CELL_TYPE);	
		for (j=0; j<cols; j++) {
			/* check for NULL values and update min and max */			
			if ( G_is_c_null_value (&cellbuf[j]) == 1) {
				/* pass NULL values through to output map */
				G_set_c_null_value (&outcellbuf[j],1);
			} else {
				/* check if any range cutting has to be done */
				if ( cutrange ) {
					if ( (cellbuf[j] < rmin) || (cellbuf[j] > rmax) ) {
						G_set_c_null_value (&outcellbuf[j],1);
					} else {
						value = abs(min) + cellbuf[j] + 1;						
						outcellbuf[j] = (int) ceil ( (double) value / (double) divisor ) -1;
						/* last category may be slightly larger */
						if (outcellbuf[j] > (num-1)) {
							outcellbuf[j] = (num-1);
						}
					}
				} else {
					/* just write mapped value */
					value = abs(min) + cellbuf[j] + 1;						
					outcellbuf[j] = (int) ceil ( (double) value / (double) divisor ) -1;
					/* last category may be slightly larger */
					if (outcellbuf[j] > (num-1)) {
						outcellbuf[j] = (num-1);
					}					
				}
			}
		}
		/* write output row */
		G_put_c_raster_row (outfd,outcellbuf);
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}
	}
	if (print_progress) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}
	
	/* create categories and category labels */
	G_init_cats (0, "", &cats);	
	strbuf = G_calloc (255, sizeof (char));
	strbuf2 = G_calloc (255, sizeof (char));
	if ( cutrange ) {
		sprintf (strbuf,"Categories mapped from %i to %i. Cut range = %i to %i ", 
				 min, max, rmin, rmax);
	} else {
			sprintf (strbuf,"Categories mapped from %i to %i.", min , max);
	}
	G_set_cats_title (strbuf, &cats);
	for (i=0; i<num; i++) {
		sprintf (strbuf,"%i to %i", (min + i*divisor), ((min + i*divisor) + divisor));
		/* last category may be slightly wider */
		if (i == num-1 ) {
			sprintf (strbuf,"%i to %i", (min + i*divisor), max);
		}
		G_set_cat (i, strbuf, &cats);
	}	
	G_free (cellbuf);
	G_close_cell (fd);
	G_free (outcellbuf);
	G_close_cell (outfd);
	
	/* write category file */
	G_write_cats (output, &cats);
	
	/* write some comments into the history file */
	sprintf (strbuf,"%s@%s",name,mapset);
	if ( rmin != rmax ) {
		sprintf (strbuf2,"r.categorise mode=num,%i min=%i max=%i",num, rmin, rmax);
	} else {
		sprintf (strbuf2,"r.categorise mode=num,%i",num);
	}
	GT_write_hist (output,strbuf,"Original INT data range categorised using fixed number of categories.",
					strbuf2);
	G_free (strbuf);
	G_free (strbuf2);
		
	return (num);	
}


/* GT_set_f_cats_num () */
/* Create a new raster map with categories ranging from 0 .. N
			Let the user specify N.

   ARGS:	name = name of GRASS raster map to read in
           mapset = mapset to read map from (leave empty or NULL 
		         	for first matching map in search path)
			output = name of result raster map (will always be stored
                 	in the user's current mapset).
			min, max = set to different values to cut the output range
         			(see NOTE)
			num = number of categories to generate
			intout = set to '1' to create a CELL (integer) output map
			print_progress = set this to '1' to have a status display
   RETURN:	number of categories created (N)
     		0 = no categories created
			-1 = input map not in CELL format
			-2 = input map error
			-3 = output map write error
			
	NOTE:	Maps values: divides range of DCELL/FCELL values in the input
	  			into N intervals of user specified, equal width
				Each interval will become a category in the output map.
			Range of categories can be cut by passing 'min' and 'max'
          		paremeters != -1. All values outside the range in the input map 
				will be replaced with NULL-values in the output map.
			The last category in the output map might end up wider than the
				actual maximum value in the input map.
			To improve legibility of map legends, the intervals will start at
				an integer offset, if 'round_cat=1'
*/
int GT_set_f_cats_num (char *name, char *mapset, char *output, 
						 double rmin, double rmax, int num, int intout, int print_progress) {
	int fd, outfd;
	int error;
	struct Categories cats;															
	int i,j;
	int rows, cols;
	DCELL *dcellbuf;
	CELL *outcellbuf;
	DCELL *doutcellbuf;
	DCELL dvalue;
	DCELL dmin, dmax;
	FCELL fmin, fmax;
	double divisor;
	double min, max;
	char *strbuf, *strbuf2;
	int map_type;
	
	/* a flag to control quantification of the output map */
	int cutrange = 0;
	
	rows = G_window_rows ();
	cols = G_window_cols ();

	/* to disable compiler warnings */
	outcellbuf = NULL;
	doutcellbuf = NULL;
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {		
		return (-2);	
  	}
	
   	/* determine default mode of output map */ 	
	if (!G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (-1);
    }
	map_type = G_raster_map_type (name, mapset);
	G_set_fp_type (map_type);
	
	/* open new map for output */
	if ( intout == 1 ) outfd = G_open_cell_new (output);
		else outfd = G_open_fp_cell_new (output);
 	if ( outfd < 0 ) {
		return (-3);	
  	}				
	
	if ( num < 2 ) {
		G_fatal_error ("GT_set_f_cats_num(): Number of categories must be at least 2.");
	}
	
	/* FIRST PASS: analyse raster file and get min and max ints */
	GT_get_f_range (name, mapset, &min, &max, print_progress);	
	
	/* check, if user wants to cut range and if min and max have been
	   set to sane values */
	if ( rmin != rmax ) {
		cutrange = 1; /* user wants to cut. Let's check ... */
		if ( rmin > rmax ) {
			G_warning ("User specified 'min' of input range larger than 'max'. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmin < min) && (cutrange == 1)) {
			G_warning ("User specified 'min' of input range smaller than minimum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmax > max) && (cutrange == 1)) {
			G_warning ("User specified 'max' of input range larger than maximum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
	}
	
	/* SECOND PASS: remap values, create labels and write output map */
	dcellbuf = G_allocate_raster_buf (DCELL_TYPE);
	if ( intout == 1 ) outcellbuf = G_allocate_raster_buf (CELL_TYPE);
		else doutcellbuf = G_allocate_raster_buf (DCELL_TYPE);
	
	if (print_progress) {
		fprintf (stdout, "Mapping categories: \n");
	}			
	divisor = (max-min) / num;
		
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, dcellbuf, i, DCELL_TYPE);	
		for (j=0; j<cols; j++) {
			/* check for NULL values and update min and max */			
			if ( G_is_d_null_value (&dcellbuf[j]) == 1) {
				/* pass NULL values through to output map */
				if ( intout == 1 ) G_set_c_null_value (&outcellbuf[j],1);
					else G_set_d_null_value (&doutcellbuf[j],1);
			} else {
				/* check if any range cutting has to be done */
				if ( cutrange ) {
					if ( (dcellbuf[j] < rmin) || (dcellbuf[j] > rmax) ) {
						if ( intout == 1 ) G_set_c_null_value (&outcellbuf[j],1);
							else G_set_d_null_value (&doutcellbuf[j],1);
					} else {						
						dvalue = dcellbuf[j] - min;						
						if ( intout == 1 ) outcellbuf[j] = (CELL) floor (dvalue / divisor);
							else doutcellbuf[j] = dcellbuf[j];
						/* maximum value must be forced into highest category */
						if ( intout == 1 ) {
							if ( outcellbuf[j] > (num -1) ) {
								outcellbuf[j] --;											
							}
						}
					}
				} else {
					dvalue = dcellbuf[j] - min;
					if ( intout == 1 ) outcellbuf[j] = (CELL) floor (dvalue / divisor);
						else doutcellbuf[j] = dcellbuf[j];
					/* maximum value must be forced into highest category */
					if ( intout == 1 ) {	
						if ( outcellbuf[j] > (num -1) ) {
							outcellbuf[j] --;
						}
					}
				}
			}
		}
		/* write output row */
		if ( intout == 1) G_put_c_raster_row (outfd,outcellbuf);
			else G_put_d_raster_row (outfd,doutcellbuf);
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}
	}
	if (print_progress) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}

	G_free (dcellbuf);
	G_close_cell (fd);
	if (intout == 1) G_free (outcellbuf);
		else G_free (doutcellbuf);
	G_close_cell (outfd);	
	
	/* create categories and category labels */
	G_init_cats (num, "", &cats);			
	strbuf = G_calloc (255,sizeof (char));
	strbuf2 = G_calloc (255,sizeof (char));
	if ( cutrange ) {
		sprintf (strbuf,"Cut range=%2$.*1$f to %3$.*1$f ", 
				GT_DECDIGITS, rmin, rmax);
	} else {
			sprintf (strbuf,"Full range of source map");
	}
	G_set_cats_title (strbuf, &cats);
	for (i=0; i<num; i++) {
		sprintf (strbuf,"%2$.*1$f to %3$.*1$f", GT_DECDIGITS, (min + i*divisor), 
				((min + i*divisor) + divisor));
		if ( intout == 1 ) G_set_cat (i, strbuf, &cats); /* integer cats */
			else {
				/* create floating point category ranges */
				if ( map_type == DCELL_TYPE ) {
					dmin = (min + i*divisor);
					dmax = (min + i*divisor) + divisor;
					G_set_d_raster_cat (&dmin, &dmax, strbuf, &cats);
				}
				if ( map_type == FCELL_TYPE ) {
					fmin = (min + i*divisor);
					fmax = (min + i*divisor) + divisor;
					G_set_f_raster_cat (&fmin, &fmax, strbuf, &cats);
				}
			}
	}	
	
	/* write category file */
	G_write_cats (output, &cats);
	
	/* write some comments into the history file */
	sprintf (strbuf,"%s@%s",name,mapset);
	if ( rmin != rmax ) {
		sprintf (strbuf2,"r.categorise mode=num,%i min=%.3f max=%.3f",num, rmin, rmax);
	} else {
		sprintf (strbuf2,"r.categorise mode=num,%i", num);
	}
	GT_write_hist (output,strbuf,"Original FP data range categorised using fixed number of intervals.",
					strbuf2);	
	G_free (strbuf);
	G_free (strbuf2);	
	
	return (num);							 
}


/* GT_set_cats_width () */
/* Create a new CELL raster map with categories ranging from 0 .. N
			Let the user specify category width. N will then be
 			determined automatically.
			Input map can be of any GRASS raster type.

   ARGS:	name = name of GRASS raster map to read in
           mapset = mapset to read map from (leave empty or NULL 
		         	for first matching map in search path)
			output = name of result raster map (will always be stored
                 	in the user's current mapset).
			min, max = set to different values to cut the output range
         			(see NOTE)
			width = width of categories to generate
			round_cat = set to '1' to start category 0 at the nearest integer
						value (floor).
			intout = set to '1' to force integer (CELL) map output
			print_progress = set this to '1' to have a status display
   RETURN:	number of categories created (N)
     		0 = no categories created
			-1 = invalid input map format
			-2 = input map error
			-3 = output map write error
			
	NOTE:	Maps values: divides range of DCELL/FCELL values in the input
	  			into N intervals of user specified, equal width
				Each interval will become a category in the output map.
			Range of categories can be cut by passing 'min' and 'max'
          		paremeters != -1. All values outside the range in the input map 
				will be replaced with NULL-values in the output map.
			The last category in the output map might end up wider than the
				actual maximum value in the input map.
			To improve legibility of map legends, the intervals will start at
				an integer offset, if 'round_cat=1' (DCELL and FCELL maps only)
*/
int GT_set_cats_width (char *name, char *mapset, char *output,
					double rmin, double rmax, double width, int round_cat, 
					int intout, int print_progress) {
	int fd;					

	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (-1);	
  	}
    								
	if (G_raster_map_is_fp (name, mapset)) {
		return (GT_set_f_cats_width (name, mapset, output, rmin, rmax, 
									width, round_cat, intout, print_progress));
		
    } else {
    	return (GT_set_c_cats_width (name, mapset, output, (int) rmin, (int) rmax, 
									(int) width, print_progress));
    }
	
    return (0);						
}


/* GT_set_c_cats_width () */
/* Create a new CELL raster map with categories ranging from 0 .. N
			Let the user specify category width. N will then be determined
			automatically.

   ARGS:	name = name of GRASS raster map to read in
           mapset = mapset to read map from (leave empty or NULL 
		         	for first matching map in search path)
			output = name of result raster map (will always be stored
                 	in the user's current mapset).
			min, max = set to different values to cut the output range
         			(see NOTE)
			width = width of each category
			print_progress = set this to '1' to have a status display
   RETURN:	number of categories created (N)
     		0 = no categories created
			-1 = input map not in CELL format
			-2 = input map error
			-3 = output map write error
			
	NOTE:	Maps values: divides the entire range of CELL values in the input
	  			map into N categories of user-specified width.
			Range of categories can be cut by passing 'min' and 'max'
          		paremeters != -1. All values outside the range in the input map 
				will be replaced with NULL-values in the output map.
*/
int GT_set_c_cats_width (char *name, char *mapset, char *output, 
						int rmin, int rmax, int width, int print_progress) {
	int fd, outfd;
	int error;
	struct Categories cats;															
	int i,j;
	int rows, cols;
	CELL *cellbuf, *outcellbuf;
	CELL value;
	int divisor;
	int min, max;	
	int num;	
	char *strbuf, *strbuf2;
	/* a flag to control quantification of the output map */
	int cutrange = 0;
	
	rows = G_window_rows ();
	cols = G_window_cols ();
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {		
		return (-2);	
  	}
	
	/* try to open new CELL map for output */
	outfd = G_open_cell_new (output);
 	if ( fd < 0 ) {
		return (-3);	
  	}	
    	
	if (G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		G_close_cell (outfd);
		return (-1);
    }	
	
	if ( width < 2 ) {
		G_fatal_error ("GT_set_c_cats_width(): Width of categories must be at least 2.");
	}

	G_init_cats (0, "", &cats);
		
	/* FIRST PASS: analyse raster file and get min and max ints */
	GT_get_c_range (name, mapset, &min, &max, print_progress);	
	
	/* check, if user wants to cut range and if min and max have been
	   set to sane values */
	if ( rmin != rmax ) {
		cutrange = 1; /* user wants to cut. Let's check ... */
		if ( rmin > rmax ) {
			G_warning ("User specified 'min' of input range larger than 'max'. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmin < min) && (cutrange == 1)) {
			G_warning ("User specified 'min' of input range smaller than minimum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmax > max) && (cutrange == 1)) {
			G_warning ("User specified 'max' of input range larger than maximum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
	}
	
	/* SECOND PASS: remap values, create labels and write output map */
	cellbuf = G_allocate_raster_buf (CELL_TYPE);
	outcellbuf = G_allocate_raster_buf (CELL_TYPE);
	if (print_progress) {
		fprintf (stdout, "Mapping categories: \n");
	}	
	divisor = width;
	num = (max - min) / width;
	if ( num < 2 ) {
		G_fatal_error ("GT_set_c_cats_width(): Category number must be at least 2.");
	}
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, cellbuf, i, CELL_TYPE);	
		for (j=0; j<cols; j++) {
			/* check for NULL values and update min and max */			
			if ( G_is_c_null_value (&cellbuf[j]) == 1) {
				/* pass NULL values through to output map */
				G_set_c_null_value (&outcellbuf[j],1);
			} else {
				/* check if any range cutting has to be done */
				if ( cutrange ) {
					if ( (cellbuf[j] < rmin) || (cellbuf[j] > rmax) ) {
						G_set_c_null_value (&outcellbuf[j],1);
					} else {
						/* map */
						value = abs(min) + cellbuf[j] + 1;						
						outcellbuf[j] = (int) ceil ( (double) value / (double) divisor ) - 1;
						/* last category may be slightly larger */
						if (outcellbuf[j] > (num-1)) {
							outcellbuf[j] = (num-1);
						}
					}
				} else {
					/* just mapped value */
					value = abs(min) + cellbuf[j] + 1;						
					outcellbuf[j] = (int) ceil ( (double) value / (double) divisor ) - 1;
					/* last category may be slightly larger */
					if (outcellbuf[j] > (num-1)) {
						outcellbuf[j] = (num-1);
					}					
				}
			}
		}
		/* write output row */
		G_put_c_raster_row (outfd,outcellbuf);
		if (print_progress) {
			G_percent (i,rows-1,1);
			fflush (stdout);
		}
	}
	if (print_progress) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}
	
	/* create categories and category labels */
	strbuf = G_calloc (255, sizeof(char));
	strbuf2 = G_calloc (255, sizeof(char));
	if ( cutrange ) {
		sprintf (strbuf,"Categories mapped from %i to %i. Cut range = %i to %i ", 
				 min, max, rmin, rmax);
	} else {
			sprintf (strbuf,"Categories mapped from %i to %i.", min , max);
	}
	G_set_cats_title (strbuf, &cats);
	for (i=0; i<num; i++) {
		sprintf (strbuf,"%i to %i", (min + i*divisor), ((min + i*divisor) + divisor));
		/* last category may be slightly wider */
		if (i == num-1 ) {
			sprintf (strbuf,"%i to %i", (min + i*divisor), max);
		}
		G_set_cat (i, strbuf, &cats);
	}
	
	G_free (cellbuf);
	G_close_cell (fd);
	G_free (outcellbuf);
	G_close_cell (outfd);
	/* write category file */
	G_write_cats (output, &cats);
	/* write some comments into the history file */
	sprintf (strbuf,"%s@%s",name,mapset);
	if ( rmin != rmax ) {
		sprintf (strbuf2,"r.categorise mode=width,%i min=%i max=%i",width, rmin, rmax);
	} else {
		sprintf (strbuf2,"r.categorise mode=width,%i",width);
	}
	GT_write_hist (output,strbuf,"Original INT data range categorised using fixed width intervals.",
					strbuf2);
	G_free (strbuf);
	G_free (strbuf2);
	
	return (num);	
}


/* GT_set_f_cats_width () */
/* Create a new raster map with categories ranging from 0 .. N
			Let the user specify category width. N will then be
 			determined automatically.

   ARGS:	name = name of GRASS raster map to read in
           mapset = mapset to read map from (leave empty or NULL 
		         	for first matching map in search path)
			output = name of result raster map (will always be stored
                 	in the user's current mapset).
			min, max = set to different values to cut the output range
         			(see NOTE)
			width = width of categories to generate
			round_cat = set to '1' to start category 0 at the nearest integer
						value (floor).
			intout = set to '1' to force integer (CELL) map output.
			print_progress = set this to '1' to have a status display
   RETURN:	number of categories created (N)
     		0 = no categories created
			-1 = input map not in CELL format
			-2 = input map error
			-3 = output map write error
			
	NOTE:	Maps values: divides range of DCELL/FCELL values in the input
	  			into N intervals of user specified, equal width
				Each interval will become a category in the output map.
			Range of categories can be cut by passing 'min' and 'max'
          		paremeters != -1. All values outside the range in the input map 
				will be replaced with NULL-values in the output map.
			The last category in the output map might end up wider than the
				actual maximum value in the input map.
			To improve legibility of map legends, the intervals will start at
				an integer offset, if 'round_cat=1'
*/
int GT_set_f_cats_width (char *name, char *mapset, char *output, 
						 double rmin, double rmax, double width, int round_cat, 
						 int intout, int print_progress) {
	int fd, outfd;
	int error;
	int num;
	struct Categories cats;															
	int i,j;
	int rows, cols;
	DCELL *dcellbuf;
	CELL *outcellbuf;
	DCELL *doutcellbuf;
	DCELL dvalue;
	DCELL dmin, dmax;
	FCELL fmin, fmax;
	double divisor;
	double min, max;		
	char *strbuf, *strbuf2;
	int cutrange = 0;
	int map_type;
	
	rows = G_window_rows ();
	cols = G_window_cols ();
	
	/* to disable compiler warnings */
	outcellbuf = NULL;
	doutcellbuf = NULL;
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {		
		return (-2);	
  	}
	 
	/* determine mode of output map */   	
	if (!G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (-1);
    }	
	map_type = G_raster_map_type (name, mapset);
	G_set_fp_type (map_type);
	
	/* open new map for output */
	if ( intout == 1 ) outfd = G_open_cell_new (output);
		else outfd = G_open_fp_cell_new (output);
 	if ( outfd < 0 ) {
		return (-3);	
  	}				
			
	if ( width <= 0 ) {
		G_fatal_error ("GT_set_f_cats_width(): Width of categories must be > 0.");
	}
		
	/* FIRST PASS: analyse raster file and get min and max ints */
	GT_get_f_range (name, mapset, &min, &max, print_progress);	
	
	/* check, if user wants to cut range and if min and max have been
	   set to sane values */
	if ( rmin != rmax ) {
		cutrange = 1; /* user wants to cut. Let's check ... */
		if ( rmin > rmax ) {
			G_warning ("User specified 'min' of input range larger than 'max'. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmin < min) && (cutrange == 1)) {
			G_warning ("User specified 'min' of input range smaller than minimum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmax > max) && (cutrange == 1)) {
			G_warning ("User specified 'max' of input range larger than maximum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
	}
	
	/* do we want rounded lower category boundaries? */
	if ( round_cat == 1 ) {
		min = floor (min);
	}	
	
	/* SECOND PASS: map values, create labels and write output map */
	dcellbuf = G_allocate_raster_buf (DCELL_TYPE);
	if ( intout == 1) outcellbuf = G_allocate_raster_buf (CELL_TYPE);
		else {
			doutcellbuf = G_allocate_raster_buf (DCELL_TYPE);
			outcellbuf = NULL;
		}
	if (print_progress) {
		fprintf (stdout, "Mapping categories: \n");
	}
	divisor = width;
	num = (int) ((max - min) / width);
	if ((width * num) < (max - min)) {
		num ++;
	}
	if ( num < 2 ) {
		G_fatal_error ("GT_set_f_cats_width(): Category number must be at least 2.");
	}
		
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, dcellbuf, i, DCELL_TYPE);	
		for (j=0; j<cols; j++) {
			/* check for NULL values and update min and max */			
			if ( G_is_d_null_value (&dcellbuf[j]) == 1) {
				/* pass NULL values through to output map */
				if ( intout == 1 ) G_set_c_null_value (&outcellbuf[j],1);
					else G_set_d_null_value (&doutcellbuf[j],1);				
			} else {
				/* check if any range cutting has to be done */
				if ( cutrange ) {
					if ( (dcellbuf[j] < rmin) || (dcellbuf[j] > rmax) ) {
						if ( intout == 1 ) G_set_c_null_value (&outcellbuf[j],1);
							else G_set_d_null_value (&doutcellbuf[j],1);
					} else {
						dvalue = dcellbuf[j] - min;
						if ( intout == 1) outcellbuf[j] = (CELL) floor (dvalue / divisor);
							else doutcellbuf[j] = dcellbuf[j];
						if ( intout == 1 ) {
							if ( dvalue == max ) {
								outcellbuf[j] --;
							}
						}						
					}
				} else {
					/* just write mapped value */
					dvalue = dcellbuf[j] - min;
					if ( intout == 1) outcellbuf[j] = (CELL) floor (dvalue / divisor);
						else doutcellbuf[j] = dcellbuf[j];
					if ( intout == 1 ) {
						if ( dvalue == max ) {
							outcellbuf[j] --;
						}					
					}
				}
			}
		}
		/* write output row */
		if ( intout == 1) G_put_c_raster_row (outfd,outcellbuf);
			else G_put_d_raster_row (outfd,doutcellbuf);
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}
	}
	if (print_progress) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}
	/* FIRST CLOSE RASTERS! */
	G_free (dcellbuf);
	G_close_cell (fd);
	if ( intout == 1) G_free (outcellbuf);
		else G_free (doutcellbuf);
	G_close_cell (outfd);			
	
	/* create categories and category labels */
	G_init_cats (num, "", &cats);	
	strbuf = G_calloc (255,sizeof(char));
	strbuf2 = G_calloc (255,sizeof(char));
	if ( cutrange ) {
		sprintf (strbuf,"Categories mapped from %.3f to %.3f. Cut range = %.3f to %.3f ", 
				 min, max, rmin, rmax);
	} else {
			sprintf (strbuf,"Categories mapped from %.3f to %.3f", min , max);
	}
	G_set_cats_title (strbuf, &cats);
	for (i=0; i<num; i++) {		
		sprintf (strbuf,"%2$.*1$f to %3$.*1$f", GT_DECDIGITS, (min + i*divisor), ((min + i*divisor) + divisor));
		if ( i == num-1 ) {
			sprintf (strbuf,"%2$.*1$f to %3$.*1$f", GT_DECDIGITS, (min + i*divisor), 
					max);
		}		
		if ( intout == 1 ) G_set_cat (i, strbuf, &cats); /* integer cats */
			else {
				/* create floating point category ranges */
				if ( map_type == DCELL_TYPE ) {
					dmin = (min + i*divisor);
					dmax = (min + i*divisor) + divisor;
					if ( i == num-1 ) {						
						dmax = (DCELL) max; /* last category always has max as roof */
					}					
					G_set_d_raster_cat (&dmin, &dmax, strbuf, &cats);
				}
				if ( map_type == FCELL_TYPE ) {
					fmin = (min + i*divisor);
					fmax = (min + i*divisor) + divisor;
					if ( i == num-1 ) {
						fmax = (FCELL) max; /* last category always has max as roof */
					}					
					G_set_f_raster_cat (&fmin, &fmax, strbuf, &cats);
				}
			}
	}
	
	/* write category file */
	G_write_cats (output, &cats);
	
	/* write some comments into the history file */
	sprintf (strbuf,"%s@%s",name,mapset);
	if ( rmin != rmax ) {
		if ( round_cat == 0) {
			sprintf (strbuf2,"r.categorise mode=width,%.3f min=%.3f max=%.3f",width, rmin, rmax);
		} else {
			sprintf (strbuf2,"r.categorise mode=rwidth,%.3f min=%.3f max=%.3f",width, rmin, rmax);
		}
	} else {
		if ( round_cat == 0) {
			sprintf (strbuf2,"r.categorise mode=width,%.3f",width);
		} else {
			sprintf (strbuf2,"r.categorise mode=rwidth,%.3f",width);
		}			
	}
	GT_write_hist (output,strbuf,"Original FP data range categorised using fixed width intervals.",
					strbuf2);
	
	G_free (strbuf);
	G_free (strbuf2);
	
	return (num);							 							 							 
}


/* GT_set_c_cats_scale () */
/* Create a new CELL raster map with categories ranging from 0 .. N

   ARGS:	name = name of GRASS raster map to read in
           mapset = mapset to read map from (leave empty or NULL 
		         	for first matching map in search path)
			output = name of result raster map (will always be stored
                 	in the user's current mapset).
			min, max = set to different values to cut the output range
         			(see NOTE)
			print_progress = set this to '1' to have a status display
   RETURN:	number of categories created (N)
     		0 = no categories created
			-1 = input map not in CELL format
			-2 = input map error
			-3 = output map write error
			
	NOTE:	Rescales values: Smallest integer value found in the map will be
				set to '0', largest integer will be 'N'.
            	Categories and labels will be automatically generated
 				for the entire range 0 .. N (!)
			Range of categories can be cut by passing 'min' and 'max'
          		paremeters != -1. All values outside the range in the input map 
				will be replaced with NULL-values in the output map.
*/
int GT_set_c_cats_scale (char *name, char *mapset, char *output, 
						int rmin, int rmax, int print_progress) {
	int fd, outfd;
	int error;
	struct Categories cats;															
	int i,j;
	int rows, cols;
	CELL *cellbuf, *outcellbuf;
	int categories;
	int min, max;		
	char *strbuf, *strbuf2;
	/* a flag to control quantification of the output map */
	int cutrange = 0;
	
	rows = G_window_rows ();
	cols = G_window_cols ();
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {		
		return (-2);	
  	}
	
	/* try to open new CELL map for output */
	outfd = G_open_cell_new (output);
 	if ( outfd < 0 ) {
		return (-3);	
  	}	
    	
	if (G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		G_close_cell (outfd);
		return (-1);
    }
		
	/* FIRST PASS: analyse raster file and get min and max ints */
	GT_get_c_range (name, mapset, &min, &max, print_progress);
	
	/* check, if user wants to cut range and if min and max have been
	   set to sane values */
	if ( rmin != rmax ) {
		cutrange = 1; /* user wants to cut. Let's check ... */
		if ( rmin > rmax ) {
			G_warning ("User specified 'min' of input range larger than 'max'. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmin < min) && (cutrange == 1)) {
			G_warning ("User specified 'min' of input range smaller than minimum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmax > max) && (cutrange == 1)) {
			G_warning ("User specified 'max' of input range larger than maximum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
	}
	
	/* SECOND PASS: rescale values, create labels and write output map */
	cellbuf = G_allocate_raster_buf (CELL_TYPE);
	outcellbuf = G_allocate_raster_buf (CELL_TYPE);
	if (print_progress) {
		fprintf (stdout, "Rescaling categories: \n");
	}		
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, cellbuf, i, CELL_TYPE);	
		for (j=0; j<cols; j++) {
			/* check for NULL values and update min and max */			
			if ( G_is_c_null_value (&cellbuf[j]) == 1) {
				/* pass NULL values through to output map */
				G_set_c_null_value (&outcellbuf[j],1);
			} else {
				/* check if any range cutting has to be done */
				if ( cutrange ) {
					if ( (cellbuf[j] < rmin) || (cellbuf[j] > rmax) ) {
						G_set_c_null_value (&outcellbuf[j],1);
					} else {
						outcellbuf[j] = cellbuf[j] + abs (min);
					}
				} else {
					/* just write rescaled value */
					outcellbuf[j] = cellbuf[j] + abs (min);
				}
			}
		}
		/* write output row */
		G_put_c_raster_row (outfd,outcellbuf);
		if (print_progress) {
			G_percent (i, rows-1,1);
			fflush (stdout);
		}
	}		
	if (print_progress) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}
	
	/* create categories and category labels */
	G_init_cats (0, "", &cats);
	strbuf = G_calloc (255,sizeof(char));
	strbuf2 = G_calloc (255,sizeof(char));
	if ( cutrange ) {
		sprintf (strbuf,"Categories rescaled from %i to %i. Cut range = %i to %i ", 
				 min, max, rmin, rmax);
	} else {
			sprintf (strbuf,"Categories rescaled from %i to %i.", min , max);
	}
	G_set_cats_title (strbuf, &cats);
	categories = abs(min) + max + 1;
	for (i=0; i < categories; i++) {
		sprintf (strbuf,"%i",i);
		G_set_cat (i, strbuf, &cats);
	}	
	G_free (cellbuf);
	G_close_cell (fd);
	G_free (outcellbuf);
	G_close_cell (outfd);
	
	/* write category file */
	G_write_cats (output, &cats);
	
	/* write some comments into the history file */
	sprintf (strbuf,"%s@%s",name,mapset);
	if ( rmin != rmax ) {
		sprintf (strbuf2,"r.categorise mode=scale min=%i max=%i",rmin, rmax);
	} else {
		sprintf (strbuf2,"r.categorise mode=scale");
	}
	GT_write_hist (output,strbuf,"Original INT data range rescaled from 0 to N.",
					strbuf2);
	G_free (strbuf);
	G_free (strbuf2);
	
	return (categories);	
}


/* GT_set_f_cats_round () */
/* Create a new CELL raster map with categories ranging from 0 .. N
			Input map must be of type DCELL or FCELL.
			Values in the input map are rounded to the nearest integer.

   ARGS:	name = name of GRASS raster map to read in
           mapset = mapset to read map from (leave empty or NULL 
		         	for first matching map in search path)
			output = name of result raster map (will always be stored
                 	in the user's current mapset).
			min, max = set to different values to cut the output range
         			(see NOTE)
			print_progress = set this to '1' to have a status display

   RETURN:	number of categories created (N)
     		0 = no categories created
			-1 = input map not in DCELL/FCELL format
			-2 = input map error
			-3 = output map write error
			
	NOTE:	Range of categories can be cut by passing 'min' and 'max'
          	paremeters != -1. All values outside the range in the input map 
			will be replaced with NULL-values in the output map.
			This function uses the rintf() function for rounding, which
			means that half-way values are rounded to the nearest even
			integer.
			The output map will contain as many categories as there can
			be between the minimum and maximum rounded values in the input map.
			Categories defined in the input map are disregarded.

*/
int GT_set_f_cats_round (char *name, char *mapset, char *output, 
						 double rmin, double rmax, int print_progress) {
	int fd, outfd;
	int error;
	struct Categories cats;															
	int n_cats = 0;	
	int i,j;
	int rows, cols;
	DCELL *dcellbuf;
	DCELL dvalue;
	CELL *outcellbuf;
	char *strbuf, *strbuf2;
	double min, max;
	/* a flag to control quantification of the output map */
	int cutrange = 0;	
	
	rows = G_window_rows ();
	cols = G_window_cols ();
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (-2);	
  	}
	
	/* try to open new CELL map for output */
	outfd = G_open_cell_new (output);
 	if ( outfd < 0 ) {
		return (-3);	
  	}		
    	
	if (! G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (-1);
    }
				
	dcellbuf = G_allocate_raster_buf (DCELL_TYPE);
	outcellbuf = G_allocate_raster_buf (CELL_TYPE);

	/* FIRST PASS: analyse raster file and get min and max ints */
	GT_get_f_range (name, mapset, &min, &max, print_progress);
	
	/* check, if user wants to cut range and if min and max have been
	   set to sane values */
	if ( rmin != rmax ) {
		cutrange = 1; /* user wants to cut. Let's check ... */
		if ( rmin > rmax ) {
			G_warning ("User specified 'min' of input range larger than 'max'. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmin < min) && (cutrange == 1)) {
			G_warning ("User specified 'min' of input range smaller than minimum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmax > max) && (cutrange == 1)) {
			G_warning ("User specified 'max' of input range larger than maximum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
	}
	
	/* SECOND PASS: do the rounding */
	if (print_progress) {
		fprintf (stdout, "Rounding floating point cells: \n");
	}	
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, dcellbuf, i, DCELL_TYPE);	
		/* write entire row of output map as NULL files, first */
		G_set_c_null_value (outcellbuf, cols);
		for (j=0; j<cols; j++) {
			/* check for NULL value */			
			if ( !G_is_d_null_value (&dcellbuf[j]) == 1) {				
				dvalue = dcellbuf[j];
				/* check for cutrange */
				if ( (cutrange == 0) || ((dvalue >= rmin) && (dvalue <= rmax)) ) {
					/* round floating point value */
					outcellbuf[j] = (CELL) rint (dcellbuf[j]);
				}
			}
		}
		/* write one line of output map */
		G_put_c_raster_row (outfd,outcellbuf);
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}		
	}	
	if (print_progress) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}	
	G_free (dcellbuf);
	G_close_cell (fd);
	G_free (outcellbuf);
	G_close_cell (outfd);
	
	/* write N category labels to new output map */
	n_cats = ((int) ceil (max) - (int) floor (min)) + 1;
	G_init_cats (n_cats, "", &cats);		
	strbuf = G_calloc (255,sizeof(char));
	for (i=0; i<n_cats; i++) {
		sprintf (strbuf,"%i",i);
		G_set_cat (i, strbuf, &cats);
	}
	sprintf (strbuf,"Rounded values from %s@%s.",name,mapset);
	G_set_cats_title (strbuf,&cats);
	G_write_cats (output, &cats);		
	
	/* write some comments into the history file */
	sprintf (strbuf,"%s@%s",name,mapset);
	strbuf2 = G_calloc (255,sizeof(char));
	if ( rmin != rmax ) {
		sprintf (strbuf2,"r.categorise mode=round min=%f max=%f",rmin, rmax);
	} else {
		sprintf (strbuf2,"r.categorise mode=round");
	}	
	GT_write_hist (output,strbuf,"Original FP data range categorised by rounding values.",
					strbuf2);
	G_free (strbuf);
	G_free (strbuf2);
	
	return (n_cats);
}


/* GT_set_f_cats_trunc () */
/* Create a new CELL raster map with categories ranging from 0 .. N
			Input map must be of type DCELL or FCELL.
			Values in the input map are truncated integer parts.

   ARGS:	name = name of GRASS raster map to read in
           mapset = mapset to read map from (leave empty or NULL 
		         	for first matching map in search path)
			output = name of result raster map (will always be stored
                 	in the user's current mapset).
			min, max = set to different values to cut the output range
         			(see NOTE)
			print_progress = set this to '1' to have a status display

   RETURN:	number of categories created (N)
     		0 = no categories created
			-1 = input map not in DCELL/FCELL format
			-2 = input map read error
			-3 = output map write error
			
	NOTE:	Range of categories can be cut by passing 'min' and 'max'
          	paremeters != -1. All values outside the range in the input map 
			will be replaced with NULL-values in the output map.
			The output map will contain as many categories as there can
			be between the minimum and maximum truncated values in the input map.
			Categories defined in the input map are disregarded.
*/
int GT_set_f_cats_trunc (char *name, char *mapset, char *output, 
						 double rmin, double rmax, int print_progress) {
								 
	int fd, outfd;
	int error;
	struct Categories cats;															
	int n_cats = 0;	
	int i,j;
	int rows, cols;
	DCELL *dcellbuf;
	DCELL dvalue;
	CELL *outcellbuf;
	char *strbuf, *strbuf2;
	double min, max;
	/* a flag to control quantification of the output map */
	int cutrange = 0;
	
	rows = G_window_rows ();
	cols = G_window_cols ();
	
	/* find first match in searchpath, if no path given */
	if ((mapset == NULL) || (strcmp (mapset,"") == 0)) {
		mapset =  G_find_cell (name,"");
	}
	
	/* check for valid map */
	fd = G_open_cell_old (name, mapset);
 	if ( fd < 0 ) {
		return (-2);	
  	}
	
	/* try to open new CELL map for output */
	outfd = G_open_cell_new (output);
 	if ( outfd < 0 ) {
		return (-3);	
  	}		
    	
	if (! G_raster_map_is_fp (name, mapset)) {
		G_close_cell (fd);
		return (-1);
    }
				
	/* FIRST PASS: analyse raster file and get min and max ints */
	GT_get_f_range (name, mapset, &min, &max, print_progress);
	
	/* check, if user wants to cut range and if min and max have been
	   set to sane values */
	if ( rmin != rmax ) {
		cutrange = 1; /* user wants to cut. Let's check ... */
		if ( rmin > rmax ) {
			G_warning ("User specified 'min' of input range larger than 'max'. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmin < min) && (cutrange == 1)) {
			G_warning ("User specified 'min' of input range smaller than minimum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
		if ( (rmax > max) && (cutrange == 1)) {
			G_warning ("User specified 'max' of input range larger than maximum CELL value. Ignoring.");
			cutrange = 0; /* cannot cut this range, so turn it off */
		}
	}
	
	/* SECOND PASS: do the truncation */
	dcellbuf = G_allocate_raster_buf (DCELL_TYPE);
	outcellbuf = G_allocate_raster_buf (CELL_TYPE);
	if (print_progress) {
		fprintf (stdout, "Truncating floating point cells: \n");
	}	
	for (i=0; i< rows; i++) {
		error = G_get_raster_row (fd, dcellbuf, i, DCELL_TYPE);	
		/* write entire row of output map as NULL files, first */
		G_set_c_null_value (outcellbuf, cols);
		for (j=0; j<cols; j++) {
			/* check for NULL value */			
			if ( !G_is_d_null_value (&dcellbuf[j]) == 1) {								
				dvalue = dcellbuf[j];
				/* check for cutrange */
				if ( (cutrange == 0) || ((dvalue >= rmin) && (dvalue <= rmax)) ) {
					/* truncate floating point value */
					outcellbuf[j] = (CELL) dcellbuf[j];
				}
			}
		}
		/* write one line of output map */
		G_put_c_raster_row (outfd,outcellbuf);
		if (print_progress) {
			G_percent (i, rows-1, 1);
			fflush (stdout);
		}		
	}	
	if (print_progress) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}	
	G_free (dcellbuf);
	G_close_cell (fd);
	G_free (outcellbuf);
	G_close_cell (outfd);
	
	/* write N category labels to new output map */
	n_cats = ((int) max - (int) min) + 1;
	G_init_cats (n_cats, "", &cats);		
	strbuf = G_calloc (255,sizeof(char));
	for (i=0; i<n_cats; i++) {
		sprintf (strbuf,"%i",i);
		G_set_cat (i, strbuf, &cats);
	}
	sprintf (strbuf,"Truncated values from %s@%s.",name,mapset);
	G_set_cats_title (strbuf,&cats);
	G_write_cats (output, &cats);
	
	/* write some comments into the history file */
	sprintf (strbuf,"%s@%s",name,mapset);	
	strbuf2 = G_calloc (255,sizeof(char));
	if ( rmin != rmax ) {
		sprintf (strbuf2,"r.categorise mode=trunc min=%f max=%f",rmin, rmax);
	} else {
		sprintf (strbuf2,"r.categorise mode=trunc");
	}	
	GT_write_hist (output,strbuf,"Original FP data range categorised by rounding values.",
					strbuf2);		

	G_free (strbuf);
	G_free (strbuf2);
	
	return (n_cats);
}

/* GT_write_hist () */
/* A convenience function to add some simple metadata (history) to
   a GRASS raster file in the user's current mapset.

   ARGS: 	name = name of raster file
			source = description of source file (e.g. raster file from
				which the current one was derived)
			desc = a one-line description of the data
			comment = any one-line comment

   NOTE:	all char* arguments except 'name' may be NULL, in which
			case the corresponding history entries will be left empty.
			ALL HISTORY ENTRIES MAY BE AT MOST 80 CHARS LONG !!!
*/
int GT_write_hist (char *name, char* source, char *desc, char *comment) {
	
	struct History hist;
	int error;
		
	error = G_short_history (name, "raster", &hist);		
	if (error != 1) return (error);
		
	if ( source != NULL) strcpy (hist.datsrc_1, source);
	if ( desc != NULL ) strcpy (hist.keywrd, desc);
	hist.edlinecnt = 1;
	if ( comment != NULL) strcpy (hist.edhist[0], comment);	
	
	error = G_write_history (name, &hist);
	if (error != 0) return (error);
	
	return (0);	
}

/* GT_set_decdigits () */
/* This function sets the global variable GT_DECDIGITS */
/* which controls the number of decimal digits displayed */
/* in the raster history files and category labels. */
void GT_set_decdigits (unsigned int digits) {
	GT_DECDIGITS = digits;
}
