#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

#define SPECTRALBANDSMAX 1000

// Structure to represent a point in 2D space
typedef struct {
    double x;
    double y;
} Point;


// Function to calculate the orientation of three points (p, q, r)
double orientation(Point p, Point q, Point r) {
    return (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y);
}

// Function to find the convex hull of a set of points
void convexHull(Point *points, int n, Point *hull, int *hullSize) {
    // Find the leftmost point
    int l = 0;

    // Find the point with maximum x-coordinate
    int maxXIndex = 0;
    for (int i = 1; i < n; ++i) {
        if (points[i].x > points[maxXIndex].x) {
            maxXIndex = i;
        }
    }

    // Storage for the convex hull
    *hullSize = 0;

    // Start from the leftmost point and move clockwise until the point with maximum x-coordinate
    int p = l;
    int q;
    while (p != maxXIndex) {
        // Add the current point to the result
        hull[(*hullSize)++] = points[p];

        // Search for a point 'q' such that orientation(p, q, x) is clockwise for all points 'x'
        q = (p + 1) % n;
        for (int i = 0; i < n; ++i) {
            if (orientation(points[p], points[i], points[q]) > 0) {
                q = i;
            }
        }

        // Now q is the most clockwise with respect to p
        // Set p as q for the next iteration
        p = q;
    }

    // Add the point with maximum x-coordinate to the result
    hull[(*hullSize)++] = points[maxXIndex];
}

// Comparison function for qsort
int comparePoints(const void *a, const void *b) {
    return ((Point *)a)->x > ((Point *)b)->x ? 1 : -1;
}

// Function to perform linear interpolation
double interpolate(double x, Point p1, Point p2) {
    double denominator = p2.x - p1.x;
    if (denominator == 0.0) {
        // Avoid division by zero, return a default value (e.g., p1.y)
        if (p1.y > 0) return p1.y;
        else if (p2.y > 0) return p2.y;
        else return 0;
    } else { 
        return p1.y + (x - p1.x) * (p2.y - p1.y) / denominator;
    }
}


// Function to interpolate and fill y-coordinates
void interpolateAndFill(Point *originalData, int originalSize, Point *convexHull, int hullSize) {
    // Sort convex hull points based on x-coordinates
    qsort(convexHull, hullSize, sizeof(Point), comparePoints);

    // Interpolate linearly to fill y-coordinates of original data
    int j = 0;
    for (int i = 0; i < originalSize; ++i) {
        double x = originalData[i].x;

        // Find the convex hull points within the x-range [x1, x2]
        while (j < hullSize - 1 && convexHull[j + 1].x <= x) {
            j++;
        }

        // Interpolate and update the y-coordinate
        double outval = interpolate(x, convexHull[j], convexHull[j + 1]);
        if (outval > 0){
            originalData[i].y = outval;
        }
    }
}

void continuumremoval(Point *points, int numPoints, Point *cr){
    // Make a backup for later
    Point orig[numPoints];
    for (int i = 0; i < numPoints; ++i) {
        orig[i].x = points[i].x;
        orig[i].y = points[i].y;
    }
    // CONVEX HULL COMPUTATION
    // Create arrays to store the convex hull points
    Point hull[numPoints];
    int hullSize;
    // Call the convexHull function
    convexHull(points, numPoints, hull, &hullSize);
    // INTERPOLATION OF CONVEX HULL OUTPUT TO INPUT X-COORD LENGTH
    // Call the interpolateAndFill function
    interpolateAndFill(points, numPoints, hull, hullSize);
    // Removal of continuum = original / convex hull
    for (int i = 0; i < numPoints; ++i) {
        cr[i].x = orig[i].x;
        cr[i].y = orig[i].y / points[i].y;
    }
}

// data: input spectrum (array of doubles, length numPoints)
// dout: output spectrum (array of doubles, length numPoints)
// numPoints: number of bands
void convexhull(const double *data, double *dout, int numPoints) {
    int i;
    Point *points = (Point *)malloc(numPoints * sizeof(Point));
    Point *cr = (Point *)malloc(numPoints * sizeof(Point));
    if (!points || !cr) {
        fprintf(stderr, "Memory allocation failed in convexhull\n");
        exit(EXIT_FAILURE);
    }

    // Fill points with input data
    for (i = 0; i < numPoints; i++) {
        points[i].x = (double)(i + 1);
        points[i].y = data[i];
    }


    continuumremoval(points, numPoints, cr);

    // Write output
    for (i = 0; i < numPoints; ++i) {
        dout[i] = cr[i].y;
    }

    free(points);
    free(cr);
}

