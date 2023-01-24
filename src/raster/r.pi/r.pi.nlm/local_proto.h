#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <time.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/stats.h>
#include "../r.pi.library/r_pi.h"

typedef struct {
    int x, y;
} Point;

typedef struct {
    Point *list;
    int count;
} Point_List;

/* list_array */

extern Point_List *list_array;

/* list.c */
void list_init(int count, int rows, int cols);
int list_count(int patch);
Point *list_patch(int patch);
void list_add(int patch, int x, int y);
Point list_get(int patch, int pos);
void list_set(int patch, int pos, int x, int y);
void list_insert(int patch, int pos, int x, int y);
void list_remove(int patch, int pos);
void list_remove_range(int patch, int pos, int size);
int list_indexOf(int patch, int x, int y);
void list_shuffle(int patch);

/* func.c */
void FractalIter(double *map, double d, double dmod, int n, int size);
double DownSample(double *map, double min, int x, int y, int newcols,
                  int newrows, int oldsize);
double CutValues(double *map, double mapcover, int size);
double UpSample(int *map, int x, int y, int oldcols, int oldrows, int newsize);
void MinMax(double *map, double *min, double *max, int size);

#endif /* LOCAL_PROTO_H */
