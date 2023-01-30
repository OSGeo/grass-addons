/***********************************************************************/
/*
   azimuth.h

   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 17/08/2000, for r.horizon in GRASS 5.x

   NOTES

 */

/***********************************************************************/

#ifndef AZIMUTH_H
#define AZIMUTH_H

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

void calc_azimuth(int, int, int *, int *, double *, double *, double *,
                  double *);
/* calc_azimuth (row, col, axis, quadrant, smallest azimuth, centre azimuth,
   largest azimuth, distance) */

#endif
