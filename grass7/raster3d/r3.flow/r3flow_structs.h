#ifndef R3FLOW_STRUCTS_H
#define R3FLOW_STRUCTS_H

#include <grass/raster3d.h>

struct Seed
{
    double x;
    double y;
    double z;
    int flowline;
    int flowaccum;
};

struct Integration
{
    int direction;
    char *unit;
    double step;
    double cell_size;
    int limit;
};

#endif // R3FLOW_STRUCTS_H
