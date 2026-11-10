#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/segment.h>
#include <grass/glocale.h>
#include "pavl.h"
#include "rclist.h"
#include "cache.h"

struct nbr_cnt {
    int id;
    int row, col;
    int cnt;
};

static void avl_free_item(void *avl_item)
{
    G_free(avl_item);
}

static int cmp_nbrs(const void *a, const void *b)
{
    struct nbr_cnt *aa = (struct nbr_cnt *)a;
    struct nbr_cnt *bb = (struct nbr_cnt *)b;

    return (aa->id - bb->id);
}

static int cmp_rc(const void *first, const void *second)
{
    struct rc *a = (struct rc *)first, *b = (struct rc *)second;

    if (a->row == b->row)
        return (a->col - b->col);

    return (a->row - b->row);
}

static int get_eight_neighbors(int row, int col, int nrows, int ncols,
                               int neighbors[8][2])
{
    int rown, coln, n;

    n = -1;
    /* previous row */
    rown = row - 1;
    if (rown >= 0) {
        coln = col - 1;
        if (coln >= 0) {
            n++;
            neighbors[n][0] = rown;
            neighbors[n][1] = coln;
        }
        n++;
        neighbors[n][0] = rown;
        neighbors[n][1] = col;
        coln = col + 1;
        if (coln < ncols) {
            n++;
            neighbors[n][0] = rown;
            neighbors[n][1] = coln;
        }
    }

    /* next row */
    rown = row + 1;
    if (rown < nrows) {
        coln = col - 1;
        if (coln >= 0) {
            n++;
            neighbors[n][0] = rown;
            neighbors[n][1] = coln;
        }
        n++;
        neighbors[n][0] = rown;
        neighbors[n][1] = col;
        coln = col + 1;
        if (coln < ncols) {
            n++;
            neighbors[n][0] = rown;
            neighbors[n][1] = coln;
        }
    }

    /* current row */
    coln = col - 1;
    if (coln >= 0) {
        n++;
        neighbors[n][0] = row;
        neighbors[n][1] = coln;
    }
    coln = col + 1;
    if (coln < ncols) {
        n++;
        neighbors[n][0] = row;
        neighbors[n][1] = coln;
    }

    return n;
}

static int get_four_neighbors(int row, int col, int nrows, int ncols,
                              int neighbors[8][2])
{
    int rown, coln, n;

    n = -1;
    /* previous row */
    rown = row - 1;
    if (rown >= 0) {
        n++;
        neighbors[n][0] = rown;
        neighbors[n][1] = col;
    }

    /* next row */
    rown = row + 1;
    if (rown < nrows) {
        n++;
        neighbors[n][0] = rown;
        neighbors[n][1] = col;
    }

    /* current row */
    coln = col - 1;
    if (coln >= 0) {
        n++;
        neighbors[n][0] = row;
        neighbors[n][1] = coln;
    }
    coln = col + 1;
    if (coln < ncols) {
        n++;
        neighbors[n][0] = row;
        neighbors[n][1] = coln;
    }

    return n;
}

static int (*get_neighbors)(int row, int col, int nrows, int ncols,
                            int neighbors[8][2]);

static int update_cid(struct cache *k_seg, int row, int col, int old_id,
                      int new_id)
{
    int nrows, ncols, rown, coln, n;
    int this_id;
    int neighbors[8][2];
    struct rc next;
    struct rclist rilist;

    cache_get(k_seg, &this_id, row, col);
    if (this_id != old_id) {
        G_fatal_error(_("Wrong id %d for row %d, col %d"), this_id, row, col);
    }
    cache_put(k_seg, &new_id, row, col);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* breadth-first search */
    next.row = row;
    next.col = col;
    rclist_init(&rilist);

    do {

        n = get_neighbors(next.row, next.col, nrows, ncols, neighbors);
        do {
            rown = neighbors[n][0];
            coln = neighbors[n][1];

            cache_get(k_seg, &this_id, rown, coln);
            if (this_id == old_id) {
                cache_put(k_seg, &new_id, rown, coln);
                rclist_add(&rilist, rown, coln);
            }

        } while (n--); /* end do loop - next neighbor */
    } while (rclist_drop(&rilist, &next)); /* while there are cells to check */

    rclist_destroy(&rilist);

    return 1;
}

