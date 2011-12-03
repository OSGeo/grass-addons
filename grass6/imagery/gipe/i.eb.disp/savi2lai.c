#include<stdio.h>
#include<stdlib.h>
#include<math.h>

/* Found in Pawan (2004) */

double savi_lai(double savi)
{
    double result;

    if (savi < 0.1) {
	result = 0.00001;
    }
    else if (savi > 0.689) {
	result = 6.0;
    }
    else {
	result = -(log((0.69 - savi) / 0.59) / 0.91);
    }

    return result;
}
