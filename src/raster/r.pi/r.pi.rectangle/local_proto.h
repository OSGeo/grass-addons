#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <time.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/stats.h>
#include "../r.pi.library/r_pi.h"

/* buffer.c */
void set_buffer(CELL *buffer, int x, int y, int width, int height, int sx,
                int sy, int align);

#endif /* LOCAL_PROTO_H */
