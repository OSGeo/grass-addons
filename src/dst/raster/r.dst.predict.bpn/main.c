/* r.dst.bpn */
/* Part of the GRASS Dempster-Shafer Predictive Modelling Extension */

/* Purpose: 	Automatically calculate statistic BPNs (Basic Probability Numbers)
		for a predictive model of site locations using Dempster-Shafer's
		theory of evidence.
				
 		Needs two files that constitute one source of evidence: 
		(a) a fully classified input raster map (integer format)
		(b) a list of sites
				
		The difference in relative class frequencies between the entire raster map
		and the cells that lie under the sites is taken to be evidence for one of two
		mutually exclusive hypotheses:
		(a) h1 = a site is present in this cell
		(b) h2 = no site is present
		the probability masses of each source of evidence.
		
		The output consists of three floating point raster maps,
		encoding the BPNs for each of the three hypotheses in the
		interval [0..1].
		The output map names will be suffixed '.SITE', '.NOSITE' and
		'.SITE.NOSITE', respectively.

	This file is licensed under the GPL (version 2 or later at your option)
 	see: http://www.gnu.org/copyleft/gpl.html* /

 	(c) Benjamin Ducke 2006
	benducke@compuserve.de

*/



#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <math.h>
#include <time.h>

#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/dbmi.h>

#include "gt/cat_engine.h"
#include "gt/rowcache.h"
#include "gt/gstats_tests.h"
#include "gt/gstats_error.h"

#define PROGVERSION 1.6

#define BUF_SIZE 4096

#define ANULL -1.1111111111

/* program will issue a warning if sample points are fewer than MIN_SAMPLE_SIZE */
#define MIN_SAMPLE_SIZE 50

typedef struct
{
	float a;
	float b;
	float a_b;
}
bpn_struct;

float MINBPN_H1 = 1.00;
float MAXBPN_H1 = 0.00;
float MINBPN_H2 = 1.00;
float MAXBPN_H2 = 0.00;
float MINBPN_H1_2 = 1.00;
float MAXBPN_H1_2 = 0.00;

unsigned int WARN_ON = 0;
unsigned int WARN_N_TO_SMALL = 0;

extern int errno;
int cachesize;

char tmp_file[BUF_SIZE];
int debug_mode = 1;		/* 1 to enable writing debug output to logfile */
FILE *logfile;


/* This calculates the actual BPN values */
/* a = share_smp; b = share_nat */
/* h1 = belief in "site", calculated from z-statistic */
/* h2 = belief in "no site", calculated from z-statistic */
/* h1_2 = "no site OR site" (uncertainty hypothesis) */
/* int i and char *label are passed so that some information can be written
   to the logfile */
/* if the user has specified bias map(s), an amount proportionate to */
/* the proportion of biased cells and the mean bias in those cells will */
/* be transferred from the NO SITE hyp h2 to uncertainty h1_2 */
void
dst_calc (float *a, float *b, float *a_b, int sample_size,
			int i, char *label, float **share_bias, float **mean_bias, int num_bias_maps,
			float perror )
{
	float h1, h2, h1_2;
	float transfer;
	int j;
	float p0;

	h1 = 0.01;
	h2 = 0.01;
	
	
	/* calculate z-statistic */
	p0 = (gstats_test_ZP2 (*a/100, *b/100, sample_size));
	 
	if (*a > *b) {		
		/* probability of error < significance level: */
		/* directly transfer the other probability mass to h1 */
		if ( p0 <= perror ) {
			h1 = 1 - p0;
		/* if error probability > significance level: */
		} else {	
			h1 = 1 - powf ( p0, (1 - p0) - p0);
		}
		if (h1 > 0.98) {
			h1 = 0.98;
		}
	}		
	
	if (*a < *b) {
		if ( p0 <= perror ) {	
			h2 = 1 - p0;
		} else {
			h2 = 1 - powf ( p0, (1- p0) - p0);		
		}
		if (h2 > 0.98) {
			h2 = 0.98;
		}
	}	
	
	/* shift bias to uncertainty if bias map(s) present */
	if (( h2 > 0.01 ) && (mean_bias != NULL)) {
		transfer = 0;
		/* j steps thru all bias maps, i is the current map category */
		for (j = 0; j < num_bias_maps; j++) {
			transfer = h2 * mean_bias[j][i] * (share_bias[j][i]/100);
			h2 = h2 - transfer;
		}
	}	
	
	if (h1 < 0.01) { h1 = 0.01; }
	if (h2 < 0.01) { h2 = 0.01; }	
	
	/* whatever is left gets shifted to the uncertainty hypothesis */
	h1_2 = 1 - (h1 + h2);	
	
	/* return results */
	*a = h1;
	*b = h2;
	*a_b = h1_2;
	
	/* keep track of global min and max BPN values */
	if ( h1 < MINBPN_H1 ) {
		MINBPN_H1 = h1;
	}
	if ( h1 > MAXBPN_H1 ) {
		MAXBPN_H1 = h1;
	}
	if ( h2 < MINBPN_H2 ) {
		MINBPN_H2 = h2;
	}
	if ( h2 > MAXBPN_H2 ) {
		MAXBPN_H2 = h2;
	}
	if ( h1_2 < MINBPN_H1_2 ) {
		MINBPN_H1_2 = h1_2;
	}
	if ( h1_2 > MAXBPN_H1_2 ) {
		MAXBPN_H1_2 = h1_2;
	}	
}


