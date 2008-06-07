/* Functions: nearest, adjust_line, parallel_line
**
** Author: Radim Blazek Feb 2000
**
**
*/
#include <stdlib.h>
#include <math.h>
#include <grass/Vect.h>
#include <grass/gis.h>

#define LENGTH(DX, DY)  (  sqrt( (DX*DX)+(DY*DY) )  )
#define PI M_PI

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

/* find_cross find first crossing between segments from s1 to s2 and from s3 to s4
** s5 is set to first segment and s6 to second
** neighbours are taken as crossing each other only if overlap
** returns: 1 found
**         -1 found overlap
**          0 not found
*/
int find_cross ( struct line_pnts *Points, int s1, int s2, int s3, int s4,  int *s5, int *s6 )
{
    int i, j, np, ret;
    double *x, *y;

    G_debug (5, "find_cross(): npoints = %d, s1 = %d, s2 = %d, s3 = %d, s4 = %d",
	                 Points->n_points, s1, s2, s3, s4 );

    x = Points->x;
    y = Points->y;
    np = Points->n_points;

    for ( i=s1; i<=s2; i++)
    {
	for ( j=s3; j<=s4; j++)
	{
	    if ( j==i ){
		continue;
	    }
	    ret = dig_test_for_intersection ( x[i], y[i], x[i+1], y[i+1], x[j], y[j], x[j+1], y[j+1] );
	    if ( ret == 1 &&  ( (i-j) > 1 || (i-j) < -1 )  )
	    {
		*s5 = i;
		*s6 = j;
                G_debug (5, "  intersection: s5 = %d, s6 = %d", *s5, *s6 );
		return 1;
	    }
	    if (  ret == -1  )
	    {
		*s5 = i;
		*s6 = j;
                G_debug (5, "  overlap: s5 = %d, s6 = %d", *s5, *s6 );
		return -1;
	    }
	}
    }
    G_debug (5, "  no intersection" );
    return 0;
}

/* point_in_buf - test if point px,py is in d buffer of Points
** returns:  1 in buffer
**           0 not  in buffer
*/
int point_in_buf ( struct line_pnts *Points, double px, double py, double d )
{
    int i, np;
    double sd;

    np = Points->n_points;
    d *= d;
    for ( i=0; i < np-1; i++)
    {
	sd = dig_distance2_point_to_line ( px, py, 0,
		Points->x[i], Points->y[i], 0, Points->x[i+1], Points->y[i+1], 0,
	        0, NULL, NULL, NULL, NULL, NULL	);
	if ( sd <= d )
	{
	    return 1;
	}
    }
    return 0;
}

