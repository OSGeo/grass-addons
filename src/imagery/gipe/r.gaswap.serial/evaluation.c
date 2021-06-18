
/***************************************************************/
/* This is a simple genetic algorithm implementation where the */
/* evaluation function takes positive values only and the      */
/* fitness of an individual is the same as the value of the    */
/* objective function (after Michalewicz, 1996)                */

/***************************************************************/
/* Added SWAP input file creation - finput() - September 2003  */

/***************************************************************/
/* Added SWAP output ETa file creation - foutput() - October 03 */

/***************************************************************/
/* Copyleft LGPL Yann Chemin - yann.chemin@ait.ac.th 2003      */
/* ychemin@yahoo.com - Code enhancements welcome!              */
/* Modified by Shamim Akhter - shamimakhter@gmail.com 2005     */

/***************************************************************/

#include <stdio.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>		/*foutput() */
#include <time.h>		/*foutput() */
#include <unistd.h>		/*sleep() in evaluate() */
#include "gaswap.h"

#define TRUE 1
#define FALSE 0


				/*int generation; *//* current generation number */
				/*int cur_best; *//* best individual */
/*FILE *galog; */



/* the SWAP variables to optimize */
int DECd1, DECm1, DECy1;

int FECd1, FECm1, FECY1;

int STSd1, STSm1, STSy1;

int DECdloy1, FECdloy1, STSdloy1;

		   /*      int doy; *//* used in date2doy1() */
			  /*      int day, month; *//* used in doy2date1() */
int TECdoy1;			/*cropping season time extent */

int GWJan1, GWDec1;		/* GW level values in 01Jan & 31Dec */


				/*char *dateName[257]; *//*foutput() */
				/*char *dateNameValue; *//*foutput() */
char **satDATE1;

int dateCounter1;		/*foutput() */

double swapETA1[367];		/*foutput() */

double satETA1[367];		/*foutput() */

double tex1[4];

				/*int POPSIZE; *//* population size */
				/*int MAXGENS; *//* max. number of generations */
			/*int NVARS; *//* max. number of variables */
			/*int NSATEL; *//* max. number of satellite images */
/*int YEAR; */
int SSRUN1, ESRUN1;

double LAT1, ALT1;

char METFIL1[100];

				/*double PXOVER; *//* probability of crossover */
				/*double PMUTATION; *//* probability of mutation */
			    /*double TARGET_FITNESS; *//* fitness value that will stop GA */


/* Declaration of procedures used by this genetic algorithm */

void evaluate(int popsize, int nvar, int *gene, double *fitness, int DECy1,
	      int nsatel, double text[], double ETA[], char **DATE, int ssrun,
	      int esrun, double lat, double alt, char *metfile);
int doy2date1(int *d, int *m, int *day, int *month);

int date2doy1(int *d, int *m);


/*void finput1(void); */
/*void finput2(void); */
void swapkey1(void);

void calfil1(void);

void capfil1(void);

void swafil1(void);

void bbcfil1(void);

void crpfil1(void);

void sol1fil1(void);

void sol2fil1(void);

void sol3fil1(void);

void sol4fil1(void);

void sol5fil1(void);

/*int foutput(void); */
/*int get_sat_eta(void); */
int satellite_dates1(int nsatel);

int get_eta1(char *dateName, char *dateNameValue, int dateCounter1);

/**************************************************************/
/* gaswap function: Each generation involves selecting the best */
/* members, performing crossover & mutation and then          */
/* evaluating the resulting population, until the terminating */
/* condition is satisfied.                                    */

/**************************************************************/


/*************************************************************/
/* Evaluation function: this takes a user defined function.  */
/* Each time this is changed, the code has to be recompiled. */
/* The current function is: square (sat[ETA]-swap[ETA])      */

/*************************************************************/

void evaluate(int popsize, int nvar, int *gene, double *fitness, int DECy1,
	      int nsatel, double text[], double ETA[], char **DATE, int ssrun,
	      int esrun, double lat, double alt, char *metfile)
