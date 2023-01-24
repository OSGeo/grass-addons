#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/stats.h>
#include "../r.pi.library/r_pi.h"
#include <math.h>
#include <time.h>

typedef struct {
    int x, y;
} Point;

typedef struct {
    Point *list;
    int count;
} Point_List;

/* list_array */

extern Point_List *list_array;

void list_init(int count, int rows, int cols);
int list_count(int patch);
Point *list_patch(int patch);
void list_add(int patch, int x, int y);
Point list_get(int patch, int pos);
void list_set(int patch, int pos, int x, int y);
void list_insert(int patch, int pos, int x, int y);
void list_remove(int patch, int pos);
int list_indexOf(int patch, int x, int y);

#endif /* LOCAL_PROTO_H */
