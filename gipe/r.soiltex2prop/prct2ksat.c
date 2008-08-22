#include<stdio.h>

#define POLYGON_DIMENSION 50

struct vector
{
    double sand;
    double clay;
    double silt;
};


/* KSAT */

double prct2ksat(double sand_input, double clay_input)
{
    int i, index;

    double temp, ksat;

    double silt_input = 0.0;	/*Rawls et al (1990) */

    /*do not have silt input */
    /*printf("in prct2ksat(), cm/h\n"); */
    /*setup the 3Dvectors and initialize them */
    struct vector cls[POLYGON_DIMENSION] = { 0.0 };
    /*In case silt is not == 0.0, fill up explicitly */
    for (i = 0; i < POLYGON_DIMENSION; i++) {
	cls[i].sand = 0.0;
	cls[i].clay = 0.0;
	cls[i].silt = 0.0;
    }
    /*fill up initial polygon points */
    cls[0].sand = 0.0;
    cls[0].clay = 100.0;
    cls[1].sand = 0.0;
    cls[1].clay = 60.0;
    cls[2].sand = 7.0;
    cls[2].clay = 56.0;
    /*Get started */
    index =
	point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			  cls[0].clay, cls[0].silt, cls[1].sand, cls[1].clay,
			  cls[1].silt, cls[2].sand, cls[2].clay, cls[2].silt);
    if (index == 1) {
	ksat = 0.0025;
	index = 1;
	/*printf("Ksat=0.0025\n"); */
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 0.0;
	cls[0].clay = 100.0;
	cls[1].sand = 7.0;
	cls[1].clay = 56.0;
	cls[2].sand = 30.0;
	cls[2].clay = 56.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.0025\n"); */
	    ksat = 0.0025;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 0.0;
	cls[0].clay = 100.0;
	cls[1].sand = 30.0;
	cls[1].clay = 56.0;
	cls[2].sand = 40.0;
	cls[2].clay = 63.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.0025\n"); */
	    ksat = 0.0025;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 100.0;
	cls[0].clay = 0.0;
	cls[1].sand = 85.0;
	cls[1].clay = 0.0;
	cls[2].sand = 90.0;
	cls[2].clay = 10.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=25.0\n"); */
	    ksat = 25.0;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 85.0;
	cls[0].clay = 0.0;
	cls[1].sand = 90.0;
	cls[1].clay = 10.0;
	cls[2].sand = 80.0;
	cls[2].clay = 0.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=15.0\n"); */
	    ksat = 15.0;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 80.0;
	cls[0].clay = 0.0;
	cls[1].sand = 90.0;
	cls[1].clay = 10.0;
	cls[2].sand = 85.0;
	cls[2].clay = 15.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=15.0\n"); */
	    ksat = 15.0;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 85.0;
	cls[0].clay = 15.0;
	cls[1].sand = 80.0;
	cls[1].clay = 0.0;
	cls[2].sand = 70.0;
	cls[2].clay = 0.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=7.5\n"); */
	    ksat = 7.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 70.0;
	cls[0].clay = 0.0;
	cls[1].sand = 85.0;
	cls[1].clay = 15.0;
	cls[2].sand = 75.0;
	cls[2].clay = 25.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=7.5\n"); */
	    ksat = 7.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 70.0;
	cls[0].clay = 0.0;
	cls[1].sand = 75.0;
	cls[1].clay = 25.0;
	cls[2].sand = 68.0;
	cls[2].clay = 23.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=2.5\n"); */
	    ksat = 2.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 75.0;
	cls[0].clay = 25.0;
	cls[1].sand = 68.0;
	cls[1].clay = 23.0;
	cls[2].sand = 70.0;
	cls[2].clay = 30.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=2.5\n"); */
	    ksat = 2.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 70.0;
	cls[0].clay = 0.0;
	cls[1].sand = 35.0;
	cls[1].clay = 0.0;
	cls[2].sand = 68.0;
	cls[2].clay = 23.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=2.5\n"); */
	    ksat = 2.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 17.0;
	cls[0].clay = 0.0;
	cls[1].sand = 35.0;
	cls[1].clay = 0.0;
	cls[2].sand = 22.0;
	cls[2].clay = 5.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=1.5\n"); */
	    ksat = 1.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 22.0;
	cls[0].clay = 5.0;
	cls[1].sand = 35.0;
	cls[1].clay = 0.0;
	cls[2].sand = 68.0;
	cls[2].clay = 23.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=1.5\n"); */
	    ksat = 1.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 22.0;
	cls[0].clay = 5.0;
	cls[1].sand = 68.0;
	cls[1].clay = 23.0;
	cls[2].sand = 60.0;
	cls[2].clay = 25.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=1.5\n"); */
	    ksat = 1.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 60.0;
	cls[0].clay = 25.0;
	cls[1].sand = 68.0;
	cls[1].clay = 23.0;
	cls[2].sand = 70.0;
	cls[2].clay = 30.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=1.5\n"); */
	    ksat = 1.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 60.0;
	cls[0].clay = 25.0;
	cls[1].sand = 65.0;
	cls[1].clay = 35.0;
	cls[2].sand = 70.0;
	cls[2].clay = 30.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=1.5\n"); */
	    ksat = 1.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 17.0;
	cls[0].clay = 0.0;
	cls[1].sand = 10.0;
	cls[1].clay = 0.0;
	cls[2].sand = 22.0;
	cls[2].clay = 5.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.8\n"); */
	    ksat = 0.8;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 20.0;
	cls[0].clay = 12.0;
	cls[1].sand = 10.0;
	cls[1].clay = 0.0;
	cls[2].sand = 22.0;
	cls[2].clay = 5.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.8\n"); */
	    ksat = 0.8;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 20.0;
	cls[0].clay = 12.0;
	cls[1].sand = 42.0;
	cls[1].clay = 20.0;
	cls[2].sand = 22.0;
	cls[2].clay = 5.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.8\n"); */
	    ksat = 0.8;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 60.0;
	cls[0].clay = 25.0;
	cls[1].sand = 42.0;
	cls[1].clay = 20.0;
	cls[2].sand = 22.0;
	cls[2].clay = 5.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.8\n"); */
	    ksat = 0.8;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 60.0;
	cls[0].clay = 25.0;
	cls[1].sand = 42.0;
	cls[1].clay = 20.0;
	cls[2].sand = 57.0;
	cls[2].clay = 30.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.8\n"); */
	    ksat = 0.8;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 60.0;
	cls[0].clay = 25.0;
	cls[1].sand = 65.0;
	cls[1].clay = 35.0;
	cls[2].sand = 57.0;
	cls[2].clay = 30.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.8\n"); */
	    ksat = 0.8;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 63.0;
	cls[0].clay = 38.0;
	cls[1].sand = 65.0;
	cls[1].clay = 35.0;
	cls[2].sand = 57.0;
	cls[2].clay = 30.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.8\n"); */
	    ksat = 0.8;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 55.0;
	cls[0].clay = 35.0;
	cls[1].sand = 60.0;
	cls[1].clay = 40.0;
	cls[2].sand = 63.0;
	cls[2].clay = 38.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.5\n"); */
	    ksat = 0.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 55.0;
	cls[0].clay = 35.0;
	cls[1].sand = 57.0;
	cls[1].clay = 30.0;
	cls[2].sand = 63.0;
	cls[2].clay = 38.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.5\n"); */
	    ksat = 0.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 55.0;
	cls[0].clay = 35.0;
	cls[1].sand = 57.0;
	cls[1].clay = 30.0;
	cls[2].sand = 38.0;
	cls[2].clay = 23.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.5\n"); */
	    ksat = 0.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 42.0;
	cls[0].clay = 20.0;
	cls[1].sand = 57.0;
	cls[1].clay = 30.0;
	cls[2].sand = 38.0;
	cls[2].clay = 23.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.5\n"); */
	    ksat = 0.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 42.0;
	cls[0].clay = 20.0;
	cls[1].sand = 23.0;
	cls[1].clay = 20.0;
	cls[2].sand = 20.0;
	cls[2].clay = 12.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.5\n"); */
	    ksat = 0.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 7.0;
	cls[0].clay = 3.0;
	cls[1].sand = 23.0;
	cls[1].clay = 20.0;
	cls[2].sand = 20.0;
	cls[2].clay = 12.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.5\n"); */
	    ksat = 0.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 7.0;
	cls[0].clay = 3.0;
	cls[1].sand = 10.0;
	cls[1].clay = 0.0;
	cls[2].sand = 20.0;
	cls[2].clay = 12.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.5\n"); */
	    ksat = 0.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 7.0;
	cls[0].clay = 3.0;
	cls[1].sand = 10.0;
	cls[1].clay = 0.0;
	cls[2].sand = 0.0;
	cls[2].clay = 0.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.5\n"); */
	    ksat = 0.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 7.0;
	cls[0].clay = 3.0;
	cls[1].sand = 0.0;
	cls[1].clay = 3.0;
	cls[2].sand = 0.0;
	cls[2].clay = 0.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.5\n"); */
	    ksat = 0.5;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 7.0;
	cls[0].clay = 3.0;
	cls[1].sand = 0.0;
	cls[1].clay = 3.0;
	cls[2].sand = 9.0;
	cls[2].clay = 18.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.3\n"); */
	    ksat = 0.3;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 0.0;
	cls[0].clay = 16.0;
	cls[1].sand = 0.0;
	cls[1].clay = 3.0;
	cls[2].sand = 9.0;
	cls[2].clay = 18.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.3\n"); */
	    ksat = 0.3;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 7.0;
	cls[0].clay = 3.0;
	cls[1].sand = 23.0;
	cls[1].clay = 20.0;
	cls[2].sand = 9.0;
	cls[2].clay = 18.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.3\n"); */
	    ksat = 0.3;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 22.0;
	cls[0].clay = 29.0;
	cls[1].sand = 23.0;
	cls[1].clay = 20.0;
	cls[2].sand = 9.0;
	cls[2].clay = 18.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.3\n"); */
	    ksat = 0.3;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 22.0;
	cls[0].clay = 29.0;
	cls[1].sand = 23.0;
	cls[1].clay = 20.0;
	cls[2].sand = 33.0;
	cls[2].clay = 29.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.3\n"); */
	    ksat = 0.3;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 38.0;
	cls[0].clay = 23.0;
	cls[1].sand = 23.0;
	cls[1].clay = 20.0;
	cls[2].sand = 33.0;
	cls[2].clay = 29.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.3\n"); */
	    ksat = 0.3;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 38.0;
	cls[0].clay = 23.0;
	cls[1].sand = 50.0;
	cls[1].clay = 35.0;
	cls[2].sand = 33.0;
	cls[2].clay = 29.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.3\n"); */
	    ksat = 0.3;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 38.0;
	cls[0].clay = 23.0;
	cls[1].sand = 50.0;
	cls[1].clay = 35.0;
	cls[2].sand = 55.0;
	cls[2].clay = 35.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.3\n"); */
	    ksat = 0.3;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 60.0;
	cls[0].clay = 40.0;
	cls[1].sand = 50.0;
	cls[1].clay = 35.0;
	cls[2].sand = 55.0;
	cls[2].clay = 35.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.3\n"); */
	    ksat = 0.3;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 60.0;
	cls[0].clay = 40.0;
	cls[1].sand = 50.0;
	cls[1].clay = 35.0;
	cls[2].sand = 57.0;
	cls[2].clay = 44.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.3\n"); */
	    ksat = 0.3;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 40.0;
	cls[0].clay = 38.0;
	cls[1].sand = 50.0;
	cls[1].clay = 35.0;
	cls[2].sand = 57.0;
	cls[2].clay = 44.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.15\n"); */
	    ksat = 0.15;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 40.0;
	cls[0].clay = 38.0;
	cls[1].sand = 55.0;
	cls[1].clay = 45.0;
	cls[2].sand = 57.0;
	cls[2].clay = 44.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.15\n"); */
	    ksat = 0.15;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 40.0;
	cls[0].clay = 38.0;
	cls[1].sand = 50.0;
	cls[1].clay = 35.0;
	cls[2].sand = 33.0;
	cls[2].clay = 29.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.15\n"); */
	    ksat = 0.15;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 40.0;
	cls[0].clay = 38.0;
	cls[1].sand = 30.0;
	cls[1].clay = 38.0;
	cls[2].sand = 33.0;
	cls[2].clay = 29.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.15\n"); */
	    ksat = 0.15;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 22.0;
	cls[0].clay = 29.0;
	cls[1].sand = 30.0;
	cls[1].clay = 38.0;
	cls[2].sand = 33.0;
	cls[2].clay = 29.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.15\n"); */
	    ksat = 0.15;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 22.0;
	cls[0].clay = 29.0;
	cls[1].sand = 30.0;
	cls[1].clay = 38.0;
	cls[2].sand = 13.0;
	cls[2].clay = 29.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.15\n"); */
	    ksat = 0.15;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 22.0;
	cls[0].clay = 29.0;
	cls[1].sand = 9.0;
	cls[1].clay = 18.0;
	cls[2].sand = 13.0;
	cls[2].clay = 29.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.15\n"); */
	    ksat = 0.15;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 0.0;
	cls[0].clay = 16.0;
	cls[1].sand = 9.0;
	cls[1].clay = 18.0;
	cls[2].sand = 13.0;
	cls[2].clay = 29.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.15\n"); */
	    ksat = 0.15;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 0.0;
	cls[0].clay = 16.0;
	cls[1].sand = 0.0;
	cls[1].clay = 25.0;
	cls[2].sand = 13.0;
	cls[2].clay = 29.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.15\n"); */
	    ksat = 0.15;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 0.0;
	cls[0].clay = 33.0;
	cls[1].sand = 0.0;
	cls[1].clay = 25.0;
	cls[2].sand = 15.0;
	cls[2].clay = 38.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.075\n"); */
	    ksat = 0.075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 13.0;
	cls[0].clay = 29.0;
	cls[1].sand = 0.0;
	cls[1].clay = 25.0;
	cls[2].sand = 15.0;
	cls[2].clay = 38.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.075\n"); */
	    ksat = 0.075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 13.0;
	cls[0].clay = 29.0;
	cls[1].sand = 30.0;
	cls[1].clay = 38.0;
	cls[2].sand = 15.0;
	cls[2].clay = 38.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.075\n"); */
	    ksat = 0.075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 20.0;
	cls[0].clay = 41.0;
	cls[1].sand = 30.0;
	cls[1].clay = 38.0;
	cls[2].sand = 15.0;
	cls[2].clay = 38.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.075\n"); */
	    ksat = 0.075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 20.0;
	cls[0].clay = 41.0;
	cls[1].sand = 30.0;
	cls[1].clay = 38.0;
	cls[2].sand = 50.0;
	cls[2].clay = 50.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.075\n"); */
	    ksat = 0.075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 40.0;
	cls[0].clay = 38.0;
	cls[1].sand = 30.0;
	cls[1].clay = 38.0;
	cls[2].sand = 50.0;
	cls[2].clay = 50.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.075\n"); */
	    ksat = 0.075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 40.0;
	cls[0].clay = 38.0;
	cls[1].sand = 55.0;
	cls[1].clay = 45.0;
	cls[2].sand = 50.0;
	cls[2].clay = 50.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.075\n"); */
	    ksat = 0.075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 13.0;
	cls[0].clay = 50.0;
	cls[1].sand = 20.0;
	cls[1].clay = 41.0;
	cls[2].sand = 50.0;
	cls[2].clay = 50.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.025\n"); */
	    ksat = 0.025;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 13.0;
	cls[0].clay = 50.0;
	cls[1].sand = 18.0;
	cls[1].clay = 53.0;
	cls[2].sand = 50.0;
	cls[2].clay = 50.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.025\n"); */
	    ksat = 0.025;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 35.0;
	cls[0].clay = 55.0;
	cls[1].sand = 18.0;
	cls[1].clay = 53.0;
	cls[2].sand = 50.0;
	cls[2].clay = 50.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.025\n"); */
	    ksat = 0.025;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 35.0;
	cls[0].clay = 55.0;
	cls[1].sand = 43.0;
	cls[1].clay = 58.0;
	cls[2].sand = 50.0;
	cls[2].clay = 50.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.025\n"); */
	    ksat = 0.025;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 13.0;
	cls[0].clay = 50.0;
	cls[1].sand = 20.0;
	cls[1].clay = 41.0;
	cls[2].sand = 15.0;
	cls[2].clay = 38.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.025\n"); */
	    ksat = 0.025;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 13.0;
	cls[0].clay = 50.0;
	cls[1].sand = 0.0;
	cls[1].clay = 33.0;
	cls[2].sand = 15.0;
	cls[2].clay = 38.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.025\n"); */
	    ksat = 0.025;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 13.0;
	cls[0].clay = 50.0;
	cls[1].sand = 0.0;
	cls[1].clay = 33.0;
	cls[2].sand = 0.0;
	cls[2].clay = 51.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.025\n"); */
	    ksat = 0.025;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 8.0;
	cls[0].clay = 56.0;
	cls[1].sand = 0.0;
	cls[1].clay = 60.0;
	cls[2].sand = 0.0;
	cls[2].clay = 51.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.0075\n"); */
	    ksat = 0.0075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 8.0;
	cls[0].clay = 56.0;
	cls[1].sand = 13.0;
	cls[1].clay = 50.0;
	cls[2].sand = 0.0;
	cls[2].clay = 51.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.0075\n"); */
	    ksat = 0.0075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 8.0;
	cls[0].clay = 56.0;
	cls[1].sand = 13.0;
	cls[1].clay = 50.0;
	cls[2].sand = 18.0;
	cls[2].clay = 53.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.0075\n"); */
	    ksat = 0.0075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 8.0;
	cls[0].clay = 56.0;
	cls[1].sand = 30.0;
	cls[1].clay = 56.0;
	cls[2].sand = 18.0;
	cls[2].clay = 53.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.0075\n"); */
	    ksat = 0.0075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 35.0;
	cls[0].clay = 55.0;
	cls[1].sand = 30.0;
	cls[1].clay = 56.0;
	cls[2].sand = 18.0;
	cls[2].clay = 53.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.0075\n"); */
	    ksat = 0.0075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 35.0;
	cls[0].clay = 55.0;
	cls[1].sand = 30.0;
	cls[1].clay = 56.0;
	cls[2].sand = 43.0;
	cls[2].clay = 58.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.0075\n"); */
	    ksat = 0.0075;
	}
    }
    if (index == 0) {		/* if index not found then continue */
	cls[0].sand = 40.0;
	cls[0].clay = 63.0;
	cls[1].sand = 30.0;
	cls[1].clay = 56.0;
	cls[2].sand = 43.0;
	cls[2].clay = 58.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    index = 1;
	    /*printf("Ksat=0.0075\n"); */
	    ksat = 0.0075;
	}
    }
    return ksat;
}
