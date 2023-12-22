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
    int i, j;
    int ncols;
    size_t bufsize;

    ncols = Rast_input_window_cols();
    bufsize = ncols * sizeof(CELL);

    for (i = 0; i < ncb.nin; i++) {
        ncb.in[i].buf = (CELL **)G_malloc(ncb.nsize * sizeof(CELL *));
        for (j = 0; j < ncb.nsize; j++) {
            ncb.in[i].buf[j] = (CELL *)G_malloc(bufsize);
            Rast_set_c_null_value(ncb.in[i].buf[j], ncols);
        }
    }

    return 0;
}

int rotate_bufs(void)
{
    CELL *temp;
    int i, j;

    for (i = 0; i < ncb.nin; i++) {
        temp = ncb.in[i].buf[0];

        for (j = 1; j < ncb.nsize; j++)
            ncb.in[i].buf[j - 1] = ncb.in[i].buf[j];

        ncb.in[i].buf[ncb.nsize - 1] = temp;
    }

    return 0;
}
