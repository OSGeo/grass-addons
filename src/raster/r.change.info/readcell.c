#include <unistd.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include "ncb.h"
#include "local_proto.h"

int readcell(int row, int nrows, int ncols)
{
    int i;

    rotate_bufs();

    if (row < nrows) {
        for (i = 0; i < ncb.nin; i++)
            Rast_get_c_row(ncb.in[i].fd, ncb.in[i].buf[ncb.nsize - 1], row);
    }
    else {
        for (i = 0; i < ncb.nin; i++)
            Rast_set_c_null_value(ncb.in[i].buf[ncb.nsize - 1], ncols);
    }

    return 0;
}
