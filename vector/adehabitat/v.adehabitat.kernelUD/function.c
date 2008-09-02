#include <math.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include "global.h"



/* probability for gaussian distribution */
double gaussianKernel(double x, double term)
{
  return(term * exp(-(x*x)/2.));
}




double segno(double x)
{
  double y; 

  y = (x > 0 ? 1. : 0.) + (x < 0 ? -1. : 0.);

  return y;
}




/* euclidean distance between vectors x and y of length n */
double euclidean_distance(double *x, double *y, int n)
{
  int j;
  double out = 0.0;
  double tmp;

  for(j=0;j<n;j++){
    tmp = x[j] - y[j];
    out += tmp * tmp;
  }

  return sqrt(out);
}
