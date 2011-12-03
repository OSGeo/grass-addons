#include <grass/gis.h>

double euclidean_distance(double *x, double *y, int n);
double gaussianKernel(double x, double term);

int read_points(struct Map_info *In, double ***coordinate);
double compute_all_distances(double **coordinate, double **dists, int n, double dmax);
void compute_distance( double N, double E, struct Map_info *In, 
	               double sigma, double term, double *gaussian, double dmax);