/* clean_parallel - clean parallel line created by parallel_line:
** - looking for loops and if loop doesn't contain any other loop
**   and centroid of loop is in buffer removes this loop (repeated)
** - optionaly removes all end points in buffer
*    parameters:
*	Points - parallel line
*	origPoints - original line
*	d - offset
*	rm_end - remove end points in buffer
** note1: on some lines (multiply selfcrossing; lines with end points
**        in buffer of line other; some shapes of ends ) may create nosense
** note2: this function is stupid and slow, somebody more clever
**        than I am should write paralle_line + clean_parallel
**        better;    RB March 2000
*/
void clean_parallel ( struct line_pnts *Points, struct line_pnts *origPoints, double d , int rm_end )
{
    int i, j, np, npn, sa, sb;
    int sa_max = 0;
    int first=0, current, last, lcount;
    double *x, *y, px, py, ix, iy;
    static struct line_pnts *sPoints = NULL;

    G_debug (4, "clean_parallel(): npoints = %d, d = %f, rm_end = %d", Points->n_points, d, rm_end );

    x = Points->x;
    y = Points->y;
    np = Points->n_points;

    if ( sPoints == NULL )
        sPoints = Vect_new_line_struct();

    Vect_reset_line ( sPoints );

    npn=1;

    /* remove loops */
    while( first < np-2 ){
	/* find first loop which doesn't contain any other loop */
	current=first;  last=Points->n_points-2;  lcount=0;
	while( find_cross ( Points, current, last-1, current+1, last,  &sa, &sb ) != 0 )
	{
	    if ( lcount == 0 ){ first=sa; } /* move first forward */

	    current=sa+1;
	    last=sb;
	    lcount++;
            G_debug (5, "  current = %d, last = %d, lcount = %d", current, last, lcount);
	}
	if ( lcount == 0 ) { break; }   /* loop not found */

	/* ensure sa is monotonically increasing, so npn doesn't reset low */
	if (sa > sa_max ) sa_max = sa;
	if (sa < sa_max ) break;

	/* remove loop if in buffer */
	if ( (sb-sa) == 1 ){ /* neighbouring lines overlap */
	    j=sb+1;
	    npn=sa+1;
	} else {
	    Vect_reset_line ( sPoints );
	    dig_find_intersection ( x[sa],y[sa],x[sa+1],y[sa+1],x[sb],y[sb],x[sb+1],y[sb+1], &ix,&iy);
	    Vect_append_point ( sPoints, ix, iy, 0 );
	    for ( i=sa+1 ; i < sb+1; i++ ) { /* create loop polygon */
		Vect_append_point ( sPoints, x[i], y[i], 0 );
	    }
	    Vect_find_poly_centroid  ( sPoints, &px, &py);
	    if ( point_in_buf( origPoints, px, py, d )  ){ /* is loop in buffer ? */
		npn=sa+1;
		x[npn] = ix;
		y[npn] = iy;
		j=sb+1;
		npn++;
		if ( lcount == 0 ){ first=sb; }
	    } else {  /* loop is not in buffer */
		first=sb;
	        continue;
	    }
	}

	for (i=j;i<Points->n_points;i++) /* move points down */
	{
	    x[npn] = x[i];
	    y[npn] = y[i];
	    npn++;
	}
	Points->n_points=npn;
    }

    if ( rm_end ) {
	/* remove points from start in buffer */
	j=0;
	for (i=0;i<Points->n_points-1;i++)
	{
	    px=(x[i]+x[i+1])/2;
	    py=(y[i]+y[i+1])/2;
	    if ( point_in_buf ( origPoints, x[i], y[i], d*0.9999)
		 && point_in_buf ( origPoints, px, py, d*0.9999) ){
		j++;
	    } else {
		break;
	    }
	}
	if (j>0){
	    npn=0;
	    for (i=j;i<Points->n_points;i++)
	    {
		x[npn] = x[i];
		y[npn] = y[i];
		npn++;
	    }
	    Points->n_points = npn;
	}
	/* remove points from end in buffer */
	j=0;
	for (i=Points->n_points-1 ;i>=1; i--)
	{
	    px=(x[i]+x[i-1])/2;
	    py=(y[i]+y[i-1])/2;
	    if ( point_in_buf ( origPoints, x[i], y[i], d*0.9999)
		 && point_in_buf ( origPoints, px, py, d*0.9999) ){
		j++;
	    } else {
		break;
	    }
	}
	if (j>0){
	    Points->n_points -= j;
	}
    }
}

#ifdef this_is_comment
/* parallel_line - remove duplicate points from input line and
*  creates new parallel line in 'd' offset distance;
*  'tol' is tolerance between arc and polyline;
*  this function doesn't care about created loops;
*
*  New line is written to existing nPoints structure.
*/

void parallel_line (struct line_pnts *Points, double d, double tol, struct line_pnts *nPoints)
{
    int i, j, np, na, side;
    double *x, *y, nx, ny, tx, ty, vx, vy, ux, uy, wx, wy;
    double atol, atol2, a, av, aw;

    G_debug (4, "parallel_line()" );

    Vect_reset_line ( nPoints );

    Vect_line_prune ( Points );
    np = Points->n_points;
    x = Points->x;
    y = Points->y;

    if ( np == 0 )
	return;

    if ( np == 1 ) {
	Vect_append_point ( nPoints, x[0], y[0], 0 ); /* ? OK, should make circle for points ? */
	return;
    }

    if ( d == 0 ) {
	Vect_copy_xyz_to_pnts ( nPoints, x, y, NULL, np );
	return;
    }

    side = (int)(d/fabs(d));
    atol = 2 * acos( 1-tol/fabs(d) );

    for (i = 0; i < np-1; i++)
    {
	norm_vector( x[i], y[i], x[i+1], y[i+1], &tx, &ty);
	vx  = ty * d;
	vy  = -tx * d;

	nx = x[i] + vx;
	ny = y[i] + vy;
	Vect_append_point ( nPoints, nx, ny, 0 );

	nx = x[i+1] + vx;
	ny = y[i+1] + vy;
	Vect_append_point ( nPoints, nx, ny, 0 );

	if ( i < np-2 ) {  /* use polyline instead of arc between line segments */
	    norm_vector( x[i+1], y[i+1], x[i+2], y[i+2], &ux, &uy);
	    wx  =  uy * d;
	    wy  = -ux * d;
	    av = atan2 ( vy, vx );
	    aw = atan2 ( wy, wx );
	    a = (aw - av) * side;
	    if ( a < 0 )  a+=2*PI;

            /* TODO: a <= PI can probably fail because of representation error */
	    if ( a <= PI && a > atol)
	    {
		na = (int) (a/atol);
		atol2 = a/(na+1) * side;
		for (j = 0; j < na; j++)
		{
		    av+=atol2;
		    nx = x[i+1] + fabs(d) * cos(av);
		    ny = y[i+1] + fabs(d) * sin(av);
		    Vect_append_point ( nPoints, nx, ny, 0 );
		}
	    }
	}
    }
    Vect_line_prune ( nPoints );
}
#endif

