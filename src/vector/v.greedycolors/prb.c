/* Produced by texiweb from libavl.w. */

/* libavl - library for manipulation of binary trees.
   Copyright (C) 1998, 1999, 2000, 2001, 2002, 2004 Free Software
   Foundation, Inc.

   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public
   License as published by the Free Software Foundation; either
   version 3 of the License, or (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public
   License along with this library; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
   02110-1301 USA.
 */

/* Nov 2016, Markus Metz
 * from libavl-2.0.3
 * added safety checks and speed optimizations
 */

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "prb.h"

/* Creates and returns a new table
   with comparison function |compare| using parameter |param|
   and memory allocator |allocator|.
   Returns |NULL| if memory allocation failed. */
struct prb_table *prb_create(prb_comparison_func * compare, void *param,
			     struct libavl_allocator *allocator)
{
    struct prb_table *tree;

    assert(compare != NULL);

    if (allocator == NULL)
	allocator = &prb_allocator_default;

    tree = allocator->libavl_malloc(allocator, sizeof *tree);
    if (tree == NULL)
	return NULL;

    tree->prb_root = NULL;
    tree->prb_compare = compare;
    tree->prb_param = param;
    tree->prb_alloc = allocator;
    tree->prb_count = 0;

    return tree;
}

/* Search |tree| for an item matching |item|, and return it if found.
   Otherwise return |NULL|. */
void *prb_find(const struct prb_table *tree, const void *item)
{
    const struct prb_node *p;

    assert(tree != NULL && item != NULL);

    p = tree->prb_root;
    while (p != NULL) {
	int cmp = tree->prb_compare(item, p->prb_data, tree->prb_param);

	if (cmp == 0)
	    return p->prb_data;

	p = p->prb_link[cmp > 0];
    }

    return NULL;
}

/* Inserts |item| into |tree| and returns a pointer to |item|'s address.
   If a duplicate item is found in the tree,
   returns a pointer to the duplicate without inserting |item|.
   Returns |NULL| in case of memory allocation failure. */
void **prb_probe(struct prb_table *tree, void *item)
{
    struct prb_node *p;		/* Traverses tree looking for insertion point. */
    struct prb_node *q;		/* Parent of |p|; node at which we are rebalancing. */
    struct prb_node *n;		/* Newly inserted node. */
    int dir;			/* Side of |q| on which |n| is inserted. */

    assert(tree != NULL && item != NULL);

    p = tree->prb_root;
    q = NULL;
    dir = 0;
    while (p != NULL) {
	int cmp = tree->prb_compare(item, p->prb_data, tree->prb_param);

	if (cmp == 0)
	    return &p->prb_data;

	dir = cmp > 0;
	q = p, p = p->prb_link[dir];
    }

    n = tree->prb_alloc->libavl_malloc(tree->prb_alloc, sizeof *p);
    if (n == NULL)
	return NULL;

    tree->prb_count++;
    n->prb_link[0] = n->prb_link[1] = NULL;
    n->prb_parent = q;
    n->prb_data = item;
    if (q == NULL) {
	n->prb_color = PRB_BLACK;
	tree->prb_root = n;
	
	return &n->prb_data;
    }
    n->prb_color = PRB_RED;
    q->prb_link[dir] = n;

    q = n;
    while (q != NULL) {
	struct prb_node *f;	/* Parent of |q|. */
	struct prb_node *g;	/* Grandparent of |q|. */

	f = q->prb_parent;
	if (f == NULL || f->prb_color == PRB_BLACK)
	    break;

	g = f->prb_parent;
	if (g == NULL)
	    break;

	if (g->prb_link[0] == f) {
	    struct prb_node *y = g->prb_link[1];

	    if (y != NULL && y->prb_color == PRB_RED) {
		f->prb_color = y->prb_color = PRB_BLACK;
		g->prb_color = PRB_RED;
		q = g;
	    }
	    else {
		struct prb_node *h;	/* Great-grandparent of |q|. */

		h = g->prb_parent;
		if (h == NULL)
		    h = (struct prb_node *)&tree->prb_root;

		if (f->prb_link[1] == q) {
		    f->prb_link[1] = q->prb_link[0];
		    q->prb_link[0] = f;
		    g->prb_link[0] = q;
		    f->prb_parent = q;
		    if (f->prb_link[1] != NULL)
			f->prb_link[1]->prb_parent = f;

		    f = q;
		}

		g->prb_color = PRB_RED;
		f->prb_color = PRB_BLACK;

		g->prb_link[0] = f->prb_link[1];
		f->prb_link[1] = g;
		h->prb_link[h->prb_link[0] != g] = f;

		f->prb_parent = g->prb_parent;
		g->prb_parent = f;
		if (g->prb_link[0] != NULL)
		    g->prb_link[0]->prb_parent = g;
		break;
	    }
	}
	else {
	    struct prb_node *y = g->prb_link[0];

	    if (y != NULL && y->prb_color == PRB_RED) {
		f->prb_color = y->prb_color = PRB_BLACK;
		g->prb_color = PRB_RED;
		q = g;
	    }
	    else {
		struct prb_node *h;	/* Great-grandparent of |q|. */

		h = g->prb_parent;
		if (h == NULL)
		    h = (struct prb_node *)&tree->prb_root;

		if (f->prb_link[0] == q) {
		    f->prb_link[0] = q->prb_link[1];
		    q->prb_link[1] = f;
		    g->prb_link[1] = q;
		    f->prb_parent = q;
		    if (f->prb_link[0] != NULL)
			f->prb_link[0]->prb_parent = f;

		    f = q;
		}

		g->prb_color = PRB_RED;
		f->prb_color = PRB_BLACK;

		g->prb_link[1] = f->prb_link[0];
		f->prb_link[0] = g;
		h->prb_link[h->prb_link[0] != g] = f;

		f->prb_parent = g->prb_parent;
		g->prb_parent = f;
		if (g->prb_link[1] != NULL)
		    g->prb_link[1]->prb_parent = g;
		break;
	    }
	}
    }
    tree->prb_root->prb_color = PRB_BLACK;

    return &n->prb_data;
}

