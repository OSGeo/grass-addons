/* 
 * FUNCTIONS FOR CALCULATION OF THE ORIGINAL XTENT MODEL AND A NORMALIZED VARIATION
 */


#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>

#include "globals.h"
#include "tools.h"
#include "gt_vector.h"
#include "geom.h"


/* Returns the record number (0..n) of the vector point that is closest
   to the location specified by x and y as given by the original Xtent model
   
   costs is an array of doubles that stores the value of the cost surface map(s) for each center at x and y
   
   Returns -1 on error,
   id of most influential center (0..n), otherwise
   
*/
int get_center_xtent_original ( double x, double y, double *C, double a, double k, double *costs, double *reach, int *ruler, GVT_map_s *map ) {
	int i;
	int center;
	double I;
	double d;
	double max;
	int max_set;
	int within_reach;

	/* TODO:
		speed-up: read point coordinates from array instead of vector map
		better: leave attribute and coordinate caching to GT_vector lib routines
	*/
	GVT_rewind ( map );
	max = 0.0;
	max_set = 0;
	I = -1.0;
	center = -1;
	i = 0;
	while ( GVT_next ( map ) ) {
		within_reach = 0;
		d = get_distance ( x, y , costs, map );
		I = pow(C[i],a) - (k*d);
		if ( reach[i] >= 0.0 ) { /* we have a center with constrained reach */
			if ( d <= reach[i] ) {
				/* this center is within reach! */
				within_reach = 1;
			} 
		} else {
			/* reach checking was turned off */
			within_reach = 1;
		}		
		if ( DEBUG > 1) {
			fprintf ( stderr, "I = %.10f^%.10f - %.10f*%.10f = %.10f\n", C[i], a, k, d, I );
		}
		if ( (!max_set) && (within_reach)) {
			max = I;
			max_set = 1;
			center = ruler[i];
		} else {
			if ( (I > max) && (within_reach) ) {
				max = I;
				center = ruler[i];
			}
		}
		i ++;
	}

	if ( flag.strict->answer ) {
		if ( max < 0 ) {
			return ( -1 );
		}
	}
	
	return ( center );
}


/* Returns the record number (0..n) of the vector point that is * second * most influential
   to the location specified by x and y as given by the Xtent model
   
   *diff is set to the absolute difference between first and second highest I
   
   Returns -1 on error,
   id of second most influential center (0..n), otherwise   
*/
int get_center_xtent_second ( double x, double y, double *C, double a, double k, double *diff, double *costs, int *ruler, GVT_map_s *map ) {
	int i,j;
	int second;
	int matched;
	double *sorted;
	double *unsorted;
	double I;
	double d;
	double val;
	
	/* make array to store I values for all centers in input map */
	sorted = G_malloc ( num_centers * sizeof ( double ) );
	unsorted = G_malloc ( num_centers * sizeof ( double ) );
	
	/* step through the input vector map and calculate I for all centers */
	GVT_rewind ( map );
	i = 0;
	while ( GVT_next ( map ) ) {
		d = get_distance ( x, y , costs, map );
		I = pow(C[i],a) - (k*d);
		sorted[i] = I;
		unsorted[i] = I;
		i ++;
	}
	
	/* now sort all I values ascendingly and pick the second highest one that is NOT ruled by
	   another center (if all are ruled, then there is no competitor and we return -1!) */
	quicksort ( sorted, num_centers );
	matched = 0;
	second = -1;
	val = -1.0;
	for ( i = num_centers - 2; i >= 0; i -- ) {
		/* get ID of the center at this position in the sorted array */
		for ( j = 0; j < num_centers; j ++ ) {
			if ( unsorted[j] == sorted[i] ) {
				second = j;
			}
		}
		if ( (ruler[second] == second) && (!matched) ) {
			val = sorted [ i ];
			matched = 1;
		}
	}
	if ( !matched ) {
		return ( -1 );
	}
	
	/* store absolute difference between first and second highest I */
	*diff = fabs ( sorted[num_centers-1] - sorted[num_centers-2] );

	/* get the ID of the center that corresponds to competitor's ID and return it */
	for ( i=0; i < num_centers; i++ ) {
			if ( unsorted[i] == val ) {
				if ( flag.strict->answer ) {
					/* in strict mode, second I < 0 is also invalid! */
					if ( unsorted[i] < 0 ) {
						return ( -1 );
					}
				}
				return ( i );
			}
	}
	
	return ( -1 );
}


