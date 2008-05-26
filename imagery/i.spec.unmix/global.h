#include <math.h>
#include <grass/imagery.h>
#include <grass/la.h> /* LAPACK/BLAS */

#ifndef GLOBAL
#define GLOBAL extern
#endif

#define MAXFILES 255

GLOBAL mat_struct *A, *A_tilde_trans;
GLOBAL vec_struct *Avector1, *Avector2, *b, *fraction;
GLOBAL int matrixsize;
GLOBAL double svd_error;
GLOBAL float curr_angle;

GLOBAL char *group;
GLOBAL struct Ref Ref;

GLOBAL CELL **cell;
GLOBAL int *cellfd;

GLOBAL CELL **result_cell;
GLOBAL int *resultfd;

GLOBAL CELL *error_cell;
GLOBAL int  error_fd;

GLOBAL CELL *iter_cell;
GLOBAL int  iter_fd;

GLOBAL char result_name[80];
GLOBAL char *result_prefix, *matrixfile, *error_name, *iter_name;

GLOBAL struct
    {
     struct Flag *quiet;
    } flag;
                
GLOBAL struct
    {
     struct Flag *veryquiet;
    } flag2;
