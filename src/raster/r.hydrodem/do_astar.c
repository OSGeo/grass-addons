#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "local_proto.h"

#define GET_PARENT(c) ((((GW_LARGE_INT)(c) - 2) >> 2) + 1)
#define GET_CHILD(p)  (((GW_LARGE_INT)(p) << 2) - 2)

#define HEAP_CMP(a, b)     \
    (((a)->ele < (b)->ele) \
         ? 1               \
         : (((a)->ele > (b)->ele) ? 0 : (((a)->added < (b)->added) ? 1 : 0)))

struct heap_point heap_drop(void);

double get_slope(CELL, CELL, double);

int do_astar(void)
{
    int r, c, r_nbr, c_nbr, ct_dir;
    GW_LARGE_INT count;
    int nextdr[8] = {1, -1, 0, 0, -1, 1, 1, -1};
    int nextdc[8] = {0, 0, -1, 1, 1, -1, 1, -1};
    int asp_r[9] = {0, -1, -1, -1, 0, 1, 1, 1, 0};
    int asp_c[9] = {0, 1, 0, -1, -1, -1, 0, 1, 1};
    CELL ele_val, ele_down, ele_nbr[8];
    char is_bottom;
    char is_in_list, is_worked;
    struct dir_flag df;
    struct heap_point heap_p;
    /* sides
     * |7|1|4|
     * |2| |3|
     * |5|0|6|
     */
    int nbr_ew[8] = {0, 1, 2, 3, 1, 0, 0, 1};
    int nbr_ns[8] = {0, 1, 2, 3, 3, 2, 3, 2};
    double dx, dy, dist_to_nbr[8], ew_res, ns_res;
    double slope[8];
    int skip_diag;
    struct Cell_head window;

    count = 0;

    first_cum = n_points;

    sinks = first_sink = NULL;
    n_sinks = 0;

    G_message(_("A* Search..."));

    Rast_get_window(&window);

    for (ct_dir = 0; ct_dir < sides; ct_dir++) {
        /* get r, c (r_nbr, c_nbr) for neighbours */
        r_nbr = nextdr[ct_dir];
        c_nbr = nextdc[ct_dir];
        /* account for rare cases when ns_res != ew_res */
        dy = abs(r_nbr) * window.ns_res;
        dx = abs(c_nbr) * window.ew_res;
        if (ct_dir < 4)
            dist_to_nbr[ct_dir] = dx + dy;
        else
            dist_to_nbr[ct_dir] = sqrt(dx * dx + dy * dy);
    }
    ew_res = window.ew_res;
    ns_res = window.ns_res;

    while (heap_size > 0) {
        G_percent(count++, n_points, 1);
        if (count > n_points)
            G_fatal_error(_("BUG in A* Search: %lld surplus points"),
                          (long long int)heap_size);

        if (heap_size > n_points)
            G_fatal_error(_("BUG in A* Search: too many points in heap %lld, "
                            "should be %lld"),
                          (long long int)heap_size, (long long int)n_points);

        heap_p = heap_drop();

        /* flow accumulation order is not needed */
        r = heap_p.r;
        c = heap_p.c;

        first_cum--;
        seg_get(&dirflag, (char *)&df, r, c);
        FLAG_SET(df.flag, WORKEDFLAG);
        seg_put(&dirflag, (char *)&df, r, c);

        ele_val = ele_down = heap_p.ele;
        is_bottom = 0;

        if (df.dir > 0 && !FLAG_GET(df.flag, EDGEFLAG)) {
            r_nbr = r + asp_r[(int)df.dir];
            c_nbr = c + asp_c[(int)df.dir];
            cseg_get(&ele, &ele_down, r_nbr, c_nbr);
            if (ele_down > ele_val)
                is_bottom = 1;
        }

        for (ct_dir = 0; ct_dir < sides; ct_dir++) {
            /* get r, c (r_nbr, c_nbr) for neighbours */
            r_nbr = r + nextdr[ct_dir];
            c_nbr = c + nextdc[ct_dir];
            slope[ct_dir] = -1;
            ele_nbr[ct_dir] = 0;

            /* check that neighbour is within region */
            if (r_nbr < 0 || r_nbr >= nrows || c_nbr < 0 || c_nbr >= ncols)
                continue;

            seg_get(&dirflag, (char *)&df, r_nbr, c_nbr);
            is_in_list = FLAG_GET(df.flag, INLISTFLAG);
            is_worked = FLAG_GET(df.flag, WORKEDFLAG);
            skip_diag = 0;

            /* avoid diagonal flow direction bias */
            if (!is_worked) {
                cseg_get(&ele, &ele_nbr[ct_dir], r_nbr, c_nbr);
                slope[ct_dir] =
                    get_slope(ele_val, ele_nbr[ct_dir], dist_to_nbr[ct_dir]);
            }

            if (!is_in_list || (!is_worked && df.dir < 0)) {
                if (ct_dir > 3 && slope[ct_dir] > 0) {
                    if (slope[nbr_ew[ct_dir]] >= 0) {
                        /* slope to ew nbr > slope to center */
                        if (slope[ct_dir] < get_slope(ele_nbr[nbr_ew[ct_dir]],
                                                      ele_nbr[ct_dir], ew_res))
                            skip_diag = 1;
                    }
                    if (!skip_diag && slope[nbr_ns[ct_dir]] >= 0) {
                        /* slope to ns nbr > slope to center */
                        if (slope[ct_dir] < get_slope(ele_nbr[nbr_ns[ct_dir]],
                                                      ele_nbr[ct_dir], ns_res))
                            skip_diag = 1;
                    }
                }
            }

            if (!skip_diag) {
                if (!is_in_list) {
                    df.dir = drain[r_nbr - r + 1][c_nbr - c + 1];
                    FLAG_SET(df.flag, INLISTFLAG);
                    seg_put(&dirflag, (char *)&df, r_nbr, c_nbr);
                    heap_add(r_nbr, c_nbr, ele_nbr[ct_dir]);

                    if (ele_nbr[ct_dir] < ele_val)
                        is_bottom = 0;
                }
                else if (!is_worked) {
                    if (FLAG_GET(df.flag, EDGEFLAG)) {
                        if (df.dir < 0 && slope[ct_dir] > 0) {
                            /* update edge cell ? no */
                            /* df.dir = drain[r_nbr - r + 1][c_nbr - c + 1]; */
                            /* check if this causes trouble */
                            /* seg_put(&dirflag, (char *)&df, r_nbr, c_nbr); */

                            if (ele_nbr[ct_dir] < ele_val)
                                is_bottom = 0;
                        }
                    }
                    else if (FLAG_GET(df.flag, DEPRFLAG)) {
                        G_debug(3, "real depression");
                        /* neighbour is inside real depression, not yet worked
                         */
                        if (df.dir == 0 && ele_val <= ele_nbr[ct_dir]) {
                            df.dir = drain[r_nbr - r + 1][c_nbr - c + 1];
                            FLAG_UNSET(df.flag, DEPRFLAG);
                            seg_put(&dirflag, (char *)&df, r_nbr, c_nbr);
                        }
                    }
                }
            }
        } /* end neighbours */

        if (is_bottom) {
            /* add sink bottom */
            /* process upstream */
            if (1) {
                if (first_sink) {
                    sinks->next =
                        (struct sink_list *)G_malloc(sizeof(struct sink_list));
                    sinks = sinks->next;
                }
                /* first sink */
                else {
                    first_sink =
                        (struct sink_list *)G_malloc(sizeof(struct sink_list));
                    sinks = first_sink;
                }
                sinks->next = NULL;
            }
            /* process downstream */
            if (0) {
                sinks = (struct sink_list *)G_malloc(sizeof(struct sink_list));
                sinks->next = first_sink;
                first_sink = sinks;
            }
            sinks->r = r;
            sinks->c = c;
            n_sinks++;
        }
    } /* end A* search */

    G_percent(n_points, n_points, 1); /* finish it */

    if (first_cum)
        G_warning(_("processed points mismatch of %lld"),
                  (long long int)first_cum);

    return 1;
}

