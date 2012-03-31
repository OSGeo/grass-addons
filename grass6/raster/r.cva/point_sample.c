/***********************************************************************/
/*
  point_sample.c

  Updated by Mark Lake on 17/8/01 for GRASS 5.x

  CONTAINS

  1) point_sample                                                      */

/***********************************************************************/

/***********************************************************************/
/*
  point_sample

  Called from:
  
  1) main                   main.c
 
  Calls:
 
  1) line_of_sight          line_of_site.c
  2) count_visible_cells    count_visible_cells.c
  3) cumulate_visible_cells cumulate_visible_cells.c
  4) delete_lists           delete_lists.c                             */

/***********************************************************************/

#include <stdlib.h>
#include <string.h>

#include <grass/gis.h>
#include <grass/segment.h>
#include <grass/Vect.h>
#include <grass/dbmi.h>

#include "config.h"
#include "point.h"
#include "global_vars.h"

#include "init_segment_file.h"
#include "line_of_sight.h"
#include "count_visible_cells.h"
#include "cumulate_visible_cells.h"
#include "delete_lists.h"


void point_sample (struct Cell_head *window, int nrows, int ncols,
		   SEGMENT *seg_in_p, SEGMENT *seg_out_1_p,
		   SEGMENT *seg_out_2_p, SEGMENT *seg_patt_p,
		   SEGMENT *seg_patt_p_v,
		   double *attempted_sample, double *actual_sample,
		   char *site_file, int terse, RASTER_MAP_TYPE data_type,
		   int ignore_att)
{
  int row_viewpt, col_viewpt;
  
  /* 'value' stores a byte-sized (CELL) item from the mask segment file(s) */
  void *value = NULL;
  	
  CELL cell_no;
  double viewpt_elev = 0;
  struct point *heads[16];
  long int sites_in_region, sites_of_interest, cells_in_map;
  int null_value;
  char *site_mapset;
  CELL mask = 0;
  long num_sites = 0;
  /* the following are used to store different raster map types */
  CELL c_value;
  FCELL f_value;
  DCELL d_value;

  struct Map_info in_vect_map;
  struct line_pnts *vect_points;
  struct line_cats *vect_cats;
  int cur_type;
  char errmsg [200];
  double x,y,z;
  int n_points = 1;
  
  /* site attribute management */
  int i;
  struct field_info *field;
  char     buf[5000], *colname;   
  int      dbcol, dbncols, ctype, sqltype, more; 
  dbString sql, str;
  dbDriver *driver;
  dbHandle handle;
  dbCursor cursor;
  dbTable  *table;
  dbColumn *column;
  dbValue  *dbvalue;

 
  vect_points = Vect_new_line_struct ();
  vect_cats = Vect_new_cats_struct ();

  if ((site_mapset = G_find_vector2 (site_file, "")) == NULL) {
    sprintf (errmsg, "Could not find input vector map %s\n", site_file);
    G_fatal_error (errmsg);

  }

  Vect_set_open_level (1);        
  if (1 > Vect_open_old (&in_vect_map, site_file, site_mapset)) {
    sprintf (errmsg, "Could not open input vector points.\n");
    G_fatal_error (errmsg);
  }


  /* Initialise output segment file with appropriate data value */
  init_segment_file (nrows, ncols, seg_out_2_p, seg_patt_p);

  /* Initialise variables */
  cells_in_map = nrows * ncols;
  sites_in_region = 0;
  sites_of_interest = 0;
  cell_no = 0;

  /* filter vector objects to current region and point types only */
  Vect_set_constraint_region (&in_vect_map, window->north, window->south, 
			      window->east, window->west, 0.0, 0.0); 
  Vect_set_constraint_type (&in_vect_map, GV_POINT);
  
  /* calculate number of vector points in map and current region */
  while ((cur_type = Vect_read_next_line (&in_vect_map, vect_points, NULL)) > 0) {     
      num_sites ++;            
  }

  /* rewind vector points file: close and re-open */
  Vect_close (&in_vect_map);
  Vect_open_old(&in_vect_map, site_file, site_mapset);
  Vect_set_constraint_type (&in_vect_map, GV_POINT);
  Vect_set_constraint_region (&in_vect_map, window->north, window->south,
                              window->east, window->west, 0.0, 0.0);
    
  
  /* Traverse site list  */  
  while ((cur_type = Vect_read_next_line (&in_vect_map, vect_points, vect_cats)) > 0) {
    mask = 0;
    cell_no ++;
    
    /* check for site attributes */
    for (i = 0; i < vect_cats->n_cats; i++) {
    	field = Vect_get_field( &in_vect_map, vect_cats->field[i]);
	if ((field != NULL) && (!ignore_att)) {
		db_init_string (&sql);
		driver = db_start_driver(field->driver);
		db_init_handle (&handle);
		db_set_handle (&handle, field->database, NULL);
		if (db_open_database(driver, &handle) == DB_OK){
			/* sql query */
			sprintf (buf, "select * from %s where %s = %d", field->table, 
									field->key, 
									vect_cats->cat[i]);
			db_set_string (&sql, buf);
			
			db_open_select_cursor(driver, &sql, &cursor, DB_SEQUENTIAL);
			table = db_get_cursor_table (&cursor);
			db_fetch (&cursor, DB_NEXT, &more );
			dbncols = db_get_table_number_of_columns (table);
			for( dbcol = 0; dbcol < dbncols; dbcol++) {
				column = db_get_table_column(table, dbcol);
				sqltype = db_get_column_sqltype (column);
				ctype = db_sqltype_to_Ctype(sqltype);
				dbvalue  = db_get_column_value(column);
				db_convert_value_to_string( dbvalue, sqltype, &str);
				colname = db_get_column_name (column);
				/* check if we have some of the supported attributes */
				if (ctype == DB_C_TYPE_DOUBLE) {
					if (!strcmp (colname,"SPOT")){
						SPOT = atof (db_get_string (&str));
						SPOT_SET = 1;
					}
					if (!strcmp (colname,"OFFSETA")){
						obs_elev = atof (db_get_string (&str));
					}
					if (!strcmp (colname,"OFFSETB")){
						OFFSETB_SET =1;
						OFFSETB = atof (db_get_string (&str));
					}
					if (!strcmp (colname,"AZIMUTH1")){
						AZIMUTH1 = atof (db_get_string (&str));
						AZIMUTH1_SET = 1;
					}				
					if (!strcmp (colname,"AZIMUTH2")){
						AZIMUTH2 = atof (db_get_string (&str));
						AZIMUTH2_SET = 1;
					}				
					if (!strcmp (colname,"VERT1")){
						VERT1 = atof (db_get_string (&str));
						VERT1_SET = 1;
					}				
					if (!strcmp (colname,"VERT2")){
						VERT2 = atof (db_get_string (&str));
						VERT2_SET = 1;
					}				
					if (!strcmp (colname,"RADIUS1")){
						RADIUS1 = atof (db_get_string (&str));
					}				
					if (!strcmp (colname,"RADIUS2")){
						max_dist = atof (db_get_string (&str));
					}
				}								
			}
			db_close_cursor(&cursor);
			db_close_database(driver);
			db_shutdown_driver(driver); 			
		} else {
			db_shutdown_driver(driver);
		}
	}
    }
    
    Vect_copy_pnts_to_xyz (vect_points, &x, &y, &z, &n_points);
    /* If site falls within current region */	  
	  sites_in_region ++;
		
	  /* Get array coordinates of viewpoint */			 
	  /* row_viewpt = (window->north - site->north) / window->ns_res;
          col_viewpt = (site->east - window->west) / window->ew_res;
	  */
	  row_viewpt = G_northing_to_row ( y, window );
	  col_viewpt = G_easting_to_col ( x, window );
	  
	  /* Check whether viewpoint is in area of interest */
	  if (patt_flag_v) {
	    value = (char*) &mask;
	    segment_get(seg_patt_p_v, value, row_viewpt, col_viewpt);
	  } else 
	    mask = 1;
	  
	  /* Only include if viewpoint is in area of interest */
	  if (mask == 1) {
	    sites_of_interest ++;

	    /* We do not check for duplicates because it is possible
		in cases of low resolution that two or more sites with 
		different map coordinates could have the same array 
		coordinates */

	    /* Read elevation of current view point */			
	    if ( data_type == CELL_TYPE ) {
	      value = (CELL*) &c_value;
	    }		      
	    if ( data_type == FCELL_TYPE ) {
	      value = (FCELL*) &f_value;
	    }		      
	    if ( data_type == DCELL_TYPE ) {
	      value = (DCELL*) &d_value;
	    }
	    
	    null_value = 0;
	    segment_get (seg_in_p, value, row_viewpt, col_viewpt); /* height now in value */    														     /* and in read_viewpt_elev */
	   
	    if ( data_type == CELL_TYPE ) {
		viewpt_elev = c_value + obs_elev;
		if (G_is_c_null_value (&c_value)) {
			null_value = 1;
		}		
            }		
	    if ( data_type == FCELL_TYPE ) {
	    	viewpt_elev = f_value + obs_elev;
		if (G_is_f_null_value (&f_value)) {
			null_value = 1;
		}		
            }		
	    if ( data_type == DCELL_TYPE ) {
	    	viewpt_elev = d_value + obs_elev;
		if (G_is_d_null_value (&d_value)) {
			null_value = 1;
		}
            }

	    /* skip sites on NULL dem cells */
	    if (!null_value) {
	    	if (SPOT_SET) {
	       		if (ADJUST) {
				if (SPOT >= viewpt_elev) {
					viewpt_elev = SPOT + obs_elev;
				}
	       		} else {
	    			viewpt_elev = SPOT;
			}
	    	}	    
	    
	    	/* Do line of sight analysis from current viewpoint */	      
		/* this updates the information in 'heads', defined in 'point.h' */
	    	line_of_sight (cell_no, row_viewpt, col_viewpt,
			           nrows, ncols, viewpt_elev,
			           heads, seg_in_p, seg_out_1_p, seg_patt_p,
			           patt_flag, data_type);
	      	      
	    	/* Calculate viewshed */	      
	    	if (! from_cells) {
			count_visible_cells (cell_no, row_viewpt, col_viewpt,
		                       seg_out_1_p, seg_out_2_p, seg_patt_p, heads);
		} else
			cumulate_visible_cells (cell_no, row_viewpt, col_viewpt,
		                          seg_out_1_p, seg_out_2_p, seg_patt_p, heads);	      
	      	      
	    	/* Free memory used in line-of-sight analysis */	      
	    	delete_lists (heads);
	    }
	    
	    /* Print progress message */
	    if (!terse) {
			G_percent (sites_of_interest, num_sites, 1);
	    }
	  } /* END (if (mask == 1)) */		
  } /* END (loop through sites list) */
  Vect_close (&in_vect_map);

  /* Calculate_sample */
  /* % of cells in region */
  *attempted_sample = 100.0 / (double) cells_in_map * (double) sites_in_region;

  /* % of cells in area of interest */
  *actual_sample = 100.0 / (double) cells_in_map * (double) sites_of_interest;

#ifdef DEBUG
  fprintf (stdout, "\nSites in: region = %ld, area of interest = %ld", 
	   sites_in_region,
	   sites_of_interest);
  fflush (stdout); 
#endif
}