/*void evaluate(struct genotype *population) */
{
    int mem, i;

    /*      int DECdloy1,STSdloy1,TECdoy1,GWJan1,GWDec1,FECdloy1; */
    /*      int FECd1,FECm1,FECY1; */
    double fit_value, dif_value;

    satDATE1 = (char **)malloc((nsatel + 1) * sizeof(char *));
    for (i = 0; i < nsatel + 1; i++)
	satDATE1[i] = (char *)malloc(367 * sizeof(char));

    SSRUN1 = ssrun;
    ESRUN1 = esrun;
    LAT1 = lat;
    ALT1 = alt;
    sprintf(METFIL1, "%s", metfile);
    for (i = 0; i < 4; i++)
	tex1[i] = text[i];
    for (i = 1; i <= nsatel; i++) {
	satETA1[i] = ETA[i];
	sprintf(satDATE1[i], "%s", DATE[i]);
    }
    swapkey1();
    capfil1();
    swafil1();
    sol1fil1();
    sol2fil1();
    sol3fil1();
    sol4fil1();
    sol5fil1();
    for (mem = 0; mem < popsize; mem++) {
	fit_value = 0;
	DECdloy1 = (int)(*(gene + (mem * nvar) + 0));
	STSdloy1 = (int)(*(gene + (mem * nvar) + 1));
	TECdoy1 = (int)(*(gene + (mem * nvar) + 2));
	GWJan1 = (int)(*(gene + (mem * nvar) + 3));
	GWDec1 = (int)(*(gene + (mem * nvar) + 4));
	/* Create the FECd1 and FECm1 from DEC & TEC */

		/*******************************************/
	/* Get the FECdloy1 = DECdloy1 + TECdoy1 */
	FECdloy1 = DECdloy1 + TECdoy1;
	/* leap year */
	if (DECy1 / 4 * 4 == DECy1 && FECdloy1 > 366) {
	    FECd1 = 31.0;
	    FECm1 = 12.0;
	    FECY1 = DECy1 + 1;
	}
	/* normal year */
	if (DECy1 / 4 * 4 != DECy1 && FECdloy1 > 365) {
	    FECd1 = 31.0;
	    FECm1 = 12.0;
	    FECY1 = DECy1 + 1;
	}
	else {
	    /* Get the FECd1 and FECm1 */
	    doy2date1(&FECdloy1, &DECy1, &FECd1, &FECm1);
	}
	FECdloy1 = 0;

		/*************************/
	doy2date1(&DECdloy1, &DECy1, &DECd1, &DECm1);
	doy2date1(&STSdloy1, &STSy1, &STSd1, &STSm1);
	calfil1();
	bbcfil1();
	crpfil1();
	system("./swap");
	satellite_dates1(nsatel);
	for (i = 1; i <= nsatel; i++) {
	    dif_value = (int)(1000.0 * (satETA1[i] - swapETA1[i]));
	    fit_value = fit_value + ((double)(fabs(dif_value) / 1000.0));
	}
	double const1, constraint1, lambda1;

	constraint1 = TECdoy1 - 90.0;
	if (constraint1 >= 0.0)
	    lambda1 = 0.0;
	else
	    lambda1 = 10.0;

	const1 = lambda1 * (pow(constraint1, 2.0));
	constraint1 = const1;
	fit_value = fit_value / (double)nsatel;
	fit_value = 1.0 / (fit_value * (1.0 + constraint1));
	fitness[mem] = (fit_value);
    }
    free(satDATE1);
}

/*********************************************/
int doy2date1(int *d, int *m, int *day, int *month)
{

	/*********************************************/
    /*This routine converts doy to day/month/year */

	/*********************************************/
    int leap = 0;

    int year, doy;

    *day = 0;
    *month = 0;
    doy = *d;
    year = *m;
    /* Leap year if dividing by 4 leads % 0.0 */
    if (year / 4 * 4 == year) {
	leap = 1;
    }
    if (doy < 32) {
	*month = 1;
	*day = doy;
    }
    else if (doy > 31 && doy < (60 + leap)) {
	*month = 2;
	*day = doy - 31;
    }
    else if (doy > (59 + leap) && doy < (91 + leap)) {
	*month = 3;
	*day = doy - (59 + leap);
    }
    else if (doy > (90 + leap) && doy < (121 + leap)) {
	*month = 4;
	*day = doy - (90 + leap);
    }
    else if (doy > (120 + leap) && doy < (152 + leap)) {
	*month = 5;
	*day = doy - (120 + leap);
    }
    else if (doy > (151 + leap) && doy < (182 + leap)) {
	*month = 6;
	*day = doy - (151 + leap);
    }
    else if (doy > (181 + leap) && doy < (213 + leap)) {
	*month = 7;
	*day = doy - (181 + leap);
    }
    else if (doy > (212 + leap) && doy < (244 + leap)) {
	*month = 8;
	*day = doy - (212 + leap);
    }
    else if (doy > (243 + leap) && doy < (274 + leap)) {
	*month = 9;
	*day = doy - (243 + leap);
    }
    else if (doy > (273 + leap) && doy < (305 + leap)) {
	*month = 10;
	*day = doy - (273 + leap);
    }
    else if (doy > (304 + leap) && doy < (335 + leap)) {
	*month = 11;
	*day = doy - (304 + leap);
    }
    else if (doy > 334) {
	*month = 12;
	*day = doy - (334 + leap);
    }
    return 1;

}

