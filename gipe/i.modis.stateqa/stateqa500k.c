/* Internal Snow Mask unsigned int bits[15]
 * 0 -> class 0: Snow
 * 1 -> class 1: No snow
 */  

#include "grass/gis.h"

CELL stateqa500k(CELL pixel) 
{
    CELL qctemp;

    pixel >>= 15;
    qctemp = pixel & 0x01;

    return qctemp;
}


