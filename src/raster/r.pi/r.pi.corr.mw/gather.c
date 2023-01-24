#include <grass/gis.h>
#include <grass/raster.h>
#include "ncb.h"

/*
   given the starting col of the neighborhood,
   copy the cell values from the bufs into the array of values
   and return the number of values copied.
 */

int gather(DCELL *values, int bufnumber, int offset)
{
    int row, col;
    int n = 0;

    if (bufnumber < 1 || bufnumber > 2)
        return -1;

    *values = 0;

    for (row = 0; row < ncb.nsize; row++)
        for (col = 0; col < ncb.nsize; col++) {
            DCELL *c;

            if (bufnumber == 1)
                c = &ncb.buf1[row][offset + col];
            else
                c = &ncb.buf2[row][offset + col];

            if (Rast_is_d_null_value(c))
                Rast_set_d_null_value(&values[n], 1);
            else
                values[n] = *c;

            n++;
        }

    return n ? n : -1;
}
