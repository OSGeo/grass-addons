#include <stdio.h>
#include "ramseg.h"

long size_array(long *ramseg, int nrows, int ncols)
{
    *ramseg = (long)ncols;
    
    return ((long) nrows * ncols);
}

/* get r, c from seg_index */
long seg_index_rc(long ramseg, long seg_index, int *r, int *c)
{
    *r = seg_index / ramseg;
    *c = seg_index - *r * ramseg;
    
    return 0;
}
