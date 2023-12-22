#include <stdlib.h>
#include <math.h>
#include <limits.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "local_proto.h"

struct ns {
    int r, c;
    int next_side;
    int n_ngbrs;
};

static struct ns *n_stack;
static int stack_alloc;

static int asp_r[9] = {0, -1, -1, -1, 0, 1, 1, 1, 0};
static int asp_c[9] = {0, 1, 0, -1, -1, -1, 0, 1, 1};

static int nextdr[8] = {1, -1, 0, 0, -1, 1, 1, -1};
static int nextdc[8] = {0, 0, -1, 1, 1, -1, 1, -1};

static int count_fill(int peak_r, int peak_c, CELL peak_ele, int *n_splits,
                      CELL *next_ele)
{
    int r, c, r_nbr, c_nbr, ct_dir;
    CELL ele_nbr;
    int n_to_fill;
    int top, done;
    struct dir_flag df;

    /* go upstream from spill point */
    r = peak_r;
    c = peak_c;
    *n_splits = 0;
    n_to_fill = 0;
    /* post-order traversal */
    /* add spill point as root to stack */
    top = 0;
    n_stack[top].r = peak_r;
    n_stack[top].c = peak_c;
    n_stack[top].next_side = 0;
    n_stack[top].n_ngbrs = 0;
    while (top >= 0) {
        done = 1;
        r = n_stack[top].r;
        c = n_stack[top].c;
        for (ct_dir = n_stack[top].next_side; ct_dir < sides; ct_dir++) {
            r_nbr = r + nextdr[ct_dir];
            c_nbr = c + nextdc[ct_dir];
            /* check that neighbour is within region */
            if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 && c_nbr < ncols) {

                cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);
                seg_get(&dirflag, (char *)&df, r_nbr, c_nbr);
                if (df.dir > 0) {
                    /* contributing cell */
                    if (r_nbr + asp_r[(int)df.dir] == r &&
                        c_nbr + asp_c[(int)df.dir] == c) {

                        /* contributing neighbour is lower than
                         * spill point, add to stack */
                        if (peak_ele >= ele_nbr) {

                            if (peak_ele > ele_nbr)
                                n_to_fill++;
                            n_stack[top].next_side = ct_dir + 1;
                            n_stack[top].n_ngbrs++;
                            top++;
                            if (top >= stack_alloc) {
                                stack_alloc += nrows + ncols;
                                n_stack = (struct ns *)G_realloc(
                                    n_stack, stack_alloc * sizeof(struct ns));
                            }
                            n_stack[top].r = r_nbr;
                            n_stack[top].c = c_nbr;
                            n_stack[top].next_side = 0;
                            n_stack[top].n_ngbrs = 0;
                            done = 0;
                            break;
                        }
                        else if (next_ele && peak_ele < ele_nbr) {
                            if (*next_ele > ele_nbr)
                                *next_ele = ele_nbr;
                        }
                    }
                } /* end contributing */
                else if (df.dir == 0 && peak_ele > ele_nbr)
                    /* found bottom of real depression, don't fill */
                    return -1;
            } /* end in region */
        }     /* end sides */

        if (done) {
            *n_splits += (n_stack[top].n_ngbrs > 1);
            n_stack[top].next_side = sides;

            top--;
        }
    }
    return n_to_fill;
}

/* detect flat area:
 * count neighbouring cells with same ele
 * exclude contributing cells and cell this one is contributing to */