/* Inserts |item| into |table|.
   Returns |NULL| if |item| was successfully inserted
   or if a memory allocation error occurred.
   Otherwise, returns the duplicate item. */
void *prb_insert(struct prb_table *table, void *item)
{
    void **p = prb_probe(table, item);

    return p == NULL || *p == item ? NULL : *p;
}

/* Inserts |item| into |table|, replacing any duplicate item.
   Returns |NULL| if |item| was inserted without replacing a duplicate,
   or if a memory allocation error occurred.
   Otherwise, returns the item that was replaced. */
void *prb_replace(struct prb_table *table, void *item)
{
    void **p = prb_probe(table, item);

    if (p == NULL || *p == item)
	return NULL;
    else {
	void *r = *p;

	*p = item;

	return r;
    }
}

/* Deletes from |tree| and returns an item matching |item|.
   Returns a null pointer if no matching item found. */
void *prb_delete(struct prb_table *tree, const void *item)
{
    struct prb_node *p;		/* Node to delete. */
    struct prb_node *q;		/* Parent of |p|. */
    struct prb_node *f;		/* Node at which we are rebalancing. */
    int cmp;			/* Result of comparison between |item| and |p|. */
    int dir;			/* Side of |q| on which |p| is a child;
				   side of |f| from which node was deleted. */

    assert(tree != NULL && item != NULL);

    p = tree->prb_root;
    dir = 0;
    while (p != NULL) {
	cmp = tree->prb_compare(item, p->prb_data, tree->prb_param);

	if (cmp == 0)
	    break;

	dir = cmp > 0;
	p = p->prb_link[dir];
    }
    if (p == NULL)
	return NULL;

    item = p->prb_data;

    q = p->prb_parent;
    if (q == NULL) {
	q = (struct prb_node *)&tree->prb_root;
	dir = 0;
    }

    if (p->prb_link[1] == NULL) {
	q->prb_link[dir] = p->prb_link[0];
	if (q->prb_link[dir] != NULL)
	    q->prb_link[dir]->prb_parent = p->prb_parent;

	f = q;
    }
    else {
	enum prb_color t;
	struct prb_node *r = p->prb_link[1];

	if (r->prb_link[0] == NULL) {
	    r->prb_link[0] = p->prb_link[0];
	    q->prb_link[dir] = r;
	    r->prb_parent = p->prb_parent;
	    if (r->prb_link[0] != NULL)
		r->prb_link[0]->prb_parent = r;

	    t = p->prb_color;
	    p->prb_color = r->prb_color;
	    r->prb_color = t;

	    f = r;
	    dir = 1;
	}
	else {
	    struct prb_node *s = r->prb_link[0];

	    while (s->prb_link[0] != NULL)
		s = s->prb_link[0];
	    r = s->prb_parent;
	    r->prb_link[0] = s->prb_link[1];
	    s->prb_link[0] = p->prb_link[0];
	    s->prb_link[1] = p->prb_link[1];
	    q->prb_link[dir] = s;
	    if (s->prb_link[0] != NULL)
		s->prb_link[0]->prb_parent = s;
	    s->prb_link[1]->prb_parent = s;
	    s->prb_parent = p->prb_parent;
	    if (r->prb_link[0] != NULL)
		r->prb_link[0]->prb_parent = r;

	    t = p->prb_color;
	    p->prb_color = s->prb_color;
	    s->prb_color = t;

	    f = r;
	    dir = 0;
	}
    }

    if (p->prb_color == PRB_BLACK) {
	while (f != NULL) {
	    struct prb_node *x;	/* Node we want to recolor black if possible. */
	    struct prb_node *g;	/* Parent of |f|. */
	    struct prb_node *t;	/* Temporary for use in finding parent. */

	    x = f->prb_link[dir];
	    if (x != NULL && x->prb_color == PRB_RED) {
		x->prb_color = PRB_BLACK;
		break;
	    }

	    if (f == (struct prb_node *)&tree->prb_root)
		break;

	    g = f->prb_parent;
	    if (g == NULL)
		g = (struct prb_node *)&tree->prb_root;

	    if (dir == 0) {
		struct prb_node *w = f->prb_link[1];

		if (w->prb_color == PRB_RED) {
		    w->prb_color = PRB_BLACK;
		    f->prb_color = PRB_RED;

		    f->prb_link[1] = w->prb_link[0];
		    w->prb_link[0] = f;
		    g->prb_link[g->prb_link[0] != f] = w;

		    w->prb_parent = f->prb_parent;
		    f->prb_parent = w;

		    g = w;
		    w = f->prb_link[1];

		    w->prb_parent = f;
		}

		if ((w->prb_link[0] == NULL
		     || w->prb_link[0]->prb_color == PRB_BLACK)
		    && (w->prb_link[1] == NULL
			|| w->prb_link[1]->prb_color == PRB_BLACK)) {
		    w->prb_color = PRB_RED;
		}
		else {
		    if (w->prb_link[1] == NULL
			|| w->prb_link[1]->prb_color == PRB_BLACK) {
			struct prb_node *y = w->prb_link[0];

			y->prb_color = PRB_BLACK;
			w->prb_color = PRB_RED;
			w->prb_link[0] = y->prb_link[1];
			y->prb_link[1] = w;
			if (w->prb_link[0] != NULL)
			    w->prb_link[0]->prb_parent = w;
			w = f->prb_link[1] = y;
			w->prb_link[1]->prb_parent = w;
		    }

		    w->prb_color = f->prb_color;
		    f->prb_color = PRB_BLACK;
		    w->prb_link[1]->prb_color = PRB_BLACK;

		    f->prb_link[1] = w->prb_link[0];
		    w->prb_link[0] = f;
		    g->prb_link[g->prb_link[0] != f] = w;

		    w->prb_parent = f->prb_parent;
		    f->prb_parent = w;
		    if (f->prb_link[1] != NULL)
			f->prb_link[1]->prb_parent = f;
		    break;
		}
	    }
	    else {
		struct prb_node *w = f->prb_link[0];

		if (w->prb_color == PRB_RED) {
		    w->prb_color = PRB_BLACK;
		    f->prb_color = PRB_RED;

		    f->prb_link[0] = w->prb_link[1];
		    w->prb_link[1] = f;
		    g->prb_link[g->prb_link[0] != f] = w;

		    w->prb_parent = f->prb_parent;
		    f->prb_parent = w;

		    g = w;
		    w = f->prb_link[0];

		    w->prb_parent = f;
		}

		if ((w->prb_link[0] == NULL
		     || w->prb_link[0]->prb_color == PRB_BLACK)
		    && (w->prb_link[1] == NULL
			|| w->prb_link[1]->prb_color == PRB_BLACK)) {
		    w->prb_color = PRB_RED;
		}
		else {
		    if (w->prb_link[0] == NULL
			|| w->prb_link[0]->prb_color == PRB_BLACK) {
			struct prb_node *y = w->prb_link[1];

			y->prb_color = PRB_BLACK;
			w->prb_color = PRB_RED;
			w->prb_link[1] = y->prb_link[0];
			y->prb_link[0] = w;
			if (w->prb_link[1] != NULL)
			    w->prb_link[1]->prb_parent = w;
			w = f->prb_link[0] = y;
			w->prb_link[0]->prb_parent = w;
		    }

		    w->prb_color = f->prb_color;
		    f->prb_color = PRB_BLACK;
		    w->prb_link[0]->prb_color = PRB_BLACK;

		    f->prb_link[0] = w->prb_link[1];
		    w->prb_link[1] = f;
		    g->prb_link[g->prb_link[0] != f] = w;

		    w->prb_parent = f->prb_parent;
		    f->prb_parent = w;
		    if (f->prb_link[0] != NULL)
			f->prb_link[0]->prb_parent = f;
		    break;
		}
	    }

	    t = f;
	    f = f->prb_parent;
	    if (f == NULL)
		f = (struct prb_node *)&tree->prb_root;
	    dir = f->prb_link[0] != t;
	}
    }

    tree->prb_alloc->libavl_free(tree->prb_alloc, p);
    tree->prb_count--;

    if (tree->prb_root != NULL)
	tree->prb_root->prb_color = PRB_BLACK;

    return (void *)item;
}

