#ifndef _PSFRAME_H_
#define _PSFRAME_H_

/* Header file: frames.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */


#include "colors.h"

typedef struct
{
    double x, y;		/* left-top corner */
    double xset, yset;		/* x and y offset */
    int xref, yref;		/* reference point */

    double border;		/* outer border width */
    PSCOLOR color;		/* border color */

    PSCOLOR fcolor;		/* fill color */

    double margin;		/* inner margin */
    double rotate;

} PSFRAME;

#endif
