/****************************************************************
 *      delete_lists.c
 *      
 *      Delete the 16 segment lists used to record the cells
 *      that are visible from each viewpoint.
 *
 ****************************************************************/

/* Modified from r.cumlos
 * by MWL on 1/3/96 to:-
 * 
 * Updated by Mark Lake on 17/8/01 for GRASS 5.x
 * 
 * 1) Delete the 16 segment lists used to record the cells
 *    that are visible from each viewpoint.
 *
 * Modifications to r.cumlos version 3.0:-
 *
 * 1) Taken out of main() and placed in function delete_lists().
 *
 * Modifications to r.los:-
 *
 * 1) r.los does not perform this function.
 *
 * Called by:-
 * 
 * 1) scan_all_cells()
 * 2) random_sample()
 * 3) systematic_sample()
 * 4) from_sites()
 *
 * Calls:-
 *
 * 1)  delete_one_list()
 */

#include <grass/segment.h>

#include "config.h"
#include "point.h"

void delete_lists (struct point *heads[])

/* struct point *heads[] is same as "struct point **heads" */

{
    int segment_no;
    void delete_one_list ();

    /* delete the list of visible cells */
    
    for (segment_no = 1; segment_no <= 16; segment_no++)
    {
	/*		printf ("\nDeleting list for segment = %d ", segment_no);
			fflush (stdout);*/
	delete_one_list (heads[segment_no-1]);
    }
}

