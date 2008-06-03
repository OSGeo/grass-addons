#include<stdio.h>
#include<stdlib.h>
#include<math.h>


double ra_h(double disp,double z0h,double psih,double ustar){
	double rah;
	
	rah   = (log10((2-disp)/z0h)-psih)/(0.41*ustar);

	return rah;
}
