/***********************************************************************/
/*
   sort.c

   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 15/07/2002, for r.horizon in GRASS 5.x

   NOTES

   Mergesort uses algorithm from R. Sedgewick, 1990, 'Algorithms in C',
   Reading, MA: Addison Wesley

   When used with the functions in list.c, the mergesort functions
   require that the first data node in the list be passed as the 'head'
   and they return a pointer to the first data node.  Do not pass the
   address of the head node to the mergesort functions.  Similarly, do
   not attempt to set a pointer to the head node to the value returned
   by the mergesort functions.

 */

/***********************************************************************/

#include <math.h>
#include "global_vars.h"
#include "list.h"

/***********************************************************************/
/* Prototypes for private functions                                    */

/***********************************************************************/

struct node *Merge_increasing_smallest_azimuth(struct node *, struct node *,
                                               struct node *);
struct node *Merge_increasing_largest_azimuth(struct node *, struct node *,
                                              struct node *);
struct node *Merge_increasing_centre_horizon_azimuth(struct node *,
                                                     struct node *,
                                                     struct node *);

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

struct node *Mergesort_increasing_smallest_azimuth(struct node *head,
                                                   struct node *tail)
{
    struct node *a, *b;

    if (head->next_smallest != tail) {
        a = head;
        b = head->next_smallest->next_smallest->next_smallest;
        while (b != tail) {
            head = head->next_smallest;
            b = b->next_smallest->next_smallest;
        }
        b = head->next_smallest;
        head->next_smallest = tail;
        return Merge_increasing_smallest_azimuth(
            Mergesort_increasing_smallest_azimuth(a, tail),
            Mergesort_increasing_smallest_azimuth(b, tail), tail);
    }
    return head;
}

/***********************************************************************/

void Pseudo_sort_decreasing_smallest_azimuth(struct node *head,
                                             struct node *tail)

/* This simply sets the prev_smallest pointers to
   the reverse sequence of the next_smallest pointers.
   It therefore requires that the list has already been
   sorted by increasing smallest */
{
    struct node *cur;

    if (head->next_smallest != tail) {
        cur = head->next_smallest;
        cur->prev_smallest = tail;
        while (cur->next_smallest != tail) {
            cur->next_smallest->prev_smallest = cur;
            cur = cur->next_smallest;
        }
        head->prev_smallest = cur;
    }
}

/***********************************************************************/

struct node *Mergesort_increasing_largest_azimuth(struct node *head,
                                                  struct node *tail)
{
    struct node *a, *b;

    if (head->next_largest != tail) {
        a = head;
        b = head->next_largest->next_largest->next_largest;
        while (b != tail) {
            head = head->next_largest;
            b = b->next_largest->next_largest;
        }
        b = head->next_largest;
        head->next_largest = tail;
        return Merge_increasing_largest_azimuth(
            Mergesort_increasing_largest_azimuth(a, tail),
            Mergesort_increasing_largest_azimuth(b, tail), tail);
    }
    return head;
}

/***********************************************************************/

void Pseudo_sort_decreasing_largest_azimuth(struct node *head,
                                            struct node *tail)

/* This simply sets the prev_largest pointers to
   the reverse sequence of the next_largest pointers.
   It therefore requires that the list has already been
   sorted by increasing largest */
{
    struct node *cur;

    if (head->next_largest != tail) {
        cur = head->next_largest;
        cur->prev_largest = tail;
        while (cur->next_largest != tail) {
            cur->next_largest->prev_largest = cur;
            cur = cur->next_largest;
        }
        head->prev_largest = cur;
    }
}

/***********************************************************************/

struct node *Mergesort_increasing_centre_horizon_azimuth(struct node *head,
                                                         struct node *tail)
{
    struct node *a, *b;

    if (head->next_horizon != tail) {
        a = head;
        b = head->next_horizon->next_horizon->next_horizon;
        while (b != tail) {
            head = head->next_horizon;
            b = b->next_horizon->next_horizon;
        }
        b = head->next_horizon;
        head->next_horizon = tail;
        return Merge_increasing_centre_horizon_azimuth(
            Mergesort_increasing_centre_horizon_azimuth(a, tail),
            Mergesort_increasing_centre_horizon_azimuth(b, tail), tail);
    }
    return head;
}

/***********************************************************************/
/* Private functions                                                   */

/***********************************************************************/

struct node *Merge_increasing_largest_azimuth(struct node *a, struct node *b,
                                              struct node *tail)
{
    struct node *c;

    c = tail;
    do {
        if (a->largest_azimuth <= b->largest_azimuth) {
            c->next_largest = a;
            c = a;
            a = a->next_largest;
        }
        else {
            c->next_largest = b;
            c = b;
            b = b->next_largest;
        }
    } while (c != tail);

    c = tail->next_largest;
    tail->next_largest = tail;

    return c;
}

/***********************************************************************/

struct node *Merge_increasing_smallest_azimuth(struct node *a, struct node *b,
                                               struct node *tail)
{
    struct node *c;

    c = tail;
    do {
        if (a->smallest_azimuth <= b->smallest_azimuth) {
            c->next_smallest = a;
            c = a;
            a = a->next_smallest;
        }
        else {
            c->next_smallest = b;
            c = b;
            b = b->next_smallest;
        }
    } while (c != tail);

    c = tail->next_smallest;
    tail->next_smallest = tail;

    return c;
}

/***********************************************************************/

struct node *Merge_increasing_centre_horizon_azimuth(struct node *a,
                                                     struct node *b,
                                                     struct node *tail)
{
    struct node *c;

    c = tail;
    do {
        if (a->centre_azimuth <= b->centre_azimuth) {
            c->next_horizon = a;
            c = a;
            a = a->next_horizon;
        }
        else {
            c->next_horizon = b;
            c = b;
            b = b->next_horizon;
        }
    } while (c != tail);

    c = tail->next_horizon;
    tail->next_horizon = tail;

    return c;
}
