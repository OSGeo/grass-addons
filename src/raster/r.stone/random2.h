/*
 * Data structure required by the Marsaglia random number generator
 */
#pragma once // TODO: check if this is the correct include guard for GRASS

typedef struct {
    float u[98];
    float c;
    float cd;
    float cm;
    int ui;
    int uj;
    unsigned long randMax;
} UniSave;

void Init_RNG(UniSave *uniData, unsigned int seed);

double Uniform(UniSave *uniData, double mean, double std_devn);

double Gaussian(UniSave *uniData, double mean, double std_devn);

double Cauchy(UniSave *uniData, double mean, double half_width);

double SimpleUniform(UniSave *uniData, double min, double max);
