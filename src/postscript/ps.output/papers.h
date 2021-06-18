#ifndef _PSPAPER_H_
#define _PSPAPER_H_

/* Header file: papers.h
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
    char *name;
    int width, height;
    double left, right, top, bot;
    PSCOLOR fcolor;

} PAPER;

#endif
