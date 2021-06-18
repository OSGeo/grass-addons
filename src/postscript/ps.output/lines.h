#ifndef _PSLINE_H_
#define _PSLINE_H_

/* Header file: lines.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */


#include "colors.h"

/* line end style */
#define LINECAP_BUTT    0
#define LINECAP_ROUND   1
#define LINECAP_EXTBUTT 2

/* line join style */
#define LINEJOIN_MITER  0
#define LINEJOIN_ROUND  1
#define LINEJOIN_BEVEL  2


typedef struct
{
    double width;		/* width of line */
    PSCOLOR color;		/* color of line */
    int cap;			/* linecap style */
    int join;			/* linejoin style */
    char *dash;			/* dash ps format */
    int odash;			/* offset dash */
} PSLINE;

#endif
