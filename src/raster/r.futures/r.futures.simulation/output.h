#ifndef FUTURES_OUTPUT_H
#define FUTURES_OUTPUT_H

#include <grass/raster.h>
#include <grass/segment.h>
#include <stdbool.h>

char *name_for_step(const char *basename, const int step, const int nsteps);
void output_developed_step(SEGMENT *developed_segment, const char *name,
                           int year_from, int year_to, int nsteps,
                           bool contains_abandoned);
void output_step(SEGMENT *output_segment, SEGMENT *developed_segment,
                 const char *name, RASTER_MAP_TYPE data_type);
#endif // FUTURES_OUTPUT_H