static int is_flat(int r, int c, CELL this_ele)
{
    int r_nbr, c_nbr, ct_dir;
    CELL ele_nbr;
    struct dir_flag df, df_nbr;
    int counter = 0;

    seg_get(&dirflag, (char *)&df, r, c);

    if (df.dir < 1)
        return 0;

    for (ct_dir = 0; ct_dir < sides; ct_dir++) {
        r_nbr = r + nextdr[ct_dir];
        c_nbr = c + nextdc[ct_dir];
        /* check that neighbour is within region */
        if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 && c_nbr < ncols) {

            cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);
            seg_get(&dirflag, (char *)&df_nbr, r_nbr, c_nbr);
            if (df_nbr.dir > 0) {
                /* not a contributing cell */
                if (r_nbr + asp_r[(int)df_nbr.dir] != r ||
                    c_nbr + asp_c[(int)df_nbr.dir] != c) {
                    /* does not contribute to this cell */
                    if (r + asp_r[(int)df.dir] != r_nbr ||
                        c + asp_c[(int)df.dir] != c_nbr) {
                        if (ele_nbr == this_ele)
                            counter++;
                    }
                }
            }
        }
    }

    return (counter > 0);
}

static int fill_sink(int peak_r, int peak_c, CELL peak_ele)
{
    int r, c, r_nbr, c_nbr, ct_dir;
    CELL ele_nbr;
    int n_to_fill = 0;
    int top, done;
    struct dir_flag df;

    /* post-order traversal */
    /* add spill point as root to stack */
    top = 0;
    n_stack[top].r = peak_r;
    n_stack[top].c = peak_c;
    n_stack[top].next_side = 0;
    n_stack[top].n_ngbrs = 0;
    while (top >= 0) {
        done = 1;
        r = n_stack[top].r;
        c = n_stack[top].c;
        for (ct_dir = n_stack[top].next_side; ct_dir < sides; ct_dir++) {
            r_nbr = r + nextdr[ct_dir];
            c_nbr = c + nextdc[ct_dir];
            /* check that neighbour is within region */
            if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 && c_nbr < ncols) {

                cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);
                seg_get(&dirflag, (char *)&df, r_nbr, c_nbr);
                if (df.dir > 0) {
                    /* contributing cell */
                    if (r_nbr + asp_r[(int)df.dir] == r &&
                        c_nbr + asp_c[(int)df.dir] == c) {

                        /* contributing neighbour is lower than
                         * spill point, add to stack */
                        if (peak_ele >= ele_nbr) {

                            n_to_fill++;
                            n_stack[top].next_side = ct_dir + 1;
                            n_stack[top].n_ngbrs++;
                            top++;
                            if (top >= stack_alloc) {
                                stack_alloc += nrows + ncols;
                                n_stack = (struct ns *)G_realloc(
                                    n_stack, stack_alloc * sizeof(struct ns));
                            }
                            n_stack[top].r = r_nbr;
                            n_stack[top].c = c_nbr;
                            n_stack[top].next_side = 0;
                            n_stack[top].n_ngbrs = 0;
                            done = 0;
                            break;
                        }
                    }
                } /* end contributing */
            }     /* end in region */
        }         /* end sides */

        if (done) {
            cseg_put(&ele, &peak_ele, r, c);
            n_stack[top].next_side = sides;
            top--;
        }
    }

    return n_to_fill;
}

