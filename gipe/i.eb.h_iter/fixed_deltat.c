#include<stdio.h>
#include<stdlib.h>
#include<math.h>

#define PI 3.14159265358979323846 

double fixed_deltat(double u2m, double roh_air,double cp,double dt,double disp,double z0m,double z0h,double tempk,int iteration){
	int i;
	double ublend;
	double length;
	double xm,xh;
	double psim, psih;
	double ustar;
	double rah;
	double h_in;
	double temp1;
	
	/* Failsafe all the Log10 */
	if(disp==100){
		disp=99.99999;
	}
	if(disp==2){
		disp=1.99999;
	}
	if(z0m==0.0){
		z0m=0.00001;
	}
	if(log10(2-disp)-log10(z0m)==0.0){
		//ublend=u2m*(log10(100-disp)-log10(z0m))/(log10(2-disp)-log10(z0m)+0.001);
		ublend=u2m*(log(100-disp)-log(z0m))/(log(2-disp)-log(z0m)+0.001);
	} else {
		ublend=u2m*(log(100-disp)-log(z0m))/(log(2-disp)-log(z0m));
		//ublend=u2m*(log10(100-disp)-log10(z0m))/(log10(2-disp)-log10(z0m));
	}
	psim=0.0;
	psih=0.0;

	for(i=0;i<iteration;i++){
		if((log10((100-disp)/z0m)-psim)==0.0){
			//ustar = 0.41*ublend/(log10((100-disp)/z0m)-psim+0.0001);
			ustar = 0.41*ublend/(log((100-disp)/z0m)-psim+0.0001);
		} else {
			//ustar = 0.41*ublend/(log10((100-disp)/z0m)-psim);
			ustar = 0.41*ublend/(log((100-disp)/z0m)-psim);
		}
		if(z0h==0.0){
			z0h=0.00001;
		}
		if(ustar==0.0){
			ustar=0.00001;
		}
		if(((2-disp)/z0h)-psih==0.0){
			//rah   = (log10((2-disp)/z0h)-psih+0.00001)/(0.41*ustar);
			rah   = (log((2-disp)/z0h)-psih+0.00001)/(0.41*ustar);
		} else {			
			//rah   = (log10((2-disp)/z0h)-psih)/(0.41*ustar);
			rah   = (log((2-disp)/z0h)-psih)/(0.41*ustar);
		}
		if(rah==0.0){
			rah=0.00001;
		}			
		h_in  = roh_air * cp * dt / rah;
		if(h_in==0.0){
			h_in=0.00001;
		}
		length= -roh_air*cp*pow(ustar,3)*tempk/(0.41*9.81*h_in);
		if(length==0.0){
			length=-0.00001;
		}
		xm    = pow(1.0-16.0*((100-disp)/length),0.25);
		xh    = pow(1.0-16.0*((2-disp)/length),0.25);
		if((1.0+xm)/2.0==0.0||(1+xm*xm)-2*atan(xm)+0.5*PI==0.0){
			//psim  = 2.0*log10((1.0+xm+0.00001)/2.0)+log10((1+xm*xm)-2*atan(xm)+0.5*PI+0.00001);
			psim  = 2.0*log((1.0+xm+0.00001)/2.0)+log((1+xm*xm)-2*atan(xm)+0.5*PI+0.00001);
		} else {
			//psim  = 2.0*log10((1.0+xm)/2.0)+log10((1+xm*xm)-2*atan(xm)+0.5*PI);
			psim  = 2.0*log((1.0+xm)/2.0)+log((1+xm*xm)-2*atan(xm)+0.5*PI);
		}
		if((1.0+xh*xh)/2.0==0.0){
			//psih  = 2.0*log10((1.0+xh*xh+0.00001)/2.0);
			psih  = 2.0*log((1.0+xh*xh+0.00001)/2.0);
		} else {
			//psih  = 2.0*log10((1.0+xh*xh)/2.0);
			psih  = 2.0*log((1.0+xh*xh)/2.0);
		}
	}

	return rah;
}
