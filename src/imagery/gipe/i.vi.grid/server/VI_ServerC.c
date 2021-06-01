#include<stdio.h>
#include<math.h>
#include<stdlib.h>
#include<unistd.h>

void VI_CALC(int n, int *I, double *a,double *b, double *c, double *d, double *e, double *f,double *r)
{

	
	int col,t,temp;
	char  hname[256];
	//temp=400;	
	gethostname(hname, (int) sizeof(hname));
	printf("Hostname:%s\n",hname);
	//printf("temp=%d\n",temp);
	for (col=0; col<n; col++)
	{
	  // for(t=0;t<temp;t++){	
		if (I[col]==0) r[col]=-999.99;
		else if (I[col]==1){
		//sr
			if(  a[col] ==  0.0 ){
				r[col] = -1.0;
			} else {
				r[col] = (b[col]/ a[col]);
			}	
		}
		else if (I[col]==2){
		//ndvi
			if( ( b[col] + a[col] ) ==  0.0 ){
				r[col] = -1.0;
			} else {
				r[col] = ( b[col] - a[col] ) / ( b[col] + a[col] );
			}
		}
		else if (I[col]==3){
		//ipvi	
		
			if( ( b[col] + a[col] ) ==  0.0 ){
				r[col] = -1.0;
			} else {
				r[col] = ( b[col] ) / ( b[col] + a[col] );
			}	

		}	
		else if (I[col]==4){
		//dvi
			if( ( b[col] + a[col] ) ==  0.0 ){
				r[col] = -1.0;
			} else {
				r[col] = ( b[col] - a[col] ) ;
			}		
		}
		else if (I[col]==5){
		//pvi
			if( ( b[col] + a[col] ) ==  0.0 ){
				r[col] = -1.0;
			} else {
				r[col] = (sin(1) * b[col] ) / ( cos(1) * a[col] ); 

			}
	
		}
		else if (I[col]==6){
		//wdvi
			double slope=1;//slope of soil line //
			if( ( b[col] + a[col] ) ==  0.0 ){
				r[col] = -1.0;
			} else {
				r[col] = ( b[col] - slope*a[col] );

			}
		}
		else if (I[col]==7){
		//savi
			if( ( b[col] + a[col] ) ==  0.0 ){
				r[col] = -1.0;

			} else {

				r[col] = ((1+0.5)*( b[col] - a[col] )) / ( b[col] + a[col] +0.5);

			}
		}
		else if (I[col]==8){
		//msavi
			if( ( b[col] + a[col] ) ==  0.0 ){
				r[col] = -1.0;

			} else {

				r[col] =(1/2)*(2 * (b[col]+1)-sqrt((2*b[col]+1)*(2*b[col]+1))-(8 *(b[col]-a[col]))) ;

			}
		}
		else if (I[col]==9){
		//msavi2
			if( ( b[col] + a[col] ) ==  0.0 ){
				r[col] = -1.0;
			} else {

				r[col] =(1/2)*(2 * (b[col]+1)-sqrt((2*b[col]+1)*(2*b[col]+1))-(8 *(b[col]-a[col]))) ;
			}
		}
		else if (I[col]==10){
		//gemi
			if( ( b[col] + a[col] ) ==  0.0 ){
				r[col] = -1.0;
			} else {
				r[col] = (( (2*((b[col] * b[col])-(a[col] * a[col]))+1.5*b[col]+0.5*a[col]) /(b[col]+ a[col] + 0.5)) * (1 - 0.25 * (2*((b[col] * b[col])-(a[col] * a[col]))+1.5*b[col]+0.5*a[col]) /(b[col] + a[col] + 0.5))) -( (a[col] - 0.125) / (1 - a[col])) ;

			}
		}
		else if (I[col]==11){
		//arvi
			if( ( b[col] + a[col] ) ==  0.0 ){
				r[col] = -1.0;
			} else {
				r[col] = ( b[col] - (2*a[col] - d[col])) / ( b[col] + (2*a[col] - d[col]));
			}
		}
		else if (I[col]==12){
		//gvi
			if( ( b[col] + a[col] ) ==  0.0 ){
				r[col] = -1.0;
			} else	{
				r[col] = (-0.2848*d[col]-0.2435*c[col]-0.5436*a[col]+0.7243*b[col]+0.0840*e[col]- 0.1800*f[col]);
			}
		}
		else if (I[col]==13){
		//gari
			r[col] = ( b[col] - (c[col]-(d[col] - a[col]))) / ( b[col] + (c[col]-(d[col] - a[col]))) ;
		}
	  // } //t	
	}//for col end

	
}//function end
