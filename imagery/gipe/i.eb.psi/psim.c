#include<stdio.h>
#include<stdlib.h>
#include<math.h>

#define PI 3.14159265358979323846

double psi_m(double disp, double molength, double height)
{
    double xm, psim;

    xm = pow(1.0 - 16.0 * ((height - disp) / molength), 0.25);
    psim =
	2.0 * log((1.0 + xm) / 2.0) + log((1 + xm * xm) - 2 * atan(xm) +
					  0.5 * PI);

    return psim;
}
