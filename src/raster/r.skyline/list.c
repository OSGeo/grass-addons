/***********************************************************************/
/*
   list.c

   Revised by Mark Lake, 28/07/20017, for r.skyline in GRASS 7.x
   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 15/07/2002, for r.horizon in GRASS 5.x

   NOTES
   This implementation of a linked list uses a fixed head and tail node,
   neither of which contain data.  This means that the first data node
   is obtained via the head 'next' and 'prev' pointers (e.g.
   head->next_smallest, etc.).

   List_get_length returns the number of data items (i.e. the total
   number of nodes minus the fixed head and tail).

 */

/***********************************************************************/

#include <stdlib.h>
#include <math.h>
#include "global_vars.h"
#include "list.h"
#include "raster_file.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

struct node *List_add_to_horizon_list_after(struct node *this,
                                            struct node *after)
{
    this->next_horizon = after->next_horizon;
    after->next_horizon = this;
    return this;
}

/***********************************************************************/

struct node *List_first_horizon_quad1(struct node *edge_head)
{
    /* See azimuth.c for the definition of quad and axis */

    int this_axis;
    struct node *cur;

    cur = edge_head->next_horizon;
    while (cur != cur->next_horizon) {
        this_axis = cur->axis;
        if (this_axis == 1) {
            if (cur != edge_head->next_horizon)
                G_fatal_error(_("first cell on axis 1 not at start of list of "
                                "horizon cells (programming error)"));
            return cur;
        }
        cur = cur->next_horizon;
    }
    G_fatal_error(_("no horizon cells on axis 1 (programming error)"));
}

/***********************************************************************/

struct node *List_first_horizon_quad2(struct node *edge_head)
{
    int this_axis;
    struct node *cur;

    cur = edge_head->next_horizon;
    while (cur != cur->next_horizon) {
        this_axis = cur->axis;
        if (this_axis == 2) {
            return cur;
        }
        cur = cur->next_horizon;
    }
    G_fatal_error(_("no horizon cells on axis 2 (programming error)"));
}

/***********************************************************************/

struct node *List_first_horizon_quad3(struct node *edge_head)
{
    int this_axis;
    struct node *cur;

    cur = edge_head->next_horizon;
    while (cur != cur->next_horizon) {
        this_axis = cur->axis;
        if (this_axis == 3) {
            return cur;
        }
        cur = cur->next_horizon;
    }
    G_fatal_error(_("no horizon cells on axis 3 (programming error)"));
}

/***********************************************************************/

struct node *List_first_horizon_quad4(struct node *edge_head)
{
    int this_axis;
    struct node *cur;

    cur = edge_head->next_horizon;
    while (cur != cur->next_horizon) {
        this_axis = cur->axis;
        if (this_axis == 4) {
            return cur;
        }
        cur = cur->next_horizon;
    }
    G_fatal_error(_("no horizon cells on axis 4 (programming error)"));
}

/***********************************************************************/

void List_delete_smallest_after(struct node *cur)
{
    struct node *node_to_delete;

    node_to_delete = cur->next_smallest;
    cur->next_smallest = node_to_delete->next_smallest;

    /* N.B. Following requires external check that cur->next_smallest is
       not tail */

    free(node_to_delete);
}

/***********************************************************************/

int List_get_length(struct node *head)
{
    struct node *cur;
    int count = 0;

    cur = head->next_smallest;
    while (cur != cur->next_smallest) {
        count++;
        cur = cur->next_smallest;
    }
    return count;
}

/***********************************************************************/

void List_init(struct node *head, struct node *tail)
{
    head->prev_smallest = tail;
    head->next_smallest = tail;
    head->prev_largest = tail;
    head->next_largest = tail;
    head->next_horizon = tail;
    tail->prev_smallest = tail;
    tail->next_smallest = tail;
    tail->prev_largest = tail;
    tail->next_largest = tail;
    tail->next_horizon = tail;
}

/***********************************************************************/

