/* modified by Benjamin Ducke to work with different raster map types */
/* May 2004 */

/**************************************************************************/
/* 
   Use fract to set the number of segments.  On a machine with 32Kb RAM 
   it is possible that only 1 segment is required unless many maps
   are to be opened simultaneously.  Increasing the number of segments
   seriously degrades performance                	  						   */

/**************************************************************************/

#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <grass/gis.h>
#include <grass/segment.h>

char* Create_segment_file (int, int, RASTER_MAP_TYPE);
int Init_segment_file (char*, SEGMENT*);


/**************************************************************************/
/* Public functions                                                       */
/**************************************************************************/

void Close_segmented_infile (int map_fd, char* seg_name, int seg_fd, SEGMENT* seg)
{
  segment_release (seg);
  close (seg_fd);
  unlink (seg_name);
  G_close_cell (map_fd);
}


/* Create result map in CELL format */
/* NULL cell handling added by Benjamin Ducke, May 2004 */
void Close_segmented_outfile (char* map_name, int map_fd,
			             char* seg_name, int seg_fd, SEGMENT* seg, 
                         CELL* cell_buf, int terse,
                         SEGMENT* elevation_seg, RASTER_MAP_TYPE data_type, int make_nulls)
{
  unsigned long row, nrows, col, ncols;
  void *value = NULL;
  char *null_flags;
  /* the following are used to store different raster map types */
  CELL c_value;
  FCELL f_value;
  DCELL d_value;  	

	
  /* Find number of rows and columns in elevation map */
  nrows = G_window_rows();
  ncols = G_window_cols();
	
  /* allocate memory for a NULL data row */	
  null_flags = G_calloc ((signed) ncols, sizeof (char));
    
  /* Write pending updates by segment_put() to output map */
  segment_flush(seg);
  
  if (!terse) {	
    fprintf (stdout, "\nWriting raster map '%s': \n", map_name);	
  }
	
  /* Convert output submatrices to full cell overlay */
  for(row=0; row< nrows; row++) {
    segment_get_row(seg, cell_buf, (signed) row);
	/* check for NULL values in the corresponding row of the */
	/* elevation input file. If there are any, set the CELLs */
	/* in the output file to NULL, as well */
	
	/* initialize null data row */
	for (col=0; col<ncols; col++) {
		null_flags[col] = 0;
	}
	
	/* convert all -1 cells to NULL, if user wants it so */
    if ( make_nulls == 1 ) {
	    for (col=0; col<ncols; col++) {
		   if ( cell_buf[col] == -1 ) {
		     null_flags[col] = 1;
		   }
		}
	}
	
	/* update NULL flags in row */
    for (col=0; col<ncols; col++) {
		if ( data_type == CELL_TYPE ) {
		    value = (CELL*) &c_value;
		}		  
		if ( data_type == FCELL_TYPE ) {
		    value = (FCELL*) &f_value;
		}		  
		if ( data_type == DCELL_TYPE ) {
		    value = (DCELL*) &d_value;
		}
		
        segment_get (elevation_seg, value, (signed) row, (signed) col);
		
		/* check for NULL value and record in null_flags row */
		if ( data_type == CELL_TYPE ) {
		    if (G_is_c_null_value (&c_value) ) {
			  null_flags[col] = 1; /* signal NULL value in null_flags row */
			}			
		}		  
		if ( data_type == FCELL_TYPE ) {
		    if (G_is_f_null_value (&f_value) ) {
			  null_flags[col] = 1; /* signal NULL value in null_flags row */
			}
		}		  
		if ( data_type == DCELL_TYPE ) {
		    if (G_is_d_null_value (&d_value) ) {
			  null_flags[col] = 1; /* signal NULL value in null_flags row */
			}						
		}
	}
    /* set all NULL cells according to null_flags row */
	G_insert_c_null_values (cell_buf, null_flags, (signed) ncols);
	
	/* now, write this row to disk */  
    if(G_put_raster_row (map_fd, cell_buf, CELL_TYPE) < 0) {
	  G_fatal_error ("Failed to convert output submatrices ");	  
	}
	
	/* progress display */
	if (! terse) {
		G_percent ((signed) row, (signed) nrows-1,2);
	}	
  }
  
  G_free (null_flags);
  
/* Close files */
  segment_release (seg);
  close (seg_fd);
  unlink (seg_name);
  G_close_cell (map_fd);
}

void Close_segmented_tmpfile (char *seg_name, int seg_fd, SEGMENT *seg)
{
  /* Close files */
  segment_release (seg);
  close (seg_fd);
  unlink (seg_name);
}

