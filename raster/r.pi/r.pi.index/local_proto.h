#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

#define MAX_DOUBLE 1000000.0

typedef struct
{
    int x, y;
    int neighbors;
} Coords;

extern void writeFrag(int row, int col, int nbr_cnt);

extern int f_area(DCELL * vals, Coords ** frags, int);

extern int f_perim(DCELL * vals, Coords ** frags, int);

extern int f_shapeindex(DCELL *, Coords **, int);

extern int f_borderindex(DCELL *, Coords **, int);

extern int f_compactness(DCELL *, Coords **, int);

extern int f_asymmetry(DCELL *, Coords **, int);

extern int f_area_perim_ratio(DCELL *, Coords **, int);

extern int f_frac_dim(DCELL *, Coords **, int);

extern int f_nearest_dist(DCELL *, Coords **, int);

/* global variables */
GLOBAL int nrows, ncols;
GLOBAL Coords **fragments;
GLOBAL int *flagbuf;

GLOBAL Coords *actpos;
GLOBAL int verbose;

#endif /* LOCAL_PROTO_H */