/*********************************************/
/*This program converts day/month/year to doy */

/*********************************************/

/*********************************************/
int date2doy1(int *d, int *m)
{
    int leap = 0;

    int day_month_tot = 0;

    int day, month;

    int doy;

    doy = 0;
    day = *d;
    month = *m;
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
    /* Leap year if dividing by 4 leads % 0.0 */
    if (DECy1 / 4 * 4 == DECy1) {
	leap = 1;
    }
    doy = day_month_tot + day + leap;
    return (doy);
}

/*******************************************************/
/*                                                     */
/* Getting ETa from SWAP INC.file => swap.eta          */
/*         and merging it with satellite.eta file      */
/*         Resulting file => eval.eta                  */
/*         Format of eval.eta: ETaRS ETaSWAP\n         */

/*******************************************************/

/********************************************************/

/********************************************************/

/********************************************************/
int get_eta1(char *dateName, char *dateNameValue, int dateCounter1)
{
    FILE *f;

    char s[1000], *ptr;

    int i = 0;

    char *p;

    int TRA1 = 0, TRA2, EVS1 = 0, EVS2;

    double TRA = 0.0, EVS;

    f = fopen("out.INC", "r");
    if (!f)
	return 1;

    while (fgets(s, 1000, f) != NULL) {
	ptr = strstr(s, dateNameValue);
	if (ptr != NULL) {
	    p = strtok(ptr, " .");
	    while (i < 17) {
		p = strtok(NULL, " .");
		if ((i == 11 || i == 12 || i == 15 || i == 16) && p) {
		    if (i == 11 && p) {
			TRA1 = atoi(p);
		    }
		    else if (i == 12 && p) {
			TRA2 = atoi(p);
			TRA = (double)(TRA1) + (double)(TRA2 / 1000.0);
		    }
		    else if (i == 15 && p) {
			EVS1 = atoi(p);
		    }
		    else if (i == 16 && p) {
			EVS2 = atoi(p);
			EVS = (double)(EVS1) + (double)(EVS2 / 1000.0);
			swapETA1[dateCounter1] = (TRA + EVS);
		    }
		}
		i = i + 1;
	    }
	}
    }
    (void)fclose(f);
    return 1;
}

/*******************************************************/
/*                                                     */
/* Getting dates from "satellite.dates" file           */
/*                                                     */

/*******************************************************/
/* Thanks Dr Honda honda@ait.ac.th!                    */
/*                                                     */
/* Limited to 99 images so far...                      */

/*******************************************************/
int satellite_dates1(int nsatel)
{
    struct tm t;

#define	BUFLEN	1000
    int iline = 0;

    int i;

    char dateName[256];

    char *dateNameFormat = "%s%2.2d";

    char *date = "date";

    char dateNameValue[256];

    char *dateFormat1 = "%1.1d/%2.2d/%4.4d";

    char *dateFormat2 = "%2.2d/%2.2d/%4.4d";

    int dateCounter1 = 0;

    char buf[BUFLEN];

    for (i = 1; i <= nsatel; i++) {
	if (sscanf(satDATE1[i], "%d/%d/%d", &t.tm_mday, &t.tm_mon, &t.tm_year)
	    != 3) {
	    fprintf(stderr, "reading problem; line : %d: %s\n", iline, buf);
	    return 1;
	}
	t.tm_mon--;
	t.tm_year -= 1900;
	sprintf(dateName, dateNameFormat, date, i);
	i++;
	if (t.tm_mday < 10.0) {
	    sprintf(dateNameValue, dateFormat1, t.tm_mday, t.tm_mon + 1,
		    t.tm_year + 1900);
	}
	else {
	    sprintf(dateNameValue, dateFormat2, t.tm_mday, t.tm_mon + 1,
		    t.tm_year + 1900);
	}
	get_eta1(dateName, dateNameValue, dateCounter1);	/*send the sat.date to get_eta1() */
	dateCounter1++;
    }
    return 1;
}

/*******************************************************/
/*                                                     */
/*                File Input for SWAP                  */
/*                                                     */

