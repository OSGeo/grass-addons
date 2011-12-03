/*
	

TODO:

NULL value handling:
          GVT_get_no_cache currently returns NULL for values that are NULL or missing -- maybe differentiate
            between these two cases`? 
          use GRASS NULL values for CELL and DCELL types as int and double NULL representations !
          -> look at value.c for hints !

ATTRIBUTE CHECKING:
- a function to check numerical attributes for validity, range and NULL data
- the same for text attributes
- a function to read all values for an attribute into an array and return it with NULL-termination
- a function that returns any numerical attribute as DOUBLE
- a function that returns any numerical attribute as INT

HANLDE OTHER TYPE OF ATTRIBUTES:
  DATE type
  ... (?)


ATTRIBUTE CACHING:
  All functions reading/checking attributes call stub funcs GVT_get_attr() and GVT_attr_exists().
  Those two need to be modified ...

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

#include <grass/glocale.h>

#include <grass/gis.h>
#include <grass/dbmi.h>
#include <grass/Vect.h>

#include "globals.h"
#include "gt_vector.h"


/*
	Check if GVT has been initialized and abort, if not.
*/
int GVT_check_init ( void ) {
	return (0);
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
		sprintf ( tmp, "GVT: Failed to allocate %i bytes of memory.\n", size );
		if ( GVT_FATAL_MEM_ERRORS )
			G_fatal_error (_( tmp ));
		G_warning (_( tmp ));
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
		sprintf ( tmp, "GVT: Failed to allocate %i bytes of memory for new map.\n", 
				sizeof (GVT_map_s) );
		if ( GVT_FATAL_MEM_ERRORS )
			G_fatal_error (_( tmp ));
		G_warning (_( tmp ));
		return (map);		
	}
	map->mem_size = map->mem_size + sizeof (GVT_map_s);
	map->open_level = -1;
	
	/* TODO: keep track of number of bytes alloc'd */
	map->vect_points = Vect_new_line_struct ();
  	map->vect_cats = Vect_new_cats_struct ();
	
	/* -2 indicates that no records exist in this map yet */
	map->current_record = -2;
	
	/* DEFAULT CONSTRAINTS */
	/* filter vector objects to current region */
	G_get_window (&window);	
	Vect_set_constraint_region (&map->in_vect_map, window.north, window.south, 
			      window.east, window.west, window.top, window.bottom); 			      
	map->north = window.north;
	map->south = window.south;
	map->east = window.east;
	map->west = window.west;
	map->top = window.top;
	map->bottom = window.bottom;	
				      		  	
	/* initialize SQL query */
	db_init_string ( &map->sql );
	db_set_string ( &map->sql, GVT_EMPTY_SQL );	
	/* initialize string buffer */
	db_init_string ( &map->str );
		
	/*lat-long location? */
	if ( G_projection () == 3 ) {
		map->isLatLong = TRUE;
	} else {
		map->isLatLong = FALSE;
	}
  	
	/* distance calculations will be needed for lots of analytical applications, so might as
	   well initialize them right now ...
	*/
	G_begin_distance_calculations ();
	
	/* TODO: set all attribute caches to 'dirty' */
	
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
/* TODO: handle layers: let user choose layer, if 0: look for the first layer 
 * 		 that has objects of the specified type (issue a warning) or abort,
 * 		 if none found.
 */
