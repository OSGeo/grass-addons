/* Functions: ...
**
** Author: Radim Blazek, Rosen Matev; July 2008
**
**
*/
#include <stdlib.h>
#include <math.h>
#include <grass/Vect.h>
#include <grass/gis.h>
#include "dgraph.h"

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
    int i, j, res, np;
    double *x, *y;
    double tx, ty, vx, vy, wx, wy, nx, ny, mx, my, rx, ry;
    double vx1, vy1, wx1, wy1;
    double a0, b0, c0, a1, b1, c1;
    double phi1, phi2, delta_phi;
    double nsegments, angular_tol, angular_step;
    double cosa, sina, r;
    int inner_corner, turns180;
    
    G_debug(4, "parallel_line()");
    
    if (looped && 0) {
        /* start point != end point */
        return;
    }
    
    Vect_reset_line(nPoints);

    if (looped) {
        Vect_append_point(Points, Points->x[1], Points->y[1], Points->z[1]);
    }
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
    
    for (i = 0; i < np-1; i++)
    {
        /* save the old values */
        a0 = a1;
        b0 = b1;
        c0 = c1;
        wx = vx;
        wy = vy;        
        
        
        norm_vector(x[i], y[i], x[i+1], y[i+1], &tx, &ty);
        elliptic_tangent(side*tx, side*ty, da, db, dalpha, &vx, &vy);
        
        nx = x[i] + vx;
        ny = y[i] + vy;
        
        mx = x[i+1] + vx;
        my = y[i+1] + vy;

        line_coefficients(nx, ny, mx, my, &a1, &b1, &c1);

        if (i == 0) {
            if (!looped)
                Vect_append_point(nPoints, nx, ny, 0);
            continue;
        }
        
        delta_phi = atan2(ty, tx) - atan2(y[i]-y[i-1], x[i]-x[i-1]);
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
        
        if ((!looped) && (i == np-2)) {
            Vect_append_point(nPoints, mx, my, 0);
        }
    }
    
    if (looped) {
        Vect_append_point(nPoints, nPoints->x[0], nPoints->y[0], nPoints->z[0]);
    }
    
    Vect_line_prune ( nPoints );
    
    if (looped) {
        Vect_line_delete_point(Points, Points->n_points-1);
    }
}

/*
* side: side >= 0 - extracts contour on right side of edge, side < 0 - extracts contour on left side of edge
* returns: the side of the output line, where we should draw parallel line
*/
static int extract_contour(struct planar_graph *pg, struct pg_edge *first, int side, int stop_at_line_end, struct line_pnts *nPoints) {
    int i, j, ret;
    int v; /* current vertex number */
    int v0;
    int eside; /* side of the current edge */
    double eangle; /* current edge angle with Ox (according to the current direction) */
    struct pg_vertex *vert; /* current vertex */
    struct pg_vertex *vert0; /* last vertex */
    struct pg_edge *edge; /* current edge; must be edge of vert */
    int cs; /* on which side are we turning along the contour */
    double opt_angle, tangle;
    int opt_j, opt_side, opt_flag;
    
    G_debug(4, "extract_contour(): v1=%d, v2=%d, side=%d, stop_at_line_end=%d", first->v1, first->v2, side, stop_at_line_end);

    Vect_reset_line(nPoints);
    
    edge = first;
    eside = (side >= 0)?(1):(-1);
    v = edge->v1; /* we might select v1 or v2 if we always want ccw output line */
    v0 = edge->v2;
    vert = &(pg->v[v]);
    vert0 = &(pg->v[v0]);
    /*for (i = 0; i < pg->v[v0].ecount; i++)
        if (pg->v[v0].edges[i] == edge) {
            eangle = pg->v[v0].angles[i];
            break;
        }
    */
    eangle = atan2(vert->y - vert0->y, vert->x - vert0->x);
    cs = -eside; /* because we chose to go v2-->v1 */
    while (1) {
        Vect_append_point(nPoints, vert0->x, vert0->y, 0);
        G_debug(4, "ec: v0=%d, v=%d, eside=%d, edge->v1=%d, edge->v2=%d", v0, v, eside, edge->v1, edge->v2);
        G_debug(4, "ec: edge=%X, first=%X", edge, first);
        //G_debug(4, "ec: first->v1=%d, first->v2=%d", first->v1, first->v2);
        G_debug(4, "ec: append point x=%.18f y=%.18f", vert0->x, vert0->y);
       
        /* mark current edge as visited on the appropriate side */
        if (eside == 1)
            edge->visited_right = 1;
        else
            edge->visited_left = 1;
        
        opt_flag = 1;
        for (j = 0; j < vert->ecount; j++) {
            /* exclude current edge */
            if (vert->edges[j] != edge) {
                tangle = vert->angles[j] - eangle;
                if (tangle < -PI)
                    tangle += 2*PI;
                else if (tangle > PI)
                    tangle -= 2*PI;
                /* now tangle is in (-PI, PI) */
                
                if (opt_flag || (cs*tangle < cs*opt_angle)) {
                    opt_j = j;
                    opt_side = (vert->edges[j]->v1 == v)?(cs):(-cs);
                    opt_angle = tangle;
                    opt_flag = 0;
                }
            }
        }
        
//        G_debug(4, "ec: opt: side=%d opt_flag=%d opt_angle=%.18f opt_j=%d opt_step=%d", side, opt_flag, opt_angle, opt_j, opt_step);
        
        /* if line end is reached (no other edges at curr vertex) */
        if (opt_flag) {
            if (stop_at_line_end) {
                ret = 2;
                break;
            }
            else {
                opt_j = 0; /* the only edge of vert is vert->edges[0] */
                opt_side = -eside; /* go to the other side of the curr edge */
            }
        }
        
        if ((vert->edges[opt_j] == first) && (opt_side == side)) {
            ret = 1;
            break;
        }

        edge = vert->edges[opt_j];
        eside = opt_side;
        v0 = v;
        v = (edge->v1 == v)?(edge->v2):(edge->v1);
        vert0 = vert;
        vert = &(pg->v[v]);
        eangle = vert0->angles[opt_j];
    }
    Vect_append_point(nPoints, vert->x, vert->y, 0);
    G_debug(4, "ec: append point x=%.18f y=%.18f", vert->x, vert->y);

    return cs;
}

