/* s.report */
/* Show histogram of vector object distribution over raster map values. */

#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <math.h>
#include <time.h>

#include <grass/gis.h>
#include <grass/Vect.h>

#include "gt/rowcache.h"
#include "gt/cat_engine.h"
#include "gt/gstats_gain.h"

#define PROGVERSION 1.1

extern int errno;
int CACHESIZE;

char *PROGNAME;

void delete_tmpfile ( char *tmpfile ) {

	int error;

		error = G_remove ("cell",tmpfile);
		if ( error < 1 ) {
			G_warning ("Could not delete cell element of temporary file (%s).", tmpfile);
		}
		error = G_remove ("cellhd",tmpfile);
		if ( error < 1 ) {
			G_warning ("Could not delete cellhd element of temporary file (%s).", tmpfile);
		}
		error = G_remove ("cats",tmpfile);
		if ( error < 1 ) {
			G_warning ("Could not delete cats element of temporary file (%s).", tmpfile);
		}
		error = G_remove ("hist",tmpfile);
		if ( error < 1 ) {
			G_warning ("Could not delete hist element of temporary file (%s).", tmpfile);
		}
		error = G_remove ("cell_misc",tmpfile);
		if ( error < 1 ) {
			G_warning ("Could not delete cell_misc element of temporary file (%s).", tmpfile);
		}		
}
/* create the actual report */
void do_report_CELL ( char *map, char *mapset, char *sites,
					int precision, int null_flag, int uncat_flag,
					int all_flag, int quiet_flag, int skip_flag,
				  	char *logfile, int background, int gain, int show_progress) {
    	CELL *cellbuf;
	struct Cell_head region;
	GT_Row_cache_t *cache;
	unsigned long row_idx, col_idx;	
	int fd;
	unsigned long i,j,k;
	unsigned long no_sites;
	FILE *lp;	
	unsigned long nrows, ncols;
	unsigned long *share_smp = NULL; /* array that keeps percentage of sites */
	double total = 0;
	double map_total = 0;
	double kvamme_gain;
	long null_count = 0; /* keeps count of sites on NULL cells */
	long nocat_count = 0;
	/* category counts and descriptions */
	int cats;
	char **cats_description; /* category labels */
	long *cat_count; /* category counts */
	long null_count_map; /* number of NULL cells in input map */
	long nocat_count_map; /* number of cells that do not fall into the category range [0 .. n] */		
	int debug_mode = 0;		/* 1 to enable writing additional output to logfile */
	time_t systime;

	char errmsg [200];
	struct Map_info in_vect_map;
  	struct line_pnts *vect_points;
	double x,y,z;
	int n_points = 1;
	int cur_type;
	

	/* get current region */
	G_get_window (&region);
	nrows = G_window_rows ();
	ncols = G_window_cols ();	
	
	/* check logfile */
	if (logfile != NULL) {
		debug_mode = 1;	
		if ( !G_legal_filename (logfile) ) {
			delete_tmpfile (map);
			G_fatal_error ("Please specify a legal filename for the logfile.\n");
		}
		/* attempt to write to logfile */
		if ( (lp = fopen ( logfile, "w+" ) ) == NULL )	{
			delete_tmpfile (map);
			G_fatal_error ("Could not create logfile.\n");
		}
		/* we want unbuffered output for the logfile */
		setvbuf (lp,NULL,_IONBF,0);	
		fprintf (lp,"This is %s, version %.2f\n",PROGNAME, PROGVERSION);
		systime = time (NULL);
		fprintf (lp,"Started on %s",ctime(&systime));
		fprintf (lp,"\tlocation    = %s\n",G_location());
		fprintf (lp,"\tmapset      = %s\n",G_mapset());
		fprintf (lp,"\tinput map   = %s\n",map);
		fprintf (lp,"\tsample file = %s\n",sites);
	} else {		
		/* log output to stderr by default */
		lp = stderr;
	}

  	if (1 > Vect_open_old (&in_vect_map, sites, "")) {
		delete_tmpfile (map);
    		sprintf (errmsg, "Could not open input map %s.\n", sites);
    		G_fatal_error (errmsg);
  	}

	vect_points = Vect_new_line_struct ();

	if (all_flag != 1) {
		Vect_set_constraint_region (&in_vect_map, region.north, region.south, 
			region.east, region.west, 0.0, 0.0);
	}
		
	/* get total number of sampling points */
	i = 0;	
	while ((cur_type = Vect_read_next_line (&in_vect_map, vect_points, NULL) > 0)) {
		i ++;
	}

	no_sites = i; /* store this for later use */
			
	/* open raster map */
	fd = G_open_cell_old (map, G_find_cell (map, ""));
	if (fd < 0)
	{
		delete_tmpfile (map);
		G_fatal_error ("Could not open raster map for reading!\n");
	}
	/* allocate a cache and a raster buffer */
	cache = (GT_Row_cache_t *) G_malloc (sizeof (GT_Row_cache_t));
	GT_RC_open (cache, CACHESIZE, fd, CELL_TYPE);
	cellbuf = G_allocate_raster_buf (CELL_TYPE);			
	
	cats = GT_get_stats (map,mapset,&null_count_map, &nocat_count_map, show_progress);
	if ( cats < 2 ) {
		delete_tmpfile (map);
		G_fatal_error ("Input map must have at least two categories.");
	}
	
	/* get category labels and counts */
	cats_description = GT_get_labels (map,mapset);
	if (cats_description == NULL) {
		delete_tmpfile (map);
		G_fatal_error ("Could not read category labels from input map.");
	}
	cat_count = GT_get_c_counts (map,mapset, show_progress);
	if (cat_count == NULL) {
		delete_tmpfile (map);
		G_fatal_error ("Could not count categories in input map.");
	}		
	
	/* allocate a double array to hold statistics */
	share_smp = (unsigned long *) G_malloc ((signed)(cats * sizeof (unsigned long)));
	for (i = 0; i < cats; i++)
	{
		share_smp[i] = 0;
		
	}	
	
	/* count raster values under sampling points */
	i = 0;
	k = 0; /* progress counter for status display */
	
	Vect_rewind (&in_vect_map);	
	
	if ( !quiet_flag ) {
		fprintf (stdout, "Counting sample: \n");
		fflush (stdout);	
	}
	
	/* we MUST not set constraints so that no raster values outside the current region are
	   accessed, which would give an "illegal cache request" error */
	Vect_set_constraint_region (&in_vect_map, region.north, region.south, 
				     region.east, region.west, 0.0, 0.0);
	
	while ((cur_type = Vect_read_next_line (&in_vect_map, vect_points, NULL) > 0)) {	
		Vect_copy_pnts_to_xyz (vect_points, &x, &y, &z, &n_points);		
		k ++;
		if ( !quiet_flag ) {
			G_percent ((signed) k, (signed) no_sites, 1);
		}
		/* get raster row with same northing as sample and perform
		   quantification */
		row_idx = (long) G_northing_to_row (y, &region);
		col_idx = (long) G_easting_to_col (x, &region);				
				
		cellbuf = GT_RC_get (cache, (signed) row_idx);
		/* now read the raster value under the current site */
		if (G_is_c_null_value (&cellbuf[col_idx]) == 0) {
			/* site on cell within category range [0..cats] ? */
			if ( (cellbuf[col_idx] > -1) && (cellbuf[col_idx] <= cats) ) {
				share_smp [cellbuf[col_idx] ] ++;
				/* i keeps track of samples on non-null coverage only */
				/* inside the current region */
				i ++;
			} else {
				if ( uncat_flag ) {
					/* also keep count of sites on uncategorised cells? */
					i ++;
					nocat_count++;
				}
			}				
		}
		if (G_is_c_null_value (&cellbuf[col_idx]) == 1) { 
			/* got a NULL value under this site */
			if (null_flag) { /* only count this, if null flag is set */
				null_count ++;
				i ++;
			}
		}
	}
	
	Vect_close (&in_vect_map);		
	
	fprintf (lp,"\n");
	if ( background ) {
		fprintf (lp,"Distribution of categories under %lu points (%lu in region) and in input map:\n",i,no_sites);	
	} else {
		fprintf (lp,"Distribution of categories under %lu points (%lu in region):\n",i,no_sites);	
	}
	/* determine starting value for total of sites analysed */
	total = 0;
	for ( j=0; j < cats; j ++) {
		total = total + share_smp[j];
		map_total = map_total + cat_count[j];
	}
	if (null_flag) { /* add NULL values to total */	
		total = total + null_count;
		map_total = map_total + null_count_map;
	}
	if (uncat_flag) { /* add uncategorised cells to total */
		total = total + nocat_count;
		map_total = map_total + nocat_count_map;
		
	}
	
	/* Now display those values which the user has chosen */
	if ( (background) && (gain) ) {	
		fprintf (lp,"Cat.\tPts.\t(%%)\tMap\t(%%)\tGain\tDescription\n");				
	}
	if ( (background) && (!gain) ) {	
		fprintf (lp,"Cat.\tPts.\t(%%)\tMap\t(%%)\tDescription\n");		
	}
	if ( (!background) && (gain) ) {	
		fprintf (lp,"Cat.\tPts.\t(%%)\tGain\tDescription\n");
	}
	if ( (!background) && (!gain) ) {	
		fprintf (lp,"Cat.\tPts.\t(%%)\tDescription\n");
	}	
	for ( j = 0; j < cats; j ++) {
		/* if skip_flag is not set: only show categories that have count > 0 */
		if ((skip_flag == 1) || ((skip_flag == 0) && (share_smp[j] > 0))) {
			if ( (background) && (gain) ) {
				/* Kvamme's Gain = 1 - (%area/%sites) */
				kvamme_gain = gstats_gain_K(((double) share_smp[j]*(100/total)),
							    ((double) cat_count[j]*(100/map_total)));							    				
				fprintf (lp, "%lu\t%6lu\t%6.2f\t%8lu %6.2f\t%6.2f\t%s\n", j, share_smp[j], (float) share_smp[j]*(100/total),
						cat_count[j], (float) cat_count[j]*(100/map_total),
						kvamme_gain, cats_description[j]);
			} 
			if ( (background) && (!gain) ) {
				fprintf (lp, "%lu\t%6lu\t%6.2f\t%8lu %6.2f\t%s\n", j, share_smp[j], (float) share_smp[j]*(100/total),
						cat_count[j], (float) cat_count[j]*(100/map_total),
						cats_description[j]);
				
			} 			
			if ( (!background) && (gain) ) {
				kvamme_gain = 1-( (float) cat_count[j]*(100/map_total) / (float) share_smp[j]*(100/total) );
				fprintf (lp, "%lu\t%6lu\t%6.2f\t%6.2f\t%s\n", j, share_smp[j], (float) share_smp[j]*(100/total),						
						kvamme_gain, cats_description[j]);				
			} 			
			if ( (!background) && (!gain) ) {
				fprintf (lp, "%lu\t%6lu\t%6.2f\t%s\n", j, share_smp[j], (float) share_smp[j]*(100/total),
						cats_description[j]);
			} 									
		}
	}
	if (null_flag) {		
		if ( background ) {
			fprintf (lp,"NULL\t%6lu\t%6.2f\t%8lu %6.2f\n",null_count, (float) null_count * 100 / total
						,null_count_map, (float) null_count_map * 100 / map_total);
		} else {
			fprintf (lp,"NULL\t%6lu\t%6.2f\n",null_count, (float) null_count * 100 / total);
		}
	}
	if (uncat_flag) {
		if ( background ) {
			fprintf (lp,"NOCAT\t%6lu\t%6.2f\t%8lu %6.2f\n",nocat_count, (float) nocat_count * 100 / total
						,nocat_count_map, (float) nocat_count_map * 100 / map_total);
		} else {
			fprintf (lp,"NOCAT\t%6lu\t%6.2f\n",nocat_count, (float) nocat_count * 100 / total);
		}		
	}	
	if ( background) {
		fprintf (lp,"TOTAL\t%6lu\t%6.2f\t%8lu %6.2f\n",(long) total, (float) 100, (long) map_total, (float) 100);
	} else {
		fprintf (lp,"TOTAL\t%6lu\t%6.2f\n",(long) total, (float) 100);
	}
	
	/* close cache and sites file; free buffers. */
	GT_RC_close (cache);
	G_free (cellbuf);
	G_free (cache);	
}