/* this routine creates four segment files on disk, then stores */
/* a raster map in them */
/* store a raster map in a mem segment on disk */
void Segment_infile (char* map_name, char* mapset, char* search_mapset, int* map_fd, 
		char* seg_name, int* seg_fd, SEGMENT* seg, void *cell_buf, int fract, 
        RASTER_MAP_TYPE data_type)
{
    int nrows, row;

    strcpy (mapset, G_find_cell (map_name, search_mapset));
    if (mapset == NULL)
	  G_fatal_error ("Can't find displayed data layer ");
    if ((*map_fd = G_open_cell_old (map_name, mapset)) < 0)
	  G_fatal_error ("Can't open displayed data layer ");

    nrows = G_window_rows ();

	/* next line creates the actual segment, returns name of disk file */
    strcpy (seg_name, Create_segment_file (nrows, fract, data_type));
    *seg_fd = open (seg_name, O_RDWR);

    if (*seg_fd < 0)
	  G_fatal_error ("Cannot open segment disk file ");
	
    segment_init (seg, *seg_fd, 4);
	
	/* store map data in segment file IGNORE MASK */
	/* cell_buf must be pre-allocated by caller! */
    for (row = 0; row < nrows; row++) {
	    if (G_get_raster_row_nomask (*map_fd, cell_buf, row, data_type) < 0) {
	        G_fatal_error ("Unable to read data layer into segment file ");
        }		
	    segment_put_row (seg, cell_buf, row); /* store raster map in segment file */
    }
	
}


/**************************************************************************/

void Segment_outfile (char* map_name, char* mapset, int* map_fd,
		         char* seg_name, int* seg_fd, SEGMENT* seg, char* prompt, int fract,
                 RASTER_MAP_TYPE data_type)
{
    int nrows;
    char* mapset_address;

    mapset_address = G_ask_cell_new (prompt, map_name);
    
	if (mapset_address == NULL)
	  G_fatal_error ("Can't continue without filename ");
	
    strcpy (mapset, mapset_address);
    
	if ((*map_fd = G_open_cell_new (map_name)) < 0)
	  G_fatal_error ("Can't create output layer ");

    nrows = G_window_rows ();
    strcpy (seg_name, Create_segment_file (nrows, fract, data_type));
    *seg_fd = open (seg_name, 2);
    
	if (*seg_fd < 0)
	  G_fatal_error ("Can't open segment disk file ");
	
    segment_init (seg, *seg_fd, 4);
}


/**************************************************************************/

void Segment_named_outfile (char* map_name, char* mapset, int* map_fd,
			           char* seg_name, int* seg_fd, SEGMENT* seg, int overwrite, 
                       int terse, int fract, RASTER_MAP_TYPE data_type)
{
    int nrows;
    char* mapset_address;
    char message [64];

    mapset_address = G_find_cell (map_name, G_mapset ());
    strcpy (mapset, G_mapset ());
    if (mapset_address != NULL)
    {
      if (!overwrite)
	{
	  sprintf (message, "Raster map '%s' exists ", map_name);
	  G_fatal_error (message);
	}
      else
	{
	  if (!terse)
	    fprintf (stdout, "\nOverwriting raster map '%s' ", map_name);
	}
    }
    else
      {
	if (!terse)
	  fprintf (stdout, "\nCreating raster map '%s' ", map_name);
      }

    if ((*map_fd = G_open_cell_new (map_name)) < 0)
	  G_fatal_error ("Can't create output layer ");

    nrows = G_window_rows ();
    
    strcpy (seg_name, Create_segment_file (nrows, fract, data_type));
    
    *seg_fd = open (seg_name, O_RDWR);
	
    if (*seg_fd < 0)
	  G_fatal_error ("Can't open segment disk file ");
	
    segment_init (seg, *seg_fd, 4);
}


void Segment_tmpfile (char* seg_name, int* seg_fd, SEGMENT* seg, int fract, 
                 RASTER_MAP_TYPE data_type)
{
    int nrows;

    nrows = G_window_rows ();

    strcpy (seg_name, Create_segment_file (nrows, fract, data_type));
    *seg_fd = open (seg_name, O_RDWR);
    if (*seg_fd < 0)
	G_fatal_error ("Can't open segment disk file ");
	
	/* get a handle to read segment file data values */
	/* dimensions of segment and size of stored items are read */
	/* automatically from the file header and stored in 'seg' */
    segment_init (seg, *seg_fd, 4);
}


/**************************************************************************/
/* Private functions                                                      */
/**************************************************************************/

char* Create_segment_file (int nrows, int fract, RASTER_MAP_TYPE data_type)
{
    int seg_fd;
    char* seg_name;
    int ncols;
    int submatrix_rows, submatrix_cols; 
    int length_data_item = 0;
    int seg_error;

    ncols = G_window_cols ();
	if (data_type == CELL_TYPE) length_data_item = sizeof (CELL);
	if (data_type == FCELL_TYPE) length_data_item = sizeof (FCELL);
	if (data_type == DCELL_TYPE) length_data_item = sizeof (DCELL);	
    submatrix_rows = nrows/fract + 1;
    submatrix_cols = ncols/fract + 1;
    seg_name = G_tempfile ();
    seg_fd = creat (seg_name, 0666);
	
	/* create a new segment file on disk */
	/* size of data items (CELL, DCELL, FCELL ...) is stored in the file header */
    seg_error = segment_format (seg_fd, nrows, ncols,
		    submatrix_rows, submatrix_cols, length_data_item); 
	
	if ( seg_error != 1 ) {
		G_fatal_error ("Cannot create segment file(s).\nCheck available diskspace and access rights.");
	}
    close (seg_fd);
	
    return seg_name;
}


/**************************************************************************/

int Init_segment_file (char* seg_name, SEGMENT* seg)
{
    int seg_fd;

    seg_fd = open (seg_name, 2);
    if (seg_fd < 0)
	G_fatal_error ("Cannot open segment disk file");
    segment_init (seg, seg_fd, 4);
    return seg_fd;
}