/* carve channel */
static int carve(int bottom_r, int bottom_c, CELL bottom_ele, int peak_r,
                 int peak_c)
{
    int r, c, r_nbr, c_nbr, carved = 0;
    struct dir_flag df;
    int ct_dir;
    CELL ele_val, ele_nbr;
    int top, done;

    /* carve upstream from spill point --> */
    /* post-order traversal */
    /* add spill point as root to stack */
    top = 0;
    n_stack[top].r = peak_r;
    n_stack[top].c = peak_c;
    n_stack[top].next_side = 0;
    n_stack[top].n_ngbrs = 0;
    while (top >= 0) {
        done = 1;
        r = n_stack[top].r;
        c = n_stack[top].c;
        cseg_get(&ele, &ele_val, r, c);
        for (ct_dir = n_stack[top].next_side; ct_dir < sides; ct_dir++) {
            r_nbr = r + nextdr[ct_dir];
            c_nbr = c + nextdc[ct_dir];
            /* check that neighbour is within region */
            if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 && c_nbr < ncols) {

                cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);
                seg_get(&dirflag, (char *)&df, r_nbr, c_nbr);
                if (df.dir > 0) {
                    /* contributing cell */
                    if (r_nbr + asp_r[(int)df.dir] == r &&
                        c_nbr + asp_c[(int)df.dir] == c) {

                        /* contributing neighbour is lower than
                         * current point, add to stack */
                        if (ele_val > ele_nbr && ele_nbr >= bottom_ele) {

                            n_stack[top].next_side = ct_dir + 1;
                            n_stack[top].n_ngbrs++;
                            top++;
                            if (top >= stack_alloc) {
                                stack_alloc += nrows + ncols;
                                n_stack = (struct ns *)G_realloc(
                                    n_stack, stack_alloc * sizeof(struct ns));
                            }
                            n_stack[top].r = r_nbr;
                            n_stack[top].c = c_nbr;
                            n_stack[top].next_side = 0;
                            n_stack[top].n_ngbrs = 0;
                            done = 0;
                            break;
                        }
                    }
                } /* end contributing */
            }     /* end in region */
        }         /* end sides */

        if (done) {
            /* lower all cells to bottom ele
             * that have lower lying contributing neighbours */
            if (n_stack[top].n_ngbrs > 0)
                cseg_put(&ele, &bottom_ele, r, c);
            n_stack[top].next_side = sides;
            top--;
        }
    }
    /* <-- carve upstream from spill point */

    /* carve downstream from sink bottom */
    seg_get(&dirflag, (char *)&df, bottom_r, bottom_c);
    if (df.dir < 1) {
        G_warning(_("Can't carve downstream from r %d, c %d"), bottom_r,
                  bottom_c);
        return 0;
    }

    r_nbr = bottom_r + asp_r[(int)df.dir];
    c_nbr = bottom_c + asp_c[(int)df.dir];

    cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);

    /* go downstream up to peak and down to bottom again */
    while (ele_nbr >= bottom_ele) {
        seg_get(&dirflag, (char *)&df, r_nbr, c_nbr);
        cseg_put(&ele, &bottom_ele, r_nbr, c_nbr);
        carved++;

        if (df.dir > 0) {
            r_nbr = r_nbr + asp_r[(int)df.dir];
            c_nbr = c_nbr + asp_c[(int)df.dir];
            cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);
        }
        else {
            G_debug(2, "%d carved to edge", carved);
            return carved;
        }
    }

    return carved;
}