int GVT_open_map ( char *mapname, int type, GVT_map_s *map ) {
	char *mapset;
	char tmp [2048];
	int i, dbcol;

	dbColumn *column;
	dbValue  *dbvalue;
	int ctype, sqltype, more;
	char *colname;
	
	/* DO NOT ALLOCATE ANYTHING IN THE *MAP STRUCT BETWEEN HERE ... */
	
	/* TODO: check if this object has already been created (?) */
	if ( map->open_level > -1 ) {
		sprintf (tmp, "GVT: Vector map already loaded into this object.\n" );
		if ( GVT_FATAL_FILE_ERRORS ) 			
			G_fatal_error (_(tmp));
		G_warning (_( tmp ));
		return (-1);		
	}

	/* TODO: check if a valid type has been specified */
	/* and exit, if GVT_FATAL_TYPE_ERRORS is set */
		
	/* check if map exists and if there are > 0 vector points in 
	   the specified layer */
	mapset = G_find_vector2 (mapname, "");
	if (mapset == NULL) {
		sprintf (tmp, "GVT: Could not open vector map: %s.\n", mapname );
		if ( GVT_FATAL_FILE_ERRORS )			
			G_fatal_error (_(tmp));
		G_warning (_( tmp ));
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
		sprintf (tmp, "GVT: Could not open vector map for level 1 access: %s.\n", mapname );
		if ( GVT_FATAL_FILE_ERRORS )
			G_fatal_error (_(tmp));
		G_warning (_( tmp ));		
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
  
  	sprintf ( map->name, mapname );
  
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
	/*
	
	TODO: currently, this only connects to the first layer in the map!
	      also, there is no abort condition, if map->vect_cats->n_cats < 1, i.e. there is no DB connection !!!
	       -> QUESTION: is there always at least on layer (field) with cats int attribute?
	
    The loop should look like:
      
    for ( i = 0; i < map->vect_cats->n_cats; i++ ) {
      ...
    }
    
    because n_cats has the number of DB connections for this map.
    
	*/
	for ( i = 0; i < 1; i++ ) {		
		map->field = Vect_get_field (&map->in_vect_map, map->vect_cats->field[i]);
		/* TODO: in which cases could field == NULL? what to do then? */
		/* TODO: catch cases without a DB connection */
		if ( map->field != NULL ) {
		  /* start DB connection for the current layer (field) */
			map->driver = db_start_driver ( map->field->driver );
			db_init_handle ( &map->handle );			
			db_set_handle ( &map->handle, map->field->database, NULL);
			if (db_open_database(map->driver, &map->handle) != DB_OK){
				/* TODO: DB access failed, anything else we need to do? */
				db_shutdown_driver( map->driver );
				G_fatal_error (_("GVT: Error accessing database layer.\n"));
			} else {
			  /* the default SQL statement is: "select all records" (in current layer) */
				sprintf ( map->sql_buf, "select * from %s where %s = %d ",
						map->field->table, 
						map->field->key,
						map->vect_cats->cat[i]); 				
				db_set_string ( &map->sql, map->sql_buf );
				/* now open a cursor to fetch data from the DB */
				/* other GVT funcs can use this cursor directly to access the attribute data for this map */
				db_open_select_cursor(map->driver, &map->sql, &map->cursor, DB_SEQUENTIAL);
				map->table = db_get_cursor_table (&map->cursor);
				db_fetch ( &map->cursor, DB_NEXT, &more );
				map->dbncols = db_get_table_number_of_columns (map->table);
				/* TODO: lots of the vars in here should not be part of GVT_map_s struct
					many of them need to be tracked for each layer separately
				 */
				for ( dbcol = 0; dbcol < map->dbncols; dbcol ++ ) {
					/* TODO: save this info in GVT_map_s, so that other funcs that need to check
                   attribute table types and structure can access it ! 
                   This info includes the name and type of each attribute in the table.         
          */
					column = db_get_table_column(map->table, dbcol);
					sqltype = db_get_column_sqltype (column);
					ctype = db_sqltype_to_Ctype(sqltype);
					dbvalue  = db_get_column_value(column);
					db_convert_value_to_string( dbvalue, sqltype, &map->str);
					colname = (char*) db_get_column_name (column);
          
          if ( DEBUG > 1 ) {					
					  fprintf (stderr, "ATT = %s\n", colname);
				  }
				}
				
				db_close_cursor(&map->cursor);
				
			}
		}
		map->num_layers ++;
	}	

  /* the DB connection will remain open for other GVT funcs to use !!! */
	
	/* TODO: activate first layer of given type */
	map->current_layer = 1;
	
	/* TODO: */
	/*	init attribute caches for current layer (?) */	
	
	Vect_rewind (&map->in_vect_map);
	map->current_record = -1;
	//free (mapset);		
	
	return ( map->open_level );
}


int GVT_open_map_points ( char *mapname, int type, GVT_map_s *map ) {
	return ( GVT_open_map ( mapname, GV_POINT, map ) );
}


void GVT_close_map ( GVT_map_s *map ) {
	Vect_close (&map->in_vect_map);
	map->current_record = -2;

  /* close DBMI driver and table(s) and cursor(s) */
  /* TODO: this needs to be update for multilayered maps !!! 
          AND CHECK if a table was opened, at all !!!  
  */
	db_close_database( map->driver);
	db_shutdown_driver( map->driver);	
	
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


/* rewind database: jump to position -1 (immediately before first record)! */
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
    This function checks for the existence of attribute *name value in the current *map record's attributes
    in the currently active layers.
    It bypasses the GVT attribute caching scheme, using SQL calls to get the attribute data
    from the DB which *map is connected to
    If an attribute *name exists, TRUE will be returned, FALSE otherwise.
    Type checking can be done by setting type to GVT_DOUBLE|INT|STRING ...
    Set type to -1 to accept any type of attribute.    
*/
int GVT_attr_exists_no_cache ( char *name, int type, GVT_map_s *map ) {
	int dbcol;
	int ctype, sqltype, more;
  /* these two are pointers to members of the attribute table
     they need not be free'd ! */
	dbColumn *column;
	char *colname;		

	if ( map->field != NULL ) {    
    /* Run SQL statement to refresh attribute information */
    /* TODO: Do we really have to go through all this in order to read the current record's attribute values? */
    /* START */
		sprintf ( map->sql_buf, "select * from %s where %s = %d ",
				map->field->table, 
				map->field->key,
				map->vect_cats->cat[ map->current_layer - 1 ]);
		db_set_string ( &map->sql, map->sql_buf );
	  db_open_select_cursor(map->driver, &map->sql, &map->cursor, DB_SEQUENTIAL); /* this does not alloc any memory, so no need to clean up */
	  map->table = db_get_cursor_table (&map->cursor);	
	  db_fetch ( &map->cursor, DB_NEXT, &more );
	  /* END of stuff to do for reading attribute values */	
	
		for ( dbcol = 0; dbcol < map->dbncols; dbcol ++ ) {
			column = db_get_table_column(map->table, dbcol);
			sqltype = db_get_column_sqltype (column);
  		ctype = db_sqltype_to_Ctype(sqltype);
			colname = (char*) db_get_column_name (column);									
			if (!strcmp (colname,name)){
			  /* found an attribute of that name! */
			  if ( type == -1 ) {
			   /* no type checking required! */
         db_close_cursor(&map->cursor);
			   return ( TRUE );
        }
				if (ctype == type) {
          /* now we can break out of this loop! */
          db_close_cursor(&map->cursor);
					return ( TRUE );         					
				}
			}
		}		
		db_close_cursor(&map->cursor);
  }	
	return ( FALSE );
}

/*
  STUB FUNCTION
*/
int GVT_attr_exists ( char *name, int type, GVT_map_s *map ) {
  return GVT_attr_exists_no_cache ( name, type, map );
}


/*
	The following functions check if an attribute of a specific name and type exists.
*/
int GVT_double_exists ( char *name, GVT_map_s *map ) {
	return ( GVT_attr_exists (name, GVT_DOUBLE, map));
}

int GVT_int_exists ( char *name, GVT_map_s *map ) {
	return ( GVT_attr_exists (name, GVT_INT, map));
}

int GVT_numeric_exists ( char *name, GVT_map_s *map ) {
	if ( (GVT_attr_exists (name, GVT_INT, map)) || (GVT_attr_exists (name, GVT_DOUBLE, map)) ) {
		return ( TRUE );
	}
	return ( FALSE );
}

int GVT_string_exists ( char *name, GVT_map_s *map ) {
	return ( GVT_attr_exists (name, GVT_STRING, map));
}

int GVT_any_exists ( char *name, GVT_map_s *map ) {
  return ( GVT_attr_exists (name, -1, map));
}


/*
    This function returns an attribute value from the current *map record's attributes
    in the currently active layers.
    It bypasses the GVT attribute caching scheme, using SQL calls to get the attribute data
    from the DB which *map is connected to
    If an attribute *name exists, it's string value will be returned. New memory will be
    allocated for the return value and the caller is responsible for releasing it.
    
    If the attribute does not exist, NULL will be returned. NULL will also be returned, if the
    attribute exists, but does not have a value.
    In addition, *ctype will be set to the attribute type or to -1, if the attribute was
    not found. This allows you to differentiate between cases where NULL is returned because
    of a missing attribute and where it is returned because of a missing or NULL value!
        
*/
char *GVT_get_attr_no_cache ( char *name, int *ctype, GVT_map_s *map ) {
	int dbcol;
	char *val = NULL;

  /* these three are pointers to members of the attribute table
     they need not be free'd ! */
	dbColumn *column;
	dbValue  *dbvalue;
	char *colname;	
	
	int sqltype, more;

	if ( map->field != NULL ) {
    *ctype = -1;      	
    /* TODO: Do we really have to go through all this in order to read the current record's attribute values? */
    /* START */
		sprintf ( map->sql_buf, "select * from %s where %s = %d ",
				map->field->table, 
				map->field->key,
				map->vect_cats->cat[ map->current_layer - 1 ]);
		db_set_string ( &map->sql, map->sql_buf );
	  db_open_select_cursor(map->driver, &map->sql, &map->cursor, DB_SEQUENTIAL); /* this does not alloc any memory, so no need to clean up */
	  map->table = db_get_cursor_table (&map->cursor);	
	  db_fetch ( &map->cursor, DB_NEXT, &more );
	  /* END of stuff to do for reading attribute values */
			
		/* now find the right attribute col and read the value in there */
		/* TODO: need to update dbncols = db_get_table_number_of_columns (map->table) */
		for ( dbcol = 0; dbcol < map->dbncols; dbcol ++ ) {
			column = db_get_table_column(map->table, dbcol);
			sqltype = db_get_column_sqltype (column);
			*ctype = db_sqltype_to_Ctype(sqltype);
			colname = (char*) db_get_column_name (column);									
			if (!strcmp (colname,name)){
				dbvalue  = db_get_column_value(column);
				if ( db_test_value_isnull (dbvalue) ) {
				  /* got a null value, so return NULL! */
				  db_close_cursor(&map->cursor);
				  return ( NULL );
        }
				db_convert_value_to_string( dbvalue, sqltype, &map->str);						
				val = strdup ( db_get_string ( &map->str ) );
				
       	if ( GVT_DEBUG > 1 ) {
	        fprintf ( stderr, "GVT: ATT TXT = %s\n", val );
        }
        db_close_cursor(&map->cursor);				
				return (val);						
			}
		}		
		db_close_cursor(&map->cursor);
	}
	
	/* return value will be NULL, if nothing was read or attribute missing !!!! */	
	return ( NULL );
}

/*
  STUB FUNCTION
*/
char *GVT_get_attr ( char *name, int *ctype, GVT_map_s *map ) {
  return GVT_get_attr_no_cache ( name, ctype, map );
}



/*
    This function returns a DOUBLE attribute value from the current *map record's attributes
    in the currently active layers.
    
    If the attribute does not exist or is not of the right type, program execution will be aborted.
    In all other cases, the return value will be a double value.
*/
double GVT_get_double ( char *name, GVT_map_s *map) {
	double val; 
	char *att;
	int ctype;

  /* TODO: set this to standardized NULL value for DOUBLE attributes !!! */
  val = 0.0;

  /* get raw attribute text */
  att = GVT_get_attr ( name, &ctype, map );
  
  if ( att == NULL ) {
    /* something is wrong */
    if ( ctype == -1 ) {
      G_fatal_error (_( "GVT: Missing attribute '%s' in map '%s'.\n"), name, map->name );
    }
    if ( ctype != GVT_DOUBLE ) {
      G_fatal_error (_( "GVT: Attribute '%s' in map '%s' not of type DOUBLE.\n"), name, map->name);
    }
    /* double attribute exists, but has no value */ 
    return ( val );
  }
  
	val = atof ( att );
  G_free ( att );

	if ( GVT_DEBUG > 1 ) {
	 fprintf ( stderr, "GVT: DBL VAL = %.f\n", val );
	}
   					
	return (val);
}


/*
    This function returns an INTEGER attribute value from the current *map record's attributes
    in the currently active layers.
    
    If the attribute does not exist or is not of the right type, program execution will be aborted.
    In all other cases, the return value will be a double value.
*/
int GVT_get_int ( char *name, GVT_map_s *map) {
	int val; 
	char *att;
	int ctype;

  /* TODO: set this to standardized NULL value for INTEGER attributes !!! */
  val = 0;

  /* get raw attribute text */
  att = GVT_get_attr ( name, &ctype, map );
  
  if ( att == NULL ) {
    /* something is wrong */
    if ( ctype == -1 ) {
      G_fatal_error (_("GVT: Missing attribute '%s' in map '%s'.\n"), name, map->name );
    }
    if ( ctype != GVT_INT ) {
      G_fatal_error (_("GVT: Attribute '%s' in map '%s' not of type INTEGER.\n"), name, map->name );
    }
    /* integer attribute exists, but has no value */ 
    return ( val );
  }
  
	val = atoi ( att );
  G_free ( att );

	if ( GVT_DEBUG > 1 ) {
	 fprintf ( stderr, "GVT: INT VAL = %.i\n", val );
	}
   					
	return (val);
}


/*
  This will read an attribute that's either double or integer type and always
  returns the value as a double type.
  
  The return value is the same as for function GVT_get_double ().
*/
double GVT_get_numeric ( char *name, GVT_map_s *map) {
	double val; 
	char *att;
	int ctype;

  /* TODO: set this to standardized NULL value for DOUBLE attributes !!! */
  val = 0.0;

  /* get raw attribute text */
  att = GVT_get_attr ( name, &ctype, map );
  
  if ( att == NULL ) {
    /* something is wrong */
    if ( ctype == -1 ) {
      G_fatal_error (_("GVT: Missing attribute '%s' in map '%s'.\n"), name, map->name );
    }
    if ( ctype != (GVT_DOUBLE || GVT_INT) ) {
      G_fatal_error (_("GVT: Attribute '%s' in map '%s' not of type DOUBLE or INTEGER.\n"), name, map->name );
    }
    /* attribute exists, but has no value */ 
    return ( val );
  }
  
	val = atof ( att );
  G_free ( att );

	if ( GVT_DEBUG > 1 ) {
	 fprintf ( stderr, "GVT: NUM VAL = %.f\n", val );
	}
   					
	return (val);
}


/*
    This function returns a STRING attribute value from the current *map record's attributes
    in the currently active layers.
    
    If the attribute does not exist or is not of the right type, program execution will be aborted.
    In all other cases, the return value will be a string value (NULL if the attribute did not have a value).
    
    New memory will be allocated for the string returned and must be free'd by the caller.
*/
char *GVT_get_string ( char *name, GVT_map_s *map) {
	char *att;
	int ctype;


  /* get raw attribute text */
  att = GVT_get_attr ( name, &ctype, map );
  
  if ( att == NULL ) {
    /* something is wrong */
    if ( ctype == -1 ) {
      G_fatal_error (_( "GVT: Missing attribute '%s' in map '%s'.\n"), name, map->name );
    }
    if ( ctype != GVT_STRING ) {
      G_fatal_error (_("GVT: Attribute '%s' in map '%s' not of type STRING.\n"), name, map->name );
    }
    /* double attribute exists, but has no value */ 
    return ( NULL );
  }
  
	if ( GVT_DEBUG > 1 ) {
	 fprintf ( stderr, "GVT: STR VAL = %s\n", att );
	}
   					
	return ( att );
}


/* TODO: implement C API attribute writes in GVT_set_double2 and delete this version ! */
/* this writes a new value into a double type attribute of the current record */
int GVT_set_double ( char *name, double dvalue, GVT_map_s *map ) { 

	char tmp [GVT_MAX_STRING_SIZE];

	map->field = Vect_get_field (&map->in_vect_map, map->vect_cats->field[ map->current_layer - 1 ]);
	/* TODO: in which cases could field == NULL? what to do then? */
	/* TODO: catch cases without a DB connection */
	if ( map->field != NULL ) {
		sprintf ( tmp, "echo \"UPDATE %s SET %s=%f WHERE cat=%d\" | db.execute", map->name, name, dvalue, map->vect_cats->cat[map->current_layer - 1]);
		system ( tmp );
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
					if (ctype == GVT_DOUBLE) {					
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

	/* TODO: replace system call with appropriate C API calls */
	/* TODO: check if column with same name (but different type) exists */
	
	sprintf ( buf, "echo \"ALTER TABLE %s ADD COLUMN %s double precision\" | db.execute", map->name, name );
	fprintf ( stderr, "%s\n", buf );
	system ( buf );
	
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
	double a,b,c;

	/* TODO: check if it's a points map! */
	
	if ( map->isLatLong ) {
		px = *map->vect_points->x;
		py = *map->vect_points->y;
		d = G_geodesic_distance ( x, y, px, py );
	} else {
		px = *map->vect_points->x;
		py = *map->vect_points->y;		
		a = fabs (px - x);
		b = fabs (py - y);
		c = sqrt ( pow (a,2.0) + pow (b,2.0) );
		d = c;
	}
	
	return (d);
}

double GVT_get_point_x ( GVT_map_s *map ) {
	/* TODO: check if this is a point map */
	return ( *map->vect_points->x );
}

double GVT_get_point_y ( GVT_map_s *map ) {
	/* TODO: check if this is a point map */
	return ( *map->vect_points->y );	
}




