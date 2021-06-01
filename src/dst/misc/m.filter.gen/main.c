/*

  PROGRAM:      m.filter.gen
  AUTHOR(S):    Benjamin Ducke <benjamin.ducke AT oadigital.net>
  PURPOSE:      Outputs different types of filters for use with r.mfilter(.fp).

  USAGE:	Run from within GRASS GIS.
  		   Use --help flag for usage instructions.

  COPYRIGHT:    (C) 2011 by Benjamin Ducke

                This program is free software under the GNU General Public
                License (>=v2). Read the file COPYING that comes with GRASS
                for details.
*/

/*

NOTES

Produce the following types of filters:

- mean (square or round)
- gaussian
- laplacian
- single line with any length and orientation (destriping)

Geometric operations (rotate):
http://homepages.inf.ed.ac.uk/rbf/HIPR2/geomops.htm



*/

#define TYPE_MEAN 0 /* simple mean, with different shapes */
#define TYPE_GAUSS 1 /* gaussian, fixed shape */
#define TYPE_LAPLACE 2 /* laplacian, fixed shape */
#define TYPE_DIRECTM 3 /* directional mean filter, definable rotation and x/y dims */

#define VERSION "1.00"

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include <grass/gis.h>

# GLOBAL VARS
int MODE = TYPE_MEAN; /* default filter type */

/* module options and flags */
struct GModule *module;
struct Option *type; /* filter type */
struct Option *divisor; /* filter divisor; default=0 */
struct Option *radiusx; /* filter radius in   */
struct Option *sigma; /* Gaussian: sigma */
struct Option *shape; /* Mean: geometric shape of filter */
struct Option *opt_max_dist, *output, *opt_seed, *opt_sample;
struct Option *sites;
struct Option *fieldopt;
struct Option *curvature_corr;
struct Option *spot, *offseta, *offsetb, *azimuth1, *azimuth2, *vert1, *vert2, *radius1, *radius2;
/* parallel filtering: always use unmodified input cells
	neighborhood to calculate new cell value */
struct Flag *parallel; 

/*
	Generates a Gaussian shape filter description.
*/
int gen_gauss ( int cols, int rows ) {
	/* gauss bell variables */
	double w[cols][rows]; /* cell weights (exact) */
	int n; /* approximation steps in each direction from center */
	double s; /* sigma */
	double s2;
	double a;
	double sum;
	
	/* approximated gauss bell */
	int wi[cols][rows]; /* cell weights (integer) */
	double min;
	double max;
	double m_i;
	int sum_i;
	
	/* looping vars */
	int i,j,x,y;
	double checksum;
		
}


int main ( int argc, char *argv[] ) 
{


	/* program options 
	int option;
	int option_index = 0;
	static struct option long_options[] = {
		{ "nsteps", 1, NULL, 'n' },
		{ "sigma", 1, NULL, 's' },
		{ "mfilter", 0, NULL, 'm' },
		{ "total", 0, NULL, 't' },
		{ "integer", 0, NULL, 'i' },
		{ "help", 0, NULL, 'h' },
		{ 0, 0, 0, 0 }
	};
	*/

	/* default settings */
	n = 2;
	s = 1.0;
	format_mfilter = 0;
	print_sum = 0;
	integer = 0;


	/* check options */
	if ( n < 1 ) {
		fprintf (stderr, "ERROR: 'n' must be larger or equal than '1'.\n");
		exit (1);				
	}
	if ( s <= 0.0 ) {
		fprintf (stderr, "ERROR: 's' must be larger than '0.0'.\n");
		exit (1);				
	}
	if ( format_mfilter && print_sum ) {
		fprintf (stderr, "WARNING: sum total will not be printed for mfilter output.\n");
	}

	/* compute "exact" gauss bell */
	s2 = 2 * pow ( s,2 );
	sum = 0;
	for ( y = -n; y <= n; y ++ ) {
		j = y + n;
		for ( x = -n; x <= n; x ++ ) {
			i = x + n;
			a = ( pow((double)x,2) + pow((double)y,2) ) / s2;
			w[i][j] = exp (-a);
			sum = sum + w [i][j]; /* sum of weights */
		}
	}

	/* check for sane kernel shape */
	checksum = 0;
	for ( x = -n; x <= n; x ++ ) {
		i = x + n;
		checksum = checksum + w[i][0];
	}
	if ( checksum < 0.001 ) {
		fprintf (stderr, "WARNING: Kernel dimensions too large. Sigma should be increased.\n");
	}

	if ( integer ) {
		/* compute integer version of bell */
		max = w[n][n];
		min = w[0][0];
		if ( min < 0.001 ) {
			/* avoid division by zero problem */
			min = 0.001;
		}
		m_i = round ((max / min) * 2 ); /* integer multiplication factor */
		sum_i = 0;
		for ( y = -n; y <= n; y ++ ) {
			j = y + n;
			for ( x = -n; x <= n; x ++ ) {
				i = x + n;
				wi[i][j] = (int) round (m_i*w[i][j]);
				/* guard against hitting integer size limit */
				if ( wi[i][j] < 0 ) {
					fprintf (stderr, "ERROR: Integer overflow.\n");
					exit (1);				
				}
				sum_i = sum_i + wi [i][j];
			}
		}
	}

	/* print filter matrix */
	if ( format_mfilter ) {	
		/* print in mfilter format */
		fprintf ( stdout, "TITLE %ix%i Gaussian\n", (2*n+1), (2*n+1) );
		fprintf ( stdout, "MATRIX %i\n", (2*n+1) );
		for ( j = 0; j < (2*n+1) ; j ++ ) {				
			for ( i = 0; i < (2*n+1) ; i ++ ) {
				if ( integer )
					fprintf ( stdout, "%i", wi[i][j] );
				else 
					fprintf ( stdout, "%.3f", w[i][j] );
				if ( i < (2*n) )
					fprintf ( stdout, " " );
			}
			fprintf ( stdout, "\n" );
		}
		fprintf ( stdout, "DIVISOR 0\n" );
		fprintf ( stdout, "TYPE P\n" );
	} else {
		/* print as raw data dump */
		for ( j = 0; j < (2*n+1) ; j ++ ) {				
			for ( i = 0; i < (2*n+1) ; i ++ ) {
				if ( integer )
					fprintf ( stdout, "%i\t", wi[i][j] );
				else
					fprintf ( stdout, "%.3f\t", w[i][j] );
			}
			fprintf ( stdout, "\n" );
		}
		if ( print_sum ) {
			if ( integer )
				fprintf ( stdout, "sum=%i\n", sum_i );
			else
				fprintf ( stdout, "sum=%.3f\n", sum );
		}
	}

	return (0);
}

