#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include "ncb.h"
#include "window.h"

#define sqr(x) ((x) * (x))

double (*entropy)(double);
double (*entropy_p)(double);

static double alpha = 1.;

void circle_mask(void)
{
    int i, j;
    double dist, distsq;

    if (ncb.mask)
        return;

    ncb.mask = G_malloc(ncb.nsize * sizeof(char *));

    for (i = 0; i < ncb.nsize; i++)
        ncb.mask[i] = G_malloc(ncb.nsize);

    dist = (ncb.nsize - 1.0) / 2.0;
    distsq = sqr(dist);
    if (ncb.nsize % 2 == 0) {
        /* nsize is even */
        distsq += 0.25;
    }

    ncb.n = 0;
    for (i = 0; i < ncb.nsize; i++) {
        for (j = 0; j < ncb.nsize; j++) {
            ncb.mask[i][j] = sqr(i - dist) + sqr(j - dist) <= distsq;
            ncb.n += ncb.mask[i][j];
        }
    }
}

/* argument of the sum for general entropy */
double eai(double p)
{
    if (p)
        return pow(p, alpha);
    return 0;
}

/* argument of the sum for Shannon entropy */
double shi(double p)
{
    if (p)
        return -p * log2(p);
    return 0;
}

/* general entropy for alpha */
double eah(double h)
{
    if (h)
        return log2(h) / (1 - alpha);
    return 0;
}

/* Shannon entropy */
double shh(double h)
{
    return h;
}

int set_alpha(double a)
{
    if (a == 1) {
        entropy_p = shi;
        entropy = shh;
    }
    else {
        alpha = a;
        entropy_p = eai;
        entropy = eah;
    }

    return (a == 1);
}

int types_differ(CELL a, CELL b)
{
    if (!Rast_is_c_null_value(&a) && !Rast_is_c_null_value(&b))
        return (a != b);

    if (Rast_is_c_null_value(&a) && Rast_is_c_null_value(&b))
        return 0;

    /* either a or b is NULL */
    return 1;

    if ((Rast_is_c_null_value(&a) && !Rast_is_c_null_value(&b)) ||
        (!Rast_is_c_null_value(&a) && Rast_is_c_null_value(&b)))
        return 1;

    return 0;
}