/* Deletes from |tree| and returns first item.
   Returns a null pointer if the tree is empty. */
void *prb_delete_first(struct prb_table *tree)
{
    struct prb_node *p;		/* Node to delete. */
    struct prb_node *q;		/* Parent of |p|. */
    struct prb_node *f;		/* Node at which we are rebalancing. */
    int dir;			/* Side of |q| on which |p| is a child;
				   side of |f| from which node was deleted. */
    const void *item;

    assert(tree != NULL);

    p = tree->prb_root;
    if (p == NULL)
	return NULL;

    dir = 0;
    while (p->prb_link[dir] != NULL)
	p = p->prb_link[dir];

    item = p->prb_data;

    q = p->prb_parent;
    if (q == NULL) {
	q = (struct prb_node *)&tree->prb_root;
	dir = 0;
    }

    if (p->prb_link[1] == NULL) {
	q->prb_link[dir] = p->prb_link[0];
	if (q->prb_link[dir] != NULL)
	    q->prb_link[dir]->prb_parent = p->prb_parent;

	f = q;
    }
    else {
	enum prb_color t;
	struct prb_node *r = p->prb_link[1];

	if (r->prb_link[0] == NULL) {
	    r->prb_link[0] = p->prb_link[0];
	    q->prb_link[dir] = r;
	    r->prb_parent = p->prb_parent;
	    if (r->prb_link[0] != NULL)
		r->prb_link[0]->prb_parent = r;

	    t = p->prb_color;
	    p->prb_color = r->prb_color;
	    r->prb_color = t;

	    f = r;
	    dir = 1;
	}
	else {
	    struct prb_node *s = r->prb_link[0];

	    while (s->prb_link[0] != NULL)
		s = s->prb_link[0];
	    r = s->prb_parent;
	    r->prb_link[0] = s->prb_link[1];
	    s->prb_link[0] = p->prb_link[0];
	    s->prb_link[1] = p->prb_link[1];
	    q->prb_link[dir] = s;
	    if (s->prb_link[0] != NULL)
		s->prb_link[0]->prb_parent = s;
	    s->prb_link[1]->prb_parent = s;
	    s->prb_parent = p->prb_parent;
	    if (r->prb_link[0] != NULL)
		r->prb_link[0]->prb_parent = r;

	    t = p->prb_color;
	    p->prb_color = s->prb_color;
	    s->prb_color = t;

	    f = r;
	    dir = 0;
	}
    }

    if (p->prb_color == PRB_BLACK) {
	while (f != NULL) {
	    struct prb_node *x;	/* Node we want to recolor black if possible. */
	    struct prb_node *g;	/* Parent of |f|. */
	    struct prb_node *t;	/* Temporary for use in finding parent. */

	    x = f->prb_link[dir];
	    if (x != NULL && x->prb_color == PRB_RED) {
		x->prb_color = PRB_BLACK;
		break;
	    }

	    if (f == (struct prb_node *)&tree->prb_root)
		break;

	    g = f->prb_parent;
	    if (g == NULL)
		g = (struct prb_node *)&tree->prb_root;

	    if (dir == 0) {
		struct prb_node *w = f->prb_link[1];

		if (w->prb_color == PRB_RED) {
		    w->prb_color = PRB_BLACK;
		    f->prb_color = PRB_RED;

		    f->prb_link[1] = w->prb_link[0];
		    w->prb_link[0] = f;
		    g->prb_link[g->prb_link[0] != f] = w;

		    w->prb_parent = f->prb_parent;
		    f->prb_parent = w;

		    g = w;
		    w = f->prb_link[1];

		    w->prb_parent = f;
		}

		if ((w->prb_link[0] == NULL
		     || w->prb_link[0]->prb_color == PRB_BLACK)
		    && (w->prb_link[1] == NULL
			|| w->prb_link[1]->prb_color == PRB_BLACK)) {
		    w->prb_color = PRB_RED;
		}
		else {
		    if (w->prb_link[1] == NULL
			|| w->prb_link[1]->prb_color == PRB_BLACK) {
			struct prb_node *y = w->prb_link[0];

			y->prb_color = PRB_BLACK;
			w->prb_color = PRB_RED;
			w->prb_link[0] = y->prb_link[1];
			y->prb_link[1] = w;
			if (w->prb_link[0] != NULL)
			    w->prb_link[0]->prb_parent = w;
			w = f->prb_link[1] = y;
			w->prb_link[1]->prb_parent = w;
		    }

		    w->prb_color = f->prb_color;
		    f->prb_color = PRB_BLACK;
		    w->prb_link[1]->prb_color = PRB_BLACK;

		    f->prb_link[1] = w->prb_link[0];
		    w->prb_link[0] = f;
		    g->prb_link[g->prb_link[0] != f] = w;

		    w->prb_parent = f->prb_parent;
		    f->prb_parent = w;
		    if (f->prb_link[1] != NULL)
			f->prb_link[1]->prb_parent = f;
		    break;
		}
	    }
	    else {
		struct prb_node *w = f->prb_link[0];

		if (w->prb_color == PRB_RED) {
		    w->prb_color = PRB_BLACK;
		    f->prb_color = PRB_RED;

		    f->prb_link[0] = w->prb_link[1];
		    w->prb_link[1] = f;
		    g->prb_link[g->prb_link[0] != f] = w;

		    w->prb_parent = f->prb_parent;
		    f->prb_parent = w;

		    g = w;
		    w = f->prb_link[0];

		    w->prb_parent = f;
		}

		if ((w->prb_link[0] == NULL
		     || w->prb_link[0]->prb_color == PRB_BLACK)
		    && (w->prb_link[1] == NULL
			|| w->prb_link[1]->prb_color == PRB_BLACK)) {
		    w->prb_color = PRB_RED;
		}
		else {
		    if (w->prb_link[0] == NULL
			|| w->prb_link[0]->prb_color == PRB_BLACK) {
			struct prb_node *y = w->prb_link[1];

			y->prb_color = PRB_BLACK;
			w->prb_color = PRB_RED;
			w->prb_link[1] = y->prb_link[0];
			y->prb_link[0] = w;
			if (w->prb_link[1] != NULL)
			    w->prb_link[1]->prb_parent = w;
			w = f->prb_link[0] = y;
			w->prb_link[0]->prb_parent = w;
		    }

		    w->prb_color = f->prb_color;
		    f->prb_color = PRB_BLACK;
		    w->prb_link[0]->prb_color = PRB_BLACK;

		    f->prb_link[0] = w->prb_link[1];
		    w->prb_link[1] = f;
		    g->prb_link[g->prb_link[0] != f] = w;

		    w->prb_parent = f->prb_parent;
		    f->prb_parent = w;
		    if (f->prb_link[0] != NULL)
			f->prb_link[0]->prb_parent = f;
		    break;
		}
	    }

	    t = f;
	    f = f->prb_parent;
	    if (f == NULL)
		f = (struct prb_node *)&tree->prb_root;
	    dir = f->prb_link[0] != t;
	}
    }

    tree->prb_alloc->libavl_free(tree->prb_alloc, p);
    tree->prb_count--;

    if (tree->prb_root != NULL)
	tree->prb_root->prb_color = PRB_BLACK;

    return (void *)item;
}

