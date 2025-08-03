#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include <grass/kdtree.h>
#include <grass/segment.h>
#include "tps.h"
#include "flag.h"
#include "rclist.h"

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

        if (fabs(pivot) < GRASS_EPSILON) {
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

static int load_tps_pnts(struct tps_pnt *pnts, int n_points, int n_vars,
                         double regularization, double **m, double *a)
{
    int i, j, k;
    double dx, dy, dist, dist2, distsum, reg;

    for (i = 0; i <= n_vars; i++) {
        a[i] = 0.0;
        for (j = 0; j <= n_vars; j++) {
            m[i][j] = m[j][i] = 0.0;
        }
    }

    distsum = 0;
    for (i = 0; i < n_points; i++) {
        /* global */
        a[i + 1 + n_vars] = pnts[i].val;
        m[0][i + 1 + n_vars] = m[i + 1 + n_vars][0] = 1.0;

        for (j = 0; j < n_vars; j++) {
            m[j + 1][i + 1 + n_vars] = m[i + 1 + n_vars][j + 1] =
                pnts[i].vars[j];
        }

        /* TPS */
        for (k = 0; k <= i; k++) {
            dx = (pnts[i].c - pnts[k].c) * 2.0;
            dy = (pnts[i].r - pnts[k].r) * 2.0;

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

    return 1;
}

int global_tps(int out_fd, int *var_fd, int n_vars, int mask_fd,
               struct tps_pnt *pnts, int n_points, double regularization)
{
    int row, col, nrows, ncols;
    double **m, *a, *B;
    int i, j;
    int nalloc;
    double dx, dy, dist, dist2;
    DCELL **dbuf, result, *outbuf;
    CELL *maskbuf;

    G_message(_("Global TPS interpolation with %d points..."), n_points);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* alloc */
    outbuf = Rast_allocate_d_buf();
    nalloc = n_points;
    a = G_malloc((nalloc + 1 + n_vars) * sizeof(double));
    B = G_malloc((nalloc + 1 + n_vars) * sizeof(double));
    m = G_malloc((nalloc + 1 + n_vars) * sizeof(double *));
    for (i = 0; i < (nalloc + 1 + n_vars); i++)
        m[i] = G_malloc((nalloc + 1 + n_vars) * sizeof(double));

    dbuf = NULL;
    if (n_vars) {
        dbuf = G_malloc(n_vars * sizeof(DCELL *));
        for (i = 0; i < n_vars; i++) {
            dbuf[i] = Rast_allocate_d_buf();
        }
    }

    maskbuf = NULL;
    if (mask_fd >= 0)
        maskbuf = Rast_allocate_c_buf();

    /* load points to matrix */
    load_tps_pnts(pnts, n_points, n_vars, regularization, m, a);

    /* solve */
    if (!solvemat(m, a, B, n_points + 1 + n_vars))
        G_fatal_error(_("Matrix is unsolvable"));

    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        for (j = 0; j < n_vars; j++)
            Rast_get_d_row(var_fd[j], dbuf[j], row);
        if (maskbuf)
            Rast_get_c_row(mask_fd, maskbuf, row);

        for (col = 0; col < ncols; col++) {

            if (maskbuf &&
                (Rast_is_c_null_value(&maskbuf[col]) || maskbuf[col] == 0)) {

                Rast_set_d_null_value(&outbuf[col], 1);

                continue;
            }

            if (n_vars) {
                int isnull = 0;

                for (j = 0; j < n_vars; j++) {
                    if (Rast_is_d_null_value(&dbuf[j][col])) {
                        isnull = 1;
                        break;
                    }
                }
                if (isnull) {
                    Rast_set_d_null_value(&outbuf[col], 1);
                    continue;
                }
            }

            result = B[0];
            for (j = 0; j < n_vars; j++)
                result += dbuf[j][col] * B[j + 1];

            for (i = 0; i < n_points; i++) {
                dx = (pnts[i].c - col) * 2.0;
                dy = (pnts[i].r - row) * 2.0;

                dist2 = dx * dx + dy * dy;
                dist = 0;
                if (dist2 > 0) {
                    dist = dist2 * log(dist2) * 0.5;
                    result += B[1 + n_vars + i] * dist;
                }
            }
            outbuf[col] = result;
        }
        Rast_put_d_row(out_fd, outbuf);
    }
    G_percent(1, 1, 1);

    if (n_vars) {
        for (i = 0; i < n_vars; i++) {
            G_free(dbuf[i]);
        }
        G_free(dbuf);
    }
    if (maskbuf)
        G_free(maskbuf);
    G_free(outbuf);

    return 1;
}

static int cmp_rc(const void *first, const void *second)
{
    struct rc *a = (struct rc *)first, *b = (struct rc *)second;

    if (a->row == b->row)
        return (a->col - b->col);

    return (a->row - b->row);
}

static int bfs_search(SEGMENT *p_seg, FLAG *mask_flag, int *bfsid, int row,
                      int col, int max_points, double min_dist, int rmin,
                      int rmax, int cmin, int cmax)
{
    int nrows, ncols, rown, coln;
    int nextr[8] = {-1, -1, -1, 0, 0, 1, 1, 1};
    int nextc[8] = {-1, 0, 1, -1, 1, -1, 0, 1};
    int n, found;
    int pid;
    struct rc next, ngbr_rc;
    struct rclist rilist;
    struct RB_TREE *visited;
    double dx, dy, dist;

    visited = rbtree_create(cmp_rc, sizeof(struct rc));
    ngbr_rc.row = row;
    ngbr_rc.col = col;
    rbtree_insert(visited, &ngbr_rc);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

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
            if ((FLAG_GET(mask_flag, rown, coln)))
                continue;

            ngbr_rc.row = rown;
            ngbr_rc.col = coln;

            if (rbtree_find(visited, &ngbr_rc))
                continue;

            rbtree_insert(visited, &ngbr_rc);

            Segment_get(p_seg, (void *)&pid, rown, coln);

            if (pid < 0) {
                rclist_add(&rilist, rown, coln);
            }
            else if (rown >= rmin && rown <= rmax && coln >= cmin &&
                     coln <= cmax) {
                dx = coln - col;
                dy = rown - row;

                dist = dx * dx + dy * dy;

                if (dist > min_dist) {
                    bfsid[found] = pid;
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
    rbtree_destroy(visited);

    return found;
}

int local_tps(int out_fd, int *var_fd, int n_vars, int mask_fd,
              struct tps_pnt *pnts, int n_points, int min_points,
              double regularization, double overlap, double pthin,
              int clustered, double segs_mb)
{
    int ridx, cidx, row, col, nrows, ncols;
    double **m, *a, *B;
    int i, j;
    int kdalloc, palloc, n_cur_points;
    struct tps_pnt *cur_pnts;
    double dx, dy, dist, dist2, mfactor;
    DCELL **dbuf, result, *outbuf, *varbuf;
    CELL *maskbuf;
    int solved;
    struct kdtree *kdt;
    double c[2];
    int *kduid, kdfound;
    double *kddist;
    int *bfsid, bfsfound, pfound;

    FLAG *mask_flag;
    SEGMENT var_seg, out_seg, p_seg;
    int nsegs;
    double segsize;
    int varsize;
    struct tps_out {
        double val;
        double wsum;
        double wmax;
    } tps_out;
    double weight, dxi, dyi;
    double wmin, wmax;
    int rmin, rmax, cmin, cmax, rminp, rmaxp, cminp, cmaxp;
    int irow, irow1, irow2, icol, icol1, icol2;
    int nskipped;
    double pthin2;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    kdalloc = palloc = min_points;
    a = G_malloc((palloc + 1 + n_vars) * sizeof(double));
    B = G_malloc((palloc + 1 + n_vars) * sizeof(double));
    m = G_malloc((palloc + 1 + n_vars) * sizeof(double *));
    for (i = 0; i < (palloc + 1 + n_vars); i++)
        m[i] = G_malloc((palloc + 1 + n_vars) * sizeof(double));
    cur_pnts = G_malloc(palloc * 5 * sizeof(struct tps_pnt));
    kduid = G_malloc(palloc * sizeof(int));
    kddist = G_malloc(palloc * sizeof(double));

    bfsid = G_malloc(min_points * sizeof(int));

    mask_flag = flag_create(nrows, ncols);

    maskbuf = NULL;
    if (mask_fd >= 0) {
        G_message("Loading mask map...");
        maskbuf = Rast_allocate_c_buf();

        for (row = 0; row < nrows; row++) {
            Rast_get_c_row(mask_fd, maskbuf, row);
            for (col = 0; col < ncols; col++) {
                if (Rast_is_c_null_value(&maskbuf[col]) || maskbuf[col] == 0)
                    FLAG_SET(mask_flag, row, col);
            }
        }
        G_free(maskbuf);
        maskbuf = NULL;
    }

    /* create and init SEG structs */
    varsize = n_vars * sizeof(DCELL);
    segsize = (double)64 * 64 *
              (sizeof(struct tps_out) + varsize + clustered * sizeof(int));
    nsegs = 1024. * 1024. * segs_mb / segsize;

    if (Segment_open(&out_seg, G_tempfile(), nrows, ncols, 64, 64,
                     sizeof(struct tps_out), nsegs) != 1) {
        G_fatal_error("Unable to create input temporary files");
    }

    dbuf = NULL;
    varbuf = NULL;
    if (n_vars) {
        dbuf = G_malloc(n_vars * sizeof(DCELL *));
        varbuf = G_malloc(n_vars * sizeof(DCELL));
        for (i = 0; i < n_vars; i++) {
            dbuf[i] = Rast_allocate_d_buf();
        }

        if (Segment_open(&var_seg, G_tempfile(), nrows, ncols, 64, 64, varsize,
                         nsegs) != 1) {
            G_fatal_error("Unable to create input temporary files");
        }
    }

    if (clustered) {
        G_message("Creating temporary point map...");

        if (Segment_open(&p_seg, G_tempfile(), nrows, ncols, 64, 64,
                         sizeof(int), nsegs) != 1) {
            G_fatal_error("Unable to create input temporary files");
        }
        i = -1;
        for (row = 0; row < nrows; row++) {
            G_percent(row, nrows, 2);

            for (col = 0; col < ncols; col++) {
                if (Segment_put(&p_seg, (void *)&i, row, col) != 1)
                    G_fatal_error(_("Unable to write to temporary file"));
            }
        }
        for (i = 0; i < n_points; i++) {
            G_percent(i, n_points, 2);
            if (pnts[i].r < 0 || pnts[i].r >= nrows || pnts[i].c < 0 ||
                pnts[i].c >= ncols)
                continue;
            if (Segment_put(&p_seg, (void *)&i, pnts[i].r, pnts[i].c) != 1)
                G_fatal_error(_("Unable to write to temporary file"));
        }
    }

    G_message(_("Initializing output ..."));
    tps_out.val = 0;
    tps_out.wsum = 0;
    tps_out.wmax = 0;
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);
        if (n_vars) {
            for (j = 0; j < n_vars; j++)
                Rast_get_d_row(var_fd[j], dbuf[j], row);
        }

        for (col = 0; col < ncols; col++) {
            if (n_vars) {
                for (j = 0; j < n_vars; j++) {
                    varbuf[j] = dbuf[j][col];
                }
                if (Segment_put(&var_seg, (void *)varbuf, row, col) != 1)
                    G_fatal_error(_("Unable to write to temporary file"));
            }
            if (Segment_put(&out_seg, (void *)&tps_out, row, col) != 1)
                G_fatal_error(_("Unable to write to temporary file"));
        }
    }
    if (n_vars) {
        for (j = 0; j < n_vars; j++)
            G_free(dbuf[j]);
        G_free(dbuf);
        dbuf = NULL;
    }
    G_percent(1, 1, 2);

    /* create k-d tree */
    G_message(_("Creating search index ..."));
    pthin2 = pthin * pthin;
    if (pthin > 0)
        G_message(_("Thinning points with minimum distance %g"), pthin);
    kdt = kdtree_create(2, NULL);
    nskipped = 0;
    rminp = nrows;
    rmaxp = 0;
    cminp = ncols;
    cmaxp = 0;
    for (i = 0; i < n_points; i++) {
        G_percent(i, n_points, 2);

        c[0] = pnts[i].c;
        c[1] = pnts[i].r;

        if (pthin > 0 && i > 0) {
            kdfound = kdtree_knn(kdt, c, kduid, kddist, 1, NULL);
            if (kdfound && kddist[0] <= pthin2) {
                nskipped++;
                continue;
            }
        }

        kdtree_insert(kdt, c, i, 0);

        if (rminp > pnts[i].r)
            rminp = pnts[i].r;
        if (rmaxp < pnts[i].r)
            rmaxp = pnts[i].r;
        if (cminp > pnts[i].c)
            cminp = pnts[i].c;
        if (cmaxp < pnts[i].c)
            cmaxp = pnts[i].c;
    }
    kdtree_optimize(kdt, 2);
    G_percent(1, 1, 2);

    if (nskipped) {
        G_message(_("%d of %d points were thinned out"), nskipped, n_points);
        n_points -= nskipped;
    }

    G_message(_("Local TPS interpolation with %d points..."), n_points);

    wmin = 10;
    wmax = 0;

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

        for (cidx = 0; cidx < ncols; cidx++) {

            col = (cidx >> 1);
            if (cidx & 1)
                col = ncols - 1 - col;

            if ((FLAG_GET(mask_flag, row, col))) {
                continue;
            }

            if (n_vars) {
                int isnull = 0;

                Segment_get(&var_seg, (void *)varbuf, row, col);
                for (j = 0; j < n_vars; j++) {
                    if (Rast_is_d_null_value(&varbuf[j])) {
                        isnull = 1;
                        break;
                    }
                }
                if (isnull)
                    continue;
            }

            Segment_get(&out_seg, (void *)&tps_out, row, col);
            if (tps_out.wmax > overlap)
                continue;

            solved = 0;
            n_cur_points = 0;
            kdfound = 0;
            c[0] = col;
            c[1] = row;

            while (!solved) {

                /* increase points if unsolvable */
                n_cur_points += min_points;
                if (n_cur_points > n_points)
                    n_cur_points = n_points;

                /* alloc */
                if (kdalloc < n_cur_points) {
                    G_free(kduid);
                    G_free(kddist);
                    G_free(bfsid);
                    G_free(cur_pnts);

                    kdalloc = n_cur_points;

                    kduid = G_malloc(kdalloc * sizeof(int));
                    kddist = G_malloc(kdalloc * sizeof(double));
                    bfsid = G_malloc(kdalloc * sizeof(int));
                    cur_pnts = G_malloc(kdalloc * 5 * sizeof(struct tps_pnt));
                }

                /* collect nearest neighbors */
                kdfound = kdtree_knn(kdt, c, kduid, kddist, n_cur_points, NULL);

                /* load points to matrix */
                rmin = nrows;
                rmax = 0;
                cmin = ncols;
                cmax = 0;
                for (i = 0; i < kdfound; i++) {
                    cur_pnts[i] = pnts[kduid[i]];
                    if (rmin > cur_pnts[i].r)
                        rmin = cur_pnts[i].r;
                    if (rmax < cur_pnts[i].r)
                        rmax = cur_pnts[i].r;
                    if (cmin > cur_pnts[i].c)
                        cmin = cur_pnts[i].c;
                    if (cmax < cur_pnts[i].c)
                        cmax = cur_pnts[i].c;
                }
                pfound = kdfound;

                if (clustered) {
                    /* collect points with breadth-first search
                     * min dist must be > max dist of nearest neighbors */

                    /* qrt1: 0, row, col + 1, ncols - 1 */
                    if (rminp <= row && cmaxp > col) {
                        bfsfound =
                            bfs_search(&p_seg, mask_flag, bfsid, row, col,
                                       n_cur_points / 2, kddist[kdfound - 1], 0,
                                       row, col + 1, ncols - 1);

                        if (bfsfound == 0)
                            G_debug(4, "No BFS points for NE quadrant");

                        for (i = 0; i < bfsfound; i++) {
                            cur_pnts[pfound + i] = pnts[bfsid[i]];
                        }
                        pfound += bfsfound;
                    }

                    /* qrt2: 0, row - 1, 0, col */
                    if (rminp < row && cminp <= col) {
                        bfsfound =
                            bfs_search(&p_seg, mask_flag, bfsid, row, col,
                                       n_cur_points / 2, kddist[kdfound - 1], 0,
                                       row - 1, 0, col);

                        if (bfsfound == 0)
                            G_debug(4, "No BFS points for NW quadrant");

                        for (i = 0; i < bfsfound; i++) {
                            cur_pnts[pfound + i] = pnts[bfsid[i]];
                        }
                        pfound += bfsfound;
                    }

                    /* qrt3: row, nrows - 1, 0, col - 1 */
                    if (rmaxp >= row && cminp < col) {
                        bfsfound =
                            bfs_search(&p_seg, mask_flag, bfsid, row, col,
                                       n_cur_points / 2, kddist[kdfound - 1],
                                       row, nrows - 1, 0, col - 1);

                        if (bfsfound == 0)
                            G_debug(4, "No BFS points for SW quadrant");

                        for (i = 0; i < bfsfound; i++) {
                            cur_pnts[pfound + i] = pnts[bfsid[i]];
                        }
                        pfound += bfsfound;
                    }

                    /* qrt4: row + 1, nrows - 1, col, ncols - 1 */
                    if (rmaxp > row && cmaxp >= col) {
                        bfsfound =
                            bfs_search(&p_seg, mask_flag, bfsid, row, col,
                                       n_cur_points / 2, kddist[kdfound - 1],
                                       row + 1, nrows - 1, col, ncols - 1);

                        if (bfsfound == 0)
                            G_debug(4, "No BFS points for SE quadrant");

                        for (i = 0; i < bfsfound; i++) {
                            cur_pnts[pfound + i] = pnts[bfsid[i]];
                        }
                        pfound += bfsfound;
                    }
                }

                if (palloc < pfound) {
                    G_free(a);
                    G_free(B);
                    for (i = 0; i < (palloc + 1 + n_vars); i++)
                        G_free(m[i]);
                    G_free(m);

                    palloc = pfound;
                    a = G_malloc((palloc + 1 + n_vars) * sizeof(double));
                    B = G_malloc((palloc + 1 + n_vars) * sizeof(double));
                    m = G_malloc((palloc + 1 + n_vars) * sizeof(double *));
                    for (i = 0; i < (palloc + 1 + n_vars); i++)
                        m[i] = G_malloc((palloc + 1 + n_vars) * sizeof(double));
                }

                /* sort points */
                /* qsort(cur_pnts, kdfound, sizeof(struct tps_pnt), cmp_pnts);
                 */

                load_tps_pnts(cur_pnts, pfound, n_vars, regularization, m, a);

                /* solve */
                solved = solvemat(m, a, B, pfound + 1 + n_vars);

                if (!solved && n_cur_points == n_points)
                    G_fatal_error(_("Matrix is unsolvable"));
            }

            rmin = nrows;
            rmax = 0;
            cmin = ncols;
            cmax = 0;
            for (i = 0; i < kdfound; i++) {
                if (rmin > cur_pnts[i].r)
                    rmin = cur_pnts[i].r;
                if (rmax < cur_pnts[i].r)
                    rmax = cur_pnts[i].r;
                if (cmin > cur_pnts[i].c)
                    cmin = cur_pnts[i].c;
                if (cmax < cur_pnts[i].c)
                    cmax = cur_pnts[i].c;
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
                    mfactoradj = pow((1 - dmin / dmax), 2.0) * 0.5;
                    G_debug(1, "adjusted mfactor: %g", mfactoradj);
                }
                mfactor = mfactoradj;
            }

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
                for (icol = icol1; icol <= icol2; icol++) {
                    if ((FLAG_GET(mask_flag, irow, icol))) {
                        continue;
                    }

                    if (n_vars) {
                        int isnull = 0;

                        Segment_get(&var_seg, (void *)varbuf, irow, icol);
                        for (j = 0; j < n_vars; j++) {
                            if (Rast_is_d_null_value(&varbuf[j])) {
                                isnull = 1;
                                break;
                            }
                        }
                        if (isnull)
                            continue;
                    }

                    Segment_get(&out_seg, (void *)&tps_out, irow, icol);

                    result = B[0];
                    if (n_vars) {
                        Segment_get(&var_seg, (void *)varbuf, irow, icol);
                        for (j = 0; j < n_vars; j++)
                            result += varbuf[j] * B[j + 1];
                    }

                    for (i = 0; i < pfound; i++) {
                        dx = (cur_pnts[i].c - icol) * 2.0;
                        dy = (cur_pnts[i].r - irow) * 2.0;

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
                    Segment_put(&out_seg, (void *)&tps_out, irow, icol);
                }
            }
        }
    }
    G_percent(1, 1, 1);

    G_debug(1, "wmin: %g", wmin);
    G_debug(1, "wmax: %g", wmax);

    if (n_vars)
        Segment_close(&var_seg);

    if (clustered)
        Segment_close(&p_seg);

    outbuf = Rast_allocate_d_buf();

    G_message(_("Writing output..."));
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        for (col = 0; col < ncols; col++) {

            if ((FLAG_GET(mask_flag, row, col))) {
                Rast_set_d_null_value(&outbuf[col], 1);
                continue;
            }

            Segment_get(&out_seg, (void *)&tps_out, row, col);

            if (tps_out.wsum == 0)
                Rast_set_d_null_value(&outbuf[col], 1);
            else
                outbuf[col] = tps_out.val / tps_out.wsum;
        }
        Rast_put_d_row(out_fd, outbuf);
    }
    G_percent(1, 1, 2);

    G_free(outbuf);
    Segment_close(&out_seg);

    return 1;
}
