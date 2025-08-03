/***********************************************************************/
/*
   find_horizon.c

   Revised by Mark Lake, 14/08/20017, for bug fix
   Revised by Mark Lake, 28/07/20017, for r.skyline in GRASS 7.x
   Revised by Mark Lake, 26/07/20017, for r.horizon in GRASS 7.x
   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 15/07/2002, for r.horizon in GRASS 5.x

   NOTES
   To debug this file #define DEBUG in global_vars.h because you also
   need debug-only functions in list.c

   Bug fix on 14/08/20017 fixed failure to identify horizon in
   circumstances where the clockwise list of potentially covering cells
   ended in quad 4 but the potential horizon cell was on axis 1

 */

/***********************************************************************/

#include <math.h>
#include "global_vars.h"
#include "list.h"
#include "azimuth.h"
#include "sort.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

int Find_horizon(struct node *head, struct node *tail)
{
    struct node *cur;
    struct node *start_next_smallest, *start_prev_smallest;
    struct node *end_next_smallest, *end_prev_smallest;
    struct node *start_next_largest, *start_prev_largest;
    struct node *end_next_largest, *end_prev_largest;
    struct node *tmp, *test;
    struct node tmp_head, tmp_tail;

    /* struct node *tmp_head_p; */
    struct node *next_horizon;
    double stop;
    int beyond_range;
    int horizon;

    /* int i; */

    /* Check that list is not empty */

    if (head->next_smallest == tail)
        return 0;

    next_horizon = head;

    /* Sort list in order of increasing smallest azimuth */

    tail->smallest_azimuth = 999.0; /* Set tail to impossibly large value */
    head->next_smallest =
        Mergesort_increasing_smallest_azimuth(head->next_smallest, tail);

#ifdef DEBUG
    fprintf(stdout, "\nMergesorted smallest azimuth\n");
    List_print_edges_increasing_smallest_azimuth(stdout, head, tail);
#endif

    /* Sort list in order of decreasing smallest azimuth.  This does not
       overwrite the results of the previous sort because it uses a
       separate set of pointers */

    Pseudo_sort_decreasing_smallest_azimuth(head, tail);

#ifdef DEBUG
    fprintf(stdout, "\nPseudosorted smallest azimuth\n");
    List_print_edges_decreasing_smallest_azimuth(stdout, head, tail);
#endif

    /* Sort list in order of increasing largest azimuth */

    tail->largest_azimuth = 999.0; /* Set tail to impossibly large value */
    head->next_largest =
        Mergesort_increasing_largest_azimuth(head->next_largest, tail);

#ifdef DEBUG
    fprintf(stdout, "\nMergesorted largest azimuth\n");
    List_print_edges_increasing_largest_azimuth(stdout, head, tail);
#endif

    /* Sort list in order of decreasing largest azimuth.  This does not
       overwrite the results of the previous sort because it uses a
       separate set of pointers */

    Pseudo_sort_decreasing_largest_azimuth(head, tail);

#ifdef DEBUG
    fprintf(stdout, "\nPseudosorted largest azimuth\n");
    List_print_edges_decreasing_largest_azimuth(stdout, head, tail);
#endif

    /* Temporarily make closed circular lists of smallest and largest
       azimuths */

    start_next_smallest = head->next_smallest;
    cur = start_next_smallest;
    while (cur->next_smallest != tail) {
        cur = cur->next_smallest;
    }
    end_next_smallest = cur;
    cur->next_smallest = start_next_smallest;

    start_prev_smallest = head->prev_smallest;
    cur = start_prev_smallest;
    while (cur->prev_smallest != tail) {
        cur = cur->prev_smallest;
    }
    end_prev_smallest = cur;
    cur->prev_smallest = start_prev_smallest;

    start_next_largest = head->next_largest;
    cur = start_next_largest;
    while (cur->next_largest != tail) {
        cur = cur->next_largest;
    }
    end_next_largest = cur;
    cur->next_largest = start_next_largest;

    start_prev_largest = head->prev_largest;
    cur = start_prev_largest;
    while (cur->prev_largest != tail) {
        cur = cur->prev_largest;
    }
    end_prev_largest = cur;
    cur->prev_largest = start_prev_largest;

    /* Set up temporary list to hold cells being considered as
       masking horizon */

    List_init(&tmp_head, &tmp_tail);

    /***** Traverse list to find which cells are on the horizon *****/

    cur = start_next_smallest;
    do

    /* Collect a list of all cells that could alternatively be all or
       part of the far horizon between the current cell's smallest and
       largest azimuths.  Such cells meet either condition A or B
       below. */

    {

        /*****/
        /*   */
        /* A */
        /*   */

        /*****/

        /* Find cells such that: current largest >= test largest
           >current smallest.  This picks up overlapping cells at the
           anticlockwise end of the range, but potentially misses some
           at the clockwise end.  Traversing the list using the
           prev_largest index does not guarantee that the first
           inequality is met (e.g. when all edges are in one quadrant),
           so we still have to test it */

        tmp = &tmp_head;
        beyond_range = 0;
        test = cur->prev_largest;
        do {
            /* If current cell is not on an axis its range cannot be
               discontinuous (cannot include 0 degrees), so we can
               simply check that the test cell does not fall in a
               different quadrant or on larger numbered axis */

            if (cur->quad) {
                /* Test cell can only cover current cell's horizon if it
                   is in same quadrant.  Note that test cells on the
                   preceeding axis can have largest azimuths greater
                   than the smallest azimuth of current cell, but only
                   if the test cell is at a smaller centre-to-centre
                   distance from the viewpoint, in which case the
                   current cell `wins' anyway. Consequently we can
                   ignore test cells that fall on axes */

                if (test->quad == cur->quad) { /* test->quad = 0 if test cell
                                                  falls on axis */
                    /* Add to list of possible covering cells if
                       condition A is met */

                    if ((test->largest_azimuth > cur->smallest_azimuth) &&
                        (test->smallest_azimuth < cur->largest_azimuth)) {
                        /* Check that test is at greater distance from
                           viewpoint */

                        if (test->distance >= cur->distance)
                            tmp = List_insert_after(
                                test->type, test->row, test->col, test->axis,
                                test->quad, 0.0, test->smallest_azimuth, 0.0,
                                test->largest_azimuth, test->distance, tmp);
                    }
                    else
                        beyond_range = 1; /* Works because we are
                                             traversing a sorted list */
                }
                else {
                    /* If test cell is in a quadrant we must be beyond
                       range */

                    if (test->quad)
                        beyond_range = 1;

                    /* Whereas if test cell is on an axis this does not
                       guarantee that we are now beyond range */
                }
            }
            else {
                /* Since current cell is on an axis its range could be
                   discontinuous */

                /* Range must be discontinuous if current cell is on
                   axis 1, so we must adjust azimuths to provide a
                   continuous range for later processing */

                if (cur->axis == 1) {
                    /* Test cell can only cover current cell's horizon
                       if it is on axis 1 or in quadrant 1 or 4 */

                    if ((test->axis == 1) || (test->quad == 1) ||
                        (test->quad == 4)) {
                        /* Add to list of possible covering cells if
                           condition A is met */

                        /* If test cell is on axis 1 then its largest
                           azimuth must be > current cell's smallest
                           azimuth (although in practice is is smaller
                           owing to cell stradling 0 degrees) */

                        if (test->axis == 1) {
                            /* Check that test is at greater distance
                               from viewpoint */
                            if (test->distance >= cur->distance)
                                tmp = List_insert_after(
                                    test->type, test->row, test->col,
                                    test->axis, test->quad, 0.0,
                                    test->smallest_azimuth, 0.0,
                                    test->largest_azimuth + 360.0,
                                    test->distance, tmp);
                        }
                        else {
                            /* If test cell is in quad 1 then its
                               largest azimuth must be > current cell's
                               smallest azimuth (although in practice is
                               is smaller owing to cell stradling 0
                               degrees). */

                            if (test->quad == 1) {
                                /* But we still need to check that test
                                   cell's smallest azimuth is less than
                                   current cell's largest; the
                                   inequality for this is as expected */

                                if (test->smallest_azimuth <
                                    cur->largest_azimuth)

                                    /* Check that test is at greater
                                       distance from viewpoint */
                                    if (test->distance >= cur->distance)
                                        tmp = List_insert_after(
                                            test->type, test->row, test->col,
                                            test->axis, test->quad, 0.0,
                                            test->smallest_azimuth + 360.0, 0.0,
                                            test->largest_azimuth + 360.0,
                                            test->distance, tmp);
                            }
                            else
                            /* Test cell is in quad 4 and doesn't
                               straddle 0 degrees, so inequalities are
                               as expected.  In this case test cell's
                               smallest azimuth must be less than
                               current cell's largest (although in
                               practice is is smaller owing to range
                               stradling 0 degrees) */
                            {
                                if (test->largest_azimuth >
                                    cur->smallest_azimuth) {
                                    /* Check that test is at greater
                                       distance from viewpoint */

                                    if (test->distance >= cur->distance)
                                        tmp = List_insert_after(
                                            test->type, test->row, test->col,
                                            test->axis, test->quad, 0.0,
                                            test->smallest_azimuth, 0.0,
                                            test->largest_azimuth,
                                            test->distance, tmp);
                                }
                                else
                                    beyond_range = 1;
                            }
                        }
                    }
                    else
                        beyond_range = 1;
                }
                else
                /* current cell is on axis 2, 3 or 4.
                   Consequently there can be no problem with cells
                   stradling 0 degrees */
                {

                    /* Test cell can only cover current cell's horizon
                       if it is on same axis or in an adjacent quadrant */

                    if ((test->axis == cur->axis) ||
                        (test->quad == (cur->axis - 1)) || /* anticlockwise */
                        (test->quad == cur->axis)) {       /* clockwise */
                        /* Add to list of possible covering cells if
                           condition A is met.  */

                        if ((test->largest_azimuth > cur->smallest_azimuth) &&
                            (test->smallest_azimuth < cur->largest_azimuth)) {
                            /* Check that test is at greater
                               distance from viewpoint */

                            if (test->distance >= cur->distance)
                                tmp = List_insert_after(
                                    test->type, test->row, test->col,
                                    test->axis, test->quad, 0.0,
                                    test->smallest_azimuth, 0.0,
                                    test->largest_azimuth, test->distance, tmp);
                        }
                        else
                            beyond_range = 1;
                    }
                    else
                        beyond_range = 1;
                }
            }
            test = test->prev_largest;
        } while (!beyond_range);

        /*****/
        /*   */
        /* B */
        /*   */

        /*****/

        /* Now find cells such that: current largest > test smallest >=
           cur smallest.  This picks up overlapping cells at the
           clockwise end of the range, but potentially misses some at
           the anti clockwise end. We ignore those already picked up in
           A. */

        beyond_range = 0;
        test = cur->next_smallest;
        do {

            /* If current cell is not on an axis its range cannot be
               discontinuous (cannot include 0 degrees), so we can
               simply check that the test cell does not fall in a
               different quadrant or on larger numbered axis */

            if (cur->quad) {
                /* Test cell can only cover current cell's horizon if it
                   is in same quadrant.  Note that test cells on the
                   following axis can have smallest azimuths less
                   than the largest azimuth of current cell, but only
                   if the test cell is at a smaller centre-to-centre
                   distance from the viewpoint, in which case the
                   current cell `wins' anyway. Consequently we can
                   ignore test cells that fall on axes */

                if (test->quad == cur->quad) { /* test->quad = 0 if
                                                  test cell falls on
                                                  axis */
                    /* Add to list of possible covering cells if
                       condition B is met */

                    if ((test->smallest_azimuth < cur->largest_azimuth) &&
                        (test->largest_azimuth > cur->smallest_azimuth)) {
                        /* Prevent duplicate entries for cells picked up
                           in A */

                        if (test->largest_azimuth >= cur->largest_azimuth)

                            /* Check that test is at greater distance from
                               viewpoint */

                            if (test->distance >= cur->distance)
                                tmp = List_insert_after(
                                    test->type, test->row, test->col,
                                    test->axis, test->quad, 0.0,
                                    test->smallest_azimuth, 0.0,
                                    test->largest_azimuth, test->distance, tmp);
                    }
                    else
                        beyond_range = 1; /* Works because we are
                                             traversing a sorted list */
                }
                else {
                    /* If test cell is in a quadrant we must be beyond
                       range */

                    if (test->quad)
                        beyond_range = 1;

                    /* Whereas if test cell is on an axis this does not
                       guarantee that we are now beyond range */
                }
            }
            else {
                /* Since current cell is on an axis its range could be
                   discontinuous */

                /* Range must be discontinuous if current cell is on
                   axis 1, so we must adjust azimuths to provide a
                   continuous range for later processing */

                if (cur->axis == 1) {
                    /* Test cell can only cover current cell's horizon
                       if it is on axis 1 or in quadrant 1 or 4 */

                    if ((test->axis == 1) || (test->quad == 1) ||
                        (test->quad == 4)) {
                        /* Add to list of possible covering cells if
                           condition B is met */

                        /* If test cell is on axis its smallest
                           azimuth must be < current cell's largest
                           azimuth (although in practice is is
                           greater owing to cell stradling 0
                           degrees) */

                        if (test->axis == 1) {
                            /* Prevent duplicate entries for cells
                               picked up in A */
                            if (test->largest_azimuth >= cur->largest_azimuth)

                                /* Check that test is at greater distance
                                   from viewpoint */
                                if (test->distance >= cur->distance)
                                    tmp = List_insert_after(
                                        test->type, test->row, test->col,
                                        test->axis, test->quad, 0.0,
                                        test->smallest_azimuth, 0.0,
                                        test->largest_azimuth + 360.0,
                                        test->distance, tmp);
                        }
                        else
                        /* If Test cell is in quad 1 then doesn't
                           straddle 0 degrees and inequalities are as
                           expected.  Test cell's largest azimuth must
                           be greater than current cell's smallest
                           azimuth (although in practice is is less
                           owing to range stradling 0 degrees) */

                        {
                            if (test->quad == 1) {
                                if (test->smallest_azimuth <
                                    cur->largest_azimuth) {

                                    /* Prevent duplicate entries for
                                       cells picked up in A */

                                    if (test->largest_azimuth >=
                                        cur->largest_azimuth)

                                        /* Check that test is at greater
                                           distance from viewpoint */

                                        if (test->distance >= cur->distance)
                                            tmp = List_insert_after(
                                                test->type, test->row,
                                                test->col, test->axis,
                                                test->quad, 0.0,
                                                test->smallest_azimuth + 360.0,
                                                0.0,
                                                test->largest_azimuth + 360.0,
                                                test->distance, tmp);
                                }
                                else
                                    beyond_range = 1;
                            }
                            else
                            /* Test cell is in quad 4 so its
                               smallest azimuth must be less than
                               the current cell's greatest azimuth
                               (even though in practice it will be
                               larger due to straddling 0
                               degrees).  Equally, however, test's
                               largest must be smaller than
                               current's largest, so it must
                               already have been picked up in A,
                               so do nothing.  However, if test
                               cell's largest is less than current
                               cell's smallest, then we are beyond
                               range */
                            {
                                if (test->largest_azimuth <
                                    cur->smallest_azimuth)
                                    beyond_range = 1;
                            }
                        }
                    }
                    else
                        beyond_range = 1;
                }
                else
                /* current cell is on axis 2, 3 or 4.
                   Consequently there can be no problem with cells
                   stradling 0 degrees */
                {

                    /* Test cell can only cover current cell's
                       horizon if it is on same axis or in
                       adjacent quadrants */

                    if ((test->axis == cur->axis) ||
                        (test->quad == (cur->axis - 1)) || /* anticlockwise */
                        (test->quad == cur->axis)) {       /* clockwise */
                        /* Add to list of possible covering cells if
                           condition B is met */

                        if ((test->smallest_azimuth < cur->largest_azimuth) &&
                            (test->largest_azimuth > cur->smallest_azimuth)) {
                            /* Prevent duplicate entries for cells
                               picked up in A */

                            if (test->largest_azimuth >= cur->largest_azimuth)

                                /* Check that test is at greater distance
                                   from viewpoint */

                                if (test->distance >= cur->distance)
                                    tmp = List_insert_after(
                                        test->type, test->row, test->col,
                                        test->axis, test->quad, 0.0,
                                        test->smallest_azimuth, 0.0,
                                        test->largest_azimuth, test->distance,
                                        tmp);
                        }
                        else
                            beyond_range = 1;
                    }
                    else
                        beyond_range = 1;
                }
            }
            test = test->next_smallest;
        } while (!beyond_range);

        /* If the temporary list is empty, then the current cell is
           definitely a horizon cell */

        if (tmp_head.next_smallest == &tmp_tail)
            horizon = 1;
        else
        /*  If list is not empty, then current cell may or may not be
           on horizon */
        {
            /* Sort temporary list */

            tmp_tail.smallest_azimuth = 999.0; /* Set tail to impossibly large
                                                  value */
            Mergesort_increasing_smallest_azimuth(&tmp_head, &tmp_tail);
            /* tmp_head_p = Mergesort_increasing_smallest_azimuth (&tmp_head, */
            /*                                                  &tmp_tail); */
            Pseudo_sort_decreasing_smallest_azimuth(&tmp_head, &tmp_tail);

            horizon = 0;
            test = tmp_head.next_smallest;
            stop = test->smallest_azimuth;

            /* If there is more than one cell then we must find whether
               they are contiguous.  Note though, that we don't need to
               check the contiguity of last cell */

            if (test->next_smallest != &tmp_tail) { /* I.e. more than cell */
                while (test != &tmp_tail) {
                    /* MWL debug */
                    /* if ((cur->col == 1084) && (cur->row=1553)) */
                    /* if (cur->col == 893) */
                    /*   fprintf
                     * (stderr,"\nCol,%d,Row,%d,Dist,%lf,Az,%d,Qd,%d,SAz,%lf,CAz,%lf,LAz,%lf,|,Col,%d,Row,%d,Dist,%lf,Ax,%d,Qd,%d,SAz,%lf,LAz,%lf",cur->col,cur->row,cur->distance,cur->axis,cur->quad,cur->smallest_azimuth,cur->centre_azimuth,cur->largest_azimuth,test->col,test->row,test->distance,test->axis,test->quad,test->smallest_azimuth,test->largest_azimuth);
                     */
                    if (test->largest_azimuth > stop) {
                        stop = test->largest_azimuth;
                    }
                    /* Only check for contiguity if not last cell */

                    if (test->next_smallest != &tmp_tail) {
                        if (test->next_smallest->smallest_azimuth > stop) {
                            horizon = 1;
                            break;
                        }
                    }
                    test = test->next_smallest;
                }

                /* If cell is not thought to be on horizon
                   (i.e. covering cells are contiguous) then we must
                   check whether contiguous range does in fact cover
                   cell's full range */

                if (!horizon) {
                    if ((cur->axis == 1) && (stop <= 360.0)) {
                        /* By definition covering cells ending in quad 4
                           can not completly cover a cell on axis 1.  A
                           bug fix by MWL on 2017-08-14 */
                        horizon = 1;
                    }
                    else {
                        if ((tmp_head.next_smallest->smallest_azimuth >
                             cur->smallest_azimuth) ||
                            (stop < cur->largest_azimuth))
                            horizon = 1;
                    }
                }
            }
            else
            /* The geometry of a raster map ensures that exactly one
               cell at a greater distance cannot completely cover
               another that is closer to the viewpoint */
            {
                horizon = 1;
            }
        }

        /* If current cell is on horizon add it to the list of horizon
           cells */

        /* MWL debug */
        /* if (cur->col == 1084) */
        /*        fprintf (stderr,"\nCol=%d Row=%d,
         * onHoz=%d",cur->col,cur->row,horizon); */

        if (horizon)
            next_horizon = List_add_to_horizon_list_after(cur, next_horizon);

        tmp = &tmp_head;
        /* i = 0; */
        while (tmp->next_smallest != &tmp_tail) {

            List_delete_smallest_after(&tmp_head);
        }
        cur = cur->next_smallest;
    } while (cur != start_next_smallest);

    /* Restore lists to linear form with head and tail nodes */

    next_horizon->next_horizon = tail;
    head->next_smallest = start_next_smallest;
    end_next_smallest->next_smallest = tail;
    head->prev_smallest = start_prev_smallest;
    end_prev_smallest->prev_smallest = tail;
    head->next_largest = start_next_largest;
    end_next_largest->next_largest = tail;
    head->prev_largest = start_prev_largest;
    end_prev_largest->prev_largest = tail;

    /* Sort horizon cells in order of increasing centre azimuth */

    tail->centre_azimuth = 999.0; /* Set tail to impossibly large value */
    head->next_horizon =
        Mergesort_increasing_centre_horizon_azimuth(head->next_horizon, tail);

#ifdef DEBUG
    fprintf(stdout, "\nMergesorted central azimuth, horizon only\n");
    List_print_horizon_increasing_centre_azimuth(stdout, head, tail);
#endif

    return 1;
}