/* remove sinks */
int hydro_con(void)
{
    int counter = 1;
    int r, c, r_nbr, c_nbr, peak_r, peak_c, noedge, force_carve;
    CELL ele_val, ele_nbr, ele_last, peak_ele, bottom_ele;
    int down_uphill, down_downhill, n_cells;
    struct sink_list *last_sink;
    struct dir_flag df;

    int n_splits, n_to_fill;
    int n_filled, n_carved, n_just_a_bit, n_processed;
    int carve_to_edge, skipme;

    stack_alloc = nrows + ncols;

    n_stack = (struct ns *)G_malloc(stack_alloc * sizeof(struct ns));

    G_message(_("Processing %d sinks"), n_sinks);

    n_filled = n_carved = n_just_a_bit = n_processed = 0;

    while (first_sink) {
        G_percent(counter++, n_sinks, 1);

        r = first_sink->r;
        c = first_sink->c;

        cseg_get(&ele, &ele_val, r, c);
        bottom_ele = ele_val;

        skipme = 0;

        G_debug(1, "get spill point");

        /* go downstream, get spill point */
        peak_r = r;
        peak_c = c;
        seg_get(&dirflag, (char *)&df, r, c);

        r_nbr = r + asp_r[(int)df.dir];
        c_nbr = c + asp_c[(int)df.dir];

        cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);

        down_uphill = down_downhill = 0;
        noedge = 1;
        ele_last = bottom_ele;
        n_cells = 0;
        while (ele_nbr >= ele_last) {
            n_cells++;
            if (ele_nbr > ele_last) {
                down_uphill = n_cells;
                peak_r = r_nbr;
                peak_c = c_nbr;
            }
            seg_get(&dirflag, (char *)&df, r_nbr, c_nbr);

            if (df.dir > 0) {
                r_nbr = r_nbr + asp_r[(int)df.dir];
                c_nbr = c_nbr + asp_c[(int)df.dir];

                ele_last = ele_nbr;
                cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);
            }
            else {
                break;
            }
        }

        cseg_get(&ele, &peak_ele, peak_r, peak_c);

        seg_get(&dirflag, (char *)&df, peak_r, peak_c);
        noedge = (FLAG_GET(df.flag, EDGEFLAG) == 0);
        r_nbr = peak_r;
        c_nbr = peak_c;
        ele_nbr = peak_ele;

        /* check */
        if (down_uphill == 0) {
            G_debug(2, "sink already processed");
            n_processed++;

            last_sink = first_sink;
            first_sink = first_sink->next;
            G_free(last_sink);
            continue;
        }

        carve_to_edge = 0;
        if (noedge) {
            G_debug(1, "go downstream from spill point");
            /* go downstream from spill point
             * until we reach bottom ele again */
            while (ele_nbr >= bottom_ele) {
                if (ele_nbr > bottom_ele)
                    down_downhill++;
                seg_get(&dirflag, (char *)&df, r_nbr, c_nbr);

                /* detect flat area ? */

                if (df.dir > 0) {
                    r_nbr = r_nbr + asp_r[(int)df.dir];
                    c_nbr = c_nbr + asp_c[(int)df.dir];

                    cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);
                }
                else {
                    carve_to_edge = 1;
                    break;
                }
            }
        }
        G_debug(1, "%d cells downstream from spill point", down_downhill);

        /* count number of cells
         * that would be filled from current spill point upstream */
        G_debug(1, "count fill");
        n_to_fill = count_fill(peak_r, peak_c, peak_ele, &n_splits, NULL);

        skipme = (!do_all && n_to_fill <= size_max);

        nat_thresh = 10;

        /* shallow inland pans:
         * - bottom is close to center of the depression
         * - long channel to carve downstream from spill point
         * - shallowness */
        if (n_to_fill > nat_thresh && peak_ele - bottom_ele < 10 &&
            sqrt(n_to_fill) / 4.0 < down_uphill)
            G_debug(1, "shallow inland pan?");

        /*************************/
        /* set correction method */
        /*************************/

        /* force carving if edge not past spill point ? */
        force_carve = (noedge == 0);
        force_carve = 0;
        if (!force_carve && (do_all || n_mod_max >= 4) &&
            down_uphill + down_downhill <= 4 &&
            down_uphill + down_downhill <= n_to_fill)
            force_carve = 0;

        if (force_carving)
            force_carve = 1;

        /************************************/
        /* apply selected correction method */
        /************************************/

        /* force carve channel to edge if edge not past spill point */
        if (force_carve) {
            G_debug(1, "force carve small channel or to edge");
            carve(first_sink->r, first_sink->c, bottom_ele, peak_r, peak_c);
            n_carved++;
        }
        else if (force_filling) {
            G_debug(1, "force filling sinks");
            /* find spill point and its elevation */
            fill_sink(peak_r, peak_c, peak_ele);
            n_filled++;
        }
        /* impact reduction algorithm */
        else if (!skipme) {
            int next_r, next_c;
            int n_new_splits, is_edge = 0, this_is_flat;
            CELL min_bottom_ele, last_ele, next_bottom_ele;
            int least_impact, li_max;
            int least_impact_r, least_impact_c;
            CELL least_impact_ele;

            /* initialize least impact */
            li_max = n_to_fill + down_uphill + down_downhill;
            least_impact = down_uphill + down_downhill;
            least_impact_r = first_sink->r;
            least_impact_c = first_sink->c;
            least_impact_ele = bottom_ele;

            /* IRA --> */

            G_debug(1, "impact reduction algorithm");

            /* start with sink bottom, proceed to spill point
             * fill incrementally
             * for each step check if IRA condition fulfilled
             * proceed until condition no longer met
             * then use least impact solution
             * the determined new sink bottom can be
             * - the original sink bottom: no filling, only carving
             * - the spill point: no carving, only filling
             * - any cell in between the two */

            next_r = first_sink->r;
            next_c = first_sink->c;
            min_bottom_ele = bottom_ele;

            G_debug(1, "find new fill point");

            /* include no filling, full carving,
             * and full filling, no carving */
            while (bottom_ele <= peak_ele) {

                /* get n_to_fill, down_uphill, down_downhill */

                down_uphill = 0;
                down_downhill = 0;

                /* count cells to fill */
                next_bottom_ele = peak_ele;
                n_to_fill = count_fill(next_r, next_c, bottom_ele,
                                       &n_new_splits, &next_bottom_ele);

                if (n_to_fill < 0)
                    break;

                /* count channel length from spill point */
                /* go downstream from spill point
                 * until we reach bottom ele again */
                G_debug(2, "count channel length from spill point");
                r_nbr = peak_r;
                c_nbr = peak_c;
                last_ele = ele_nbr = peak_ele;
                min_bottom_ele = bottom_ele;
                this_is_flat = 0;
                while (ele_nbr >= bottom_ele && this_is_flat < 4) {
                    if (ele_nbr > bottom_ele) {
                        down_downhill++;
                        /* catch min 2 consecutive cells
                         * in flat area with same ele */
                        if (is_flat(r_nbr, c_nbr, ele_nbr)) {
                            if (ele_nbr == last_ele) {
                                this_is_flat++;
                                if (this_is_flat > 2 &&
                                    ele_nbr > min_bottom_ele)
                                    min_bottom_ele = bottom_ele + 1;
                            }
                            else
                                this_is_flat = 1;
                        }
                        if (next_bottom_ele > ele_nbr)
                            next_bottom_ele = ele_nbr;
                    }
                    seg_get(&dirflag, (char *)&df, r_nbr, c_nbr);

                    if (df.dir > 0) {
                        r_nbr = r_nbr + asp_r[(int)df.dir];
                        c_nbr = c_nbr + asp_c[(int)df.dir];

                        last_ele = ele_nbr;
                        cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);
                    }
                    else {
                        G_debug(2, "reached edge past spill point");
                        break;
                    }
                }

                /* carving ok */
                if (this_is_flat < 4) {
                    min_bottom_ele = bottom_ele;
                    /* count cells to carve from sink bottom to spill point */
                    ele_last = ele_nbr = bottom_ele;
                    r_nbr = next_r;
                    c_nbr = next_c;
                    n_cells = 0;
                    while (ele_nbr >= ele_last) {
                        n_cells++;
                        if (ele_nbr > bottom_ele) {
                            down_uphill = n_cells;
                        }
                        seg_get(&dirflag, (char *)&df, r_nbr, c_nbr);

                        if (df.dir > 0) {
                            r_nbr = r_nbr + asp_r[(int)df.dir];
                            c_nbr = c_nbr + asp_c[(int)df.dir];

                            ele_last = ele_nbr;
                            cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);
                        }
                        else {
                            break;
                        }
                    }
                    /* remember least impact */
                    if (least_impact >
                        n_to_fill + down_uphill + down_downhill) {
                        least_impact = n_to_fill + down_uphill + down_downhill;
                        least_impact_r = next_r;
                        least_impact_c = next_c;
                        least_impact_ele = bottom_ele;
                    }
                }
                /* carving not ok, need to fill more */
                else {
                    G_debug(2, "carving not ok");
                    least_impact = li_max;
                    least_impact_r = peak_r;
                    least_impact_c = peak_c;
                    least_impact_ele = peak_ele;
                    min_bottom_ele = bottom_ele + 1;
                }

                /* there is no better solution by filling more */
                if (n_to_fill > least_impact)
                    break;

                G_debug(2,
                        "channel length to spill point %d, channel length from "
                        "spill point %d, cells to fill %d",
                        down_uphill, down_downhill, n_to_fill);

                /* check IRA condition */
                /* preference for channel carving, relaxed stream split
                 * condition */
                /* continue filling ? */
                /* remains a mystery why n_new_splits results in less
                 * modifications... */
                if (sqrt(n_to_fill) < (down_uphill + down_downhill) ||
                    n_new_splits <= 4 || bottom_ele <= min_bottom_ele ||
                    least_impact == li_max) {
                    /* continue with IRA */
                    G_debug(2, "IRA conditions fulfilled");
                }
                /* IRA condition no longer fulfilled */
                else {
                    G_debug(2, "IRA conditions not met");
                    G_debug(2, "n to fill: %d", n_to_fill);
                    G_debug(2, "down_uphill: %d", down_uphill);
                    G_debug(2, "down_downhill: %d", down_downhill);
                    break;
                }

                if (bottom_ele >= peak_ele)
                    break;

                /* below spill point
                 * get next higher cell downstream of current bottom */
                G_debug(2, "get next fill point candidate");

                r_nbr = next_r;
                c_nbr = next_c;
                seg_get(&dirflag, (char *)&df, r_nbr, c_nbr);
                if (df.dir > 0) {

                    cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);
                    /* go to next higher cell downstream */
                    while (ele_nbr == bottom_ele || ele_nbr < min_bottom_ele) {
                        seg_get(&dirflag, (char *)&df, r_nbr, c_nbr);

                        if (df.dir > 0) {
                            r_nbr = r_nbr + asp_r[(int)df.dir];
                            c_nbr = c_nbr + asp_c[(int)df.dir];

                            cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);
                        }
                        else {
                            is_edge = 1;
                            break;
                        }
                    }
                    /* got next downstream cell that's higher than sink bottom
                     */
                    G_debug(2, "got next downstream cell");
                }
                else
                    is_edge = 1;

                if (is_edge) {
                    G_debug(1, "IRA reached edge");
                    break;
                }

                /* increase ele or go to next point */
                if (ele_nbr > next_bottom_ele &&
                    next_bottom_ele >= min_bottom_ele) {
                    G_debug(2, "increase ele, keep point");
                    bottom_ele = next_bottom_ele;
                }
                else {
                    next_r = r_nbr;
                    next_c = c_nbr;
                    bottom_ele = ele_nbr;
                }
            }
            /* <-- IRA */

            if (n_to_fill > -1 && least_impact == li_max)
                G_warning(_("IRA error"));

            if (n_to_fill > -1 && (do_all || least_impact <= n_mod_max)) {

                /* (partially) fill the sink */
                n_to_fill = 0;
                cseg_get(&ele, &ele_val, first_sink->r, first_sink->c);
                if (least_impact_ele != ele_val) {
                    G_debug(1, "IRA sink filling");

                    cseg_get(&ele, &ele_val, least_impact_r, least_impact_c);
                    if (ele_val != least_impact_ele) {
                        G_debug(1, "changing ele from %d to %d", ele_val,
                                least_impact_ele);
                        cseg_put(&ele, &least_impact_ele, least_impact_r,
                                 least_impact_c);
                    }
                    n_to_fill = fill_sink(least_impact_r, least_impact_c,
                                          least_impact_ele);
                    first_sink->r = least_impact_r;
                    first_sink->c = least_impact_c;
                    if (least_impact_ele < peak_ele)
                        n_just_a_bit++;
                    else
                        n_filled++;
                }
                else {
                    n_carved++;
                    G_debug(1, "IRA at bottom");
                }

                /* carve if not completely filled */
                down_downhill = 0;
                if (least_impact_ele < peak_ele) {
                    G_debug(2, "IRA carving");
                    down_downhill = carve(first_sink->r, first_sink->c,
                                          least_impact_ele, peak_r, peak_c);
                }
            }
        }

        G_debug(1, "get next sink");

        last_sink = first_sink;
        first_sink = first_sink->next;
        G_free(last_sink);
    }

    G_verbose_message("------------------------------------------------------");
    G_verbose_message(_("%d sinks processed"), n_sinks);
    G_verbose_message(_("%d sinks within larger sinks"), n_processed);
    G_verbose_message(_("%d sinks completely filled"), n_filled);
    G_verbose_message(_("%d sinks partially filled and carved with IRA"),
                      n_just_a_bit);
    G_verbose_message(_("%d channels carved"), n_carved);
    G_verbose_message("------------------------------------------------------");

    return 1;
}

