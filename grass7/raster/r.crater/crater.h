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

/* Kinetic Energy 1/2*m*v^2 (W in Melosh) */
double kinetic_energy(double Mi,double Vi);
/*Gault Scaling (Gault, 1974)*/
double Gault_Dat(double W, double r_proj, double r_targ, double theta, bool solid_rock);
/*Yield Scaling (Nordyke, 1962)*/
double Yield_Dat(double W, double r_proj, double r_targ, double L);
/*Pi-group Scaling (Schmidt and Holsapple, 1983)*/
double Pi_Dat(double W, double r_proj, double r_targ, double L, double g);
