#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/segment.h>
#include <grass/glocale.h>
#include "cache.h"
#include "tps.h"
#include "flag.h"
#include "rclist.h"
#include "pavlrc.h"

static int solvemat(double **m, double a[], double B[], int n)
{
    int i, j, i2, j2, imark;
    double factor, temp, *tempp;
    double pivot; /* ACTUAL VALUE OF THE LARGEST PIVOT CANDIDATE */

    for (i = 0; i < n; i++) {
        j = i;

        /* find row with largest magnitude value for pivot value */

        pivot = m[i][j];
        imark = i;
        for (i2 = i + 1; i2 < n; i2++) {
            temp = fabs(m[i2][j]);
            if (temp > fabs(pivot)) {
                pivot = m[i2][j];
                imark = i2;
            }
        }

        /* if the pivot is very small then the points are nearly co-linear */
        /* co-linear points result in an undefined matrix, and nearly */
        /* co-linear points results in a solution with rounding error */

        if (fabs(pivot) < 1.0e-7) {
            G_debug(4, "Matrix is unsolvable: pivot = %g", pivot);
            return 0;
        }

        /* if row with highest pivot is not the current row, switch them */

        if (imark != i) {
            /*
            for (j2 = 0; j2 < n; j2++) {
                temp = m[imark][j2];
                m[imark][j2] = m[i][j2];
                m[i][j2] = temp;
            }
            */

            tempp = m[imark];
            m[imark] = m[i];
            m[i] = tempp;

            temp = a[imark];
            a[imark] = a[i];
            a[i] = temp;
        }

        /* compute zeros above and below the pivot, and compute
           values for the rest of the row as well */

        for (i2 = 0; i2 < n; i2++) {
            if (i2 != i) {
                factor = m[i2][j] / pivot;
                for (j2 = j; j2 < n; j2++)
                    m[i2][j2] -= factor * m[i][j2];
                a[i2] -= factor * a[i];
            }
        }
    }

    /* SINCE ALL OTHER VALUES IN THE MATRIX ARE ZERO NOW, CALCULATE THE
       COEFFICIENTS BY DIVIDING THE COLUMN VECTORS BY THE DIAGONAL VALUES. */

    for (i = 0; i < n; i++) {
        B[i] = a[i] / m[i][i];
    }

    return 1;
}

static int row_src2dst(int row, struct Cell_head *src, struct Cell_head *dst)
{
    return (dst->north - src->north + (row + 0.5) * src->ns_res) / dst->ns_res;
}

static int col_src2dst(int col, struct Cell_head *src, struct Cell_head *dst)
{
    return (src->west - dst->west + (col + 0.5) * src->ew_res) / dst->ew_res;
}

static int cmp_pnts(const void *first, const void *second)
{
    struct tps_pnt *a = (struct tps_pnt *)first;
    struct tps_pnt *b = (struct tps_pnt *)second;

    if (a->r == b->r)
        return (a->c - b->c);

    return (a->r - b->r);
}

static int load_tps_pnts(struct cache *in_seg, DCELL *dval, int n_vars,
                         struct tps_pnt *pnts, int n_points,
                         struct Cell_head *src, struct Cell_head *dst,
                         double regularization, double **m, double *a,
                         double **mvars, double *avars, double **mpnts,
                         double *apnts, double *vmin, double *vmax)
{
    int i, j, k;
    double dx, dy, dist, dist2, distsum, reg;

    for (i = 0; i <= n_vars; i++) {
        a[i] = 0.0;
        m[i][i] = 0.0;
        for (j = 0; j < i; j++) {
            m[i][j] = m[j][i] = 0.0;
        }
    }

    if (n_vars && mvars) {
        for (i = 0; i <= n_vars; i++) {
            avars[i] = 0.0;
            mvars[i][i] = 0.0;
            for (j = 0; j < i; j++) {
                mvars[i][j] = mvars[j][i] = 0.0;
            }
        }
    }

    distsum = 0;
    for (i = 0; i < n_points; i++) {

        cache_get(in_seg, (void *)dval, pnts[i].r, pnts[i].c);

        /* global */
        a[i + 1 + n_vars] = dval[0];
        m[0][i + 1 + n_vars] = m[i + 1 + n_vars][0] = 1.0;

        for (j = 0; j < n_vars; j++) {
            m[j + 1][i + 1 + n_vars] = m[i + 1 + n_vars][j + 1] = dval[j + 1];

            if (vmin) {
                if (i == 0) {
                    vmin[j] = vmax[j] = dval[j + 1];
                }
                else {
                    if (vmin[j] > dval[j + 1])
                        vmin[j] = dval[j + 1];
                    if (vmax[j] < dval[j + 1])
                        vmax[j] = dval[j + 1];
                }
            }
        }

        if (n_vars && mvars) {
            avars[0] += dval[0];
            mvars[0][0] += 1;
            for (j = 1; j <= n_vars; j++) {
                mvars[j][0] += dval[j];
                mvars[0][j] = mvars[j][0];
                mvars[j][j] += dval[j] * dval[j];
                for (k = 1; k < j; k++) {
                    mvars[j][k] += dval[j] * dval[k];
                    mvars[k][j] = mvars[j][k];
                }
                avars[j] += dval[0] * dval[j];
            }
        }

        /* convert src r,c to n,s */
        pnts[i].r = src->north - (pnts[i].r + 0.5) * src->ns_res;
        pnts[i].c = src->west + (pnts[i].c + 0.5) * src->ew_res;

        /* TPS */
        for (k = 0; k <= i; k++) {

            dx = (pnts[i].c - pnts[k].c);
            dy = (pnts[i].r - pnts[k].r);
            dist2 = dx * dx + dy * dy;
            dist = 0;
            if (dist2 > 0)
                dist = dist2 * log(dist2) * 0.5;

            m[i + 1 + n_vars][k + 1 + n_vars] = dist;

            if (regularization > 0 && dist2 > 0) {
                dist = sqrt(dist2);
                distsum += dist;
            }
            if (k != i) {
                m[k + 1 + n_vars][i + 1 + n_vars] =
                    m[i + 1 + n_vars][k + 1 + n_vars];
                if (regularization > 0 && dist2 > 0)
                    distsum += dist;
            }
        }
    }

    if (regularization > 0) {
        distsum /= (n_points * n_points);
        reg = regularization * distsum * distsum;

        for (i = 0; i < n_points; i++)
            m[i + 1 + n_vars][i + 1 + n_vars] = reg;
    }

    if (n_vars && mpnts) {
        mpnts[0][0] = m[0][0];
        apnts[0] = a[0];
        for (i = 0; i < n_points; i++) {
            mpnts[0][i + 1] = m[0][i + 1 + n_vars];
            mpnts[i + 1][0] = m[i + 1 + n_vars][0];

            mpnts[i + 1][i + 1] = m[i + 1 + n_vars][i + 1 + n_vars];
            for (j = 0; j < i; j++) {
                mpnts[i + 1][j + 1] = m[i + 1 + n_vars][j + 1 + n_vars];
                mpnts[j + 1][i + 1] = m[j + 1 + n_vars][i + 1 + n_vars];
            }
            apnts[i + 1] = a[i + 1 + n_vars];
        }
    }

    return 1;
}

