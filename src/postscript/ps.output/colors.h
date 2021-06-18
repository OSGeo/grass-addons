#ifndef _PSCOLOR_H_
#define _PSCOLOR_H_

/* Header file: colors.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

typedef struct
{
    int none;
    double r, g, b;
    double a;
} PSCOLOR;

#endif
