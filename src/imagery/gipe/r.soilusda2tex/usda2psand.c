#include<stdio.h>

/* From FAOSOIL CD, after USDA 1951, p209 */

double usda2psand(int texture)
{
    double psand;

    double psilt;

    double pclay;

    if (texture == 0) {
	/*              printf("clay\n"); */
	psand = 0.2;
	psilt = 0.2;
	pclay = 0.8;
    }
    else if (texture == 1) {
	/*              printf("sandy clay\n"); */
	psand = 0.5;
	psilt = 0.1;
	pclay = 0.4;
    }
    else if (texture == 2) {
	/*              printf("silty clay\n"); */
	psand = 0.05;
	psilt = 0.5;
	pclay = 0.45;
    }
    else if (texture == 3) {
	/*              printf("sandy clay loam\n"); */
	psand = 0.6;
	psilt = 0.15;
	pclay = 0.25;
    }
    else if (texture == 4) {
	/*              printf("clay loam\n"); */
	psand = 0.3;
	psilt = 0.35;
	pclay = 0.35;
    }
    else if (texture == 5) {
	/*              printf("silty clay loam\n"); */
	psand = 0.1;
	psilt = 0.55;
	pclay = 0.35;
    }
    else if (texture == 6) {
	/*              printf("sand\n"); */
	psand = 0.9;
	psilt = 0.05;
	pclay = 0.05;
    }
    else if (texture == 7) {
	/*              printf("loamy sand\n"); */
	psand = 0.85;
	psilt = 0.05;
	pclay = 0.1;
    }
    else if (texture == 8) {
	/*              printf("sandy loam\n"); */
	psand = 0.65;
	psilt = 0.25;
	pclay = 0.1;
    }
    else if (texture == 9) {
	/*              printf("loam\n"); */
	psand = 0.4;
	psilt = 0.4;
	pclay = 0.2;
    }
    else if (texture == 10) {
	/*              printf("silt loam\n"); */
	psand = 0.2;
	psilt = 0.65;
	pclay = 0.15;
    }
    else if (texture == 11) {
	/*              printf("silt\n"); */
	psand = 0.05;
	psilt = 0.9;
	pclay = 0.05;
    }
    else {
	/*printf("i am confused here...Can you do it yourself please?\n"); */
    }
    return psand;
}
