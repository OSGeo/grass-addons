#define MAX_DOUBLE 1000000.0

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

typedef struct
{
    int x, y;
    int neighbors;
    double value;
} Coords;

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
