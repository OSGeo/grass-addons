/* Point infiltration function based on Green-Ampt equation. The formulation
*  follows the approach proposed by Smith et al. (1993) to redistribute the
*  water profiles during and after the hiatus phase.

*  Written by Bahram Saghafian
*
*  The two profiles, if exist, are volume averaged to compute the average 
*  surface soil moisture.
*
*/

/*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

	      Description of Some of the Variables

teta_n = soil moisture equal to saturated content (tetae)
         after first ponding, and equal to the width of
	 the first infiltrated redistributing water profile
	 during hiatus period. It also represents the surface
	 moisture before first ponding, calculated based on
	 how far the first ponding time is, such that at that
	 ponding time the surface moisture must equal to
	 saturation moisture.

iter_i_less_k = an array set equal to current time iteration
		(itime) as long as rainfall intensity at the
		very early stages of storm is less than
		hydraulic conductivity at [row][col] cell.

@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*/




#include "all.h"

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/
void INF_REDIST(
int   yes_redist_vary,
int   vect,
double dt,
float *vinf,
int itime,
int   *iter_pond_1,
int   *iter_i_less_k,
float *teta_n,
float *vinf_n,
int   yes_w_surf_moist,
float *surf_moist,
int   yes_w_inf_rate,
float *frate,
int *no_wat_prof,
int   *iter_n,
float *K,float *H,float *P,float *M,float *LN,float *RS,
double *hov)
/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

