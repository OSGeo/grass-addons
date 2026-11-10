#ifndef FUTURES_DEVPRESSURE_H
#define FUTURES_DEVPRESSURE_H

#include <grass/segment.h>

#include "inputs.h"

enum development_pressure { OCCURRENCE, GRAVITY, KERNEL };

struct DevPressure {
    float scaling_factor;
    float gamma;
    int neighborhood;
    float **matrix;
    enum development_pressure alg;
};

void update_development_pressure(int row, int col, struct Segments *segments,
                                 struct DevPressure *devpressure_info);
void update_development_pressure_precomputed(
    int row, int col, struct Segments *segments,
    struct DevPressure *devpressure_info);
void initialize_devpressure_matrix(struct DevPressure *devpressure_info);

#endif // FUTURES_DEVPRESSURE_H
