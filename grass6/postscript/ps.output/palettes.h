#ifndef _PALETTE_H_
#define _PALETTE_H_

/* Header file: palette.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

typedef struct
{
    char name[50];
    double h, s, v;
} PALETTE;


#ifdef MAIN
PALETTE *Palette;
int ncolors;
#else
extern PALETTE *Palette;
extern int ncolors;
#endif


#endif
