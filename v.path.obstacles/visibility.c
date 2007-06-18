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
 
#include "visibility.h"

int load_lines( struct Map_info * map, struct Point ** points, struct Line ** lines )
{
	int index_line = 0;
	int index_point = 0;
	struct line_pnts* sites;
	struct line_cats* cats;
	int cat,type;
	
	int nb_lines;
	
	sites = Vect_new_line_struct();
	cats = Vect_new_cats_struct();
	
	nb_lines = Vect_get_num_lines(map);
	*points = (struct Point * ) G_malloc( nb_lines*2*sizeof(struct Point) );
	*lines = ( struct Line * ) G_malloc( nb_lines*sizeof(struct Line) );
	
	/* TODO here is only the first segment of a line that is copied, need to fix that 
	 each point is associated with two segments except for the starting and ending point ( for line and boundary ) */
	
	while( ( type = Vect_read_next_line( map, sites, cats) ) > -1 )
	{
	
		if ( type != GV_LINE )
			continue;
		
		Vect_cat_get (cats, 1, &cat);
		
		(*points)[index_point].x = sites->x[0];
		(*points)[index_point].y = sites->y[0];
		(*points)[index_point].line = &((*lines)[index_line]);
		(*points)[index_point].left_brother = NULL;
		(*points)[index_point].right_brother = NULL;
		(*points)[index_point].father = NULL;
		(*points)[index_point].rightmost_son = NULL;
		
		
		index_point++;
		
		(*points)[index_point].x = sites->x[1];
		(*points)[index_point].y = sites->y[1];
		(*points)[index_point].line = &((*lines)[index_line]);
		(*points)[index_point].left_brother = NULL;
		(*points)[index_point].right_brother = NULL;
		(*points)[index_point].father = NULL;
		(*points)[index_point].rightmost_son = NULL;
		
		
		(*lines)[index_line].p1 = &((*points)[index_point-1]);
		(*lines)[index_line].p2 = &((*points)[index_point]);
				
		index_line++;
		index_point++;
		
		G_message("Line %d with points : %f %f %f %f", &((*lines)[index_line-1]), (*points)[index_point-1].x, (*points)[index_point-1].y, (*points)[index_point-2].x, (*points)[index_point-2].y );
		
	}
	
	return index_line;
}


