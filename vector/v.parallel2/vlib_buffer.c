/* Functions: ...
**
** Author: Radim Blazek, Rosen Matev; June 2008
**
**
*/
#include <stdlib.h>
#include <math.h>
#include <grass/Vect.h>
#include <grass/gis.h>

#define LENGTH(DX, DY) (sqrt((DX*DX)+(DY*DY)))
#ifndef MIN
    #define MIN(X,Y) ((X<Y)?X:Y)
#endif
#ifndef MAX
    #define MAX(X,Y) ((X>Y)?X:Y)
#endif    
#define PI M_PI
#define RIGHT_SIDE 1
#define LEFT_SIDE -1
#define LOOPED_LINE 1
#define NON_LOOPED_LINE 0

/*
* a[i] = 0 means i-th line segment is not visited
* a[i] = 1 means i-th line segment is visited on it's right side
* a[i] = 2 means i-th line segment is visited on it's left side
* a[i] = 3 means i-th line segment is visited on both sides
*/
struct visited_segments
{
    char *a;
    int n;
};

/* norm_vector() calculates normalized vector form two points */
static void norm_vector(double x1, double y1, double x2, double y2, double *x, double *y )
{
    double dx, dy, l;
    dx  = x2 - x1;
    dy  = y2 - y1;
    l = LENGTH(dx, dy);
    if (l == 0) {
        /* assume that dx == dy == 0, which should give (NaN,NaN) */
        /* without this, very small dx or dy could result in Infinity */
        dx = dy = 0;
    }
    *x = dx/l;
    *y = dy/l;
}

static void rotate_vector(double x, double y, double cosa, double sina, double *nx, double *ny) {
    *nx = x*cosa - y*sina;
    *ny = x*sina + y*cosa;
    return;   
}

/*
* (x,y) shoud be normalized vector for common transforms; This func transforms (x,y) to a vector corresponding to da, db, dalpha params
*/
static void elliptic_transform(double x, double y, double da, double db, double dalpha, double *nx, double *ny) {
    double cosa = cos(dalpha);
    double sina = sin(dalpha);
/*    double cc = cosa*cosa;
    double ss = sina*sina;
    double t = (da-db)*sina*cosa;
    
    *nx = (da*cc + db*ss)*x + t*y;
    *ny = (da*ss + db*cc)*y + t*x;
    return;*/
    
    double va, vb;
    va = (x*cosa + y*sina)*da;
    vb = (x*(-sina) + y*cosa)*db;
    *nx = va*cosa + vb*(-sina);
    *ny = va*sina + vb*cosa;
    return; 
}

/*
* vect(x,y) must be normalized
* gives the tangent point of the tangent to ellpise(da,db,dalpha) parallel to vect(x,y)
* ellipse center is in (0,0)
*/
static void elliptic_tangent(double x, double y, double da, double db, double dalpha, double *px, double *py) {
    double cosa = cos(dalpha);
    double sina = sin(dalpha);
    double u, v, len;
    /* rotate (x,y) -dalpha radians */
    rotate_vector(x, y, cosa, -sina, &x, &y);
    /*u = (x + da*y/db)/2;
    v = (y - db*x/da)/2;*/
    u = da*da*y;
    v = -db*db*x;
    len = da*db/sqrt(da*da*v*v + db*db*u*u);
    u *= len;
    v *= len;
    rotate_vector(u, v, cosa, sina, px, py);
    return; 
}


/*
* !!! This is not line in GRASS' sense. See http://en.wikipedia.org/wiki/Line_%28mathematics%29
*/
static void line_coefficients(double x1, double y1, double x2, double y2, double *a, double *b, double *c) {
    *a = y2 - y1;
    *b = x1 - x2;
    *c = x2*y1 - x1*y2;
    return;
}

/*
* Finds intersection of two straight lines. Returns 0 if the lines are parallel, 1 if they cross,
* 2 if they are the same line.
* !!!!!!!!!!!!!!!! FIX THIS TOLLERANCE CONSTANTS BAD (and UGLY) CODE !!!!!!!!!
*/
static int line_intersection(double a1, double b1, double c1, double a2, double b2, double c2, double *x, double *y) {
    double d;
    
    if (fabs(a2*b1 - a1*b2) == 0) {
        if (fabs(a2*c1 - a1*c2) == 0)
            return 2;
        else                   
            return 0;
    }
    else {
        d = a1*b2 - a2*b1;
        *x = (b1*c2 - b2*c1)/d;
        *y = (c1*a2 - c2*a1)/d;
        return 1;
    }
}