/*******************************************************/
/* Date: 20030901                                      */

/*******************************************************/

/********************************************************/
/* main program                                         */

/********************************************************/

/********************************************************/
void swapkey1(void)
{
    FILE *swapkey1;		/* SWAP.KEY file-variable */

    swapkey1 = fopen("SWAP.KEY", "w");
    fputs(" Project = 'Rood'\n", swapkey1);
    fputs(" Path = ''\n", swapkey1);
    fputs(" CType = 1\n", swapkey1);
    fputs(" SWSCRE = 0\n\n", swapkey1);
    fprintf(swapkey1, " SSRUN1 = 01 01 %d\n", SSRUN1);
    fprintf(swapkey1, " ESRUN1 = 31 12 %d\n", ESRUN1);
    fputs(" FMAY = 1\n", swapkey1);
    fputs(" Period = 1\n", swapkey1);
    fputs(" SWRES = 1\n\n", swapkey1);
    fputs(" SWODAT = 0\n", swapkey1);
    fputs("*\n", swapkey1);
    fputs("* DD MM YYYY\n", swapkey1);
    fputs("* End_of_table\n\n", swapkey1);
    fprintf(swapkey1, " METFIL1 = \'%s\'\n", METFIL1);
    fprintf(swapkey1, " LAT1 = %lf\n", LAT1);
    fprintf(swapkey1, " ALT1 = %lf\n", ALT1);
    fputs(" SWETR = 0\n", swapkey1);
    fputs(" SWRAI = 0\n\n", swapkey1);
    fputs("* IRGFIL CALFIL   DRFIL   BBCFIL  OUTFIL\n", swapkey1);
    fputs("  ''     'RoodC'  'none'  'Rood'  'out'\n", swapkey1);
    fputs("* End_of_table\n\n", swapkey1);
    fputs(" SWDRA = 0\n\n", swapkey1);
    fputs(" SWSOLU = 0\n\n", swapkey1);
    fputs(" SWHEA = 0\n\n", swapkey1);
    fputs(" SWVAP = 0\n\n", swapkey1);
    fputs(" SWDRF = 0\n\n", swapkey1);
    fputs(" SWSWB = 0\n\n", swapkey1);
    fputs(" SWAFO = 0\n", swapkey1);
    fputs(" AFONAM = 'testA'\n\n", swapkey1);
    fputs(" SWAUN = 0\n", swapkey1);
    fputs(" AUNNAM = 'testA'\n\n", swapkey1);
    fputs(" SWATE = 0\n", swapkey1);
    fputs(" ATENAM = 'testA'\n\n", swapkey1);
    fputs(" SWAIR = 0\n", swapkey1);
    fputs(" AIRNAM = 'testA'\n\n", swapkey1);
    (void)fclose(swapkey1);
    return;
}

/********************************************************/
/* CAL-file                                             */

/********************************************************/

void calfil1(void)
{
    FILE *calfil1;		/* RoodC.CAL file_variable */

    calfil1 = fopen("RoodC.CAL", "w");
    fputs("* CRPFIL Type CAPFIL  EMERGENCE END_crop START_sch\n", calfil1);
    fputs("*                     d1 m1     d2 m2    d3 m3\n", calfil1);
    fprintf(calfil1, " 'Crop'  1    'RoodC' %i %i     %i %i    %i %i\n",
	    DECd1, DECm1, FECd1, FECm1, STSd1, STSm1);
    fputs("* End_of_table\n\n", calfil1);
    (void)fclose(calfil1);
    return;
}

/*******************************************************/
/* CAP-file                                            */

/*******************************************************/

