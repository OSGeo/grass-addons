#ifndef __GLOBAL_H__
#define __GLOBAL_H__

#include <grass/config.h>
#include <grass/gis.h>
#include <grass/gmath.h>
#include <grass/la.h>

#ifndef GLOBAL
#define GLOBAL extern
#endif


GLOBAL struct Ref Ref;

GLOBAL CELL **cell;
GLOBAL int *cellfd;

GLOBAL CELL **result_cell;
GLOBAL int *resultfd;

GLOBAL CELL *error_cell;
GLOBAL int error_fd;

GLOBAL CELL *iter_cell;
GLOBAL int iter_fd;


GLOBAL float spectral_angle(vec_struct *, vec_struct *);
GLOBAL int do_histogram(char *, char *);
GLOBAL void make_history(char *, char *, char *);
GLOBAL int open_files(char *, char *, char *, char *, mat_struct * A);

#endif /* __GLOBAL_H__ */
