#ifndef _NOTES_H_
#define _NOTES_H_

/* Header file: notes.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdio.h>
#include "fonts.h"
#include "frames.h"

typedef struct
{
    PSFRAME box;
    PSFONT font;

    char text[1024];

    double angle;
    double width;

} NOTES;

#endif