void capfil1(void)
{
    FILE *capfil1;		/* RoodC.CAP file_variable */

    capfil1 = fopen("RoodC.CAP", "w");
    fputs(" ISUAS = 1\n\n", capfil1);
    fputs(" CIRRS = 2.56\n\n", capfil1);
    fputs(" TCS1 = 0\n", capfil1);
    fputs("* DVS  Ta/Tp\n", capfil1);
    fputs("0.0 0.75\n", capfil1);
    fputs("2.0 0.75\n", capfil1);
    fputs("* End of table\n\n", capfil1);
    fputs("TCS2 = 0\n", capfil1);
    fputs("* DVS  RAW\n", capfil1);
    fputs("  0.0  0.95\n", capfil1);
    fputs("  2.0  0.95\n", capfil1);
    fputs("* End of table\n\n", capfil1);
    fputs("TCS3 = 0\n", capfil1);
    fputs("* DVS  TAW\n", capfil1);
    fputs("  0.0  0.50\n", capfil1);
    fputs("  2.0  0.50\n", capfil1);
    fputs("* End of table\n\n", capfil1);
    fputs("TCS4 = 0\n", capfil1);
    fputs("* DVS  DWA\n", capfil1);
    fputs("  0.0  40.0\n", capfil1);
    fputs("  2.0  40.0\n", capfil1);
    fputs("* End of table\n\n", capfil1);
    fputs(" TCS5 = 1\n", capfil1);
    fputs(" PHORMC = 0\n", capfil1);
    fputs(" DCRIT = 0.0\n", capfil1);
    fputs("* DVS  VALUE\n", capfil1);
    fputs("  0.0  1.0\n", capfil1);
    fputs("  2.0  1.0\n", capfil1);
    fputs("* End of table\n\n", capfil1);
    fputs(" DCS1 = 0\n", capfil1);
    fputs("* DVS  dI\n", capfil1);
    fputs("  0.0  0.0\n", capfil1);
    fputs("  2.0  0.0\n", capfil1);
    fputs("* End of table\n\n", capfil1);
    fputs(" DCS2 = 1\n", capfil1);
    fputs("* DVS  FID\n", capfil1);
    fputs("  0.0  100.0\n", capfil1);
    fputs("  2.0  100.0\n", capfil1);
    fputs("* End of table\n\n", capfil1);
    (void)fclose(capfil1);
    return;
}

/*******************************************************/
/* SWA-file                                            */

/*******************************************************/

void swafil1(void)
{
    FILE *swafil1;		/* Rood.SWA file_variable */

    swafil1 = fopen("Rood.SWA", "w");
    fputs
	("*******************************************************************************\n",
	 swafil1);
    fputs(" PONDMX = 10.0\n\n", swafil1);
    fputs
	("*******************************************************************************\n\n",
	 swafil1);

    fputs
	("*******************************************************************************\n",
	 swafil1);
    fputs(" SWCFBS = 0\n", swafil1);
    fputs(" CFBS = 0.9\n", swafil1);
    fputs(" SWREDU = 2\n", swafil1);
    fputs(" COFRED = 0.35\n", swafil1);
    fputs(" RSIGNI = 0.5\n\n", swafil1);
    fputs
	("*******************************************************************************\n\n",
	 swafil1);

    fputs
	("*******************************************************************************\n",
	 swafil1);
    fputs(" DTMIN = 1.0E-4\n", swafil1);
    fputs(" DTMAX = 0.1\n", swafil1);
    fputs(" SWNUMS = 2\n", swafil1);
    fputs(" THETOL = 0.01\n\n", swafil1);
    fputs
	("*******************************************************************************\n\n",
	 swafil1);

    fputs
	("*******************************************************************************\n",
	 swafil1);
    fputs(" NUMLAY = 5\n", swafil1);
    fputs(" NUMNOD = 50\n\n", swafil1);

    fputs(" BOTCOM = 14 19 22 26 50\n", swafil1);
    fputs("*\n", swafil1);
    fputs("* thickness of soil compartments [cm]:\n", swafil1);
    fputs("* total 500 cm\n", swafil1);
    fputs("*\n", swafil1);
    fputs(" DZ =\n", swafil1);
    fputs
	("     1.0     1.0     1.0     1.0     1.0     1.0     1.0     1.0     1.0     1.0\n",
	 swafil1);
    fputs
	("     5.0     5.0     5.0     5.0     5.0     5.0     5.0     5.0     5.0     5.0\n",
	 swafil1);
    fputs
	("    10.0    10.0    10.0    10.0    10.0    10.0    10.0    10.0    10.0    10.0\n",
	 swafil1);
    fputs
	("    10.0    10.0    10.0    10.0    10.0    10.0    10.0    10.0    10.0    10.0\n",
	 swafil1);
    fputs
	("    20.0    20.0    20.0    20.0    20.0    20.0    20.0    20.0    40.0    40.0\n",
	 swafil1);
    fputs
	("*******************************************************************************\n\n",
	 swafil1);

    fputs
	("*******************************************************************************\n",
	 swafil1);
    fputs(" SOLFIL = 'Rood_1' 'Rood_2' 'Rood_3' 'Rood_4' 'Rood_5'\n\n",
	  swafil1);
    fputs("* PSAND  PSILT  PCLAY  ORGMAT\n", swafil1);
    fprintf(swafil1, "  %lf   %lf   %lf   %lf\n", tex1[0], tex1[1], tex1[2],
	    tex1[3]);
    fprintf(swafil1, "  %lf   %lf   %lf   %lf\n", tex1[0], tex1[1], tex1[2],
	    tex1[3]);
    fprintf(swafil1, "  %lf   %lf   %lf   %lf\n", tex1[0], tex1[1], tex1[2],
	    tex1[3]);
    fprintf(swafil1, "  %lf   %lf   %lf   %lf\n", tex1[0], tex1[1], tex1[2],
	    tex1[3]);
    fprintf(swafil1, "  %lf   %lf   %lf   %lf\n\n", tex1[0], tex1[1], tex1[2],
	    tex1[3]);

    fputs
	("*******************************************************************************\n\n",
	 swafil1);

    fputs(" RDS = 300.0\n\n", swafil1);

    fputs(" SWHYST = 0\n", swafil1);
    fputs(" TAU = 0.2\n\n", swafil1);

    fputs(" SWSCAL = 0\n", swafil1);
    fputs(" NSCALE = 0\n", swafil1);
    fputs(" ISCLAY = 0\n", swafil1);
    fputs(" SWMOBI = 0\n", swafil1);
    fputs("* PF1  FM1  PF2  FM2  THETIM\n", swafil1);
    fputs("  0.0  0.0  0.0  0.0  0.0\n", swafil1);
    fputs("  0.0  0.0  0.0  0.0  0.0\n", swafil1);
    fputs("* End_of_table\n\n", swafil1);

    fputs(" SWCRACK = 0\n", swafil1);
    fputs(" SHRINA = 0.53\n", swafil1);
    fputs(" MOISR1 = 1.0\n", swafil1);
    fputs(" MOISRD = 0.05\n", swafil1);
    fputs(" ZNCRACK = -5.0\n", swafil1);
    fputs(" GEOMF = 3.0\n", swafil1);
    fputs(" DIAMPOL = 40.0\n", swafil1);
    fputs(" RAPCOEF = 0.0\n", swafil1);
    fputs(" DIFDES = 0.2\n", swafil1);
    fputs(" THETCR = 0.50  0.50  0.50  0.50  0.50\n\n", swafil1);
    fputs(" SWDIVD = 0\n", swafil1);
    fputs(" COFANI =    1.0    1.0    1.0    1.0    1.0\n\n", swafil1);
    fputs(" SWINCO = 2\n", swafil1);
    fputs(" GWLI = -200.0\n", swafil1);
    fputs(" OSGWLM = 30.0\n\n", swafil1);
    (void)fclose(swafil1);
    return;
}