static double angular_tolerance(double tol, double da, double db) {
    double a = MAX(da, db);
    double b = MIN(da, db);
    if (tol > a)
        tol = a;
/*    t = b*sqrt(tol*(2*a - tol))/(a*(a-tol));
    return 2*atan(t);*/
    return 2*acos(1-tol/a);
}

/*
* This function generates parallel line (with loops, but not like the old ones).
* It is not to be used directly for creating buffers.
* + added elliptical buffers/par.lines support
*
* dalpha - direction of elliptical buffer major axis in degrees
* da - distance along major axis
* db: distance along minor (perp.) axis
* side: side >= 0 - right side, side < 0 - left side
* when (da == db) we have plain distances (old case)
* round - 1 for round corners, 0 for sharp corners. (tol is used only if round == 1)
*/
void parallel_line(struct line_pnts *Points, double da, double db, double dalpha, int side, int round, int caps, int looped, double tol, struct line_pnts *nPoints)
{
    int i, i_minus_1, j, res, np;
    double *x, *y;
    double tx, ty, vx, vy, wx, wy, nx, ny, mx, my, rx, ry;
    double vx1, vy1, wx1, wy1;
    double a0, b0, c0, a1, b1, c1;
    double phi1, phi2, delta_phi;
    double nsegments, angular_tol, angular_step;
    double cosa, sina, r;
    int inner_corner, turns180, loop_flag;
    
    G_debug(4, "parallel_line()");
    
    Vect_reset_line(nPoints);
    
    np = Points->n_points;
    x = Points->x;
    y = Points->y;

    if ((np == 0) || (np == 1))
        return;

    if ((da == 0) && (db == 0)) {
        Vect_copy_xyz_to_pnts(nPoints, x, y, NULL, np);
        return;
    }

    side = (side >= 0)?(1):(-1); /* normalize variable */
    dalpha *= PI/180; /* convert dalpha from degrees to radians */
    angular_tol = angular_tolerance(tol, da, db);
    loop_flag = 1;
    
    for (i = 0; (i < np)&&(loop_flag); i++)
    {
        i_minus_1 = i - 1;
        if (i == np-1) {
            if (!looped) {
                break;
            }
            else {
                i = 0;
                i_minus_1 = np - 2;
                loop_flag = 0;
            }
        }
        
        norm_vector(x[i], y[i], x[i+1], y[i+1], &tx, &ty);
        elliptic_tangent(side*tx, side*ty, da, db, dalpha, &vx, &vy);
        
        nx = x[i] + vx;
        ny = y[i] + vy;
        
        mx = x[i+1] + vx;
        my = y[i+1] + vy;

        line_coefficients(nx, ny, mx, my, &a1, &b1, &c1);
        
        if ((i == 0) && loop_flag) {
            if (!looped) {
                Vect_append_point(nPoints, nx, ny, 0);
                G_debug(4, "append point x=%.18f y=%.18f i=%d", nx, ny, i);
            }
        }
        else {
            delta_phi = atan2(ty, tx) - atan2(y[i_minus_1+1]-y[i_minus_1], x[i_minus_1+1]-x[i_minus_1]);
            if (delta_phi > PI)
                delta_phi -= 2*PI;
            else if (delta_phi <= -PI)
                delta_phi += 2*PI;
            /* now delta_phi is in [-pi;pi] */
            turns180 = (fabs(fabs(delta_phi) - PI) < 1e-15);
            inner_corner = (side*delta_phi <= 0) && (!turns180);
            
            if ((turns180) && (!(caps && round))) {
                if (caps) {
                    norm_vector(0, 0, vx, vy, &tx, &ty);
                    elliptic_tangent(side*tx, side*ty, da, db, dalpha, &tx, &ty);
                }
                else {
                    tx = 0;
                    ty = 0;
                }
                Vect_append_point(nPoints, x[i] + wx + tx, y[i] + wy + ty, 0);
                Vect_append_point(nPoints, nx + tx, ny + ty, 0); /* nx == x[i] + vx, ny == y[i] + vy */
            }
            else if ((!round) || inner_corner) {
                res = line_intersection(a0, b0, c0, a1, b1, c1, &rx, &ry);
/*                if (res == 0) {
                    G_debug(4, "a0=%.18f, b0=%.18f, c0=%.18f, a1=%.18f, b1=%.18f, c1=%.18f", a0, b0, c0, a1, b1, c1);
                    G_fatal_error("Two consequtive line segments are parallel, but not on one straight line! This should never happen.");
                    return;
                }  */
                if (res == 1) {
                    Vect_append_point(nPoints, rx, ry, 0);
                }
            }
            else {
                /* we should draw elliptical arc for outside corner */
                
                /* inverse transforms */
                elliptic_transform(wx, wy, 1/da, 1/db, dalpha, &wx1, &wy1);
                elliptic_transform(vx, vy, 1/da, 1/db, dalpha, &vx1, &vy1);
                
                phi1 = atan2(wy1, wx1);
                phi2 = atan2(vy1, vx1);
                delta_phi = side*(phi2 - phi1);
                
                /* make delta_phi in [0, 2pi] */
                if (delta_phi < 0)
                    delta_phi += 2*PI;
                
                nsegments = (int)(delta_phi/angular_tol) + 1;
                angular_step = side*(delta_phi/nsegments);
                
                for (j = 0; j <= nsegments; j++) {
                    elliptic_transform(cos(phi1), sin(phi1), da, db, dalpha, &tx, &ty);
                    Vect_append_point(nPoints, x[i] + tx, y[i] + ty, 0);
                    phi1 += angular_step;
                }
            }
        }
        
        if ((i == np-2) && (!looped)) {
            Vect_append_point(nPoints, mx, my, 0);
        }
        
        /* save the old values */
        a0 = a1;
        b0 = b1;
        c0 = c1;
        wx = vx;
        wy = vy;        
    }
    
    if (looped) {
        i = nPoints->n_points - 1;
        Vect_line_insert_point(nPoints, 0, nPoints->x[i], nPoints->y[i], 0);
    }
    Vect_line_prune ( nPoints );
}

