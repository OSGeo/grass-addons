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
double mass_impactor(double r_proj, double L);
/* Kinetic Energy 1/2*m*v^2 (W in Melosh) */
double kinetic_energy(double r_proj, double L, double Vi);

/******************************************************************/
/* Forward mode equations                                         */
/******************************************************************/
/*Gault Scaling (Gault, 1974)*/
double Gault_Dat(double W, double r_proj, double r_targ, double theta,
                 int target_type);
/*Yield Scaling (Nordyke, 1962)*/
double Yield_Dat(double W, double r_proj, double r_targ, double L);
/*Pi-group Scaling (Schmidt and Holsapple, 1983)*/
double Pi_Dat(double W, double r_proj, double r_targ, double L, double g);

/******************************************************************/
/* Backward mode equations                                        */
/******************************************************************/
/*Gault Scaling (Gault, 1974), equations 7.8.1a/b/c in Meloch*/
double Gault_L(double Dat, double Vi, double r_proj, double r_targ,
               double theta, int target_type);
/*Yield Scaling (Nordyke, 1962), equation 7.8.3 in Meloch*/
double Yield_L(double Vi, double r_proj, double r_targ, double Dat);
/*Pi-group Scaling (Schmidt and Holsapple, 1983), equation 7.8.4 in Meloch*/
double Pi_L(double Vi, double r_proj, double r_targ, double Dat, double g);
