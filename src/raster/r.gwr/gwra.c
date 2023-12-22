#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>
#include "rclist.h"
#include "pavl.h"
#include "local_proto.h"
#include "gwr.h"

/* geographically weighted regression:
 * estimate coefficients for given cell */

struct gwr_pnt {
    int r, c; /* row, col in target window */
};

static int cmp_rc(const void *first, const void *second, void *avl_param)
{
    struct rc *a = (struct rc *)first, *b = (struct rc *)second;

    if (a->row == b->row)
        return (a->col - b->col);

    return (a->row - b->row);
}

static int cmp_pnts(const void *first, const void *second)
{
    struct gwr_pnt *a = (struct gwr_pnt *)first;
    struct gwr_pnt *b = (struct gwr_pnt *)second;

    if (a->r == b->r)
        return (a->c - b->c);

    return (a->r - b->r);
}

static void avl_free_item(void *avl_item, void *avl_param)
{
    G_free(avl_item);
}

static int bfs_search(FLAG *null_flag, struct gwr_pnt *cur_pnts, int max_points,
                      int row, int col, double *distmax)
{
    int nrows, ncols, rown, coln;
    int nextr[8] = {0, -1, 0, 1, -1, -1, 1, 1};
    int nextc[8] = {1, 0, -1, 0, 1, -1, -1, 1};
    int n, found;
    struct rc next, ngbr_rc, *pngbr_rc;
    struct rclist rilist;
    struct pavl_table *visited;
    double dx, dy, dist;

    ngbr_rc.row = row;
    ngbr_rc.col = col;

    visited = pavl_create(cmp_rc, NULL, NULL);
    pngbr_rc = G_malloc(sizeof(struct rc));
    *pngbr_rc = ngbr_rc;
    pavl_insert(visited, pngbr_rc);
    pngbr_rc = NULL;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    found = 0;
    *distmax = 0.0;

    if (FLAG_GET(null_flag, row, col)) {
        /* add to cur_pnts */
        cur_pnts[found].r = row;
        cur_pnts[found].c = col;
        found++;
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

            if (pngbr_rc == NULL)
                pngbr_rc = G_malloc(sizeof(struct rc));

            *pngbr_rc = ngbr_rc;

            if (pavl_insert(visited, pngbr_rc) != NULL) {
                continue;
            }

            pngbr_rc = NULL;

            rclist_add(&rilist, rown, coln);

            if (FLAG_GET(null_flag, rown, coln)) {

                dx = coln - col;
                dy = rown - row;

                dist = dx * dx + dy * dy;

                if (*distmax < dist)
                    *distmax = dist;

                cur_pnts[found].r = rown;
                cur_pnts[found].c = coln;
                found++;
            }

            if (found == max_points)
                break;
        }
        if (found == max_points)
            break;
    } while (rclist_drop(&rilist, &next)); /* while there are cells to check */

    rclist_destroy(&rilist);
    if (pngbr_rc)
        G_free(pngbr_rc);
    pavl_destroy(visited, avl_free_item);

    return found;
}