/*
* (x, y) shoud be normalized vector; This func transforms it to a vector corresponding to da, db, dalpha params
*/
static void elliptic_transform(double x, double y, double da, double db, double dalpha, double *nx, double *ny) {
    double cosa = cos(dalpha);
    double sina = sin(dalpha);
    double cc = cosa*cosa;
    double ss = sina*sina;
    double t = (da-db)*sina*cosa;
    
    *nx = (da*cc + db*ss)*x + t*y;
    *ny = (da*ss + db*cc)*y + t*x;
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
    double ka = a2/a1;
    double kb = b2/b1;
    double kc;
    double d;
    
    if (fabs(ka - kb) < 1e-10) {
        kc = c2/c1;
        if (fabs(ka-kc) < 1e-10)
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
* round == 1 will be implemented soon
*/
void parallel_line(struct line_pnts *Points, double da, double db, double dalpha, int side, int round, double tol, struct line_pnts *nPoints)
{
    int i, j, res, np, na;
    double *x, *y;
    double tx, ty, vx, vy, nx, ny, mx, my, rx, ry;
    double a0, b0, c0, a1, b1, c1;
    double ux, uy, wx, wy;
    double atol, atol2, a, av, aw;

    G_debug(4, "parallel_line2()");

    dalpha *= 180/PI;
    Vect_reset_line ( nPoints );

    Vect_line_prune ( Points );
    np = Points->n_points;
    x = Points->x;
    y = Points->y;

    if ( np == 0 )
        return;

    if ( np == 1 ) {
        /* Vect_append_point ( nPoints, x[0], y[0], 0 ); /* ? OK, should make circle for points ? */
        return;
    }

    if ((da == 0) && (db == 0)) {
        Vect_copy_xyz_to_pnts(nPoints, x, y, NULL, np);
        return;
    }

    side = (side >= 0)?(1):(-1);
/*    atol = 2 * acos( 1-tol/fabs(d) ); */

    for (i = 0; i < np-1; i++)
    {
        norm_vector(x[i], y[i], x[i+1], y[i+1], &tx, &ty);
        elliptic_transform(-ty*side, tx*side, da, db, dalpha, &vx, &vy);
        
        nx = x[i] + vx;
        ny = y[i] + vy;
            
        mx = x[i+1] + vx;
        my = y[i+1] + vy;

        line_coefficients(nx, ny, mx, my, &a1, &b1, &c1);
        
        if (i == 0) {
            Vect_append_point(nPoints, nx, ny, 0);
        }
        else {
            res = line_intersection(a0, b0, c0, a1, b1, c1, &rx, &ry);
            if (res == 0) {
                /* THIS ISN'T SUPPOSED TO HAPPEN, MUST THROW ERROR*/
                G_fatal_error(("Two consequtive line segments are parallel, but not on one straight line!\nThis should never happen."));
                return;
            }
            else if (res == 1) {
                Vect_append_point(nPoints, rx, ry, 0);
            }
            /* else if (res == 2) do nothing */
        }
        
        if (i == np-2) {
            Vect_append_point(nPoints, mx, my, 0);
        }
        
        a0 = a1;
        b0 = b1;
        c0 = c1;
        
    /*    
	if ( i < np-2 ) {   /*use polyline instead of arc between line segments 
	    norm_vector( x[i+1], y[i+1], x[i+2], y[i+2], &ux, &uy);
	    wx  =  uy * d;
	    wy  = -ux * d;
	    av = atan2 ( vy, vx );
	    aw = atan2 ( wy, wx );
	    a = (aw - av) * side;
	    if ( a < 0 )  a+=2*PI;

             /*TODO: a <= PI can probably fail because of representation error 
	    if ( a <= PI && a > atol)
	    {
		na = (int) (a/atol);
		atol2 = a/(na+1) * side;
		for (j = 0; j < na; j++)
		{
		    av+=atol2;
		    nx = x[i+1] + fabs(d) * cos(av);
		    ny = y[i+1] + fabs(d) * sin(av);
		    Vect_append_point ( nPoints, nx, ny, 0 );
		}
	    }
	}*/
    }
    Vect_line_prune ( nPoints );
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
void Vect_line_parallel2(struct line_pnts *InPoints, double da, double db, double dalpha, int side, int round, int loops, double tol, struct line_pnts *OutPoints )
{
    G_debug(4, "Vect_line_parallel(): npoints = %d, da = %f, db = %f, dalpha = %f, side = %d, round_corners = %d, loops = %d, tol = %f",
            InPoints->n_points, da, db, dalpha, side, round, loops, tol);

    parallel_line (InPoints, da, db, dalpha, side, round, tol, OutPoints);
    
/*    if (!loops)
        clean_parallel(OutPoints, InPoints, distance, rm_end);
        */
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



