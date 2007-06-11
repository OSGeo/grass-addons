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

#include "rotation_tree.h"


void add_rightmost(struct Point* p, struct Point* q)
{
	q->rightmost_son = p;
	p->father = q;
}

void add_leftof(struct Point* p, struct Point* q)
{
	q->left_brother = p;
	p->right_brother = q;
	p->father = q->father;
}

void remove_point(struct Point* p)
{
	struct Point * f = p->father;
	struct Point * l = p->left_brother;
	struct Point * r = p->right_brother;
	
	if ( l != NULL )
		l->right_brother = NULL;
	if ( r != NULL )
		r->left_brother = NULL;
	
	if ( f->rightmost_son == p )
		f->rightmost_son = NULL;
		
	p->father = NULL;
	p->left_brother = NULL;
	p->right_brother = NULL;
	p->rightmost_son = NULL;
	
}

struct Point* right_brother(struct Point* p)
{
	return p->right_brother;
}

struct Point* left_brother(struct Point* p)
{
	return p->left_brother;
}

struct Point* father( struct Point* p)
{
	return p->father;
}

struct Point* rightmost_son( struct Point * p )
{
	return p->rightmost_son;
}

struct Line * segment( struct Point * p )
{
	return p->line;
}

struct Point * other( struct Point * p )
{	
	if ( p->line->p1 == p )
		return p->line->p2;
	else
		return p->line->p1;
}

int before( struct Point * p, struct Point * q, struct Line * e )
{
	/* true if q lies nearer to p than segment e*/
	
	if ( e == NULL )
		return 1;
	
	double pq = p->x * q->x + p->y*q->y;
	double pe1 = p->x * e->p1->x + p->y*e->p1->y;
	double pe2 = p->x * e->p2->x + p->y*e->p2->y;
	
	
	return ( pq < pe1 && pq < pe2 );
}