static void split_at_intersections(struct line_pnts *Points, struct line_pnts *nPoints)
{
    #define MAX_SEGMENT_INTERSECTIONS 10  /* we should make dynamic array here? */
    #define EPSILON 1e-10 /*  */
    int i, j, k, res, np;
    double *x, *y; /* input coordinates */
    double x1, y1, z1, x2, y2, z2; /* intersection points */
    double len; /* current i-th line length */
    double tdist, min;
    double px[MAX_SEGMENT_INTERSECTIONS], py[MAX_SEGMENT_INTERSECTIONS], pdist[MAX_SEGMENT_INTERSECTIONS];
    int pcount, min_i;

    G_debug(1, "split_at_intersections()");
    
    Vect_reset_line(nPoints);

    Vect_line_prune(Points);
    np = Points->n_points;
    x = Points->x;
    y = Points->y;

    if ((np == 0) || (np == 1))
        return;

    for (i = 0; i < np-1; i++) {
        Vect_append_point(nPoints, x[i], y[i], 0);
        G_debug(1, "appended point x=%f y=%f", x[i], y[i]);
        
        
        /* find all intersections */
        pcount = 0;
        len = LENGTH((x[i]-x[i+1]), (y[i]-y[i+1]));
        for (j = 0; j < np-1; j++) {
            /* exclude previous (i-1)th, current i-th, and next (i+1)th line */
            if ((j < i-1) || (j > i+1)) {
                res = Vect_segment_intersection(x[i], y[i], 0, x[i+1], y[i+1], 0,
                                                x[j], y[j], 0, x[j+1], y[j+1], 0,
                                                &x1, &y1, &z1, &x2, &y2, &z2, 0);
                G_debug(1, "intersection=%d", res);
                if (res == 1) {
                    /* generall intersection */
                    tdist = LENGTH((x[i]-x1), (y[i]-y1));
                    /* we only want intersections on the inside */
                    G_debug(1, "x1=%f y1=%f tdist=%f len=%f, eps=%f", x1, y1, tdist, len, EPSILON);
                    if ((tdist > EPSILON) && (tdist < len - EPSILON)) {
                        px[pcount] = x1;
                        py[pcount] = y1;
                        pdist[pcount] = tdist;
                        pcount++;
                    }
                }
                /* TODO: implement cases of overlappings */
            }
        }
        
        /* now we shoud output interserction points ordered by distance to (x[i],y[i]) */
        /* we do it in O(pcount^2) time, since pcount is usually small it's okey */
        G_debug(1, "pcount=%d", pcount);
        for (j = 0; j < pcount; j++) {
            min = 2*len;
            for (k = 0; k < pcount; k++) {
                if (pdist[k] < min) {
                    min = pdist[k];
                    min_i = k;
                }
            }
            pdist[min_i] = 4*len;
            Vect_append_point(nPoints, px[min_i], py[min_i], 0);
            G_debug(1, "appended point x=%f y=%f", px[min_i], py[min_i]);
            
        }
    }
    Vect_append_point(nPoints, x[np-1], y[np-1], 0);
    G_debug(1, "appended point x=%f y=%f", x[i], y[i]);
    Vect_line_prune(nPoints);    
}

