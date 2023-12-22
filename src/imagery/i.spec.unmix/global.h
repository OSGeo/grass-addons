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
GLOBAL int do_histogram(const char *, const char *);
GLOBAL void make_history(char *, char *, char *);
GLOBAL mat_struct *open_files(char *matrixfile, char *img_grp,
                              char *result_prefix, char *iter_name,
                              char *error_name);

#endif /* __GLOBAL_H__ */