/* Initializes |trav| for use with |tree|
   and selects the null node. */
void prb_t_init(struct prb_traverser *trav, struct prb_table *tree)
{
    trav->prb_table = tree;
    trav->prb_node = NULL;
}

/* Initializes |trav| for |tree|.
   Returns data item in |tree| with the least value,
   or |NULL| if |tree| is empty. */
void *prb_t_first(struct prb_traverser *trav, struct prb_table *tree)
{
    assert(tree != NULL && trav != NULL);

    trav->prb_table = tree;
    trav->prb_node = tree->prb_root;
    if (trav->prb_node != NULL) {
	while (trav->prb_node->prb_link[0] != NULL)
	    trav->prb_node = trav->prb_node->prb_link[0];
	return trav->prb_node->prb_data;
    }
    else
	return NULL;
}

/* Initializes |trav| for |tree|.
   Returns data item in |tree| with the greatest value,
   or |NULL| if |tree| is empty. */
void *prb_t_last(struct prb_traverser *trav, struct prb_table *tree)
{
    assert(tree != NULL && trav != NULL);

    trav->prb_table = tree;
    trav->prb_node = tree->prb_root;
    if (trav->prb_node != NULL) {
	while (trav->prb_node->prb_link[1] != NULL)
	    trav->prb_node = trav->prb_node->prb_link[1];
	return trav->prb_node->prb_data;
    }
    else
	return NULL;
}