/*
* This function extracts the outer contour of a (self crossing) line.
* It can generate left/right contour if none of the line ends are in a loop.
* If one or both of them is in a loop, then there's only one contour
* 
* side: side > 0 - right contour, side < 0 - left contour, side = 0 - outer contour
*       if side != 0 and there's only one contour, the function returns it
* 
* TODO: Implement side != 0 feature;
* retunrs: the side of the output line, where we should draw parallel line
*/
int extract_outer_contour(struct planar_graph *pg, int side, struct line_pnts *nPoints) {
    int i;
    int flag;
    int v;
    struct pg_vertex *vert;
    struct pg_edge *edge;
    double min_x, min_angle, ta;

    G_debug(4, "extract_outer_contour()");

    if (side != 0) {
        G_fatal_error("    side != 0 feature not implemented");
        return;
    }
    
    /* find a line segment which is on the outer contour */
    flag = 1;
    for (i = 0; i < pg->vcount; i++) {
        if (flag || (pg->v[i].x < min_x)) {
            v = i;
            min_x = pg->v[i].x;
            flag = 0;
        }
    }
    vert = &(pg->v[v]);
    
    flag = 1;
    for (i = 0; i < vert->ecount; i++) {
        if (flag || (vert->angles[i] < min_angle)) {
            edge = vert->edges[i];
            min_angle = vert->angles[i];
            flag = 0;
        }
    }
    
    return extract_contour(pg, edge, (edge->v1 == v)?RIGHT_SIDE:LEFT_SIDE, 0, nPoints);
}

/*
* Extracts contours which are not visited.
* IMPORTANT: the outer contour must be visited (you should call extract_outer_contour() to do that),
*            so that extract_inner_contour() doesn't return it
* returns: 0 when there are no more inner contours; otherwise, the side of the output line, where we should draw parallel line
*/
int extract_inner_contour(struct planar_graph *pg, struct line_pnts *nPoints) {
    int i;
    
    G_debug(4, "extract_inner_contour()");

    for (i = 0; i < pg->ecount; i++) {
        if (!(pg->e[i].visited_right))
            return extract_contour(pg, &(pg->e[i]), RIGHT_SIDE, 0, nPoints);

        if (!(pg->e[i].visited_left))
            return extract_contour(pg, &(pg->e[i]), LEFT_SIDE, 0, nPoints);
    }
    
    return 0;
}

void extract_all_inner_contours(struct line_pnts *Points, struct line_pnts ***iPoints, int *inner_count) {
    struct planar_graph *pg;
    struct line_pnts *tPoints;
    struct line_pnts **arrPoints;
    int i, res, count;
    int more = 8;
    int allocated = more;
    
    G_debug(4, "extract_all_inner_contours()");
    
    /* initializations */
    tPoints = Vect_new_line_struct();
    arrPoints = G_malloc(allocated*sizeof(struct line_pnts *));
    pg = pg_create(Points);
        
    /* extract outer contour so that we have visited edges appropriately */
    extract_outer_contour(pg, 0, tPoints);
    
    /* inner contours */
    count = 0;
    res = extract_inner_contour(pg, tPoints);
    while (res != 0) {
        if (allocated < count+1) {
            allocated += more;
            arrPoints = G_realloc(arrPoints, allocated*sizeof(struct line_pnts *));
        }
        arrPoints[count] = Vect_new_line_struct();
        Vect_copy_xyz_to_pnts(arrPoints[count], tPoints->x, tPoints->y, tPoints->z, tPoints->n_points);
        count++;
        
        res = extract_inner_contour(pg, tPoints);
    }
    
    arrPoints = G_realloc(arrPoints, count*sizeof(struct line_pnts *));
    *inner_count = count;
    *iPoints = arrPoints;
        
    pg_destroy_struct(pg);
    Vect_destroy_line_struct(tPoints);
    
    return;  
}

