#include <string.h>
#include <grass/segment.h>
#include <grass/glocale.h>
#include "cache.h"

static void *cache_get_r(struct cache *c, void *p, int row, int col)
{
    return memcpy(p, c->r + ((size_t)row * c->cols + col) * c->n, c->n);
}

static void *cache_put_r(struct cache *c, void *p, int row, int col)
{
    return memcpy(c->r + ((size_t)row * c->cols + col) * c->n, p, c->n);
}

static void *cache_get_s(struct cache *c, void *p, int row, int col)
{
    Segment_get(&c->s, p, row, col);

    return p;
}

static void *cache_put_s(struct cache *c, void *p, int row, int col)
{
    if (Segment_put(&c->s, p, row, col) != 1)
        G_fatal_error(_("Unable to write to temporary file"));

    return p;
}

int cache_create(struct cache *c, int nrows, int ncols, int srows, int scols,
                 int nbytes, int nseg)
{
    int nseg_total;

    c->n = nbytes;
    c->rows = nrows;
    c->cols = ncols;

    nseg_total = ((nrows + srows - 1) / srows) * ((ncols + scols - 1) / scols);

    if (nseg < nseg_total) {
        G_verbose_message("Using disk cache");

        if (Segment_open(&c->s, G_tempfile(), nrows, ncols, srows, scols,
                         nbytes, nseg) != 1)
            G_fatal_error("Unable to create temporary file");

        c->r = NULL;
        c->get = cache_get_s;
        c->put = cache_put_s;
    }
    else {
        G_verbose_message("Using memory cache");

        c->r = G_malloc(sizeof(char) * c->rows * c->cols * c->n);
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
