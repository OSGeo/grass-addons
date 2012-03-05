/* CAT_ENGINE.H */

/* Part of the GRASS Toolkit (GT) functions collection */
/* Purpose:	provide functions for handling categories in GRASS raster maps. */

/* Usage:	1. call GT_set_decdigits (unsigned int digits) (!) to set decimal precision (e.g. 3) */
/*		2. use GT_get_stats () on a GRASS raster map to get basic category information */
/*            	3. use GT_get_* functions for more information */
/*		4. use GT_set_* functions to create categories for a raster map */
/*                 functions GT_set_f_* are for floating point rasters (FCELL ord DCELL) */
/*		   functions GT_set_c_* are for integer rasters */
/*                 functions GT_set_* determine mode automatically */
/*		5. the output map will always be a CELL map with values 0..N, each being a category */
/*		   output map is always fully categorised, i.e. each cell a category or NULL */
/*              Take a look at 'cat_engine.c' for detailed descriptions of functions */


/* This file is licensed under the GPL (version 2 ) */
/* see: http://www.gnu.org/copyleft/gpl.html */

/* (c) Benjamin Ducke 2004 */
/* benducke@compuserve.de */

#ifndef GT_CAT_ENGINE_H
#define GT_CAT_ENGINE_H

unsigned int GT_DECDIGITS; /* number of decimal digits for statistics/logfile */

/* USER MUST CALL THIS FUNCTION FIRST */
/* to determine number of decimal digits in history files */
/* and category labels. Otherwise it will be garbage! */
void GT_set_decdigits (unsigned int digits);

/* functions for any type of GRASS raster maps */
/* these determine the map mode and automatically call map type */
/*   specific functions below */
int GT_get_stats (char *name, char *mapset, long *null_count, 
							long *nocat_count, int print_progress);
int GT_get_range (char *name, char *mapset, double *min, 
							double *max, int print_progress);							
long *GT_get_counts (char *name, char *mapset, int print_progress);
char **GT_get_labels (char *name, char *mapset);
int GT_set_cats_only (char *name, char *mapset, char *output, int fp, int print_progress);
int GT_set_cats_num (char *name, char *mapset, char *output,
					double rmin, double rmax, int num, int intout, int print_progress);
int GT_set_cats_width (char *name, char *mapset, char *output,
					double rmin, double rmax, double width, int round_cat, 
					int intout, int print_progress);

/* functions for categories in CELL files */
int GT_get_c_stats (char *name, char *mapset, long *null_count, 
							long *nocat_count, int print_progress);
int GT_get_c_range (char *name, char *mapset, int *min, 
							int *max, int print_progress);							
long *GT_get_c_counts (char *name, char *mapset, int print_progress);
char **GT_get_c_labels (char *name, char *mapset);
int GT_set_c_cats_only (char *name, char *mapset, char *output, int print_progress);
int GT_set_c_cats_scale (char *name, char *mapset, char *output, 
						 int rmin, int rmax, int print_progress);
int GT_set_c_cats_num (char *name, char *mapset, char *output, 
						 int rmin, int rmax, int num, int print_progress);
int GT_set_c_cats_width (char *name, char *mapset, char *output, 
						 int rmin, int rmax, int width, int print_progress);
						 
/* functions for categories in DCELL/FCELL files */
/* all of these work with double (DCELL) precision internally */
int GT_get_f_stats (char *name, char *mapset, long *null_count, 
							long *nocat_count, int print_progress);
int GT_get_f_range (char *name, char *mapset, double *min, 
							double *max, int print_progress);														
long *GT_get_f_counts (char *name, char *mapset, int print_progress);
char **GT_get_f_labels (char *name, char *mapset);
int GT_set_f_cats_only (char *name, char *mapset, char *output, int fp, int print_progress);
int GT_set_f_cats_round (char *name, char *mapset, char *output, 
						 double rmin, double rmax, int print_progress);
int GT_set_f_cats_trunc (char *name, char *mapset, char *output, 
						 double rmin, double rmax, int print_progress);
int GT_set_f_cats_num (char *name, char *mapset, char *output, 
						 double rmin, double rmax, int num, int intout, int print_progress);
int GT_set_f_cats_width (char *name, char *mapset, char *output, 
						 double rmin, double rmax, double width, int round_cat, 
						 int intout, int print_progress);

/* auxillary functions */
int GT_write_hist (char *name, char* source, char *desc, char *comment);

#endif /* GT_CAT_ENGINE_H */
