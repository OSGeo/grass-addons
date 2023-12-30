#include <stdio.h>
#include <stdlib.h>

/* Difference of temperature between surface skin and about 2m
 * Initialization parameter of sensible heat flux iteration in SEBAL
 * Found in Pawan (2004)
 */

double delta_t(double tempk)
{
    double result;

    result = -321.147 + 1.095 * tempk;
    if (result < 1) {
        result = 1.0;
    }
    else if (result > 13) {
        result = 13.0;
    }
    return result;
}
