/*
INFORMATION FROM THE ORIGINAL FORTRAN CODE
//program crater
//Short program to evaluate the scaling equations to determine
//the diameter of a transient crater given details on the nature
//of the projectile, conditions of impact, and state of the
//target.  The diameter is evaluated by three independent methods,
//yield scaling, pi-scaling and Gault's semi-empirical relations
//supplemented by rules on how crater size depends on gravity and
//angle of impact.
//Updated Nov. 1997 to compute projectile size from a given
//transient crater diameter.  Projectile and crater diameter
//computation functions merged into a single program April 1998.
//See Melosh, Impact Cratering, chapter 7 for more details
//Updated Oct. 1999 to take final crater diameters as well as 
//transient crater diameters into account.
//Copyright 1996, 1997 and 1998 by H. J. Melosh
The original code was translated to Python @EGU2013 (20130410),
then to C version @TRENTO GRASS meeting (20130414),
into GRASS GIS @TRENTO GRASS meeting (20130416).
Public domain - Yann Chemin
*/

#include<stdio.h>
#include<stdlib.h>
#include<math.h>

int crater(double v, double theta, double rhotarget, double g, int targtype, double rhoproj, double L, double Dt, double Dfinal, int scaling_law, int return_time, int comptype){
	double pi=3.1415926535897932384626433;
	double third=1./3.;
	/*constants for the Schmidt-Holsapple pi scaling & gravity conversion factors*/
	double Cd[3]={1.88,1.54,1.6};
	double beta[3]={0.22,0.165,0.22};
	double gearth=9.8;
	double gmoon=1.67;
	double rhomoon=2700.;
	double Dstarmoon=1.8*pow(10,4);
	double Dprmoon=1.4*pow(10,5);
	//convert units to SI and compute some auxiliary quantites
	v=1000.*v;					/*km/sec to m/sec*/
	theta=theta*(pi/180.);				/*degrees to radians*/
	double anglefac=pow((sin(theta)),third);	/*impact angle factor*/
	double densfac=pow(rhoproj,0.16667)/sqrt(rhotarget);
	double pifac=(1.61*g)/(v*v);			/*inverse froude length factor*/
	double Ct=0.80;					/*coefficient for formation time*/
	if(targtype == 1){
		Ct=1.3;
	}
	double Dstar=(gmoon*rhomoon*Dstarmoon)/(g*rhotarget);	/*transition crater diameter*/
	double Dpr  =(gmoon*rhomoon*Dprmoon  )/(g*rhotarget);	/*peak-ring crater diameter*/
	double Dstd, Lpiscale, Lyield, Lgault; /*Default mode*/

	/***************************************************/
	/*    computation for specified projectile diameter*/
	/***************************************************/
	double m, W, pitwo, dscale, Dpiscale, Dyield, gsmall, Dgault, Tform, Dsimple, size;
	char *cratertype;
	if(comptype == 1){
		m=(pi/6.)*rhoproj*pow(L,3);		/*projectile mass*/
		W=0.5*m*v*v;				/*projectile kinetic energy*/
		pitwo=pifac*L;				/*inverse froude number*/
		dscale=pow((m/rhotarget),third);	/*scale for crater diameter*/
		if(scaling_law==0){
			//Pi Scaling (Schmidt and Holsapple 1987)
			Dpiscale=dscale*Cd[targtype-1]*pow(pitwo,(-beta[targtype-1]));
			Dpiscale=Dpiscale*anglefac;
			size=Dpiscale;
		} else if(scaling_law==2){
			//Yield Scaling (Nordyke 1962) with small correction for depth of projectile penetration
			Dyield=0.0133*pow(W,(1/3.4))+1.51*sqrt(rhoproj/rhotarget)*L;
			Dyield=Dyield*anglefac*pow((gearth/g),0.165);
			size=Dyield;
		} else {
			//Gault (1974) Semi-Empirical scaling
			gsmall=0.25*densfac*pow(W,0.29)*anglefac;
			if(targtype == 3){
				gsmall=0.015*densfac*pow(W,0.37)*pow(anglefac,2);
			}
			if(gsmall < 100.){
				Dgault=gsmall;
			}else{
				Dgault=0.27*densfac*pow(W,0.28)*anglefac;
			}
			Dgault=Dgault*pow((gmoon/g),0.165);
			size=Dgault;
		}
		if(return_time){
			/*Compute crater formation time from Schmidt and Housen*/
			Tform=(Ct*L/v)*pow(pitwo,-0.61);
		}
		/*Compute final crater type and diameter from pi-scaled transient dia.*/
		Dsimple=1.56*Dpiscale;
		/* TODO: Return category */
		if (Dsimple < Dstar){
			Dfinal=Dsimple;
			cratertype="Simple";
		}else{
			Dfinal=pow(Dsimple,1.18)/pow(Dstar,0.18);
			cratertype="Complex";
		}
		if((Dsimple < Dstar*1.4) && (Dsimple > Dstar*0.71)){
			cratertype="Simple/Complex";
		}
		if(Dfinal > Dpr){
			cratertype="Peak-ring";
		}
		
		/*Print out results*/
// 		printf("Three scaling laws yield the following *transient*', crater diameters:\n");
// 		printf("(note that diameters are measured at the pre-impact surface.\n");
// 		printf("Rim-to-rim diameters are about 1.25X larger!)\n");
// 		printf("Yield Scaling                       Dyield   =%f m\n", Dyield);
// 		printf("Pi Scaling    (Preferred method!)   Dpiscale =%f m\n", Dpiscale);
// 		printf("Gault Scaling                       Dgault   =%f m\n", Dgault);
// 		printf("Crater Formation Time               Tform    =%f sec\n", Tform);
// 		printf("Using the Pi-scaled transient crater, the *final* crater has\n");
// 		printf("rim-to-rim diameter =%f km, and is of type %s\n",Dfinal/1000.,cratertype);
	}
	/***************************************************************/
	/* Default Mode: Estimate projectile size from crater diameter */
	/***************************************************************/
	else{
		/*convert input crater rim-to-rim diameter to transient crater diameter*/
		if(Dt == 0.){
			if(Dfinal < Dstar){
				Dt=0.64*Dfinal;
			}else{
				Dt=0.64*pow((Dfinal*pow(Dstar,0.18)),0.8475);
			}
		dscale=pow(((6.*rhotarget)/(pi*rhoproj)),third);
		}
		if(scaling_law==0){
			/*Pi Scaling (Schmidt and Holsapple 1987)*/
			Dstd=Dt/anglefac;
			Lpiscale=(Dstd*dscale*pow(pifac,beta[targtype-1]))/Cd[targtype-1];
			Lpiscale=pow(Lpiscale,(1./(1.-beta[targtype-1])));
			size=Lpiscale;
		} else if(scaling_law==2){
			/*Yield Scaling (Nordyke 1962) without correction for projectile penetration depth.*/
			Dstd=(Dt*pow((g/gearth),0.165))/anglefac;
			W=pow((Dstd/0.0133),3.4);
			Lyield=pow(((12.*W)/(pi*rhoproj*v*v)),third);
			size=Lyield;
		} else {
			/*Gault (1974) Semi-Empirical scaling*/
			Dstd=Dt*pow((g/gmoon),0.165);
			if((Dstd <= 10.) && (targtype == 3)){
				W=pow(((Dstd/0.015)/(densfac*pow(anglefac,2))),2.70);
			}else if(Dstd < 300.){
				W=pow(((Dstd/0.25)/(densfac*anglefac)),3.45);
			}else{
				W=pow(((Dstd/0.27)/(densfac*anglefac)),3.57);
			}
			Lgault=pow(((12.*W)/(pi*rhoproj*pow(v,2))),third);
			size=Lgault;
		}
		if(return_time){
			/*Compute crater formation time for Pi-scaled diameter*/
			Tform=(Ct*Lpiscale/v)*pow((pifac*Lpiscale),-0.61);
		}
		/*Print out results*/
// 		printf("Three scaling laws yield the following projectile diameters:\n");
// 		printf("(note that diameters assume a spherical projectile)\n");
// 		printf("Yield Scaling                       Lyield   =%f m\n",Lyield);
// 		printf("Pi Scaling    (Preferred method!)   Lpiscale =%f m\n",Lpiscale);
// 		printf("Gault Scaling                       Lgault   =%f m\n",Lgault);
// 		printf("Crater Formation Time               Tform    =%f sec\n",Tform);
	}
	if(return_time) return (Tform);
	else return (size);
}