struct node *List_insert_after(int type, int row, int col, int axis, int quad,
                               double inclination, double smallest_azimuth,
                               double centre_azimuth, double largest_azimuth,
                               double distance, struct node *cur)
{
    struct node *new;

    new = (struct node *)malloc(sizeof(struct node));
    if (new == NULL)
        G_fatal_error("Out of memory while creating list of edges ");
    new->type = type;
    new->row = row;
    new->col = col;
    new->axis = axis;
    new->quad = quad;
    new->inclination = inclination;
    new->smallest_azimuth = smallest_azimuth;
    new->centre_azimuth = centre_azimuth;
    new->largest_azimuth = largest_azimuth;
    new->distance = distance;
    new->elevation = 0.0;

    /* Initialise next_smallest and next_largest pointers because all
       cells must be in these lists
       Note: we use next_smallest as pointer sequence for building and deleting
       lists, the others don't make sense until the list is explicitly sorted
       on them */

    new->prev_smallest = cur->prev_smallest;
    new->next_smallest = cur->next_smallest;
    cur->prev_smallest = new;
    cur->next_smallest = new;
    new->prev_largest = cur->prev_largest;
    new->next_largest = cur->next_largest;
    cur->prev_largest = new;
    cur->next_largest = new;

    /* Initialise next_horizon pointers with NULL because not all
       cells will be horizon cells */

    new->next_horizon = NULL;

    return new;
}

/***********************************************************************/

struct node *List_next_horizon(struct node *cur)
{
    return cur->next_horizon;
}

/***********************************************************************/

struct node *List_next_largest(struct node *cur)
{
    return cur->next_largest;
}

/***********************************************************************/

struct node *List_next_smallest(struct node *cur)
{
    return cur->next_smallest;
}

/***********************************************************************/

struct node *List_prev_largest(struct node *cur)
{
    return cur->prev_largest;
}

/***********************************************************************/

struct node *List_prev_smallest(struct node *cur)
{
    return cur->prev_smallest;
}

/***********************************************************************/

void List_print_entry(FILE *stream, struct node *cur)
{
    fprintf(stream, "%3.4lf,%3.4lf,%5.4lf,%5.2lf,%d\n", cur->centre_azimuth,
            cur->inclination, cur->distance, cur->elevation, cur->type);
    fflush(stream);
}

/***********************************************************************/

void List_print_entry_all(FILE *stream, struct node *cur)
{
    fprintf(stream,
            "CAz=,%1.4lf,SAz=,%1.4lf,LAz=,%1.4lf,Inc=,%1.2lf,Dst=,%1.2lf,Elv=,%"
            "1.2lf,Typ=,%d,Qd=,%d,Ax=,%d,Rw=,%d,Cl=,%d\n",
            cur->centre_azimuth, cur->smallest_azimuth, cur->largest_azimuth,
            cur->inclination, cur->distance, cur->elevation, cur->type,
            cur->quad, cur->axis, cur->row, cur->col);
    fflush(stream);
}

/***********************************************************************/

void List_print_entry_no_elev(FILE *stream, struct node *cur)
{
    fprintf(stream, "%3.4lf,%3.4lf,%5.2lf,%d\n", cur->centre_azimuth,
            cur->inclination, cur->distance, cur->type);
    fflush(stream);
}

/***********************************************************************/

void List_retrieve_elevation_from_buf(void *map_buf, struct node *this,
                                      RASTER_MAP_TYPE buf_type)
{
    this->elevation =
        Get_buffer_value_d_row_col(map_buf, buf_type, this->row, this->col);
}

/***********************************************************************/

void List_retrieve_inclination_from_buf(void *map_buf, struct node *this,
                                        RASTER_MAP_TYPE buf_type)
{
    this->inclination =
        Get_buffer_value_d_row_col(map_buf, buf_type, this->row, this->col);
}

/***********************************************************************/

double List_return_diff_from_azimuth(struct node *cur, double azimuth)
/* If this cell covers the azimuth return the distance from the
   centre, else return an impossibly large value > 360 */
{
    double diff = 0;

    if (cur->smallest_azimuth <= cur->largest_azimuth) {
        diff = abs(azimuth - cur->centre_azimuth);
        if ((azimuth >= cur->smallest_azimuth) &&
            (azimuth <= cur->largest_azimuth))
            return diff;
        else
            return 999;
    }
    else
    /* Straddling zero degrees, so matching azimuth may be smaller
       than both extremes, or greater than both extremes, and it may
       be greater or smaller than the centre */
    {
        if (cur->centre_azimuth > cur->largest_azimuth)
            diff = abs(azimuth - (360 - cur->centre_azimuth));
        else
            diff = abs(azimuth - cur->centre_azimuth);

        if ((azimuth <= cur->smallest_azimuth) &&
            (azimuth <= cur->largest_azimuth))
            return diff;
        else {
            if ((azimuth >= cur->smallest_azimuth) &&
                (azimuth >= cur->largest_azimuth))
                return diff;
            else
                return 999;
        }
    }
}

/***********************************************************************/

int List_return_horizon_type(struct node *cur)
{
    return cur->type;
}

/***********************************************************************/

double List_return_inclination(struct node *cur)
{
    return cur->inclination;
}

/***********************************************************************/

int List_return_quad(struct node *cur)
{
    return cur->quad;
}

