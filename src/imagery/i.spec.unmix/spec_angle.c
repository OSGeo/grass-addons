/* Spectral angle mapping
 * (c) 1999 Markus Neteler, Hannover, GPL >= 2.0
 *
 * 25. Nov. 1998 - V. 0.2
 *
 * Updated to LAPACK/BLAS by Mohammed Rashad, 2012
 *****/

#include <stdio.h>
#include <math.h>
#include <grass/gmath.h>
#include "global.h"

/* input mat_struct A, vec_struct Avector1, Avector2
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

float spectral_angle(vec_struct *Avector1, vec_struct *Avector2)
{
    vec_struct *vtmp1;
    double norm1, norm2, norm3;

    /* Measure spectral angle */

    /* multiply one A column with second */
    vtmp1 = G_vector_init(Avector1->rows, Avector1->rows, CVEC);
    vtmp1 = G_vector_product(Avector1, Avector2, vtmp1);
    norm1 = G_vector_norm1(vtmp1);          /* calculate 1-norm */
    norm2 = G_vector_norm_euclid(Avector1); /* calculate 2-norm (Euclidean) */
    norm3 = G_vector_norm_euclid(Avector2); /* calculate 2-norm (Euclidean) */

    G_vector_free(vtmp1);

    /* Calculate angle and return in degree globally */
    return (acos(norm1 / (norm2 * norm3)) * 180 / M_PI);
}
