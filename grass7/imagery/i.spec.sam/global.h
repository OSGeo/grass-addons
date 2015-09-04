#ifndef __GLOBAL_H__
#define __GLOBAL_H__

#include <grass/config.h>
#include <grass/gis.h>
#include <grass/gmath.h>

#ifndef GLOBAL
#define GLOBAL extern
#endif

#define MAXFILES 255

extern MAT *A;
extern VEC *b, *Avector;
extern int matrixsize;
extern float curr_angle;

extern char *group;
extern struct Ref Ref;

extern CELL **cell;
extern int *cellfd;

extern CELL **result_cell;
extern int *resultfd;

extern CELL **error_cell;
extern int  error_fd;

extern char result_name[80];
extern char *result_prefix, *matrixfile;

