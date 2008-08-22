#include<stdio.h>
#include<math.h>
#include<stdlib.h>

    /* Xie, X.Q., 1991: Estimation of daily evapo-transpiration (ET) 
     * from one time-of-day remotely sensed canopy temperature. 
     * Remote Sensing of Environment China, 6, pp.253-259.
     */ 
    
#define PI 3.1415927
double daily_et(double et_instantaneous, double time,
		 double sunshine_hours) 
{
    double n_e, result;

    
	/*Daily ET hours */ 
	n_e = sunshine_hours - 2.0;
    result = et_instantaneous * (2 * n_e) / (PI * sin(PI * time / n_e));
    return result;
}


