#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H

#include "../r.pi.library/r_pi.h"

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

extern int f_area(DCELL *vals, Coords **frags, int);
extern int f_perim(DCELL *vals, Coords **frags, int);
extern int f_shapeindex(DCELL *, Coords **, int);
extern int f_borderindex(DCELL *, Coords **, int);
extern int f_compactness(DCELL *, Coords **, int);
extern int f_asymmetry(DCELL *, Coords **, int);
extern int f_area_perim_ratio(DCELL *, Coords **, int);
extern int f_frac_dim(DCELL *, Coords **, int);
extern int f_nearest_dist(DCELL *, Coords **, int);

/* global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *actpos;

#endif /* LOCAL_PROTO_H */
