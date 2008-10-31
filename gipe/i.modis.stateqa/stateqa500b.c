/* cloud shadow unsigned int bits[2]
 * 0 -> class 0: yes
 * 1 -> class 1: no
 */  

#include "grass/gis.h"

CELL stateqa500b(CELL pixel) 
{
    CELL qctemp;

    pixel >>= 2;
    qctemp = pixel & 0x01;

    return qctemp;
}


