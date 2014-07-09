#include<stdio.h>
#include<math.h>
#include <grass/gis.h>

#define PI 3.1415926
#define HARMONIC_MAX 50000


void fourier(DCELL *t_sim,DCELL *inrast,int length,int harmonic_number){
	int u, t, col;
	double t_obs[HARMONIC_MAX] = {0.0};
	for (col = 0; col < length; col++)
		t_obs[col] = (double) inrast[col];
	double fcos[HARMONIC_MAX] = {0.0};
	double fsin[HARMONIC_MAX] = {0.0};
	double fm[HARMONIC_MAX] = {0.0};
	double fp[HARMONIC_MAX] = {0.0};

	//Generate F[u], Fm[u] and Fp[u] for u=1 to q
	//u is spectral dimension
	//t is temporal dimension
	for (u=0;u<harmonic_number;u++){
		for (t=0;t<length;t++){
			fcos[u] = fcos[u]+t_obs[t]*cos(2*PI*u*t/length);
			fsin[u] = fsin[u]+t_obs[t]*sin(2*PI*u*t/length);
		}
		fcos[u]	= fcos[u]/length;
		fsin[u]	= fsin[u]/length;
		fm[u]	= pow(pow(fcos[u],2)+pow(fsin[u],2),0.5);
		fp[u]	= atan2(fcos[u],fsin[u]);
	}
	for (t=0;t<length;t++){
		for (u=0;u<harmonic_number;u++){
			t_sim[t] = t_sim[t]+fm[u]*(cos((2*PI*u*t/length)-fp[u])+sin((2*PI*u*t/length)+fp[u]));
		}
	}
}