static int bfs_search_nn(FLAG *pnt_flag, struct Cell_head *src,
                         struct tps_pnt *cur_pnts, int max_points, int row,
                         int col, int *rmin, int *rmax, int *cmin, int *cmax,
                         double *distmax)
{
    int nrows, ncols, rown, coln;
    int nextr[8] = {0, -1, 0, 1, -1, -1, 1, 1};
    int nextc[8] = {1, 0, -1, 0, 1, -1, -1, 1};
    int n, found;
    struct rc next;
    struct rclist rilist;
    struct pavlrc ngbr_rc;
    struct pavlrc_table *visited;
    double dx, dy, dist;

    visited = pavlrc_create(NULL);

    ngbr_rc.row = row;
    ngbr_rc.col = col;
    pavlrc_insert(visited, &ngbr_rc);

    nrows = src->rows;
    ncols = src->cols;

    found = 0;
    *distmax = 0.0;

    if (FLAG_GET(pnt_flag, row, col)) {
        /* add to cur_pnts */
        cur_pnts[found].r = row;
        cur_pnts[found].c = col;
        found++;

        if (*rmin > row)
            *rmin = row;
        if (*rmax < row)
            *rmax = row;
        if (*cmin > col)
            *cmin = col;
        if (*cmax < col)
            *cmax = col;
    }

    /* breadth-first search */
    next.row = row;
    next.col = col;
    rclist_init(&rilist);

    do {
        for (n = 0; n < 8; n++) {
            rown = next.row + nextr[n];
            coln = next.col + nextc[n];

            if (rown < 0 || rown >= nrows || coln < 0 || coln >= ncols)
                continue;

            ngbr_rc.row = rown;
            ngbr_rc.col = coln;

            if (pavlrc_insert(visited, &ngbr_rc) != NULL) {
                continue;
            }

            rclist_add(&rilist, rown, coln);

            if (FLAG_GET(pnt_flag, rown, coln)) {

                dx = coln - col;
                dy = rown - row;

                dist = dx * dx + dy * dy;

                if (*distmax < dist)
                    *distmax = dist;

                cur_pnts[found].r = rown;
                cur_pnts[found].c = coln;
                found++;

                if (*rmin > rown)
                    *rmin = rown;
                if (*rmax < rown)
                    *rmax = rown;
                if (*cmin > coln)
                    *cmin = coln;
                if (*cmax < coln)
                    *cmax = coln;
            }

            if (found == max_points)
                break;
        }
        if (found == max_points)
            break;
    } while (rclist_drop(&rilist, &next)); /* while there are cells to check */

    rclist_destroy(&rilist);
    pavlrc_destroy(visited);

    return found;
}

static int bfs_search(FLAG *pnt_flag, struct Cell_head *src,
                      struct tps_pnt *cur_pnts, int row, int col,
                      int max_points, double min_dist, int rmin, int rmax,
                      int cmin, int cmax)
{
    int nrows, ncols, rown, coln;
    int nextr[8] = {0, -1, 0, 1, -1, -1, 1, 1};
    int nextc[8] = {1, 0, -1, 0, 1, -1, -1, 1};
    int n, found;
    struct rc next;
    struct rclist rilist;
    struct pavlrc ngbr_rc;
    struct pavlrc_table *visited;
    double dx, dy, dist;

    visited = pavlrc_create(NULL);

    ngbr_rc.row = row;
    ngbr_rc.col = col;
    pavlrc_insert(visited, &ngbr_rc);

    nrows = src->rows;
    ncols = src->cols;

    /* breadth-first search */
    next.row = row;
    next.col = col;
    rclist_init(&rilist);

    found = 0;

    do {
        for (n = 0; n < 8; n++) {
            rown = next.row + nextr[n];
            coln = next.col + nextc[n];

            if (rown < 0 || rown >= nrows || coln < 0 || coln >= ncols)
                continue;
            if (rown < rmin || rown > rmax || coln < cmin || coln > cmax)
                continue;

            ngbr_rc.row = rown;
            ngbr_rc.col = coln;

            if (pavlrc_insert(visited, &ngbr_rc) != NULL) {
                continue;
            }

            if (!(FLAG_GET(pnt_flag, rown, coln))) {
                rclist_add(&rilist, rown, coln);
            }
            else {
                dx = coln - col;
                dy = rown - row;

                dist = dx * dx + dy * dy;

                if (dist > min_dist) {
                    cur_pnts[found].r = rown;
                    cur_pnts[found].c = coln;
                    found++;
                }
            }
            if (found == max_points)
                break;
        }
        if (found == max_points)
            break;
    } while (rclist_drop(&rilist, &next)); /* while there are cells to check */

    rclist_destroy(&rilist);
    pavlrc_destroy(visited);

    return found;
}

static int window_pnts(FLAG *pnt_flag, struct Cell_head *src,
                       struct tps_pnt *cur_pnts, int radius, int row, int col,
                       int *rmin, int *rmax, int *cmin, int *cmax,
                       double *distmax)
{
    int rown, coln, row1, row2, col1, col2;
    int found;
    double dx, dy, dist;

    found = 0;
    *distmax = 0.0;

    row1 = row - radius;
    if (row1 < 0)
        row1 = 0;
    row2 = row + radius;
    if (row2 > src->rows - 1)
        row2 = src->rows - 1;

    col1 = col - radius;
    if (col1 < 0)
        col1 = 0;
    col2 = col + radius;
    if (col2 > src->cols - 1)
        col2 = src->cols - 1;

    for (rown = row1; rown <= row2; rown++) {
        for (coln = col1; coln <= col2; coln++) {
            if (FLAG_GET(pnt_flag, rown, coln)) {
                /* add to cur_pnts */
                cur_pnts[found].r = rown;
                cur_pnts[found].c = coln;
                found++;

                if (*rmin > rown)
                    *rmin = rown;
                if (*rmax < rown)
                    *rmax = rown;
                if (*cmin > coln)
                    *cmin = coln;
                if (*cmax < coln)
                    *cmax = coln;

                dx = coln - col;
                dy = rown - row;

                dist = dx * dx + dy * dy;

                if (*distmax < dist)
                    *distmax = dist;
            }
        }
    }

    return found;
}

