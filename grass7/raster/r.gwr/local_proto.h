#include "bufs.h"

extern double ** (*w_fn) (int);

void set_wfn(char *name, int vfu);

int gwr(struct rb *xbuf, int ninx, struct rb *ybuf, int cc,
        int bw, double **w, DCELL *est, double **B0);

int estimate_bandwidth(int *inx, int ninx, int iny, int nrows, int ncols,
         DCELL *est, int bw);
