#include "local_proto.h"

double *triple(double x, double y, double z)
{
  double *t;
  t = (double *) G_malloc(3 * sizeof(double));

  *t = x;
  *(t+1) = y;
  *(t+2) = z;
  
  return t;
}

/* Bearing */
double bearing(double x0, double x1, double y0, double y1)
{
  double dy, dx, us;
  dy = y1 - y0;
  dx = x1 - x0;
  if (dy == 0. && dx == 0.)
    return -9999;

  us = atan(fabsf(dy/dx));
  if (dx==0. && dy>0.)
    us = 0.5*PI;
  if (dx<0. && dy>0.)
    us = PI-us;
  if (dx<0. && dy==0.)
    us = PI;
  if (dx<0. && dy<0.)
    us = PI+us;
  if (dx==0. && dy<0.)
    us = 1.5*PI;
  if (dx>0. && dy<0.)
    us = 2.0*PI-us;

  return us;
}

/*double distance(double *r0, double *r1)
{
  double dx, dy, dz, dist;
  dx = *r1 - *r0;
  dy = *(r1+1) - *(r0+1);
  dz = *(r1+2) - *(r0+2);
  dist = sqrt(dx*dx + dy*dy + dz*dz);
  
  return dist;
  }*/
