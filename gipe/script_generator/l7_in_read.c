/*Copyright (C) Yann Chemin
ychemin@gmail.com
Asian Institute of Technology,
PO Box 4, Klong Luang,
12120 Pathum Thani,
Thailand

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; 
version 2.1 of the License.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

Thanks to Brad Douglas <rez@touchofmadness.com> to fix the .tif filename issue
*/

#include<stdio.h>
#include<stdlib.h>
#include<string.h>

#define MAXFILES 9
int date2doy(int day, int month, int year);

void usage(){
	printf("Usage: ./l7_in_read l7metfile\n");
	printf("\nThis program is parsing Landsat 7 ETM+ metadata file (.met) for useful information for further processing and returns it to stdout and also issues the same as shell script variables\n");
	printf("Conventional mapping of Landsat 7 ETM+ L1B bands is 1,2,3,4,5,6L,6H,7,8Pan\n");
	printf("Available variables are:\nday, month, year, doy, sun_elevation, sun_azimuth\nlmin0 (for band 1) to lmin8 (for band 9), same for lmax[0-8], qcalmin[0-8], qcalmax[0-8]\n");
}

int main(int argc, char *argv[])
{
	FILE *f;
	char s[1000], *ptr;
	int i=0;
	char *p;

	char *metfName;

	char	b1[80],b2[80],b3[80];
	char	b4[80],b5[80],b61[80];
	char	b62[80],b7[80],b8[80]; //Load .tif file names

	double	lmin[MAXFILES]={0.0};
	double	lmax[MAXFILES]={0.0};
	double	qcalmin[MAXFILES]={0.0};
	double	qcalmax[MAXFILES]={0.0};
	double	kexo[MAXFILES]={0.0};
	double	sun_elevation=0.0, sun_azimuth=0.0;
	int	day=0, month=0, year=0, doy=0;

//	char	*sys_day,*sys_month,*sys_year;
//	char	*sys_doy,*sys_sun_elevation,*sys_sun_azimuth;
//	char	*sys_lmin[MAXFILES];
//	char	*sys_lmax[MAXFILES];
//	char	*sys_qcalmin[MAXFILES];
//	char	*sys_qcalmax[MAXFILES];


	if(argc < 1){
		usage();
	}

	metfName = argv[1];

	f=fopen(metfName,"r");

	if (!f)
	return 1;

//	printf("1\n");
	while (fgets(s,1000,f)!=NULL)
	{
	//	printf("2%s\n",s);
		ptr = strstr(s, "ACQUISITION_DATE");
		if (ptr != NULL)
		{
	//		printf("3\t");
			p = strtok(ptr, " =");
			p = strtok(NULL, " =-");
			year = atoi(p);
	//		printf("4\t");
			p = strtok(NULL, "-");
			month = atoi(p);
	//		printf("5\t");
			p = strtok(NULL, "-");
			day = atoi(p);
	//		printf("6\n");
		}
		ptr = strstr(s, "BAND1_FILE_NAME");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\"");
		//	printf("b1=%s\n",p);
			snprintf(b1, 80, "%s", p);
		//	printf("b1=%s\n",band1);
		}
		ptr = strstr(s, "BAND2_FILE_NAME");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\"");
		//	printf("b2=%s\n",p);
			snprintf(b2, 80, "%s", p);
		//	printf("b2=%s\n",band2);
		}
		ptr = strstr(s, "BAND3_FILE_NAME");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\"");
			snprintf(b3, 80, "%s", p);
		}
		ptr = strstr(s, "BAND4_FILE_NAME");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\"");
			snprintf(b4, 80, "%s", p);
		}
		ptr = strstr(s, "BAND5_FILE_NAME");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\"");
			snprintf(b5, 80, "%s", p);
		}
		ptr = strstr(s, "BAND61_FILE_NAME");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\"");
			snprintf(b61, 80, "%s", p);
		}
		ptr = strstr(s, "BAND62_FILE_NAME");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\"");
			snprintf(b62, 80, "%s", p);
		}
		ptr = strstr(s, "BAND7_FILE_NAME");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\"");
			snprintf(b7, 80, "%s", p);
		}
		ptr = strstr(s, "BAND8_FILE_NAME");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\"");
			snprintf(b8, 80, "%s", p);
		}
		ptr = strstr(s, "SUN_AZIMUTH");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			sun_azimuth = atof(p);
		}
		ptr = strstr(s, "SUN_ELEVATION");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			sun_elevation = atof(p);
		}
		ptr = strstr(s, "\tLMAX_BAND1");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmax[0] = atof(p);
		}
		ptr = strstr(s, "\tLMIN_BAND1");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmin[0] = atof(p);
		}
		ptr = strstr(s, "\tLMAX_BAND2");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmax[1] = atof(p);
		}
		ptr = strstr(s, "\tLMIN_BAND2");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmin[1] = atof(p);
		}
		ptr = strstr(s, "\tLMAX_BAND3");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmax[2] = atof(p);
		}
		ptr = strstr(s, "\tLMIN_BAND3");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmin[2] = atof(p);
		}
		ptr = strstr(s, "\tLMAX_BAND4");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmax[3] = atof(p);
		}
		ptr = strstr(s, "\tLMIN_BAND4");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmin[3] = atof(p);
		}
		ptr = strstr(s, "\tLMAX_BAND5");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmax[4] = atof(p);
		}
		ptr = strstr(s, "\tLMIN_BAND5");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmin[4] = atof(p);
		}
		ptr = strstr(s, "\tLMAX_BAND61");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmax[5] = atof(p);
		}
		ptr = strstr(s, "\tLMIN_BAND61");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmin[5] = atof(p);
		}
		ptr = strstr(s, "\tLMAX_BAND62");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmax[6] = atof(p);
		}
		ptr = strstr(s, "\tLMIN_BAND62");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmin[6] = atof(p);
		}
		ptr = strstr(s, "\tLMAX_BAND7");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmax[7] = atof(p);
		}
		ptr = strstr(s, "\tLMIN_BAND7");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmin[7] = atof(p);
		}
		ptr = strstr(s, "\tLMAX_BAND8");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmax[8] = atof(p);
		}
		ptr = strstr(s, "\tLMIN_BAND8");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			lmin[8] = atof(p);
		}
		ptr = strstr(s, "QCALMAX_BAND1");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmax[0] = atof(p);
		}
		ptr = strstr(s, "QCALMIN_BAND1");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmin[0] = atof(p);
		}
		ptr = strstr(s, "QCALMAX_BAND2");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmax[1] = atof(p);
		}
		ptr = strstr(s, "QCALMIN_BAND2");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmin[1] = atof(p);
		}
		ptr = strstr(s, "QCALMAX_BAND3");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmax[2] = atof(p);
		}
		ptr = strstr(s, "QCALMIN_BAND3");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmin[2] = atof(p);
		}
		ptr = strstr(s, "QCALMAX_BAND4");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmax[3] = atof(p);
		}
		ptr = strstr(s, "QCALMIN_BAND4");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmin[3] = atof(p);
		}
		ptr = strstr(s, "QCALMAX_BAND5");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmax[4] = atof(p);
		}
		ptr = strstr(s, "QCALMIN_BAND5");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmin[4] = atof(p);
		}
		ptr = strstr(s, "QCALMAX_BAND61");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmax[5] = atof(p);
		}
		ptr = strstr(s, "QCALMIN_BAND61");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmin[5] = atof(p);
		}
		ptr = strstr(s, "QCALMAX_BAND62");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmax[6] = atof(p);
		}
		ptr = strstr(s, "QCALMIN_BAND62");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmin[6] = atof(p);
		}
		ptr = strstr(s, "QCALMAX_BAND7");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmax[7] = atof(p);
		}
		ptr = strstr(s, "QCALMIN_BAND7");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmin[7] = atof(p);
		}
		ptr = strstr(s, "QCALMAX_BAND8");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmax[8] = atof(p);
		}
		ptr = strstr(s, "QCALMIN_BAND8");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =");
			qcalmin[8] = atof(p);
		}
	}

	printf("year = %i\t", year);
	printf("month = %i\t", month);
	printf("day = %i\t", day);
	
	doy = date2doy(day,month,year);
	printf("doy = %i\n",doy);

	printf("sun azimuth = %f\t", sun_azimuth);
	printf("sun elevation = %f\n", sun_elevation);
	printf("\n");

	printf("b1=%s\n",b1);
	printf("b2=%s\n",b2);
	printf("b3=%s\n",b3);
	printf("b4=%s\n",b4);
	printf("b5=%s\n",b5);
	printf("b61=%s\n",b61);
	printf("b62=%s\n",b62);
	printf("b7=%s\n",b7);
	printf("b8=%s\n",b8);


	for (i=0;i<MAXFILES;i++){
		printf("lmin%i=%7.3f\t",i,lmin[i]);
		printf("lmax%i=%7.3f\t",i,lmax[i]);
		printf("qcalmin%i=%7.3f\t",i,qcalmin[i]);
		printf("qcalmax%i=%7.3f\n",i,qcalmax[i]);
	}
