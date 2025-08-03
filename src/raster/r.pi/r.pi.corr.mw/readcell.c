#include <unistd.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include "ncb.h"
#include "local_proto.h"

int readcell(int fd, int bufnumber, int row, int nrows, int ncols)
{
    if (bufnumber < 1 || bufnumber > 2)
        return -1;

    if (bufnumber == 1)
        rotate_bufs(1);
    else
        rotate_bufs(2);

    if (row < nrows)
        if (bufnumber == 1)
            Rast_get_d_row(fd, ncb.buf1[ncb.nsize - 1] + ncb.dist, row);
        else
            Rast_get_d_row(fd, ncb.buf2[ncb.nsize - 1] + ncb.dist, row);
    else if (bufnumber == 1)
        Rast_set_d_null_value(ncb.buf1[ncb.nsize - 1] + ncb.dist, ncols);
    else
        Rast_set_d_null_value(ncb.buf2[ncb.nsize - 1] + ncb.dist, ncols);

    return 0;
}
