/***********************************************************************/
/*
   skyline.c

   Written by Mark Lake, 28/07/20017, for r.skyline in GRASS 7.x

   *****

   NOTES

   compute_skyline_index () finds the inclination of the horizon cell
   opposite the given cell using an index to the first horizon cell in
   each quad in order to start searching part way through the list of
   horizon cells. This index must be set up using
   List_first_horizon_quad1 () etc. in list.c.  See azimuth.c for the
   definition of quad and axis.

   compute_skyline_index () uses a brute force approach to locating
   opposite horizon cell which ought to be optimised.  One way would be
   to build an index to the first horizon cell in each quad and then
   use this to search the appropriate quarter of the list.

   *****

   TODO



 */

/***********************************************************************/

#include "skyline.h"

/* #define DEBUG2 */
/* #define COL_OFFSET 5 */
/* #define ROW_OFFSET 1 */

/***********************************************************************/
/* Prototypes for private functions                                    */

/***********************************************************************/

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

double compute_skyline_index(int row, int col, double inclination,
                             struct node *edge_head, struct node *quad1_head,
                             struct node *quad2_head, struct node *quad3_head,
                             struct node *quad4_head)
{
    struct node *search_head;
    double opposite_inclination = 999;
    int axis, quad;
    int opposite_horizon_type;
    double distance;
    double smallest_azimuth, centre_azimuth, largest_azimuth;
    double opposite_azimuth, least_azimuth_diff, this_azimuth_diff;
    struct node *edge_cur;

    /* Reverse the inclination because we are computing for the line of
       site back from a cell in the viewshed towards the viewpoint */

    inclination = 90 + (90 - inclination);

    /* Calc azimuth */
    calc_azimuth(row, col, &axis, &quad, &smallest_azimuth, &centre_azimuth,
                 &largest_azimuth, &distance);

    G_debug(5, "\nviewptrow %d, viewptcol %d, row %d, col %d, quad %d, axis %d",
            viewpt_row, viewpt_col, row, col, quad, axis);

    if (axis == 5)
    /* axis = 5 means this is the viewpoint, so nothing to do here
       except mark the viewpoint as such */
    {
        return VIEWPT_SKYLINE;
    }

    if ((centre_azimuth >= 0) && (centre_azimuth < 180))
        opposite_azimuth = 180 + centre_azimuth;
    else
        opposite_azimuth = centre_azimuth - 180;

#ifdef DEBUG
        /* fprintf(stderr, "\nrow %d, col %d, this azimuth %.3lf, opposite
         * azimuth %.3lf", */
        /*   row, col, centre_azimuth, opposite_azimuth); */
#endif

    /* Find the inclination of the horizon cell opposite this cell.
       Here we use an index to the first horizon cell in each quad in
       order to start searching part way through the list of horizon
       cells. */

    /* The simple case is where the cell falls in a clearly defined
       quadrant (is not on an axis) */

    search_head = NULL;
    if (axis == 0) {
        switch (quad) {
        case (1):
            search_head = quad3_head;
            break;
        case (2):
            search_head = quad4_head;
            break;
        case (3):
            search_head = quad1_head;
            break;
        case (4):
            search_head = quad2_head;
            break;
        };
    }
    else
    /* The more difficult case is where the cell falls on axis 3,
       since we could then be looking for an opposite cell that
       straddles axis 1, in which case we rely on the test within
       List_return_diff_from_azimuth () to deal with this since
       quad1_head should point to the start of the list of horizon
       cells */
    {
        switch (axis) {
        case (1):
            search_head = quad3_head;
            break;
        case (2):
            search_head = quad4_head;
            break;
        case (3):
            search_head = quad1_head;
            break;
        case (4):
            search_head = quad2_head;
            break;
        case (5):
            /* Shouldn't get here */
            G_fatal_error(_("failed to skip viewpoint (programming error)"));
        };
    }
    if (search_head == NULL)
        G_fatal_error(_("failed to indentify search head (programming error)"));

