#include <grass/gis.h>
#include <grass/raster.h>
#include "bufs.h"

/*
   allocate the i/o bufs

   the i/o bufs will be rotated by the read operation so that the
   last row read will be in the last i/o buf

 */

int allocate_bufs(struct rb *rbuf, int ncols, int bw, int fd)
{
    int i;
    int ncolsbw;
    size_t bufsize;

    ncolsbw = ncols + 2 * bw;
    bufsize = ncolsbw * sizeof(DCELL);

    rbuf->bw = bw;
    rbuf->nsize = bw * 2 + 1;
    rbuf->fd = fd;
    rbuf->row = 0;

    rbuf->buf = (DCELL **)G_malloc(rbuf->nsize * sizeof(DCELL *));

    for (i = 0; i < rbuf->nsize; i++) {
        rbuf->buf[i] = (DCELL *)G_malloc(bufsize);
        Rast_set_d_null_value(rbuf->buf[i], ncolsbw);
    }

    return 0;
}

int release_bufs(struct rb *rbuf)
{
    int i;

    for (i = 0; i < rbuf->nsize; i++) {
        G_free(rbuf->buf[i]);
    }

    G_free(rbuf->buf);

    rbuf->bw = 0;
    rbuf->nsize = 0;
    rbuf->row = 0;

    return 0;
}

static int rotate_bufs(struct rb *rbuf)
{
    DCELL *temp;
    int i;

    temp = rbuf->buf[0];

    for (i = 1; i < rbuf->nsize; i++)
        rbuf->buf[i - 1] = rbuf->buf[i];

    rbuf->buf[rbuf->nsize - 1] = temp;

    return 0;
}

int readrast(struct rb *rbuf, int nrows, int ncols)
{
    rotate_bufs(rbuf);

    if (rbuf->row < nrows) {
        Rast_get_d_row(rbuf->fd, rbuf->buf[rbuf->nsize - 1] + rbuf->bw,
                       rbuf->row);
    }
    else {
        Rast_set_d_null_value(rbuf->buf[rbuf->nsize - 1] + rbuf->bw, ncols);
    }

    rbuf->row++;

    return 0;
}
