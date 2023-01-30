#include "local_proto.h"
#define PI M_PI

/*******************************
These functions are mostly taken from the module v.hull (Aime, A., Neteler, M.,
Ducke, B., Landa, M.)

Minimum Bounding Rectangle (MBR)
 - obtain vertices of convex hull,
 - transform coordinates of vertices into coordinate system with axes parallel
to hull's edges,
 - find extents,
 - compute areas and find minimum of them.
 *******************************
*/

/* ----------------------------
 * Obtain convex hull vertices: functions from  hull.c (Andrea Aime)
 * Theoretical background: Andrew's variant of Graham Scan
 * Source: Mark Nelson, 2007: http://marknelson.us/2007/08/22/convex/
 */

/* Function to determine whether a point is above or below the line
 * connecting the leftmost and the rightmost points */

int rightTurn(double (*P)[3], int i, int j, int k)
{
    double a, b, c, d;

    /* Coordinate translation: P[j] = 0.0 */
    a = P[i][0] - P[j][0];
    b = P[i][1] - P[j][1];
    c = P[k][0] - P[j][0];
    d = P[k][1] - P[j][1];
    /* Determinant of P[i] and P[k] */
    return a * d - b * c <
           0; /* Returns |det| < 0 => P[k] is angled off in left direction */
}

/* Function to compare two points (for sorting points in convexHull) */
int cmpPoints(const void *v1, const void *v2)
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

/* Function to obtain vertices of convex hull */
int convexHull(struct points *pnts, struct convex *hull)
{
    int pointIdx, upPoints, loPoints;
    int i, *upHull, *loHull;
    int n = pnts->n;

    double *ro, (*ri)[3], (*r)[3]; /* r = [xyz] */

    r = (double(*)[3])G_malloc(n * 3 * sizeof(double));
    ri = &r[0];
    ro = &pnts->r[0];

    for (i = 0; i < n; i++) {
        (*ri)[0] = *ro;
        (*ri)[1] = *(ro + 1);
        (*ri)[2] = *(ro + 2);
        ri++;
        ro += 3;
    }

    /* sort points in ascending x order
     * modified according to
     * http://www.physicsforums.com/showthread.php?t=546209 */
    qsort(&r[0][0], n, 3 * sizeof(double), cmpPoints);

    hull->hull = (int *)G_malloc(n * 3 * sizeof(int));

    /* compute upper hull */
    upHull = hull->hull;
    upHull[0] = 0;
    upHull[1] = 1;
    upPoints = 1; /* number of points in upper hull */
    for (pointIdx = 2; pointIdx < n; pointIdx++) {
        upPoints++;
        upHull[upPoints] = pointIdx;
        while (upPoints > 1 &&
               !rightTurn(r, upHull[upPoints], upHull[upPoints - 1],
                          upHull[upPoints - 2])) {
            upHull[upPoints - 1] = upHull[upPoints];
            upPoints--;
        }
    }

    /* compute lower hull, overwrite last point of upper hull */
    loHull = &(upHull[upPoints]);
    loHull[0] = n - 1;
    loHull[1] = n - 2;
    loPoints = 1; /* number of points in lower hull */
    for (pointIdx = n - 3; pointIdx >= 0; pointIdx--) {
        loPoints++;
        loHull[loPoints] = pointIdx;
        while (loPoints > 1 &&
               !rightTurn(r, loHull[loPoints], loHull[loPoints - 1],
                          loHull[loPoints - 2])) {
            loHull[loPoints - 1] = loHull[loPoints];
            loPoints--;
        }
    }
    hull->n = loPoints + upPoints;

    G_debug(3, "numPoints:%d loPoints:%d upPoints:%d", n, loPoints, upPoints);

    /* reclaim uneeded memory */
    hull->hull = (int *)G_realloc(hull->hull, (hull->n + 1) * sizeof(int));

    /* Obtain coordinates of hull vertices */
    hull->coord = (double *)G_malloc((hull->n + 1) * 3 *
                                     sizeof(double)); /* 1st = last pnt */

    int *hh, *hh0;
    double *hc, (*r0)[3];

    hc = &hull->coord[0];
    hh = &hull->hull[0];
    ri = &r[0];

    for (i = 0; i <= hull->n; i++) {
        if (i < hull->n) {
            *hc = (*(ri + *hh))[0];
            *(hc + 1) = (*(ri + *hh))[1];
            *(hc + 2) = (*(ri + *hh))[2];
            hc += 3;
            hh++;
        }
        else { // coords of 1st equal to coords of last hull vertex
            r0 = &r[0];
            hh0 = &hull->hull[0];
            *hc = (*(r0 + *hh0))[0];
            *(hc + 1) = (*(r0 + *hh0))[1];
            *(hc + 2) = (*(r0 + *hh0))[2];
        }
    }

    return hull->n;
}

/* ----------------------------
 * MBR area estimation
 * ----------------------------*/
double MBR(struct points *pnts)
{
    int i, k;
    double us, cosus, sinus, S, S_min;
    double *hc, *hc_k; // original and to be transformed vertices of hull
    double *r_min, *r_max;

    r_min = (double *)G_malloc(3 * sizeof(double));
    r_max = (double *)G_malloc(3 * sizeof(double));

    double *hull_trans,
        *ht; /* Coordinates of hull vertices transformed into coordinate system
                with axes parallel to hull's edges */

    hull_trans = (double *)G_malloc(3 * sizeof(double));
    ht = &hull_trans[0];

    struct convex hull;

    hull.n = convexHull(pnts, &hull);
    hc = &hull.coord[0];

    S_min = (pnts->r_max[0] - pnts->r_min[0]) *
            (pnts->r_max[1] - pnts->r_min[1]); /* Area of extent */

    for (i = 0; i < hull.n; i++) {
        /* Bearings of hull edges */
        us = bearing(*hc, *(hc + 3), *(hc + 1), *(hc + 4)); // x0, x1, y0, y1
        if (us == -9999) {                                  // Identical points
            continue;
        }
        cosus = cos(us);
        sinus = sin(us);

        hc_k = &hull.coord[0]; // original coords
        for (k = 0; k <= hull.n; k++) {
            /* Coordinate transformation */
            *ht = *hc_k * cosus + *(hc_k + 1) * sinus;
            *(ht + 1) = -(*hc_k) * sinus + *(hc_k + 1) * cosus;
            *(ht + 2) = *(hc_k + 2);

            /* Transformed extent */
            switch (k) {
            case 0:
                r_min = r_max = triple(*ht, *(ht + 1), *(ht + 2));
                break;
            default:
                r_min = triple(MIN(*ht, *r_min), MIN(*(ht + 1), *(r_min + 1)),
                               MIN(*(ht + 2), *(r_min + 2)));
                r_max = triple(MAX(*ht, *r_max), MAX(*(ht + 1), *(r_max + 1)),
                               MAX(*(ht + 2), *(r_max + 2)));
                break;
            }
            hc_k += 3;
        } // end k

        hc += 3; // next point

        S = (*r_max - *r_min) *
            (*(r_max + 1) - *(r_min + 1)); /* Area of transformed extent */
        S_min = MIN(S, S_min);
    } // end i

    G_free(r_min);
    G_free(r_max);

    return S_min;
}
