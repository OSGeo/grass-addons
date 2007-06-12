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
		
		G_message("Line %d with points : %f %f %f %f", index_line, (*points)[index_point-1].x, (*points)[index_point-1].y, (*points)[index_point-2].x, (*points)[index_point-2].y );
		
	}
	
	return index_line;
}


int left_turn( struct Point * p1, struct Point * p2, struct Point * p3 )
{
    double a, b, c, d;
	
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
	
		return a*d - b*c < 0;	
	}
}

void init_vis( struct Point * points, struct Line * lines, int num )
{
	int i;
	int j;
	int current = 0;
	int null=0;
	double y;
	
	for ( i = 0 ; i < num ; i++ )
	{
		for ( j = 1 ; j < num/2 ; j++ )
		{
			
			if ( points[i].y < lines[j].p1->y && points[i].y < lines[j].p2->y )
			{
				if ( lines[current].p1->y < lines[current].p2->y )
					y = lines[current].p1->y;
				else
					y = lines[current].p2->y;

				if ( lines[j].p1->y < y || lines[j].p2->y < y )
				{
					current = j;
					null =1;
				}
			}
		}
		
		if ( null == 0 )
		{
			points[i].vis = NULL;
		}
		else
		{
			points[i].vis = &lines[current];
		}
		
		current = 0;
		null = 0;
	}
}

void handle( struct Point* p, struct Point* q, struct Map_info * out )
{	
	if ( q == other(p) )
	{
		report( p, q, out );
	}
	else if ( segment(q) == p->vis )
	{
		p->vis = q->vis ;
		report( p,q, out );
	}
	else if ( before(p,q, p->vis ) )
	{
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


int cmp_points(const void* v1, const void* v2) {
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

	
	init_vis( points, lines, num_points );
	
	init_stack(num_points);

	/* sort points in decreasing x order*/
    qsort(points, num_points, sizeof(struct Point), cmp_points);
	
	add_rightmost( p_ninfinity, p_infinity );
	
	for ( i = 0; i < num_points ; i ++ )
	{
		add_rightmost( &points[i], p_ninfinity );	
	}
		
	push( &points[0] );
	

	G_message("p_infinity is %d and p_ninfinity is %d ", p_infinity, p_ninfinity );
	
	while( !empty_stack() )
	{
		
		p = pop();
		p_r = right_brother(p);
		q = father(p);
		
		G_message("---------");
		G_message("p is %d and q is %d and p_r is %d", p, q ,p_r);
		
		if ( q != p_ninfinity )
		{
			G_message("Handling %d and %d", p,q);
			handle(p,q, out);
		}
			
		z = left_brother(q);
		
		G_message("z is %d", z );
		if ( z!= NULL ) G_message("father(z) is %d", father(z) );
		
		remove_point(p);
		
		if ( z == NULL || !left_turn(p,z, father(z) ) )
		{
			G_message("adding p leftof q ");
			add_leftof(p,q);
		}
		else
		{
			
			while( rightmost_son(z) != NULL && left_turn(p, rightmost_son(z),z) )
				z = rightmost_son(z);
			
			add_rightmost(p,z);
			
			G_message("add p as rightmost son of z which is %d", z);
			
			if ( z == top() )
				z = pop();
		}
		
		G_message("father(p) is now %d", father(p) );
		
		if ( left_brother(p) == NULL && father(p) != p_infinity )
		{
			G_message("pushing p");
			push(p);
		}
		
		if ( p_r != NULL )
		{
			push(p_r);
			G_message("pushing p_r ");
		}
		
		G_message("The stack has %d points", stack_index);
	}
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

