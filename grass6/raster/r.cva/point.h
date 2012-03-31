#ifndef __POINT_H__
#define __POINT_H__


/****************************************************************/
/*								*/
/*	point.h		in	~/src/Glos			*/
/*								*/
/*	This header file defines the data structure of a 	*/
/*	point (structure containing various attributes of	*/
/*	a grid cell).						*/
/*								*/
/****************************************************************/

	struct point {

        double orientation;	
	/* horizontal angle(degrees) measured from +ve x-axis	*/ 

        double inclination;	
	/* vertical angle(degrees) from the viewing point	*/
	
	double probability;
	/* for probabilistic viewsheds: this stores the probability
	   of the point being visible */

        int x;	/* x-coor measured from viewing point location	*/
        int y;	/* y-coor measured from viewing point location  */
	
        struct point *next;	/* pointer to next point in list*/
        struct point *previous; /* ptr to previous pt. in list	*/ 
	
        };

/****************************************************************/

#endif

