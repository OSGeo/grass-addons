/* Spectral angle mapping
 * (c) 1998 Markus Neteler, Hannover
 *
 * 26. Oct. 1998 - V. 0.1
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


float spectral_angle() /* returns spectral angle*/
{

/* input MAT A, VEC Avector
 * output cur_angle
 *
 *                   v_DN * v_reference
 *  cos alpha = ----------------------------
 *               ||v_DN|| * ||v_reference||
 * 
 *
 *                 b * Avector
 *            = -----------------------
 *              ||b|| * ||Avector||
 */


  VEC *vtmp1;
      double norm1, norm2, norm3;
        
  /* Measure spectral angle*/

   vtmp1 = v_star(Avector, b, VNULL); /* multiply with b vector */
   norm1 = v_norm1(vtmp1);       /* calculate 1-norm */
   norm2 = v_norm2(Avector);     /* calculate 2-norm (Euclidean) */
   norm3 = v_norm2(b);           /* calculate 2-norm (Euclidean) */

   V_FREE(vtmp1);
      
   curr_angle = (acos(norm1/(norm2 * norm3)) * 180/MY_PI);  /* Calculate angle */
        /* return in degree*/
}