int gwra(SEGMENT *in_seg, FLAG *null_flag, int ninx, int rr, int cc, int npnts,
         DCELL *est, double **B0)
{
    int r, c, n, nfound;
    int i, j, k;
    double bw, maxdist2, dist2, w;
    static DCELL *xval = NULL, *seg_val = NULL;
    DCELL yval;
    int count, isnull, solved;
    static int npnts_alloc = 0;
    static struct gwr_pnt *cur_pnts = NULL;
    /* OLS */
    static double **a = NULL;
    static double **B = NULL;
    static struct MATRIX *m_all = NULL;
    struct MATRIX *m;

    if (!xval) {
        xval = G_malloc((ninx + 1) * sizeof(DCELL));
        xval[0] = 1.;
        seg_val = G_malloc((ninx + 1) * sizeof(DCELL));
    }

    if (!m_all) {
        m_all = (struct MATRIX *)G_malloc((ninx + 1) * sizeof(struct MATRIX));
        a = (double **)G_malloc((ninx + 1) * sizeof(double *));
        B = (double **)G_malloc((ninx + 1) * sizeof(double *));

        m = &(m_all[0]);
        m->n = ninx + 1;
        m->v = (double **)G_malloc(m->n * sizeof(double));
        m->v[0] = (double *)G_malloc(m->n * m->n * sizeof(double));
        for (i = 1; i < m->n; i++) {
            m->v[i] = m->v[i - 1] + m->n;
        }

        a[0] = (double *)G_malloc(m->n * sizeof(double));
        B[0] = (double *)G_malloc(m->n * sizeof(double));

        for (k = 1; k <= ninx; k++) {
            m = &(m_all[k]);
            m->n = ninx;
            m->v = (double **)G_malloc(m->n * sizeof(double *));
            m->v[0] = (double *)G_malloc(m->n * m->n * sizeof(double));
            for (i = 1; i < m->n; i++) {
                m->v[i] = m->v[i - 1] + m->n;
            }
            a[k] = (double *)G_malloc(m->n * sizeof(double));
            B[k] = (double *)G_malloc(m->n * sizeof(double));
        }
    }

    if (npnts_alloc < npnts) {
        if (cur_pnts)
            G_free(cur_pnts);
        npnts_alloc = npnts;
        cur_pnts = G_malloc(sizeof(struct gwr_pnt) * npnts_alloc);
    }

    for (k = 0; k <= ninx; k++) {
        m = &(m_all[k]);
        for (i = 0; i < m->n; i++) {
            for (j = i; j < m->n; j++)
                M(m, i, j) = 0.0;
            a[k][i] = 0.0;
            B[k][i] = 0.0;
        }
    }

    Rast_set_d_null_value(est, ninx + 1);
    if (B0)
        *B0 = NULL;

    /* first pass: collect values */
    nfound = bfs_search(null_flag, cur_pnts, npnts, rr, cc, &maxdist2);

    qsort(cur_pnts, nfound, sizeof(struct gwr_pnt), cmp_pnts);

    /* bandwidth */
    bw = sqrt(maxdist2);

    /* second pass: load values */
    count = 0;
    for (n = 0; n < nfound; n++) {

        r = cur_pnts[n].r;
        c = cur_pnts[n].c;

        Segment_get(in_seg, (void *)seg_val, r, c);

        isnull = 0;
        for (i = 0; i < ninx; i++) {
            xval[i + 1] = seg_val[i];
            if (Rast_is_d_null_value(&(xval[i + 1]))) {
                isnull = 1;
                break;
            }
        }
        if (isnull)
            continue;

        yval = seg_val[ninx];
        if (Rast_is_d_null_value(&yval))
            continue;

        dist2 = (r - rr) * (r - rr) + (c - cc) * (c - cc);
        w = w_fn(dist2, bw);

        for (i = 0; i <= ninx; i++) {
            double val1 = xval[i];

            for (j = i; j <= ninx; j++) {
                double val2 = xval[j];

                m = &(m_all[0]);
                M(m, i, j) += val1 * val2 * w;

                /* linear model without predictor k */
                for (k = 1; k <= ninx; k++) {
                    if (k != i && k != j) {
                        int i2 = k > i ? i : i - 1;
                        int j2 = k > j ? j : j - 1;

                        m = &(m_all[k]);
                        M(m, i2, j2) += val1 * val2 * w;
                    }
                }
            }

            a[0][i] += yval * val1 * w;
            for (k = 1; k <= ninx; k++) {
                if (k != i) {
                    int i2 = k > i ? i : i - 1;

                    a[k][i2] += yval * val1 * w;
                }
            }
        }
        count++;
    }
    if (count < ninx + 1) {
        G_message(_("Unable to determine coefficients. Consider increasing the "
                    "number of points."));
        return 0;
    }

    /* estimate coefficients */
    solved = ninx + 1;
    for (k = 0; k <= ninx; k++) {
        m = &(m_all[k]);

        /* TRANSPOSE VALUES IN UPPER HALF OF M TO OTHER HALF */
        for (i = 1; i < m->n; i++)
            for (j = 0; j < i; j++)
                M(m, i, j) = M(m, j, i);

        if (!solvemat(m, a[k], B[k])) {
            /*
            for (i = 0; i <= ninx; i++) {
                fprintf(stdout, "b%d=0.0\n", i);
            }
            */
            solved--;
        }
    }
    if (solved < ninx + 1) {
        G_debug(3, "%d of %d equation systems could not be solved",
                ninx + 1 - solved, ninx + 1);
        return 0;
    }

    /* third pass: calculate estimates */
    Segment_get(in_seg, (void *)seg_val, rr, cc);
    isnull = 0;
    for (i = 0; i < ninx; i++) {

        xval[i + 1] = seg_val[i];
        if (Rast_is_d_null_value(&(xval[i + 1]))) {
            isnull = 1;
            break;
        }
    }
    if (isnull)
        return 0;

    est[0] = 0.0;
    for (k = 0; k <= ninx; k++) {
        est[0] += B[0][k] * xval[k];

        if (k > 0) {
            est[k] = 0.0;

            /* linear model without predictor k */
            for (i = 0; i <= ninx; i++) {
                if (i != k) {
                    j = k > i ? i : i - 1;
                    est[k] += B[k][j] * xval[i];
                }
            }
        }
    }
    if (B0)
        *B0 = B[0];

    return count;
}
