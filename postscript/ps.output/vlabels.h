#ifndef _VLABELS_H_
#define _VLABELS_H_

/* Header file: vlabels.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */


#include "fonts.h"
#include "frames.h"

typedef struct
{
    int type;

    PSFRAME box;
    PSFONT font;

    char *labelcol;		/* label from database */
    int decimals;		/* number of decimals */

    double style;

} VLABELS;

#endif
