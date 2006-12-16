#include<stdio.h>
#include<math.h>
#include<stdlib.h>

// Broadband albedo MODIS
// yann.chemin@ait.ac.th LGPL, Copylefted, 2004.

double bb_alb_modis( double redchan, double nirchan, double chan3, double chan4, double chan5, double chan6, double chan7 )
{
	double	result;
	
	if( nirchan < 0 || redchan < 0 || chan3 < 0 || chan4 < 0 || chan5 < 0 || chan6 < 0 || chan7 < 0){
		result = -1.0;
	} else {
		result = ((0.22831*redchan + 0.15982*nirchan + 0.09132*(chan3+chan4+chan5) + 0.10959*chan6 + 0.22831*chan7 ) / 10000.0 ) ;
	}

	return result;
}