static double interp_wa(struct cache *in_seg, DCELL *dval,
                        struct tps_pnt *cur_pnts, int pfound, int row, int col,
                        struct Cell_head *src, struct Cell_head *dst,
                        double distmax, double *tps_weight)
{
    int i;
    int src_row, src_col;
    double wsum, maxweight, weight, result;
    double i_n, i_e, dxyw;
    double dx, dy, dist2;

    G_fatal_error("Weighted average");

    i_n = dst->north - (row + 0.5) * dst->ns_res;
    i_e = dst->west + (col + 0.5) * dst->ew_res;
    dxyw = distmax * (src->ns_res + src->ew_res) / 2.0;

    result = 0;
    wsum = 0;
    maxweight = 0;
    for (i = 0; i < pfound; i++) {

        src_row = (src->north - cur_pnts[i].r) / src->ns_res;
        src_col = (cur_pnts[i].c - src->west) / src->ew_res;

        cache_get(in_seg, (void *)dval, src_row, src_col);

        dx = cur_pnts[i].c - i_e;
        dy = cur_pnts[i].r - i_n;

        /* weight for average */
        dx = fabs(dx) / dxyw;
        dy = fabs(dy) / dxyw;
        dist2 = dx * dx + dy * dy;
        weight = exp(-dist2 * 4.0);

        /* weight for tps */
        if (maxweight < weight)
            maxweight = weight;

        wsum += weight;
        result += dval[0] * weight;
    }
    result /= wsum;
    *tps_weight = maxweight;

    return result;
}

static double lm_rsqr(struct cache *in_seg, int n_vars, struct Cell_head *src,
                      struct tps_pnt *cur_pnts, int pfound, double *B)
{
    int i, j, r, c;
    double *obs, *est;
    DCELL *dval;
    double sumX, sumY, sumsqX, sumsqY, sumXY, R2;

    obs = G_malloc(pfound * sizeof(double));
    est = G_malloc(pfound * sizeof(double));
    dval = G_malloc((1 + n_vars) * sizeof(DCELL));

    sumX = sumY = sumsqX = sumsqY = sumXY = 0.0;
    for (i = 0; i < pfound; i++) {

        r = (int)((src->north - cur_pnts[i].r) / src->ns_res);
        c = (int)((cur_pnts[i].c - src->west) / src->ew_res);

        cache_get(in_seg, (void *)dval, r, c);
        obs[i] = dval[0];
        est[i] = B[0];
        for (j = 1; j <= n_vars; j++) {
            est[i] += dval[j] * B[j];
        }

        sumX += obs[i];
        sumY += est[i];
        sumsqX += obs[i] * obs[i];
        sumsqY += est[i] * est[i];
        sumXY += obs[i] * est[i];
    }

    R2 = (sumXY * pfound - sumX * sumY) * (sumXY * pfound - sumX * sumY) /
         ((sumsqX * pfound - sumX * sumX) * (sumsqY * pfound - sumY * sumY));

    G_free(obs);
    G_free(est);
    G_free(dval);

    return R2;
}