/*
* IMPORTANT: split_at_intersections() must be applied to input line before calling extract_contour().
*            When visited != NULL, extract_contour() marks the sides of lines as visited along the contour.
*            visited->a must have at least Points->n_points elements
*
* side: side >= 0 - right contour, side < 0 - left contour
* returns: -1 when contour is a loop; 0 or Points->n_points-1 when contour finishes at line end (depending on which one)
*/
static int extract_contour(struct line_pnts *Points, int first_point, int first_step, int side, int stop_at_line_end, struct line_pnts *nPoints, struct visited_segments *visited) {
    int i, is, j, k, step, np;
    int ret;
    double *x, *y;
    double cx, cy, tx, ty;
    double u, v, len, new_len, new_step;
    int intersection_flag;
    double x1, y1, z1, x2, y2, z2;
    double opt_angle, tangle;
    int opt_j, opt_step, opt_flag;
    
    G_debug(4, "extract_contour(): first_point=%d, first_step=%d, side=%d, stop_at_line_end=%d", first_point, first_step, side, stop_at_line_end);

    Vect_reset_line(nPoints);
            
    np = Points->n_points;
    x = Points->x;
    y = Points->y;
    G_debug(4, "ec: Points->n_points=%d", np);
    
    if ((np == 0) || (np == 1))
        return;

    /* normalize parameter side */
    if (side >= 0)
        side = 1;
    else if (side < 0)
        side = -1;
    
    i = first_point;
    step = first_step;
    while (1) {
        /* precessing segment AB: A=(x[i],y[i]) B=(x[i+step],y[i+step]) */
        Vect_append_point(nPoints, x[i], y[i], 0);
        G_debug(4, "ec: append point x=%.18f y=%.18f", x[i], y[i]);
        is = i + step;
        
        if (visited != NULL) {
            j = (3-step*side)/2; /* j is 1 when (step*side == 1), and j is 2 when (step*side == -1) */
            k = MIN(i, is);
            if ((visited->a[k] & j) == 0)
                visited->n++;
            visited->a[k] |= j;
        }
                
        cx = x[i] - x[is];
        cy = y[i] - y[is];
        opt_flag = 1;
        for (j = 0; j < np-1; j++) {
            /* exclude current segment AB */
            if (j != i - (1-step)/2) {
                if ((fabs(x[j]-x[is]) < EPSILON) && (fabs(y[j]-y[is]) < EPSILON)) {
                    tx = x[j+1] - x[j];
                    ty = y[j+1] - y[j];
                    tangle = atan2(ty, tx) - atan2(cy, cx);
                    if (tangle < 0)
                        tangle += 2*PI;
                    /* now tangle is in [0, 2PI) */
                    
                    if (opt_flag || (side*tangle < side*opt_angle)) {
                        opt_j = j;
                        opt_step = 1;
                        opt_angle = tangle;
                        opt_flag = 0;
                    }
                }
                else if ((fabs(x[j+1]-x[is]) < EPSILON) && (fabs(y[j+1]-y[is]) < EPSILON)) {
                    tx = x[j] - x[j+1];
                    ty = y[j] - y[j+1];
                    tangle = atan2(ty, tx) - atan2(cy, cx);
                    if (tangle < 0)
                        tangle += 2*PI;
                    /* now tangle is in [0, 2PI) */
                    
                    if (opt_flag || (side*tangle < side*opt_angle)) {
                        opt_j = j+1;
                        opt_step = -1;
                        opt_angle = tangle;
                        opt_flag = 0;
                    }
                    
                }
            }
        }
        
        /* if line end is reached */
        if (opt_flag) {
            if (stop_at_line_end) {
                Vect_append_point(nPoints, x[is], y[is], 0);
                ret = is;
                break;
            }
            else {
                opt_j = is;
                opt_step = -step;
            }
        }
        
        if ((opt_j == first_point) && (opt_step == first_step)) {
            Vect_append_point(nPoints, x[is], y[is], 0);
            ret = -1;
            break;
        }
        
        i = opt_j;
        step = opt_step;
    }        
    Vect_line_prune(nPoints);

    return ret;
}