/* patch identification */
int gather(int offset)
{
    int row, col;
    int i, j;
    int idx;
    int n = 0;
    int nchanges = 0;
    int connected, old_pid, new_pid;
    int *pid_curr, *pid_prev, *pid_tmp;
    struct c_h *ch;

    /* reset stats */
    for (i = 0; i < ncb.nin; i++) {
        ci.n[i] = 0;
        ci.ht[i] = 0;
        ci.hts[i] = 0;

        for (j = 0; j < ci.ntypes; j++) {
            ci.dt[i][j] = 0;
            ci.dts[i][j] = 0;
        }
        for (j = ci.ntypes; j < ci.dts_size; j++)
            ci.dts[i][j] = 0;

        for (j = 0; j < ci.nsizebins; j++) {
            ci.ds[i][j] = 0;
        }

        ch = &ci.ch[i];
        ch->pid = 0;

        Rast_set_c_null_value(&ch->up, 1);
        Rast_set_c_null_value(&ch->left, 1);
        Rast_set_c_null_value(&ch->curr, 1);

        for (j = 0; j < ch->palloc; j++) {
            ch->pst[j].size = 0;
            ch->pst[j].type = 0;
        }
        ch->np = 0;

        for (j = 0; j < ncb.nsize; j++) {
            ch->pid_curr[j] = 0;
            ch->pid_prev[j] = 0;
        }
    }

    /* collect distributions */
    n = 0;
    for (row = 0; row < ncb.nsize; row++) {

        for (i = 0; i < ncb.nin; i++) {
            ch = &ci.ch[i];

            Rast_set_c_null_value(&ch->left, 1);

            pid_tmp = ch->pid_prev;
            ch->pid_prev = ch->pid_curr;
            ch->pid_curr = pid_tmp;
        }

        for (col = 0; col < ncb.nsize; col++) {

            if (ncb.mask && !ncb.mask[row][col])
                continue;

            for (i = 0; i < ncb.nin; i++) {

                ch = &ci.ch[i];
                ch->pid_curr[col] = 0;

                ch->curr = ncb.in[i].buf[row][offset + col];
                /* number of changes */
                if (i > 0)
                    nchanges += types_differ(ch->curr, ci.ch[i - 1].curr);

                if (Rast_is_c_null_value(&ch->curr)) {
                    ch->left = ch->curr;
                    continue;
                }
                Rast_set_c_null_value(&ch->up, 1);
                if (row > 0) {
                    if (ncb.mask) {
                        if (ncb.mask[row - 1][col])
                            ch->up = ncb.in[i].buf[row - 1][offset + col];
                    }
                    else {
                        ch->up = ncb.in[i].buf[row - 1][offset + col];
                    }
                }

                /* type count */
                ci.dt[i][ch->curr - ci.tmin] += 1;

                /* trace patch clumps */
                pid_curr = ch->pid_curr;
                pid_prev = ch->pid_prev;

                connected = 0;
                if (!Rast_is_c_null_value(&ch->left) && ch->curr == ch->left) {
                    pid_curr[col] = pid_curr[col - 1];
                    connected = 1;
                    ch->pst[pid_curr[col]].size++;
                }

                if (!Rast_is_c_null_value(&ch->up) && ch->curr == ch->up) {

                    if (pid_curr[col] != pid_prev[col]) {

                        if (connected) {
                            ch->np--;

                            if (ch->np == 0) {
                                G_fatal_error("npatch == 0 at row %d, col %d",
                                              row, col);
                            }
                        }

                        old_pid = pid_curr[col];
                        new_pid = pid_prev[col];
                        pid_curr[col] = new_pid;
                        if (old_pid > 0) {
                            /* merge */
                            /* update left side of the current row */
                            for (j = 0; j < col; j++) {
                                if (pid_curr[j] == old_pid)
                                    pid_curr[j] = new_pid;
                            }
                            /* update right side of the previous row */
                            for (j = col + 1; j < ncb.nsize; j++) {
                                if (pid_prev[j] == old_pid)
                                    pid_prev[j] = new_pid;
                            }
                            ch->pst[new_pid].size += ch->pst[old_pid].size;
                            ch->pst[old_pid].size = 0;

                            if (old_pid == ch->pid)
                                ch->pid--;
                        }
                        else {
                            ch->pst[new_pid].size++;
                        }
                    }
                    connected = 1;
                }
                if (!connected) {
                    /* start new patch */
                    ch->np++;
                    ch->pid++;
                    pid_curr[col] = ch->pid;

                    if (ch->pid >= ch->palloc) {
                        ch->pst = (struct pst *)G_realloc(
                            ch->pst, (ch->pid + 10) * sizeof(struct pst));

                        for (j = ch->palloc; j < ch->pid + 10; j++)
                            ch->pst[j].size = 0;

                        ch->palloc = ch->pid + 10;
                    }

                    ch->pst[ch->pid].size = 1;
                    ch->pst[ch->pid].type = ch->curr;
                }

                ch->left = ch->curr;
                ci.n[i]++;
                n++;
            }
        }
    }

    if (n == 0) {
        return 0;
    }

    /* convert patches to distribution of types and size classes */
    for (i = 0; i < ncb.nin; i++) {
        int nsum;

        ch = &ci.ch[i];
        nsum = 0;
        for (j = 0; j <= ch->pid; j++) {
            if (ch->pst[j].size > 0) {
                frexp(ch->pst[j].size, &idx);
                ci.ds[i][idx - 1] += ch->pst[j].size;
                idx = (ch->pst[j].type - ci.tmin) * ci.nsizebins + idx - 1;
                ci.dts[i][idx] += ch->pst[j].size;
            }
            nsum += ch->pst[j].size;
        }
        if (nsum != ci.n[i])
            G_fatal_error("patch sum is %d, should be %d", nsum, ci.n[i]);
    }

    ci.nchanges = nchanges;

    return n;
}
