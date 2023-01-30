#include <grass/gis.h>
#include <grass/raster.h>
#include "ncb.h"

/*
   allocate the i/o bufs

   the i/o bufs will be rotated by the read operation so that the
   last row read will be in the last i/o buf

 */

int allocate_bufs(void)
{
    int i;
    int bufsize;

    bufsize = (Rast_window_cols() + 2 * ncb.nsize) * sizeof(DCELL);

    ncb.buf1 = (DCELL **)G_malloc(ncb.nsize * sizeof(DCELL *));
    ncb.buf2 = (DCELL **)G_malloc(ncb.nsize * sizeof(DCELL *));
    for (i = 0; i < ncb.nsize; i++) {
        ncb.buf1[i] = (DCELL *)G_malloc(bufsize);
        ncb.buf2[i] = (DCELL *)G_malloc(bufsize);
        Rast_set_d_null_value(ncb.buf1[i], Rast_window_cols() + 2 * ncb.nsize);
        Rast_set_d_null_value(ncb.buf2[i], Rast_window_cols() + 2 * ncb.nsize);
    }

    return 0;
}

int rotate_bufs(int bufnumber)
{
    DCELL *temp;
    int i;

    if (bufnumber < 1 || bufnumber > 2)
        return -1;

    if (bufnumber == 1) {
        temp = ncb.buf1[0];

        for (i = 1; i < ncb.nsize; i++) {
            ncb.buf1[i - 1] = ncb.buf1[i];
        }

        ncb.buf1[ncb.nsize - 1] = temp;
    }
    else {
        temp = ncb.buf2[0];

        for (i = 1; i < ncb.nsize; i++) {
            ncb.buf2[i - 1] = ncb.buf2[i];
        }

        ncb.buf2[ncb.nsize - 1] = temp;
    }

    return 0;
}
