#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include <grass/gis.h>

#include "structs.h"
#include "dst.h"
#include "print.h"
#include "sets.h"
#include "garbage.h"

BOOL **garbage_init ( void ) {
	BOOL **garbage;
	long i;
	
	garbage = (BOOL **) G_malloc ((unsigned)(garbage_size() * sizeof (BOOL*)));		
	for (i=0; i<garbage_size(); i++) {
		garbage[i] = NULL;
	}	
	return (garbage);
}

void garbage_throw ( BOOL **garbage, int k, BOOL *item ) {
	if ( garbage[k] != NULL ) {
		G_fatal_error ("Garbage allocation error!\n");
	}
	garbage[k] = item;	
}

void garbage_print ( BOOL **garbage ) {
	long i;
	
	fprintf (lp,"GARBAGE: \n");
	for (i=0; i<garbage_size(); i++) {
		fprintf (lp,"%li = %i\n",i,*garbage[i]);
	}	
}

long garbage_size ( void ) {
	Uint no_of_sets;
	long slots;
	
	no_of_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
	slots = (N + (N-1)) * no_of_sets;
	return (slots);
}

void garbage_free ( BOOL **garbage ) {	
	int i;
	
	for ( i=0; i<garbage_size(); i++ ) {		
		G_free (garbage[i]);		
	}	
	G_free (garbage);
}
