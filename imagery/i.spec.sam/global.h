#include <math.h>
#include <grass/imagery.h>
#include "matrix.h"

#ifndef GLOBAL
#define GLOBAL extern
#endif

#define MAXFILES 255

GLOBAL MAT *A;
GLOBAL VEC *b, *Avector;
GLOBAL int matrixsize;
GLOBAL float curr_angle;

GLOBAL char *group;
GLOBAL struct Ref Ref;

GLOBAL CELL **cell;
GLOBAL int *cellfd;

GLOBAL CELL **result_cell;
GLOBAL int *resultfd;

GLOBAL CELL **error_cell;
GLOBAL int  error_fd;

GLOBAL char result_name[80];
GLOBAL char *result_prefix, *matrixfile;

GLOBAL struct
    {
     struct Flag *quiet;
    } flag;
                
