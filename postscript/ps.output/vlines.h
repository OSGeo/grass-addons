#ifndef _VLINES_H_
#define _VLINES_H_

/* Header file: vlines.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */


#include "colors.h"
#include "lines.h"
#include <grass/gis.h>


typedef struct
{
    int type;			/* line or boundary */

    PSLINE line;
    PSLINE hline;

    char *idcol;		/* if set, id rule for legend */
    char *rgbcol;		/* line color from database */

    double offset;		/* offset parallel line */

} VLINES;

#endif
