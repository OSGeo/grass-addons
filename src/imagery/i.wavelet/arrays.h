#include <stdio.h>

/** Get size of an array **/
#define N_ELEMENTS(array) (sizeof(array) / sizeof((array)[0]))
/*Create 1D arrays*/
int *ai1d(int X);
float *af1d(int X);
double *ad1d(int X);
/*Create 2D arrays*/
int **ai2d(int X, int Y);
float **af2d(int X, int Y);
double **ad2d(int X, int Y);
