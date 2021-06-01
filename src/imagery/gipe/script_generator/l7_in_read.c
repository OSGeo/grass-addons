/*Copyright (C) Yann Chemin
yann.chemin@gmail.com
GRASS Development Team

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

/* This is auto-generating an image processing script for GRASS GIS.
 * It is created by extracting useful information from the .met metadata
 * file of Landsat 7
 * It runs several GRASS GIS modules to calculate (hopefully) 
 * automagically ET Potential and more ET types...
 * It assumes you just downloaded *.gz Landsat images from public 
 * repositories such as www.landsat.org or other and run this code 
 * in that directory from the GRASS GIS shell
 */

#include<stdio.h>
#include<stdlib.h>
#include<string.h>

#define MAXFILES 9
int date2doy(int day, int month, int year);

void usage(){
	printf("Usage: ./l7_in_read l7metfile\n");
	printf("\nThis program is run from WITHIN GRASS GIS and is parsing Landsat 7 ETM+ metadata file (.met) for useful information for ETPOT processing and issues GRASS GIS modules commands into temp.txt and runs it\n\n\nCAREFUL! It assumes that the directory where it is run has freshly downloaded Landsat 7 .gz files with their accompanying .met file!\n\n");
	printf("Conventional mapping of Landsat 7 ETM+ L1B bands is 1,2,3,4,5,6L,6H,7,8Pan\n");
	printf("Available variables are:\nday, month, year, doy, sun_elevation, sun_azimuth\n b1 to b7 for the .tif file names\n");
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
	char	b62[80],b7[80],b8[80]; /*Load .tif file names*/
	char	path[80],row[80]; /*load path and row of L7*/
	char	basedate[80];/*p127r05020001104*/

	double	lmin[MAXFILES]={0.0};
	double	lmax[MAXFILES]={0.0};
	double	qcalmin[MAXFILES]={0.0};
	double	qcalmax[MAXFILES]={0.0};
	double	kexo[MAXFILES]={0.0};
	double	sun_elevation=0.0, sun_azimuth=0.0;
	int	day=0, month=0, year=0, doy=0;
	char	char_day[80],char_month[80];

	char	sys_metfName[80];
	char	sys_day[80],sys_month[80],sys_year[80];
	char	sys_doy[80],sys_sun_elevation[80],sys_sun_azimuth[80];
	char	sys_lmin[80];
	char	sys_lmax[80];
	char	sys_qcalmin[80];
	char	sys_qcalmax[80];
	char	sys_basedate[80];/*catenate of path and row (i.e.p127r050)*/
	char	sys_b1[80],sys_b2[80],sys_b3[80];
	char	sys_0[100],sys_00[100];
	char	sys_b4[80],sys_b5[80],sys_b61[80];
	char	sys_b62[80],sys_b7[80],sys_b8[80]; /*Load .tif file names*/
	char	sys_1[1000],sys_2[1000],sys_3[1000],sys_4[1000];
	char	sys_5[1000],sys_6[1000],sys_7[1000],sys_8[1000];
	char	sys_9[1000],sys_10[1000],sys_100[1000];
	char	sys_11[1000],sys_12[1000],sys_13[1000],sys_14[1000];
	char	sys_15[1000],sys_16[1000],sys_17[1000],sys_18[1000];
	char	sys_19[1000],sys_20[1000],sys_21[1000],sys_22[1000];
	char	sys_23[1000],sys_24[1000],sys_25[1000],sys_26[1000];
	char	sys_27[1000],sys_28[1000],sys_29[1000],sys_30[1000];
	char	sys_31[1000],sys_32[1000],sys_33[1000],sys_34[1000];

	if(argc < 1){
		usage();
	}

	metfName = argv[1];

	f=fopen(metfName,"r");

	if (!f)
	return 1;

	while (fgets(s,1000,f)!=NULL)
	{
		ptr = strstr(s, "ACQUISITION_DATE");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =-");
			year = atoi(p);
			p = strtok(NULL, "-");
			month = atoi(p);
			p = strtok(NULL, "-");
			day = atoi(p);
		}
		ptr = strstr(s, "WRS_PATH");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\n");
/* 			printf("path=%s\n",p);*/
			snprintf(path, 80, "%s", p);
/* 			printf("path=%s\n",path);*/
		}
		ptr = strstr(s, "WRS_ROW");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\n");