/*
	sprintf(sys_day,"year=",year);
	system(sys_day);

	sprintf(sys_month,"month=",month);
	system(sys_month);

	sprintf(sys_year,"day=",day);
	system(sys_year);

	sprintf(sys_sun_azimuth,"sun_azimuth=",sun_azimuth);
	system(sys_sun_azimuth);

	sprintf(sys_sun_elevation,"sun_elevation=",sun_elevation);
	system(sys_sun_elevation);

	for (i=0;i<MAXFILES;i++){
		sprintf(sys_lmin[i],"lmin%i=%f\n",i,lmin[i]);
		sprintf(sys_lmax[i],"lmax%i=%f\n",i,lmax[i]);
		sprintf(sys_qcalmin[i],"qcalmin%i=%f\n",i,qcalmin[i]);
		sprintf(sys_qcalmax[i],"qcalmax%i=%f\n",i,qcalmax[i]);
		system(sys_lmin[i]);
		system(sys_lmax[i]);
		system(sys_qcalmin[i]);
		system(sys_qcalmax[i]);
	}
*/
	(void)fclose(f);
	return;
}

/*********************************************/
/*This program converts day/month/year to doy*/
/*********************************************/
/*********************************************/

int date2doy(int day, int month, int year)
{
	int leap=0;
	int day_month_tot=0;
	int doy;

	doy=0;	

/*printf("Date is %i/%i/%i\n", day, month, year);*/

	if (month == 1) {
		day_month_tot = 0;
	}
	else if (month == 2) {
		day_month_tot = 31;
	}
	else if (month == 3) {
		day_month_tot = 59;
	}
	else if (month == 4) {
		day_month_tot = 90;
	}
	else if (month == 5) {
		day_month_tot = 120;
	}
	else if (month == 6) {
		day_month_tot = 151;
	}
	else if (month == 7) {
		day_month_tot = 181;
	}
	else if (month == 8) {
		day_month_tot = 212;
	}
	else if (month == 9) {
		day_month_tot = 243;
	}
	else if (month == 10) {
		day_month_tot = 273;
	}
	else if (month == 11) {
		day_month_tot = 304;
	}
	else if (month == 12) {
		day_month_tot = 334;
	}
	
	/* Leap year if dividing by 4 leads % 0.0*/
	
	if (year/4*4 == year) {
		leap = 1;
	}
	
	doy=day_month_tot+day;
	if(doy>59){
		doy=day_month_tot+day+leap;
	}

	return(doy);
}