/* Searches for |item| in |tree|.
   If found, initializes |trav| to the item found and returns the item
   as well.
   If there is no matching item, initializes |trav| to the null item
   and returns |NULL|. */
void *prb_t_find(struct prb_traverser *trav, struct prb_table *tree,
		 void *item)
{
    struct prb_node *p;

    assert(trav != NULL && tree != NULL && item != NULL);

    trav->prb_table = tree;
    p = tree->prb_root;
    while (p != NULL) {
	int cmp = tree->prb_compare(item, p->prb_data, tree->prb_param);

	if (cmp == 0) {
	    trav->prb_node = p;

	    return p->prb_data;
	}

	p = p->prb_link[cmp > 0];
    }

    trav->prb_node = NULL;

    return NULL;
}

/* Attempts to insert |item| into |tree|.
   If |item| is inserted successfully, it is returned and |trav| is
   initialized to its location.
   If a duplicate is found, it is returned and |trav| is initialized to
   its location.  No replacement of the item occurs.
   If a memory allocation failure occurs, |NULL| is returned and |trav|
   is initialized to the null item. */
void *prb_t_insert(struct prb_traverser *trav,
		   struct prb_table *tree, void *item)
{
    void **p;

    assert(trav != NULL && tree != NULL && item != NULL);

    p = prb_probe(tree, item);
    if (p != NULL) {
	trav->prb_table = tree;
	trav->prb_node = ((struct prb_node *)
			  ((char *)p - offsetof(struct prb_node, prb_data)));

	return *p;
    }
    else {
	prb_t_init(trav, tree);
	return NULL;
    }
}

