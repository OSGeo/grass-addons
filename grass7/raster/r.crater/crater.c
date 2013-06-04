#include <stdio.h>
#include <math.h>
/*
 * Public Domain
 * Defining crater equations after chapter 7 of Melosh
 * Dat = Diameter Apparent Transient
 * r_proj = density projectile (impactor)
 * r_targ = density target
 * theta = impacting angle
 * Vi = impacting velocity
 * Mi = impactor mass
 * L = impactor diameter
 * solid_rock = boolean, is target made of solid rock?
*/

/* Convert density and diameter into mass of impactor (Mi) */
double mass_impactor(double r_proj, double L){
	double volume = (4/3.0)*PI*pow((L/2.0),3);
	return(r_proj*volume);
}

/* Kinetic Energy 1/2*m*v^2 (W in Melosh) */
double kinetic_energy(double Mi,double Vi){
	return 0.5*Mi*Vi*Vi;
}

/*Gault Scaling (Gault, 1974)*/
double Gault_Dat(double W, double r_proj, double r_targ, double theta, bool solid_rock){
	double Dat;
        if (solid_rock){
                /*for craters up to 10 m + solid target rock*/
                Dat=0.015*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(W,0.37)*pow(sin(theta),2/3.0);
                if (Dat > 10){
                        /*for craters up to 100 m + loose target rock or regolith*/
                        Dat=0.25*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(W,0.29)*pow(sin(theta),1/3.0);
		}
        } else {
                /*for craters up to 100 m + loose target rock or regolith*/
                Dat=0.25*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(W,0.29)*pow(sin(theta),1/3.0)
                if (Dat > 100){
                        /*for craters > 100m up to 1000 m + any kind of target material*/
                        Dat=0.27*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(W,0.28)*pow(sin(theta),1/3.0);
	}
        return(Dat);
}

/*Yield Scaling (Nordyke, 1962)*/
double Yield_Dat(double W, double r_proj, double r_targ, double L){
        return (0.0133*pow(W,1/3.4) + 1.51*pow(r_proj,1/2.0)*pow(r_targ,-1/2.0)*L);
}

/*Pi-group Scaling (Schmidt and Holsapple, 1983)*/
double Pi_Dat(double W, double r_proj, double r_targ, double L, double g){
        return (1.8*pow(r_proj,0.11)*pow(r_targ,-1/3.0)*pow(g,-0.22)*pow(L,0.13)*pow(W,0.22));
}