/* create the actual report */
/* This function is for floating point maps */
void do_report_DCELL ( char *map, char *mapset, char *sites,
					int precision, int null_flag, int uncat_flag,
					int all_flag, int quiet_flag, int skip_flag,
				  	char *logfile, int background, int gain, int show_progress) {
    	DCELL *dcellbuf;
	DCELL dvalue;
	CELL value;
	struct Cell_head region;
	struct Categories categories;
	GT_Row_cache_t *cache;
	unsigned long row_idx, col_idx;	
	short error;
	int fd;
	unsigned long i,j,k;
	unsigned long no_sites;
	FILE *lp;	
	unsigned long nrows, ncols;
	unsigned long *share_smp = NULL; /* array that keeps percentage of sites */
	double total = 0;
	double map_total = 0;
	double kvamme_gain;
	long null_count = 0; /* keeps count of sites on NULL cells */
	long nocat_count = 0; /* sites on cells outside category range */
	/* category counts and descriptions */
	int cats;
	char **cats_description; /* category labels */
	long *cat_count; /* category counts */
	long null_count_map; /* number of NULL cells in input map */
	long nocat_count_map; /* number of cells that do not fall into the category range [0 .. n] */		
	
	int debug_mode = 0;		/* 1 to enable writing additional output to logfile */
	time_t systime;

	char errmsg [200];
	struct Map_info in_vect_map;
  	struct line_pnts *vect_points;
	double x,y,z;
	int n_points = 1;
	int cur_type;


	/* get current region */
	G_get_window (&region);
	nrows = G_window_rows ();
	ncols = G_window_cols ();	
	
	/* check logfile */
	if (logfile != NULL) {
		debug_mode = 1;	
		if ( !G_legal_filename (logfile) ) {
			delete_tmpfile (map);
			G_fatal_error ("Please specify a legal filename for the logfile.\n");
		}
		/* attempt to write to logfile */
		if ( (lp = fopen ( logfile, "w+" ) ) == NULL )	{
			delete_tmpfile (map);
			G_fatal_error ("Could not create logfile.\n");
		}
		/* we want unbuffered output for the logfile */
		setvbuf (lp,NULL,_IONBF,0);	
		fprintf (lp,"This is s.report, version %.2f\n",PROGVERSION);
		systime = time (NULL);
		fprintf (lp,"Started on %s",ctime(&systime));
		fprintf (lp,"\tlocation    = %s\n",G_location());
		fprintf (lp,"\tmapset      = %s\n",G_mapset());
		fprintf (lp,"\tinput map   = %s\n",map);
		fprintf (lp,"\tsample file = %s\n",sites);
	} else {		
		/* log output to stderr by default */
		lp = stderr;
	}

  	if (1 > Vect_open_old (&in_vect_map, sites, "")) {
    		sprintf (errmsg, "Could not open input map %s.\n", sites);
		delete_tmpfile (map);	
    		G_fatal_error (errmsg);
  	}

	vect_points = Vect_new_line_struct ();

	if (all_flag != 1) {
		Vect_set_constraint_region (&in_vect_map, region.north, region.south, 
			region.east, region.west, 0.0, 0.0);
	}
		
	/* get total number of sampling points */
	i = 0;	
	while ((cur_type = Vect_read_next_line (&in_vect_map, vect_points, NULL) > 0)) {
		i ++;
	}
	no_sites = i; /* store this for later use */
			
	/* open raster map */
	fd = G_open_cell_old (map, G_find_cell (map, ""));
	if (fd < 0)
	{
		delete_tmpfile (map);
		G_fatal_error ("Could not open raster map for reading!\n");
	}
	/* allocate a cache and a raster buffer */
	cache = (GT_Row_cache_t *) G_malloc (sizeof (GT_Row_cache_t));
	GT_RC_open (cache, CACHESIZE, fd, DCELL_TYPE);
	dcellbuf = G_allocate_raster_buf (DCELL_TYPE);			
	
	cats = GT_get_stats (map,mapset,&null_count_map, &nocat_count_map, show_progress);
	if ( cats < 2 ) {
		delete_tmpfile (map);
		G_fatal_error ("Input map must have at least two categories.");
	}
	
	/* get category labels and counts */
	cats_description = GT_get_labels (map,mapset);
	if (cats_description == NULL) {
		delete_tmpfile (map);
		G_fatal_error ("Could not read category labels from input map.");
	}	
	cat_count = GT_get_f_counts (map,mapset, show_progress);
	if (cat_count == NULL) {
		delete_tmpfile (map);
		G_fatal_error ("Could not count categories in input map.");
	}

	/* now read category structure of input map*/
	G_init_cats (0, "", &categories);
	error = G_read_cats (map, mapset, &categories);
	if (error != 0) {	/* no categories found */
		delete_tmpfile (map);		
		G_fatal_error ("Could not read category information of input map.");
	}
	
	/* allocate a double array to hold statistics */
	share_smp = (unsigned long *) G_malloc ((signed) (cats * sizeof (unsigned long)));
	for (i = 0; i < cats; i++)
	{
		share_smp[i] = 0;		
	}	
	
	/* count raster values under sites */
	/* re-open sites file with samples */
	i = 0;
	k = 0; /* progress counter for status display */

	Vect_rewind (&in_vect_map);

	if ( !quiet_flag ) {
		fprintf (stdout, "Counting sample: \n");
		fflush (stdout);	
	}
	
	/* we MUST not set constraints so that no raster values outside the current region are
	   accessed, which would give an "illegal cache request" error */
	Vect_set_constraint_region (&in_vect_map, region.north, region.south, 
				     region.east, region.west, 0.0, 0.0);
		
	while ((cur_type = Vect_read_next_line (&in_vect_map, vect_points, NULL) > 0)) {
		Vect_copy_pnts_to_xyz (vect_points, &x, &y, &z, &n_points);		
		k ++;
		if ( !quiet_flag ) {
			G_percent ((signed) k, (signed) no_sites, 1);
		}
		/* get raster row with same northing as sample and perform
		 * quantification */
		row_idx = (long) G_northing_to_row (y, &region);
		col_idx = (long) G_easting_to_col (x, &region);				
				
		dcellbuf = GT_RC_get (cache, (signed) row_idx);
		/* now read the raster value under the current site */
		if (G_is_d_null_value (&dcellbuf[col_idx]) == 0) {	
			dvalue = dcellbuf[col_idx];
			value = G_quant_get_cell_value (&categories.q, dvalue);
			if ( ! (( value < 0 ) || ( value > cats -1)) ) {
				share_smp [value] ++;
				i ++;
			} else {
				if ( uncat_flag ) {
					/* also keep count of sites on uncategorised cells? */
					i ++;
					nocat_count++;
				}
			}							
		}
		if (G_is_d_null_value (&dcellbuf[col_idx]) == 1) { 
			/* got a NULL value under this site */
			if (null_flag) { /* only count this, if null flag is set */
				null_count ++;
				i ++;
			}
		}
	}

	Vect_close (&in_vect_map);		
	
	fprintf (lp,"\n");
	if ( background ) {
		fprintf (lp,"Distribution of categories under %lu points (%lu in region) and in input map:\n",i,no_sites);	
	} else {
		fprintf (lp,"Distribution of categories under %lu points (%lu in region):\n",i,no_sites);	
	}
	/* determine starting value for total of sites analysed */
	total = 0;
	for ( j=0; j < cats; j ++) {
		total = total + share_smp[j];
		map_total = map_total + cat_count[j];
	}
	if (null_flag) { /* add NULL values to total */	
		total = total + null_count;
		map_total = map_total + null_count_map;
	}
	if (uncat_flag) { /* add uncategorised cells to total */
		total = total + nocat_count;
		map_total = map_total + nocat_count_map;
		
	}
	/* Now display those values which the user has chosen */
	if ( (background) && (gain) ) {	
		fprintf (lp,"Cat.\tPts.\t(%%)\tMap\t(%%)\tGain\tDescription\n");				
	}
	if ( (background) && (!gain) ) {	
		fprintf (lp,"Cat.\tPts.\t(%%)\tMap\t(%%)\tDescription\n");		
	}
	if ( (!background) && (gain) ) {	
		fprintf (lp,"Cat.\tPts.\t(%%)\tGain\tDescription\n");
	}
	if ( (!background) && (!gain) ) {	
		fprintf (lp,"Cat.\tPts.\t(%%)\tDescription\n");
	}	
	for ( j = 0; j < cats; j ++) {
		/* if skip_flag is not set: only show categories that have count > 0 */
		if ((skip_flag == 1) || ((skip_flag == 0) && (share_smp[j] > 0))) {
			if ( (background) && (gain) ) {
				/* Kvamme's Gain = 1 - (%area/%sites) */
				kvamme_gain = gstats_gain_K(((double) share_smp[j]*(100/total)),
							    ((double) cat_count[j]*(100/map_total)));							    				
				fprintf (lp, "%lu\t%6lu\t%6.2f\t%8lu %6.2f\t%6.2f\t%s\n", j, share_smp[j], (float) share_smp[j]*(100/total),
						cat_count[j], (float) cat_count[j]*(100/map_total),
						kvamme_gain, cats_description[j]);
			} 
			if ( (background) && (!gain) ) {
				fprintf (lp, "%lu\t%6lu\t%6.2f\t%8lu %6.2f\t%s\n", j, share_smp[j], (float) share_smp[j]*(100/total),
						cat_count[j], (float) cat_count[j]*(100/map_total),
						cats_description[j]);
				
			} 			
			if ( (!background) && (gain) ) {
				kvamme_gain = 1 - ( ((float) cat_count[j]*(100/map_total)) / ((float) share_smp[j]*(100/total)) );
				fprintf (lp, "%lu\t%6lu\t%6.2f\t%6.2f\t%s\n", j, share_smp[j], (float) share_smp[j]*(100/total),						
						kvamme_gain, cats_description[j]);				
			} 			
			if ( (!background) && (!gain) ) {
				fprintf (lp, "%lu\t%6lu\t%6.2f\t%s\n", j, share_smp[j], (float) share_smp[j]*(100/total),
						cats_description[j]);
			} 									
		}
	}
	if (null_flag) {		
		if ( background ) {
			fprintf (lp,"NULL\t%6lu\t%6.2f\t%8lu %6.2f\n",null_count, (float) null_count * 100 / total
						,null_count_map, (float) null_count_map * 100 / map_total);
		} else {
			fprintf (lp,"NULL\t%6lu\t%6.2f\n",null_count, (float) null_count * 100 / total);
		}
	}
	if (uncat_flag) {
		if ( background ) {
			fprintf (lp,"NOCAT\t%6lu\t%6.2f\t%8lu %6.2f\n",nocat_count, (float) nocat_count * 100 / total
						,nocat_count_map, (float) nocat_count_map * 100 / map_total);
		} else {
			fprintf (lp,"NOCAT\t%6lu\t%6.2f\n",nocat_count, (float) nocat_count * 100 / total);
		}		
	}
	if ( background) {
		fprintf (lp,"TOTAL\t%6lu\t%6.2f\t%8lu %6.2f\n",(long) total, (float) 100, (long) map_total, (float) 100);
	} else {
		fprintf (lp,"TOTAL\t%6lu\t%6.2f\n",(long) total, (float) 100);
	}
	
	/* close cache and sites file; free buffers. */
	GT_RC_close (cache);
	G_free (dcellbuf);
	G_free (cache);	
}


