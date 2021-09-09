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

#ifndef PRB_H
#define PRB_H 1

#include <stddef.h>

/* Function types. */
typedef int prb_comparison_func(const void *prb_a, const void *prb_b,
				void *prb_param);
typedef void prb_item_func(void *prb_item, void *prb_param);
typedef void *prb_copy_func(void *prb_item, void *prb_param);

#ifndef LIBAVL_ALLOCATOR
#define LIBAVL_ALLOCATOR
/* Memory allocator. */
struct libavl_allocator
{
    void *(*libavl_malloc) (struct libavl_allocator *, size_t libavl_size);
    void (*libavl_free) (struct libavl_allocator *, void *libavl_block);
};
#endif

/* Default memory allocator. */
extern struct libavl_allocator prb_allocator_default;
void *prb_malloc(struct libavl_allocator *, size_t);
void prb_free(struct libavl_allocator *, void *);

/* Maximum PRB height. */
#ifndef PRB_MAX_HEIGHT
#define PRB_MAX_HEIGHT 128
#endif

/* Tree data structure. */
struct prb_table
{
    struct prb_node *prb_root;	/* Tree's root. */
    prb_comparison_func *prb_compare;	/* Comparison function. */
    void *prb_param;		/* Extra argument to |prb_compare|. */
    struct libavl_allocator *prb_alloc;	/* Memory allocator. */
    size_t prb_count;		/* Number of items in tree. */
};

/* Color of a red-black node. */
enum prb_color
{
    PRB_BLACK,			/* Black. */
    PRB_RED			/* Red. */
};

/* A red-black tree with parent pointers node. */
struct prb_node
{
    struct prb_node *prb_link[2];	/* Subtrees. */
    struct prb_node *prb_parent;	/* Parent. */
    void *prb_data;		/* Pointer to data. */
    unsigned char prb_color;	/* Color. */
};

/* PRB traverser structure. */
struct prb_traverser
{
    struct prb_table *prb_table;	/* Tree being traversed. */
    struct prb_node *prb_node;	/* Current node in tree. */
};

/* Table functions. */
struct prb_table *prb_create(prb_comparison_func *, void *,
			     struct libavl_allocator *);
struct prb_table *prb_copy(const struct prb_table *, prb_copy_func *,
			   prb_item_func *, struct libavl_allocator *);
void prb_destroy(struct prb_table *, prb_item_func *);
void **prb_probe(struct prb_table *, void *);
void *prb_insert(struct prb_table *, void *);
void *prb_replace(struct prb_table *, void *);
void *prb_delete(struct prb_table *, const void *);
void *prb_delete_first(struct prb_table *);
void *prb_find(const struct prb_table *, const void *);
void prb_assert_insert(struct prb_table *, void *);
void *prb_assert_delete(struct prb_table *, void *);

#define prb_count(table) ((size_t) (table)->prb_count)

/* Table traverser functions. */
void prb_t_init(struct prb_traverser *, struct prb_table *);
void *prb_t_first(struct prb_traverser *, struct prb_table *);
void *prb_t_last(struct prb_traverser *, struct prb_table *);
void *prb_t_find(struct prb_traverser *, struct prb_table *, void *);
void *prb_t_insert(struct prb_traverser *, struct prb_table *, void *);
void *prb_t_copy(struct prb_traverser *, const struct prb_traverser *);
void *prb_t_next(struct prb_traverser *);
void *prb_t_prev(struct prb_traverser *);
void *prb_t_cur(struct prb_traverser *);
void *prb_t_replace(struct prb_traverser *, void *);

#endif /* prb.h */
