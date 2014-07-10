/*!
   \file gradient.c

   \brief Gradient computation

    Gradient computation (second order approximation)
    using central differencing scheme (plus forward and backward
    difference of second order approx.)
   
   (C) 2014 by the GRASS Development Team

   This program is free software under the GNU General Public
   License (>=v2).  Read the file COPYING that comes with GRASS
   for details.

   \author Anna Petrasova
 */
#include "r3flow_structs.h"

void gradient(struct Array *array, double *step,
	      struct Array *grad_x, struct Array *grad_y,
	      struct Array *grad_z)
{
    int col, row, depth;

    for (depth = 0; depth < array->sz; depth++) {
	for (row = 0; row < array->sy; row++) {
	    ACCESS(grad_x, 0, row, depth) =
		(-3 * ACCESS(array, 0, row, depth) +
		 4 * ACCESS(array, 1, row, depth) -
		 ACCESS(array, 2, row, depth)) / (2 * step[0]);

	    ACCESS(grad_x, array->sx - 1, row, depth) =
		(3 * ACCESS(array, array->sx - 1, row, depth) -
		 4 * ACCESS(array, array->sx - 2, row, depth) +
		 ACCESS(array, array->sx - 3, row, depth)) / (2 * step[0]);

	    for (col = 0; col < array->sx; col++) {
		ACCESS(grad_x, col, row, depth) =
		    (ACCESS(array, col + 1, row, depth) -
		     ACCESS(array, col - 1, row, depth)) / (2 * step[0]);
	    }
	}
    }
    for (depth = 0; depth < array->sz; depth++) {
	for (col = 0; col < array->sx; col++) {
	    ACCESS(grad_y, col, 0, depth) =
		(-3 * ACCESS(array, col, 0, depth) +
		 4 * ACCESS(array, col, 1, depth) -
		 ACCESS(array, col, 2, depth)) / (2 * step[1]);

	    ACCESS(grad_y, col, array->sy - 1, depth) =
		(3 * ACCESS(array, col, array->sy - 1, depth) -
		 4 * ACCESS(array, col, array->sy - 2, depth) +
		 ACCESS(array, col, array->sy - 3, depth)) / (2 * step[1]);

	    for (row = 0; row < array->sy; row++) {
		ACCESS(grad_y, col, row, depth) =
		    (ACCESS(array, col, row + 1, depth) -
		     ACCESS(array, col, row - 1, depth)) / (2 * step[1]);
	    }
	}
    }
    for (row = 0; row < array->sy; row++) {
	for (col = 0; col < array->sx; col++) {
	    ACCESS(grad_z, col, row, 0) =
		(-3 * ACCESS(array, col, row, 0) +
		 4 * ACCESS(array, col, row, 1) -
		 ACCESS(array, col, row, 2)) / (2 * step[2]);

	    ACCESS(grad_z, col, row, array->sz - 1) =
		(3 * ACCESS(array, col, row, array->sz - 1) -
		 4 * ACCESS(array, col, row, array->sz - 2) +
		 ACCESS(array, col, row, array->sz - 3)) / (2 * step[2]);

	    for (depth = 0; depth < array->sz; depth++) {
		/* is minus here? */
		ACCESS(grad_y, col, row, depth) =
		    -(ACCESS(array, col, row, depth + 1) -
		      ACCESS(array, col, row, depth - 1)) / (2 * step[2]);
	    }
	}
    }
}
