#ifndef __GLOBAL_H__
#define __GLOBAL_H__
#endif

#include <grass/config.h>
#include <grass/gis.h>
#include <grass/gmath.h>
#include <grass/la.h>

#ifndef GLOBAL
#define GLOBAL extern
#endif

#define MAXFILES 255

extern vec_struct *b, *Avector;
extern int signature;
extern int signaturecount;
extern int spectralcount;
extern float curr_angle;

extern char *group;
extern struct Ref Ref;

extern DCELL **cell;
extern int *cellfd;

extern DCELL **result_cell;
extern int *resultfd;

extern DCELL **error_cell;
extern int error_fd;

extern char result_name[80];
extern char *result_prefix;
