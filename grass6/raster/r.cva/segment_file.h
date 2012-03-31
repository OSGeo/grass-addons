#ifndef __SEGMENT_FILE_H__
#define __SEGMENT_FILE_H__

#include <grass/gis.h>
#include <grass/segment.h>

void Segment_infile (char* map_name, char* mapset, char* search_mapset, int* map_fd, 
		char* seg_name, int* seg_fd, SEGMENT* seg, void *cell_buf, int fract, 
        RASTER_MAP_TYPE data_type);
	
void Segment_named_outfile (char* map_name, char* mapset, int* map_fd,
			           char* seg_name, int* seg_fd, SEGMENT* seg, int overwrite, 
                       int terse, int fract, RASTER_MAP_TYPE data_type);	
	
void Segment_tmpfile (char* seg_name, int* seg_fd, SEGMENT* seg, int fract, 
                 RASTER_MAP_TYPE data_type);
		 
void Close_segmented_tmpfile (char *seg_name, int seg_fd, SEGMENT *seg);

void Close_segmented_infile (int map_fd, char* seg_name, int seg_fd, SEGMENT* seg);

void Close_segmented_outfile (char* map_name, int map_fd,
			             char* seg_name, int seg_fd, SEGMENT* seg, 
                         CELL* cell_buf, int terse,
                         SEGMENT* elevation_seg, RASTER_MAP_TYPE data_type, int make_nulls);

#endif