int tps_nn(struct cache *in_seg, struct cache *var_seg, int n_vars,
           struct cache *out_seg, int out_fd, char *mask_name,
           struct Cell_head *src, struct Cell_head *dst, off_t n_points,
           int min_points, int max_points, double regularization,
           double overlap, int clustered, double lm_thresh, double efac)
{
    int ridx, cidx, row, col, nrows, ncols, src_row, src_col;
    double **m, *a, *B;
    double **mfull, *afull, *Bfull;
    double **mpnts, *apnts, *Bpnts;
    double **mvars, *avars, *Bvars;
    double *Bc;
    int i, j;
    int kdalloc, palloc, n_cur_points;
    struct tps_pnt *cur_pnts;
    double dx, dy, dist, dist2, mfactor;
    DCELL *dval, result, *outbuf, *varbuf;
    CELL *maskbuf;
    int solved, solved_tps_lm, solved_tps, solved_lm;
    int n_vars_i, n_vars_ic;
    double rsqr;
    int kdfound, bfsfound, pfound;
    double distmax, mindist;
    int do_clustered;
    int mask_fd;
    FLAG *mask_flag, *pnt_flag;
    struct tps_out tps_out;
    double *pvar;
    double weight, dxi, dyi;
    double wmin, wmax;
    int rmin, rmax, cmin, cmax, rminp, rmaxp, cminp, cmaxp;
    int irow, irow1, irow2, icol, icol1, icol2;
    unsigned int cnt_wa, cnt_tps_lm, cnt_tps, cnt_efac;
    double i_n, i_e;
    double *vmin, *vmax;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    kdalloc = palloc = min_points;
    a = G_malloc((palloc + 1 + n_vars) * sizeof(double));
    B = G_malloc((palloc + 1 + n_vars) * sizeof(double));
    m = G_malloc((palloc + 1 + n_vars) * sizeof(double *));
    for (i = 0; i < (palloc + 1 + n_vars); i++)
        m[i] = G_malloc((palloc + 1 + n_vars) * sizeof(double));
    cur_pnts = G_malloc(palloc * 5 * sizeof(struct tps_pnt));

    afull = a;
    Bfull = B;
    mfull = m;

    pvar = NULL;
    varbuf = NULL;
    mvars = NULL;
    avars = NULL;
    Bvars = NULL;

    mpnts = NULL;
    apnts = NULL;
    Bpnts = NULL;

    Bc = NULL;

    vmin = NULL;
    vmax = NULL;
    if (n_vars) {
        pvar = G_malloc(palloc * 5 * n_vars * sizeof(double));
        cur_pnts[0].vars = pvar;
        for (i = 1; i < palloc * 5; i++)
            cur_pnts[i].vars = cur_pnts[i - 1].vars + n_vars;

        varbuf = G_malloc(n_vars * sizeof(DCELL));

        avars = G_malloc((1 + n_vars) * sizeof(double));
        Bvars = G_malloc((1 + n_vars) * sizeof(double));
        mvars = G_malloc((1 + n_vars) * sizeof(double *));
        for (i = 0; i < (1 + n_vars); i++)
            mvars[i] = G_malloc((1 + n_vars) * sizeof(double));

        apnts = G_malloc((palloc + 1) * sizeof(double));
        Bpnts = G_malloc((palloc + 1) * sizeof(double));
        mpnts = G_malloc((palloc + 1) * sizeof(double *));
        for (i = 0; i < (palloc + 1); i++)
            mpnts[i] = G_malloc((palloc + 1) * sizeof(double));

        vmin = G_malloc(n_vars * sizeof(double));
        vmax = G_malloc(n_vars * sizeof(double));
    }

    dval = G_malloc((1 + n_vars) * sizeof(DCELL));

    mask_flag = flag_create(nrows, ncols);

    maskbuf = NULL;
    if (mask_name) {
        G_message("Loading mask map...");
        mask_fd = Rast_open_old(mask_name, "");
        maskbuf = Rast_allocate_c_buf();

        for (row = 0; row < nrows; row++) {
            Rast_get_c_row(mask_fd, maskbuf, row);
            for (col = 0; col < ncols; col++) {
                if (Rast_is_c_null_value(&maskbuf[col]) || maskbuf[col] == 0)
                    FLAG_SET(mask_flag, row, col);
            }
        }
        Rast_close(mask_fd);
        G_free(maskbuf);
        maskbuf = NULL;
    }

    G_message(_("Analyzing input ..."));
    pnt_flag = flag_create(src->rows, src->cols);

    rminp = src->rows;
    rmaxp = 0;
    cminp = src->cols;
    cmaxp = 0;
    for (row = 0; row < src->rows; row++) {
        G_percent(row, src->rows, 2);

        for (col = 0; col < src->cols; col++) {
            cache_get(in_seg, (void *)dval, row, col);
            if (!Rast_is_d_null_value(dval)) {
                FLAG_SET(pnt_flag, row, col);
                if (rminp > row)
                    rminp = row;
                if (rmaxp < row)
                    rmaxp = row;
                if (cminp > col)
                    cminp = col;
                if (cmaxp < col)
                    cmaxp = col;
            }
        }
    }
    rminp = row_src2dst(rminp, src, dst);
    rmaxp = row_src2dst(rmaxp, src, dst);
    cminp = col_src2dst(cminp, src, dst);
    cmaxp = col_src2dst(cmaxp, src, dst);
    G_percent(1, 1, 2);

    G_message(_("Initializing output ..."));
    tps_out.val = 0;
    tps_out.wsum = 0;
    tps_out.wmax = 0;
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        for (col = 0; col < ncols; col++) {
            if (cache_put(out_seg, (void *)&tps_out, row, col) == NULL)
                G_fatal_error(_("Unable to write to temporary file"));
        }
    }
    G_percent(1, 1, 2);

    G_message(_("Nearest neighbor TPS interpolation with %ld points..."),
              n_points);

    wmin = 10;
    wmax = 0;
    cnt_wa = 0;
    cnt_tps_lm = 0;
    cnt_tps = 0;
    cnt_efac = 0;

    if (overlap > 1.0)
        overlap = 1.0;
    if (overlap < 0.0)
        overlap = 0.0;
    /* keep in sync with weight calculation below */
    overlap = exp((overlap - 1.0) * 8.0);

    for (ridx = 0; ridx < nrows; ridx++) {

        G_percent(ridx, nrows, 1);

        row = (ridx >> 1);
        if (ridx & 1)
            row = nrows - 1 - row;

        src_row = row_src2dst(row, dst, src);

        for (cidx = 0; cidx < ncols; cidx++) {

            col = (cidx >> 1);
            if (cidx & 1)
                col = ncols - 1 - col;

            if ((FLAG_GET(mask_flag, row, col))) {
                continue;
            }

            if (n_vars) {

                cache_get(var_seg, (void *)varbuf, row, col);

                if (Rast_is_d_null_value(varbuf))
                    continue;
            }

            cache_get(out_seg, (void *)&tps_out, row, col);
            if (tps_out.wmax > overlap)
                continue;

            rmin = src->rows;
            rmax = 0;
            cmin = src->cols;
            cmax = 0;

            solved = 0;
            solved_tps_lm = solved_tps = 0;
            n_cur_points = 0;
            pfound = kdfound = 0;
            src_col = col_src2dst(col, dst, src);
            distmax = 0;
            n_vars_i = n_vars;

            while (!solved && (max_points == 0 || n_cur_points < max_points)) {

                /* increase points if unsolvable */
                n_cur_points += min_points;

                if (n_cur_points > min_points)
                    G_verbose_message(_("Increasing number of points to %d"),
                                      n_cur_points);

                if (n_cur_points > n_points)
                    n_cur_points = n_points;

                /* alloc */
                if (kdalloc < n_cur_points) {
                    G_free(cur_pnts);

                    kdalloc = n_cur_points;

                    cur_pnts = G_malloc(kdalloc * 5 * sizeof(struct tps_pnt));
                    if (n_vars) {
                        G_free(pvar);
                        pvar = G_malloc(kdalloc * 5 * n_vars * sizeof(double));
                        cur_pnts[0].vars = pvar;
                        for (i = 1; i < kdalloc * 5; i++)
                            cur_pnts[i].vars = cur_pnts[i - 1].vars + n_vars;
                    }
                }

                /* collect nearest neighbors */
                rmin = src->rows;
                rmax = 0;
                cmin = src->cols;
                cmax = 0;
                kdfound = bfs_search_nn(pnt_flag, src, cur_pnts, n_cur_points,
                                        src_row, src_col, &rmin, &rmax, &cmin,
                                        &cmax, &distmax);

                mindist = n_cur_points / M_PI * 1.5;

                do_clustered = 0;
                if (distmax > mindist || rmin >= src_row || rmax <= src_row ||
                    cmin >= src_col || cmax <= src_col) {

                    do_clustered = 1;
                }

                pfound = kdfound;

                if (clustered && do_clustered) {
                    /* collect points with breadth-first search
                     * min dist must be > max dist of nearest neighbors */

                    /* qrt1: 0, row, col + 1, ncols - 1 */
                    if (rminp <= row && cmaxp > col) {
                        bfsfound = bfs_search(
                            pnt_flag, src, cur_pnts + pfound, src_row, src_col,
                            n_cur_points / 3, distmax, 0, src_row, src_col + 1,
                            src->cols - 1);

                        if (bfsfound == 0)
                            G_debug(4, "No BFS points for NE quadrant");

                        pfound += bfsfound;
                    }

                    /* qrt2: 0, row - 1, 0, col */
                    if (rminp < row && cminp <= col) {
                        bfsfound =
                            bfs_search(pnt_flag, src, cur_pnts + pfound,
                                       src_row, src_col, n_cur_points / 3,
                                       distmax, 0, src_row - 1, 0, src_col);

                        if (bfsfound == 0)
                            G_debug(4, "No BFS points for NW quadrant");

                        pfound += bfsfound;
                    }

                    /* qrt3: row, nrows - 1, 0, col - 1 */
                    if (rmaxp >= row && cminp < col) {
                        bfsfound = bfs_search(
                            pnt_flag, src, cur_pnts + pfound, src_row, src_col,
                            n_cur_points / 3, distmax, src_row, src->rows - 1,
                            0, src_col - 1);

                        if (bfsfound == 0)
                            G_debug(4, "No BFS points for SW quadrant");

                        pfound += bfsfound;
                    }

                    /* qrt4: row + 1, nrows - 1, col, ncols - 1 */
                    if (rmaxp > row && cmaxp >= col) {
                        bfsfound = bfs_search(
                            pnt_flag, src, cur_pnts + pfound, src_row, src_col,
                            n_cur_points / 3, distmax, src_row + 1,
                            src->rows - 1, src_col, src->cols - 1);

                        if (bfsfound == 0)
                            G_debug(4, "No BFS points for SE quadrant");

                        pfound += bfsfound;
                    }
                }

                m = mfull;
                a = afull;
                B = Bfull;

                if (palloc < pfound) {
                    G_free(a);
                    G_free(B);
                    for (i = 0; i < (palloc + 1 + n_vars); i++)
                        G_free(m[i]);
                    G_free(m);

                    if (n_vars) {
                        G_free(apnts);
                        G_free(Bpnts);
                        for (i = 0; i < (palloc + 1); i++)
                            G_free(mpnts[i]);
                        G_free(mpnts);
                    }

                    palloc = pfound;
                    a = G_malloc((palloc + 1 + n_vars) * sizeof(double));
                    B = G_malloc((palloc + 1 + n_vars) * sizeof(double));
                    m = G_malloc((palloc + 1 + n_vars) * sizeof(double *));
                    for (i = 0; i < (palloc + 1 + n_vars); i++)
                        m[i] = G_malloc((palloc + 1 + n_vars) * sizeof(double));

                    mfull = m;
                    afull = a;
                    Bfull = B;

                    if (n_vars) {
                        apnts = G_malloc((palloc + 1) * sizeof(double));
                        Bpnts = G_malloc((palloc + 1) * sizeof(double));
                        mpnts = G_malloc((palloc + 1) * sizeof(double *));
                        for (i = 0; i < (palloc + 1); i++)
                            mpnts[i] = G_malloc((palloc + 1) * sizeof(double));
                    }
                }

                /* sort points */
                /* qsort(cur_pnts, kdfound, sizeof(struct tps_pnt), cmp_pnts);
                 */

                qsort(cur_pnts, pfound, sizeof(struct tps_pnt), cmp_pnts);

                load_tps_pnts(in_seg, dval, n_vars, cur_pnts, pfound, src, dst,
                              regularization, m, a, mvars, avars, mpnts, apnts,
                              vmin, vmax);

                /* solve */
                /* it can happen that a simple linear model with the
                 * given covariables can be solved but TPS with
                 * covariables can not be solved
                 */
                solved_tps_lm = solved_tps = 0;
                n_vars_i = n_vars;
                m = mfull;
                a = afull;
                B = Bfull;
                if (n_vars) {

                    solved_tps_lm = solvemat(m, a, B, pfound + 1 + n_vars);

                    if (solved_tps_lm && lm_thresh > 0) {

                        solved_lm = solvemat(mvars, avars, Bvars, 1 + n_vars);
                        if (!solved_lm) {
                            G_debug(1,
                                    "LM with covariables not working at row "
                                    "%d, col %d",
                                    row, col);

                            solved_tps_lm = 0;
                        }
                        else {
                            rsqr = lm_rsqr(in_seg, n_vars, src, cur_pnts,
                                           pfound, B);

                            if (rsqr < lm_thresh) {
                                solved_tps_lm = 0;
                            }
                            else {
                                for (i = 1; i <= n_vars; i++) {
                                    if (fabs(B[i]) > fabs(5 * Bvars[i])) {
                                        G_debug(
                                            1, "LM B%d is %g but TPS B%d is %g",
                                            i, Bvars[i], i, B[i]);
                                        solved_tps_lm = 0;
                                    }
                                }
                            }
                        }
                    }

                    if (efac) {
                        for (i = 0; i < n_vars; i++) {
                            double diff;

                            diff = efac * (vmax[i] - vmin[i]);
                            vmin[i] -= diff;
                            vmax[i] += diff;
                        }
                    }

                    if (!solved_tps_lm) {
                        n_vars_i = 0;
                        m = mpnts;
                        a = apnts;
                        B = Bpnts;

                        solved_tps = solvemat(m, a, B, pfound + 1);
                    }
                }
                else {
                    solved_tps = solvemat(m, a, B, pfound + 1);
                }

                solved = (solved_tps_lm | solved_tps);

                if (!solved && n_cur_points == n_points)
                    G_fatal_error(_("Matrix is unsolvable"));
            }

            /* priorities for interpolation
             * TPS with covariables
             * TPS without covariables
             * weighted average
             */

            if (solved_tps_lm)
                cnt_tps_lm++;
            else if (solved_tps)
                cnt_tps++;

            if (!solved) {
                if (pfound > 0 && distmax > 0) {

                    G_debug(1, "Weighted average");

                    result = interp_wa(in_seg, dval, cur_pnts, pfound, row, col,
                                       src, dst, distmax, &weight);

                    cache_get(out_seg, (void *)&tps_out, irow, icol);

                    /* weight according to distance to nearest point */
                    if (tps_out.wmax < weight)
                        tps_out.wmax = weight;

                    tps_out.val += result * weight;
                    tps_out.wsum += weight;
                    cache_put(out_seg, (void *)&tps_out, row, col);

                    cnt_wa++;
                }
                continue;
            }

            /* must be <= 0.5 */
            mfactor = 0.0;
            /* min: 0
             * max: 0.5
             * 1 - 1 / d: -> 0 for dense spacing
             *            1 for sparse points
             */

            if (clustered) {
                double mfactoradj;
                double dmin;
                double dmax;

                dmin = 2.0 * sqrt(2.0 * kdfound / M_PI);
                dmax = rmax - rmin;
                if (dmax < cmax - cmin)
                    dmax = cmax - cmin;

                mfactoradj = 0.0;
                if (dmax > dmin) {
                    mfactoradj = pow(1 - dmin / dmax, 2.0) * 0.5;
                    G_debug(1, "adjusted mfactor: %g", mfactoradj);
                }
                mfactor = mfactoradj;
            }

            rmin = row_src2dst(rmin, src, dst);
            rmax = row_src2dst(rmax, src, dst);
            cmin = col_src2dst(cmin, src, dst);
            cmax = col_src2dst(cmax, src, dst);

            irow1 = rmin + (int)((rmax - rmin) * mfactor);
            irow2 = rmax - (int)((rmax - rmin) * mfactor);
            icol1 = cmin + (int)((cmax - cmin) * mfactor);
            icol2 = cmax - (int)((cmax - cmin) * mfactor);

            if (irow1 > row) {
                irow2 -= irow1 - row;
                irow1 = row;
            }
            if (irow2 < row) {
                irow1 += row - irow2;
                irow2 = row;
            }
            if (icol1 > col) {
                icol2 -= icol1 - col;
                icol1 = col;
            }
            if (icol2 < col) {
                icol1 += col - icol2;
                icol2 = col;
            }

            if (rmin == rminp)
                irow1 = 0;
            if (rmax == rmaxp)
                irow2 = nrows - 1;
            if (cmin == cminp)
                icol1 = 0;
            if (cmax == cmaxp)
                icol2 = ncols - 1;

            if (irow1 < 0)
                irow1 = 0;
            if (irow2 > nrows - 1)
                irow2 = nrows - 1;
            if (icol1 < 0)
                icol1 = 0;
            if (icol2 > ncols - 1)
                icol2 = ncols - 1;

            if (pfound == n_points) {
                /* one global equation, one interpolation window */
                irow1 = 0;
                irow2 = nrows - 1;
                icol1 = 0;
                icol2 = ncols - 1;
            }

            dxi = icol2 - icol1 + 1;
            dyi = irow2 - irow1 + 1;

            for (irow = irow1; irow <= irow2; irow++) {
                if (pfound == n_points)
                    G_percent(irow - irow1, irow2 - irow1, 1);

                i_n = dst->north - (irow + 0.5) * dst->ns_res;

                for (icol = icol1; icol <= icol2; icol++) {
                    if ((FLAG_GET(mask_flag, irow, icol))) {
                        continue;
                    }

                    n_vars_ic = n_vars_i;
                    Bc = B;

                    if (n_vars_i) {

                        cache_get(var_seg, (void *)varbuf, irow, icol);
                        if (Rast_is_d_null_value(varbuf)) {
                            continue;
                        }

                        if (efac) {
                            for (i = 0; i < n_vars_i; i++) {
                                if (varbuf[i] < vmin[i] ||
                                    varbuf[i] > vmax[i]) {
                                    if (!solved_tps)
                                        solved_tps = solvemat(
                                            mpnts, apnts, Bpnts, pfound + 1);
                                    if (solved_tps) {
                                        n_vars_ic = 0;
                                        Bc = Bpnts;
                                        cnt_efac++;
                                    }
                                    break;
                                }
                            }
                        }
                    }

                    i_e = dst->west + (icol + 0.5) * dst->ew_res;

                    cache_get(out_seg, (void *)&tps_out, irow, icol);

                    result = Bc[0];
                    if (n_vars_ic) {
                        for (j = 0; j < n_vars_ic; j++) {
                            result += varbuf[j] * Bc[j + 1];
                        }
                    }

                    for (i = 0; i < pfound; i++) {
                        dx = cur_pnts[i].c - i_e;
                        dy = cur_pnts[i].r - i_n;

                        dist2 = dx * dx + dy * dy;
                        dist = 0;
                        if (dist2 > 0) {
                            dist = dist2 * log(dist2) * 0.5;
                            result += Bc[1 + n_vars_ic + i] * dist;
                        }
                    }

                    dx = fabs(2.0 * icol - (icol2 + icol1)) / dxi;
                    dy = fabs(2.0 * irow - (irow2 + irow1)) / dyi;

                    dist2 = (dx * dx + dy * dy);

                    weight = exp(-dist2 * 4.0);

                    if (wmin > weight)
                        wmin = weight;
                    if (wmax < weight)
                        wmax = weight;

                    if (tps_out.wmax < weight)
                        tps_out.wmax = weight;

                    tps_out.val += result * weight;
                    tps_out.wsum += weight;
                    cache_put(out_seg, (void *)&tps_out, irow, icol);
                }
            }
        }
    }
    G_percent(1, 1, 1);

    G_debug(1, "min weight: %g", wmin);
    G_debug(1, "max weight: %g", wmax);
    G_debug(1, "Weighted average count: %u", cnt_wa);

    if (n_vars > 0 && cnt_tps) {
        double perc_no_vars;

        G_verbose_message(
            _("Number of TPS interpolations with covariables: %u"), cnt_tps_lm);
        G_verbose_message(
            _("Number of TPS interpolations without covariables: %u"), cnt_tps);
        perc_no_vars = (double)100.0 * cnt_tps / (cnt_tps + cnt_tps_lm);
        G_verbose_message(
            _("Percentage of TPS interpolations without covariables: %.2f"),
            perc_no_vars);
    }
    if (cnt_efac) {
        G_verbose_message(
            _("Number of TPS interpolations avoiding extrapolation: %u"),
            cnt_efac);
    }

    flag_destroy(pnt_flag);

    outbuf = Rast_allocate_d_buf();

    G_message(_("Writing output..."));
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        for (col = 0; col < ncols; col++) {

            if ((FLAG_GET(mask_flag, row, col))) {
                Rast_set_d_null_value(&outbuf[col], 1);
                continue;
            }

            cache_get(out_seg, (void *)&tps_out, row, col);

            if (tps_out.wsum == 0)
                Rast_set_d_null_value(&outbuf[col], 1);
            else
                outbuf[col] = tps_out.val / tps_out.wsum;
        }
        Rast_put_d_row(out_fd, outbuf);
    }
    G_percent(1, 1, 2);

    G_free(outbuf);
    flag_destroy(mask_flag);

    return 1;
}