/* process input map and write BPN values to output map */
void write_BPNs (char *coverage_answer, char* mapset, char *sites_answer, char **bias_maps,
		    char *result_answer, float perror, char *color_rules, int show_progress)
{
	CELL *cellbuf;
	FCELL *fcellbuf;
	struct Categories *cats;
	struct Cell_head region;
	struct Colors colors;
	FCELL from, to; /* for color ramp */
	GT_Row_cache_t *cache;		
	int nrows, ncols;
	int row, col;
	int fd, fd_out_a, fd_out_b, fd_out_a_b, fd_bias;
	int n; /* number of classes */
	int i,j, k, sample_size;	
	long total = 0; /* for cell statistics */
	float *share_nat = NULL;
	float *share_smp = NULL;
	/* for chi-square test */
	double chisq_result;
	int *observed = NULL;
	int *expected = NULL;
	int chi_cats;
	bpn_struct *bpn; /* stores BPN values */
	/* temporary variables for DST quantification */
	float a, b, a_b;
	char result_map[255] = "";
	char **cats_description; /* category labels */
	long *cat_count; /* category counts */
	int *site_count;
	/* needed for analysing sites file */
	int n_sites = 0;
	long row_idx;
	long col_idx;
	
	int num_bias_maps;
	float **share_bias;
	float **mean_bias;
	DCELL *bias_dcellbuf = NULL;
	CELL  *bias_cellbuf = NULL;
	
	char errmsg[200];
	struct Map_info vect_map;
	struct line_pnts *vect_points;
	int type;
	double x,y,z;
	int n_points;

	cats = G_malloc (sizeof (struct Categories));
	G_get_window (&region);
	nrows = G_window_rows ();
	ncols = G_window_cols ();
		
	cellbuf = NULL;


	/* STEP 1: Calculate ranges and number of categories in input maps */
			
	/* get number of categories */
	G_read_cats (coverage_answer, G_find_cell (coverage_answer, ""), cats);
	
	n = G_number_of_cats (coverage_answer, G_find_cell (coverage_answer, "")) + 1;
	if (n < 2) {
		G_fatal_error ("Could not find at least two categories in input map.");
	}
	if (debug_mode)
	{
		fprintf (logfile, "Found %i categories in input map.\n", n);
		fflush (logfile);
	}
	
	/* get category labels and counts */
	cats_description = GT_get_labels (coverage_answer,G_find_cell (coverage_answer, ""));
	if (cats_description == NULL) {
		G_fatal_error ("Could not read category labels from input map.");
	}	
	cat_count = GT_get_c_counts (coverage_answer,G_find_cell (coverage_answer, ""), show_progress);
	if (cat_count == NULL) {
		G_fatal_error ("Could not count categories in input map.");
	}
		
	/* calculate percentual shares of coverage cats and store them */
	share_nat = (float *) G_malloc ((signed) (n * sizeof (float)));
	for (i = 0; i < n; i++) {
		share_nat[i] = 0;
		total = total + cat_count[i];
	}	

	for (i = 0; i < n; i++) {
		share_nat[i] = (float) cat_count[i] / total * 100;
	}
	if (debug_mode)
	{
		fprintf (logfile,"\nCategories in input map '%s@%s':\n", coverage_answer, G_find_cell (coverage_answer, ""));	
		fprintf (logfile,"Cat.\tCount\t(%%)\tDescription\n");
		for (i = 0; i < n; i++) {
			fprintf (logfile, "%i\t%li\t%5.2f\t%s\n", i, cat_count[i],share_nat[i],
					cats_description[i]);
		}
		fflush (logfile);
	}

	/* open evidence raster map for reading */
	fd = G_open_cell_old (coverage_answer, G_find_cell (coverage_answer, ""));	
	if (fd < 0) {
		G_fatal_error ("Could not open input map for reading.\n");
	}
	
	/* open bias map(s) (if given), count percentage of categories under bias > 0 and store mean
	   bias for each category */
	mean_bias = NULL;
	share_bias = NULL;
	num_bias_maps = 0;
	if (bias_maps != NULL) {
		while (bias_maps[num_bias_maps] != NULL) {
			num_bias_maps ++;	
		}
	}
	if (num_bias_maps > 0) {
		/* allocate memory for bias maps */
		share_bias = (float **) G_malloc ((signed) (num_bias_maps * sizeof (float*)));
		mean_bias  = (float **) G_malloc ((signed) (num_bias_maps * sizeof (float*)));
		bias_cellbuf = G_allocate_c_raster_buf ();
		bias_dcellbuf = G_allocate_d_raster_buf ();

		if (show_progress) {
			fprintf (stdout, "Analysing bias map(s):\n");
		}	
		for (i = 0; i < num_bias_maps; i++) {
			fd_bias = G_open_cell_old (bias_maps[i], G_find_cell (bias_maps[i], ""));
			if (fd_bias < 0) {
				G_fatal_error ("Could not open bias map '%s' for reading.\n", bias_maps[i]);
			}
			if (debug_mode) {
				fprintf (logfile, "\nImpact of NO SITE bias in '%s':\n", bias_maps[i]);
				fprintf (logfile, "Cat.\tMean\tArea(%%)\tDescription\n");
			}
			share_bias [i] = (float *) G_malloc ((signed) (n * sizeof (float)));
			mean_bias  [i] = (float *) G_malloc ((signed) (n * sizeof (float)));			
			for (j = 0; j < n; j ++) {
				share_bias [i][j] = 0;
				mean_bias  [i][j] = 0;
			}
			for (j = 0; j < nrows; j++) {
				/* read one row from coverage and bias maps */
				G_get_c_raster_row (fd, bias_cellbuf, j);
				G_get_d_raster_row (fd_bias, bias_dcellbuf, j);
				for (k = 0; k < ncols; k++) {
					/* analyse row */
					if (!G_is_c_null_value (&bias_cellbuf[k])) {
						/* NULL values have no effect */
						if (!G_is_d_null_value (&bias_dcellbuf[k])) {
							if (bias_dcellbuf[k] > 0) {
								share_bias [i][bias_cellbuf[k]] ++;
								mean_bias  [i][bias_cellbuf[k]] += bias_dcellbuf[k];
							}
						}	
					}
				}
			}
			for (j=0; j<n; j++) {
				/* calculate %area that is biased */
				if ((mean_bias[i][j] != 0) && (share_bias[i][j] != 0) && (cat_count[j] != 0)) {
					mean_bias [i][j] = mean_bias [i][j] / share_bias[i][j];
					share_bias[i][j] = share_bias[i][j] / (((float) cat_count[j]) / 100);
				} else {
					mean_bias[i][j] = 0;
					share_bias[i][j] = 0;
				}
				if (debug_mode) {
					fprintf (logfile,"%i\t%.2f\t%.2f\t%s\n", j, mean_bias[i][j], 
								share_bias[i][j], cats_description[j]);
				}
		
			}
			G_close_cell (fd_bias);
		
			if (show_progress) {
				G_percent (i + 1, num_bias_maps, 1);
				fflush (stdout);
			}
		}
		if (show_progress) {
			fprintf (stdout,"\n");
			fflush (stdout);
		}
	}

	/* open vector points */
        vect_points = Vect_new_line_struct ();
	Vect_set_open_level (1); 
	if (1 > Vect_open_old (&vect_map, sites_answer, "") )
	  {
	     sprintf (errmsg, "Could not open vector map with sample points for reading.\n");
	     G_fatal_error ("%s",errmsg);
	  }	
	Vect_set_constraint_region (&vect_map, region.north, region.south, 
					region.east, region.west, 0.0, 0.0);

	/* calculate total size of sites sample in current region */		
	while ( (type = Vect_read_next_line (&vect_map, vect_points, NULL)) > 0)
	{
		if ( type == GV_POINT ) {
			n_sites ++;
		}
	}
	if ( n_sites < 2 ) {
		G_fatal_error ("Less than two vector points (sites) in current region.");
	}
	
	/* rewind sites file */
	Vect_close (&vect_map);
	Vect_open_old (&vect_map, sites_answer, "");
	Vect_set_constraint_region (&vect_map, region.north, region.south, 
					region.east, region.west, 0.0, 0.0);
	
	/* create array to store sites<->categories counts */
	site_count = G_calloc (n, sizeof(int));
	/* attach a cache to raster map */
	cache = (GT_Row_cache_t *) G_malloc (sizeof (GT_Row_cache_t));
	GT_RC_open (cache, cachesize, fd, CELL_TYPE);
			
	total = 0; i = 0;
	if (show_progress) {
		fprintf (stdout, "Counting categories under sites:\n");
	}
	
	j = 0;
	n_points = 1; /* since we are dealing with points, we only need to read one coord per object */
	while ((type = Vect_read_next_line (&vect_map, vect_points, NULL)) > 0)
	{
		if (type == GV_POINT) {
			/* check if site in current region */
			Vect_copy_pnts_to_xyz (vect_points, &x, &y, &z, &n_points);
			/*
			if (	(x >= region.west) &&
		    		(x <= region.east) &&
		    		(y >= region.south) &&
		    		(y <= region.north)	)
			{	
			*/		
				/* get raster row with same northing as sample and perform
			 	* quantification */
				row_idx =
					(long) G_northing_to_row (y, &region);
				col_idx =
					(long) G_easting_to_col (x, &region);
				cellbuf = GT_RC_get (cache, row_idx);
				/* now read the raster value under the current site */
				if (G_is_c_null_value (&cellbuf[col_idx]) == 0)
				{
					site_count [cellbuf[col_idx]]++;
					total++;				
					i ++; /* i keeps track of samples on non-null coverage inside the current region */
				}
			/*
			}
			*/
			/* update progress display */
			j ++;
			if (show_progress) {
				G_percent (j, n_sites, 1);
				fflush (stdout);
			}
		}
	}
	/* store size of sample for later use */
	sample_size = i;
			
	/* allocate an array to store percentages of cats under sites */
	share_smp = (float *) G_malloc ((signed) (n * sizeof (float)));
	/* calculate percentages */
	for (j = 0; j < n; j++) {
		share_smp[j] = (float) site_count[j] / total * 100;
	}	
	if (show_progress) {	
		fprintf (stdout, "\n");
		fflush (stdout);
	}
	
	if (debug_mode)
	{
		fprintf (logfile, "\nCategories under %i sites in '%s':\n", i, sites_answer);
		fprintf (logfile,"Cat.\tCount\t(%%)\tDescription\n");
		for (i=0; i < n; i ++) {
			fprintf (logfile, "%i\t%i\t%5.2f\t%s\n", i, site_count[i], share_smp[i],
						cats_description[i]);
		}
		fflush (logfile);
	}
	
	/* now do the DST quantification */
	/* a = site; b = no site; a_b = could be both */
	bpn = G_malloc ((signed) (n * sizeof (bpn_struct)));
	
	if (debug_mode) {
		fprintf (logfile,"\nBPN quantifications for categories; threshold p(NULL) = %.2f\n", perror);
		fprintf (logfile,"Cat.\t{h1}\t{h2}\t{h1,h2}\tDescription*\n");
	}
	
	for (i = 0; i < n; i++)
	{
		a = share_smp[i];
		b = share_nat[i];
		a_b = 0;
		/* calculate the actual BPN values */
		dst_calc (&a, &b, &a_b, sample_size, i, cats_description[i],
				share_bias, mean_bias, num_bias_maps, perror);
		bpn[i].a = a;
		bpn[i].b = b;
		bpn[i].a_b = a_b;
	}

	/* shift some belief to uncertainty for ALL categories, if chi-square tests gives us reason */
	/* to doubt the significance of the differences in *a and *b over ALL categories */
	expected = G_malloc ((signed) (n * sizeof(int)));
	observed = G_malloc ((signed) (n * sizeof(int)));
	chi_cats = 0;
	for (i = 0; i < n; i++) {
		/* make sure categories not present in current region do not get included in test */
		if ( share_nat[i] > 0 ) {
			observed [chi_cats] = site_count [i];
			/* the expected frequency is calculated from the population frequencies */
			expected [chi_cats] = sample_size * share_nat[i]/100;
			chi_cats ++;
		}
	}
		
	/* run a relaxed chi-square test */
	chisq_result = gstats_rtest_XF (observed, expected, chi_cats, chi_cats - 1);
	G_free (expected);
	G_free (observed);
	
	/* subtract probability of Type I error from ALL BPNs */
	/* exponentially more probability is subtracted if P(0) */
	/* exceeds the user-setable threshold (0.05 by default) */
	for (i = 0; i < n; i++) {
		if ( chisq_result <= perror ) {	
			bpn[i].a = bpn[i].a - chisq_result;
		} else {
			bpn[i].a = bpn[i].a - powf (chisq_result, (1-chisq_result)-chisq_result);		
		}	
		if (bpn[i].a < 0.01) {
			bpn[i].a = 0.01;
		}
		bpn[i].b = bpn[i].b - chisq_result;
		if (bpn[i].b < 0.01) {
			bpn[i].b = 0.01;
		}		
		bpn[i].a_b = 1 - (bpn[i].a + bpn[i].b);
	}
	
	/* write information on BPN quantification to logfile */
	if (debug_mode)
	{
		for (i = 0; i < n; i++) { 
			fprintf (logfile, "%i\t%4.2f\t%4.2f\t%4.2f\t%s\n",
				i,bpn[i].a, bpn[i].b, bpn[i].a_b, cats_description[i]);
		}
	}
	if (debug_mode) {
		fprintf (logfile,"\n*h1 = 'site present', h2 = 'no site present'\nh1,h2 = 'site present' OR 'no site present' (uncertainty)\n");
		fprintf (logfile,"\nChi-square test result: probability of type I error = %.6f\n", chisq_result);
	}	
	
	/* open result maps */
	sprintf (result_map, "%s.SITE", result_answer);
	fd_out_a = G_open_raster_new (result_map, FCELL_TYPE);
	sprintf (result_map, "%s.NOSITE", result_answer);
	fd_out_b = G_open_raster_new (result_map, FCELL_TYPE);
	sprintf (result_map, "%s.SITE.NOSITE", result_answer);
	fd_out_a_b = G_open_raster_new (result_map, FCELL_TYPE);
	if ((fd_out_a < 1) || (fd_out_b < 1) || (fd_out_a_b < 1))
	{
		G_fatal_error ("Could not open result map for writing.\n");
	}
	
	if (show_progress) {
		fprintf (stdout, "Writing BPN quantifications: \n");
	}	
	fcellbuf = G_allocate_raster_buf(FCELL_TYPE);	
	for (row = 0; row < nrows; row++) {
		cellbuf = GT_RC_get (cache, row);
		/* parse one row of raster data and write BPNs */
		for (col = 0; col < ncols; col++) {
			if (G_is_c_null_value (&cellbuf[col]) == 0) {
				fcellbuf[col] = bpn[cellbuf[col]].a;
			} else { /* copy null-value */				
				G_set_f_null_value (&fcellbuf[col], 1);
			}
		}		
		G_put_raster_row (fd_out_a, fcellbuf, FCELL_TYPE);
		
		for (col = 0; col < ncols; col++) {
			if (G_is_c_null_value (&cellbuf[col]) == 0) {
				fcellbuf[col] = bpn[cellbuf[col]].b;
			} else { /* copy null-value */				
				G_set_f_null_value (&fcellbuf[col], 1);
			}
		}
		G_put_raster_row (fd_out_b, fcellbuf, FCELL_TYPE);
				
		for (col = 0; col < ncols; col++) {
			if (G_is_c_null_value (&cellbuf[col]) == 0) {
				fcellbuf[col] = bpn[cellbuf[col]].a_b;
			} else { /* copy null-value */				
				G_set_f_null_value (&fcellbuf[col], 1);
			}
		}
		G_put_raster_row (fd_out_a_b, fcellbuf, FCELL_TYPE);
		
		if (show_progress) {
			G_percent (row, nrows-1, 1);
			fflush (stdout);
		}
	}
	if (show_progress) {
		fprintf (stdout, "\n");
		fflush (stdout);
	}
	
	/* we can now close the coverage map ... */
	/* close cache first */
	GT_RC_close (cache);
	/* now close the maps */
	G_close_cell (fd_out_a);
	G_close_cell (fd_out_b);
	G_close_cell (fd_out_a_b);		
	

	/*** WRITE COLOR SCHEMES FOR OUTPUT MAPS ***/
	
	/*** H1 ***/
	G_init_colors (&colors);
	if ( !strcmp ( color_rules, "cont" ) ) {	
		from = 0.000;
		to = 1.001;
		G_add_f_raster_color_rule (&from, 0, 0, 0, &to, 255, 0, 0, &colors);		
	}
	if ( !strcmp ( color_rules, "stct" ) ) {	
		from = MINBPN_H1;
		to = MAXBPN_H1;
		G_add_f_raster_color_rule (&from, 0, 0, 0, &to, 255, 0, 0, &colors);
	}
	if ( !strcmp ( color_rules, "bins" ) ) {
		from = 0.000;
		to = 0.333;
		G_add_f_raster_color_rule (&from, 255, 0, 0, &to, 255, 0, 0, &colors);
		from = 0.334;
		to = 0.666;		
		G_add_f_raster_color_rule (&from, 255, 255, 0, &to, 255, 255, 0, &colors);
		from = 0.667;
		to = 1.001;		
		G_add_f_raster_color_rule (&from, 0, 255, 0, &to, 0, 255, 0, &colors);
	}
	if ( !strcmp ( color_rules, "stbs" ) ) {
		from = MINBPN_H1;
		to = MINBPN_H1 + ((MAXBPN_H1-MINBPN_H1) / 3);
		G_add_f_raster_color_rule (&from, 255, 0, 0, &to, 255, 0, 0, &colors);
		from = MINBPN_H1 + ((MAXBPN_H1-MINBPN_H1) / 3) + 0.001;
		to = MINBPN_H1 + (((MAXBPN_H1-MINBPN_H1) / 3) * 2 );
		G_add_f_raster_color_rule (&from, 255, 255, 0, &to, 255, 255, 0, &colors);
		from = MINBPN_H1 + (((MAXBPN_H1-MINBPN_H1) / 3) * 2 ) + 0.001;
		to = MAXBPN_H1 + 0.001;	
		G_add_f_raster_color_rule (&from, 0, 255, 0, &to, 0, 255, 0, &colors);
	}	
	sprintf (result_map, "%s.SITE", result_answer);
	G_write_colors (result_map, G_mapset(), &colors);
	G_free_colors (&colors);
	
	/*** H2 ***/
	G_init_colors (&colors);	
	if ( !strcmp ( color_rules, "cont" ) ) {	
		from = 0.000;
		to = 1.001;
		G_add_f_raster_color_rule (&from, 0, 0, 0, &to, 0, 255, 0, &colors);		
	}
	if ( !strcmp ( color_rules, "stct" ) ) {	
		from = MINBPN_H2;
		to = MAXBPN_H2;
		G_add_f_raster_color_rule (&from, 0, 0, 0, &to, 0, 255, 0, &colors);
	}
	if ( !strcmp ( color_rules, "bins" ) ) {
		from = 0.000;
		to = 0.333;
		G_add_f_raster_color_rule (&from, 255, 0, 0, &to, 255, 0, 0, &colors);
		from = 0.334;
		to = 0.666;		
		G_add_f_raster_color_rule (&from, 255, 255, 0, &to, 255, 255, 0, &colors);
		from = 0.667;
		to = 1.001;		
		G_add_f_raster_color_rule (&from, 0, 255, 0, &to, 0, 255, 0, &colors);
	}
	if ( !strcmp ( color_rules, "stbs" ) ) {
		from = MINBPN_H2;
		to = MINBPN_H2 + ((MAXBPN_H2-MINBPN_H2) / 3);
		G_add_f_raster_color_rule (&from, 255, 0, 0, &to, 255, 0, 0, &colors);
		from = MINBPN_H2 + ((MAXBPN_H2-MINBPN_H2) / 3) + 0.001;
		to = MINBPN_H2 + (((MAXBPN_H2-MINBPN_H2) / 3) * 2 );
		G_add_f_raster_color_rule (&from, 255, 255, 0, &to, 255, 255, 0, &colors);
		from = MINBPN_H2 + (((MAXBPN_H2-MINBPN_H2) / 3) * 2 ) + 0.001;
		to = MAXBPN_H2 + 0.001;	
		G_add_f_raster_color_rule (&from, 0, 255, 0, &to, 0, 255, 0, &colors);
	}	
	sprintf (result_map, "%s.NOSITE", result_answer);
	G_write_colors (result_map, G_mapset(), &colors);
	G_free_colors (&colors);
	
	/*** H1 OR H2 ***/
	G_init_colors (&colors);
	if ( !strcmp ( color_rules, "cont" ) ) {	
		from = 0.000;
		to = 1.001;
		G_add_f_raster_color_rule (&from, 0, 0, 0, &to, 255, 255, 0, &colors);
	}
	if ( !strcmp ( color_rules, "stct" ) ) {	
		from = MINBPN_H1_2;
		to = MAXBPN_H1_2;
		G_add_f_raster_color_rule (&from, 0, 0, 0, &to, 255, 255, 0, &colors);
	}
	if ( !strcmp ( color_rules, "bins" ) ) {
		from = 0.000;
		to = 0.333;
		G_add_f_raster_color_rule (&from, 255, 0, 0, &to, 255, 0, 0, &colors);
		from = 0.334;
		to = 0.666;		
		G_add_f_raster_color_rule (&from, 255, 255, 0, &to, 255, 255, 0, &colors);
		from = 0.667;
		to = 1.001;		
		G_add_f_raster_color_rule (&from, 0, 255, 0, &to, 0, 255, 0, &colors);
	}
	if ( !strcmp ( color_rules, "stbs" ) ) {
		from = MINBPN_H1_2;
		to = MINBPN_H1_2 + ((MAXBPN_H1_2-MINBPN_H1_2) / 3);
		G_add_f_raster_color_rule (&from, 255, 0, 0, &to, 255, 0, 0, &colors);
		from = MINBPN_H1_2 + ((MAXBPN_H1_2-MINBPN_H1_2) / 3) + 0.001;
		to = MINBPN_H1_2 + (((MAXBPN_H1_2-MINBPN_H1_2) / 3) * 2 );
		G_add_f_raster_color_rule (&from, 255, 255, 0, &to, 255, 255, 0, &colors);
		from = MINBPN_H1_2 + (((MAXBPN_H1_2-MINBPN_H1_2) / 3) * 2 ) + 0.001;
		to = MAXBPN_H1_2 + 0.001;	
		G_add_f_raster_color_rule (&from, 0, 255, 0, &to, 0, 255, 0, &colors);
	}			
	sprintf (result_map, "%s.SITE.NOSITE", result_answer);	
	G_write_colors (result_map, G_mapset(), &colors);
	G_free_colors (&colors);

	/* clean up fp map stuff */
	G_free (cellbuf);
	G_free (fcellbuf);
	G_free (share_nat);
	G_free (share_smp);
	G_free (cat_count);
	if ( share_bias != NULL ) {
		for (i = 0; i < num_bias_maps; i ++) {
			G_free (share_bias[i]);
			G_free (mean_bias[i]);
		}
		G_free (share_bias);
		G_free (mean_bias);
		G_free (bias_cellbuf);
		G_free (bias_dcellbuf);
	}
	G_free (site_count);
	for (i = 0; i< n; i++) {
		G_free (cats_description[i]);
	}
	G_free (cats_description);	
}


