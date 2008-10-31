/* MOD35 snow/ice flag unsigned int bits [12]
 * 0 -> class 0: Yes
 * 1 -> class 1: No
 */  

#include "grass/gis.h"

CELL stateqa500h(CELL pixel) 
{
    CELL qctemp;

    pixel >>= 12;
    qctemp = pixel & 0x01;

    return qctemp;
}


