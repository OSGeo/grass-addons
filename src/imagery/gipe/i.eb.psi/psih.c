#include<stdio.h>
#include<stdlib.h>
#include<math.h>


double psi_h(double disp, double molength, double height)
{
    double xh, psih;

    xh = pow(1.0 - 16.0 * ((height - disp) / molength), 0.25);
    psih = psih = 2.0 * log((1.0 + xh * xh) / 2.0);

    return psih;
}
