#ifndef _LEGEND_H_
#define _LEGEND_H_

/* Header file: legends.h
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
    PSFRAME box;        /* frame box */
    PSFONT font;        /* legend font */

	int cols;           /* column number */
    double span;        /* column separation */
    double width;       /* symbol width  */

    char title[51];     /* text title */
    PSFONT title_font;  /* title font */
} LEGEND;

#endif
