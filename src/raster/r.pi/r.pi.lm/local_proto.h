#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/stats.h>
#include "../r.pi.library/r_pi.h"
#include <math.h>

void clearPatch(DCELL *map, int *flagbuf, int flagval, int row, int col,
                int nrows, int ncols, int nbr_cnt);

void linear_regression(DCELL *x, DCELL *y, int count, DCELL *res_offset,
                       DCELL *res_slope, DCELL *res_residuals,
                       DCELL *res_correlation);

#endif /* LOCAL_PROTO_H */