/*******************************************************/
/* BBC-file                                            */

/*******************************************************/

void bbcfil1(void)
{
    FILE *bbcfil1;		/* Rood.BBC file_variable */

    bbcfil1 = fopen("Rood.BBC", "w");
    fputs(" SWOPT1 = 1\n", bbcfil1);
    fputs("* d1 m1 GWlevel\n", bbcfil1);
    fprintf(bbcfil1, "  1  1 -%i.0\n", GWJan1);
    fprintf(bbcfil1, " 31 12 -%i.0\n", GWDec1);
    fputs("* End of table\n\n", bbcfil1);
    fputs(" SWOPT2 = 0\n", bbcfil1);
    fputs(" SWC2 = 2\n", bbcfil1);
    fputs(" C2AVE = 0.1\n", bbcfil1);
    fputs(" C2AMP = 0.05\n", bbcfil1);
    fputs(" C2STA = 91\n", bbcfil1);
    fputs("* d2 m2 Qbot\n", bbcfil1);
    fputs("   1  1 0.10\n", bbcfil1);
    fputs("   5  6 0.20\n", bbcfil1);
    fputs("  31 12 0.10\n", bbcfil1);
    fputs("* End of table\n\n", bbcfil1);
    fputs(" SWOPT3 = 0\n", bbcfil1);
    fputs(" SHAPE = 0.79\n", bbcfil1);
    fputs(" RIMLAY = 500\n", bbcfil1);
    fputs(" AQAVE = 50.0\n", bbcfil1);
    fputs(" AQAMP = 20.0\n", bbcfil1);
    fputs(" AQTAMX = 120\n", bbcfil1);
    fputs(" AQPER = 365\n\n", bbcfil1);
    fputs(" SWOPT4 = 0\n", bbcfil1);
    fputs(" COFQHA = -0.3\n", bbcfil1);
    fputs(" COFQHB = -0.01\n\n", bbcfil1);
    fputs(" SWOPT5 = 0\n", bbcfil1);
    fputs("* d5 m5 GWlevel\n", bbcfil1);
    fputs("   1  1  50.0\n", bbcfil1);
    fputs("  31 12  20.0\n", bbcfil1);
    fputs("* End of table\n\n", bbcfil1);
    fputs(" SWOPT6 = 0\n", bbcfil1);
    fputs(" SWOPT7 = 0\n", bbcfil1);
    fputs(" SWOPT8 = 0\n", bbcfil1);
    (void)fclose(bbcfil1);
    return;
}

