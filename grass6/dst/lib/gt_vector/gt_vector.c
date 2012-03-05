/*

TODO:

eliminate DEBUG statements

Catch all calls to alloc() and free () in a custom function that keeps track of
memory allocation in map->mem_size

NULL data handling: NULL attributes can be handled by managing an array of short ints
that can be set to 1 to signify a NULL attribute at that record.
But: how do NULL atts appear in the original data? As missing values? As special codes?

from d.what.vect:

fprintf( stdout, _("Layer: %d\ncategory: %d\n"), Cats->field[j], Cats->cat[j] );

currently, map->field seems to point to the currently layer's db connection, after:
map->field = Vect_get_field (&map->in_vect_map, map->vect_cats->field[ map->current_layer - 1 ]);

For advanced analytical operations, we need to able to open a map in level 2!
Any analytical function requiring this should check if that has already been done,
	if not attempt to open level 2, if that fails: warn or abort.
	
Speed up attribute operations: copy all attribute values into an internal array, upon first
query for that attribute (cache status=dirty). Serve all queries from that cache in the future.
Set cache status back to dirty, if sth. has changed in the attribute table or another record
has been added, so that the cache will be rebuilt on next access.

Use Vect_get_num_updated_lines() and Vect_get_updated_line() to determine if cache needs to
be set to dirty.

A function that will return the numerical value of an attribute as type double, as long as
that attribute is any number format (integer, double, ...)

A function that checks, if an attribute of any numerical type exists (GVT_num_exists()).

*/

/* split into low and high level functions (e.g. export new vector map from SQL selection */

/* if layer number = -1, parse all layers (see Martin Landa's recent posting; do other GRASS
   modules handle it this way, too? Should this be default when opening a map? */
   
/* in addition to the global

 int GVT_NO_REGION_CONSTRAINTS;
 int GVT_NO_TYPE_CONSTRAINTS;
 int GVT_NO_SQL_CONSTRAINTS;
 
 we need to be able to set these for each map, individually, too! 
 
 */


#define GVT_DEBUG 1

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/dbmi.h>
#include <grass/Vect.h>

#include "gt/gt_vector.h"


/*
	Check if GVT has been initialized and abort, if not.
*/
int GVT_check_init ( void ) {
	return (0);
}


/*
	Check if a vector map has been opened and signal a file error, if not.
	The error will be fatal and program execution aborted, GVT_FATAL_FILE_ERRORS = TRUE.
	Otherwise, the function will return FALSE.
	It will return TRUE, if the map has been opened in the specified level:
		1 = geometries and attributes
		2 = same as 1 plus full topological information
*/
int GVT_check_opened ( GVT_map_s *map, int open_level ) {
	
	if ( map->open_level >= open_level ) {
		return ( TRUE );
	}
	
	if ( GVT_FATAL_FILE_ERRORS ) {
		G_fatal_error ("GVT: attempted to access a map that had not been opened.\n");
	} 
	
	return ( FALSE );
}	


/* 	Allocates memory for a vector map, keeping track of the amount
	of mem allocated in a counter in the struct.
*/
void * GVT_malloc ( size_t size, GVT_map_s *map ) {
	void *p;
	char tmp [2048];
	
	p = G_malloc ( size );
	if ( p == NULL ) {
		/* TODO: %i is not the right type */
		sprintf ( tmp, "GVT: failed to allocate %i bytes of memory.\n", size );
		if ( GVT_FATAL_MEM_ERRORS )
			G_fatal_error ( "%s", tmp );
		G_warning ( "%s", tmp );
		return (p);
	}
	map->mem_size = map->mem_size + size;
	return (p);
}


/*

	PUBLIC FUNCTIONS

*/


/*
	Initializes a bunch of global variables to default values.
	Always call this function once in your program before using
	any other GVT functions!
*/
void GVT_init ( void ) {
	GVT_NO_REGION_CONSTRAINTS = FALSE;
	GVT_NO_TYPE_CONSTRAINTS = FALSE;
	GVT_NO_SQL_CONSTRAINTS = FALSE;
	
	GVT_NO_ATTRIBUTE_CACHING = FALSE;
	GVT_MAX_CACHE_SIZE = 100000;

	GVT_FATAL_FILE_ERRORS = TRUE;
	GVT_FATAL_TYPE_ERRORS = TRUE;
	GVT_FATAL_MEM_ERRORS = TRUE;
	
	GVT_INIT_DONE = TRUE;
}



