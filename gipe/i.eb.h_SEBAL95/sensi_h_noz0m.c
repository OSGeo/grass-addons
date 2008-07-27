#include<stdio.h>
#include<math.h>
#include<stdlib.h>
#include "functions.h"

/* Arrays Declarations */
#define ITER_MAX 10

/* if dtair_desert < 0 then internal calculations */ 
/* if dtair0 < 0 then internal calculations */ 

double sensi_h_noz0m( int iteration, double tempk_water, double tempk_desert, double t0_dem, double tempk, double dtair0, double ndvi, double ndvi_max, double dem, double rnet_desert, double g0_desert, double t0_dem_desert, double u_hu, double hu, double dem_desert, double dtair_desert)
{
	/* Arrays Declarations */
	double dtair[ITER_MAX], roh_air[ITER_MAX], rah[ITER_MAX];
	double h[ITER_MAX];
	double ustar[ITER_MAX], zom[ITER_MAX];

	/* Declarations */
	int	i, j, ic, debug=0;
	double u_0, zom0;
	double h_desert, rah_desert, roh_air_desert;
	double psih, psim, psih_desert,psim_desert;
	double ustar_desert,ustar_desertold,zom_desert;
	double result;

	/* Fat-free junk food */
	if (iteration>ITER_MAX){
		iteration=ITER_MAX;
	}

	if(debug==1){
		printf("*****************************\n");
		printf("t0_dem = %5.3f\n",t0_dem);
		printf("ndvi = %5.3f ndvimax = %5.3f\n",ndvi,ndvi_max);
		printf("*****************************\n");
	}
	if(t0_dem<250.0)
		t0_dem=250.0;
// 	printf("*****************************dtair = %5.3f\n",dtair[0]);
	roh_air[0] 	= roh_air_0(tempk);
// 	printf("*****************************rohair=%5.3f\n",roh_air[0]);
	roh_air_desert 	= roh_air_0(tempk_desert);
// 	printf("**rohairdesert = %5.3f\n",roh_air_desert);
	zom0 		= zom_0(ndvi, ndvi_max);
// 	printf("*****************************zom = %5.3f\n",zom0);
	u_0 		= U_0(zom0, u_hu, hu);
// 	printf("*****************************u0\n");
	rah[0] 		= rah_0(zom0, u_hu, hu);
// 	printf("*****************************rah = %5.3f\n",rah[0]);
	if(dtair_desert < 0.0){
		h_desert= rnet_desert - g0_desert;
		zom_desert= 0.002;
		ustar_desert= u_star(t0_dem_desert,h_desert,u_0,roh_air_desert,zom_desert,u_hu,hu);
		psih_desert= psi_h(t0_dem_desert,h_desert,ustar_desert,roh_air_desert,hu);
		psim_desert= psi_m(t0_dem_desert,h_desert,ustar_desert,roh_air_desert,hu);
		rah_desert = rah1(zom_desert,psih_desert,psim_desert,ustar_desert);
// 		printf("*****************************rah_desert = %5.3f\n",rah_desert);
		dtair_desert = dt_air_desert(h_desert, roh_air_desert, rah_desert);
	}
	if(dtair0 < 0.0){
		dtair[0] = dt_air(t0_dem,tempk_water,tempk_desert,dtair_desert);
	} else {
		dtair[0] = dtair0;
	}
	h[0] 		= h_0(roh_air[0], rah[0], dtair[0]);
// 	printf("*****************************h\n");
	if(debug==1){
		printf("dtair[0]	= %5.3f K\n", dtair[0]);
		printf("roh_air[0] 	= %5.3f kg/m3\n", roh_air[0]);
		printf("roh_air_desert0 = %5.3f kg/m3\n", roh_air_desert);
		printf("zom_0 		= %5.3f\n", zom0);
		printf("u_0 		= %5.3f\n", u_0);
		printf("rah[0] 		= %5.3f s/m\n", rah[0]);
		printf("h[0] 		= %5.3f W/m2\n", h[0]);
	}

/*----------------------------------------------------------------*/
/*Main iteration loop of SEBAL*/
	zom[0] = zom0;
	for(ic=1;ic<iteration+1;ic++){
		if(debug==1){
			printf("\n ******** ITERATION %i *********\n",ic);
		}
		ustar[ic] = u_star(t0_dem,h[ic-1],u_0,roh_air[ic-1],zom[0],u_hu,hu);
		psih = psi_h(t0_dem,h[ic-1],ustar[ic],roh_air[ic-1],hu);
		psim = psi_m(t0_dem,h[ic-1],ustar[ic],roh_air[ic-1],hu);
		rah[ic] = rah1(zom0, psih, psim, ustar[ic]);	
		if(rah[ic]<0.0)
			rah[ic]=0.0;
		/* get desert point values from maps */
		roh_air_desert	= rohair(dem_desert,tempk_desert,dtair_desert);
		h_desert	= h1(roh_air_desert,rah_desert,dtair_desert);
		ustar_desertold = ustar_desert;
		ustar_desert	= u_star(t0_dem_desert,h_desert,ustar_desertold,roh_air_desert,zom_desert,u_hu,hu);
		psih_desert 	= psi_h(t0_dem_desert,h_desert,ustar_desertold,roh_air_desert,hu);
		psim_desert 	= psi_m(t0_dem_desert,h_desert,ustar_desert,roh_air_desert,hu);
		rah_desert	= rah1(zom_desert,psih_desert,psim_desert,ustar_desert);
		dtair_desert 	= dt_air_desert(h_desert, roh_air_desert, rah_desert);
		/* This should find the new dtair from inversed h equation...*/
		dtair[ic] 	= dt_air(t0_dem, tempk_water, tempk_desert, dtair_desert);
		/* This produces h[ic] and roh_air[ic+1] */
		roh_air[ic] 	= rohair(dem, tempk, dtair[ic]);
		h[ic] 		= h1(roh_air[ic], rah[ic], dtair[ic]);
		/* Output values of the iteration parameters */
		if(debug==1){
			printf("psih[%i] 	= %5.3f\n", ic, psih);
			printf("ustar[%i] 	= %5.3f\n", ic, ustar[ic]);
			printf("rah[%i] 	= %5.3f s/m\n",ic, rah[ic]);
			printf("h_desert 	= %5.3f\n", h_desert);
			printf("rohair_desert	= %5.3f\n", roh_air_desert);
			printf("psih_desert 	= %5.3f\tustar_desert = %5.3f\trah_desert = %5.3f\n", psih_desert, ustar_desert, rah_desert);
			printf("dtair_desert 	= %8.5f\n", dtair_desert);	
			printf("dtair[%i] 	= %5.3f K\n", ic, dtair[ic]);	
			printf("roh_air[%i] 	= %5.3f kg/m3\n", ic, roh_air[ic]);	
			printf("h[%i] 		= %5.3f W/m2\n",ic, h[ic]);
		}
	}
	return h[iteration];
}
 
