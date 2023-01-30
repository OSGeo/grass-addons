/***********************************************************************/
/*
   list.h

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

#ifndef LIST_H
#define LIST_H

#include <stdio.h>
#include "grass/gis.h"

/***********************************************************************/
/* Node structure                                                      */

/***********************************************************************/

struct node {
    int type;
    int row;
    int col;
    int axis;
    int quad;
    double inclination;
    double elevation;
    double smallest_azimuth;
    double centre_azimuth;
    double largest_azimuth;
    double distance;
    struct node *prev_smallest;
    struct node *next_smallest;
    struct node *prev_largest;
    struct node *next_largest;
    struct node *next_horizon;
};

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

struct node *List_add_to_horizon_list_after(struct node *, struct node *);

/* List_add_to_horizon_list_after (pointer to this node, pointer to node
   whose 'next horizon' will be set to this node)
   Returns pointer to node added */

void List_delete_smallest_after(struct node *);

/* List_delete_smallest_after (pointer to node whose next node in the
   'next smallest' list will be deleted) */

struct node *List_first_horizon_quad1(struct node *);

struct node *List_first_horizon_quad2(struct node *);

struct node *List_first_horizon_quad3(struct node *);

struct node *List_first_horizon_quad4(struct node *);

int List_get_length(struct node *);

/* List_get_length (pointer to head of list)
   Returns the number of data items in the list, i.e. the number of nodes
   minus 2 (the dummy head and tail) */

void List_init(struct node *, struct node *);

/* List_init (pointer to head, pointer to tail) */

struct node *List_insert_after(int, int, int, int, int, double, double, double,
                               double, double, struct node *);
/* List_insert_after (edge type, row, column, axis, quadrant, inclination,
   smallest azimuth, centre azimuth, largest azimuth, distance, pointer to
   node afetr which to add new node in the 'next smallest' list)
   Returns pointer to new node */

struct node *List_next_horizon(struct node *);

/* List_next_horizon (pointer to this node)
   Returns pointer to next node in this node's 'next horizon' list */

struct node *List_next_largest(struct node *);

/* List_next_largest (pointer to this node)
   Returns pointer to next node in this node's 'next largest' list */

struct node *List_next_smallest(struct node *);

/* List_next_smallest (pointer to this node)
   Returns pointer to next node in this node's 'next smallest' list */

struct node *List_prev_largest(struct node *);

/* List_prev_largest (pointer to this node)
   Returns pointer to next node in this node's 'previous largest' list */

struct node *List_prev_smallest(struct node *);

/* List_prev_smallest (pointer to this node)
   Returns pointer to next node in this node's 'previous smallest' list */

void List_print_entry(FILE *, struct node *);

/* List_print (filestream, pointer to node whose data will be printed) */

void List_print_entry_all(FILE *, struct node *);

/* List_print (filestream, pointer to node whose data will be printed) */

void List_print_entry_no_elev(FILE *, struct node *);

/* List_print (filestream, pointer to node whose data will be printed) */

void List_retrieve_elevation_from_buf(void *, struct node *, RASTER_MAP_TYPE);

/* List_retrieve_elevation_from_buf (pointer to buffer,
   pointer to node to store elevation, buffer data type) */

void List_retrieve_inclination_from_buf(void *, struct node *, RASTER_MAP_TYPE);
/* List_retrieve_inclination_from_raster (pointer to buffer,
   pointer to node to store inclination, buffer data type) */

double List_return_diff_from_azimuth(struct node *, double);

/* If this cell covers the azimuth return the distance from the
   centre, else return impossibly large value > 360 (pointer to
   horizon cell to check, azimuth we are searching for */

int List_return_horizon_type(struct node *);

/* List_return_horizon_type (pointer to horizon cell) */

double List_return_inclination(struct node *);

/* List_return_inclination (pointer to horizon cell) */

int List_return_quad(struct node *);

/* List_return_quad (pointer to horizon cell) */

void List_write_azimuth_to_buf(void *, struct node *, RASTER_MAP_TYPE);

/* List_write_azimuth_to_buf (pointer to buffer, pointer to node containing
   azimuth, buffer data type) */

void List_write_inclination_to_buf(void *, struct node *, RASTER_MAP_TYPE);

/* List_write_inclination_to_buf (pointer to buffer, pointer to node containing
   inclination, buffer data type) */

void List_write_type_to_buf(void *, struct node *, RASTER_MAP_TYPE);

/* List_write_type_to_buf  (pointer to buffer, pointer to node containing
   type, buffer data type) */

/***********************************************************************/
/* Debug functions                                                     */

/***********************************************************************/

#ifdef DEBUG

void List_print_edges_decreasing_largest_azimuth(FILE *, struct node *,
                                                 struct node *);
/* List_print_edges_decreasing_largest_azimuth (stream, pointer to head,
   pointer to tail */

void List_print_edges_decreasing_smallest_azimuth(FILE *, struct node *,
                                                  struct node *);
/* List_print_edges_decreasing_smallest_azimuth (stream, pointer to head,
   pointer to tail */

void List_print_edges_increasing_largest_azimuth(FILE *, struct node *,
                                                 struct node *);
/* List_print_edges_increasing_largest_azimuth (stream, pointer to head,
   pointer to tail */

void List_print_edges_increasing_smallest_azimuth(FILE *, struct node *,
                                                  struct node *);
/* List_print_edges_increasing_smallest_azimuth (stream, pointer to head,
   pointer to tail */

void List_print_horizon_increasing_centre_azimuth(FILE *, struct node *,
                                                  struct node *);
/* List_print_horizon_increasing_centre_azimuth (stream, pointer to head,
   pointer to tail */

#endif

#endif
