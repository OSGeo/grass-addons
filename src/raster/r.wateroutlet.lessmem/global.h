#define BITSIZE (((nrows * ncols) >> 3) + ((nrows * ncols) & 7 ? 1 : 0))
#define SETBIT(b, r, c)                                                 \
    b[((r)*ncols + (c)) >> 3] =                                         \
        (b[((r)*ncols + (c)) >> 3] & ~(1 << (((r)*ncols + (c)) & 7))) | \
        (1 << (((r)*ncols + (c)) & 7))
#define CLEARBIT(b, r, c)       \
    b[((r)*ncols + (c)) >> 3] = \
        b[((r)*ncols + (c)) >> 3] & ~(1 << (((r)*ncols + (c)) & 7))
#define GETBIT(b, r, c)                                              \
    ((b[((r)*ncols + (c)) >> 3] & (1 << (((r)*ncols + (c)) & 7))) >> \
     (((r)*ncols + (c)) & 7))

#define DIRSIZE (((nrows * ncols) >> 1) + ((nrows * ncols) & 1 ? 1 : 0))
#define SETDIR(b, r, c, d)                                                   \
    b[((r)*ncols + (c)) >> 1] = (b[((r)*ncols + (c)) >> 1] &                 \
                                 ~(15 << (((r)*ncols + (c)) & 1 ? 4 : 0))) | \
                                ((d) << (((r)*ncols + (c)) & 1 ? 4 : 0))
#define GETDIR(b, r, c)                                                       \
    ((b[((r)*ncols + (c)) >> 1] & (15 << (((r)*ncols + (c)) & 1 ? 4 : 0))) >> \
     (((r)*ncols + (c)) & 1 ? 4 : 0))

/* over_cells.c */
int overland_cells(int, int);

#ifdef _MAIN_C_
#define GLOBAL
#else
#define GLOBAL extern
#endif

GLOBAL int nrows, ncols;
GLOBAL char *drain_ptrs;
GLOBAL char *bas;