/* Initializes |trav| to have the same current node as |src|. */
void *prb_t_copy(struct prb_traverser *trav, const struct prb_traverser *src)
{
    assert(trav != NULL && src != NULL);

    trav->prb_table = src->prb_table;
    trav->prb_node = src->prb_node;

    return trav->prb_node != NULL ? trav->prb_node->prb_data : NULL;
}

/* Returns the next data item in inorder
   within the tree being traversed with |trav|,
   or if there are no more data items returns |NULL|. */
void *prb_t_next(struct prb_traverser *trav)
{
    assert(trav != NULL);

    if (trav->prb_node == NULL)
	return prb_t_first(trav, trav->prb_table);
    else if (trav->prb_node->prb_link[1] == NULL) {
	struct prb_node *q, *p;	/* Current node and its child. */

	for (p = trav->prb_node, q = p->prb_parent;; p = q, q = q->prb_parent)
	    if (q == NULL || p == q->prb_link[0]) {
		trav->prb_node = q;
		return trav->prb_node !=
		    NULL ? trav->prb_node->prb_data : NULL;
	    }
    }
    else {
	trav->prb_node = trav->prb_node->prb_link[1];
	while (trav->prb_node->prb_link[0] != NULL)
	    trav->prb_node = trav->prb_node->prb_link[0];
	return trav->prb_node->prb_data;
    }
}

