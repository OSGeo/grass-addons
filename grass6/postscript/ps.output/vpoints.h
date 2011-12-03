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
    int type;			/* centroid, point, boundary or line */
    char *symbol;

    PSLINE line;
    PSCOLOR fcolor;

    double size, scale, bias;	/* standard size, scale and bias to draw */
    char *sizecol;		/* size from database or rule */

    double rotate;		/* standard rotate */
    char *rotatecol;		/* rotate from database */

    PSLINE cline;		/* conection line */
    double distance;		/* distance between symbols on the conection line */
    double voffset;		/* vertical offset of the symbol */

} VPOINTS;

#endif
