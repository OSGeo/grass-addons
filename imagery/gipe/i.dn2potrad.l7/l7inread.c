#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include <grass/gis.h>
#include <grass/glocale.h>

int l7_in_read(char *metfName, char *b1, char *b2, char *b3, char *b4,
	       char *b5, char *b61, char *b62, char *b7, char *b8,
	       double *lmin, double *lmax, double *qcalmin, double *qcalmax,
	       double *sun_elevation, double *sun_azimuth, int *day,
	       int *month, int *year)
{
    FILE *f;

    char s[1000], *ptr;

    int i = 0;

    char *p;

    char band1[80], band2[80], band3[80];

    char band4[80], band5[80], band61[80];

    char band62[80], band7[80], band8[80];	/*Load .tif names */

    if ((f = fopen(metfName, "r")) == NULL) {
	G_fatal_error(_(".met file [%s] not found, are you in the proper directory?"),
		      metfName);
    }

    while (fgets(s, 1000, f) != NULL) {
	ptr = strstr(s, "ACQUISITION_DATE");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =-");
	    *year = atoi(p);
	    p = strtok(NULL, "-");
	    *month = atoi(p);
	    p = strtok(NULL, "-");
	    *day = atoi(p);
	}
	ptr = strstr(s, "BAND1_FILE_NAME");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =\"");
	    snprintf(band1, 80, "%s", p);
	}
	ptr = strstr(s, "BAND2_FILE_NAME");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =\"");
	    snprintf(band2, 80, "%s", p);
	}
	ptr = strstr(s, "BAND3_FILE_NAME");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =\"");
	    snprintf(band3, 80, "%s", p);
	}
	ptr = strstr(s, "BAND4_FILE_NAME");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =\"");
	    snprintf(band4, 80, "%s", p);
	}
	ptr = strstr(s, "BAND5_FILE_NAME");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =\"");
	    snprintf(band5, 80, "%s", p);
	}
	ptr = strstr(s, "BAND61_FILE_NAME");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =\"");
	    snprintf(band61, 80, "%s", p);
	}
	ptr = strstr(s, "BAND62_FILE_NAME");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =\"");
	    snprintf(band62, 80, "%s", p);
	}
	ptr = strstr(s, "BAND7_FILE_NAME");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =\"");
	    snprintf(band7, 80, "%s", p);
	}
	ptr = strstr(s, "BAND8_FILE_NAME");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =\"");
	    snprintf(band8, 80, "%s", p);
	}
	ptr = strstr(s, "SUN_AZIMUTH");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    *sun_azimuth = atof(p);

	}
	ptr = strstr(s, "SUN_ELEVATION");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    *sun_elevation = atof(p);

	}
	ptr = strstr(s, "\tLMAX_BAND1");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmax[0] = atof(p);
	}
	ptr = strstr(s, "\tLMIN_BAND1");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmin[0] = atof(p);
	}
	ptr = strstr(s, "\tLMAX_BAND2");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmax[1] = atof(p);
	}
	ptr = strstr(s, "\tLMIN_BAND2");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmin[1] = atof(p);
	}
	ptr = strstr(s, "\tLMAX_BAND3");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmax[2] = atof(p);
	}
	ptr = strstr(s, "\tLMIN_BAND3");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmin[2] = atof(p);
	}
	ptr = strstr(s, "\tLMAX_BAND4");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmax[3] = atof(p);
	}
	ptr = strstr(s, "\tLMIN_BAND4");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmin[3] = atof(p);
	}
	ptr = strstr(s, "\tLMAX_BAND5");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmax[4] = atof(p);
	}
	ptr = strstr(s, "\tLMIN_BAND5");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmin[4] = atof(p);
	}
	ptr = strstr(s, "\tLMAX_BAND61");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmax[5] = atof(p);
	}
	ptr = strstr(s, "\tLMIN_BAND61");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmin[5] = atof(p);
	}
	ptr = strstr(s, "\tLMAX_BAND62");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmax[6] = atof(p);
	}
	ptr = strstr(s, "\tLMIN_BAND62");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmin[6] = atof(p);
	}
	ptr = strstr(s, "\tLMAX_BAND7");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmax[7] = atof(p);
	}
	ptr = strstr(s, "\tLMIN_BAND7");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmin[7] = atof(p);
	}
	ptr = strstr(s, "\tLMAX_BAND8");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmax[8] = atof(p);
	}
	ptr = strstr(s, "\tLMIN_BAND8");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    lmin[8] = atof(p);
	}
	ptr = strstr(s, "QCALMAX_BAND1");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmax[0] = atof(p);
	}
	ptr = strstr(s, "QCALMIN_BAND1");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmin[0] = atof(p);
	}
	ptr = strstr(s, "QCALMAX_BAND2");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmax[1] = atof(p);
	}
	ptr = strstr(s, "QCALMIN_BAND2");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmin[1] = atof(p);
	}
	ptr = strstr(s, "QCALMAX_BAND3");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmax[2] = atof(p);
	}
	ptr = strstr(s, "QCALMIN_BAND3");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmin[2] = atof(p);
	}
	ptr = strstr(s, "QCALMAX_BAND4");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmax[3] = atof(p);
	}
	ptr = strstr(s, "QCALMIN_BAND4");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmin[3] = atof(p);
	}
	ptr = strstr(s, "QCALMAX_BAND5");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmax[4] = atof(p);
	}
	ptr = strstr(s, "QCALMIN_BAND5");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmin[4] = atof(p);
	}
	ptr = strstr(s, "QCALMAX_BAND61");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmax[5] = atof(p);
	}
	ptr = strstr(s, "QCALMIN_BAND61");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmin[5] = atof(p);
	}
	ptr = strstr(s, "QCALMAX_BAND62");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmax[6] = atof(p);
	}
	ptr = strstr(s, "QCALMIN_BAND62");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmin[6] = atof(p);
	}
	ptr = strstr(s, "QCALMAX_BAND7");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmax[7] = atof(p);
	}
	ptr = strstr(s, "QCALMIN_BAND7");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmin[7] = atof(p);
	}
	ptr = strstr(s, "QCALMAX_BAND8");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmax[8] = atof(p);
	}
	ptr = strstr(s, "QCALMIN_BAND8");
	if (ptr != NULL) {
	    p = strtok(ptr, " =");
	    p = strtok(NULL, " =");
	    qcalmin[8] = atof(p);
	}
    }

    snprintf(b1, 80, "%s", band1);
    snprintf(b2, 80, "%s", band2);
    snprintf(b3, 80, "%s", band3);
    snprintf(b4, 80, "%s", band4);
    snprintf(b5, 80, "%s", band5);
    snprintf(b61, 80, "%s", band61);
    snprintf(b62, 80, "%s", band62);
    snprintf(b7, 80, "%s", band7);
    snprintf(b8, 80, "%s", band8);
    /*      printf("year = %i\n", year);
       printf("month = %i\n", month);
       printf("day = %i\n", day);
       printf("sun azimuth = %f\n", sun_azimuth);
       printf("sun elevation = %f\n", sun_elevation);
       for (i=0;i<MAXFILES;i++){
       printf("lmin[%i]=%f\n",i,lmin[i]);
       printf("lmax[%i]=%f\n",i,lmax[i]);
       printf("qcalmin[%i]=%f\n",i,qcalmin[i]);
       printf("qcalmax[%i]=%f\n",i,qcalmax[i]);
       }
     */
    (void)fclose(f);
    return;
}