/* Returns the previous data item in inorder
   within the tree being traversed with |trav|,
   or if there are no more data items returns |NULL|. */
void *prb_t_prev(struct prb_traverser *trav)
{
    assert(trav != NULL);

    if (trav->prb_node == NULL)
	return prb_t_last(trav, trav->prb_table);
    else if (trav->prb_node->prb_link[0] == NULL) {
	struct prb_node *q, *p;	/* Current node and its child. */

	for (p = trav->prb_node, q = p->prb_parent;; p = q, q = q->prb_parent)
	    if (q == NULL || p == q->prb_link[1]) {
		trav->prb_node = q;
		return trav->prb_node !=
		    NULL ? trav->prb_node->prb_data : NULL;
	    }
    }
    else {
	trav->prb_node = trav->prb_node->prb_link[0];
	while (trav->prb_node->prb_link[1] != NULL)
	    trav->prb_node = trav->prb_node->prb_link[1];
	return trav->prb_node->prb_data;
    }
}

/* Returns |trav|'s current item. */
void *prb_t_cur(struct prb_traverser *trav)
{
    assert(trav != NULL);

    return trav->prb_node != NULL ? trav->prb_node->prb_data : NULL;
}

/* Replaces the current item in |trav| by |new| and returns the item replaced.
   |trav| must not have the null item selected.
   The new item must not upset the ordering of the tree. */
void *prb_t_replace(struct prb_traverser *trav, void *new)
{
    void *old;

    assert(trav != NULL && trav->prb_node != NULL && new != NULL);
    old = trav->prb_node->prb_data;
    trav->prb_node->prb_data = new;
    return old;
}

/* Destroys |new| with |prb_destroy (new, destroy)|,
   first initializing right links in |new| that have
   not yet been initialized at time of call. */
static void
copy_error_recovery(struct prb_node *q,
		    struct prb_table *new, prb_item_func * destroy)
{
    assert(q != NULL && new != NULL);

    for (;;) {
	struct prb_node *p = q;

	q = q->prb_parent;
	if (q == NULL)
	    break;

	if (p == q->prb_link[0])
	    q->prb_link[1] = NULL;
    }

    prb_destroy(new, destroy);
}

/* Copies |org| to a newly created tree, which is returned.
   If |copy != NULL|, each data item in |org| is first passed to |copy|,
   and the return values are inserted into the tree;
   |NULL| return values are taken as indications of failure.
   On failure, destroys the partially created new tree,
   applying |destroy|, if non-null, to each item in the new tree so far,
   and returns |NULL|.
   If |allocator != NULL|, it is used for allocation in the new tree.
   Otherwise, the same allocator used for |org| is used. */
struct prb_table *prb_copy(const struct prb_table *org, prb_copy_func * copy,
			   prb_item_func * destroy,
			   struct libavl_allocator *allocator)
{
    struct prb_table *new;
    const struct prb_node *x;
    struct prb_node *y;

