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
 
 
/* TODO take in account if it is long/lat projection */
/* TODO vis initialisation algorithm can be optimised with a scan line technic which runs in O( n log n ) instead of O( n^2 ); */

#include "visibility.h"

void count( struct Map_info * map, int * num_points, int * num_lines)
{
	int index_line = 0;
	int index_point = 0;
	struct line_pnts* sites;
	struct line_cats* cats;
	int type,i;
	
	sites = Vect_new_line_struct();
	cats = Vect_new_cats_struct();
	
	G_message("N lines %d", map->plus.n_lines);
	
	for( i = 1; i <= map->plus.n_lines ; i++ )
	{
	
		type = Vect_read_line( map, sites, cats, i);
		
		if ( type != GV_LINE && type != GV_BOUNDARY)
			continue;
		
		if ( type == GV_LINE )
		{
			index_point+= sites->n_points;
			index_line+= sites->n_points-1;
		}
		else if ( type == GV_BOUNDARY )
		{
			index_point+= sites->n_points-1;
			index_line+= sites->n_points-1;
		}
		
		
	}
	
	*num_points = index_point;
	*num_lines = index_line;

}


/** Get the lines from the map and load them in an array
*/
void load_lines( struct Map_info * map, struct Point ** points, int * num_points, struct Line ** lines, int * num_lines )
{
	int index_line = 0;
	int index_point = 0;
	struct line_pnts* sites;
	int i;
	struct line_cats* cats;
	int cat,type;
	
	sites = Vect_new_line_struct();
	cats = Vect_new_cats_struct();
	
	count( map, num_points, num_lines);
	
	*points = G_malloc( *num_points * sizeof( struct Point ));
	*lines = G_malloc( *num_lines * sizeof( struct Line ));
	
	G_message("We have %d points and %d segments", *num_points, *num_lines );
	
	
	while( ( type = Vect_read_next_line( map, sites, cats) ) > -1 )
	{
	
		if ( type != GV_LINE && type != GV_BOUNDARY)
			continue;
		
		Vect_cat_get (cats, 1, &cat);
		
		G_message("For now %d and %d", index_point, index_line );
		
		if ( type == GV_LINE )
			process_line(sites, points, &index_point, lines, &index_line, cat);
		else if ( type == GV_BOUNDARY )
			process_boundary(sites, points, &index_point, lines, &index_line, cat);
		//else if ( type == GV_POINT )
		
		
	}
}


void process_line( struct line_pnts * sites, struct Point ** points, int * index_point, struct Line ** lines, int * index_line, int cat)
{
	int n = sites->n_points;
	int i;

	for ( i = 0; i < n; i++ )
	{
	
		(*points)[*index_point].x = sites->x[i];
		(*points)[*index_point].y = sites->y[i];
		
		if ( i == 0 )
		{
			(*points)[*index_point].line1 = NULL;
			(*points)[*index_point].line2 = &((*lines)[*index_line]);
		}
		else if ( i == n-1 )
		{
			(*points)[*index_point].line1 = &((*lines)[(*index_line)-1]);
			(*points)[*index_point].line2 = NULL;
		}	
		else
		{
			(*points)[*index_point].line1 = &((*lines)[(*index_line)-1]);
			(*points)[*index_point].line2 = &((*lines)[*index_line]);
		}
		
		(*points)[*index_point].left_brother = NULL;
		(*points)[*index_point].right_brother = NULL;
		(*points)[*index_point].father = NULL;
		(*points)[*index_point].rightmost_son = NULL;
		
		
		(*index_point)++;
		
		if ( i < n-1 )
		{
			(*lines)[*index_line].p1 = &((*points)[(*index_point)-1]);
			(*lines)[*index_line].p2 = &((*points)[*index_point]);
			(*index_line)++;
		}
	}
}


