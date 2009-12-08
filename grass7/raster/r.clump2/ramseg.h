#ifndef __RAMSEG_H__
#define __RAMSEG_H__


#define RAMSEG		int
#define RAMSEGBITS 	4
#define DOUBLEBITS 	8	/* 2 * ramsegbits       */
#define SEGLENLESS 	15	/* 2 ^ ramsegbits - 1   */

#define SEG_INDEX(s,r,c) (int) \
   (((((r) >> RAMSEGBITS) * (s) + ((c) >> RAMSEGBITS)) << DOUBLEBITS) \
    + (((r) & SEGLENLESS) << RAMSEGBITS) + ((c) & SEGLENLESS))

int size_array(int *, int, int);
int seg_index_rc(int, int, int *, int *);

#endif /* __RAMSEG_H__ */