/********************************************************/
/* CRP-file                                             */

/********************************************************/

void crpfil1(void)
{
    FILE *crpfil1;		/* Crop.CRP file_variable */

    crpfil1 = fopen("Crop.CRP", "w");
    fputs(" IDEV = 1\n", crpfil1);
    fprintf(crpfil1, "LCC = %i\n", TECdoy1);
    fputs(" TSUMEA = 1050.0\n", crpfil1);
    fputs(" TSUMAM = 1000.0\n", crpfil1);
    fputs(" TBASE = 0.0\n\n", crpfil1);
    fputs(" KDIF = 0.6\n", crpfil1);
    fputs(" KDIR = 0.75\n\n", crpfil1);
    fputs(" SWGC = 1\n", crpfil1);
    fputs("*    DVS   LAI or SCF\n", crpfil1);
    fputs(" GCTB =\n", crpfil1);
    fputs("     0.0    0.00\n", crpfil1);
    fputs("     0.2    0.07\n", crpfil1);
    fputs("     0.4    0.16\n", crpfil1);
    fputs("     0.6    0.61\n", crpfil1);
    fputs("     0.8    1.25\n", crpfil1);
    fputs("     1.0    1.73\n", crpfil1);
    fputs("     1.2    1.75\n", crpfil1);
    fputs("     1.4    1.73\n", crpfil1);
    fputs("     1.6    1.71\n", crpfil1);
    fputs("     1.8    1.04\n", crpfil1);
    fputs("     2.0    0.58\n", crpfil1);
    fputs("**************\n\n", crpfil1);
    fputs(" SWCF = 2\n", crpfil1);
    fputs("*        DVS   CF or CH\n", crpfil1);
    fputs(" CFTB = 0.00   0.0\n", crpfil1);
    fputs("        1.00  70.0\n", crpfil1);
    fputs("        2.00  70.0\n\n", crpfil1);
    fputs("*         DVS   RD\n", crpfil1);
    fputs(" RDTB = 0.00   0.0\n", crpfil1);
    fputs("        1.00 100.0\n", crpfil1);
    fputs("        2.00 100.0\n\n", crpfil1);
    fputs("*        DVS   KY\n", crpfil1);
    fputs(" KYTB = 0.0   0.2\n", crpfil1);
    fputs("        0.4   0.2\n", crpfil1);
    fputs("        0.9   0.5\n", crpfil1);
    fputs("        1.5   0.5\n", crpfil1);
    fputs("        2.0   0.3\n\n", crpfil1);
    fputs("**************\n\n", crpfil1);
    fputs(" HLIM1 = -0.1\n", crpfil1);
    fputs(" HLIM2U = -30.0\n", crpfil1);
    fputs(" HLIM2L = -30.0\n", crpfil1);
    fputs(" HLIM3H = -100.0\n", crpfil1);
    fputs(" HLIM3L = -200.0\n", crpfil1);
    fputs(" HLIM4 = -16000.0\n", crpfil1);
    fputs(" RSC = 70.0\n", crpfil1);
    fputs(" ADCRH = 0.5\n", crpfil1);
    fputs(" ADCRL = 0.1\n\n", crpfil1);
    fputs(" ECMAX = 7.7\n", crpfil1);
    fputs(" ECSLOP = 5.0\n\n", crpfil1);
    fputs(" COFAB = 0.25\n\n", crpfil1);
    fputs("*        Rdepth Rdensity\n", crpfil1);
    fputs(" RDCTB = 0.0    1.0\n", crpfil1);
    fputs("         1.0    0.0\n", crpfil1);
    fputs("**************\n", crpfil1);
    (void)fclose(crpfil1);
    return;
}

/*******************************************************/
/* SOL-file number 1                                   */

/*******************************************************/

