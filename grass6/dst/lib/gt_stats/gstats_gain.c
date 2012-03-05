#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include <grass/gis.h>

/* Purpose: calculate Kvamme's gain index */

double gstats_gain_K (double sample, double area) {
	
	double kvamme_gain = 0;
					
	if (sample > area) {
		if ( area == 0 ) {
			kvamme_gain = 1;
		} else {
			kvamme_gain = 1 - ( area / sample );
		}
	}

	if (sample < area) {
		if ( sample == 0 ) {
			kvamme_gain = -1;
		} else {
			kvamme_gain = (-1) + ( sample / area );
		}
	}

	return (kvamme_gain);
};
