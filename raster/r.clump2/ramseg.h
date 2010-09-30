#ifndef __RAMSEG_H__
#define __RAMSEG_H__


#define RAMSEG		long
#define RAMSEGBITS 	4
#define DOUBLEBITS 	8	/* 2 * ramsegbits       */
#define SEGLENLESS 	15	/* 2 ^ ramsegbits - 1   */

#define SEG_INDEX(s,r,c) (long) ((r) * (s) + (c))

long size_array(long *, int, int);
long seg_index_rc(long, long, int *, int *);

#endif /* __RAMSEG_H__ */
