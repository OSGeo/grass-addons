
#include "all.h"

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/
void 
INTERCEPTION (
/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/
    int vect,
    double dt,
    float *Inter,
    float *sv,
    float *exp,
    double rainrate,
    float *intrate
)

{
double  tinc,intinc;

if(Inter[vect] < sv[vect])
{
   *intrate=rainrate;
   if((Inter[vect]+(*intrate)*dt) > sv[vect])
   { 
      tinc=(sv[vect] - Inter[vect])/rainrate;
      intinc=tinc*rainrate + exp[vect]*rainrate*(dt - tinc);
      *intrate=intinc/dt;
   }
}
else
{
   *intrate=exp[vect]*rainrate;
}

Inter[vect]=Inter[vect] + (*intrate)*dt;
return;

}
