#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

#define MAXFILES 1000 // in main.c
#define SPECTRALBANDSMAX MAXFILES

// Structure to represent a point in 2D space
typedef struct {
    double x;
    double y;
} Point;

// Function to calculate the orientation of three points (p, q, r)
double orientation(Point p, Point q, Point r);

// Function to find the convex hull of a set of points
void convexHull(Point *points, int n, Point *hull, int *hullSize);

// Comparison function for qsort
int comparePoints(const void *a, const void *b);

// Function to perform linear interpolation
double interpolate(double x, Point p1, Point p2);

// Function to interpolate and fill y-coordinates
void interpolateAndFill(Point *originalData, int originalSize, Point *convexHull, int hullSize);

// Main Function for continuum removal
void continuumremoval(Point *points, int numPoints, Point *cr);

// Function to be used in main.c
void convexhull(const double *data, double *dout, int numPoints);