/*
* This function extracts the outer contour of a (self crossing) line.
* It can generate left/right contour if none of the line ends are in a loop.
* If one or both of them is in a loop, then there's only one contour
* 
* side: side > 0 - right contour, side < 0 - left contour, side = 0 - outer contour
*       if side != 0 and there's only one contour, the function returns it
* 
* IMPORTANT: split_at_intersections() must be applied to input line before calling extract_outer_contour
* TODO: Implement side != 0 feature;
* returns: returns on which side of output line is the exterior of the input line
*/
static int extract_outer_contour(struct line_pnts *Points, int side, struct line_pnts *nPoints, struct visited_segments *visited) {
    int i, np, res, ret;
    double *x, *y;
    double min_x, min_angle, ta;
    int t1, t2, j1=-1, j2=-1;

    G_debug(4, "extract_outer_contour()");

    np = Points->n_points;
    x = Points->x;
    y = Points->y;
    
    if (side != 0) {
        res = extract_contour(Points, 0, 1, side, 1, nPoints, NULL); /* should save visited and later restore it if needed */
        /* if we have finished at the other end */
        if (res == Points->n_points-1) {
            /* !!! WE ARE STILL NOT SURE WHETHER THIS IS PROPER OUTER CONTOUR.
             * !!! CONSIDER THE CASE WHERE BOTH LINE ENDS ARE IN THE SAME LOOP. 
            */
            return side;
        }
    }
    
    /* find a line segment which is on the outer contour */
    min_x = 1e300;
    for (i = 0; i < np-1; i++) {
        if (x[i] <= x[i+1]) {
            t1 = i;
            t2 = i+1;
        }
        else {
            t1 = i+1;
            t2 = i;
        }
        G_debug(4, "t1=%d (%f,%f) t2=%d (%f,%f)", t1, x[t1], y[t1], t2, x[t2], y[t2]);
        if (x[t1] < min_x) {
            min_x = x[t1];
            min_angle = atan2(y[t2]-y[t1], x[t2]-x[t1]);
            j1 = t1;
            j2 = t2;
            G_debug(4, "j1=%d j2=%d", j1, j2);
        }
        else if ((x[t1] == min_x) && (y[t1] == y[j1])) {
            ta = atan2(y[t2]-y[t1], x[t2]-x[t1]);
            if (ta < min_angle) {
                min_angle = ta;
                j1 = t1;
                j2 = t2;
                G_debug(4, "j1=%d j2=%d", j1, j2);
            }
        }
    }
    
    G_debug(4, "j1=%d, j2-j1=%d, side=%d", j1, j2-j1, RIGHT_SIDE);
    res = extract_contour(Points, j1, j2-j1, RIGHT_SIDE, 0, nPoints, visited);
    
    return RIGHT_SIDE;
}