void sol1fil1(void)
{
    FILE *sol1fil1;		/* Rood_1.SOL file_variable */

    sol1fil1 = fopen("Rood_1.SOL", "w");
    fputs(" SWPHYS = 1\n\n", sol1fil1);
    fputs(" COFGEN1 = 0.000\n", sol1fil1);
    fputs(" COFGEN2 = 0.492\n", sol1fil1);
    fputs(" COFGEN3 = 0.500\n", sol1fil1);
    fputs(" COFGEN4 = 0.02638\n", sol1fil1);
    fputs(" COFGEN5 = -2.196\n", sol1fil1);
    fputs(" COFGEN6 = 1.1775\n", sol1fil1);
    fputs(" COFGEN8 = 0.029\n", sol1fil1);
    fputs("* End of file\n", sol1fil1);
    (void)fclose(sol1fil1);
    return;
}

/*******************************************************/
/* SOL-file number 2                                   */

/*******************************************************/

void sol2fil1(void)
{
    FILE *sol2fil1;		/* Rood_2.SOL file_variable */

    sol2fil1 = fopen("Rood_2.SOL", "w");
    fputs(" SWPHYS = 1\n\n", sol2fil1);
    fputs(" COFGEN1 = 0.000\n", sol2fil1);
    fputs(" COFGEN2 = 0.516\n", sol2fil1);
    fputs(" COFGEN3 = 30.206\n", sol2fil1);
    fputs(" COFGEN4 = 0.01216\n", sol2fil1);
    fputs(" COFGEN5 = 0.046\n", sol2fil1);
    fputs(" COFGEN6 = 1.1471\n", sol2fil1);
    fputs(" COFGEN8 = 0.013\n", sol2fil1);
    fputs("* End of file\n", sol2fil1);
    (void)fclose(sol2fil1);
    return;
}

/*******************************************************/
/* SOL-file number 3                                   */

/*******************************************************/

void sol3fil1(void)
{
    FILE *sol3fil1;		/* Rood_3.SOL file_variable */

    sol3fil1 = fopen("Rood_3.SOL", "w");
    fputs(" SWPHYS = 1\n\n", sol3fil1);
    fputs(" COFGEN1 = 0.000\n", sol3fil1);
    fputs(" COFGEN2 = 0.501\n", sol3fil1);
    fputs(" COFGEN3 = 2.295\n", sol3fil1);
    fputs(" COFGEN4 = 0.00778\n", sol3fil1);
    fputs(" COFGEN5 = 0.251\n", sol3fil1);
    fputs(" COFGEN6 = 1.0829\n", sol3fil1);
    fputs(" COFGEN8 = 0.009\n", sol3fil1);
    fputs("* End of file\n", sol3fil1);
    (void)fclose(sol3fil1);
    return;
}

/*******************************************************/
/* SOL-file number 4                                   */

/*******************************************************/

void sol4fil1(void)
{
    FILE *sol4fil1;		/* Rood_4.SOL file_variable */

    sol4fil1 = fopen("Rood_4.SOL", "w");
    fputs(" SWPHYS = 1\n\n", sol4fil1);
    fputs(" COFGEN1 = 0.000\n", sol4fil1);
    fputs(" COFGEN2 = 0.431\n", sol4fil1);
    fputs(" COFGEN3 = 4.331\n", sol4fil1);
    fputs(" COFGEN4 = 0.01379\n", sol4fil1);
    fputs(" COFGEN5 = -2.743\n", sol4fil1);
    fputs(" COFGEN6 = 1.0818\n", sol4fil1);
    fputs(" COFGEN8 = 0.015\n", sol4fil1);
    fputs("* End of file\n", sol4fil1);
    (void)fclose(sol4fil1);
    return;
}

/*******************************************************/
/* SOL-file number 5                                   */

/*******************************************************/

void sol5fil1(void)
{
    FILE *sol5fil1;		/* Rood_5.SOL file_variable */

    sol5fil1 = fopen("Rood_5.SOL", "w");
    fputs(" SWPHYS = 1\n\n", sol5fil1);
    fputs(" COFGEN1 = 0.000\n", sol5fil1);
    fputs(" COFGEN2 = 0.424\n", sol5fil1);
    fputs(" COFGEN3 = 9.843\n", sol5fil1);
    fputs(" COFGEN4 = 0.01667\n", sol5fil1);
    fputs(" COFGEN5 = -1.982\n", sol5fil1);
    fputs(" COFGEN6 = 1.1307\n", sol5fil1);
    fputs(" COFGEN8 = 0.018\n", sol5fil1);
    fputs("* End of file\n", sol5fil1);
    (void)fclose(sol5fil1);
    return;
}

/********************************************************/
