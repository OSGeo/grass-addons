#include<stdio.h>
#include<math.h>
#include<stdlib.h>

    /* Broadband albedo Landsat 5TM and 7ETM+ (maybe others too but not sure) */ 
double bb_alb_landsat(double bluechan, double greenchan, double redchan,
		       double nirchan, double chan5, double chan7) 
{
    double result;

    if (bluechan < 0 || greenchan < 0 || redchan < 0 || nirchan < 0 ||
	  chan5 < 0 || chan7 < 0) {
	result = -1.0;
    }
    else {
	result =
	    (0.293 * bluechan + 0.274 * greenchan + 0.233 * redchan +
	     0.156 * nirchan + 0.033 * chan5 + 0.011 * chan7);
    }
    return result;
}


