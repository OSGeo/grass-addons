#include<stdio.h>
#include<math.h>
#include<stdlib.h>

    /* Conversion of DN to Radiance for Landsat 5TM */ 
double dn2rad_landsat5(int c_year, int c_month, int c_day, int year,
			int month, int day, int band, int DN) 
{
    double result, gain, bias;

    int gain_mode;

    if (c_year < 2003) {
	gain_mode = 1;
    }
    else if (c_year == 2003) {
	if (c_month < 5) {
	    gain_mode = 1;
	}
	else if (c_month == 5) {
	    if (c_day < 5) {
		gain_mode = 1;
	    }
	    else {
		gain_mode = 2;
	    }
	}
	else {
	    gain_mode = 2;
	}
    }
    else if (c_year > 2003 && c_year < 2007) {
	gain_mode = 2;
    }
    else if (c_year == 2007) {
	if (c_month < 5) {
	    gain_mode = 2;
	}
	else if (year < 1992) {
	    gain_mode = 3;
	}
	else {
	    gain_mode = 4;
	}
    }
    if (gain_mode == 1) {
	if (band == 1) {
	    gain = 0.602431;
	    bias = -1.52;
	}
	if (band == 2) {
	    gain = 1.175100;
	    bias = -2.84;
	}
	if (band == 3) {
	    gain = 0.805765;
	    bias = -1.17;
	}
	if (band == 4) {
	    gain = 0.814549;
	    bias = -1.51;
	}
	if (band == 5) {
	    gain = 0.108078;
	    bias = -0.37;
	}
	if (band == 6) {
	    gain = 0.055158;
	    bias = 1.2378;
	}
	if (band == 7) {
	    gain = 0.056980;
	    bias = -0.15;
	}
    }
    if (gain_mode == 2) {
	if (band == 1) {
	    gain = 0.762824;
	    bias = -1.52;
	}
	if (band == 2) {
	    gain = 1.442510;
	    bias = -2.84;
	}
	if (band == 3) {
	    gain = 1.039880;
	    bias = -1.17;
	}
	if (band == 4) {
	    gain = 0.872588;
	    bias = -1.51;
	}
	if (band == 5) {
	    gain = 0.119882;
	    bias = -0.37;
	}
	if (band == 6) {
	    gain = 0.055158;
	    bias = 1.2378;
	}
	if (band == 7) {
	    gain = 0.065294;
	    bias = -0.15;
	}
    }
    if (gain_mode == 3) {
	if (band == 1) {
	    gain = 0.668706;
	    bias = -1.52;
	}
	if (band == 2) {
	    gain = 1.317020;
	    bias = -2.84;
	}
	if (band == 3) {
	    gain = 1.039880;
	    bias = -1.17;
	}
	if (band == 4) {
	    gain = 0.872588;
	    bias = -1.51;
	}
	if (band == 5) {
	    gain = 0.119882;
	    bias = -0.37;
	}
	if (band == 6) {
	    gain = 0.055158;
	    bias = 1.2378;
	}
	if (band == 7) {
	    gain = 0.065294;
	    bias = -0.15;
	}
    }
    if (gain_mode == 4) {
	if (band == 1) {
	    gain = 0.762824;
	    bias = -1.52;
	}
	if (band == 2) {
	    gain = 1.442510;
	    bias = -2.84;
	}
	if (band == 3) {
	    gain = 1.039880;
	    bias = -1.17;
	}
	if (band == 4) {
	    gain = 0.872588;
	    bias = -1.51;
	}
	if (band == 5) {
	    gain = 0.119882;
	    bias = -0.37;
	}
	if (band == 6) {
	    gain = 0.055158;
	    bias = 1.2378;
	}
	if (band == 7) {
	    gain = 0.065294;
	    bias = -0.15;
	}
    }
    result = gain * (double)DN + bias;
    return result;
}