/* this checks if all bias maps are valid FP maps with cell value 0.0 to 1.0 */
/* terminates the program if there are any problems */
void check_bias_maps (char **answers, int quiet) {

	int i;
	char *mapset;
	double min, max;	

	if (answers != NULL) {
		i = 0;
		while (answers[i] != NULL) {
			mapset = G_calloc (BUF_SIZE, sizeof (char));
			/* check if input map is a floating point map with min and max [0..1] */
			mapset = G_find_cell (answers[i],"");
			if ( mapset == NULL) {
				G_fatal_error ("Bias map '%s' does not exist in current location.",answers[i]);
			}
			if (!G_raster_map_is_fp (answers[i], mapset)) {
				G_fatal_error ("Bias map '%s' is not a floating point map.", answers[i]);		
    			}
			if (GT_get_f_range (answers[i],mapset,&min,&max,1-quiet) < 0) {
				G_fatal_error ("Bias map '%s' is not readable.",answers[i]);
			}
			if ((min < 0) || (max > 1)) {
				G_fatal_error ("Bias map '%s' has cells with values outside the range 0.0 to 1.0",answers[i]);
			}
			i ++;
		} 
	}
}


/* checks if all SITE bias attributes specified by user
   exist, are type DOUBLE and [0..1]
*/
double  **check_bias_atts ( char *site_file, char **atts, int quiet) {

	struct Cell_head region;
	char *site_mapset;
	struct Map_info in_vect_map;
	struct line_pnts *vect_points;
	struct line_cats *vect_cats;
	int cur_type;
	char errmsg [200];
	int nrows, ncols;
	int num_sites;
	int num_atts;
	int *num_vals;
	int i,j,k;
  
  	double **bias;
  
	/* site attribute management */
	struct field_info *field;
	char     buf[5000], *colname;   
	int      dbcol, dbncols, ctype, sqltype, more; 
	dbString sql, str;
	dbDriver *driver;
	dbHandle handle;
	dbCursor cursor;
	dbTable  *table;
	dbColumn *column;
	dbValue  *dbvalue;

	G_get_window (&region);
	nrows = G_window_rows ();
	ncols = G_window_cols ();

	vect_points = Vect_new_line_struct ();
	vect_cats = Vect_new_cats_struct ();

	if ((site_mapset = G_find_vector2 (site_file, "")) == NULL) {
	  sprintf (errmsg, "Could not find input vector map %s\n", site_file);
	  G_fatal_error ("%s",errmsg);
	}

	Vect_set_open_level (1);        
	if (1 > Vect_open_old (&in_vect_map, site_file, site_mapset)) {
	  sprintf (errmsg, "Could not open input vector points.\n");
	  G_fatal_error ("%s",errmsg);
	}

	/* filter vector objects to current region and point types only */
	Vect_set_constraint_region (&in_vect_map, region.north, region.south, 
			      region.east, region.west, 0.0, 0.0); 
	Vect_set_constraint_type (&in_vect_map, GV_POINT);

	/* get number of site bias attributes */
	num_atts = 0;
	if (atts != NULL) {		
		while (atts[num_atts] != NULL) {
			num_atts ++;
		} 
	}

  	/* calculate number of vector points in map and current region */
	num_sites = 0;
  	while ((cur_type = Vect_read_next_line (&in_vect_map, vect_points, NULL)) > 0) {     
      		num_sites ++;            
  	}
	
	/* create double arrays large enough to store all bias values */
	bias = G_malloc ( (signed) ( num_atts * sizeof ( double* )) );
	if ( bias == NULL ) {
		G_fatal_error ("Out of memory.\n");
	}
	for ( i = 0; i < num_atts; i ++ ) {
		bias[i] = G_malloc ( (signed) (num_sites * sizeof ( double )) );
		if ( bias [i] == NULL ) {
			G_fatal_error ("Out of memory.\n");
		}
		/* initialise all atts to ANULL (-1.11111...) */
		for ( j = 0; j < num_sites; j ++ ) {
			bias[i][j] = ANULL;
		}
	}
	
	/* this records the number of values read for each attribute */
	num_vals = G_malloc ( (signed) (num_atts * sizeof ( int )) );
	if (  num_vals == NULL ) {
		G_fatal_error ("Out of memory.\n");
	}
	for ( i = 0; i < num_atts; i ++ ) {
		num_vals [i] = 0;
	}		
		
  	/* rewind vector points file: close and re-open */
  	Vect_close (&in_vect_map);
	Vect_open_old(&in_vect_map, site_file, site_mapset);
	Vect_set_constraint_type (&in_vect_map, GV_POINT);
	Vect_set_constraint_region (&in_vect_map, region.north, region.south,
	                              region.east, region.west, 0.0, 0.0);

	k = 0;
	while ((cur_type = Vect_read_next_line (&in_vect_map, vect_points, vect_cats)) > 0) {    
		/* check for site attributes */
		for (i = 0; i < vect_cats->n_cats; i++) {
			field = Vect_get_field( &in_vect_map, vect_cats->field[i]);
			if ( field != NULL ) {
				db_init_string (&sql);
				driver = db_start_driver(field->driver);
				db_init_handle (&handle);
				db_set_handle (&handle, field->database, NULL);
				if (db_open_database(driver, &handle) == DB_OK){
					/* sql query */
					sprintf (buf, "select * from %s where %s = %d", field->table, 
									field->key, 
									vect_cats->cat[i]);
					db_set_string (&sql, buf);
			
					db_open_select_cursor(driver, &sql, &cursor, DB_SEQUENTIAL);
					table = db_get_cursor_table (&cursor);
					db_fetch (&cursor, DB_NEXT, &more );
					dbncols = db_get_table_number_of_columns (table);
					for( dbcol = 0; dbcol < dbncols; dbcol++) {
						column = db_get_table_column(table, dbcol);
						sqltype = db_get_column_sqltype (column);
						ctype = db_sqltype_to_Ctype(sqltype);
						dbvalue  = db_get_column_value(column);
						db_convert_value_to_string( dbvalue, sqltype, &str);
						colname = (char*) db_get_column_name (column);
						/* check if this is one of the bias atts */						
						for ( j = 0; j < num_atts; j ++ ) {
							if (!strcmp (colname, atts[j])){							
								if (ctype == DB_C_TYPE_DOUBLE) {
									/* store value */
									bias [j][k] = atof (db_get_string (&str));
								} else {
									G_warning ("Attribute '%s' found but not of type DOUBLE. Ignored.\n", atts[j]);
								}
							}
						}
						k ++; /* increment array position for attribute storage */
					}
					db_close_cursor(&cursor);
					db_close_database(driver);
					db_shutdown_driver(driver); 			
				} else {
					db_shutdown_driver(driver);
				}
			}
		}
    
	} /* END (loop through sites list) */
	Vect_close (&in_vect_map);
	
	fprintf ( stderr, "\nCHECK DONE.\n");	

	return ( bias );
}


