#include<stdio.h>
#include<stdlib.h>
#include<math.h>

#define PI 3.14159265358979323846

double fixed_deltat(double u_hu, double roh_air, double cp, double dt,
		    double disp, double z0m, double z0h, double tempk,
		    double hu, int iteration)
{
    int i;

    double ublend;

    double length;

    double xm, xh;

    double psim, psih;

    double ustar;

    double rah;

    double h_in;

    double temp1;

    if (log(hu - disp) - log(z0m) == 0.0) {
	ublend =
	    u_hu * (log(100 - disp) - log(z0m)) / (log(hu - disp) - log(z0m) +
						   0.001);
    }
    else {
	ublend =
	    u_hu * (log(100 - disp) - log(z0m)) / (log(hu - disp) - log(z0m));
    }
    psim = 0.0;
    psih = 0.0;

    for (i = 0; i < iteration; i++) {
	if ((log((100 - disp) / z0m) - psim) == 0.0) {
	    ustar = 0.41 * ublend / (log((100 - disp) / z0m) - psim + 0.0001);
	}
	else {
	    ustar = 0.41 * ublend / (log((100 - disp) / z0m) - psim);
	}
	if (z0h == 0.0) {
	    z0h = 0.00001;
	}
	if (ustar == 0.0) {
	    ustar = 0.00001;
	}
	if (((hu - disp) / z0h) - psih == 0.0) {
	    rah = (log((hu - disp) / z0h) - psih + 0.00001) / (0.41 * ustar);
	}
	else {
	    rah = (log((hu - disp) / z0h) - psih) / (0.41 * ustar);
	}
	if (rah == 0.0) {
	    rah = 0.00001;
	}
	h_in = roh_air * cp * dt / rah;
	if (h_in == 0.0) {
	    h_in = 0.00001;
	}
	length = -roh_air * cp * pow(ustar, 3) * tempk / (0.41 * 9.81 * h_in);
	if (length == 0.0) {
	    length = -0.00001;
	}
	xm = pow(1.0 - 16.0 * ((100 - disp) / length), 0.25);
	xh = pow(1.0 - 16.0 * ((hu - disp) / length), 0.25);
	if ((1.0 + xm) / 2.0 == 0.0 || (1 + xm * xm) / 2.0 == 0.0) {
	    psim =
		2.0 * log((1.0 + xm + 0.00001) / 2.0) +
		log((1 + xm * xm) / 2.0) - 2 * atan(xm) + 0.5 * PI + 0.00001;
	}
	else {
	    psim =
		2.0 * log((1.0 + xm) / 2.0) + log((1 + xm * xm) / 2.0) -
		2 * atan(xm) + 0.5 * PI;
	}
	if ((1.0 + xh * xh) / 2.0 == 0.0) {
	    psih = 2.0 * log((1.0 + xh * xh + 0.00001) / 2.0);
	}
	else {
	    psih = 2.0 * log((1.0 + xh * xh) / 2.0);
	}
    }

    return rah;
}
