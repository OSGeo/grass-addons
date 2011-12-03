#ifndef _PSGRID_H_
#define _PSGRID_H_

/* Header file: grids.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */


#include "fonts.h"
#include "lines.h"

typedef struct
{
    int sep;			/* major separation between lines */
    PSLINE line;

    PSFONT font;
    PSCOLOR fcolor;
    int lsides;			/* label, default 2 sides, else 4 */

    int msep;			/* minor separation between lines */
    PSLINE mline;

    int format;			/* border formats: 0 inner, 1 outer, ... */
    int trim;			/* digits of labels to cutoff if zero */
    double cross;		/* length of not LL crosses */
    int msubdiv;
} GRID;

#endif
