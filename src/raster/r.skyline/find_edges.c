/***********************************************************************/
/*
   find_edges.c

   Revised by Mark Lake, 26/07/20017, for r.horizon in GRASS 7.x
   In GRASS 7.x both r.los and r.viewshed code cells that are not visible
   NULL, irrespective of whether they fall within the max viewing
   distance

   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 15/07/2002, for r.horizon in GRASS 5.x

   NOTES

   Edge types are coded:
   3 = falls at edge of region  (may also be 2 or 1)
   2 = falls on max viewing distance (may also be 1)
   1 = real edge (neither 3 nor 2)
   0 = not an edge according to any of the above definitions

   r.los codes cells outside the max. viewing distance, 0, and cells
   within the max. viewing distance but not in the viewshed, NULL.
   Consequently, if any of a potential edge cell's neighbours is coded
   NULL then that potential edge cell must be a real edge,
   irrespective of whether it falls on edge of the region or at the
   maximum viewing distance.  However, the fact that a cell falls on a
   real edge does not guarantee that it would be a real far horizon,
   since there might be neighbouring cells outside the region, or
   beyond the maximum viewing distance, which fall with the viewshed -
   we just don't know.  For that reason we ensure that edge types are
   attributed such that 3 overides 2 overides 1

 */

/***********************************************************************/

#include <math.h>
#include "global_vars.h"
#include "list.h"
#include "azimuth.h"
#include "raster_file.h"

/***********************************************************************/
/* Prototypes for private functions                                    */

/***********************************************************************/

int check_if_real_edge(int, int, int, int, int, void *);
void find_edges_no_checking(int, int, int, int, int, int, void *, struct node *,
                            CELL);
void find_edges_check_max_dist(int, int, int, int, int, int, void *,
                               struct node *, CELL);

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

void find_edges(int nrows, int ncols, void *map_buf, struct node *edge_cur)
{
    double orthogonal_dist;
    int orthogonal_ew_cells, orthogonal_ns_cells;
    int box2 = 1;
    int box3 = 1;
    int box4 = 1;
    int box5 = 1;
    int e_box1, w_box1, n_box1, s_box1;
    int e_box2, w_box2, n_box2, s_box2;
    int e_box3, w_box3, n_box3, s_box3;
    int e_box4, w_box4, n_box4, s_box4;
    int e_box5, w_box5, n_box5, s_box5;

    /* Calc bounding box for cells that must be within max distance.
       Idea here is to improve speed of execution by ensuring that we do
       not have to check distance of majority of cells.  This revision
       fixes bug where cells in corner of box1 fall on max viewing
       distance but can never be identified as such as they are within
       box1.  Fix was to reduce sixe of box1 by 1 cell in each
       direction. */

    orthogonal_dist = sqrt((max_dist * max_dist) / 2);
    orthogonal_ew_cells = floor(orthogonal_dist / window.ew_res);
    e_box1 = viewpt_col + orthogonal_ew_cells - 1; /* col origin at west */
    w_box1 = viewpt_col - orthogonal_ew_cells + 1;
    /* e_box1 = viewpt_col + orthogonal_ew_cells; /\* col origin at west *\/ */
    /* w_box1 = viewpt_col - orthogonal_ew_cells; */
    orthogonal_ns_cells = floor(orthogonal_dist / window.ns_res);
    n_box1 = viewpt_row - orthogonal_ns_cells + 1; /* row origin at north */
    s_box1 = viewpt_row + orthogonal_ns_cells - 1;
    /* n_box1 = viewpt_row - orthogonal_ns_cells; /\* row origin at north *\/ */
    /* s_box1 = viewpt_row + orthogonal_ns_cells; */

    /* Adjust central bounding box if it is clipped by current region */

    if (e_box1 >= e_col) {
        e_box1 = e_col;
        box5 = 0;
    }

    if (w_box1 <= w_col) {
        w_box1 = w_col;
        box4 = 0;
    }

    if (n_box1 <= n_row) {
        n_box1 = n_row;
        box2 = 0;
    }

    if (s_box1 >= s_row) {
        s_box1 = s_row;
        box3 = 0;
    }

    /* Calc bounding boxes for cells not within central box */

    if (box2) {
        if (box5)
            e_box2 = e_box1 + 2;
        else
            e_box2 = e_box1;
        if (box4)
            w_box2 = w_box1 - 2;
        else
            w_box2 = w_box1;
        n_box2 = n_row;
        s_box2 = n_box1 - 1;
    }

    if (box3) {
        if (box5)
            e_box3 = e_box1 + 2;
        else
            e_box3 = e_box1;
        if (box4)
            w_box3 = w_box1 - 2;
        else
            w_box3 = w_box1;
        n_box3 = s_box1 + 1;
        s_box3 = s_row;
    }

    if (box4) {
        e_box4 = w_box1 - 1;
        w_box4 = w_col;
        if (box2)
            n_box4 = n_box1;
        else
            n_box4 = n_box1;
        if (box3)
            s_box4 = s_box1;
        else
            s_box4 = s_box1;
    }

    if (box5) {
        e_box5 = e_col;
        w_box5 = e_box1 + 1;
        if (box2)
            n_box5 = n_box1;
        else
            n_box5 = n_box1;
        if (box3)
            s_box5 = s_box1;
        else
            s_box5 = s_box1;
    }

    /*  Find edges in boxes */
    find_edges_no_checking(e_box1, w_box1, n_box1, s_box1, nrows, ncols,
                           map_buf, edge_cur, 1);
    if (box2)
        find_edges_check_max_dist(e_box2, w_box2, n_box2, s_box2, nrows, ncols,
                                  map_buf, edge_cur, 2);
    if (box3)
        find_edges_check_max_dist(e_box3, w_box3, n_box3, s_box3, nrows, ncols,
                                  map_buf, edge_cur, 3);
    if (box4)
        find_edges_check_max_dist(e_box4, w_box4, n_box4, s_box4, nrows, ncols,
                                  map_buf, edge_cur, 4);
    if (box5)
        find_edges_check_max_dist(e_box5, w_box5, n_box5, s_box5, nrows, ncols,
                                  map_buf, edge_cur, 5);
}