/*
* Extracts contours which are not visited. Generates counterclockwise closed lines.
* IMPORTANT: split_at_intersections() must be applied to input line before calling extract_inner_contour
* IMPORTANT: the outer contour must be visited, so that extract_inner_contour() doesn't return it
* returns: 0 when there are no more inner contours; otherwise, returns on which side of output line is the interior of the loop
*/
int extract_inner_contour(struct line_pnts *Points, struct line_pnts *nPoints, struct visited_segments *visited) {
    int i, j, np, res;
    double *x, *y;
    
    G_debug(4, "extract_inner_contour()");

    np = Points->n_points;
    x = Points->x;
    y = Points->y;
    
    for (i = 0; i < np-1; i++) {
        /* if right side is not visited */
        if ((visited->a[i] & 1) == 0) {
            res = extract_contour(Points, i+1, -1, LEFT_SIDE, 0, nPoints, visited);
            return LEFT_SIDE;
        }
        /* if left side is not visited */
        if ((visited->a[i] & 2) == 0) {
            res = extract_contour(Points, i, 1, LEFT_SIDE, 0, nPoints, visited);
            return LEFT_SIDE;
        }
    }
    
    return 0;
}

void extract_all_inner_contours(struct line_pnts *Points, struct line_pnts ***iPoints, int *inner_count) {
    struct line_pnts *Points2, *tPoints;
    struct line_pnts **arrPoints;
    int i, side, count;
    int more = 8;
    int allocated = more;
    struct visited_segments visited;
    
    G_debug(4, "extract_all_inner_contours()");
    
    /* initializations and spliting of the input line */
    tPoints = Vect_new_line_struct();
    Points2 = Vect_new_line_struct();
    split_at_intersections(Points, Points2);
    
    visited.a = (char *)G_malloc(sizeof(char)*Points2->n_points);
    memset(visited.a, 0, sizeof(char)*Points2->n_points);
    
    arrPoints = G_malloc(allocated*sizeof(struct line_pnts *));
    
    /* extract outer contour so that we have filled visited appropriately */
    side = extract_outer_contour(Points2, 0, tPoints, &visited);
    
    /* inner contours */
    count = 0;
    side = extract_inner_contour(Points2, tPoints, &visited);
    while (side != 0) {
        if (allocated < count+1) {
            allocated += more;
            arrPoints = G_realloc(arrPoints, allocated*sizeof(struct line_pnts *));
        }
        arrPoints[count] = Vect_new_line_struct();
        Vect_copy_xyz_to_pnts(arrPoints[count], tPoints->x, tPoints->y, tPoints->z, tPoints->n_points);
        count++;
        
        side = extract_inner_contour(Points2, tPoints, &visited);
    }
    
    arrPoints = G_realloc(arrPoints, count*sizeof(struct line_pnts *));
    *inner_count = count;
    *iPoints = arrPoints;
        
    G_free(visited.a);
    Vect_destroy_line_struct(tPoints);
    Vect_destroy_line_struct(Points2);
    
    return;  
}

/* point_in_buf - test if point px,py is in d buffer of Points
** returns:  1 in buffer
**           0 not  in buffer
*/
int point_in_buf(struct line_pnts *Points, double px, double py, double da, double db, double dalpha) {
    int i, np;
    double cosa = cos(dalpha);
    double sina = sin(dalpha);
    double delta, delta_k;
    double vx, vy, wx, wy, mx, my, nx, ny;
    double k, t, tx, ty, d, da2;
        
    np = Points->n_points;
    da2 = da*da;
    for (i = 0; i < np-1; i++) {
        vx = Points->x[i];
        vy = Points->y[i];
        wx = Points->x[i+1];
        wy = Points->y[i+1];
        
        if (da != db) {
            mx = wx - vx;
            my = wy - vy;
            
            delta = mx*sina - my*cosa;
            if (delta == 0) {
                t = da; da = db; db = t;
                dalpha = dalpha + M_PI_2;
                cosa = cos(dalpha);
                sina = sin(dalpha);
                delta = mx*sina - my*cosa;
            }
            delta_k = (px-vx)*sina - (py-vy)*cosa;
            k = delta_k/delta;
            nx = px - vx - k*mx;
            ny = py - vy - k*my;
            
            /* inverse transform */
            elliptic_transform(nx, ny, 1/da, 1/db, dalpha, &tx, &ty);
            
            d = dig_distance2_point_to_line(tx, ty, 0, vx, vy, 0, wx, wy, 0,
                0, NULL, NULL, NULL, NULL, NULL);
            if (d <= 1)
                return 1;
        }
        else {
            d = dig_distance2_point_to_line(px, py, 0, vx, vy, 0, wx, wy, 0,
                0, NULL, NULL, NULL, NULL, NULL);
            if (d <= da2) {
                return 1;
            }
        }
    }
    return 0;
}

