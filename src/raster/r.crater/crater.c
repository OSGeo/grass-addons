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

#define PI 3.1415927

/* Convert density and diameter into mass of impactor (Mi) */
double mass_impactor(double r_proj, double L){
	double volume = (4/3.0)*PI*pow((L/2.0),3);
	return(r_proj*volume);
}

/* Kinetic Energy 1/2*m*v^2 (W in Melosh) */
double kinetic_energy(double r_proj, double L, double Vi){
	double Mi = mass_impactor(r_proj,L);
	return 0.5*Mi*Vi*Vi;
}

/******************************************************************/
/* Forward mode equations                                         */
/******************************************************************/
/*Gault Scaling (Gault, 1974), equations 7.8.1a/b/c in Meloch*/
double Gault_Dat(double W, double r_proj, double r_targ, double theta, int target_type){
	double Dat;
        if (target_type==3){ /*Solid rock*/
                /*for craters up to 10 m + solid target rock*/
                Dat=0.015*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(W,0.37)*pow(sin(theta),2/3.0);
                if (Dat > 10){
                        /*for craters up to 100 m + loose target rock or regolith*/
                        Dat=0.25*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(W,0.29)*pow(sin(theta),1/3.0);
                	if (Dat > 100){
                        	/*for craters > 100 m up to 1000 m + any kind of target material*/
                        	Dat=0.27*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(W,0.28)*pow(sin(theta),1/3.0);
			}
		}
        } else {
                /*for craters up to 100 m + loose target rock or regolith*/
                Dat=0.25*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(W,0.29)*pow(sin(theta),1/3.0);
                if (Dat > 100){
                        /*for craters > 100 m up to 1000 m + any kind of target material*/
                        Dat=0.27*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(W,0.28)*pow(sin(theta),1/3.0);
		}
	}
        return(Dat);
}

/*Yield Scaling (Nordyke, 1962), equation 7.8.3 in Meloch*/
double Yield_Dat(double W, double r_proj, double r_targ, double L){
        return (0.0133*pow(W,1/3.4) + 1.51*pow(r_proj,1/2.0)*pow(r_targ,-1/2.0)*L);
}

/*Pi-group Scaling (Schmidt and Holsapple, 1983), equation 7.8.4 in Meloch*/
double Pi_Dat(double W, double r_proj, double r_targ, double L, double g){
        return (1.8*pow(r_proj,0.11)*pow(r_targ,-1/3.0)*pow(g,-0.22)*pow(L,0.13)*pow(W,0.22));
}

/******************************************************************/
/* Backward mode equations                                        */
/******************************************************************/
/*Gault Scaling (Gault, 1974), equations 7.8.1a/b/c in Meloch*/
double Gault_L(double Dat, double Vi, double r_proj, double r_targ, double theta, int target_type){
	double L;
        if (Dat >= 100){
                /*for craters > 100 m up to 1000 m + any kind of target material*/
                L=pow(Dat/(0.27*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(1/3.0*PI*Vi*Vi,0.28)*pow(1/2.0,3.28)*pow(sin(theta),1/3.0)),1/3.28);
	}

        if (target_type==3){ /*Solid rock*/
                if (Dat < 10){
                	/*for craters up to 10 m + solid target rock*/
                	L=pow(Dat/(0.015*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(1/3.0*PI*Vi*Vi,0.37)*pow(1/2.0,3.37)*pow(sin(theta),2/3.0)),1/3.37);
                } else {
                        /*for craters up to 100 m + loose target rock or regolith*/
                        L=pow(Dat/(0.25*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(1/3.0*PI*Vi*Vi,0.29)*pow(1/2.0,3.29)*pow(sin(theta),1/3.0)),1/3.29);
		}
        } else {
                if (Dat < 100){
                	/*for craters up to 100 m + loose target rock or regolith*/
                        L=pow(Dat/(0.25*pow(r_proj,1/6.0)*pow(r_targ,-1/2.0)*pow(1/3.0*PI*Vi*Vi,0.29)*pow(1/2.0,3.29)*pow(sin(theta),1/3.0)),1/3.29);
		}
	}
        return(L);
}
/*Yield Scaling (Nordyke, 1962), equation 7.8.3 in Meloch*/
double Yield_L(double Vi, double r_proj, double r_targ, double Dat){
        return pow(Dat/(0.0133*pow(1/3.0*PI*Vi*Vi,1/3.4)*pow(1/2.0,3/3.4)+1.51*pow(r_proj,1/2.0)*pow(r_targ,-1/2.0)),3.4/6.4);
}

/*Pi-group Scaling (Schmidt and Holsapple, 1983), equation 7.8.4 in Meloch*/
double Pi_L(double Vi, double r_proj, double r_targ, double Dat, double g){
        return pow(Dat/(1.8*pow(r_proj,0.11)*pow(r_targ,-1/3.0)*pow(g,-0.22)*pow(1/3.0*PI*Vi*Vi,0.22)*pow(1/2.0,0.66)),1/0.79);
}