/* 			printf("row=%s\n",p);*/
			snprintf(row, 80, "%s", p);
/* 			printf("row=%s\n",row);*/
		}
		ptr = strstr(s, "BAND1_FILE_NAME");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\"");
		/*	printf("b1=%s\n",p);*/
			snprintf(b1, 80, "%s", p);
		/*	printf("b1=%s\n",band1);*/
		}
		ptr = strstr(s, "BAND2_FILE_NAME");
		if (ptr != NULL)
		{
			p = strtok(ptr, " =");
			p = strtok(NULL, " =\"");
		/*	printf("b2=%s\n",p);*/
			snprintf(b2, 80, "%s", p);
		/*	printf("b2=%s\n",band2);*/
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


	snprintf(sys_year,80,"year=%d",year);
	system(sys_year);

	snprintf(sys_month,80,"month=%d",month);
	system(sys_month);

	snprintf(sys_day,80,"day=%d",day);
	system(sys_day);

	snprintf(sys_sun_azimuth,80,"sun_azimuth=%f",sun_azimuth);
	system(sys_sun_azimuth);

	snprintf(sys_sun_elevation,80,"sun_elevation=%f",sun_elevation);
	system(sys_sun_elevation);

/* 	for (i=0;i<MAXFILES;i++){
 		sprintf(sys_lmin[i],"lmin%i=%f\n",i,lmin[i]);
 		sprintf(sys_lmax[i],"lmax%i=%f\n",i,lmax[i]);
 		sprintf(sys_qcalmin[i],"qcalmin%i=%f\n",i,qcalmin[i]);
 		sprintf(sys_qcalmax[i],"qcalmax%i=%f\n",i,qcalmax[i]);
 		system(sys_lmin[i]);
 		system(sys_lmax[i]);
 		system(sys_qcalmin[i]);
 		system(sys_qcalmax[i]);
 	}*/

	if(month<10){
		snprintf(char_month,80,"0%d",month);
	} else {
		snprintf(char_month,80,"%d",month);
	}
	if(day<10){
		snprintf(char_day,80,"0%d",day);
	} else {
		snprintf(char_day,80,"%d",day);
	}
	snprintf(basedate,80,"p%sr%s%d%s%s",path,row,year,char_month,char_day);


	/*Start Processing*/
	system("echo \"#!/bin/bash\" > temp.txt");
	system("echo \"\" >> temp.txt");
	system("echo \"#This is an auto-generated script by l7inread_ingrass().\n#It is created by a C code that extract useful information from the .met metadata file of Landsat 7\n#It runs several GRASS GIS modules to calculate (hopefully) automagically ET Potential\n\n#Q: My script does not run because i am not running it from inside GRASS GIS\n#A: It will not work from outside GRASS GIS (Actually, there might be a way :P, have to ask the dev-ML...) \" >> temp.txt");
	/*ungzip the L7 files*/
	system("echo \"\" >> temp.txt");
	system("echo \"#UNGZIP ALL LANDSAT BANDS\" >> temp.txt");
	system("echo \"for file in *.gz; do gzip -d \\$file ; done\" >> temp.txt");
	/*import the Landsat 7 files*/
	system("echo \"\" >> temp.txt");
	system("echo \"#IMPORT IN GRASS GIS\" >> temp.txt");
	sprintf(sys_0,"echo \"for file in *10.tif; do r.in.gdal input=\\$file output=\\$file title=Landsat7ETM\\$file location=landsat\\%s ; done\" >> temp.txt",basedate);
	system(sys_0);
	sprintf(sys_00,"echo \"g.mapset location=landsat\\%s mapset=PERMANENT\" >> temp.txt", basedate);
	system(sys_00);
	system("echo \"for file in *.tif; do r.in.gdal input=\\$file output=\\$file title=Landsat7ETM\\$file ; done\" >> temp.txt");
	/*Set region to Temperature map*/
	system("echo \"\" >> temp.txt");
	system("echo \"#SET REGION TO TEMPERATURE MAP\" >> temp.txt");
	snprintf(sys_b61,80,"echo \"g.region rast=%s\" >> temp.txt",b61);
	system(sys_b61);
	/*export met file name to envt var*/
/*	snprintf(sys_metfName,80,"echo \"inpmetF=%s\" >> temp.txt",metfName);
	system(sys_metfName);*/
	/*Create a base variable*/
/*	snprintf(sys_basedate,80,"echo \"basedate=%s\" >> temp.txt",basedate);
	system(sys_basedate);*/
	/*calibrate DN to TOA Reflectance*/
	system("echo \"\" >> temp.txt");
	system("echo \"#DN2REF\" >> temp.txt");
	snprintf(sys_1,1000,"echo \"i.dn2full.l7 metfile=%s output=%s --overwrite ; r.null map=%s.61 setnull=-999.99 ; r.null map=%s.62 setnull=-999.99 \" >> temp.txt",metfName,basedate,basedate,basedate);
	system(sys_1);
	/*Calculate Albedo*/
	system("echo \"\" >> temp.txt");
	system("echo \"#ALBEDO\" >> temp.txt");
	snprintf(sys_2,1000,"echo \"i.albedo -l input=%s.1,%s.2,%s.3,%s.4,%s.5,%s.7 output=%s.albedo --overwrite\" >> temp.txt", basedate, basedate, basedate, basedate, basedate, basedate, basedate);
	system(sys_2);
	snprintf(sys_3,1000,"r.null map=%s.albedo setnull=0.0\" >> temp.txt",basedate);
	system(sys_3);
	/*Calculate Latitude*/
	system("echo \"\" >> temp.txt");
	system("echo \"#LATITUDE, DOY, TSW\" >> temp.txt");
	snprintf(sys_4,1000,"echo \"i.latitude input=%s.albedo latitude=%s.latitude --overwrite ; i.longitude input=%s.albedo longitude=%s.longitude --overwrite ; r.mapcalc %s.doy=%d ; r.mapcalc %s.tsw=0.7\" >> temp.txt", basedate, basedate, basedate, basedate, basedate, doy, basedate);
	/*Create a doy layer*/
	system(sys_4);
	system("echo \"\" >> temp.txt");
	/*DOWNLOAD/IMPORT SRTM*/
	system("echo \"#DOWNLOAD SRTM DEM 90m unfinished\" >> temp.txt");
	system("echo \"\" >> temp.txt");
	sprintf(sys_25,"echo \"wget -c ftp://ftp.glcf.umiacs.umd.edu/glcf/SRTM/WRS2_Tiles/p%s/SRTM_u03_p%sr%s/SRTM_u03_p%sr%s.tif.gz \" >> temp.txt",path,path,row,path,row);
	system(sys_25);
	system("echo \"\" >> temp.txt");
	system("echo \"#IMPORT SRTM DEM 90m unfinished\" >> temp.txt");
	system("echo \"\" >> temp.txt");
	sprintf(sys_26,"echo \"gzip -d SRTM_u03_p%sr%s.tif.gz \" >> temp.txt",path,row);
	system(sys_26);
	system("echo \"\" >> temp.txt");
	sprintf(sys_27,"echo \"r.in.gdal -o input=SRTM_u03_p%sr%s.tif output=%s.dem title=SRTM_u03\" >> temp.txt",path,row,basedate);
	system(sys_27);
	system("echo \"\" >> temp.txt");
	sprintf(sys_27,"echo \"r.slope.aspect elevation=%s.dem slope=%s.slope aspect=%s.aspect\" >> temp.txt",basedate,basedate,basedate);
	system(sys_27);
	/*Calculate ETPOT (and Rnetd for future ETa calculations)*/
	system("echo \"\" >> temp.txt");
	system("echo \"#ETPOT\" >> temp.txt");
	snprintf(sys_5,1000,"echo \"i.evapo.potrad -r albedo=%s.albedo tempk=%s.61 lat=%s.latitude doy=%s.doy tsw=%s.tsw etpot=%s.etpot rnetd=%s.rnetd --overwrite ; r.null map=%s.rnetd setnull=-999.99 \" >> temp.txt", basedate, basedate, basedate, basedate, basedate, basedate, basedate, basedate, basedate, basedate);
	system(sys_5);
	snprintf(sys_7,1000,"echo \"r.colors map=%s.etpot color=grey ; r.null map=%s.etpot setnull=-999.99\" >> temp.txt", basedate, basedate);
	system(sys_7);
	system("echo \"\" >> temp.txt");
	system("echo \"#NDVI\" >> temp.txt");
	/*Calculate NDVI*/
	snprintf(sys_8,1000,"echo \"i.vi viname=ndvi red=%s.3 nir=%s.4 vi=%s.ndvi --overwrite ; r.null map=%s.ndvi setnull=-1.0 ; r.colors map=%s.ndvi rules=ndvi\" >> temp.txt",basedate,basedate,basedate,basedate,basedate);
	system(sys_8);
	snprintf(sys_16,1000,"echo \"i.vi viname=savi red=%s.3 nir=%s.4 vi=%s.savi --overwrite ; r.null map=%s.savi setnull=-1.0 ; r.colors map=%s.savi rules=ndvi\" >> temp.txt",basedate,basedate,basedate,basedate,basedate);
	system(sys_16);

	/*Calculate ETa after Two-Source Algorithm (Chen et al., 2005)*/
	system("echo \"\" >> temp.txt");
	system("echo \"#TWO-SOURCE ALGORITHM\" >> temp.txt");
	system("echo \"\" >> temp.txt");
	system("echo \"r.mapcalc u2=2.0\" >> temp.txt");
	system("echo \"r.mapcalc z0s=0.002\" >> temp.txt");
	sprintf(sys_15,"echo \"i.eb.z0m -h savi=%s.savi coef=0.1 z0m=%s.z0m z0h=%s.z0h --overwrite\" >> temp.txt",basedate,basedate,basedate);
	system(sys_15);
	system("echo \"\" >> temp.txt");
	sprintf(sys_9,"echo \"i.sunhours doy=%s.doy lat=%s.latitude sunh=%s.sunh --overwrite\" >> temp.txt",basedate,basedate,basedate);
	system(sys_9);
	sprintf(sys_11,"echo \"r.mapcalc \"%s.phi=%f\"\" >> temp.txt",basedate,sun_elevation);
	system(sys_11);
	system("echo \"\" >> temp.txt");
	sprintf(sys_12," echo \"i.sattime doy=%s.doy lat=%s.latitude long=%s.longitude sun_elev=%s.phi sath=%s.sath --overwrite\" >> temp.txt",basedate,basedate,basedate,basedate,basedate);
	system(sys_12);
	sprintf(sys_13," echo \"i.eb.deltat -w tempk=%s.61 delta=%s.delta --overwrite\" >> temp.txt",basedate,basedate);
	system(sys_13);
	sprintf(sys_18,"r.null map=%s.delta setnull=-999.99\" >> temp.txt",basedate,basedate,basedate,basedate);
	system(sys_18);
	system("echo \"\" >> temp.txt");
	sprintf(sys_14," echo \"r.mapcalc %s.tempka=%s.61+%s.delta\" >> temp.txt",basedate,basedate,basedate);
	system(sys_14);
	sprintf(sys_17," echo \"r.mapcalc %s.w=5.0\" >> temp.txt",basedate);
	system(sys_17);
	sprintf(sys_10,"echo \"i.evapo.TSA RNET=%s.rnetd FV=%s.ndvi TEMPK=%s.61 TEMPKA=%s.tempka ALB=%s.albedo NDVI=%s.ndvi UZ=u2 Z=2.0 Z0=%s.z0h Z0S=z0s W=%s.w TIME=%s.sath SUNH=%s.sunh output=%s.ETA_TSA --overwrite\" >> temp.txt",basedate,basedate,basedate,basedate,basedate,basedate,basedate,basedate,basedate,basedate,basedate);
	system(sys_10);
	system("echo \"\" >> temp.txt");
	/*Calculate ET Potential after Prestley and Taylor*/
	system("echo \"#PRESTLEY AND TAYLOR ET POTENTIAL\" >> temp.txt");
	system("echo \"\" >> temp.txt");
	sprintf(sys_19,"echo \"r.mapcalc %s.patm=1010.0; r.mapcalc %s.sunza=90.0-%s.phi\" >> temp.txt",basedate,basedate,basedate);
	system(sys_19);
	sprintf(sys_20,"echo \"i.emissivity ndvi=%s.ndvi emissivity=%s.e0 --overwrite\" >> temp.txt",basedate,basedate);
	system(sys_20);
	system("echo \"\" >> temp.txt");
	sprintf(sys_21,"echo \"i.eb.netrad albedo=%s.albedo ndvi=%s.ndvi tempk=%s.61 time=%s.sath dtair=%s.delta emissivity=%s.e0 tsw=%s.tsw doy=%s.doy sunzangle=%s.sunza rnet=%s.rnet --overwrite\" >> temp.txt",basedate,basedate,basedate,basedate,basedate,basedate,basedate,basedate,basedate,basedate);
	system(sys_21);
	system("echo \"\" >> temp.txt");
	sprintf(sys_22,"echo \"i.eb.g0 albedo=%s.albedo ndvi=%s.ndvi tempk=%s.61 rnet=%s.rnet time=%s.sath g0=%s.g0 --overwrite\" >> temp.txt",basedate,basedate,basedate,basedate,basedate,basedate);
	system(sys_22);
	system("echo \"\" >> temp.txt");
	sprintf(sys_23,"echo \"i.evapo.PT -z RNET=%s.rnetd G0=%s.g0 TEMPKA=%s.tempka PATM=%s.patm PT=1.26 output=%s.ETA_PT --overwrite\" >> temp.txt",basedate,basedate,basedate,basedate,basedate);
	system(sys_23);
	system("echo \"\" >> temp.txt");
	/*Calculate the Actual ET after Pawan (2004)*/
	system("echo \"#ACTUAL ET\" >> temp.txt");
	system("echo \"\" >> temp.txt");
	sprintf(sys_24,"echo \"i.eb.disp -s lai=%s.savi disp=%s.disp --overwrite\" >> temp.txt",basedate,basedate);
	system(sys_24);
	system("echo \"\" >> temp.txt");
	sprintf(sys_28,"echo \"r.colors map=%s.dem color=srtm\" >> temp.txt",basedate);
	system(sys_28);
	system("echo \"\" >> temp.txt");
	sprintf(sys_29,"echo \"i.eb.rohair dem=%s.dem tempka=%s.tempka rohair=%s.rohair --overwrite\" >> temp.txt",basedate,basedate,basedate);
	system(sys_29);
	system("echo \"\" >> temp.txt");
	sprintf(sys_30,"echo \"r.null map=%s.rohair setnull=-999.99\" >> temp.txt",basedate);
	system(sys_30);
	system("echo \"\" >> temp.txt");
	sprintf(sys_31,"echo \"i.eb.h_iter rohair=%s.rohair cp=1004.16 dtair=%s.delta tempk=%s.61 disp=%s.disp z0m=%s.z0m z0h=%s.z0h u2m=u2 h0=%s.h0 --overwrite; r.null map=%s.h0 setnull=-999.99 \" >> temp.txt",basedate,basedate,basedate,basedate,basedate,basedate,basedate,basedate);
	system(sys_31);
	system("echo \"\" >> temp.txt");
	sprintf(sys_32,"echo \"i.eb.evapfr -m rnet=%s.rnet g0=%s.g0 h0=%s.h0 evapfr=%s.evapfr theta=%s.theta --overwrite ; r.null map=%s.evapfr setnull=-999.99 ; r.null map=%s.theta setnull=-999.99 ; r.colors map=%s.theta color=grey1.0 ; r.colors map=%s.evapfr color=grey1.0 \" >> temp.txt",basedate,basedate,basedate,basedate,basedate,basedate,basedate,basedate,basedate);
	system(sys_32);
	system("echo \"\" >> temp.txt");
	sprintf(sys_33,"echo \"i.eb.eta rnetday=%s.rnetd evapfr=%s.evapfr tempk=%s.61 eta=%s.eta --overwrite ; r.null map=%s.eta setnull=-999.99 \" >> temp.txt",basedate,basedate,basedate,basedate,basedate);
	system(sys_33);
	system("echo \"\" >> temp.txt");
	/*clean maps
 	system("chmod +x temp.txt; cat temp.txt; echo \"Start GRASS Processing\n\" ; ./temp.txt");
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