void parallel_line_b(struct line_pnts *Points, double da, double db, double dalpha, int round, int caps, double tol, struct line_pnts **oPoints, struct line_pnts ***iPoints, int *inner_count) {
    struct line_pnts *Points2, *tPoints, *sPoints;
    struct line_pnts **arrPoints;
    struct line_pnts **arrPoints2;
    int i, side, count, count2;
    int res;
    int more = 8;
    int allocated = more;
    double px, py;
    struct visited_segments visited;
    
    G_debug(4, "parallel_line_b()");
    
    /* initializations and spliting of the input line */
    tPoints = Vect_new_line_struct();
    sPoints = Vect_new_line_struct();
    Points2 = Vect_new_line_struct();
    split_at_intersections(Points, Points2);
    
    visited.a = (char *)G_malloc(sizeof(char)*Points2->n_points);
    memset(visited.a, 0, sizeof(char)*Points2->n_points);
    
    arrPoints = G_malloc(allocated*sizeof(struct line_pnts *));
    
    /* outer contour */
    side = extract_outer_contour(Points2, 0, tPoints, &visited);
    *oPoints = Vect_new_line_struct();
    parallel_line(tPoints, da, db, dalpha, side, round, caps, LOOPED_LINE, tol, *oPoints);
    
    /* inner contours */
    count = 0;
    side = extract_inner_contour(Points2, tPoints, &visited);
    while (side != 0) {
        parallel_line(tPoints, da, db, dalpha, side, round, caps, LOOPED_LINE, tol, sPoints);
        
        extract_all_inner_contours(sPoints, &arrPoints2, &count2);
        
        for (i = 0; i < count2; i++) {
            res = Vect_line_check_intersection(tPoints, arrPoints2[i], 0);
            if (res != 0) 
                continue;
                
            res = Vect_get_point_in_poly(arrPoints2[i], &px, &py);
            if (res != 0)
                G_fatal_error("Vect_get_point_in_poly() failed.");
            if (point_in_buf(tPoints, px, py, da, db, dalpha))
                continue;
            
            /* passed all tests, add new island */
            if (allocated < count+1) {
                allocated += more;
                arrPoints = G_realloc(arrPoints, allocated*sizeof(struct line_pnts *));
            }
            arrPoints[count] = Vect_new_line_struct();
            Vect_copy_xyz_to_pnts(arrPoints[count], arrPoints2[i]->x, arrPoints2[i]->y, arrPoints2[i]->z, arrPoints2[i]->n_points);
            count++;
        }
        
        side = extract_inner_contour(Points2, tPoints, &visited);
    }
    
    arrPoints = G_realloc(arrPoints, count*sizeof(struct line_pnts *));
    *inner_count = count;
    *iPoints = arrPoints;
        
    G_free(visited.a);
    Vect_destroy_line_struct(tPoints);
    Vect_destroy_line_struct(sPoints);
    Vect_destroy_line_struct(Points2);
    
    return;
}

/*
  \fn void Vect_line_parallel2 ( struct line_pnts *InPoints, double distance, double tolerance, int rm_end,
                       struct line_pnts *OutPoints )
  \brief Create parrallel line
  \param InPoints input line
  \param distance
  \param tolerance maximum distance between theoretical arc and polygon segments
  \param rm_end remove end points falling into distance
  \param OutPoints output line
*/
void Vect_line_parallel2(struct line_pnts *InPoints, double da, double db, double dalpha, int side, int round, double tol, struct line_pnts *OutPoints )
{
    G_debug(4, "Vect_line_parallel(): npoints = %d, da = %f, db = %f, dalpha = %f, side = %d, round_corners = %d, tol = %f",
            InPoints->n_points, da, db, dalpha, side, round, tol);

    parallel_line(InPoints, da, db, dalpha, side, round, 1, NON_LOOPED_LINE, tol, OutPoints);
    
/*    if (!loops)
        clean_parallel(OutPoints, InPoints, distance, rm_end);
*/
    return;
}

