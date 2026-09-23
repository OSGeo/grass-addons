#ifndef FUTURES_RANDOM_H
#define FUTURES_RANDOM_H

#include <stdbool.h>

struct GaussGenerator {
    double spare;
    bool has_spare;
    double mean;
    double std_dev;
};

void gauss_xy(double mean, double std_dev, double *x, double *y);
void gauss_generator_init(struct GaussGenerator *generator, double mean,
                          double std_dev);
double gauss_generator_next(struct GaussGenerator *generator);

#endif // FUTURES_RANDOM_H
