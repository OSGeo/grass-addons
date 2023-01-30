#include <grass/raster.h>
#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/segment.h>
#include <grass/glocale.h>

/* lattice cell */
struct lcell {
    int area;      /* area id */
    double interp; /* interpolated value */
    double adj;    /* adjustment */
    double weight; /* weighing factor */
};

/* mass area */
struct marea {
    int count;      /* number of cells in the area */
    double value;   /* original value */
    double interp;  /* cumulative interpolated values */
    double adj;     /* cumulative adjustments */
    double avgdiff; /* difference between interpolated and original */
    int count_neg;  /* count of negatives */
    int weight;     /* 0 = all weights 0, 1 = at least one weight > 0 */
};
