/****************************************************************
 * MODULE:     v.path.obstacles
 *
 * AUTHOR(S):  Maximilian Maldacker
 *  
 *
 * COPYRIGHT:  (C) 2002-2005 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#include "geometry.h"

/** returns the square distance between point q and segment e
*/
double segment_sqdistance( struct Point * q, struct Line * e )
{
	
	double e2e1x =  e->p1->x - e->p2->x ;
	double e2e1y = e->p1->y - e->p2->y;
	
	double qe1x = q->x - e->p1->x;
	double qe1y = q->y - e->p1->y;
	
	double qe2x = q->x - e->p2->x;
	double qe2y = q->y - e->p2->y;
	
	double s = e2e1x * qe2x + e2e1y * qe2y;
	double t;
	
	if ( s <= 0 )
		return qe2x * qe2x + qe2y * qe2y;
		
	t = e2e1x * e2e1x + e2e1y * e2e1y;
	
	if ( s >= t )
		return qe1x * qe1x + qe1y * qe1y;
	
	 return qe2x * qe2x + qe2y * qe2y - s * s / t ;

}

/** true if q lies nearer to p than segment e
*/
int before( struct Point * p, struct Point * q, struct Line * e )
{	
	/* first determine the square distance between p and e */
	
	if ( e == NULL )
		return 1;
	
	double e_distance = segment_sqdistance(p, e);
	double pqx =  q->x - p->x;
	double pqy = q->y - p->y;
	double pq_distance = pqx*pqx + pqy*pqy;

	return pq_distance <= e_distance ;
}



/** returns true if p3 is left of the directed line p1p2
*/
int left_turn( struct Point * p1, struct Point * p2, struct Point * p3 )
{
    double a, b, c, d;
	double r;
	
	if ( p3->y == PORT_DOUBLE_MAX)
	{
		return ( p1->x < p2->x || (p1->x == p2->x && p1->y < p2->y ) );
	}
	else
	{
		a = p1->x - p2->x;
		b = p1->y - p2->y;
		c = p3->x - p2->x;
		d = p3->y - p2->y;
			
		return a*d-b*c < 0.0;
	}
}

/** returns true if p is inbetween the segment e along the x axis
*/
int in_between( struct Point * p, struct Line * e )
{
	int a =  e->p1->x < p->x && e->p2->x > p->x ;
	int b = e->p2->x < p->x && e->p1->x > p->x;
	
	return a || b;
}

/** returns true if p is above the segment e ( y axis )
*/
int below( struct Point * p, struct Line * e )
{
	return e->p1->y < p->y || e->p2->y < p->y ;
}

/** tests if the point (x, y ) is inside the boundary of p 
*/
int point_inside( struct Point * p, double x, double y )
{
	int c = 0;
	struct Point * n1 = p;
	struct Point * n2 = other1(p);

	do
	{
		if (  ( (   n2->y <=y  &&  y < n1->y ) ||
             (  n1->y <= y &&  y< n2->y ) ) &&
            (x < (n1->x - n2->x) * (y - n2->y) / (n1->y - n2->y) + n2->x))
			c = !c;
			
		n1 = other1(n1);
		n2 = other1(n2);

	}while ( n1 != p );
	
	return c;
}