/* returns a pointer to a new GVT_map_s structure */
/* caller must not pre-allocate that pointer! */
GVT_map_s *GVT_new_map ( void ) {
	GVT_map_s *map;
	char tmp [2048];
	
	struct Cell_head window;
	
	map = G_malloc ( sizeof (GVT_map_s));
	if ( map == NULL ) {
		sprintf ( tmp, "GVT: failed to allocate %i bytes of memory for new map.\n", 
				sizeof (GVT_map_s) );
		if ( GVT_FATAL_MEM_ERRORS )
			G_fatal_error ( "%s", tmp );
		G_warning ( "%s", tmp );
		return (map);		
	}
	map->mem_size = map->mem_size + sizeof (GVT_map_s);
	map->open_level = -1;
	
	/* TODO: keep track of number of bytes alloc'd */
	map->vect_points = Vect_new_line_struct ();
  	map->vect_cats = Vect_new_cats_struct ();
	
	/* -2 indicates, that no records exist in this map, yet */
	map->current_record = -2;
	
	/* DEFAULT CONSTRAINTS */
	/* filter vector objects to current region and point types only */
	G_get_window (&window);	
	Vect_set_constraint_region (&map->in_vect_map, window.north, window.south, 
			      window.east, window.west, window.top, window.bottom); 			      
	map->north = window.north;
	map->south = window.south;
	map->east = window.east;
	map->west = window.west;
	map->top = window.top;
	map->bottom = window.bottom;	
				      		  	
	/* set SQL string to NULL */
	db_init_string ( &map->sql );
	db_set_string ( &map->sql, GVT_EMPTY_SQL );
		
	/*lat-long location? */
	if ( G_projection () == 3 ) {
		map->isLatLong = TRUE;
	} else {
		map->isLatLong = FALSE;
	}
  	
	/* distance calculations will be needed for lots of analytical applications, so might as
	   well initialize it right now ...
	*/
	G_begin_distance_calculations ();
	
	map->hasData = FALSE;
	map->num_layers = 0;
	map->num_attributes = 0;
	map->current_layer = 0;
	map->current_record = 0;
	
	return ( map );
}


/* returns number of free'd bytes */
int GVT_free_map (GVT_map_s *map) {

	int freed = 0;

	/* TODO: keep track of number of bytes dealloc'd */

	if ( map == NULL ) {
		return (0);
	}		
	
	/* TODO: free:
		Vect_new_line_struct ();
		Vect_new_cats_struct ();
	*/
	
	free ( map );	
	
	/* TODO: compare amount free'd with map->mem_size */
	
	return ( freed );	
};


