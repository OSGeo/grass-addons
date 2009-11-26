#ifndef _VPOINTS_H_
#define _VPOINTS_H_

/* Header file: vpoints.h
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


typedef struct
{
    int type;           /* centroid or point */
    char *symbol;

    double scale;

    PSLINE line;
    PSCOLOR fcolor;

    double size;
    char * sizecol;

    double rotate;
    char * rotatecol;

} VPOINTS;

#endif
