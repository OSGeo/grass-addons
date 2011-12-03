#include<stdio.h>
#include<stdlib.h>
#include<math.h>

/* Found in Pawan (2004) */

double dis_p(double lai)
{
    double result;

    result =
	1 * (1 -
	     ((1 - exp(-(pow(20.6 * lai, 0.5)))) / (pow(20.6 * lai, 0.5))));

    return result;
}