int one_cell_extrema(int do_peaks, int do_pits, int all)
{
    int r, c, r_nbr, c_nbr;
    int ct_dir;
    int skipme;
    CELL ele_min, ele_max, ele_this, ele_nbr;
    GW_LARGE_INT n_pits = 0;
    GW_LARGE_INT n_peaks = 0;
    GW_LARGE_INT counter = 0;
    double sumofsquares, mean, stddev, upperci, lowerci;
    int n_valid;

    G_message(_("Remove one cell extremas"));

    /* not for edges */
    for (r = 0; r < nrows; r++) {
        G_percent(r, nrows, 2);

        for (c = 0; c < ncols; c++) {

            skipme = 0;
            cseg_get(&ele, &ele_this, r, c);

            if (Rast_is_c_null_value(&ele_this))
                continue;

            ele_min = INT_MAX;
            ele_max = INT_MIN;
            sumofsquares = mean = n_valid = 0;

            /* TODO: better use 5x5 neighbourhood ? */
            for (ct_dir = 0; ct_dir < sides; ct_dir++) {
                /* get r, c (r_nbr, c_nbr) for neighbours */
                r_nbr = r + nextdr[ct_dir];
                c_nbr = c + nextdc[ct_dir];
                /* check that neighbour is within region */
                if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 &&
                    c_nbr < ncols) {

                    cseg_get(&ele, &ele_nbr, r_nbr, c_nbr);

                    if (Rast_is_c_null_value(&ele_nbr)) {
                        skipme = 1;
                        break;
                    }

                    n_valid++;
                    sumofsquares += ele_nbr * ele_nbr;
                    mean += ele_nbr;

                    if (ele_min > ele_nbr) {
                        ele_min = ele_nbr;
                    }
                    if (ele_max < ele_nbr) {
                        ele_max = ele_nbr;
                    }
                }
                else {
                    skipme = 1;
                    break;
                }
            }

            if (skipme)
                continue;

            counter++;

            if (all) {
                upperci = ele_this - 1;
                lowerci = ele_this + 1;
            }
            else {
                /* remove extremas only if outside 95% CI = mean +- 1.96 * SD */
                mean /= n_valid;
                stddev = sqrt(sumofsquares / n_valid - mean * mean);
                upperci = mean + 1.96 * stddev;
                lowerci = mean - 1.96 * stddev;
            }

            /* one cell pit, lower than all surrounding neighbours */
            if (do_pits) {
                if (ele_this < ele_min && ele_this < lowerci) {
                    ele_this = ele_min;
                    cseg_put(&ele, &ele_this, r, c);
                    n_pits++;
                }
            }

            /* one cell peak, higher than all surrounding neighbours */
            if (do_peaks) {
                if (ele_this > ele_max && ele_this > upperci) {
                    ele_this = ele_max;
                    cseg_put(&ele, &ele_this, r, c);
                    n_peaks++;
                }
            }
        }
    }
    G_percent(nrows, nrows, 1); /* finish it */

    G_verbose_message("%lld cells checked", (long long int)counter);
    G_verbose_message("%lld one-cell peaks removed", (long long int)n_peaks);
    G_verbose_message("%lld one-cell pits removed", (long long int)n_pits);

    return 1;
}