/* constraints can only be set or unset when openening a new map! */
/* returns the open level of the map */
/* TODO: open in level2 ? */
/* TODO: let user choose open level and abort/warn if it cannot be reached */
int GVT_open_map ( char *mapname, int type, GVT_map_s *map ) {
	char *mapset;
	char tmp [2048];
	int i, j, dbcol;

	dbColumn *column;
	dbValue  *dbvalue;
	int ctype, sqltype, more;
	char *colname;
	
	if ( map->hasData ) {
		G_fatal_error ("GVT: attempted to load data into an already opened map.\n");
	}
	
	/* DO NOT ALLOCATE ANYTHING IN THE *MAP STRUCT BETWEEN HERE ... */
	
	if ( map->open_level > -1 ) {
		sprintf (tmp, "GVT: Attempted to re-open vector map already opened in level %i.\n", map->open_level );
		if ( GVT_FATAL_FILE_ERRORS ) 			
			G_fatal_error ( "%s", tmp);
		G_warning ( "%s", tmp );
		return (-1);		
	}

	/* TODO: check if a valid type has been specified */
	/* and exit, if GVT_FATAL_TYPE_ERRORS is set */
		
	/* check if map exists and if there are > 0 vector points in 
	   the specified layer */
	if ((mapset = G_find_vector2 (mapname, "")) == NULL) {		
		free (mapset);
		sprintf (tmp, "GVT: could not open vector map: %s.\n", mapname );
		if ( GVT_FATAL_FILE_ERRORS )			
			G_fatal_error ( "%s", tmp);
		G_warning ( "%s", tmp );
		return (-1);
	}

	/* if success opening the vector map: */
	map->open_level = 0;

	/* attempt to open input map at level 1 */
	Vect_set_open_level (1);	
	if (1 > Vect_open_old (&map->in_vect_map, mapname, mapset)) {
		Vect_close (&map->in_vect_map);
		free (mapset);
		map->open_level = -1; /* reset open level */
		sprintf (tmp, "GVT: could not open vector map for level 1 access: %s.\n", mapname );
		if ( GVT_FATAL_FILE_ERRORS )
			G_fatal_error ( "%s", tmp);
		G_warning ( "%s", tmp );
		return (-1);
	}
	map->open_level = 1;
	
	
	/* ... AND HERE ! */
		
	/* TODO: override constraints, if appropriate global vars have been set */
		
	/* DEFAULT CONSTRAINTS */
	/* filter vector objects to current region and point types only */
	Vect_set_constraint_region (&map->in_vect_map, map->north, map->south, 
			      map->east, map->west, map->top, map->bottom); 			      			      
	Vect_set_constraint_type (&map->in_vect_map, type);	
	map->type_constraints = type;
		
	map->type = type;
  		
	if ( Vect_is_3d ( &map->in_vect_map ) ) {
		map->is3d = TRUE; 
	} else {
		map->is3d = FALSE; 
	}
  
  	sprintf ( map->name, "%s", mapname );
  
	/* calculate number of vector points in map and current region */
	map->num_records = 0;
	/* TODO: map->type = : this should not be necessary if type constraints are in effect! */
	while ((map->type = Vect_read_next_line (&map->in_vect_map, map->vect_points, map->vect_cats)) > 0) {     
		map->num_records ++; 
	}	
  	/* TODO: determine number of layers and repeat the object counting for all layers */
	/* exit, if no layer has the type requested and GVT_FATAL_TYPE_ERRORS is set */
  	/* save number of layers with valid type and associated layer numbers */
	
	/* check for attributes */
	/* TODO: this needs to be done for all layers, as given by n_cats (?)
		so make sure there are no mem leaks in this loop
	*/
	map->num_layers = 0;
	map->current_layer = 0;	
	for ( i = 0; i < map->vect_cats->n_cats; i++ ) {		
		map->field = Vect_get_field (&map->in_vect_map, map->vect_cats->field[i]);
		/* TODO: in which cases could field == NULL? what to do then? */
		if ( map->field == NULL ) {
			
		}
		/* TODO: catch cases without a DB connection */
		if ( map->field != NULL ) {
			map->num_attributes = 0;
			map->driver = db_start_driver ( map->field->driver );
			db_init_handle ( &map->handle );			
			db_set_handle ( &map->handle, map->field->database, NULL);
			if (db_open_database(map->driver, &map->handle) != DB_OK){
				/* TODO: DB access failed */
				db_shutdown_driver( map->driver );
			} else {
				sprintf ( map->sql_buf, "select * from %s where %s = %d ",
						map->field->table, 
						map->field->key,
						map->vect_cats->cat[i]);
				db_set_string ( &map->sql, map->sql_buf );
				db_open_select_cursor(map->driver, &map->sql, &map->cursor, DB_SEQUENTIAL);
				map->table = db_get_cursor_table (&map->cursor);
				db_fetch ( &map->cursor, DB_NEXT, &more );
				map->dbncols = db_get_table_number_of_columns (map->table);
				/* TODO: lots of the vars in here should not be part of GVT_map_s struct
					many of them need to be tracked for each layer separately
				 */
				
				map->num_attributes = map->dbncols; /* TODO: this is actually redundant but more readable */				
				map->att_names = G_calloc ( (unsigned) map->num_attributes, sizeof (char*));
				map->att_types = G_calloc ( (unsigned) map->num_attributes, sizeof (short int));
				 
				for ( dbcol = 0; dbcol < map->dbncols; dbcol ++ ) {
					map->num_attributes ++; /* count number of attributes */
					column = db_get_table_column(map->table, dbcol);
					sqltype = db_get_column_sqltype (column);
					ctype = db_sqltype_to_Ctype(sqltype);
					map->att_types[dbcol] = ctype;
					dbvalue  = db_get_column_value(column);
					db_convert_value_to_string( dbvalue, sqltype, &map->str);
					colname = (char*) db_get_column_name (column);
					map->att_names[dbcol] = strdup ( colname ); /* save this attribute name */	
					if ( (ctype!=GVT_DOUBLE) && (GVT_INT) && (GVT_STRING) && (GVT_DATETIME) ) {
						G_warning ("GVT: attribute %s is of unknown type.\n", colname);
					}					
				}
								
				/* create cache pointers and set all caches to dirty but don't read in attributes yet!*/
				/* to keep cache addressing simple, we will allocate num_attributes caches for each type */
				/* but later only allocate mem at the positions where it is really needed. */
				map->cache_status = G_calloc ((unsigned) map->num_attributes, sizeof (short int));				
				map->cache_double = G_calloc ((unsigned) map->num_attributes, sizeof (double*));
				map->cache_int = G_calloc ((unsigned) map->num_attributes, sizeof (long int*));
				map->cache_char = G_calloc ((unsigned) map->num_attributes, sizeof (char*));
				map->cache_datetime = G_calloc ((unsigned) map->num_attributes, sizeof (char*));
				/* by setting all caches to dirty, we make sure that memory will be allocated and all attributes read */
				/* into them the first time they are needed. */
				for ( j = 0; j < map->num_attributes; j ++ ) {
					map->cache_status[j] = GVT_CACHE_INIT;
				}
				
				/* TODO: keep these open for calls of GVT_get_double () etc. */
				db_close_cursor(&map->cursor);
				db_close_database( map->driver);
				db_shutdown_driver( map->driver);
			}
		}
		map->num_layers ++;
	}	
	
	/* TODO: activate first layer of given type */
	map->current_layer = 1;
	
	/* TODO: */
	/*	init attribute caches for current layer (?) */	
	
	
	Vect_rewind (&map->in_vect_map);
	map->current_record = -1;
	free (mapset);		
	
	return ( map->open_level );
}


