#include "all.h"

/*******************************************************************/
void 
dsyot (
/*
 *    THIS SUBROUTINE CALCULATES THE DOWNSTREAM DISCHARGE BOUNDARY
 *    CONDITION Y(T)
 */
    double t,
    double *ynew,
    int dltype,
    double lowspot,
    double highspot,
    double tdrain,
    double normout
)

{
   float lakelev,highelev=0.0,lowelev=0.0,ystep=0.0;
   lakelev=217.28;
   if(dltype==0) 
      {
      /* this is the outlet */
      highelev=highspot;
      lowelev=lowspot+normout;
      ystep=highelev-lowelev;
      }
   if(dltype==4)
      {
      /* this is a lake */
      highelev=237.0;
      lowelev=lakelev;
      ystep=highelev-lowelev;
      }
   if(t<=tdrain)
      {
      *ynew=highelev-ystep/tdrain*t;
      }
   else
      {
      *ynew=lowelev;
      }

/*   fprintf(stderr,"ynew=%f\n",*ynew);
 *   fflush(stderr);
 */
   return;
}
