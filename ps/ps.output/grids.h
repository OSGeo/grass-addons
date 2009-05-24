#ifndef _PSGRID_H_
#define _PSGRID_H_

/* Header file: grids.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */


#include "fonts.h"
#include "lines.h"

typedef struct
{
    int sep;         /* major separation between lines */
    PSLINE line;

    PSFONT font;
    PSCOLOR fcolor;

    int msep;        /* minor separation between lines */
    PSLINE mline;

    int format;      /* formats: 0 inner, 1 outer, ... */
    int round;       /* digits to cut if zero */
    double cross;    /* length of crosses */
} GRID;

#endif