int GVT_open_map_points ( char *mapname, int type, GVT_map_s *map ) {
	return ( GVT_open_map ( mapname, GV_POINT, map ) );
}


void GVT_close_map ( GVT_map_s *map ) {
	Vect_close (&map->in_vect_map);
	map->current_record = -2;
	map->hasData = FALSE;
	/* TODO: what else needs to be done? */
}


/* jump to first record */
void GVT_first ( GVT_map_s *map ) {
	Vect_rewind ( &map->in_vect_map );
	Vect_read_next_line (&map->in_vect_map, map->vect_points, map->vect_cats);
	map->current_record = 0;
}


/* jump to next record */
/* returns:
	1 (TRUE)	SUCCESS
	0 (FALSE)	NO MORE RECORDS (EOF)
*/
int GVT_next ( GVT_map_s *map ) {
	/* TODO: does this honor current type constraints? */
	if ( Vect_read_next_line (&map->in_vect_map, map->vect_points, map->vect_cats)  > 0 ) {
		map->current_record ++;
		return ( TRUE );
	} else {
		return ( FALSE );
	}
}


/* jump to last record */
void GVT_last ( GVT_map_s *map ) {
	GVT_seek ( map->num_records-1, map );
	map->current_record = map->num_records-1;
}


/* rewind database: jump to position before first record! */
void GVT_rewind ( GVT_map_s *map ) {
	Vect_rewind ( &map->in_vect_map );
	map->current_record = -1;
}


/* rewind and refilter data using SQL string */
/* first record has position 0 ! */
/* last record has position map->num_records-1 ! */
/* returns:
	1 (TRUE) 	SUCCESS
	0 (FALSE 	attempting to seek to illegal position
*/
int GVT_seek ( long int pos, GVT_map_s *map ) {
	long int i;
	
	/* TODO: check, if this work also with layers of mixed types! */
	if ( pos < 0 ) {
		return ( FALSE );
	}
	if ( pos > map->num_records-1 ) {
		return ( FALSE );
	}
	
	Vect_rewind ( &map->in_vect_map );
	for ( i = 0; i <= pos; i ++ ) {
		Vect_read_next_line (&map->in_vect_map, map->vect_points, map->vect_cats);
	}
	map->current_record = i;
	return ( TRUE );
}


/* returns ID (cat - 1) of currently active record */
/* TODO: maybe return cat (current_record + 1)
	is ID always = cat-1?
*/
long int GVT_get_current ( GVT_map_s *map ) {
	return ( map->current_record );
}


void GVT_query () {
}

/*
	check, if an attribute of a specified name and type exists
*/

int GVT_double_exists ( char *name, GVT_map_s *map ) {
	return ( GVT_attr_exists (name, GVT_DOUBLE, map));
}

