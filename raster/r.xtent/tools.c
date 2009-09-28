
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

#include <sys/types.h>
#include <unistd.h>

#include <grass/gis.h>
#include <grass/glocale.h>

/* this runs an external command */
void run_cmd ( char *cmd ) {  
  G_system ( cmd );
}

/* this runs a mapcalc instruction using r.mapcalc */
void r_mapcalc ( char* outmap, char *cmd ) {
  char buf[5000];
  
  sprintf ( buf, "r.mapcalc %s=%s", outmap, cmd );
  run_cmd (buf);
}


/* Function quicksort() sorts an array of double numbers
 * by ascending size.
 * The size of the array must be passed in 'n'
 * Sorting is done in place, i.e. *array will be
 * altered!
 */
int compare ( const void *a, const void *b ) {
	if ( * (double *) a < * (double *) b ) {
		return ( -1 );
	}
	if ( * (double *) a == * (double *) b ) {
		return ( 0 );
	}
	return ( 1 );
} 
 
void quicksort ( double *array, int n ) {
		
	if ( array != NULL ) {
		qsort ( array, (size_t) n, sizeof (double), compare );
	}
}


/* This function uses the posix standard function 
 * and a prefix to generate a unique name for a
 * temporary map in the current mapset.
 * Memory for the new string is allocated and can
 * be freed by the caller.
*/
char *mktmpmap ( char* prefix ) {
	int pid;
    static int uniq = 0;	
	char *name;

	name = malloc (1024 * sizeof (char) );
	pid = getpid();
	sprintf ( name, "%s%i%i", prefix, pid, uniq );
	uniq ++;
	
	return ( name );
}


/* Returns 1 if map exists in current mapset and is readable,
 * 0 if there is a problem
 */
int map_exists ( char *map ) {
	
	if ( G_find_cell( map, G_mapset( )) == NULL ) {
		return ( 0 );
	}
	
	return ( 1 );	
}


/* this function tests if a raster map exists in the current
 * mapset and can be opened for write access 
 * Returns 1 if OK, 0 if open failed
 * On failed open, it will also generate a user-defined warning.
 * */
int test_map ( char *map, char *msg, ... ) {
    char buffer[5000];
    va_list ap;
	int error;

    va_start(ap,msg);
    vsprintf(buffer,msg,ap);
    va_end(ap);

	if ( G_find_cell (map, "" ) == NULL ) {
		G_warning (_("%s"), buffer );
	}

	error = G_open_cell_old ( map, G_find_cell (map, "") );
	if ( error < 0 ) {
		G_warning (_("%s"), buffer );
		G_close_cell (error);
		return ( 0 );
	} else {
		G_close_cell ( error );
	}
	return ( 1 );
}

 
/* this function tests if a raster map exists in the current
 * mapset and can be opened for write access 
 * It aborts the program if there is a problem.
 * */
void test_map_f ( char *map, char *msg, ... ) {
    char buffer[5000];
    va_list ap;
 	int error;

    va_start(ap,msg);
    vsprintf(buffer,msg,ap);
    va_end(ap);

	if ( G_find_cell (map, "" ) == NULL ) {
		G_fatal_error (_( "%s"), buffer );
	}

	error = G_open_cell_old ( map, G_find_cell (map, "" ) );
	if ( error < 0 ) {
		G_fatal_error (_( "%s"), buffer );		
	} else {
		G_close_cell ( error );
	}
}