/***********************************************************************/

void List_write_azimuth_to_buf(void *map_buf, struct node *this,
                               RASTER_MAP_TYPE buf_type)
{
    Set_buffer_value_d_row_col(map_buf, this->centre_azimuth, buf_type,
                               this->row, this->col);
}

/***********************************************************************/

void List_write_inclination_to_buf(void *map_buf, struct node *this,
                                   RASTER_MAP_TYPE buf_type)
{
    Set_buffer_value_d_row_col(map_buf, this->inclination, buf_type, this->row,
                               this->col);
}

/***********************************************************************/

void List_write_type_to_buf(void *map_buf, struct node *this,
                            RASTER_MAP_TYPE buf_type)
{
    Set_buffer_value_c_row_col(map_buf, this->type, buf_type, this->row,
                               this->col);
}

/***********************************************************************/
/* Debug functions                                                     */

/***********************************************************************/

#ifdef DEBUG

void List_print_edges_decreasing_largest_azimuth(FILE *stream,
                                                 struct node *head,
                                                 struct node *tail)
{
    struct node *cur;

    fprintf(stream, "\nLength = %d", List_get_length(head));
    fprintf(stream, "\nHead=%p Head->PL=%p", head, head->prev_largest);
    cur = head->prev_largest;
    while (cur != cur->prev_largest) {
        fprintf(stream, "\nEdges This=%p PL=%p LAz=%lf", cur, cur->prev_largest,
                cur->largest_azimuth);
        cur = cur->prev_largest;
    }
    fprintf(stream, "\nTail=%p Tail->PL=%p\n", tail, tail->prev_largest);
    fflush(stream);
}

/***********************************************************************/

void List_print_edges_decreasing_smallest_azimuth(FILE *stream,
                                                  struct node *head,
                                                  struct node *tail)
{
    struct node *cur;

    fprintf(stream, "\nLength = %d", List_get_length(head));
    fprintf(stream, "\nHead=%p Head->PS=%p", head, head->prev_smallest);
    cur = List_prev_smallest(head);
    while (cur != cur->prev_smallest) {
        fprintf(stream, "\nEdges This=%p PS=%p SAz=%lf", cur,
                cur->prev_smallest, cur->smallest_azimuth);
        cur = cur->prev_smallest;
    }
    fprintf(stream, "\nTail=%p Tail->PS=%p\n", tail, tail->prev_smallest);
    fflush(stream);
}

/***********************************************************************/

void List_print_edges_increasing_largest_azimuth(FILE *stream,
                                                 struct node *head,
                                                 struct node *tail)
{
    struct node *cur;

    fprintf(stream, "\nLength = %d", List_get_length(head));
    fprintf(stream, "\nHead=%p Head->NL=%p", head, head->next_largest);
    cur = List_next_largest(head);
    while (cur != cur->next_largest) {
        fprintf(stream, "\nEdges This=%p NL=%p SAz=%lf", cur, cur->next_largest,
                cur->largest_azimuth);
        cur = cur->next_largest;
    }
    fprintf(stream, "\nTail=%p Tail->NL=%p\n", tail, tail->next_largest);
    fflush(stream);
}

/***********************************************************************/

void List_print_edges_increasing_smallest_azimuth(FILE *stream,
                                                  struct node *head,
                                                  struct node *tail)
{
    struct node *cur;

    fprintf(stream, "\nLength = %d", List_get_length(head));
    fprintf(stream, "\nHead=%p Head->NS=%p", head, head->next_smallest);
    cur = List_next_smallest(head);
    while (cur != cur->next_smallest) {
        fprintf(stream, "\nEdges This=%p NS=%p SAz=%lf", cur,
                cur->next_smallest, cur->smallest_azimuth);
        cur = cur->next_smallest;
    }
    fprintf(stream, "\nTail=%p Tail->NS=%p\n", tail, tail->next_smallest);
    fflush(stream);
}

/***********************************************************************/

void List_print_horizon_increasing_centre_azimuth(FILE *stream,
                                                  struct node *head,
                                                  struct node *tail)
{
    struct node *cur;

    fprintf(stream, "\nHead=%p Head->NH=%p", head, head->next_horizon);
    cur = List_next_horizon(head);
    while (cur != cur->next_horizon) {
        fprintf(stream, "\nRaw This=%p NH=%p CAz=%lf", cur, cur->next_horizon,
                cur->centre_azimuth);
        cur = cur->next_horizon;
    }
    fprintf(stream, "\nTail=%p Tail->NH=%p\n", tail, tail->next_horizon);
    fflush(stream);
}

#endif