int GVT_int_exists ( char *name, GVT_map_s *map ) {
	return ( GVT_attr_exists (name, GVT_INT, map));
}


int GVT_attr_exists ( char *name, int type, GVT_map_s *map ) {
	int i;
	
	GVT_check_opened (map, 1); /* map needs to be open at least in level 1 */
	
	for ( i=0; i < map->num_attributes; i++ ) {
		if ( !strcmp (map->att_names[i], name) ) {
			if ( map->att_types[i] == type ) {
				return (TRUE);
			}
		}
	}
	
	return ( FALSE );
}


/* checks if an attribute of any type exists in map */
int GVT_any_exists ( char *name, GVT_map_s *map ) {
	int i;
	
	GVT_check_opened (map, 1); /* map needs to be open at least in level 1 */
	
	for ( i=0; i < map->num_attributes; i++ ) {
		if ( !strcmp (map->att_names[i], name) ) {
			return (TRUE);
		}
	}
	
	return ( FALSE );
}


/* Returns the contents of an attribute field of type 'type' in the map's attribute table */
/* Memory will be allocated for the return value and must be free'd by the caller */
/* if no longer needed. */
/* TODO: this is far too much overhead for reading a single attribute! */
/* 	 fill attribute cache on first access, serve queries from cache until dirty */
/*       implement this in a function *GVT_get_attribute (). But keep this version as */
/*       an internal function that can be used if caching is turned off */
/*       check for attribute exist is already done by user-visible function, so at
	 this point we can have confidence that it exists! */
char *GVT_get_attribute_no_cache ( char *name, int type, GVT_map_s *map ) {
	int dbcol;
	int found;

	dbColumn *column;
	dbValue  *dbvalue;
	int ctype, sqltype, more;
	char *colname;

	map->field = Vect_get_field (&map->in_vect_map, map->vect_cats->field[ map->current_layer - 1 ]);
	/* TODO: in which cases could field == NULL? what to do then? */
	/* TODO: catch cases without a DB connection */
	if ( map->field != NULL ) {
		/* TODO: we should not need to re-open everything, if GVT_open_map () does not close it */
		map->driver = db_start_driver ( map->field->driver );
		db_init_handle ( &map->handle );			
		db_set_handle ( &map->handle, map->field->database, NULL);
		if (db_open_database(map->driver, &map->handle) != DB_OK){
			/* TODO: DB access failed */
			db_shutdown_driver( map->driver );
		} else {
			sprintf ( map->sql_buf, "select * from %s where %s = %d ",
					map->field->table, 
					map->field->key,
					map->vect_cats->cat[ map->current_layer - 1 ]);
			db_set_string ( &map->sql, map->sql_buf );
			db_open_select_cursor(map->driver, &map->sql, &map->cursor, DB_SEQUENTIAL);
			map->table = db_get_cursor_table (&map->cursor);
			db_fetch ( &map->cursor, DB_NEXT, &more );
			map->dbncols = db_get_table_number_of_columns (map->table);
			/* TODO: lots of the vars in here should not be part of GVT_map_s struct
				many of them need to be tracked for each layer separately
			 */
			found = FALSE;
			/* TODO: too much overhead: better to keep a list of attributes in GVT_map_s and search that! */
			/*	use internal function GVT_attr_exists () for that. */
			for ( dbcol = 0; dbcol < map->dbncols; dbcol ++ ) {
				column = db_get_table_column(map->table, dbcol);
				sqltype = db_get_column_sqltype (column);
				ctype = db_sqltype_to_Ctype(sqltype);
				colname = (char*) db_get_column_name (column);
				if (!strcmp (colname,name)){
					if (ctype == type) {
						found = TRUE;
						dbvalue  = db_get_column_value(column);
						db_convert_value_to_string( dbvalue, sqltype, &map->str);											/* TODO: now we could actually skip the other runs of this loop: */
						/* return (val) */
						/* BUT CLEAN UP FIRST! */
					} else {
						/* TODO: abort if not double attribute or return something strange to signify this */
						return ( NULL );
					}
				}
			}
			db_close_cursor(&map->cursor);
			db_close_database( map->driver);
			db_shutdown_driver( map->driver);
			if ( found == FALSE ) {
				return ( NULL );
			}
		}
	}	
					
	return ( strdup (db_get_string ( &map->str )) );
}


/*
	This function is user-visible
*/
char *GVT_get_attribute ( char *name, int type, GVT_map_s *map ) {
	/* TODO: implement attribute caching */
	return (GVT_get_attribute_no_cache ( name, type, map ));
}


