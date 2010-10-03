#include "all.h"

void 
weir_coeff (

/********************************************************************

This subroutine evaluates the Preissman coefficients for flow over a
rectangular weir.  The code considers flooded and reverse-flow cases.
Upgraded by F.L. Ogden 11-21-94 at UCONN.
*********************************************************************/
    int i,
    int j,
    float *alpha,
    float *ww,
    float *beta,
    float *bel,
    float *y,
    float *q,
    float *a,
    float *b,
    float *c,
    float *d,
    float *g,
    float *ap,
    float *bp,
    float *cp,
    float *dp,
    float *gp,
    double grav
)
{
   float eps,width,yw,yus,yds;
   float rteps,root2g,wconst;

   yus=y[i+j*NODES];
   yds=y[i+1+j*NODES];
   yw=bel[i+j*NODES];
   width=ww[i+j*NODES];

   eps=0.25/(32.2/grav);   /* the grav term converts between ft. and m ) */
   rteps=0.5/(32.2/grav);  /* the grav term converts between ft. and m ) */

   root2g=sqrt((double)(2.0*grav));
   wconst=root2g*sqrt((double)(1.0/3.0))*2.0/3.0;

   *a=0.0;
   *b=1.0;
   *c=0.0;
   *d=1.0;
   *g=q[i+j*NODES]-q[i+1+j*NODES];

   if((yds-yw) < 2.0/3.0*(yus-yw)) 
      {
      /* FREE FLOWING */
      *ap=0.0;
      *bp=0.0;
      *cp=(-width)*wconst*pow((yus-yw),(double)1.5);
      *dp=1.0;
      *gp=q[i+j*NODES]-width*wconst*pow((yus-yw),(double)1.5);
      }
   else
      {
      if((yus-yds)<=eps) 
         {
         /* FLOODED, SINGULAR */
	  *ap=width*root2g*sqrt((double)eps)/eps*(yus-2.*yds+yw);
	  *bp=0.0;
	  *cp=-width*root2g*sqrt((double)eps)/eps*(yds-yw);
	  *dp=1.0;
	  *gp=q[i+j*NODES]-width*root2g*sqrt((double)eps)*(yds-yw)*
              (yus-yds)/eps;
          }
      else
         {
         /* FULLY FLOODED */
         *ap=width*root2g*(sqrt((double)(yus-yds))-0.5*(yds-yw)*
             pow((yus-yds),(double)(-0.5)));
         *bp=0.0;
         *cp=-width*root2g/2.0*(yds-yw)*pow((yus-yds),(double)(-0.5));
         *dp=1.0;
         *gp=q[i+j*NODES]-width*root2g*(yds-yw)*sqrt((double)(yus-yds));
         }
      }
   return;
}
