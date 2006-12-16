#include<stdio.h>
#include<math.h>
#include<stdlib.h>
#include"functions.h"

// Broadband albedo NOAA AVHRR 14 (maybe others too but not sure)
// yann.chemin@ait.ac.th LGPL, Copylefted, 2004.

double bb_alb_noaa( double redchan, double nirchan )
{
	double	result;
	
	if( nirchan < 0 || redchan < 0 ){
		result = -1.0;
	} else {
		result = (( 0.035+ 0.545*nirchan - 0.32*redchan) / 10000.0 ) ;
	}

	return result;
}

