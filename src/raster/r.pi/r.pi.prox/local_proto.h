#include "../r.pi.library/r_pi.h"

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

/* frag.c */
void writeFrag(int row, int col, int nbr_cnt);

/* func.c */
int f_proximity(DCELL *, Coords **, int, int, int);
int f_modified_prox(DCELL * vals, Coords ** frags, int count, int min,
		    int max);
int f_neighborhood(DCELL *, Coords **, int, int, int);

/* global variables */
GLOBAL int nrows, ncols;
GLOBAL Coords **fragments;
GLOBAL int *flagbuf;
GLOBAL Coords *actpos;
GLOBAL int cnt;