int left_turn( struct Point * p1, struct Point * p2, struct Point * p3 )
{
    double a, b, c, d;
	double r;
	
	if ( p3 == p_infinity )
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


int in_between( struct Point * p, struct Line * e )
{
	int a =  e->p1->x < p->x && e->p2->x > p->x ;
	int b = e->p2->x < p->x && e->p1->x > p->x;
	
	return a || b;
}

int below( struct Point * p, struct Line * e )
{
	return e->p1->y < p->y || e->p2->y < p->y ;
}

void init_vis( struct Point * points, struct Line * lines, int num )
{
	/* this algorithm can be optimised with a scan line technic which runs in O( n log n ) instead of O( n^2 ); */
	int i;
	int j;
	int current = -1;
	double current_distance = PORT_DOUBLE_MAX;
	double s;
	
	for ( i = 0 ; i < num ; i++ )
	{
		for ( j = 0 ; j < num/2 ; j++ )
		{
			
			
			//if ( &lines[j] == segment( &points[i]) )
			//	continue;

			//G_message("For point %d with height %f we're considering line %d width height between %f and %f", &points[i], points[i].y, &lines[j], lines[j].p1->y, lines[j].p2->y );
			
			if ( below( &points[i], &lines[j] ) && in_between( &points[i], &lines[j] ) )
			{				
				s = segment_sqdistance( &points[i], &lines[j]);
				
				//G_message("The line is below the point and its distance is %f", s);
				
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
		
		G_message("VIS of point %d, ( %f ; %f)  is %d", &points[i], points[i].x, points[i].y, points[i].vis );

	}
}

void handle( struct Point* p, struct Point* q, struct Map_info * out )
{
	//G_message("Handling (  %f ; %f ) and ( %f ; %f )", p->x, p->y, q->x, q->y);
	G_message("Handling %d and %d Point %d with VIS %d and segment(q) = %d", p,q,p, p->vis, segment(q) );
	
	if ( q == other(p) )
	{
		//G_message("It's the other");
		//p->vis = q->vis ;
		report( p, q, out );
	}
	else if ( segment(q) == p->vis )
	{
		//G_message("Its the vis!!!! New VIS is %d", q->vis);
		p->vis = q->vis ;
		report( p,q, out );
	}
	else if ( before(p,q, p->vis ) )
	{
		//G_message("before!! New VIS %d", segment(q));
		p->vis = segment(q);
		report(p,q,out);
	}
}

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


int construct_visibility ( struct Point * points, struct Line * lines, int num_lines, struct Map_info * out )
{
	int num_points = 2*num_lines;
	struct Point * p, * p_r, * q, * z;
	int i;
	
	p_ninfinity = G_malloc( sizeof(struct Point ));
	p_infinity = G_malloc( sizeof(struct Point ));
	
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
	
	init_stack(num_points);

	/* sort points in decreasing x order*/
    //qsort(points, num_points, sizeof(struct Point), cmp_points);
	quickSort( points, 0, num_points-1 );
	
	init_vis( points, lines, num_points );
	
	add_rightmost( p_ninfinity, p_infinity );
	
	for ( i = 0; i < num_points ; i ++ )
	{
		add_rightmost( &points[i], p_ninfinity );	
	}
		
	push( &points[0] );
	
	int count = 0;

	//G_message("p_infinity is %d and p_ninfinity is %d ", p_infinity, p_ninfinity );
	
	while( !empty_stack() )
	{
		
		p = pop();
		p_r = right_brother(p);
		q = father(p);
		
		//G_message("---------");
		//G_message("p is %d and q is %d and p_r is %d", p, q ,p_r);
		
		if ( q != p_ninfinity )
		{
			handle(p,q, out);
			count++;
		}
			
		z = left_brother(q);
		
		//G_message("z is %d", z );
		//if ( z!= NULL ) G_message("father(z) is %d", father(z) );
		
		remove_point(p);
		
		if ( z == NULL || !left_turn(p,z, father(z) ) )
		{
			//G_message("adding p leftof q ");
			add_leftof(p,q);
		}
		else
		{
			
			while( rightmost_son(z) != NULL && left_turn(p, rightmost_son(z),z) )
				z = rightmost_son(z);
			
			add_rightmost(p,z);
			
			//G_message("add p as rightmost son of z which is %d", z);
			
			if ( z == top() )
				z = pop();
		}
		
		//G_message("father(p) is now %d", father(p) );
		
		if ( left_brother(p) == NULL && father(p) != p_infinity )
		{
			//G_message("pushing p");
			push(p);
		}
		
		if ( p_r != NULL )
		{
			push(p_r);
			//G_message("pushing p_r ");
		}
		
		//G_message("The stack has %d points", stack_index);
	}
	
	G_warning("There was %d comparisons for %d points", count, num_points);
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

/* TODO take in account if it is long/lat projection */

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
		
		if ( a[i].line->p1 == &a[i] ) a[i].line->p1 = &a[j];
		else a[i].line->p2 = &a[j];
		
		if ( a[j].line->p1 == &a[j] ) a[j].line->p1 = &a[i];
		else a[j].line->p2 = &a[i];		
		
		t = a[i]; a[i] = a[j]; a[j] = t;
		
	}

	if ( a[l].line->p1 == &a[l] ) a[l].line->p1 = &a[j];
	else a[l].line->p2 = &a[j];
		
	if ( a[j].line->p1 == &a[j] ) a[j].line->p1 = &a[l];
	else a[j].line->p2 = &a[l];

	t = a[l]; a[l] = a[j]; a[j] = t;
	

	return j;
}

