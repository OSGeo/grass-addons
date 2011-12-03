#ifndef _SCALEBAR_H_
#define _SCALEBAR_H_

/* Header file: scalebar.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdio.h>
#include "fonts.h"
#include "frames.h"


/* units options */
#define SB_UNITS_AUTO	0
#define SB_UNITS_METERS	1
#define SB_UNITS_KM	    2
#define SB_UNITS_FEET	3
#define SB_UNITS_MILES	4
#define SB_UNITS_NMILES	5

typedef struct
{
    char type;
    double length, height;

    PSFRAME box;
    PSFONT font;
    PSCOLOR fcolor;

    int labels, segments;	/* normal segments */
    int sublabs, subsegs;	/* first segment subdivisions */

    int ucode;
    char units[50];

} SCALEBAR;

#endif
