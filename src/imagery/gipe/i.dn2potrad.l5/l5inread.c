#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include <grass/gis.h>
#include <grass/glocale.h>

int l5_in_read(char *metfName, int *path, int *row, double *latitude,
	       double *longitude, double *sun_elevation, double *sun_azimuth,
	       int *c_year, int *c_month, int *c_day, int *day, int *month,
	       int *year, double *decimal_hour)
{
    FILE *f;

    char s[1000], *ptr;

    int i = 0;

    char *p;

    int hour, minute;

    float second;

    if ((f = fopen(metfName, "r")) == NULL) {
	G_fatal_error(_("NLAPS report file [%s] not found, are you in the proper directory?"),
		      metfName);
    }

    while (fgets(s, 1000, f) != NULL) {
	ptr = strstr(s, "Strip no.");
	if (ptr != NULL) {
	    p = strtok(ptr, ":");
	    p = strtok(NULL, " ");
	    *path = atoi(p);
	    p = strtok(NULL, " ");
	    p = strtok(NULL, "Start Row no.:");
	    *row = atoi(p);
	}
	ptr = strstr(s, "center lat");
	if (ptr != NULL) {
	    p = strtok(ptr, ":");
	    p = strtok(NULL, " ");
	    *latitude = atof(p);
	    p = strtok(NULL, " deg");
	    p = strtok(NULL, " Scene center long:");
	    *longitude = atof(p);
	}
	ptr = strstr(s, "Sun Elevation");
	if (ptr != NULL) {
	    p = strtok(ptr, ":");
	    p = strtok(NULL, " ");
	    *sun_elevation = atof(p);
	    p = strtok(NULL, " deg");
	    p = strtok(NULL, "Sun Azimuth:");
	    *sun_azimuth = atof(p);
	}
	ptr = strstr(s, "center date");
	if (ptr != NULL) {
	    p = strtok(ptr, ":");
	    p = strtok(NULL, " ");
	    *year = atoi(p);
	    p = strtok(NULL, " ");
	    *month = atoi(p);
	    p = strtok(NULL, " ");
	    *day = atoi(p);
	    p = strtok(NULL, " Scene center time:");
	    hour = atoi(p);
	    p = strtok(NULL, ":");
	    minute = atoi(p);
	    p = strtok(NULL, ":");
	    second = atof(p);
	}
	ptr = strstr(s, "Completion date");
	if (ptr != NULL) {
	    p = strtok(ptr, ":");
	    p = strtok(NULL, " ");
	    *c_year = atoi(p);
	    p = strtok(NULL, " ");
	    *c_month = atoi(p);
	    p = strtok(NULL, " ");
	    *c_day = atoi(p);
	}
    }

    /*      printf("year = %i\n", year);
       printf("month = %i\n", month);
       printf("day = %i\n", day);
       printf("sun azimuth = %f\n", sun_azimuth);
       printf("sun elevation = %f\n", sun_elevation);
       printf("latitude = %f\n", latitude);
       printf("longitude = %f\n", longitude);
     */
    (void)fclose(f);
    return;
}
