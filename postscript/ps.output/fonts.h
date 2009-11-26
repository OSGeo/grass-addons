#ifndef _PSFONT_H_
#define _PSFONT_H_

/* Header file: fonts.h
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
    char name[50];
    double size;
    double extend;
    PSCOLOR color;
} PSFONT;

#endif
