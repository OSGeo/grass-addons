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
    char *rgbcol;       /* if set, fcolor for legends */

    int type_pat;       /* private: 1 colored pattern, 2 uncolored pattern */
    char *pat;          /* name of pattern */
    double pwidth;      /* pattern width */
    double scale;       /* pattern scale */

    double width;       /* width of area */

} VAREAS;

#endif