/*!
  \fn void Vect_line_buffer ( struct line_pnts *InPoints, double distance, double tolerance,
                              struct line_pnts *OutPoints )
  \brief Create buffer around the line line.
         Buffer is closed counter clockwise polygon.
         Warning: output line may contain loops!
  \param InPoints input line
  \param distance
  \param tolerance maximum distance between theoretical arc and polygon segments
  \param OutPoints output line
*/
void
Vect_line_buffer ( struct line_pnts *InPoints, double distance, double tolerance,
                     struct line_pnts *OutPoints )
{
    double dangle;
    int    side, npoints;
    static struct line_pnts *Points = NULL;
    static struct line_pnts *PPoints = NULL;

    distance = fabs (distance );

    dangle = 2 * acos( 1-tolerance/fabs(distance) ); /* angle step */

    if ( Points == NULL )
        Points = Vect_new_line_struct();

    if ( PPoints == NULL )
        PPoints = Vect_new_line_struct();

    /* Copy and prune input */
    Vect_reset_line ( Points );
    Vect_append_points ( Points, InPoints, GV_FORWARD );
    Vect_line_prune ( Points );

    Vect_reset_line ( OutPoints );

    npoints = Points->n_points;
    if ( npoints <= 0 ) {
	return;
    } else if ( npoints == 1 ) { /* make a circle */
	double angle, x, y;

	for ( angle = 0; angle < 2*PI; angle += dangle ) {
	    x = Points->x[0] + distance * cos( angle );
	    y = Points->y[0] + distance * sin( angle );
	    Vect_append_point ( OutPoints, x, y, 0 );
	}
	/* Close polygon */
	Vect_append_point ( OutPoints, OutPoints->x[0], OutPoints->y[0], 0 );
    } else { /* 2 and more points */
	for ( side = 0; side < 2; side++ ) {
	    double angle, sangle;
	    double lx1, ly1, lx2, ly2;
	    double x, y, nx, ny, sx, sy, ex, ey;

	    /* Parallel on one side */
	    if ( side == 0 ) {
		Vect_line_parallel ( Points, distance, tolerance, 0, PPoints );
		Vect_append_points ( OutPoints, PPoints, GV_FORWARD );
	    } else {
		Vect_line_parallel ( Points, -distance, tolerance, 0, PPoints );
		Vect_append_points ( OutPoints, PPoints, GV_BACKWARD );
	    }

	    /* Arc at the end */
	    /* 2 points at theend of original line */
	    if ( side == 0 ) {
		lx1 = Points->x[npoints-2];
		ly1 = Points->y[npoints-2];
		lx2 = Points->x[npoints-1];
		ly2 = Points->y[npoints-1];
	    } else {
		lx1 = Points->x[1];
		ly1 = Points->y[1];
		lx2 = Points->x[0];
		ly2 = Points->y[0];
	    }

	    /* normalized vector */
	    norm_vector( lx1, ly1, lx2, ly2, &nx, &ny);

	    /* starting point */
	    sangle = atan2 ( -nx, ny ); /* starting angle */
	    sx  = lx2 + ny * distance;
	    sy  = ly2 - nx * distance;

	    /* end point */
	    ex  = lx2 - ny * distance;
	    ey  = ly2 + nx * distance;

	    Vect_append_point ( OutPoints, sx, sy, 0 );

	    /* arc */
	    for ( angle = dangle; angle < PI; angle += dangle ) {
		x = lx2 + distance * cos( sangle + angle );
		y = ly2 + distance * sin( sangle + angle );
		Vect_append_point ( OutPoints, x, y, 0 );
	    }

	    Vect_append_point ( OutPoints, ex, ey, 0 );
	}

	/* Close polygon */
	Vect_append_point ( OutPoints, OutPoints->x[0], OutPoints->y[0], 0 );
    }
    Vect_line_prune ( OutPoints );
}