/* point_in_buf - test if point px,py is in d buffer of Points
** returns:  1 in buffer
**           0 not  in buffer
*/
int point_in_buf(struct line_pnts *Points, double px, double py, double da, double db, double dalpha) {
    int i, np;
    double cx, cy;
    double delta, delta_k, k;
    double vx, vy, wx, wy, mx, my, nx, ny;
    double len, tx, ty, d, da2;
        
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
            len = LENGTH(mx, my);
            elliptic_tangent(mx/len, my/len, da, db, dalpha, &cx, &cy);
            
            delta = mx*cy - my*cx;
            delta_k = (px-vx)*cy - (py-vy)*cx;
            k = delta_k/delta;
/*            G_debug(4, "k = %g, k1 = %g", k, (mx * (px - vx) + my * (py - vy)) / (mx * mx + my * my)); */
            if (k <= 0) {
                nx = vx;
                ny = vy;
            }
            else if (k >= 1) {
                nx = wx;
                ny = wy;
            }
            else {
                nx = vx + k*mx;
                ny = vy + k*my;
            }
            
            /* inverse transform */
            elliptic_transform(px - nx, py - ny, 1/da, 1/db, dalpha, &tx, &ty);
            
            d = dig_distance2_point_to_line(nx + tx, ny + ty, 0, vx, vy, 0, wx, wy, 0,
                0, NULL, NULL, NULL, NULL, NULL);

/*            G_debug(4, "sqrt(d)*da = %g, len' = %g, olen = %g", sqrt(d)*da, da*LENGTH(tx,ty), LENGTH((px-nx),(py-ny)));*/
            if (d <= 1)
                return 1;
        }
        else { 
            d = dig_distance2_point_to_line(px, py, 0, vx, vy, 0, wx, wy, 0,
                0, NULL, NULL, NULL, NULL, NULL);
/*            G_debug(4, "sqrt(d)     = %g", sqrt(d));*/
            if (d <= da2) {
                return 1;
            }
        }
    }
    return 0;
}

void parallel_line_b(struct line_pnts *Points, double da, double db, double dalpha, int round, int caps, double tol, struct line_pnts **oPoints, struct line_pnts ***iPoints, int *inner_count) {
    struct planar_graph *pg, *pg2;
    struct line_pnts *tPoints, *sPoints;
    struct line_pnts **arrPoints;
    struct line_pnts **arrPoints2;
    int i, count, count2;
    int side, res;
    int more = 8;
    int allocated = 0;
    double px, py;
    
    G_debug(4, "parallel_line_b()");
    
    /* initializations */
    tPoints = Vect_new_line_struct();
    sPoints = Vect_new_line_struct();
    arrPoints = NULL;
    pg = pg_create(Points);
    
    /* outer contour */
    *oPoints = Vect_new_line_struct();
    side = extract_outer_contour(pg, 0, tPoints);
/*    parallel_line(tPoints, da, db, dalpha, side, round, caps, LOOPED_LINE, tol, *oPoints);*/
    parallel_line(tPoints, da, db, dalpha, side, round, caps, LOOPED_LINE, tol, sPoints);
    pg2 = pg_create(sPoints);
    extract_outer_contour(pg2, 0, *oPoints);
    pg_destroy_struct(pg2);
    
    /* inner contours */
    count = 0;
    side = extract_inner_contour(pg, tPoints);
    while (side != 0) {
        parallel_line(tPoints, da, db, dalpha, side, round, caps, LOOPED_LINE, tol, sPoints);
        extract_all_inner_contours(sPoints, &arrPoints2, &count2);
        for (i = 0; i < count2; i++) {
            res = Vect_line_check_intersection(tPoints, arrPoints2[i], 0);
            if (res != 0)
                continue;
            
            res = Vect_point_in_poly(arrPoints2[i]->x[0], arrPoints2[i]->y[0], tPoints);
            if (res == 0)
                continue;
                
            res = Vect_get_point_in_poly(arrPoints2[i], &px, &py);
            if (res != 0)
                G_fatal_error("Vect_get_point_in_poly() failed.");
            if (point_in_buf(tPoints, px, py, da, db, dalpha))
                continue;
            
            if (allocated == count) {
                allocated += more;
                arrPoints = G_realloc(arrPoints, allocated*sizeof(struct line_pnts *));
            }
            arrPoints[count] = Vect_new_line_struct();
            Vect_copy_xyz_to_pnts(arrPoints[count], arrPoints2[i]->x, arrPoints2[i]->y, arrPoints2[i]->z, arrPoints2[i]->n_points);
            count++;
        }
        
        side = extract_inner_contour(pg, tPoints); 
    }

    arrPoints = G_realloc(arrPoints, count*sizeof(struct line_pnts *));
    *inner_count = count;
    *iPoints = arrPoints;
        
    Vect_destroy_line_struct(tPoints);
    Vect_destroy_line_struct(sPoints);
    pg_destroy_struct(pg);
    
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
