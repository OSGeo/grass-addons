#ifndef _PSDRAW_H_
#define _PSDRAW_H_

/* Header file: draws.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include "fonts.h"

#define MAX_DRAWS    100

typedef struct
{
    int flag[MAX_DRAWS];	/* paper (watermark), free or none (clip to map) */
    char *key[MAX_DRAWS];
    char *data[MAX_DRAWS];

} PSDRAW;

#endif
