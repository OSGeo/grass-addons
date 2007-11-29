#include "all.h"

/*******************************************************************/
void reservoir (


/*     
 *  This subroutine is used to adjust the reservoir w.s.e with inflows   
 *  and outflows. 
 */
    int j,
    int ninfs,
    int *depend,
    int *backdep,
    float *qp,
    double delt,
    int *nx1,
    double qmin,
    float spilel
)

{
   /* LOCAL VARIABLES */
   int i,uplink,outlink;
   int nlakecells;
   double delts, aream2;

   nlakecells=lake_cells[lake_cat[con_vect[1+j*NODES]]];
   delts=(double)delt*(double)60.0;
   aream2=(double)nlakecells*w*w;
   for(i=1;i<=ninfs;i++)
      {
      /* CALCULATE THE POSITIVE CHANGE IN WSE DUE TO STREAM INFLOWS */
      uplink=depend[j+i*LINKS];
      lake_el[lake_cat[con_vect[1+j*NODES]]]+=
	      qp[nx1[uplink]+uplink*NODES]*delts/aream2;
      }

   /* CALCULATE THE POSITIVE CHANGE IN WSE DUE TO OTHER INFLOWS */
   lake_el[lake_cat[con_vect[1+j*NODES]]]=lake_el[lake_cat[con_vect[1+j*NODES]]]+ qtolake[lake_cat[con_vect[1+j*NODES]]]*delts/aream2;

   if(lake_el[lake_cat[con_vect[1+j*NODES]]]>spilel)
      {
      /*  CALCULATE THE NEGATIVE CHANGE IN WSE DUE TO SPILLWAY OUTFLOWS */
      outlink=backdep[j];
      lake_el[lake_cat[con_vect[1+j*NODES]]]-=(qp[1+outlink*NODES]-qmin)*
					      delts/aream2;
      }
   return;
}
