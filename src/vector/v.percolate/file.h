/***********************************************************************/
/*
   file.h

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
void Create_CSV(char *, long int, int);

/* Create_file (name, numpoints, overwrite flag) */
void Create_intermediate_group_CSV(char *, int, int, int);

/* void Create_intermediate_group_CSV (filename, nextNewGroup, iteration,
 * overwrite) */
void Create_final_group_CSV(char *, int, int, int);

/* void Create_final_group_CSV (filename, numpoints, iteration, overwrite) */

#endif