/* MAIN */
int
main (int argc, char *argv[])
{
	struct GModule *module;
	struct
	{
		struct Option *input;
		struct Option *sites;
		struct Option *n_bias_maps;
		struct Option *s_bias_atts;
		struct Option *p0_threshold;
		struct Option *colormap;
		struct Option *output;			
		struct Option *logfile;
		struct Option *cachesize;
	}
	parm;
	
	struct
	{
		struct Flag *quiet;
		struct Flag *append;
	}
	flag;
	
	char result_str[BUF_SIZE] = "bpn.";
	char *mapset;
	int show_progress = 1; /* enable progress display by default */
	time_t systime;
	clock_t proctime;
	unsigned long timeused;
	unsigned int days, hours, mins, secs;
	struct History hist;	
	/* these vars are used to store information about the input map */
	int cats; /* number of categories in input map */
	long null_count; /* number of NULL cells */
	long nocat_count; /* number of cells that do not fall into the category range [0 .. n] */	
	
	double **bias_atts;

	/* setup some basic GIS stuff */
	G_gisinit (argv[0]);
	module = G_define_module ();
	module->description = "Calculates Basic Probability Numbers (BPN) for DST predictive models.";
	/* do not pause after a warning message was displayed */
	G_sleep_on_error (0);

	/* Parameters: */
	/* input = a map that shows the natural (complete) distribution */
	/* of a feature. */
	parm.input = G_define_standard_option (G_OPT_R_INPUT);
	parm.input->key = "raster";
	parm.input->type = TYPE_STRING;
	parm.input->required = YES;
	parm.input->gisprompt = "old,cell,raster";
	parm.input->description = "Raster evidence map";

	/* site map with known sites */
	parm.sites = G_define_standard_option (G_OPT_V_INPUT);
	parm.sites->key = "sites";
	parm.sites->type = TYPE_STRING;
	parm.sites->required = YES;
	parm.sites->description = "Vector map with sample points";

	parm.n_bias_maps = G_define_standard_option (G_OPT_R_INPUT);
	parm.n_bias_maps->key = "nbias";
	parm.n_bias_maps->required  = NO;
	parm.n_bias_maps->multiple = YES;
	parm.n_bias_maps->gisprompt = "old,fcell,raster";	
	parm.n_bias_maps->description = "Raster map(s) with 'NO SITE' bias [0..1]";
	
	/*
	parm.s_bias_atts = G_define_option ();
	parm.s_bias_atts->key = "sbias";
	parm.s_bias_atts->required  = NO;
	parm.s_bias_atts->multiple = YES;
	parm.s_bias_atts->description = "Vector attribute(s) with 'SITE' bias [0..1]";
	*/

	parm.p0_threshold = G_define_option ();
	parm.p0_threshold->key = "perror";
	parm.p0_threshold->required = NO;
	parm.p0_threshold->type = TYPE_DOUBLE;
	parm.p0_threshold->answer = "0.05";
	parm.p0_threshold->options = "0.0-1.0";
	parm.p0_threshold->description = "Significance level for statistical tests";

	/* base name for output maps */
	parm.output = G_define_option ();
	parm.output->key = "output";
	parm.output->type = TYPE_STRING;
	parm.output->required = NO;
	parm.output->description = "Output raster maps base name (overwrites existing)";

	/* type of colormap for output raster map(s) */
	parm.colormap = G_define_option ();
	parm.colormap->key = "color";
	parm.colormap->type = TYPE_STRING;
	parm.colormap->required = NO;
	parm.colormap->description = "Output maps color scheme";
	parm.colormap->options = "cont,bins,stct,stbs";
	parm.colormap->answer = "cont";

	/* Name of logfile. If given, operations will be verbosely logged */
	/* to this file. */
	parm.logfile = G_define_option ();
	parm.logfile->key = "logfile";
	parm.logfile->type = TYPE_STRING;
	parm.logfile->required = NO;
	parm.logfile->description = "Name of file to log operations to";
	
	/* number of lines to store in cache */
	parm.cachesize = G_define_option ();
	parm.cachesize->key = "cachesize";
	parm.cachesize->type = TYPE_INTEGER;
	parm.cachesize->answer = "-1";
	parm.cachesize->required = NO;
	parm.cachesize->description = "Raster rows to store in cache (-1 for auto)";
	
	/* append output to existing logfile ? */
	flag.append = G_define_flag ();
	flag.append->key = 'a';
	flag.append->description = "Append log output to existing ASCII file";
	
	/* quiet operation ? */
	flag.quiet = G_define_flag ();
	flag.quiet->key = 'q';
	flag.quiet->description = "Quiet operation: display minimal information";

	/* parse command line */
	if (G_parser (argc, argv))
	{
		exit (-1);
	}
	
	/* check for 'quiet' flag */
	if ( flag.quiet->answer ) {
		show_progress = 0;
	}

	/* write log output to a file? */
	if ( parm.logfile->answer == NULL ) {
		debug_mode = 0;
	}

	mapset = G_calloc (BUF_SIZE, sizeof (char));
	/* check if input map is a fully categorized raster map */
	mapset = G_find_cell (parm.input->answer,"");
	if ( mapset == NULL) {
		G_fatal_error ("Input map does not exist in the current location.");
	}
	if (G_raster_map_is_fp (parm.input->answer, mapset)) {
		G_fatal_error ("Input map is a floating point raster.\nOnly integer rasters are allowed as input.");
    	}
	
	/* check if sample sites file exists */
	if (G_find_file ("vector", parm.sites->answer, "") == NULL)
	{
		G_fatal_error
			("Vector map with samples does not exist.");
	}

	/* construct default output filename if none given */
	if (parm.output->answer == NULL)
	{
		sprintf (result_str, "bpn.%s", parm.input->answer);
		parm.output->answer = result_str;
		G_warning ("Using default base name '%s'\n", result_str);
	}

	/* check if a legal file name was given for output map */
	/* this overwrites existing maps! */
	if (G_legal_filename (parm.output->answer) == -1)
	{
		G_fatal_error
			("Base name for result maps invalid (contains special chars, whitespace or other).");
	}
	

	/* check if logfile is wanted and ... */
	if (parm.logfile->answer != NULL)
	{
		/* ... check if a legal file name was given for logfile */
		if (G_legal_filename (parm.logfile->answer) == -1)
		{
			G_fatal_error
			("Logfile name invalid (contains special chars, whitespace or other).");
		}
	}	

	/* set cachesize */
	cachesize = atoi (parm.cachesize->answer);
	if ( (cachesize<-1) || (cachesize > G_window_rows ()) ) {
		/* if cache size is invalid, just set to auto-mode (-1) */
		G_warning ("Invalid cache size requested. Must be between 0 and %i or -1 (auto).", G_window_rows());
		cachesize = -1;
	}

	cats = GT_get_stats (parm.input->answer,mapset,&null_count, &nocat_count, show_progress);
	if ( cats < 0 ) {
		G_fatal_error ("Could not stat input map. Do you have read access?");
	}
	if ( cats == 0 ) {
		G_fatal_error ("No categories defined in input map.");		
	}
	if ( nocat_count > 0 ) {
		G_fatal_error ("Input map contains cells that do not map to categories.\nUse 'r.categorize' to produce a fully categorized input map.");
	}
	
	
	/* check all sources of BIAS supplied by the user */
	check_bias_maps (parm.n_bias_maps->answers, flag.quiet->answer);
	
	/*
	if ( parm.s_bias_atts->answers != NULL ) {		
		bias_atts = check_bias_atts (parm.sites->answer,parm.s_bias_atts->answers, flag.quiet->answer);
	}
	*/
		
	/* open logfile */
	if (parm.logfile->answer != NULL)
	{
		if (flag.append->answer) {
			if (fopen (parm.logfile->answer, "r") == NULL) {
				logfile = fopen (parm.logfile->answer, "w+");
			} else {
				logfile = fopen (parm.logfile->answer, "a");
				if (logfile == NULL) {
					G_fatal_error ("Logfile error: '%s'.", strerror (errno));
				}
				fprintf (logfile,"\n\n * * * * * \n\n");
			}
		} else {
			logfile = fopen (parm.logfile->answer, "w+");
		}
		if (logfile == NULL) {
			G_fatal_error ("Logfile error: '%s'.", strerror (errno));
		}
		else
		{
			debug_mode = 1;
			fprintf (logfile,"This is %s version %.2f\n",argv[0],PROGVERSION);
			systime = time (NULL);
			fprintf (logfile,"Calculation started on %s",ctime(&systime));
			fprintf (logfile,"\tlocation   = %s\n",G_location());
			fprintf (logfile,"\tmapset     = %s\n",G_mapset());
			fprintf (logfile,"\tinput map  = %s\n",parm.input->answer);
			fprintf (logfile,"\tsites file = %s\n",parm.sites->answer);
			fprintf (logfile,"Results will be stored in '%s.<SITE|NOSITE|SITE.NOSITE>'\n\n",parm.output->answer);
			fflush (logfile);
		}
	}	
			
	
	/* do the actual calculations */
	write_BPNs (parm.input->answer, mapset, parm.sites->answer, parm.n_bias_maps->answers, parm.output->answer,
				(float) atof (parm.p0_threshold->answer), parm.colormap->answer, show_progress);			
	
	/* write all that remains to be written to logfile */
	if (parm.logfile->answer != NULL) {
		/* write advisory if necessary */
		if ( WARN_ON ) {
			fprintf (logfile,"\nAdvice on this calculation:\n");
			if ( WARN_N_TO_SMALL ) {
				fprintf (logfile,"\tIncrease sample size to at least %i\n",MIN_SAMPLE_SIZE);
			}
		}
		/* write processing time to logfile */
		proctime = clock ();
		timeused = (unsigned long) proctime / CLOCKS_PER_SEC;
		days = timeused / 86400;
		hours = (timeused - (days * 86400)) / 3600;
		mins = (timeused - (days * 86400) - (hours * 3600)) / 60;		
		secs = (timeused - (days * 86400) - (hours * 3600) - (mins * 60));
		systime = time (NULL);
		fprintf (logfile,"\nCalculation finished on %s",ctime(&systime));		
		fprintf (logfile,"Processing time: %id, %ih, %im, %is\n",
				days, hours, mins, secs );				
		fflush (logfile);
	}
	
	/* write some metadata to the output files' histories */
	G_short_history (parm.input->answer,"raster",&hist);
	
	strcpy (hist.datsrc_1, parm.input->answer);
	strcpy (hist.keywrd, "Generated by r.dst.bpn.");
	hist.edlinecnt = 2;
	
	strcpy (hist.edhist[0], "BPN values for hypothesis {h1}='site present'.");
	sprintf (result_str,"Significance threshold = %.3f",atof (parm.p0_threshold->answer));	
	strcpy (hist.edhist[1], result_str);		
	sprintf (result_str,"%s.SITE", parm.output->answer);
	G_write_history (result_str, &hist);
	
	strcpy (hist.edhist[0], "BPN values for hypothesis {h2}='no site present'.");
	sprintf (result_str,"Significance threshold = %.3f",atof (parm.p0_threshold->answer));			
	strcpy (hist.edhist[1], result_str);
	sprintf (result_str,"%s.NOSITE", parm.output->answer);	
	G_write_history (result_str, &hist);
	
	strcpy (hist.edhist[0], "BPN values for hypothesis {h1,h2}='site present OR no site present'.");					
	sprintf (result_str,"Significance threshold = %.3f",atof (parm.p0_threshold->answer));	
	strcpy (hist.edhist[1], result_str);
	sprintf (result_str,"%s.SITE.NOSITE", parm.output->answer);
	G_write_history (result_str, &hist);
				
	return (EXIT_SUCCESS);
}
