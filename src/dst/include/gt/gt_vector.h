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

/* states for attribute caches */
#define GVT_CACHE_DIRTY -1	/* means we have to rebuild the cache by reading in all attributes */
#define GVT_CACHE_INIT 0	/* means we need to initialize this cache */
#define GVT_CACHE_CLEAN 1	/* this cache is fine. Can use it to get attributes */
#define GVT_CACHE_OFF 2		/* this cache is turned off: read attributes the slow way! */

#define GVT_MAX_STRING_SIZE 4096
#define GVT_EMPTY_SQL "GVT_SEQ_EMPTY"

/* any type of attribute */
#define GVT_ATT
/* specific types of attributes. Thes mape 1:1 to the main types in grass/dbmi.h */
#define GVT_DOUBLE DB_C_TYPE_DOUBLE
#define GVT_INT DB_C_TYPE_INT
#define GVT_STRING DB_C_TYPE_STRING
#define GVT_DATETIME DB_C_TYPE_DATETIME

/* any type of geometry */
#define GVT_GEOM
/* specific types of geometry. These map 1:1 to grass/vect/dig_defines.h */
#define GVT_POINT GV_POINT
#define GVT_LINE GV_LINE
#define GVT_BOUNDARY GV_BOUNDARY
#define GVT_CENTROID GV_CENTROID
#define GVT_AREA GV_AREA
/* 3D geometries	*/
#define GVT_KERNEL GV_KERNEL
#define GVT_FACE GV_FACE
#define GVT_VOLUME GV_VOLUME
/* Combination types	*/
#define GV_2D_POINT (GVT_POINT | GVT_CENTROID)
#define GV_2D_LINE (GVT_LINE | GVT_BOUNDARY)
/* the following are additions for GVT	*/
/* any 2D geometry	*/
#define GVT_2D_GEOM (GVT_POINT | GVT_LINE | GVT_BOUNDARY | GVT_CENTROID | GVT_AREA)
/* any 3D geometry	*/
#define GVT_3D_GEOM (GVT_KERNEL | GVT_FACE | GVT_VOLUME)



typedef struct GVT_map {
	/* name and mapset in GRASS database */
	char name[GVT_MAX_STRING_SIZE];
	char mapset[GVT_MAX_STRING_SIZE];

	/* set this to TRUE (1), if a vector map was opened successfully */
	short int hasData;

	/* infos on number of layers (DB link=table) and records (row of DB values=attributes) */
	/* num_attributes is the number of columns (including CAT) in a table */
	int num_layers; /* tables (layers) are called fields in the GRASS vect API */
	long int num_records;
	int num_attributes;

	int current_layer; /* -1 means: parse ALL layers! */	
	long int current_record;
	
	struct Map_info in_vect_map;
	struct line_pnts *vect_points;
	struct line_cats *vect_cats;
	struct field_info *field; /* a pointer to the current table (=field=layer) */
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
	char **att_names; /* list of attribute names */
	short int *att_types; /* list of attribute types (GVT geometry types) */
	
	short int *cache_status;
	double **cache_double;
	long int **cache_int;
	char **cache_char;
	char **cache_datetime;
	
	/* this is for tracking the total amount of memory claimed by this map */
	size_t mem_size;
	
} GVT_map_s;


/* these global variables are set to default values by GVT_init () */
int GVT_NO_REGION_CONSTRAINTS;
int GVT_NO_TYPE_CONSTRAINTS;
int GVT_NO_SQL_CONSTRAINTS;

int GVT_NO_ATTRIBUTE_CACHING;
long int GVT_MAX_CACHE_SIZE;

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

int GVT_attr_exists ( char *name, int type, GVT_map_s *map );
int GVT_any_exists ( char *name, GVT_map_s *map );
int GVT_double_exists ( char *name, GVT_map_s *map );
int GVT_int_exists ( char *name, GVT_map_s *map );

double GVT_get_double ( char *name, GVT_map_s *map);
long int GVT_get_int ( char *name, GVT_map_s *map);
int GVT_set_double ( char *name, double dvalue, GVT_map_s *map );
int GVT_add_double ( char *name, GVT_map_s *map );

long int GVT_get_num_objects ( GVT_map_s *map );

double GVT_get_2D_point_distance ( double x, double y, GVT_map_s *map );


#endif /* _GT_VECTOR_H */
