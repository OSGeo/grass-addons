/* Spectral angle mapping
 * (c) 1999 Markus Neteler, Hannover
 *
 * 25. Nov. 1998 - V. 0.2
 *
 ****************************************************************************
 ** Based on Meschach Library
 ** Copyright (C) 1993 David E. Steward & Zbigniew Leyk, all rights reserved.
 ****************************************************************************
 *
 * Cited references are from
 *    Steward, D.E, Leyk, Z. 1994: Meschach: Matrix computations in C.
 *       Proceedings of the centre for Mathematics and its Applicaions.
 *       The Australian National University. Vol. 32.
 *       ISBN 0 7315 1900 0
 *****/

#define GLOBAL
#define MY_PI 3.141592653589793

#include <stdio.h>
#include <math.h>
#include "matrix.h"
#include "global.h"


void spectral_angle() /* returns spectral angle globally*/
{

/* input MAT A, VEC Avector1, Avector2
 * output cur_angle
 *
 *                   v_DN * v_reference
 *  cos alpha = ----------------------------
 *               ||v_DN|| * ||v_reference||
 * 
 *
 *                  Avector1 * Avector2
 *            = ---------------------------
 *              ||Avector1|| * ||Avector2||
 *
 * 
 * Ref.: van der Meer, F. 1997: Mineral mapping and Landsat Thematic Mapper 
 *                             image Classification using spectral unmixing.
 *       Geocarto International, Vol.12, no.3 (Sept.). pp. 27-40
 */


  VEC *vtmp1;
  double norm1, norm2, norm3;


/* Measure spectral angle*/

   vtmp1 = v_star(Avector1, Avector2, VNULL); /* multiply one A column with second */
   norm1 = v_norm1(vtmp1);        /* calculate 1-norm */
   norm2 = v_norm2(Avector1);     /* calculate 2-norm (Euclidean) */
   norm3 = v_norm2(Avector2);     /* calculate 2-norm (Euclidean) */

   V_FREE(vtmp1);
      
   curr_angle = (acos(norm1/(norm2 * norm3)) * 180/MY_PI);  /* Calculate angle */
    /* return in degree globally*/
}
