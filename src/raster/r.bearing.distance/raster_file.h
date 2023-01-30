/***********************************************************************/
/*
   raster_file.h

   Revised by Mark Lake, 26/07/20017, for r.horizon in GRASS 7.x
   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 15/07/2002, for r.horizon in GRASS 5.x

   NOTES
   Once maps are loaded into a buffer, it is possible to read and write
   individual map cell values addressed by row and col, where row 0
   is the top row in the rast map and col 0 is the left-hand column
   in the raster map.

 */

/***********************************************************************/

#ifndef RASTER_FILE_H
#define RASTER_FILE_H

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

void *Allocate_raster_buf_with_null(RASTER_MAP_TYPE);

/* Allocate_raster_buf_with_null (buffer data type)
   N.B. this does not have to be the same data type as the map
   whose contents are read into it or written from it, since
   'Read_raster_infile' and 'Write_raster_outfile' can convert */

void Check_raster_outfile(char *, char *, int);

/* Check_raster_outfile (map name, mapset, overwrite flag)
   Raises a fatal error in map exists */

void Close_raster_file(int);

/* Close_raster_infile (file descriptor) */

void Copy_raster_buf(void *, void *, RASTER_MAP_TYPE, RASTER_MAP_TYPE);

/* Copy_raster_buf (pointer to input buffer, pointer to output buffer,
   input buffer data type, output buffer data type) */

void Copy_raster_buf_with_rounding(void *, void *, RASTER_MAP_TYPE,
                                   RASTER_MAP_TYPE);
/* Copy_raster_buf_with_rounding (pointer to input buffer,
   pointer to output buffer, input buffer data type,
   output buffer data type) */

CELL Get_buffer_value_c_row_col(void *, RASTER_MAP_TYPE, int, int);

/* Get_buffer_value_c_row_col (pointer to buffer, buffer data type,
   row, column)
   Returns truncated CELL value at row, column */

CELL Get_buffer_value_rounded_c_row_col(void *, RASTER_MAP_TYPE, int, int);

/* Get_buffer_value_rounded c_row_col (pointer to buffer,
   buffer data type, row, column)
   Returns rounded CELL value at row, column */

DCELL Get_buffer_value_d_row_col(void *, RASTER_MAP_TYPE, int, int);

/* Get_buffer_value_d_row_col  (pointer to buffer, buffer data type,
   row, column)
   Returns DCELL value at row, column */

FCELL Get_buffer_value_f_row_col(void *, RASTER_MAP_TYPE, int, int);

/* Get_buffer_value_f_row_col (pointer to buffer, buffer data type,
   row, column)
   Returns FCELL value at row, column */

int Open_raster_infile(char *, char *, char *, RASTER_MAP_TYPE *, char *);

/* Open_raster_infile (map name, mapset, search mapset,
   raster map data type, string to receive error message)
   Returns file descriptor */

int Open_raster_outfile(char *, char *, RASTER_MAP_TYPE, int, char *);

/* Open_raster_outfile (map name, mapset, raster map data type,
   overwrite flag, string to receive error message )
   Returns file descriptor */

void Print_raster_buf(void *, RASTER_MAP_TYPE, FILE *);

/* Print_raster_buf (pointer to buffer, buffer data type, stream) */

void Print_raster_buf_row_col(void *, RASTER_MAP_TYPE, FILE *);

/* Print_raster_buf_row_col (pointer to buffer, buffer data type, stream) */

void Read_raster_infile(void *, int, RASTER_MAP_TYPE, RASTER_MAP_TYPE);

/* Read_raster_infile (pointer to buffer, file descriptor, buffer data type,
   map data type) */

void Set_buffer_value_c_row_col(void *, CELL, RASTER_MAP_TYPE, int, int);

/* Set_buffer_value_c_row_col (pointer to buffer, CELL value to set,
   buffer data type, row, column) */

void Set_buffer_null_c_row_col(void *, RASTER_MAP_TYPE, int, int);

/* Set_buffer_null_c_row_col (pointer to buffer,
   buffer data type, row, column) */

void Set_buffer_value_d_row_col(void *, DCELL, RASTER_MAP_TYPE, int, int);

/* Set_buffer_value_d_row_col (pointer to buffer, DCELL value to set,
   buffer data type, row, column) */

void Set_buffer_null_d_row_col(void *, RASTER_MAP_TYPE, int, int);

/* Set_buffer_null_d_row_col (void* out_buf,
   RASTER_MAP_TYPE out_buf_type,
   int row, int col) */

void Set_buffer_value_f_row_col(void *, FCELL, RASTER_MAP_TYPE, int, int);

/* Set_buffer_value_f_row_col (pointer to buffer, FCELL value to set,
   buffer data type, row, column) */

void Set_buffer_null_f_row_col(void *, RASTER_MAP_TYPE, int, int);

/* Set_buffer_null_f_row_col (pointer to buffer,
   buffer data type, row, column) */

void Write_raster_outfile(void *, int, RASTER_MAP_TYPE, RASTER_MAP_TYPE);

/* Write_raster_outfile (pointer to buffer, file descriptor,
   buffer data type, map data type) */

void Write_raster_outfile_with_rounding(void *, int, RASTER_MAP_TYPE,
                                        RASTER_MAP_TYPE);
/* Write_raster_outfile_with_rounding (pointer to buffer, file descriptor,
   buffer data type, map data type) */

#endif