{
double  smd,tetae,tetai;
double  dtet,delteta,delvinf,p1,p2,rinf;
double  d_inf_end_redist, d_inf_post_redist;
double  t_pond_1;

double  ln = 0.0L,tetar = 0.0L,i_eff_sat,i_hydcon;
double  eff_sat,t_hydcon,cap_pre;
double  cap;
double  beta=1., p=1.;
                                      /* The integer maps of soil parameters
					 are converted back to the original
					 real values.  */
tetae=P[vect];
tetai=M[vect];
smd=tetae-tetai;
delvinf=vinf[vect];
cap=H[vect];
if(yes_redist_vary) 
{
  ln=LN[vect];
  tetar=RS[vect];
}

                               /* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  
			       THE FOLLOWING CONDITION IS TRUE ONLY WHEN 
			       AT THE VERY BEGINNING OF THE RAINFALL, THE 
                               INTENSITY IS LESS THAN HYDRAULIC CONDUCTIVITY 
			       OF THIS CELL.  AS SUCH, NO WATER PROFILE IS 
			       DISTRIBUTED. ONLY CUMULATIVE DEPTH INCREASES. 
			       %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  */

if(iter_i_less_k[vect] == (itime-1) && ((*hov)/dt)<=K[vect]) {
   if(yes_w_inf_rate) frate[vect]=(*hov)/dt;
   vinf[vect]=vinf[vect] + (*hov);
   (*hov)=0;
   iter_i_less_k[vect] = itime;
   if(yes_w_surf_moist) surf_moist[vect]=tetai;

   return;
   }
   
                               /* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
                               THE FOLLOWING CONDITION IS SATISFIED WHEN 
			       RAINFALL INTENSITY DROPS BELOW HYDRAULIC 
			       CONDUCTIVITY; THEN THE WATER PROFILE IS 
			       REDISTRIBUTED. THE VARIABLE no_wat_prof IS 
			       ZERO BY DEFALUT; ONE IF ONLY ONE PROFILE HAS 
			       EMERGED WHEN THE DEPTH OF THE SECOND PROFILE 
			       IN THE POST-HIATUS HAS EXCEEDED THAT OF THE 
			       FIRST PROFILE; AND TWO IF THERE IS STILL TWO 
			       PROFILES AFTER THE PREVIOUS POST-HIATUS. IN 
			       LAST CASE, THE TWO WOULD BE MERGED ACCORDING 
			       TO THEIR FIRST MOMENT ABOUT TETAI. 

                                 Soil Water Redistribution During Hiatus 
                               %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% */

if( ((*hov)/dt)<K[vect] ) {
   if(no_wat_prof[vect] == 1) {
      teta_n[vect]=tetae;
      no_wat_prof[vect] = 0;
      }

   if(no_wat_prof[vect] == 2) {
      teta_n[vect]=tetai + (vinf_n[vect]*(teta_n[vect]-tetai) + 
		       (vinf[vect]-vinf_n[vect])*
		       (tetae+teta_n[vect]-2.*tetai))/vinf[vect];
      no_wat_prof[vect] = 0;
      }

   delteta=teta_n[vect] - tetai;
   vinf[vect]=vinf[vect] + (*hov);
   vinf_n[vect]=vinf[vect];
   if(yes_w_inf_rate) frate[vect]=(*hov)/dt;
   if(teta_n[vect]==tetai) {
      iter_n[vect]=itime;
      if(yes_w_surf_moist) surf_moist[vect]=teta_n[vect];
      (*hov)=0;
      return;
   }

   if(!yes_redist_vary) {
     teta_n[vect]=teta_n[vect] + delteta*( (*hov)/dt - K[vect] -
		      K[vect]*H[vect]*delteta/vinf_n[vect])*dt/vinf_n[vect];  
   }
   else {
							  
      i_eff_sat=(tetai-tetar)/(tetae-tetar);
      i_hydcon=K[vect]*pow((double)i_eff_sat,(double)(3.+2./ln));
      eff_sat=(teta_n[vect] - tetar)/(tetae-tetar);
      t_hydcon=K[vect]*pow((double)eff_sat,(double)(3.+2./ln));
      cap_pre=H[vect]*(pow((double)eff_sat,(double)(3.+1./ln)) - 
	      pow((double)i_eff_sat,(double)(3.+1./ln)))/
	      (1.-pow((double)i_eff_sat,(double)(3.+1./ln)));

      teta_n[vect]=teta_n[vect] + delteta*( (*hov)/dt - 
		       i_hydcon - t_hydcon - beta*p*K[vect]*cap_pre*delteta/
		       vinf_n[vect])*dt/vinf_n[vect];  
      if(teta_n[vect]<tetai) teta_n[vect]=tetai;
   }

   iter_n[vect]=itime;
   if(yes_w_surf_moist) surf_moist[vect]=teta_n[vect];
   (*hov)=0;
   return;
   }

                                    /* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                                    THE FOLLOWING CONDITION IS SATISFIED WHEN 
				    RAINFALL INTENSITY IS GREATER THAN
                                    HYDRAULIC CONDUCTIVITY IN POSTHIATUS 
				    PERIOD. THE REDISTRIBUTION OF FIRST 
				    PROFILE CONTINUES UNTIL AND IF THE TWO 
				    PROFILES JOIN.
                                    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  */


if(iter_n[vect] > 0 && no_wat_prof[vect] != 1) 
{
   dtet=tetae-teta_n[vect];
   if(dtet<1e-20) dtet=1e-20;
   d_inf_post_redist=(vinf[vect]-vinf_n[vect])/dtet;
   d_inf_end_redist= vinf_n[vect] / (teta_n[vect] -  tetai);
   no_wat_prof[vect]=1;

   if(d_inf_post_redist < d_inf_end_redist) {
      no_wat_prof[vect]=2;
      delteta=teta_n[vect] - tetai;
      if(!yes_redist_vary) {
         teta_n[vect]=teta_n[vect] + delteta*
		       ( -1.0*K[vect] - K[vect]*H[vect]*delteta/vinf_n[vect])*
		       dt/vinf_n[vect];  
      }
      else {
	 i_eff_sat=(tetai-tetar)/(tetae-tetar);
	 i_hydcon=K[vect]*pow((double)i_eff_sat,(double)(3.+2./ln));
	 eff_sat=(teta_n[vect] - tetar)/(tetae-tetar);
	 t_hydcon=K[vect]*pow((double)eff_sat,(double)(3.+2./ln));
	 cap_pre=H[vect]*(pow((double)eff_sat,(double)(3.+1./ln)) - 
		 pow((double)i_eff_sat,(double)(3.+1./ln)))/
		 (1.-pow((double)i_eff_sat,(double)(3.+1./ln)));
         teta_n[vect]=teta_n[vect] + delteta*( 
	     -1.0*i_hydcon - t_hydcon - beta*p*K[vect]*cap_pre*delteta/
	     vinf_n[vect])*dt/vinf_n[vect];
         if(teta_n[vect]<tetai) teta_n[vect]=tetai;
      }
      smd=tetae-teta_n[vect];
      delvinf=vinf[vect]-vinf_n[vect];
      cap=H[vect]*pow((double)(d_inf_post_redist/d_inf_end_redist),(double)1.5);
   }
}

p1=K[vect]*dt-2.*delvinf;
p2=K[vect]*(delvinf + cap*smd);
rinf=(p1+sqrt((double)(p1*p1+8.*p2*dt)))/(2.*dt);
if(yes_w_inf_rate) frate[vect]=rinf;

if(((*hov)/dt)<=rinf) 
{
  rinf=(*hov)/dt;
  if(yes_w_inf_rate) frate[vect]=rinf;

			       /* Do the following ONLY before the very first 
			       ponding, and NOT after any redistribution
			       has occured. I'm still thinking how to 
			       distribute the second water profile formed
			       following a hiatus stage and before ponding 
			       , if any.    */
			       
  if(iter_pond_1[vect] == 0 && iter_n[vect]==0) 
  { 
     t_pond_1=K[vect]*H[vect]*(tetae-teta_n[vect])/(rinf*(rinf-K[vect]));
     teta_n[vect] = teta_n[vect] + (tetae-teta_n[vect])*dt/t_pond_1;
     if(teta_n[vect] > tetae) 
     {
	teta_n[vect]=tetae;
	iter_pond_1[vect]=itime;
     }
  }

  (*hov)=0.;
}
else 
{
  (*hov)=(*hov)-rinf*dt;
		                 /* This is true first ponding iteration 
				  * and doesn't change.           
				  */

  if(iter_pond_1[vect] == 0) 
  {
     iter_pond_1[vect]=itime;
     if(iter_n[vect]==0) teta_n[vect]=tetae;
  }
}

vinf[vect]=vinf[vect]+rinf*dt;

if(no_wat_prof[vect] == 1) teta_n[vect]=tetae;
if(yes_w_surf_moist) 
{
     if(no_wat_prof[vect]==0||no_wat_prof[vect]==1)
        surf_moist[vect]=teta_n[vect];
     if(no_wat_prof[vect]==2) 
     {
        surf_moist[vect]=tetai +
	(vinf_n[vect]*(teta_n[vect]-tetai) +
	(vinf[vect]-vinf_n[vect])*
	(tetae+teta_n[vect]-2.*tetai))/vinf[vect];
	if(surf_moist[vect] > tetae) surf_moist[vect]=tetae;
     }
                            /* This computes the soil moisture at the surface
			     * based on volume weighted average of two profiles.
			     */
}


}
