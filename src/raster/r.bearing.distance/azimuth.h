/***********************************************************************/
/*
   azimuth.h

   Revised by Mark Lake, 10/08/2017, for r.azimuth.distance in GRASS 7.x
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

double calc_azimuth(int, int, int);

/* calc_azimuth (row, col, reverse) */

double calc_azimuth_axial_diff(double, double);

/* calc_azimuth_diff (reference bearing, bearing) */

double calc_azimuth_axial_diff_signed(double, double);

/* calc_azimuth_diff (reference bearing, bearing) */

double calc_azimuth_clockwise_diff(double, double);

/* calc_azimuth_diff (reference bearing, bearing) */

int calc_segment(double);

/* int calc_segment (double diff) */

double calc_distance(int, int);

/* calc_azimuth (row, col) */

#endif
