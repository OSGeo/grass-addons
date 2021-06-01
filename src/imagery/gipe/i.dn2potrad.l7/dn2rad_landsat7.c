#include<stdio.h>
#include<math.h>
#include<stdlib.h>

    /* Conversion of DN to Radiance for Landsat 7ETM+
     * http://ltpwww.gsfc.nasa.gov/IAS/handbook/handbook_htmls/chapter11/chapter11.html#section11.3 
     */ 
double dn2rad_landsat7(double Lmin, double LMax, double QCalMax,
			double QCalmin, int DN) 
{
    double result, gain, offset;

    gain = (LMax - Lmin) / (QCalMax - QCalmin);
    offset = Lmin;
    result = gain * ((double)DN - QCalmin) + offset;
    return result;
}


