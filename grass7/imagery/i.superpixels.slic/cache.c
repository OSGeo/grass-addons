#include <string.h>
#include <grass/raster.h>
#include <grass/segment.h>
#include <grass/glocale.h>
#include "cache.h"

static void *cache_get_r(struct cache *c, void *p, int row, int col)
{
    return memcpy(p, c->r[row][col], c->n);
}

static void *cache_put_r(struct cache *c, void *p, int row, int col)
{
    return memcpy(c->r[row][col], p, c->n);
}

static void *cache_get_s(struct cache *c, void *p, int row, int col)
{
    Segment_get(&c->s, p, row, col);

    return  p;
}

static void *cache_put_s(struct cache *c, void *p, int row, int col)
{
    if (Segment_put(&c->s, p, row, col) != 1)
	G_fatal_error(_("Unable to write to temporary file"));

    return p;
}

int cache_create(struct cache *c, int nrows, int ncols, int seg_size,
                 int use_seg, int nbytes, int nseg)
{
    c->n = nbytes;
    c->rows = nrows;
    c->cols = ncols;

    if (use_seg) {
	if (Segment_open(&c->s, G_tempfile(), nrows, ncols, seg_size, seg_size,
			 nbytes, nseg) != 1)
	    G_fatal_error("Unable to create temporary file");

	c->r = NULL;
	c->get = cache_get_s;
	c->put = cache_put_s;
    }
    else {
	int row, col;

	c->r = G_malloc(sizeof(char **) * c->rows);
	for (row = 0; row < c->rows; row++) {
	    c->r[row] = G_malloc(sizeof(char *) * c->cols);
	    c->r[row][0] = G_malloc(sizeof(char) * c->cols * c->n);
	    for (col = 1; col < c->cols; col++) {
		c->r[row][col] = c->r[row][col - 1] + c->n;
	    }
	}

	c->get = cache_get_r;
	c->put = cache_put_r;
    }

    return 1;
}

int cache_destroy(struct cache *c)
{
    if (c->r == NULL) {
	Segment_close(&c->s);
    }
    else {
	int row;

	for (row = 0; row < c->rows; row++) {
	    G_free(c->r[row][0]);
	    G_free(c->r[row]);
	}
	G_free(c->r);
    }

    return 1;
}

void *cache_get(struct cache *c, void *p, int row, int col)
{
    return c->get(c, p, row, col);
}

void *cache_put(struct cache *c, void *p, int row, int col)
{
    return c->put(c, p, row, col);
}
