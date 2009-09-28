/***************************************************************************
 *            gt_vector.h
 *
 *  Mon Apr 18 15:23:06 2005
 *  Copyright  2005  Benjamin Ducke
 ****************************************************************************/

/*
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Library General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */
 
#ifndef _GT_VECTOR_H
#define _GT_VECTOR_H

#include <grass/gis.h>
#include <grass/dbmi.h>
#include <grass/Vect.h>

#define CLEAN 0
#define DIRTY 1

#define GVT_MAX_STRING_SIZE 4096
#define GVT_EMPTY_SQL "EMPTY"

/* GVT data types match column types in grass/dbmi.h */
#define GVT_DOUBLE DB_C_TYPE_DOUBLE
#define GVT_INT DB_C_TYPE_INT
#define GVT_STRING DB_C_TYPE_STRING

typedef struct GVT_map {

	char name[GVT_MAX_STRING_SIZE];
	char mapset[GVT_MAX_STRING_SIZE];

	int num_layers; /* layers are called fields in the vect API */
	int current_layer; /* -1 means: parse ALL layers! */
	long int current_record;
	long int num_records;
	int num_attributes;
	
	struct Map_info in_vect_map;
	struct line_pnts *vect_points;
	struct line_cats *vect_cats;
	struct field_info *field; /* a pointer to the current layer (=field) */
	int dbncols; 
	char sql_buf[GVT_MAX_STRING_SIZE];	
	dbString sql, str;
	dbDriver *driver;
	dbHandle handle;
	dbCursor cursor;
	dbTable  *table;
		
	/* topology properties */
	short int open_level;
	
	/* coordinate data properties */
	short int is3d;
	short int isLatLong;
	short int type;
	
	/* constraints */
	double north, south, east, west, top, bottom;
	int type_constraints;
	
	/* attribute cache and memory ops */
	short int *status;
	double **cache_double;
	short int **cache_short;
	int **cache_int;
	long int **cache_long;
	char **cache_char;
	
	size_t mem_size;
	
} GVT_map_s;

int GVT_NO_REGION_CONSTRAINTS;
int GVT_NO_TYPE_CONSTRAINTS;
int GVT_NO_SQL_CONSTRAINTS;

int GVT_NO_ATTRIBUTE_CACHING;

/* if set, GRASS module will terminate on file I/O errors */
int GVT_FATAL_FILE_ERRORS;
int GVT_FATAL_TYPE_ERRORS;
int GVT_FATAL_MEM_ERRORS;

int GVT_INIT_DONE;

/**** FUNCTIONS *****/

void GVT_init ( void );

GVT_map_s *GVT_new_map ( void );
int GVT_free_map ( GVT_map_s *map );

int GVT_open_map ( char *mapname, int type, GVT_map_s *map );
int GVT_open_map_points ( char *mapname, int type, GVT_map_s *map );
void GVT_close_map ( GVT_map_s *map );

int GVT_next ( GVT_map_s *map );
int GVT_seek ( long int pos, GVT_map_s *map );
void GVT_first ( GVT_map_s *map );
void GVT_last ( GVT_map_s *map );
void GVT_rewind ( GVT_map_s *map );
long int GVT_get_current ( GVT_map_s *map );

/* Attribute functions */

/* check attributes */
int GVT_double_exists ( char *name, GVT_map_s *map );
int GVT_int_exists ( char *name, GVT_map_s *map );
int GVT_numeric_exists ( char *name, GVT_map_s *map );
int GVT_string_exists ( char *name, GVT_map_s *map );
int GVT_any_exists ( char *name, GVT_map_s *map );

/* read attributes */
double GVT_get_double ( char *name, GVT_map_s *map);
int GVT_get_int ( char *name, GVT_map_s *map);
double GVT_get_numeric ( char *name, GVT_map_s *map);
char *GVT_get_string ( char *name, GVT_map_s *map);

/* modify attributes */
int GVT_set_double ( char *name, double dvalue, GVT_map_s *map );
int GVT_add_double ( char *name, GVT_map_s *map );

/* Info functions */
long int GVT_get_num_objects ( GVT_map_s *map );

/* Geometry functions */
double GVT_get_2D_point_distance ( double x, double y, GVT_map_s *map );
double GVT_get_point_x ( GVT_map_s *map );
double GVT_get_point_y ( GVT_map_s *map );


#endif /* _GT_VECTOR_H */
