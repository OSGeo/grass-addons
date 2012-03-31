
/****************************************************************
 *      random_int.c 
 *
 *      Return a random integer between a specified minimum 
 *      and maximum value.  Integer is a long and is drawn from
 *      a uniform population.  Minimum and maximum values may
 *      be returned.
 *
 ****************************************************************/

/* Written by Mark Lake on 1/3/96 to:-
 * 
 * Updated by Mark Lake on 17/8/01 for GRASS 5.x
 * 
 * 1) Return a random integer between a specified minimum 
 *    and maximum value.
 *
 * Called by:-
 * 
 * 1) random_sample()
 *
 * Calls:-
 *
 * 1)  zufall()
 */

#include <string.h>
#include <math.h>

#include <grass/gis.h>

#include "config.h"
#include "zufall.h"

long int random_int (long int min, long int max)
{
    double u[1];
    char message[32];

    strcpy (message, "Random number generator failed!");

    if (zufall (1, u) != 0)
	G_fatal_error (message);

    return (long int) min + floor ((max - min + 1) * u[0]);
}
