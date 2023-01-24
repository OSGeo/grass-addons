#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <math.h>
#include <string.h>
#include <sys/types.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>
#include "local_proto.h"

#ifndef USE_RAND

#ifndef HAVE_DRAND48
#define lrand48()   (((long)rand() ^ ((long)rand() << 16)) & 0x7FFFFFFF)
#define srand48(sv) (srand((unsigned)(sv)))
#endif

long make_rand(void)
{
    return lrand48();
}

void init_rand(void)
{
    srand48((long)time((time_t *)0));
}

#else

static long labs(int n)
{
    return n < 0 ? (-n) : n;
}

long make_rand(void)
{
    return (labs(rand() + (rand() << 16)));
}

void init_rand(void)
{
    srand(getpid());
}

#endif

/* estimate bandwidth
 * start with a small bandwidth */

int estimate_bandwidth(int *inx, int ninx, int iny, int nrows, int ncols,
                       DCELL *est, int bw)
{
    int i;
    int r, c;
    struct rb *xbuf1, *xbuf2, *xbuf3, ybuf1, ybuf2, ybuf3;
    int prevbw, nextbw, newbw, lastbw, bestbw, bwhi;
    int bwmin, bwmax;
    int n1, n2, n3;
    double f11, f12, f2;
    double ss1, ss2, ss3, ssmin;
    double **w1, **w2, **w3;
    DCELL *ybuf, yval;
    DCELL est1, est2, est3;
    int nr, nc, nrt, nct, count, gwrfailed, step, havemin;

    ybuf = Rast_allocate_d_buf();

    G_message(_("Estimating optimal bandwidth..."));

    /* count non-NULL cells of the dependent variable */
    nc = 0;
    for (r = 0; r < nrows; r++) {

        Rast_get_d_row(iny, ybuf, r);

        for (c = 0; c < ncols; c++) {
            yval = ybuf[c];

            if (!Rast_is_d_null_value(&yval))
                nc++;
        }
    }
    if (nc == 0)
        G_fatal_error(_("No non-NULL cells in input map"));

    /* number of cells to use for bandwidth estimation */
    nr = 10000;
    if (nr > nc)
        nr = nc;

    if (bw < 2) {
        G_warning(_("Initial bandwidth must be > 1"));
        bw = 2;
    }

    bwmin = 1;
    bwmax = sqrt((double)nrows * nrows + (double)ncols * ncols);

    init_rand();

    xbuf1 = G_malloc(ninx * sizeof(struct rb));
    xbuf2 = G_malloc(ninx * sizeof(struct rb));
    xbuf3 = G_malloc(ninx * sizeof(struct rb));

    lastbw = bestbw = bw;
    ssmin = 1.0 / 0.0;
    bwhi = 0;
    step = 2;
    havemin = 0;
    while (1) {

        if (bw > bwmax)
            break;

        if (bwhi < bw)
            bwhi = bw;

        prevbw = bw - step;
        nextbw = bw + step;

        G_message(_("Testing bandwidth %d"), bw);

        for (i = 0; i < ninx; i++) {
            allocate_bufs(&(xbuf1[i]), ncols, prevbw, inx[i]);
            allocate_bufs(&(xbuf2[i]), ncols, bw, inx[i]);
            allocate_bufs(&(xbuf3[i]), ncols, nextbw, inx[i]);
        }
        allocate_bufs(&ybuf1, ncols, prevbw, iny);
        allocate_bufs(&ybuf2, ncols, bw, iny);
        allocate_bufs(&ybuf3, ncols, nextbw, iny);

        /* initialize the raster buffers with 'bw' rows */
        for (r = 0; r < prevbw; r++) {
            for (i = 0; i < ninx; i++)
                readrast(&(xbuf1[i]), nrows, ncols);
            readrast(&ybuf1, nrows, ncols);
        }
        for (r = 0; r < bw; r++) {
            for (i = 0; i < ninx; i++)
                readrast(&(xbuf2[i]), nrows, ncols);
            readrast(&ybuf2, nrows, ncols);
        }
        for (r = 0; r < nextbw; r++) {
            for (i = 0; i < ninx; i++)
                readrast(&(xbuf3[i]), nrows, ncols);
            readrast(&ybuf3, nrows, ncols);
        }

        w1 = calc_weights(prevbw);
        w2 = calc_weights(bw);
        w3 = calc_weights(nextbw);
        /* leave one out: the center cell */
        w1[prevbw][prevbw] = 0.;
        w2[bw][bw] = 0.;
        w3[nextbw][nextbw] = 0.;

        ss1 = ss2 = ss3 = 0;
        n1 = n2 = n3 = 0;

        nrt = nr;
        nct = nc;
        count = 0;

        for (r = 0; r < nrows; r++) {
            G_percent(r, nrows, 4);

            for (i = 0; i < ninx; i++) {
                readrast(&(xbuf1[i]), nrows, ncols);
                readrast(&(xbuf2[i]), nrows, ncols);
                readrast(&(xbuf3[i]), nrows, ncols);
            }
            readrast(&ybuf1, nrows, ncols);
            readrast(&ybuf2, nrows, ncols);
            readrast(&ybuf3, nrows, ncols);

            for (c = 0; c < ncols; c++) {
                yval = ybuf2.buf[bw][c + bw];

                if (Rast_is_d_null_value(&yval))
                    continue;

                gwrfailed = 0;

                if (make_rand() % nct < nrt) {

                    if (gwr(xbuf1, ninx, &ybuf1, c, prevbw, w1, est, NULL)) {
                        est1 = est[0];
                    }
                    else {
                        gwrfailed = 1;
                    }
                    if (gwr(xbuf2, ninx, &ybuf2, c, bw, w2, est, NULL)) {
                        est2 = est[0];
                    }
                    else {
                        gwrfailed = 1;
                    }
                    if (gwr(xbuf3, ninx, &ybuf3, c, nextbw, w3, est, NULL)) {
                        est3 = est[0];
                    }
                    else {
                        gwrfailed = 1;
                    }
                    if (!gwrfailed) {
                        ss1 += (est1 - yval) * (est1 - yval);
                        n1++;
                        ss2 += (est2 - yval) * (est2 - yval);
                        n2++;
                        ss3 += (est3 - yval) * (est3 - yval);
                        n3++;

                        nrt--;
                    }
                    count++;
                }
                nct--;
            }
        }
        G_percent(nrows, nrows, 4);

        for (i = 0; i < ninx; i++) {
            release_bufs(&(xbuf1[i]));
            release_bufs(&(xbuf2[i]));
            release_bufs(&(xbuf3[i]));
        }
        release_bufs(&ybuf1);
        release_bufs(&ybuf2);
        release_bufs(&ybuf3);

        G_debug(3, "count: %d", count);

        if (n1 < count || n2 < count || n3 < count) {
            G_debug(1, "increasing bwmin to %d", bw + 1);
            bwmin = bw + 1;
            bw += step + 1;
            ss1 = 3;
            ss2 = 2;
            ss3 = 1;
            n1 = n2 = n3 = 1;
            continue;
        }

        ss1 /= n1;
        ss2 /= n2;
        ss3 /= n3;

        G_debug(1, "ss1: %g", ss1);
        G_debug(1, "ss2: %g", ss2);
        G_debug(1, "ss3: %g", ss3);

#if 0
        /* activate for debugging */
        printf("%d|%g\n", prevbw, ss1);
        printf("%d|%g\n", bw, ss2);
        printf("%d|%g\n", nextbw, ss3);
#endif

        /* first gradient */
        f11 = ss2 - ss1;
        /* second gradient */
        f12 = ss3 - ss2;
        /* gradient of gradient */
        f2 = f12 - f11;

        G_free(w1[0]);
        G_free(w2[0]);
        G_free(w3[0]);
        G_free(w1);
        G_free(w2);
        G_free(w3);

/* deactivate to get sum of squares for (newbw = bw; newbw > 1; newbw--) */
#if 1
        newbw = bw;

        if (ss2 < ss1 && ss2 < ss3) {
            /* local minimum */
            havemin = 1;

            if (lastbw > bw)
                newbw = bw - 2;
            else
                newbw = bw + 2;

            if (ss2 < ssmin) {
                G_debug(1, "New candidate %d", bw);
            }
            else if (ss2 > ssmin) {
                G_debug(1, "Local minimum at %d is larger than %d", bw, bestbw);
            }
            else { /* ss2 == ssmin */
                break;
            }
        }
        else if (ss2 > ss1 && ss2 > ss3) {
            /* local maximum */
            G_debug(1, "Detected local maximum at bw %d", bw);
            if (ss1 < ss3) {
                newbw = bw - 1;
                if (newbw == lastbw)
                    newbw--;
                if (newbw - step < bwmin) {
                    newbw = bw + 3;
                    if (newbw == lastbw)
                        newbw++;
                }
            }
            else {
                newbw = bw + 1;
                if (newbw == lastbw)
                    newbw++;
            }
        }
        else {
            /* determine new bandwidth */
            if (f2 > 0) {
                /* Newton's method to find the extremum */
                newbw = bw - (f11 + f12) / (step * f2) + 0.5;
                if (newbw == bw) {
                    if (ss1 > ss3) {
                        /* increase bandwidth */
                        newbw = bw + 1;
                    }
                    else {
                        newbw = bw - 1;
                    }
                }
                if (newbw - step < bwmin)
                    newbw = bwmin + step;
                G_debug(1, "Newton: bw %d, new %d", bw, newbw);
            }
            else {
                if (ss1 < ss3) {
                    /* decrease bandwidth */
                    newbw = (bw + bwmin) / 2;
                    if (newbw - step < bwmin) {
                        newbw = bwmin + step;
                        if (newbw == bw)
                            newbw++;
                        if (newbw == lastbw)
                            newbw++;
                    }
                }
                else if (ss1 > ss3) {
                    /* increase bandwidth */
                    newbw = bw + bw / 2;
                }
                else { /* ss1 == ss3 */
                    newbw = bw + 1;
                    if (newbw == lastbw)
                        newbw++;
                }
            }

            if (ss1 < ss2 && newbw > bw) {
                /* moving bw to wrong direction: stop here? */
                G_debug(1, "f11: %g, f12: %g, f2: %g", f11, f12, f2);
                if (f11 > 0 && f12 > 0)
                    newbw = bw - 2;
                else
                    newbw = bw + 2;
            }
            if (ss3 < ss2 && newbw < bw) {
                /* moving bw to wrong direction: stop here? */
                G_debug(1, "f11: %g, f12: %g, f2: %g", f11, f12, f2);
                if (f11 > 0 && f12 > 0)
                    newbw = bw - 2;
                else
                    newbw = bw + 2;
            }
            if (newbw - step < bwmin) {
                newbw = bwmin + step;
                if (newbw == bw)
                    newbw++;
                if (newbw == lastbw)
                    newbw++;
            }
        }

        if (ssmin > ss2) {
            ssmin = ss2;
            bestbw = bw;
        }

        if (newbw - step < bwmin) {
            newbw = bwhi + step;
        }

        if (newbw == bw)
            break;
#else
        newbw = bw - 1;
        if (newbw < bwmin)
            break;
#endif

        if (newbw < bwmin) {
            G_debug(1, "Bandwidth is getting too small: %d", newbw);
            if (bw > bwmin)
                newbw = bwmin;
            else
                break;
        }

        lastbw = bw;
        bw = newbw;
    }

    if (bw < bwmin)
        bw = bwmin;
    if (bw > bwmax)
        bw = bwmax;

    if (!havemin)
        G_warning(_("Could not find minimum"));

    return bw;
}
