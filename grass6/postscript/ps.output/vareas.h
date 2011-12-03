#ifndef _VAREAS_H_
#define _VAREAS_H_

/* Header file: vareas.h
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
    PSLINE line;

    PSCOLOR fcolor;

    char *rgbcol;		/* if set, fcolor for legend */
    char *idcol;		/* if set, id rule for legend */

    char *name_pat;		/* name of pattern */
    double lw_pat;		/* pattern linewidth */
    double sc_pat;		/* pattern scale */
    int type_pat;		/* private: 1 colored pattern, 2 uncolored pattern */

    double width;		/* width of area */
    int island;			/* draw island */

} VAREAS;

#endif
