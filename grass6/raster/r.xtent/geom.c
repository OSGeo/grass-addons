/* 
 * PRIMITIVE GEOMETRY FUNCTIONS UTILIZED BY FUNCTIONS IN xtent.c
 */


#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>

#include "globals.h"
#include "gt_vector.h"


/* returns the record number of the vector point record that is spatially closest
	to the point specified by x and y
*/
int get_closest_point ( double x, double y, GVT_map_s *map ) {
	long int i;
	long int closest;
	double d;
	double min = 0.0;
	int min_set = 0;
	
	GVT_rewind ( map );
	i = 0;
	closest = 0;
	while ( GVT_next ( map ) ) {
		i ++;
		d = GVT_get_2D_point_distance ( x, y, map );
		if ( !min_set ) {
			min = d;
			min_set = 1;
		} else {
			if ( d < min ) {
				min = d;
				closest = i-1;
			}
		}		
	}
	
	return ( closest );
	
}


/* returns distance of point x,y to current point in *map */
double get_distance ( double x, double y, double *costs, GVT_map_s *map ) {

	long int i;

	if ( DISTANCE == STRAIGHT ) {	
		return ( GVT_get_2D_point_distance ( x, y, map ) );	
	}

	if ( DISTANCE == COST ) {
		i = GVT_get_current (map);
		return ( costs[i] );
	}
		
	return ( 0.0 );
}


/* get maximum distance to sites in *map for all raster cells in current region */
double get_max_distance_region ( GVT_map_s *map ) {
	struct Cell_head window;
	
	int row, col;
	int nrows, ncols;
	double x, y;

	double dist, max_dist;
	
	G_get_window (&window);
    	nrows = G_window_rows ();
	ncols = G_window_cols ();	
		
	if ( PROGRESS ) {
		fprintf ( stdout, " Finding maximum distance for all centers.\n" );
		fflush ( stdout );
	}
		
	max_dist = 0.0;
	for (row=0; row < nrows; row ++) {
		y = G_row_to_northing ( (double) row, &window );
		for (col=0; col < ncols; col ++) {
			x = G_col_to_easting ( (double) col, &window );
			/* TODO: bottle neck: implement coordinate caching in gt_vector.c */
			GVT_rewind ( map );
			while ( GVT_next ( map ) ) {
				dist = GVT_get_2D_point_distance ( x, y, map );
				if ( dist > max_dist ) {
					max_dist = dist;
				}	
			}				
		}
		if ( PROGRESS ) {
			G_percent (row, (nrows-1), 2);
			fflush ( stdout );
		}				
	}
	
	return ( max_dist );
}


/* find biggest C in all centers */
double get_max_size ( double *C, GVT_map_s *map ) {

	long int i;
	double max_C;

	/* TODO: get rid of *C when internal attribute caching is done in vect tools lib */
	max_C = 0.0;
	GVT_rewind ( map );
	i = 0;
	while ( GVT_next ( map ) ) {
		i ++;
		if ( C[i] > max_C ) {
			max_C = C[i];
		}	
	}
	
	return ( max_C );
}