/*
	read a double attribute from a map
	
	Returns:
		NULL, if reading failed
		double value of attribute, otherwise
*/
double GVT_get_double ( char *name, GVT_map_s *map) {

	char *aval;
	double dval;

	/* todo: check, if attribute exists and has right type */

	aval = GVT_get_attribute ( name, GVT_DOUBLE, map );
	if ( aval == NULL ) {
		/* TODO: implement NULL value handling */
		G_fatal_error ("GVT: error reading double attribute '%s'.\n", name);
	}
	
	dval = atof ( db_get_string ( &map->str ) );
	return ( dval );
}


/* TODO: this is far too much overhead for reading a single attribute! */
/* 	 fill attribute cache on first access, serve queries from cache until dirty */
long int GVT_get_int ( char *name, GVT_map_s *map) {

	char *aval;
	long int ival;

	/* todo: check, if attribute exists and has right type */

	aval = GVT_get_attribute ( name, GVT_DOUBLE, map );
	if ( aval == NULL ) {
		/* TODO: implement NULL value handling */
		G_fatal_error ("GVT: error reading double attribute '%s'.\n", name);
	}
	
	ival = atol ( db_get_string ( &map->str ) );
	return ( ival );
}


/* TODO: implement C API attribute writes in GVT_set_double2 and delete this version ! */
/* this writes a new value into a double type attribute of the current record */
int GVT_set_double ( char *name, double dvalue, GVT_map_s *map ) { 

	char tmp [GVT_MAX_STRING_SIZE];
	int error;

	map->field = Vect_get_field (&map->in_vect_map, map->vect_cats->field[ map->current_layer - 1 ]);
	/* TODO: in which cases could field == NULL? what to do then? */
	/* TODO: catch cases without a DB connection */
	if ( map->field != NULL ) {
		sprintf ( tmp, "echo \"UPDATE %s SET %s=%f WHERE cat=%d\" | db.execute", map->name, name, dvalue, map->vect_cats->cat[map->current_layer - 1]);
		error = system ( tmp );
	}	
		
	return ( TRUE );
}



/* TODO: this is far too much overhead for reading a single attribute! */
/* (same as GVT_get_double) */
/* write a value into a double attribute */
/* returns:
	1 (TRUE)	SUCCESS: VALUE SET
	0 (FALSE)	FAILURE
*/
int GVT_set_double2 ( char *name, double dvalue, GVT_map_s *map ) { 
	int dbcol;
	int found;

	dbColumn *column;
	dbValue  *dbvalue;
	int ctype, sqltype, more;
	char *colname;

	map->field = Vect_get_field (&map->in_vect_map, map->vect_cats->field[ map->current_layer - 1 ]);
	/* TODO: in which cases could field == NULL? what to do then? */
	/* TODO: catch cases without a DB connection */
	if ( map->field != NULL ) {
		/* TODO: we should not need to re-open everything, if GVT_open_map () does not close it */
		map->driver = db_start_driver ( map->field->driver );
		db_init_handle ( &map->handle );			
		db_set_handle ( &map->handle, map->field->database, NULL);
		if (db_open_database(map->driver, &map->handle) != DB_OK){
			/* TODO: DB access failed */
			db_shutdown_driver( map->driver );
		} else {
			sprintf ( map->sql_buf, "select * from %s where %s = %d ",
					map->field->table, 
					map->field->key,
					map->vect_cats->cat[ map->current_layer - 1 ]);
			db_set_string ( &map->sql, map->sql_buf );
			db_open_select_cursor(map->driver, &map->sql, &map->cursor, DB_SEQUENTIAL);
			
			map->table = db_get_cursor_table (&map->cursor);
			db_fetch ( &map->cursor, DB_NEXT, &more );
			map->dbncols = db_get_table_number_of_columns (map->table);
			/* TODO: lots of the vars in here should not be part of GVT_map_s struct
				many of them need to be tracked for each layer separately
			 */
			found = FALSE;
			/* TODO: too much overhead: better to keep a list of attributes in GVT_map_s and search that! */
			for ( dbcol = 0; dbcol < map->dbncols; dbcol ++ ) {
				column = db_get_table_column(map->table, dbcol);
				sqltype = db_get_column_sqltype (column);
				ctype = db_sqltype_to_Ctype(sqltype);
				colname = (char*) db_get_column_name (column);
				if (!strcmp (colname,name)){
					if (ctype == DB_C_TYPE_DOUBLE) {					
						found = TRUE;
						dbvalue  = db_get_column_value(column); /* dbvalue now points to attribute */
						db_convert_value_to_string( dbvalue, sqltype, &map->str);
						if ( db_test_value_isnull ( dbvalue ) ) {
							fprintf ( stderr, "  NULL\n" );
						}
						db_set_value_double (dbvalue, dvalue);
						db_convert_value_to_string( dbvalue, sqltype, &map->str);						
						fprintf ( stderr, "SETTING %s TO: %f\n", db_get_string ( &map->str ), dvalue );
						
						/* TODO: now we could actually skip the other runs of this loop! */
					} else {
						/* TODO: abort if not double attribute or return something strange to signify this */
						return (FALSE);
					}
				}
			}
			db_close_cursor(&map->cursor);
			db_close_database( map->driver);
			db_shutdown_driver( map->driver);
			if ( found == FALSE ) {
				/* TODO: check if attribute exists */
				return (FALSE);
			}
		}
	}	
		
	return ( TRUE );
}


