#include <stdio.h>
#include "ramseg.h"

#ifdef LARGE_MAPS

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

#else

long size_array(long *ramseg, int nrows, int ncols)
{
    long size, segs_in_col;

    segs_in_col = ((nrows - 1) >> RAMSEGBITS) + 1;
    *ramseg = ((ncols - 1) >> RAMSEGBITS) + 1;
    size = ((((nrows - 1) >> RAMSEGBITS) + 1) << RAMSEGBITS) *
	((((ncols - 1) >> RAMSEGBITS) + 1) << RAMSEGBITS);
    size -= ((segs_in_col << RAMSEGBITS) - nrows) << RAMSEGBITS;
    size -= (*ram_seg << RAMSEGBITS) - ncols;
    return (size);
}

/* get r, c from seg_index */
long seg_index_rc(long ramseg, long seg_index, int *r, int *c)
{
    long seg_no, seg_remainder;

    seg_no = seg_index >> DOUBLEBITS;
    seg_remainder = seg_index - (seg_no << DOUBLEBITS);
    *r = ((seg_no / ramseg) << RAMSEGBITS) + (seg_remainder >> RAMSEGBITS);
    *c = ((seg_no - ((*r) >> RAMSEGBITS) * ramseg) << RAMSEGBITS) +
	seg_remainder - (((*r) & SEGLENLESS) << RAMSEGBITS);
    return seg_no;
}

#endif
