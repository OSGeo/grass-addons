#include<stdio.h>

#define POLYGON_DIMENSION 50

struct vector
{
    double sand;
    double clay;
    double silt;
};

int point_in_triangle(double point_x, double point_y, double point_z,
		      double t1_x, double t1_y, double t1_z, double t2_x,
		      double t2_y, double t2_z, double t3_x, double t3_y,
		      double t3_z)
{
    /*printf("in function: sand=%5.3f clay=%5.3f silt=%5.3f\n",point_x,point_y,point_z); */
    int index = 0;

    double answer;

    double answer1_x, answer1_y, answer1_z;

    double answer2_x, answer2_y, answer2_z;

    double answer3_x, answer3_y, answer3_z;

    /* Consider three points forming a trinagle from a given soil class boundary ABC */
    /* Consider F an additional point in space */
    double af1, af2, af3;	/*Points for vector AF */

    double bf1, bf2, bf3;	/*Points for vector BF */

    double cf1, cf2, cf3;	/*Points for vector CF */

    double ab1, ab2, ab3;	/*Points for vector AB */

    double bc1, bc2, bc3;	/*Points for vector BC */

    double ca1, ca2, ca3;	/*Points for vector CA */

    /* Create vectors AB, BC and CA */
    ab1 = (t2_x - t1_x);
    ab2 = (t2_y - t1_y);
    ab3 = (t2_z - t1_z);
    bc1 = (t3_x - t2_x);
    bc2 = (t3_y - t2_y);
    bc3 = (t3_z - t2_z);
    ca1 = (t1_x - t3_x);
    ca2 = (t1_y - t3_y);
    ca3 = (t1_z - t3_z);
    /* Create vectors AF, BF and CF */
    af1 = (point_x - t1_x);
    af2 = (point_y - t1_y);
    af3 = (point_z - t1_z);
    bf1 = (point_x - t2_x);
    bf2 = (point_y - t2_y);
    bf3 = (point_z - t2_z);
    cf1 = (point_x - t3_x);
    cf2 = (point_y - t3_y);
    cf3 = (point_z - t3_z);
    /* Calculate the following CrossProducts: */
    /* AFxAB */
    answer1_x = (af2 * ab3) - (af3 * ab2);
    answer1_y = (af3 * ab1) - (af1 * ab3);
    answer1_z = (af1 * ab2) - (af2 * ab1);
    /*      printf("answer(AFxAB)= %f %f %f\n",answer1_x, answer1_y, answer1_z); */
    /*BFxBC */
    answer2_x = (bf2 * bc3) - (bf3 * bc2);
    answer2_y = (bf3 * bc1) - (bf1 * bc3);
    answer2_z = (bf1 * bc2) - (bf2 * bc1);
    /*      printf("answer(BFxBC)= %f %f %f\n",answer2_x, answer2_y, answer2_z); */
    /*CFxCA */
    answer3_x = (cf2 * ca3) - (cf3 * ca2);
    answer3_y = (cf3 * ca1) - (cf1 * ca3);
    answer3_z = (cf1 * ca2) - (cf2 * ca1);
    /*      printf("answer(CFxCA)= %f %f %f\n",answer3_x, answer3_y, answer3_z); */
    answer = 0.0;		/*initialize value */
    if (answer1_x > 0 && answer2_x > 0 && answer3_x > 0) {
	answer += 1.0;
    }
    else if (answer1_x < 0 && answer2_x < 0 && answer3_x < 0) {
	answer -= 1.0;
    }
    if (answer1_y > 0 && answer2_y > 0 && answer3_y > 0) {
	answer += 1.0;
    }
    else if (answer1_y < 0 && answer2_y < 0 && answer3_y < 0) {
	answer -= 1.0;
    }
    if (answer1_z > 0 && answer2_z > 0 && answer3_z > 0) {
	answer += 1.0;
    }
    else if (answer1_z < 0 && answer2_z < 0 && answer3_z < 0) {
	answer -= 1.0;
    }
    if (answer == 3 || answer == -3) {
	index = 1;
    }
    else if (point_x == t1_x && point_y == t1_y && point_z == t1_z) {
	index = 1;
    }
    else if (point_x == t2_x && point_y == t2_y && point_z == t2_z) {
	index = 1;
    }
    else if (point_x == t3_x && point_y == t3_y && point_z == t3_z) {
	index = 1;
    }
    else {
	index = 0;
    }
    return index;
}
