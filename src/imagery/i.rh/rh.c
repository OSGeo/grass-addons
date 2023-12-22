#include <stdio.h>
#include <math.h>

double esat(double tamean)
{
    /*
    esat{ saturated vapour pressure
    tamean{ air temperature daily mean
    */
    return (0.61078 * exp(17.2694 * tamean / (tamean + 237.3)));
}

double eact(double esat, double rh)
{
    /*
    eact{ actual vapour pressure
    esat{ saturated vapour pressure
    rh{ relative humidity
    */
    return (0.01 * esat * rh);
}

double eatm(double eact)
{
    /*
    eatm: atmospheric emissivity
    eact: actual vapour pressure
    */
    return (1.34 - 0.14 * sqrt(eact));
}

double rh(double PW, double Pa, double Ta, double dem)
{
    /*
    https{//www.researchgate.net/publication/227247013_High-resolution_Surface_Relative_Humidity_Computation_Using_MODIS_Image_in_Peninsular_Malaysia/
    PW <- MOD05_L2 product [mm]
    Pa <- MOD07 product [kPa]
    Pa <- 1013.3-0.1038*dem [kPa]
    Ta <- MOD07 product [Celsius]
    Ta <- -0.0065*dem+TaMOD07 (if dem>400m) [Celsius]

    https{//ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD05_L2/
    https{//ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD07_L2/
    */
    /*Specific Humidity*/
    double q = 0.001 * (-0.0762 * PW * PW + 1.753 * PW + 12.405);
    double ta = -0.0065 * dem + Ta;
    double a = 17.2694 * ta / (ta + 237.3);
    return (2.63224 * q * Pa / exp(a));
}
