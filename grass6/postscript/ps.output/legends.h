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

#define TITLE_LEN   60


typedef struct
{
    PSFRAME box;		/* frame box */

    char title[TITLE_LEN];	/* text title */
    PSFONT title_font;		/* title font */

    PSFONT font;		/* legend font */

    int cols;			/* number of columns */
    double width;		/* symbol width  */
    double xspan;		/* separation between columns */
    double yspan;		/* separation between rows */

} LEGEND;

#endif
