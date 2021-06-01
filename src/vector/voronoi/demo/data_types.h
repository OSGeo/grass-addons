#include <stdlib.h>

#ifndef NULL
#define NULL   0
#endif
#define TRUE   1
#define FALSE  0

typedef enum {left, right} side;

typedef unsigned char boolean;

struct vertex {
    double x,y;
    struct edge *entry_pt;
};

struct edge {
    struct vertex *org;
    struct vertex *dest;
    struct edge *onext;
    struct edge *oprev;
    struct edge *dnext;
    struct edge *dprev;
};

extern struct vertex *sites;