    opposite_horizon_type = -1;
    least_azimuth_diff = 999;
    edge_cur = search_head;
    while (edge_cur != edge_cur->next_horizon) {
        this_azimuth_diff =
            List_return_diff_from_azimuth(edge_cur, opposite_azimuth);

#ifdef DEBUG
        /* fprintf(stderr, ", returned diff %.3lf", this_azimuth_diff);  */
#endif

#ifdef DEBUG2
        if ((col == viewpt_col + COL_OFFSET) &&
            (row == (viewpt_row + ROW_OFFSET)))
            fprintf(stderr,
                    "\nvrow %d, vcol %d row %d, col %d, searching for %.3lf, "
                    "smallest %.3lf, centre %.3lf, largest %.3lf, diff %.3lf,",
                    viewpt_row, viewpt_col, row, col, opposite_azimuth,
                    edge_cur->smallest_azimuth, edge_cur->centre_azimuth,
                    edge_cur->largest_azimuth, this_azimuth_diff);
#endif

        if (this_azimuth_diff < least_azimuth_diff) {
            least_azimuth_diff = this_azimuth_diff;
            opposite_inclination = List_return_inclination(edge_cur);
            opposite_horizon_type = List_return_horizon_type(edge_cur);
#ifdef DEBUG2
            if ((col == viewpt_col + COL_OFFSET) &&
                (row == (viewpt_row + ROW_OFFSET)))
                fprintf(stderr, " ophoz type %d, ophoz inc %.3lf\n",
                        opposite_horizon_type, opposite_inclination);
#endif
        }
        if (this_azimuth_diff > least_azimuth_diff)
            break;
        edge_cur = List_next_horizon(edge_cur);
    }

    /* If we failed to locate an opposite horizon cell (should only
       occur when considering the viewpoint itself), or if horizon is
       not 'real' (i.e. is at edge of max viewing distance or at edge of
       computational regions), then return an impossible index value
       outside the range -180 ... +180 */

    if (opposite_horizon_type != 1)
        /* G_fatal_error (_("Failed to locate opposite horizon cell ")); */
        return NO_SKYLINE;
    else
        /* If this difference is positive, then viewpoint is on skyline */
        return inclination - opposite_inclination;
}

/***********************************************************************/

double compute_skyline_index_simple(int row, int col, double inclination,
                                    struct node *edge_head)
{
    double opposite_inclination = 999;
    int axis, quad;
    int opposite_horizon_type;
    double distance;
    double smallest_azimuth, centre_azimuth, largest_azimuth;
    double opposite_azimuth, least_azimuth_diff, this_azimuth_diff;
    struct node *edge_cur;

    /* Reverse the inclination because we are computing for the line of
       site back from a cell in the viewshed towards the viewpoint */

    inclination = 90 + (90 - inclination);

    /* Calc azimuth */
    calc_azimuth(row, col, &axis, &quad, &smallest_azimuth, &centre_azimuth,
                 &largest_azimuth, &distance);

    if ((centre_azimuth >= 0) && (centre_azimuth < 180))
        opposite_azimuth = 180 + centre_azimuth;
    else
        opposite_azimuth = centre_azimuth - 180;

#ifdef DEBUG
        /* fprintf(stderr, "\nrow %d, col %d, this azimuth %.3lf, opposite
         * azimuth %.3lf", */
        /*   row, col, centre_azimuth, opposite_azimuth); */
#endif

    /* Find the inclination of the horizon cell opposite this cell.
       Here we use an inelegant brute force approach which ought to be
       optimised.  One way would be to build an index to the first
       horizon cell in each quad and then use this to search the
       appropriate quarter of the list.  */

    opposite_horizon_type = -1;
    least_azimuth_diff = 999;
    edge_cur = List_next_horizon(edge_head);
    while (edge_cur != edge_cur->next_horizon) {
        this_azimuth_diff =
            List_return_diff_from_azimuth(edge_cur, opposite_azimuth);

#ifdef DEBUG
        /* fprintf(stderr, ", returned diff %.3lf", this_azimuth_diff);  */
#endif

#ifdef DEBUG
        if ((col == viewpt_col) && (row == (viewpt_row + 1)))
            fprintf(stderr,
                    "\nrow %d, col %d, searching for %.3lf, smallest %.3lf, "
                    "centre %.3lf, largest %.3lf, diff %.3lf, ophoz type %d\n",
                    row, col, opposite_azimuth, edge_cur->smallest_azimuth,
                    edge_cur->centre_azimuth, edge_cur->largest_azimuth,
                    this_azimuth_diff, opposite_horizon_type);
#endif

        if (this_azimuth_diff < least_azimuth_diff) {
            least_azimuth_diff = this_azimuth_diff;
            opposite_inclination = List_return_inclination(edge_cur);
            opposite_horizon_type = List_return_horizon_type(edge_cur);
        }
        if (this_azimuth_diff > least_azimuth_diff)
            break;
        edge_cur = List_next_horizon(edge_cur);
    }

    /* If we failed to locate an opposite horizon cell (should only
       occur when considering the viewpoint itself), or if horizon is
       not 'real' (i.e. is at edge of max viewing distance or at edge of
       computational regions), then return an impossible index value
       outside the range -180 ... +180 */

    if (opposite_horizon_type != 1)
        /* G_fatal_error (_("Failed to locate opposite horizon cell ")); */
        return NO_SKYLINE;
    else
        /* If this difference is positive, then viewpoint is on skyline */
        return inclination - opposite_inclination;
}

/***********************************************************************/
/* Private functions                                                   */

/***********************************************************************/
