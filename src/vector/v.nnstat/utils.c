#include "local_proto.h"

/* make triple of the coordinates */
double *triple(double x, double y, double z)
{
    double *t;

    t = (double *)G_malloc(3 * sizeof(double));

    *t = x;
    *(t + 1) = y;
    *(t + 2) = z;

    return t;
}

/* bearing */
double bearing(double x0, double x1, double y0, double y1)
{
    double dy, dx, us;

    dy = y1 - y0;
    dx = x1 - x0;
    if (dy == 0. && dx == 0.) {
        return -9999;
    }

    us = atan(fabs(dy / dx));
    if (dx == 0. && dy > 0.) {
        us = 0.5 * PI;
    }
    if (dx < 0. && dy > 0.) {
        us = PI - us;
    }
    if (dx < 0. && dy == 0.) {
        us = PI;
    }
    if (dx < 0. && dy < 0.) {
        us = PI + us;
    }
    if (dx == 0. && dy < 0.) {
        us = 1.5 * PI;
    }
    if (dx > 0. && dy < 0.) {
        us = 2.0 * PI - us;
    }

    return us;
}

/* According to two points comparison (sorting points in convexHull) */
int cmpVals(const void *v1, const void *v2)
{
    double *p1, *p2;

    p1 = (double *)v1;
    p2 = (double *)v2;
    if (p1[0] > p2[0]) {
        return 1;
    }
    else if (p1[0] < p2[0]) {
        return -1;
    }
    else {
        return 0;
    }
}
