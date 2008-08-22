#include<stdio.h>

#define POLYGON_DIMENSION 50

struct vector
{
    double sand;
    double clay;
    double silt;
};

double prct2porosity(double sand_input, double clay_input)
{
    int i, index;

    double temp, porosity;

    double silt_input = 0.0;	//Rawls et al (1990)

    //do not have silt input
    //printf("in prct2poros(), Volume Fraction\n");
    //setup the 3Dvectors and initialize them
    struct vector cls[POLYGON_DIMENSION] = { 0.0 };
    //In case silt is not == 0.0, fill up explicitly
    for (i = 0; i < POLYGON_DIMENSION; i++) {
	cls[i].sand = 0.0;
	cls[i].clay = 0.0;
	cls[i].silt = 0.0;
    }
    //printf("0=>sand:%.2f\tclay:%.2f\n", sand_input,clay_input);
    cls[0].sand = 0.0;
    cls[0].clay = 100.0;
    cls[1].sand = 10.0;
    cls[1].clay = 90.0;
    cls[2].sand = 25.0;
    cls[2].clay = 75.0;
    //printf("sand0:%.2f\tclay0:%.2f\tsilt0:%.2f\n",cls[0].sand,cls[0].clay,cls[0].silt);
    //printf("sand1:%.2f\tclay1:%.2f\tsilt1:%.2f\n",cls[1].sand,cls[1].clay,cls[1].silt);
    //printf("sand2:%.2f\tclay2:%.2f\tsilt2:%.2f\n",cls[2].sand,cls[2].clay,cls[2].silt);
    //Get started
    index =
	point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			  cls[0].clay, cls[0].silt, cls[1].sand, cls[1].clay,
			  cls[1].silt, cls[2].sand, cls[2].clay, cls[2].silt);
    if (index == 1) {
	porosity = 0.575;
	//printf("Poros=0.575\n");
    }
    if (index == 0) {		// if index not found then continue
	//printf("1=>sand:%.2f\tclay:%.2f\n",sand_input,clay_input);
	cls[0].sand = 10.0;
	cls[0].clay = 0.0;
	cls[1].sand = 20.0;
	cls[1].clay = 20.0;
	cls[2].sand = 50.0;
	cls[2].clay = 0.0;
	//printf("sand0:%.2f\tclay0:%.2f\tsilt0:%.2f\n",cls[0].sand,cls[0].clay,cls[0].silt);
	//printf("sand1:%.2f\tclay1:%.2f\tsilt1:%.2f\n",cls[1].sand,cls[1].clay,cls[1].silt);
	//printf("sand2:%.2f\tclay2:%.2f\tsilt2:%.2f\n",cls[2].sand,cls[2].clay,cls[2].silt);
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.575\n");
	    porosity = 0.575;
	}
    }
    if (index == 0) {		// if index not found then continue
	//printf("2=>sand:%.2f\tclay:%.2f\n",sand_input,clay_input);
	cls[0].sand = 100.0;
	cls[0].clay = 0.0;
	cls[1].sand = 50.0;
	cls[1].clay = 50.0;
	cls[2].sand = 50.0;
	cls[2].clay = 43.0;
	//printf("sand0:%.2f\tclay0:%.2f\tsilt0:%.2f\n",cls[0].sand,cls[0].clay,cls[0].silt);
	//printf("sand1:%.2f\tclay1:%.2f\tsilt1:%.2f\n",cls[1].sand,cls[1].clay,cls[1].silt);
	//printf("sand2:%.2f\tclay2:%.2f\tsilt2:%.2f\n",cls[2].sand,cls[2].clay,cls[2].silt);
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.425\n");
	    porosity = 0.425;
	}
    }
    if (index == 0) {		// if index not found then continue
	//printf("3=>sand:%.2f\tclay:%.2f\n",sand_input,clay_input);
	cls[0].sand = 100.0;
	cls[0].clay = 0.0;
	cls[1].sand = 50.0;
	cls[1].clay = 43.0;
	cls[2].sand = 52.0;
	cls[2].clay = 33.0;
	////printf("sand0:%.2f\tclay0:%.2f\tsilt0:%.2f\n",cls[0].sand,cls[0].clay,cls[0].silt);
	////printf("sand1:%.2f\tclay1:%.2f\tsilt1:%.2f\n",cls[1].sand,cls[1].clay,cls[1].silt);
	////printf("sand2:%.2f\tclay2:%.2f\tsilt2:%.2f\n",cls[2].sand,cls[2].clay,cls[2].silt);
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.425\n");
	    porosity = 0.425;
	}
    }
    if (index == 0) {		// if index not found then continue
	cls[0].sand = 100.0;
	cls[0].clay = 0.0;
	cls[1].sand = 52.0;
	cls[1].clay = 33.0;
	cls[2].sand = 57.0;
	cls[2].clay = 25.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.425\n");
	    porosity = 0.425;
	}
    }
    if (index == 0) {		// if index not found then continue
	cls[0].sand = 100.0;
	cls[0].clay = 0.0;
	cls[1].sand = 57.0;
	cls[1].clay = 25.0;
	cls[2].sand = 87.0;
	cls[2].clay = 0.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.425\n");
	    porosity = 0.425;
	}
    }
    if (index == 0) {		// if index not found then continue
	cls[0].sand = 0.0;
	cls[0].clay = 0.0;
	cls[1].sand = 25.0;
	cls[1].clay = 75.0;
	cls[2].sand = 0.0;
	cls[2].clay = 90.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.525\n");
	    porosity = 0.525;
	}
    }
    if (index == 0) {		// if index not found then continue
	cls[0].sand = 0.0;
	cls[0].clay = 0.0;
	cls[1].sand = 25.0;
	cls[1].clay = 75.0;
	cls[2].sand = 10.0;
	cls[2].clay = 0.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.525\n");
	    porosity = 0.525;
	}
    }
    if (index == 0) {		// if index not found then continue
	cls[0].sand = 10.0;
	cls[0].clay = 0.0;
	cls[1].sand = 25.0;
	cls[1].clay = 75.0;
	cls[2].sand = 20.0;
	cls[2].clay = 20.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.525\n");
	    porosity = 0.525;
	}
    }
    if (index == 0) {		// if index not found then continue
	cls[0].sand = 20.0;
	cls[0].clay = 20.0;
	cls[1].sand = 25.0;
	cls[1].clay = 75.0;
	cls[2].sand = 25.0;
	cls[2].clay = 55.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.525\n");
	    porosity = 0.525;
	}
    }
    if (index == 0) {		// if index not found then continue
	cls[0].sand = 20.0;
	cls[0].clay = 20.0;
	cls[1].sand = 25.0;
	cls[1].clay = 55.0;
	cls[2].sand = 27.0;
	cls[2].clay = 45.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.525\n");
	    porosity = 0.525;
	}
    }
    if (index == 0) {		// if index not found then continue
	cls[0].sand = 20.0;
	cls[0].clay = 20.0;
	cls[1].sand = 27.0;
	cls[1].clay = 45.0;
	cls[2].sand = 50.0;
	cls[2].clay = 0.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.525\n");
	    porosity = 0.525;
	}
    }
    if (index == 0) {		// if index not found then continue
	cls[0].sand = 50.0;
	cls[0].clay = 0.0;
	cls[1].sand = 70.0;
	cls[1].clay = 0.0;
	cls[2].sand = 37.0;
	cls[2].clay = 25.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.525\n");
	    porosity = 0.525;
	}
    }
    if (index == 0) {		// if index not found then continue
	cls[0].sand = 25.0;
	cls[0].clay = 75.0;
	cls[1].sand = 25.0;
	cls[1].clay = 55.0;
	cls[2].sand = 28.0;
	cls[2].clay = 61.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.525\n");
	    porosity = 0.525;
	}
    }
    if (index == 0) {		// if index not found then continue
	cls[0].sand = 25.0;
	cls[0].clay = 75.0;
	cls[1].sand = 37.0;
	cls[1].clay = 65.0;
	cls[2].sand = 28.0;
	cls[2].clay = 61.0;
	index =
	    point_in_triangle(sand_input, clay_input, silt_input, cls[0].sand,
			      cls[0].clay, cls[0].silt, cls[1].sand,
			      cls[1].clay, cls[1].silt, cls[2].sand,
			      cls[2].clay, cls[2].silt);
	if (index == 1) {
	    //printf("Poros=0.525\n");
	    porosity = 0.525;
	}
    }
    if (index == 0) {		// if index not found then continue
	//printf("Poros=0.475 (final choice...)\n");
	porosity = 0.475;
    }
    return porosity;
}
