
#include "all.h"

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/
double CH_DEPTH(
int    link,int node,FILE *discharge_fd,
double dt,
double z,double depth,double wid,double qtoch,
float  *hch,double *dhch)
/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

{

double topw,dummy;


if(z>1e-10) 
{
   if(hch[node+link*NODES]>depth) 
   {
      /* *dhch=(dqch[node+link*NODES]*dt+h[vect]*w*w)/
               (w*(wid+2.*z*depth));  */

      *dhch=qtoch*dt/(w*(wid+2.*z*depth));
      hch[node+link*NODES]=hch[node+link*NODES]+(*dhch);
      if(hch[node+link*NODES]<depth) 
      {
		   /* When falling below bank */

         topw=2.*z*hch[node+link*NODES]+wid;
         dummy=topw*topw+4.*z*z*(depth-hch[node+link*NODES])
		      *(depth-hch[node+link*NODES]);
         *dhch=(-1.0*topw + sqrt(dummy))/(2.*z); 
      }

   }
   else 
   {
      topw=2.*z*hch[node+link*NODES]+wid;

      /* dummy=topw*topw+4.*z*
		(dqch[node+link*NODES]*dt+h[vect]*w*w)/w; */

         dummy=topw*topw+4.*z*qtoch*dt/w;
         if(dummy<0) {
	    fprintf(discharge_fd, "Reduce the time step. Crashed at link=%d  and node=%d  .\n",link,node);
	    fprintf(stderr, "Reduce the time step. Crashed at link=%d  and node=%d  .\n",link,node);
	    exit(1);
         }
	 *dhch=(-1.0*topw + sqrt(dummy))/(2.*z);
         hch[node+link*NODES]=hch[node+link*NODES]+(*dhch);
	 if(hch[node+link*NODES]>depth)
	 {
				      /* When going overbank */

            *dhch=((hch[node+link*NODES]-depth)*(wid+
	               z*hch[node+link*NODES]+z*depth)/(wid+2.*z*depth))
	               -(hch[node+link*NODES]-depth); 
         }
     }
}
else 
{
			   /* Rectangular cross section */
            /* *dhch=(dqch[node+link*NODES]*dt+h[vect]*w*w)/(w*wid); */
	    *dhch=qtoch*dt/(w*wid);
}

return 0;
}