/***********************************************************************/
/* Private functions                                                   */

/***********************************************************************/

void find_edges_no_checking(int e, int w, int n, int s, int nrows, int ncols,
                            void *map_buf, struct node *edge_cur, CELL box)

/* Any cells examined in this function can not fall at max. viewing
   distance so can not be type 2 */
{
    int row, col;
    int edge;
    DCELL data;
    int axis, quad;
    double smallest_azimuth, centre_azimuth, largest_azimuth;
    double distance;

    /* Check all cells in box */

    for (row = n; row <= s; row++) { /* row origin at north */
        for (col = w; col <= e; col++) {
            edge = 0;
            data = Get_buffer_value_d_row_col(map_buf, viewshed_buf_cell_type,
                                              row, col);
            /* If cell is in viewshed */
            if (!(Rast_is_null_value(&data, viewshed_buf_cell_type)))
            /* if (data > 0.0) */
            {
                /* If cell falls on edge of region */

                if (row == n_row || row == s_row || col == w_col ||
                    col == e_col)
                    edge = 3;
                else {
                    /* We now know cell is not at max. viewing distance
                       (type 2) or on edge of region (type 3), but is it a real
                       edge (type 1)? */

                    edge = check_if_real_edge(row, col, nrows, ncols, edge,
                                              map_buf);
                }
                /* Process an edge (type 3, 2 or 1)
                   if not also viewpoint */

                if (edge && !((row == viewpt_row) && (col == viewpt_col))) {
                    calc_azimuth(row, col, &axis, &quad, &smallest_azimuth,
                                 &centre_azimuth, &largest_azimuth, &distance);
                    List_insert_after(edge, row, col, axis, quad, data,
                                      smallest_azimuth, centre_azimuth,
                                      largest_azimuth, distance, edge_cur);
                }
            }
        }
    }
}

/***********************************************************************/

void find_edges_check_max_dist(int e, int w, int n, int s, int nrows, int ncols,
                               void *map_buf, struct node *edge_cur, CELL box)

