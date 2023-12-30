#ifndef FUTURES_OUTPUT_H
#define FUTURES_OUTPUT_H

#include <grass/segment.h>
#include <stdbool.h>

char *name_for_step(const char *basename, const int step, const int nsteps);
void output_developed_step(SEGMENT *developed_segment, const char *name,
                           int year_from, int year_to, int nsteps,
                           bool undeveloped_as_null, bool developed_as_one);
#endif // FUTURES_OUTPUT_H
