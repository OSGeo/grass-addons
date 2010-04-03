#include "all.h"

/*******************************************************************/
 void 
spill (


/*     
 *    GIVEN ARRAYS OF Q(T) FOR ALL FIRST ORDER STREAMS, THIS SUBROUTINE
 *    LINEARLY INTERPOLATES Q(T) VALUES FOR INTERMEDIATE TIMES.
 */
    double t,
    float *qus,
    int j,
    double spilwidth,
    double spilcoef,
    double spilelev,
    double qmin,
    int *depend,
    int lakenum,
    int *numqpipe,
    float *strick,
    float *bottom,
    int yes_drain
)

   {
   double delty,wconst,qspil;
   double lakewse;
   int    ii;
     
   if(yes_drain) 
     {
     *qus=qmin;
     return;
     }

   lakewse=lake_el[lake_cat[con_vect[1+depend[j+1*LINKS]*NODES]]];
   delty=lakewse-spilelev;
   if(delty>0.0)
      {
      wconst=sqrt(2.0*9.81)*sqrt(1./3.)*2./3.;
      qspil=spilcoef*spilwidth*wconst*pow((double)delty,(double)1.5);
      *qus=qmin+(float)qspil;
      }
   else
      {
      *qus=qmin;
      } 

   if(numqpipe[lakenum]!=0)
      {
      for(ii=1; ii<=numqpipe[lakenum]; ii++)
         {

         if(strick[ii+1+lakenum*NODES]<lakewse)
	   {
	   if(ii!=numqpipe[lakenum]) continue;
	   qspil=bottom[ii+1+lakenum*NODES];
	   *qus=*qus+qspil;
	   return;
	   }

	 if(ii==1)
	   {
	   qspil=0;
	   }
         else
	   {
	   qspil=bottom[ii+lakenum*NODES]+(bottom[ii+1+lakenum*NODES]-
	       bottom[ii+lakenum*NODES])*
	       (lakewse-strick[ii+lakenum*NODES])/
	       (strick[ii+1+lakenum*NODES]-strick[ii+lakenum*NODES]);
            }
         *qus=*qus+qspil;
	 return;
         }
       }

     return;
   }
