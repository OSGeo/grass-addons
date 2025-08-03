#include "local_proto.h"

/*
   Link: a channel between junction
   Outlet: is final cell of every segment
   Segment: a channel which order remains unchanged in spite it pass through
   junction or not Number of outlets shall be equal the number of segments
   Number of junction shall be less than number of links
 */

/*
   find outlets create table of outlets point, with r, c and value. depending of
   flag: if flag -l is as only last points of segment is added to table and uses
   the value is the category as value for whole basins if flag -l = false
   (default) last points of every link is added to table and uses the value is
   the category as value for subbasin In both cases if flag -c is used it add
   out_num+1 value as value of point. That structure is next used in
   reset_catchments and fill_catchments functions
 */

/* fifo functions */
/* insertion point: tail -> tail must always be unused */
/* removal point: head + 1 */
/* head == tail if last point removed or if only one free slot left */

static int tail, head, fifo_count;

int fifo_insert(POINT point)
{
    if (fifo_count == fifo_max)
        G_fatal_error(_("Circular buffer too small"));

    fifo_points[tail++] = point;
    if (tail > fifo_max) {
        G_debug(1, "tail > fifo_max");
        tail = 0;
    }
    fifo_count++;

    return 0;
}

POINT fifo_return_del(void)
{
    if (head >= fifo_max) {
        G_debug(1, "head >= fifo_max");
        head = -1;
    }
    fifo_count--;

    return fifo_points[++head];
}

/*
   this function adds points from outlet structure
   The lines below from function fill_catchments makes that
   outlet is not added do fifo
   queue and basin is limited by next outlet

   if (catchments[NR(i)][NR(i)]>0)
   continue;

   It is simple trick but allow gives module its real functionality

   Buffer is an correction which allow to delineate basins even if vector point
   or coordinates do not lie exactly on stream. In that case a small one pixel
   buffer is created. This is little risk functionality and must be used
   carefully.
 */

int ram_add_outlets(CELL **basins, int outlets_num)
{
    int i;

    for (i = 0; i < outlets_num; ++i)
        basins[outlets[i].r][outlets[i].c] = outlets[i].val;

    return 0;
}

int seg_add_outlets(SEGMENT *basins, int outlets_num)
{

    int i;
    int *basins_cell;

    for (i = 0; i < outlets_num; ++i) {
        basins_cell = &outlets[i].val;
        Segment_put(basins, basins_cell, outlets[i].r, outlets[i].c);
    }
    return 0;
}

/*
   algorithm uses fifo queue for determining basins area.
 */

int ram_fill_basins(OUTLET outlet, CELL **basins, CELL **dirs)
{
    int next_r, next_c;
    int r, c, val, i, j;
    POINT n_cell;
    int dirs_cell, basins_cell;

    tail = 0;
    head = -1;
    fifo_count = 0;
    r = outlet.r;
    c = outlet.c;
    val = outlet.val;

    G_debug(1, "processing outlet at row %d col %d", r, c);

    basins[r][c] = val;

    while (tail != head) {
        for (i = 1; i < 9; i++) {
            next_r = NR(i);
            next_c = NC(i);

            if (NOT_IN_REGION(i))
                continue;
            j = DIAG(i);

            dirs_cell = dirs[next_r][next_c];
            basins_cell = basins[next_r][next_c];

            /* contributing cell, not yet assigned to a basin */
            if (dirs_cell == j && basins_cell == 0) {
                basins[next_r][next_c] = val;
                n_cell.r = next_r;
                n_cell.c = next_c;
                fifo_insert(n_cell);
            }
        } /* end for i... */

        n_cell = fifo_return_del();
        r = n_cell.r;
        c = n_cell.c;
    } /* end while */

    return 0;
}

int seg_fill_basins(OUTLET outlet, SEGMENT *basins, SEGMENT *dirs)
{
    int next_r, next_c;
    int r, c, val, i, j;
    POINT n_cell;
    int dirs_cell, basins_cell;

    tail = 0;
    head = -1;
    fifo_count = 0;
    r = outlet.r;
    c = outlet.c;
    val = outlet.val;

    G_debug(1, "processing outlet at row %d col %d", r, c);

    Segment_put(basins, &val, r, c);

    while (tail != head) {
        for (i = 1; i < 9; i++) {
            next_r = NR(i);
            next_c = NC(i);

            if (NOT_IN_REGION(i))
                continue;
            j = DIAG(i);

            Segment_get(basins, &basins_cell, next_r, next_c);
            Segment_get(dirs, &dirs_cell, next_r, next_c);

            /* contributing cell, not yet assigned to a basin */
            if (dirs_cell == j && basins_cell == 0) {
                Segment_put(basins, &val, next_r, next_c);
                n_cell.r = next_r;
                n_cell.c = next_c;
                fifo_insert(n_cell);
            }
        } /* end for i... */

        n_cell = fifo_return_del();
        r = n_cell.r;
        c = n_cell.c;
    } /* end while */

    return 0;
}