void process_boundary( struct line_pnts * sites, struct Point ** points, int * index_point, struct Line ** lines, int * index_line, int cat)
{
	int n = sites->n_points;
	int i; 

	for ( i = 0; i < n-1; i++ )
	{
	
		(*points)[*index_point].x = sites->x[i];
		(*points)[*index_point].y = sites->y[i];
		
		if ( i == 0 )
		{
			(*points)[*index_point].line1 = &((*lines)[(*index_line)+n-2]);
			(*points)[*index_point].line2 = &((*lines)[*index_line]);
		}	
		else
		{
			(*points)[*index_point].line1 = &((*lines)[(*index_line)-1]);
			(*points)[*index_point].line2 = &((*lines)[*index_line]);
		}
		
		(*points)[*index_point].left_brother = NULL;
		(*points)[*index_point].right_brother = NULL;
		(*points)[*index_point].father = NULL;
		(*points)[*index_point].rightmost_son = NULL;
		
		
		(*index_point)++;
		
		if ( i == n-2 )
		{
			(*lines)[*index_line].p1 = &((*points)[(*index_point)-1]);
			(*lines)[*index_line].p2 = &((*points)[(*index_point)-n+1]);
		}
		else
		{
			(*lines)[*index_line].p1 = &((*points)[(*index_point)-1]);
			(*lines)[*index_line].p2 = &((*points)[*index_point]);
		}
			
		(*index_line)++;
	}

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


/** for all points initiate their vis line to the one directly below
*/
void init_vis( struct Point * points, int num_points, struct Line * lines, int num_lines )
{

	int i;
	int j;
	int current = -1;
	double current_distance = PORT_DOUBLE_MAX;
	double s;
	
	for ( i = 0 ; i < num_points ; i++ )
	{
		for ( j = 0 ; j < num_lines ; j++ )
		{
			
			
			if ( &lines[j] == segment1( &points[i]) || &lines[j] == segment2( &points[i]))
				continue;
			
			/* if it's directly below, compute its distance to the last smallest found */
			if ( below( &points[i], &lines[j] ) && in_between( &points[i], &lines[j] ) )
			{			

				s = segment_sqdistance( &points[i], &lines[j]);
				
				
				if(  s < current_distance)
				{
					current = j;
					current_distance = s;
				}
			}
		}
		
		if ( current == -1 )
		{
			points[i].vis = NULL;
		}
		else
		{
			points[i].vis = &lines[current];
		}
		
		current = -1;
		current_distance = PORT_DOUBLE_MAX;
	}
}

/** for a pair (p, q) of points, add the edge pq if their are visibile to each other
*/
void handle( struct Point* p, struct Point* q, struct Map_info * out )
{
	if ( q == other1(p)  )
	{

		if ( segment1(q) == segment1(p) && segment2(q) != NULL && left_turn(p,q, other2(q)))
		{
			p->vis = segment2(q);
		}
		else if ( segment2(q) == segment1(p) && segment1(q) != NULL && left_turn(p,q, other1(q)))
		{
			p->vis = segment1(q);
		}
		else
		{
			p->vis = q->vis;
		}
		
		
		report( p, q, out );
	}
	else if ( q == other2(p))
	{
		
		if ( segment1(q) == segment2(p) && segment2(q) != NULL && left_turn(p,q, other2(q)))
		{
			p->vis = segment2(q);
		}
		else if ( segment2(q) == segment2(p) && segment1(q) != NULL && left_turn(p,q, other1(q)))
		{
			p->vis = segment1(q);
		}
		else
		{
			p->vis = q->vis;
		}
	
		report(p, q, out );
	}
	else if ( segment1(q) == p->vis && segment1(q) != NULL)
	{
		
		if ( segment2(q) != NULL && left_turn(p, q, other2(q)))
			p->vis = segment2(q);
		else
			p->vis = q->vis ;

		report( p,q, out );
	}
	else if ( segment2(q) == p->vis && segment2(q) != NULL )
	{
		if ( segment1(q) != NULL && left_turn(p, q, other1(q) ))
			p->vis = segment1(q);
		else
			p->vis = q->vis;
		
		report( p,q, out );
	}
	else if ( before(p,q, p->vis ) )
	{
		if ( segment2(q) == NULL)
			p->vis = segment1(q);
		else if ( segment1(q) == NULL )
			p->vis = segment2(q);
		else if ( left_turn(p, q, other1(q) ) && !left_turn( p, q, other2(q)))
			p->vis = segment1(q);
		else if ( !left_turn(p, q, other1(q) ) && left_turn( p, q, other2(q)))
			p->vis = segment2(q);
		else if ( (dot(p,q, other1(q) )/ distance(q, other1(q)) ) <  (dot(p,q,other2(q))/distance(q, other2(q))) )
			p->vis = segment1(q);
		else 
			p->vis = segment2(q);
		
		report(p,q,out);
	}
}

/** add the edge pq to the map out 
*/
void report( struct Point * p, struct Point * q, struct Map_info * out )
{
	struct line_pnts* sites;
	struct line_cats* cats;
	double * tmpx = G_malloc( 2*sizeof(double));
	double * tmpy = G_malloc( 2*sizeof(double));
	
	sites = Vect_new_line_struct ();
    cats = Vect_new_cats_struct ();
	
	tmpx[0] = p->x; tmpx[1] = q->x;
	tmpy[0] = p->y; tmpy[1] = q->y;
	
    Vect_copy_xyz_to_pnts(sites, tmpx, tmpy, 0, 2);
    Vect_write_line (out, GV_LINE, sites, cats);
	
	G_free(tmpx);
	G_free(tmpy);
}


/** compare the points along the x axis
*/
int cmp_points(struct Point * v1, struct Point* v2) {
    struct Point *p1, *p2;
    p1 = (struct Point*) v1;
    p2 = (struct Point*) v2;
	
    if( p1->x < p2->x )
        return 1;
    else if( p1->x > p2->x )
        return -1;
    else if ( p1->y < p2->y )
        return 1;
	else if ( p1->y > p2->y )
		return -1;
	else
		return 0;
}

/** the algorithm that computes the visibility graph
*/
int construct_visibility ( struct Point * points, int num_points, struct Line * lines, int num_lines, struct Map_info * out )
{
	struct Point * p, * p_r, * q, * z;
	struct Point * p_infinity,* p_ninfinity;
	int i;

	p_ninfinity = (struct Point * ) malloc( sizeof(struct Point ));
	p_infinity = (struct Point * ) malloc( sizeof(struct Point ));
	
	p_ninfinity->x = PORT_DOUBLE_MAX;
	p_ninfinity->y = -PORT_DOUBLE_MAX;
	p_ninfinity->father = NULL;
	p_ninfinity->left_brother = NULL;
	p_ninfinity->right_brother = NULL;
	p_ninfinity->rightmost_son = NULL;
	
	p_infinity->x = PORT_DOUBLE_MAX;
	p_infinity->y = PORT_DOUBLE_MAX;
	p_infinity->father = NULL;
	p_infinity->left_brother = NULL;
	p_infinity->right_brother = NULL;
	p_infinity->rightmost_son = NULL;


	for ( i = 0 ; i < num_points ; i++ )
		G_message("Point %d with line %d and %d", &points[i], points[i].line1, points[i].line2 );
	for( i = 0 ; i < num_lines ; i++ )
		G_message("Line %d with points %d and %d", &lines[i], lines[i].p1, lines[i].p2 );
	
	
	G_message("Initialisation of the stack ... ");
	init_stack(num_points);

	G_message("Sorting the points by decreasing order...");
	/* sort points in decreasing x order*/
	quickSort( points, 0, num_points-1 );
	

	G_message("initialisation of the vis...");
	init_vis( points, num_points, lines, num_lines );
	
	
	G_message("Initialisation of the rotation tree...");
	add_rightmost( p_ninfinity, p_infinity );
	
	for ( i = 0; i < num_points ; i ++ )
	{
		add_rightmost( &points[i], p_ninfinity );	
	}
		
	push( &points[0] );
	
	int count = 0;
	
	G_message("Start of the main loop ... ");
	
	/* main loop */
	while( !empty_stack() )
	{
		
		p = pop();
		p_r = right_brother(p);
		q = father(p);
		
		/* if the father is not -infinity, handle p and q */
		if ( q != p_ninfinity )
		{
			handle(p,q, out);
			count++;
		}
			
		z = left_brother(q);
		
		remove_point(p);
		
		/* remove and reattach p to the tree */
		if ( z == NULL || !left_turn(p,z, father(z) ) )
		{
			add_leftof(p,q);
		}
		else
		{
			
			while( rightmost_son(z) != NULL && left_turn(p, rightmost_son(z),z) )
				z = rightmost_son(z);
			
			add_rightmost(p,z);
			
			if ( z == top() )
				z = pop();
		}
		
		/* if p not attached to infinity, then p has more points to visit */
		if ( left_brother(p) == NULL && father(p) != p_infinity )
		{
			push(p);
		}
		
		/* and continue with the next one ( from left to right )*/
		if ( p_r != NULL )
		{
			push(p_r);
		}
	}
	
	G_free(p_infinity);
	G_free(p_ninfinity);
}


struct Point * pop()
{
	stack_index--;
	
	return stack[stack_index+1];
}

struct Point * top()
{
	return stack[stack_index];
}

void push(struct Point * p)
{
	stack_index++;
	stack[stack_index] = p;
}

int empty_stack()
{
	return stack_index == 0;
}

void init_stack(int size)
{
	stack_index = 0;
	stack = G_malloc( size * sizeof( struct Point ) );
}


void quickSort( struct Point a[], int l, int r)
{
   int j;

   if( l < r ) 
   {
		// divide and conquer
		j = partition( a, l, r);
		quickSort( a, l, j-1);
		quickSort( a, j+1, r);
   }
	
}


int partition( struct Point a[], int l, int r)
{
	int i, j;
   
	struct Point t,pivot;
   
	pivot = a[l];
	i = l; j = r+1;
		
	while( 1)
	{
		do ++i; while( cmp_points(&a[i], &pivot) < 1 && i <= r );
		do --j; while( cmp_points(&a[j], &pivot) == 1 );

		if( i >= j ) break;
		
		if ( a[i].line1 != NULL)
		{
			if ( a[i].line1->p1 == &a[i] ) a[i].line1->p1 = &a[j];
			else a[i].line1->p2 = &a[j];
		}
		
		if ( a[j].line1 != NULL )
		{
			if(a[j].line1->p1 == &a[j] ) a[j].line1->p1 = &a[i];
			else a[j].line1->p2 = &a[i];
		}
	
		if ( a[i].line2 != NULL )
		{
			if( a[i].line2->p1 == &a[i] ) a[i].line2->p1 = &a[j];
			else a[i].line2->p2 = &a[j];
		}
		
		if ( a[j].line2 != NULL )
		{
			if(a[j].line2->p1 == &a[j] ) a[j].line2->p1 = &a[i];
			else a[j].line2->p2 = &a[i];
		}
		
		t = a[i]; a[i] = a[j]; a[j] = t;
		
	}

	if ( a[l].line1 != NULL )
	{
		if(a[l].line1->p1 == &a[l] ) a[l].line1->p1 = &a[j];
		else a[l].line1->p2 = &a[j];
	}
		
	if ( a[j].line1 != NULL )
	{
		if(a[j].line1->p1 == &a[j] ) a[j].line1->p1 = &a[l];
		else a[j].line1->p2 = &a[l];
	}
	
	if ( a[l].line2 != NULL )
	{
		if( a[l].line2->p1 == &a[l] ) a[l].line2->p1 = &a[j];
		else a[l].line2->p2 = &a[j];
	}
		
	if ( a[j].line2 != NULL )
	{
		if( a[j].line2->p1 == &a[j] ) a[j].line2->p1 = &a[l];
		else a[j].line2->p2 = &a[l];
	}

	t = a[l]; a[l] = a[j]; a[j] = t;
	

	return j;
}

