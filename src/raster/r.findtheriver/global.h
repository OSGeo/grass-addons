#ifndef _GLOBAL_H__
#define _GLOBAL_H__

#include <grass/raster.h>

#define THRESHOLD_DISTANCE 100

/* point_list.c */
typedef struct PointNode {
    int col;
    int row;
    struct PointNode *next;
} PointList_t;

PointList_t *create_list(int, int);
PointList_t *append_point(PointList_t *const, int, int);
void destroy_list(PointList_t *);
PointList_t *find_nearest_point(PointList_t *const, int, int);
void print_list(PointList_t *const, const char *const);

/* find_stream.c */
PointList_t *find_stream_pixels_in_window(int, char *, const char *,
                                          RASTER_MAP_TYPE, int, double, int,
                                          int, int, int);

#endif
