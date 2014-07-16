#ifndef R3FLOW_STRUCTS_H
#define R3FLOW_STRUCTS_H

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

struct Array
{
    double *array;
    int sx;
    int sy;
    int sz;
};

#define ACCESS(arr, x, y, z) ((arr)->array[(arr)->sx * (arr)->sy * (z) + (arr)->sx * (y) + (x)])

#endif // R3FLOW_STRUCTS_H
