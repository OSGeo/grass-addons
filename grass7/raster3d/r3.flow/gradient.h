#ifndef GRADIENT_H
#define GRADIENT_H

#include "r3flow_structs.h"

void gradient(struct Array *array, double *step,
	      struct Array *grad_x, struct Array *grad_y,
	      struct Array *grad_z);
#endif // GRADIENT_H