    assert(org != NULL);
    new = prb_create(org->prb_compare, org->prb_param,
		     allocator != NULL ? allocator : org->prb_alloc);
    if (new == NULL)
	return NULL;
    new->prb_count = org->prb_count;
    if (new->prb_count == 0)
	return new;

    x = (const struct prb_node *)&org->prb_root;
    y = (struct prb_node *)&new->prb_root;
    while (x != NULL) {
	while (x->prb_link[0] != NULL) {
	    y->prb_link[0] =
		new->prb_alloc->libavl_malloc(new->prb_alloc,
					      sizeof *y->prb_link[0]);
	    if (y->prb_link[0] == NULL) {
		if (y != (struct prb_node *)&new->prb_root) {
		    y->prb_data = NULL;
		    y->prb_link[1] = NULL;
		}

		copy_error_recovery(y, new, destroy);
		return NULL;
	    }
	    y->prb_link[0]->prb_parent = y;

	    x = x->prb_link[0];
	    y = y->prb_link[0];
	}
	y->prb_link[0] = NULL;

	for (;;) {
	    y->prb_color = x->prb_color;
	    if (copy == NULL)
		y->prb_data = x->prb_data;
	    else {
		y->prb_data = copy(x->prb_data, org->prb_param);
		if (y->prb_data == NULL) {
		    y->prb_link[1] = NULL;
		    copy_error_recovery(y, new, destroy);
		    return NULL;
		}
	    }

	    if (x->prb_link[1] != NULL) {
		y->prb_link[1] =
		    new->prb_alloc->libavl_malloc(new->prb_alloc,
						  sizeof *y->prb_link[1]);
		if (y->prb_link[1] == NULL) {
		    copy_error_recovery(y, new, destroy);
		    return NULL;
		}
		y->prb_link[1]->prb_parent = y;

		x = x->prb_link[1];
		y = y->prb_link[1];
		break;
	    }
	    else
		y->prb_link[1] = NULL;

	    for (;;) {
		const struct prb_node *w = x;

		x = x->prb_parent;
		if (x == NULL) {
		    new->prb_root->prb_parent = NULL;
		    return new;
		}
		y = y->prb_parent;

		if (w == x->prb_link[0])
		    break;
	    }
	}
    }

    return new;
}

/* Frees storage allocated for |tree|.
   If |destroy != NULL|, applies it to each data item in inorder. */
void prb_destroy(struct prb_table *tree, prb_item_func * destroy)
{
    struct prb_node *p, *q;

    assert(tree != NULL);

    p = tree->prb_root;
    while (p != NULL) {
	if (p->prb_link[0] == NULL) {
	    q = p->prb_link[1];
	    if (destroy != NULL && p->prb_data != NULL)
		destroy(p->prb_data, tree->prb_param);
	    tree->prb_alloc->libavl_free(tree->prb_alloc, p);
	}
	else {
	    q = p->prb_link[0];
	    p->prb_link[0] = q->prb_link[1];
	    q->prb_link[1] = p;
	}
	p = q;
    }

    tree->prb_alloc->libavl_free(tree->prb_alloc, tree);
}

/* Allocates |size| bytes of space using |malloc()|.
   Returns a null pointer if allocation fails. */
void *prb_malloc(struct libavl_allocator *allocator, size_t size)
{
    assert(allocator != NULL && size > 0);

    return malloc(size);
}

/* Frees |block|. */
void prb_free(struct libavl_allocator *allocator, void *block)
{
    assert(allocator != NULL && block != NULL);
    free(block);
}

/* Default memory allocator that uses |malloc()| and |free()|. */
struct libavl_allocator prb_allocator_default = {
    prb_malloc,
    prb_free
};

#undef NDEBUG
#include <assert.h>

/* Asserts that |prb_insert()| succeeds at inserting |item| into |table|. */
void (prb_assert_insert) (struct prb_table * table, void *item)
{
    void **p = prb_probe(table, item);

    assert(p != NULL && *p == item);
}

/* Asserts that |prb_delete()| really removes |item| from |table|,
   and returns the removed item. */
void *(prb_assert_delete) (struct prb_table * table, void *item)
{
    void *p = prb_delete(table, item);

    assert(p != NULL);

    return p;
}