/* Any cells examined in this function could fall at max. viewing
   distance so we must check this.  Note that this could be achieved
   by investigating whether neighbouring cells have values of zero,
   but we use trigonometry instead */
{
    int row, col;
    int edge;
    DCELL data;
    double max_rad_distance, min_rad_distance;
    double alpha;
    double x, y;
    int axis, quad;
    double smallest_azimuth, centre_azimuth, largest_azimuth;
    double distance;

    /* Check all cells */

    for (row = n; row <= s; row++) { /* row origin at north */
        for (col = w; col <= e; col++) {
            edge = 0;
            data = Get_buffer_value_d_row_col(map_buf, viewshed_buf_cell_type,
                                              row, col);
            if (!(Rast_is_null_value(&data, viewshed_buf_cell_type)))
            /* if (data > 0.0) */

            /* Check whether within or at max distance */
            {
                /* Calc orthogonal distances from centre of viewpoint to
                   centre of cell */

                if ((col - viewpt_col) == 0)
                    x = 0;
                else
                    x = (fabs((double)(col - viewpt_col) * window.ew_res));
                if ((row - viewpt_row) == 0)
                    y = 0;
                else
                    y = (fabs((double)(row - viewpt_row) * window.ns_res));

                /* Now calc alpha */

                if (x == 0)
                    alpha = 3.1415926535899 / 2; /* 90 degrees in radians */
                else
                    alpha = atan(y / x);

                /* Calc max and min radial (i.e. centre-to-centre)
                   distances that fall within this cell.  Do this using
                   largest side of the triangle to minimise errors.
                   Previous versions set min and max rad distances to
                   0.5 * cell resolution (e.g. min_rad_distance = (x -
                   (0.5 * window.ew_res))), but this is too fine a
                   tolerance in that it fails to pick up some horizon
                   cells that are clearly so owing to being at max
                   distance, so I've changed it to cell 1.0 * cell
                   resolution */

                /* if (x >= y)  */
                /*        { */
                /*          min_rad_distance = (x - (0.5 * window.ew_res)) / cos
                 * (alpha); */
                /*          max_rad_distance = (x + (0.5 * window.ew_res)) / cos
                 * (alpha); */
                /*        } */
                /* else */
                /*        { */
                /*          if (alpha == 0) */
                /*            { */
                /*              min_rad_distance = y - (0.5 * window.ns_res); */
                /*              max_rad_distance = y + (0.5 * window.ns_res); */
                /*            } */
                /*          else */
                /*            { */
                /*              min_rad_distance = (y - (0.5 * window.ns_res)) /
                 * sin (alpha); */
                /*              max_rad_distance = (y + (0.5 * window.ns_res)) /
                 * sin (alpha); */
                /*            } */
                /*        } */

                if (x >= y) {
                    min_rad_distance = (x - window.ew_res) / cos(alpha);
                    max_rad_distance = (x + window.ew_res) / cos(alpha);
                }
                else {
                    if (alpha == 0) {
                        min_rad_distance = y - window.ns_res;
                        max_rad_distance = y + window.ns_res;
                    }
                    else {
                        min_rad_distance = (y - window.ns_res) / sin(alpha);
                        max_rad_distance = (y + window.ns_res) / sin(alpha);
                    }
                }

                /* Check whether max distance falls within this cell, in
                   which case cell is at max. distance (type 2). */

                if (max_dist > min_rad_distance && max_dist <= max_rad_distance)
                    edge = 2;

                /* If cell is within or at max dist */

                if (max_dist >= min_rad_distance) {
                    /* If cell falls on the edge of the region, set edge
                       type to 3 */

                    if (row == n_row || row == s_row || col == w_col ||
                        col == e_col)
                        edge = 3;
                    else {
                        /* If cell does not fall on edge of region (type
                           3) and is not at max. viewing distance (type
                           2) check whether it is a real edge (type
                           1) */
                        if (edge != 2)
                            edge = check_if_real_edge(row, col, nrows, ncols,
                                                      edge, map_buf);
                    }
                }

                /* Process an edge (type 3, 2 or 1) if not also
                   viewpoint */

                if (edge && !((row == viewpt_row) && (col == viewpt_col))) {
                    calc_azimuth(row, col, &axis, &quad, &smallest_azimuth,
                                 &centre_azimuth, &largest_azimuth, &distance);

                    List_insert_after(edge, row, col, axis, quad, data,
                                      smallest_azimuth, centre_azimuth,
                                      largest_azimuth, distance, edge_cur);
                }
            }
        }
    }
}

/***********************************************************************/

int check_if_real_edge(int row, int col, int nrows, int ncols, int edge,
                       void *map_buf)

/* Cells examined in this function do not fall at max. viewing
   distance or on edge of region, so they are either real edges (type
   1) or not edges (type 0) */
{
    int test_row, test_col;
    DCELL data_to_test;

    if (edge != 0)
        return edge; /* Shouldn't get here if function called appropriately */

    for (test_row = row - 1; test_row <= row + 1; test_row++) {
        if (edge == 1)
            break;

        for (test_col = col - 1; test_col <= col + 1; test_col++) {
            if (edge == 1)
                break;

            /* N.B: no need to check whether 'test_row' and 'test_col' fall
               within current region because this function is not called
               for potential edge cells that fall on the edge of the
               current region, therefore cells in neighbourhood +/- 1
               must be within current region */

            data_to_test = Get_buffer_value_d_row_col(
                map_buf, viewshed_buf_cell_type, test_row, test_col);

            /* If any of neighbouring cells = NULL then this cell must
               fall on real edge (type 1), because we already know that
               it does not fall on edge of region (type 3) or at
               max. viewing distance (type 2) */

            if (Rast_is_null_value(&data_to_test, viewshed_buf_cell_type))
                edge = 1;
        }
    }
    return edge;
}