/* check if an attribute is NULL */
int GVT_is_null () {
	/* look at functions in lib/db/dbmi_base:
		column.c: db_test_column_null_allowed ();
		value.c: db_test_value_isnull (dbValue *value)
	*/		
	return ( FALSE );
}


int GVT_set_null () {
	return ( TRUE );
}


/* append new record
*/
int GVT_append ( ) {
	return ( TRUE );
}


/* delete record
*/
int GVT_delete ( ) {
	return ( TRUE );
}


/* seek to first record that matches
   a search string
*/
int GVT_find () {
	return ( TRUE );
}


int GVT_find_next () {
	return ( TRUE );
}


/* create a new double attribute
   returns:
   	1 (TRUE)	SUCCESS
	0 (FALSE)	FAILURE
*/
int GVT_add_double ( char *name, GVT_map_s *map ) {
	char buf [GVT_MAX_STRING_SIZE];
	int error;

	/* TODO: replace system call with appropriate C API calls */
	/* TODO: check if column with same name (but different type) exists */
	
	sprintf ( buf, "echo \"ALTER TABLE %s ADD COLUMN %s double precision\" | db.execute", map->name, name );
	fprintf ( stderr, "%s\n", buf );
	error = system ( buf );
	
	return ( TRUE );
}


/* delete an attribute from a table
*/
int GVT_drop_double ( char *name, GVT_map_s *map ) {
	/* TODO: replace system call with appropriate C API calls */
	/* NOTE: db.execute seems to not support DROP COLUMN statements! */
	return ( TRUE );
}


long int GVT_get_num_records ( GVT_map_s *map ) {
	return ( map->num_records );
}


int GVT_is_lat_long ( GVT_map_s *map ) {
	return ( map->isLatLong );
}


/* pass NULL for constraints that you don't want to touch */
int GVT_set_constraints ( struct Cell_head *window, char *SQL, GVT_map_s *map ) {
		
	if ( window != NULL ) {			 
		map->north = window->north;
		map->south = window->south;
		map->east = window->east;
		map->west = window->west;
		map->top = window->top;
		map->bottom = window->bottom;
	}
	
	if ( SQL != NULL ) {
	}
	return (0);
}



int GVT_get_constraints ( void ) {
	return (0);
}


int GVT_constraints ( int type, int SQL, int region ) {
	return (0);
}


/* returns the file name of the map */
char *GVT_get_mapname ( GVT_map_s *map ) {
	/* first check, if opened */
	return (NULL);
}


/* returns the mapset of the map */
char *GVT_get_mapset ( GVT_map_s *map ) {
	/* first check, if opened */
	return (NULL);
}


/* ANALYTICAL FUNCTIONS */

/* gets the 2D distance from the point in the map's current record
	to the point defined by x and y
	This also works for lat long locations
*/
double GVT_get_2D_point_distance ( double x, double y, GVT_map_s *map ) {
	double d = 0.0;
	double px, py;

	/* TODO: check if it's a points map! */
	
	if ( map->isLatLong ) {
		px = *map->vect_points->x;
		py = *map->vect_points->y;
		d = G_geodesic_distance ( x, y, px, py );
	} else {
		/* TODO: implement distance for simple cartesian space */
	}
	
	return (d);
}