int tps_window(struct cache *in_seg, struct cache *var_seg, int n_vars,
               struct cache *out_seg, int out_fd, char *mask_name,
               struct Cell_head *src, struct Cell_head *dst, off_t n_points,
               double regularization, double overlap, int radius,
               double lm_thresh)
{
    int ridx, cidx, row, col, nrows, ncols, src_row, src_col;
    double **m, *a, *B;
    double **mvars, *avars, *Bvars;
    int i, j;
    int palloc;
    struct tps_pnt *cur_pnts;
    double dx, dy, dist, dist2, mfactor;
    DCELL *dval, result, *outbuf, *varbuf;
    CELL *maskbuf;
    int solved, solved_tps_lm, solved_tps, solved_lm, n_vars_i;
    double rsqr;
    int pfound;
    double distmax;
    int mask_fd;
    FLAG *mask_flag, *pnt_flag;
    struct tps_out tps_out;
    double *pvar;
    double weight, dxi, dyi;
    double wmin, wmax;
    int rmin, rmax, cmin, cmax, rminp, rmaxp, cminp, cmaxp;
    int irow, irow1, irow2, icol, icol1, icol2;
    int wsize;
    unsigned int wacnt;
    double i_n, i_e;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    wsize = (radius * 2 + 1) * (radius * 2 + 1);

    palloc = wsize;
    a = G_malloc((palloc + 1 + n_vars) * sizeof(double));
    B = G_malloc((palloc + 1 + n_vars) * sizeof(double));
    m = G_malloc((palloc + 1 + n_vars) * sizeof(double *));
    for (i = 0; i < (palloc + 1 + n_vars); i++)
        m[i] = G_malloc((palloc + 1 + n_vars) * sizeof(double));
    cur_pnts = G_malloc(palloc * sizeof(struct tps_pnt));

    pvar = NULL;
    varbuf = NULL;
    mvars = NULL;
    avars = NULL;
    Bvars = NULL;
    if (n_vars) {
        pvar = G_malloc(palloc * n_vars * sizeof(double));
        cur_pnts[0].vars = pvar;
        for (i = 1; i < palloc; i++)
            cur_pnts[i].vars = cur_pnts[i - 1].vars + n_vars;

        varbuf = G_malloc(n_vars * sizeof(DCELL));

        avars = G_malloc((1 + n_vars) * sizeof(double));
        Bvars = G_malloc((1 + n_vars) * sizeof(double));
        mvars = G_malloc((1 + n_vars) * sizeof(double *));
        for (i = 0; i < (1 + n_vars); i++)
            mvars[i] = G_malloc((1 + n_vars) * sizeof(double));
    }

    dval = G_malloc((1 + n_vars) * sizeof(DCELL));

    mask_flag = flag_create(nrows, ncols);

    maskbuf = NULL;
    if (mask_name) {
        G_message("Loading mask map...");
        mask_fd = Rast_open_old(mask_name, "");
        maskbuf = Rast_allocate_c_buf();

        for (row = 0; row < nrows; row++) {
            Rast_get_c_row(mask_fd, maskbuf, row);
            for (col = 0; col < ncols; col++) {
                if (Rast_is_c_null_value(&maskbuf[col]) || maskbuf[col] == 0)
                    FLAG_SET(mask_flag, row, col);
            }
        }
        Rast_close(mask_fd);
        G_free(maskbuf);
        maskbuf = NULL;
    }

    G_message(_("Analyzing input ..."));
    pnt_flag = flag_create(src->rows, src->cols);

    rminp = src->rows;
    rmaxp = 0;
    cminp = src->cols;
    cmaxp = 0;
    for (row = 0; row < src->rows; row++) {
        G_percent(row, src->rows, 2);

        for (col = 0; col < src->cols; col++) {
            cache_get(in_seg, (void *)dval, row, col);
            if (!Rast_is_d_null_value(dval)) {
                FLAG_SET(pnt_flag, row, col);
                if (rminp > row)
                    rminp = row;
                if (rmaxp < row)
                    rmaxp = row;
                if (cminp > col)
                    cminp = col;
                if (cmaxp < col)
                    cmaxp = col;
            }
        }
    }
    rminp = row_src2dst(rminp, src, dst);
    rmaxp = row_src2dst(rmaxp, src, dst);
    cminp = col_src2dst(cminp, src, dst);
    cmaxp = col_src2dst(cmaxp, src, dst);
    G_percent(1, 1, 2);

    G_message(_("Initializing output ..."));
    tps_out.val = 0;
    tps_out.wsum = 0;
    tps_out.wmax = 0;
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        for (col = 0; col < ncols; col++) {
            if (cache_put(out_seg, (void *)&tps_out, row, col) == NULL)
                G_fatal_error(_("Unable to write to temporary file"));
        }
    }
    G_percent(1, 1, 2);

    G_message(_("Moving window TPS interpolation with %ld points..."),
              n_points);

    wmin = 10;
    wmax = 0;
    wacnt = 0;

    if (overlap > 1.0)
        overlap = 1.0;
    if (overlap < 0.0)
        overlap = 0.0;
    /* keep in sync with weight calculation below */
    overlap = exp((overlap - 1.0) * 8.0);

    for (ridx = 0; ridx < nrows; ridx++) {

        G_percent(ridx, nrows, 1);

        row = (ridx >> 1);
        if (ridx & 1)
            row = nrows - 1 - row;

        src_row = row_src2dst(row, dst, src);

        for (cidx = 0; cidx < ncols; cidx++) {

            col = (cidx >> 1);
            if (cidx & 1)
                col = ncols - 1 - col;

            if ((FLAG_GET(mask_flag, row, col))) {
                continue;
            }

            if (n_vars) {

                cache_get(var_seg, (void *)varbuf, row, col);

                if (Rast_is_d_null_value(varbuf))
                    continue;
            }

            cache_get(out_seg, (void *)&tps_out, row, col);
            if (tps_out.wmax > overlap)
                continue;

            solved = 0;
            pfound = 0;
            src_col = col_src2dst(col, dst, src);

            /* collect points within moving window */
            rmin = src->rows;
            rmax = 0;
            cmin = src->cols;
            cmax = 0;
            pfound = window_pnts(pnt_flag, src, cur_pnts, radius, src_row,
                                 src_col, &rmin, &rmax, &cmin, &cmax, &distmax);

            /* sort points */
            qsort(cur_pnts, pfound, sizeof(struct tps_pnt), cmp_pnts);

            load_tps_pnts(in_seg, dval, n_vars, cur_pnts, pfound, src, dst,
                          regularization, m, a, mvars, avars, NULL, NULL, NULL,
                          NULL);

            n_vars_i = n_vars;
            if (pfound > 2) {
                /* solve */
                solved_tps_lm = solved_tps = 0;

                if (n_vars) {

                    solved_tps_lm = solvemat(m, a, B, pfound + 1 + n_vars);

                    if (solved_tps_lm && lm_thresh > 0) {

                        solved_lm = solvemat(mvars, avars, Bvars, 1 + n_vars);
                        if (!solved_lm) {
                            G_debug(1,
                                    "LM with covariables not working at row "
                                    "%d, col %d",
                                    row, col);

                            solved_tps_lm = 0;
                        }
                        else {
                            rsqr = lm_rsqr(in_seg, n_vars, src, cur_pnts,
                                           pfound, B);

                            if (rsqr < lm_thresh) {
                                for (i = 1; i <= n_vars; i++) {
                                    if (fabs(B[i]) > fabs(5 * Bvars[i])) {
                                        G_debug(
                                            0, "LM B%d is %g but TPS B%d is %g",
                                            i, Bvars[i], i, B[i]);
                                        solved_tps_lm = 0;
                                    }
                                }
                            }
                        }
                    }

                    if (!solved_tps_lm) {
                        n_vars_i = 0;
                        for (i = 0; i < pfound; i++) {
                            cur_pnts[i].r = (int)((src->north - cur_pnts[i].r) /
                                                  src->ns_res);
                            cur_pnts[i].c = (int)((cur_pnts[i].c - src->west) /
                                                  src->ew_res);
                        }
                        load_tps_pnts(in_seg, dval, 0, cur_pnts, pfound, src,
                                      dst, regularization, m, a, NULL, NULL,
                                      NULL, NULL, NULL, NULL);
                    }
                }

                if (!solved_tps_lm) {
                    solved_tps = solvemat(m, a, B, pfound + 1);
                }

                solved = (solved_tps_lm | solved_tps);
            }

            if (!solved) {
                if (pfound > 0) {
                    /* weighted average */

                    G_debug(1, "Weighted average");

                    result = interp_wa(in_seg, dval, cur_pnts, pfound, row, col,
                                       src, dst, distmax, &weight);

                    /* weight according to distance to nearest point */
                    if (tps_out.wmax < weight)
                        tps_out.wmax = weight;

                    tps_out.val += result * weight;
                    tps_out.wsum += weight;
                    cache_put(out_seg, (void *)&tps_out, row, col);

                    wacnt++;
                }
                continue;
            }

            /* must be <= 0.5 */
            mfactor = 0.0;
            /* min: 0
             * max: 0.5
             * 1 - 1 / d: -> 0 for dense spacing
             *            1 for sparse points
             */

            rmin = row_src2dst(rmin, src, dst);
            rmax = row_src2dst(rmax, src, dst);
            cmin = col_src2dst(cmin, src, dst);
            cmax = col_src2dst(cmax, src, dst);

            irow1 = rmin + (int)((rmax - rmin) * mfactor);
            irow2 = rmax - (int)((rmax - rmin) * mfactor);
            icol1 = cmin + (int)((cmax - cmin) * mfactor);
            icol2 = cmax - (int)((cmax - cmin) * mfactor);

            if (irow1 > row) {
                irow2 -= irow1 - row;
                irow1 = row;
            }
            if (irow2 < row) {
                irow1 += row - irow2;
                irow2 = row;
            }
            if (icol1 > col) {
                icol2 -= icol1 - col;
                icol1 = col;
            }
            if (icol2 < col) {
                icol1 += col - icol2;
                icol2 = col;
            }

            if (rmin == rminp)
                irow1 = 0;
            if (rmax == rmaxp)
                irow2 = nrows - 1;
            if (cmin == cminp)
                icol1 = 0;
            if (cmax == cmaxp)
                icol2 = ncols - 1;

            if (irow1 < 0)
                irow1 = 0;
            if (irow2 > nrows - 1)
                irow2 = nrows - 1;
            if (icol1 < 0)
                icol1 = 0;
            if (icol2 > ncols - 1)
                icol2 = ncols - 1;

            dxi = icol2 - icol1 + 1;
            dyi = irow2 - irow1 + 1;

            for (irow = irow1; irow <= irow2; irow++) {

                i_n = dst->north - (irow + 0.5) * dst->ns_res;

                for (icol = icol1; icol <= icol2; icol++) {
                    if ((FLAG_GET(mask_flag, irow, icol))) {
                        continue;
                    }

                    if (n_vars_i) {

                        cache_get(var_seg, (void *)varbuf, irow, icol);
                        if (Rast_is_d_null_value(varbuf)) {
                            continue;
                        }
                    }

                    i_e = dst->west + (icol + 0.5) * dst->ew_res;

                    cache_get(out_seg, (void *)&tps_out, irow, icol);

                    j = 0;

                    result = B[0];
                    if (n_vars_i) {
                        for (j = 0; j < n_vars; j++) {
                            result += varbuf[j] * B[j + 1];
                        }
                    }

                    for (i = 0; i < pfound; i++) {

                        dx = cur_pnts[i].c - i_e;
                        dy = cur_pnts[i].r - i_n;

                        dist2 = dx * dx + dy * dy;
                        dist = 0;
                        if (dist2 > 0) {
                            dist = dist2 * log(dist2) * 0.5;
                            result += B[1 + n_vars + i] * dist;
                        }
                    }

                    dx = fabs(2.0 * icol - (icol2 + icol1)) / dxi;
                    dy = fabs(2.0 * irow - (irow2 + irow1)) / dyi;

                    dist2 = (dx * dx + dy * dy);

                    weight = exp(-dist2 * 4.0);

                    if (wmin > weight)
                        wmin = weight;
                    if (wmax < weight)
                        wmax = weight;

                    if (tps_out.wmax < weight)
                        tps_out.wmax = weight;

                    tps_out.val += result * weight;
                    tps_out.wsum += weight;
                    cache_put(out_seg, (void *)&tps_out, irow, icol);
                }
            }
        }
    }
    G_percent(1, 1, 1);

    G_debug(1, "wmin: %g", wmin);
    G_debug(1, "wmax: %g", wmax);
    G_debug(1, "wacnt: %u", wacnt);

    flag_destroy(pnt_flag);

    outbuf = Rast_allocate_d_buf();

    G_message(_("Writing output..."));
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        for (col = 0; col < ncols; col++) {

            if ((FLAG_GET(mask_flag, row, col))) {
                Rast_set_d_null_value(&outbuf[col], 1);
                continue;
            }

            cache_get(out_seg, (void *)&tps_out, row, col);

            if (tps_out.wsum == 0)
                Rast_set_d_null_value(&outbuf[col], 1);
            else
                outbuf[col] = tps_out.val / tps_out.wsum;
        }
        Rast_put_d_row(out_fd, outbuf);
    }
    G_percent(1, 1, 2);

    G_free(outbuf);
    flag_destroy(mask_flag);

    return 1;
}