static int find_best_neighbour(DCELL **clumpbsum, int nbands, int *clumpsize,
                               struct cache *k_seg, int row, int col,
                               int this_id, int *best_id)
{
    int rown, coln, n, count, b;
    int nrows, ncols;
    int neighbors[8][2];
    struct rc next, ngbr_rc, *pngbr_rc;
    struct rclist rilist;
    int ngbr_id;
    struct pavl_table *nbtree, *visited;
    struct nbr_cnt Rk, *Rkp;
    double sim, best_sim;

    G_debug(3, "find_best_neighbour()");

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    nbtree = pavl_create(cmp_nbrs, NULL);
    visited = pavl_create(cmp_rc, NULL);
    ngbr_rc.row = row;
    ngbr_rc.col = col;

    pngbr_rc = G_malloc(sizeof(struct rc));
    *pngbr_rc = ngbr_rc;
    pavl_insert(visited, pngbr_rc);
    pngbr_rc = NULL;

    /* breadth-first search */
    next.row = row;
    next.col = col;
    rclist_init(&rilist);
    count = 1;
    *best_id = -1;
    best_sim = 2;

    do {
        n = get_neighbors(next.row, next.col, nrows, ncols, neighbors);
        do {
            rown = neighbors[n][0];
            coln = neighbors[n][1];

            /* get neighbor ID */
            cache_get(k_seg, &ngbr_id, rown, coln);
            if (ngbr_id < 0)
                continue;

            ngbr_rc.row = rown;
            ngbr_rc.col = coln;

            if (pngbr_rc == NULL)
                pngbr_rc = G_malloc(sizeof(struct rc));

            *pngbr_rc = ngbr_rc;

            if (pavl_insert(visited, pngbr_rc) == NULL) {
                pngbr_rc = NULL;

                /* same neighbour */
                if (ngbr_id == this_id) {
                    count++;
                    rclist_add(&rilist, rown, coln);
                }
                else if (ngbr_id >= 0) { /* different neighbour */

                    /* find in neighbor tree */
                    Rk.id = ngbr_id;
                    if (pavl_find(nbtree, &Rk) == NULL) {
                        Rk.row = rown;
                        Rk.col = coln;
                        Rkp = G_malloc(sizeof(struct nbr_cnt));
                        *Rkp = Rk;
                        pavl_insert(nbtree, Rkp);

                        sim = 0;
                        for (b = 0; b < nbands; b++) {
                            sim +=
                                (clumpbsum[this_id][b] / clumpsize[this_id] -
                                 clumpbsum[ngbr_id][b] / clumpsize[ngbr_id]) *
                                (clumpbsum[this_id][b] / clumpsize[this_id] -
                                 clumpbsum[ngbr_id][b] / clumpsize[ngbr_id]);
                        }
                        sim /= nbands;

                        if (best_sim > sim) {
                            best_sim = sim;
                            *best_id = ngbr_id;
                        }
                        else if (best_sim == sim &&
                                 clumpsize[*best_id] > clumpsize[ngbr_id]) {
                            best_sim = sim;
                            *best_id = ngbr_id;
                        }
                    }
                }
            }
        } while (n--); /* end do loop - next neighbor */
    } while (rclist_drop(&rilist, &next)); /* while there are cells to check */

    rclist_destroy(&rilist);
    pavl_destroy(visited, avl_free_item);
    pavl_destroy(nbtree, avl_free_item);

    return (*best_id >= 0);
}

int merge_small_clumps(struct cache *bands_seg, int nbands, struct cache *k_seg,
                       int nlabels, int diag, int minsize)
{
    int row, col, nrows, ncols, i, b;
    int this_id;
    int best_id;
    int reg_size;
    int *clumpsize, n_clumps_new;
    DCELL **clumpbsum;
    DCELL *pdata;

    /* merge with best (most similar) neighbour */

    if (minsize < 2)
        G_fatal_error(_("Minimum size must be larger than 1"));

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    if (nlabels < 2) {
        G_warning(_("Not enough clumps for merging"));

        return nlabels;
    }

    if (diag)
        get_neighbors = get_eight_neighbors;
    else
        get_neighbors = get_four_neighbors;

    /* init clump sizes and band sums */
    clumpsize = (int *)G_malloc(sizeof(int) * (nlabels));
    clumpbsum = (DCELL **)G_malloc(sizeof(DCELL *) * (nlabels));
    for (i = 0; i < nlabels; i++) {
        clumpsize[i] = 0;
        clumpbsum[i] = (DCELL *)G_malloc(sizeof(DCELL) * (nbands));
        for (b = 0; b < nbands; b++)
            clumpbsum[i][b] = 0;
    }
    pdata = G_malloc(sizeof(DCELL) * nbands);

    G_message(_("Merging clumps smaller than %d cells..."), minsize);

    /* get clump sizes and band sums */
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++) {
            cache_get(k_seg, &this_id, row, col);
            if (this_id >= 0) {
                clumpsize[this_id]++;
                cache_get(bands_seg, pdata, row, col);
                for (b = 0; b < nbands; b++)
                    clumpbsum[this_id][b] += pdata[b];
            }
        }
    }

    /* go through all cells */
    G_percent_reset();
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        for (col = 0; col < ncols; col++) {

            /* get clump id */
            cache_get(k_seg, &this_id, row, col);
            if (this_id < 0)
                continue;

            reg_size = clumpsize[this_id];

            best_id = 0;
            while (reg_size < minsize && best_id >= 0) {
                best_id = -1;

                find_best_neighbour(clumpbsum, nbands, clumpsize, k_seg, row,
                                    col, this_id, &best_id);

                if (best_id >= 0) {
                    /* update cid */
                    update_cid(k_seg, row, col, this_id, best_id);
                    /* mark as merged */
                    for (b = 0; b < nbands; b++)
                        clumpbsum[best_id][b] += clumpbsum[this_id][b];
                    clumpsize[best_id] += clumpsize[this_id];
                    reg_size = clumpsize[best_id];
                    clumpsize[this_id] = 0;
                    this_id = best_id;
                }
            }
        }
    }
    G_percent(1, 1, 1);

    n_clumps_new = 0;

    /* clumpsize becomes new clump ID */
    for (i = 0; i < nlabels; i++) {
        if (clumpsize[i] > 0)
            clumpsize[i] = n_clumps_new++;
    }

    G_message(_("Renumbering remaining %d clumps..."), n_clumps_new);

    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 4);

        for (col = 0; col < ncols; col++) {

            cache_get(k_seg, &this_id, row, col);
            if (this_id >= 0) {
                this_id = clumpsize[this_id];
                cache_put(k_seg, &this_id, row, col);
            }
        }
    }
    G_percent(1, 1, 1);

    for (i = 0; i < nlabels; i++)
        G_free(clumpbsum[i]);
    G_free(clumpbsum);
    G_free(clumpsize);

    return n_clumps_new;
}