/*
 * compare function for heap
 * returns 1 if point1 < point2 else 0
 */

static int heap_cmp(struct heap_point *a, struct heap_point *b)
{
    if (a->ele < b->ele)
        return 1;
    else if (a->ele == b->ele) {
        if (a->added < b->added)
            return 1;
    }
    return 0;
}

int sift_up(GW_LARGE_INT start, struct heap_point child_p)
{
    GW_LARGE_INT parent, child;
    struct heap_point heap_p;

    child = start;

    while (child > 1) {
        parent = GET_PARENT(child);

        seg_get(&search_heap, (char *)&heap_p, 0, parent);

        /* push parent point down if child is smaller */
        if (heap_cmp(&child_p, &heap_p)) {
            seg_put(&search_heap, (char *)&heap_p, 0, child);
            child = parent;
        }
        else
            /* no more sifting up, found new slot for child */
            break;
    }

    /* add child to heap */
    seg_put(&search_heap, (char *)&child_p, 0, child);

    return 0;
}

/*
 * add item to heap
 * returns heap_size
 */
GW_LARGE_INT heap_add(int r, int c, CELL elev)
{
    struct heap_point heap_p;

    /* add point to next free position */

    heap_size++;

    if (heap_size > n_points)
        G_fatal_error(_("Heapsize too large"));

    heap_p.r = r;
    heap_p.c = c;
    heap_p.ele = elev;
    heap_p.added = nxt_avail_pt;

    nxt_avail_pt++;

    /* sift up: move new point towards top of heap */

    sift_up(heap_size, heap_p);

    return heap_size;
}

/*
 * drop item from heap
 * returns heap size
 */
struct heap_point heap_drop(void)
{
    unsigned int child, childr, parent;
    unsigned int i;
    struct heap_point child_p, childr_p, last_p, root_p;

    seg_get(&search_heap, (char *)&last_p, 0, heap_size);
    seg_get(&search_heap, (char *)&root_p, 0, 1);

    if (heap_size == 1) {
        heap_size = 0;
        return root_p;
    }

    parent = 1;
    while ((child = GET_CHILD(parent)) <= heap_size) {

        seg_get(&search_heap, (char *)&child_p, 0, child);

        if (child < heap_size) {
            childr = child + 1;
            i = child + 4;
            while (childr <= heap_size && childr < i) {
                seg_get(&search_heap, (char *)&childr_p, 0, childr);
                if (heap_cmp(&childr_p, &child_p)) {
                    child = childr;
                    child_p = childr_p;
                }
                childr++;
            }
        }
        if (heap_cmp(&last_p, &child_p)) {
            break;
        }

        /* move hole down */
        seg_put(&search_heap, (char *)&child_p, 0, parent);
        parent = child;
    }

    /* fill hole */
    if (parent < heap_size) {
        seg_put(&search_heap, (char *)&last_p, 0, parent);
    }

    /* the actual drop */
    heap_size--;

    return root_p;
}

double get_slope(CELL elev, CELL up_ele, double dist)
{
    if (elev >= up_ele)
        return 0.0;
    else
        return (double)(up_ele - elev) / dist;
}
