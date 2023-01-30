/***********************************************************************/
/*
   file.h

   Revised by Mark Lake, 28/07/20017, for r.skyline in GRASS 7.x
   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 17/08/2000, for r.horizon in GRASS 5.x

   NOTES

 */

/***********************************************************************/

#ifndef FILEH
#define FILEH

#include <stdio.h>
#include <grass/gis.h>
#include <grass/glocale.h>

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

FILE *Create_file(char *, char *, char *, int);

/* Create_file (name, suffix, string for message, overwrite flag) */

#endif