int
main (int argc, char *argv[]) {
	struct GModule *module;
	struct Option *map; /* raster map to work on */
	struct Option *sites; /* output map to write */
	struct Option *mode; /* Categorisation mode */
	struct Option *min; /* range of values to categorise ... */
	struct Option *max; /*   .. anything outside will be NULL in output */
	struct Option *logfile; /* log output to this file instead of stdout */
	struct Option *precision; /* decimal digits precision for log file */
	struct Option *cachesize;
	struct Flag *null; /* also count NULL values? */
	struct Flag *all; /* disregard region when reporting total percentages */			
	struct Flag *zeroskip;	/* also show categories with 0 count? */
	struct Flag *uncat; /* also show cells outside category range? */	
	struct Flag *background; /* show background distribution? */
	struct Flag *gain; /* calculate Kvamme's gain for each category? */
	struct Flag *quiet; /* no status display on screen */				
	
	char *mapset;
	int show_progress = 1; /* enable progress display by default */
	/* these vars are used to store information about the input map */
	int cats; /* number of categories in input map */
	long null_count; /* number of NULL cells */
	long nocat_count; /* number of cells that do not fall into the category range [0 .. n] */	
	/* use to create command line for r.categorize call */
	char *sysstr, *tmpfile, *input_map;	
	int error;
	
	sysstr = NULL;
	tmpfile = NULL;
	
	/* setup some basic GIS stuff */
	G_gisinit (argv[0]);
	module = G_define_module ();
	module->description = "Analyses distribution of vector sample over a raster map";
	/* do not pause after a warning message was displayed */
	G_sleep_on_error (0);
		
	/* DEFINE OPTIONS AND FLAGS */
	/* raster map to sample */
	map = G_define_standard_option (G_OPT_R_INPUT);
	map->key = "raster";
	map->type = TYPE_STRING;
	map->required = YES;
	map->description = "Raster map to sample";

	/* site map for sampling positions */
	sites = G_define_standard_option (G_OPT_V_INPUT);
	sites->key = "positions";
	sites->type = TYPE_STRING;
	sites->required = YES;
	sites->description = "Vector map with sampling positions";
		
	/* Categorisation mode */
	mode = G_define_option ();
	mode->key = "mode";
	mode->type = TYPE_STRING;
	mode->required = NO;
	mode->description = "Categorisation mode (see manual)";

	/* min raster value to categorise */
	min = G_define_option ();
	min->key = "min";
	min->type = TYPE_DOUBLE;
	min->required = NO;
	min->description = "Minimum value to include in categorisation";

	/* max raster value to categorise */
	max = G_define_option ();
	max->key = "max";
	max->type = TYPE_DOUBLE;
	max->required = NO;
	max->description = "Maximum value to include in categorisation.";

	/* optional name of logfile */
	logfile = G_define_option ();
	logfile->key = "logfile";
	logfile->type = TYPE_DOUBLE;
	logfile->required = NO;
	logfile->description = "Name of ASCII logfile, if desired.";
	
	/* optional number of decimal digitis to store in logfile/show on screen */
	precision = G_define_option ();
	precision->key = "precision";
	precision->type = TYPE_DOUBLE;
	precision->required = NO;
	precision->answer = "2";
	precision->description = "Number of decimal digits for statistics/logfile";		
	
	/* number of lines to store in cache */
	cachesize = G_define_option ();
	cachesize->key = "cachesize";
	cachesize->type = TYPE_INTEGER;
	cachesize->answer = "-1";
	cachesize->required = NO;
	cachesize->description = "Number of raster rows to store in cache (-1 for auto)";	
		
	null = G_define_flag ();
	null->key = 'n';
	null->description = "Include NULL cells in report.";
	
	uncat = G_define_flag ();
	uncat->key = 'u';
	uncat->description = "Include uncategorised cells in statistics.";
	
	all = G_define_flag ();
	all->key = 'a';
	all->description = "Disregard region setting for counts.";	
	
	zeroskip = G_define_flag ();
	zeroskip->key = 'z';
	zeroskip->description = "Also show categories with zero count/percentage.";

	background = G_define_flag ();
	background->key = 'b';
	background->description = "Show background distribution of categories in raster input map.";

	gain = G_define_flag ();
	gain->key = 'g';
	gain->description = "Calculate Kvamme's Gain Factor for each category.";

	quiet = G_define_flag ();
	quiet->key = 'q';
	quiet->description = "Quiet operation: do not show progress display.";	

	
	/* parse command line */
	if (G_parser (argc, argv))
	{
		exit (-1);
	}

	/* check for 'quiet' flag */
	if ( quiet->answer ) {
		show_progress = 0;
	}
	
	PROGNAME = argv[0];		

	/* copy the 'map' option string to another buffer and use that */
	/* from now on. We do this because we might want to manipulate */
	/* that string and that is dangerous with GRASS Option->answer strings! */
	input_map = G_calloc (255, sizeof (char));
	G_strcpy (input_map, map->answer);
	
	mapset = G_calloc (255, sizeof (char));
	/* check if input map is a fully categorised raster map */
	mapset = G_find_cell (input_map,"");
	if ( mapset == NULL) {
		G_fatal_error ("The input map does not exist in the current database.");
	}

	if ( mode->answer == NULL ) {		
		cats = GT_get_stats (input_map,mapset,&null_count, &nocat_count, show_progress);
		if ( cats < 0 ) {
			G_fatal_error ("Could not stat input map. Do you have read access?");
		}
		if ( ((cats == 0) && (mode->answer==NULL)) ) {
			G_fatal_error ("No categories defined in input map.\nPlease specify a mode to create a fully classified map.");
		}
	}

	/* a classification mode was given: call r.categorize and save output
	   in a tmp file */
	if ( mode->answer != NULL ) {
		srand ((unsigned long) time(NULL));
		tmpfile = G_calloc (255, sizeof(char));
		sysstr = G_calloc (255, sizeof(char));
		/* create tmp file name from current PID and system time */		
		sprintf (tmpfile,"tmp.%i.%i", getpid(),(rand())/10000);
		if ( getenv("GISBASE") == NULL ) {
			G_fatal_error ("GISBASE not set. Unable to call GRASS module 'r.categorise'.");
		}		
		if ( quiet->answer ) {
			sprintf (sysstr,"%s/bin/r.categorize input=%s@%s output=%s mode=%s min=%s max=%s -q", getenv("GISBASE"), map->answer, 
					mapset, tmpfile, mode->answer, min->answer, max->answer);
		} else {
			sprintf (sysstr,"%s/bin/r.categorize input=%s@%s output=%s mode=%s min=%s max=%s", getenv("GISBASE"), map->answer, 
					mapset, tmpfile, mode->answer, min->answer, max->answer);
		}
		/* now create fully classified map using r.categorize and store */
		/* it in a temporary raster map */
		error = system (sysstr);
		if ( error < 0 ) {
			G_fatal_error ("Calling r.categorize has failed. Check your installation.");
		}
				
		/* store name of temporary file as new input map */
		G_strcpy (input_map, tmpfile);
		
		/* check categories of tmpfile */
		cats = GT_get_stats (input_map,mapset,&null_count, &nocat_count, show_progress);
		if (cats < 1) {
			G_fatal_error ("Could not create a fully categorised temporary file.\nTry another categorisation mode.");
		}
	}
	
	/* initialise cache structure */
	if ( input_map != NULL ) {
		/* set cachesize */
		CACHESIZE = atoi (cachesize->answer);
		if ( (CACHESIZE<-1) || (CACHESIZE > G_window_rows ()) ) {
			/* if cache size is invalid, just set to auto-mode (-1) */
			G_warning ("Invalid cache size requested (must be between 0 and %i or -1).\n", G_window_rows());
			CACHESIZE = -1;
		}
	}			
	
	if ( G_raster_map_is_fp (input_map, mapset))  {
		do_report_DCELL (input_map, mapset, sites->answer,
				atoi (precision->answer),null->answer, uncat->answer,
	           	all->answer, quiet->answer, zeroskip->answer,
			   	logfile->answer, background->answer, gain->answer, show_progress);
	} else {
		do_report_CELL (input_map, mapset, sites->answer,
				atoi (precision->answer),null->answer, uncat->answer,
	           	all->answer, quiet->answer, zeroskip->answer,
			   	logfile->answer, background->answer, gain->answer, show_progress);		
	}

		
	/* delete temporary file, if needed */
	if ( mode->answer != NULL ) {
		delete_tmpfile (tmpfile);
		G_free (tmpfile);
	}
	
	if ( sysstr != NULL ) {
		G_free (sysstr);
	}
	G_free (input_map);

	return (EXIT_SUCCESS);
}
