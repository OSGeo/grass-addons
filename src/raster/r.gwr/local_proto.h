#include <grass/segment.h>
#include "flag.h"
#include "bufs.h"

void set_wfn(char *name, int vfu);

extern double (*w_fn)(double, double);

double **calc_weights(int bw);

int gwr(struct rb *xbuf, int ninx, struct rb *ybuf, int cc, int bw, double **w,
        DCELL *est, double **B0);

int gwra(SEGMENT *in_seg, FLAG *yflag, int ninx, int rr, int cc, int npnts,
         DCELL *est, double **B0);

int estimate_bandwidth(int *inx, int ninx, int iny, int nrows, int ncols,
                       DCELL *est, int bw);
