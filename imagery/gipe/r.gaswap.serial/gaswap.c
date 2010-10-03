
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


int generation;			/* current generation number */

int cur_best;			/* best individual */

FILE *galog;



/* the SWAP variables to optimize */
int DECd, DECm, DECy;

int FECd, FECm, FECy;

int STSd, STSm, STSy;

int DECdoy, FECdoy, STSdoy;

int doy;			/* used in date2doy() */

int day, month;			/* used in doy2date() */

int TECdoy;			/*cropping season time extent */

int GWJan, GWDec;		/* GW level values in 01Jan & 31Dec */


//char *dateName[257];  /*foutput()*/
//char *dateNameValue;  /*foutput()*/
char **satDATE;

int dateCounter;		/*foutput() */

double swapETA[367];		/*foutput() */

double satETA[367];		/*foutput() */

double tex[4];

int *gene_tmp;

double *fitness_tmp;

int POPSIZE;			/* population size */

int MAXGENS;			/* max. number of generations */

int NVARS;			/* max. number of variables */

int NSATEL;			/* max. number of satellite images */

int YEAR;

int SSRUN, ESRUN;

double LAT, ALT;

char METFIL[100];

double PXOVER;			/* probability of crossover */

double PMUTATION;		/* probability of mutation */

double TARGET_FITNESS;		/* fitness value that will stop GA */


/* Declaration of procedures used by this genetic algorithm */
void initialize(struct genotype *population);

void evaluate_init(struct genotype *population);

void evaluate(int popsize, int nvar, int *gene, double *fitness, int DECy,
	      int nsatel, double text[], double ETA[], char **DATE, int ssrun,
	      int esrun, double lat, double alt, char *metfile);

void keep_the_best(struct genotype *population);

void elitist(struct genotype *population);

void selection(struct genotype *population, struct genotype *newpopulation);

void crossover(struct genotype *population);

void mutate(struct genotype *population);

void report(struct genotype *population, int generation);

void makegrasscell(struct genotype **population);

int doy2date(int *d, int *m);

int date2doy(int *d, int *m);

void finput1(void);

void finput2(void);

void swapkey(void);

void calfil(void);

void capfil(void);

void swafil(void);

void bbcfil(void);

void crpfil(void);

void sol1fil(void);

void sol2fil(void);

void sol3fil(void);

void sol4fil(void);

void sol5fil(void);

int foutput(void);

int get_sat_eta(void);

int satellite_dates(void);

int get_eta(char *dateName, char *dateNameValue, int dateCounter);

/**************************************************************/
/* gaswap function: Each generation involves selecting the best */
/* members, performing crossover & mutation and then          */
/* evaluating the resulting population, until the terminating */
/* condition is satisfied.                                    */

/**************************************************************/


void gaswap(double texture[], double sat[], double satDOY[], int NVAR,
	    int NSAT, int year, int pop, int maxgen, double pmute,
	    double pxover, double target_fitness, int syear, int eyear,
	    char *METRO, double Lati, double Alt, double *grass_c)
{

    int i;

    POPSIZE = pop;
    MAXGENS = maxgen;
    PXOVER = pxover;
    PMUTATION = pmute;
    TARGET_FITNESS = target_fitness;
    NVARS = NVAR;
    NSATEL = NSAT;
    YEAR = year;
    SSRUN = syear;
    ESRUN = eyear;
    LAT = Lati;
    ALT = Alt;
    //////////////////////
    i = 0;
    while (!(METRO[i] == 0)) {
	METFIL[i] = METRO[i];
	i++;
    }
    METFIL[i] = 0;
    generation = 0;
    DECy = YEAR;
    FECy = YEAR;
    STSy = YEAR;
    struct genotype *population, *newpopulation;

    //printf("start MALLOC\n");
    /* malloc the population[number][size] and newpopulation[number][size] */
    if ((population =
	 malloc((POPSIZE + 1) * sizeof(struct genotype))) == NULL) {
	printf("Ooops malloc1.1 == null...\n");
	exit(1);
    }

    for (i = 0; i <= POPSIZE; i++) {
	population[i].gene = malloc((NVARS) * sizeof(int));
	population[i].upper = malloc((NVARS) * sizeof(double));
	population[i].lower = malloc((NVARS) * sizeof(double));
    }

    if ((newpopulation =
	 malloc((POPSIZE + 1) * sizeof(struct genotype))) == NULL) {
	printf("Ooops malloc2.1 == null...\n");
	//exit(1);
    }
    for (i = 0; i <= POPSIZE; i++) {
	newpopulation[i].gene = malloc((NVARS) * sizeof(int));
	newpopulation[i].upper = malloc((NVARS) * sizeof(double));
	newpopulation[i].lower = malloc((NVARS) * sizeof(double));
    }

    satDATE = (char **)malloc((NSATEL + 1) * sizeof(char *));

    for (i = 0; i < NSATEL + 1; i++)
	satDATE[i] = (char *)malloc(367 * sizeof(char));

    //printf("converting satDOY to satDATES\n");
    /* Converting the SATdoy to SATdates */
    int satdoy_var;

    for (i = 1; i <= NSATEL; i++) {
	//printf("converting satDOY to satDATES 1.%i\n",i);
	satETA[i] = sat[i];
	//printf("converting satDOY to satDATES 2.%i\n",i);
	satdoy_var = satDOY[i];
	//printf("converting satDOY to satDATES 3.%i\n",i);
	doy2date(&satdoy_var, &DECy);
	//printf("converting satDOY to satDATES 4.%i\n",i);
	satDOY[i] = satdoy_var;
	//printf("converting satDOY to satDATES 5.%i\n",i);
	//printf("day=%d month=%d DEcy=%d\n",day,month,DECy);
	sprintf(satDATE[i], "%d/%d/%d", day, month, DECy);
	//printf("converte satDATES %s\n",satDATE[i]);
	day = 0;
	month = 0;

    }
    //printf("End of converting satDOY to satDATES\n");
    for (i = 1; i <= NSATEL; i++) {
	satETA[i] = sat[i];
	//printf("satETA %f\n",satETA[i]);
    }
    //printf("End of converting NSATEL\n");
    for (i = 0; i < 4; i++)
	tex[i] = texture[i];

    generation = 0;
    srand(getuid() * getpid() % getppid());
    initialize(population);
    evaluate_init(population);
    keep_the_best(population);
    gene_tmp = (int *)malloc(sizeof(int) * ((POPSIZE + 1) * NVARS));
    fitness_tmp = (double *)malloc(sizeof(double) * (POPSIZE + 1));
    generation = 0;

    while (generation < MAXGENS) {
	generation++;
	selection(population, newpopulation);
	crossover(population);
	mutate(population);
	int c1, c2;

	for (c1 = 0; c1 < POPSIZE + 1; c1++)
	    for (c2 = 0; c2 < NVARS; c2++) {
		*(gene_tmp + (c1 * NVARS) + c2) = population[c1].gene[c2];
		//printf("population[%d].gene[%d]=%d ",c1,c2,population[c1].gene[c2]);
	    }
	for (c1 = 0; c1 < POPSIZE + 1; c1++) {
	    fitness_tmp[c1] = population[c1].fitness;
	    printf("population[%d].fitness=%f  ", c1, population[c1].fitness);
	}
	evaluate(POPSIZE, NVARS, gene_tmp, fitness_tmp, DECy, NSATEL, tex,
		 satETA, satDATE, SSRUN, ESRUN, LAT, ALT, METFIL);

	for (c1 = 0; c1 < POPSIZE + 1; c1++) {
	    population[c1].fitness = fitness_tmp[c1];
	    printf("population[%d].fitness=%f  ", c1, population[c1].fitness);
	}
	elitist(population);
    }
    int k;

    for (k = 1; k < NVARS; k++) {
	grass_c[k] = (population[POPSIZE].gene[k - 1]);
	//printf("Inside GASWAP %f\n", grass_c[k]);
    }
    grass_c[k] = population[POPSIZE].fitness;

    free(gene_tmp);
    free(fitness_tmp);
    free(satDATE);
    free(population);
    free(newpopulation);
    return;
}

void initialize(struct genotype *population)
{
    int i, j;

    double lbound[NVARS], ubound[NVARS];

    population[POPSIZE].fitness = 0.0;	/*init best member fitness */

    for (i = 0; i < POPSIZE; i++) {
	for (j = 0; j < NVARS; j++) {

	    if (j == 0) {
		lbound[j] = 60.0;
		ubound[j] = 120.0;
	    }
	    if (j == 1) {
		lbound[j] = 90.0;
		ubound[j] = 150.0;
	    }
	    if (j == 2) {
		lbound[j] = 160.0;
		ubound[j] = 200.0;
	    }
	    if (j == 3 || j == 4) {
		lbound[j] = 140.0;
		ubound[j] = 160.0;
	    }
	    if (j == 7 || j == 8) {
		lbound[j] = 10.0;
		ubound[j] = 200.0;
	    }
	    if (j == 9 || j == 10) {


	    }

	    population[i].lower[j] = 0.0;
	    population[i].upper[j] = 0.0;
	    population[i].fitness = 0.0;
	    population[i].rfitness = 0.0;
	    population[i].cfitness = 0.0;
	    population[i].lower[j] = lbound[j];
	    population[i].upper[j] = ubound[j];
	    population[i].gene[j] =
		(int)((rand() % 1000 / 1000.0) *
		      (population[i].upper[j] - population[i].lower[j]) +
		      population[i].lower[j]);

	}
    }
}


/*************************************************************/
/* Evaluation function: this takes a user defined function.  */
/* Each time this is changed, the code has to be recompiled. */
/* The current function is: square (sat[ETA]-swap[ETA])      */

/*************************************************************/

void evaluate_init(struct genotype *population)
{
    int mem, i;

    double fit_value, dif_value;

    for (mem = 0; mem < POPSIZE; mem++) {
	fit_value = 0;
	DECdoy = (int)(population[mem].gene[0]);
	STSdoy = (int)(population[mem].gene[1]);
	TECdoy = (int)(population[mem].gene[2]);
	GWJan = (int)(population[mem].gene[3]);
	GWDec = (int)(population[mem].gene[4]);

	/* Create the FECd and FECm from DEC & TEC */

		/*******************************************/
	/* Get the FECdoy = DECdoy + TECdoy */
	FECdoy = DECdoy + TECdoy;
	/* leap year */
	if (DECy / 4 * 4 == DECy && FECdoy > 366) {
	    FECd = 31.0;
	    FECm = 12.0;
	    FECy = DECy + 1;
	}
	/* normal year */
	if (DECy / 4 * 4 != DECy && FECdoy > 365) {
	    FECd = 31.0;
	    FECm = 12.0;
	    FECy = DECy + 1;
	}
	else {
	    /* Get the FECd and FECm */
	    doy2date(&FECdoy, &DECy);
	    FECd = day;
	    FECm = month;
	    day = 0;
	    month = 0;
	}
	FECdoy = 0;

		/*************************/

	doy2date(&DECdoy, &DECy);

	DECd = day;
	DECm = month;
	day = 0;
	month = 0;

	doy2date(&STSdoy, &STSy);

	STSd = day;
	STSm = month;
	day = 0;
	month = 0;

	if (DECd == 0 || DECm == 0 || FECd == 0 || FECm == 0 || STSd == 0 ||
	    STSm == 0 || GWJan == 0 || GWDec == 0) {
	    population[mem].fitness = 0.0;
	    initialize(population);
	}
	else {
	    if (generation < 2) {
		finput1();
	    }
	    else {
		finput2();
	    }
	    system("./swap");
	    foutput();
	    for (i = 1; i <= NSATEL; i++) {
		dif_value = (int)(1000.0 * (satETA[i] - swapETA[i]));
		fit_value = fit_value + ((double)(fabs(dif_value) / 1000.0));	// *(double) (fabs(dif_value)/1000.0));
	    }
	    fit_value = fit_value / (double)NSATEL;
	    population[mem].fitness = (fit_value);
	}
    }
}

/*********************************************/
int doy2date(int *d, int *m)
{

	/*********************************************/
    /*This routine converts doy to day/month/year */

	/*********************************************/

    int leap = 0;

    int year;

    day = 0;
    month = 0;
    doy = *d;
    year = *m;

    /* Leap year if dividing by 4 leads % 0.0 */
    if (year / 4 * 4 == year) {
	leap = 1;
    }

    if (doy < 32) {
	month = 1;
	day = doy;
    }
    else if (doy > 31 && doy < (60 + leap)) {
	month = 2;
	day = doy - 31;
    }
    else if (doy > (59 + leap) && doy < (91 + leap)) {
	month = 3;
	day = doy - (59 + leap);
    }
    else if (doy > (90 + leap) && doy < (121 + leap)) {
	month = 4;
	day = doy - (90 + leap);
    }
    else if (doy > (120 + leap) && doy < (152 + leap)) {
	month = 5;
	day = doy - (120 + leap);
    }
    else if (doy > (151 + leap) && doy < (182 + leap)) {
	month = 6;
	day = doy - (151 + leap);
    }
    else if (doy > (181 + leap) && doy < (213 + leap)) {
	month = 7;
	day = doy - (181 + leap);
    }
    else if (doy > (212 + leap) && doy < (244 + leap)) {
	month = 8;
	day = doy - (212 + leap);
    }
    else if (doy > (243 + leap) && doy < (274 + leap)) {
	month = 9;
	day = doy - (243 + leap);
    }
    else if (doy > (273 + leap) && doy < (305 + leap)) {
	month = 10;
	day = doy - (273 + leap);
    }
    else if (doy > (304 + leap) && doy < (335 + leap)) {
	month = 11;
	day = doy - (304 + leap);
    }
    else if (doy > 334) {
	month = 12;
	day = doy - (334 + leap);
    }
    return 1;

}

/*********************************************/
/*This program converts day/month/year to doy */

/*********************************************/

/*********************************************/

int date2doy(int *d, int *m)
{
    int leap = 0;

    int day_month_tot = 0;

    int day, month;

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
    if (DECy / 4 * 4 == DECy) {
	leap = 1;
    }

    doy = day_month_tot + day + leap;

    return (doy);
}

/**************************************************************/
/* Keep_the_best function: This function keeps track of the   */
/* best member of the population. Note that the last entry in */
/* the array Population holds a copy of the best individual.  */

/**************************************************************/

void keep_the_best(struct genotype *population)
{
    int mem;

    int i;

    cur_best = 0;		/* stores the index of the best individual */

    for (mem = 0; mem < POPSIZE; mem++) {	//yann you need to change here...
	if (population[mem].fitness > population[POPSIZE].fitness) {
	    cur_best = mem;
	    population[POPSIZE].fitness = population[mem].fitness;
	}
    }

    /* once the best member of the population is found, copy the genes */

    for (i = 0; i < NVARS; i++)
	population[POPSIZE].gene[i] = population[cur_best].gene[i];
}


/****************************************************************/
/* Elitist function: The best member of the previous generation */
/* is stored as the last in the array. If the best member of    */
/* the current generation is worse then the best member of the  */
/* previous generation, the latter one would replace the worst  */
/* member in the new population.                                */

/****************************************************************/

void elitist(struct genotype *population)
{
    int i;

    double best, worst;		/* best and worst fitness values */

    int best_mem = 0, worst_mem = 0;	/* indexes of the best and worst member */

    best = population[0].fitness;
    worst = population[0].fitness;
    for (i = 0; i < POPSIZE - 1; i++) {
	if (population[i].fitness > population[i + 1].fitness) {
	    if (population[i].fitness >= best) {
		best = population[i].fitness;
		best_mem = i;
	    }
	    if (population[i + 1].fitness <= worst) {
		worst = population[i + 1].fitness;
		worst_mem = i + 1;
	    }
	}
	else {
	    if (population[i].fitness <= worst) {
		worst = population[i].fitness;
		worst_mem = i;
	    }
	    if (population[i + 1].fitness >= best) {
		best = population[i + 1].fitness;
		best_mem = i + 1;
	    }
	}
    }

    for (i = 0; i < POPSIZE; i++) {
	if (population[i].fitness >= best) {
	    best = population[i].fitness;
	    best_mem = i;
	}
	else if (population[i].fitness <= worst) {
	    worst = population[i].fitness;
	    worst_mem = i;
	}
    }

    /* If best individual from the new populationis better than */
    /* the best individual from the previous population, then   */
    /* copy the best from the new population; else replace the  */
    /* worst individual from the current population with the    */
    /* best one from the previous generation                    */

    if (best >= population[POPSIZE].fitness) {
	for (i = 0; i < NVARS; i++)
	    population[POPSIZE].gene[i] = population[best_mem].gene[i];
	population[POPSIZE].fitness = population[best_mem].fitness;
    }
    else {
	for (i = 0; i < NVARS; i++)
	    population[worst_mem].gene[i] = population[POPSIZE].gene[i];
	population[worst_mem].fitness = population[POPSIZE].fitness;
    }
}


/*************************************************************/
/* Selection function: standard proportional selection for   */
/* maximization problems incorporating elitist model - makes */
/* sure that the best member survives.                       */

/*************************************************************/
void selection(struct genotype *population, struct genotype *newpopulation)
{
    int mem, i, j;

    double sum = 0;

    double p;

    /* find total fitness of the population */
    for (mem = 0; mem < POPSIZE; mem++) {
	sum += population[mem].fitness;
    }

    /* calculate relative fitness */
    for (mem = 0; mem < POPSIZE; mem++) {
	population[mem].rfitness = population[mem].fitness / sum;
    }
    population[0].cfitness = population[0].rfitness;

    /* Calculate cumulative fitness */
    for (mem = 1; mem < POPSIZE; mem++) {
	population[mem].cfitness =
	    population[mem - 1].cfitness + population[mem].rfitness;
    }

    /* finally select survivors using cumulative fitness. */
    for (i = 0; i < POPSIZE; i++) {
	p = rand() % 1000 / 1000.0;
	if (p < population[0].cfitness)
	    newpopulation[i] = population[0];
	else {
	    for (j = 0; j < POPSIZE; j++)
		if (p >= population[j].cfitness &&
		    p <= population[j + 1].cfitness)
		    newpopulation[i] = population[j + 1];
	}
    }

    /* Once a new population is created, copy it back */

    for (i = 0; i < POPSIZE; i++)
	population[i] = newpopulation[i];
}

/**************************************************************/
/* Crossover selection: selects two parents that take part in */
/* the crossover. Implements a single point crossover.        */

/**************************************************************/

void crossover(struct genotype *population)
{
    int mem, one = 0;

    int first = 0;		/* Count of the numbers of members chosen */

    int ii;

    int point;			/* crossover point */

    int temp;

    double x;

    for (mem = 0; mem < POPSIZE; mem++) {
	x = rand() % 1000 / 1000.0;
	if (x < PXOVER) {
	    ++first;
	    if (first % 2 == 0) {
		//Xover(one,mem);
		if (NVARS > 1) {
		    if (NVARS == 2)
			point = 1;
		    else
			point = (rand() % (NVARS - 1)) + 1;

		    for (ii = 0; ii < point; ii++) {

			temp = population[one].gene[ii];
			population[one].gene[ii] = population[mem].gene[ii];
			population[mem].gene[ii] = temp;

		    }
		}


		else
		    one = mem;
	    }			//if nested
	}			//if
    }				//for

}

/**************************************************************/
/* Mutation: random uniform mutation. A variable selected for */
/* mutation is replaced by a random value between lower and   */
/* upper bounds of this variable.                             */

/**************************************************************/

void mutate(struct genotype *population)
{
    int i, j;

    double x;

    double lbound[NVARS], ubound[NVARS];

    for (i = 0; i < POPSIZE; i++) {
	for (j = 0; j < NVARS; j++) {
	    if (j == 0) {
		lbound[j] = 60.0;
		ubound[j] = 120.0;
	    }
	    if (j == 1) {
		lbound[j] = 90.0;
		ubound[j] = 150.0;
	    }
	    if (j == 2) {
		lbound[j] = 160.0;
		ubound[j] = 200.0;
	    }
	    if (j == 3 || j == 4) {
		lbound[j] = 140.0;
		ubound[j] = 160.0;
	    }

	    population[i].lower[j] = 0.0;
	    population[i].upper[j] = 0.0;
	    population[i].lower[j] = lbound[j];
	    population[i].upper[j] = ubound[j];
	}
    }


    for (i = 0; i < POPSIZE; i++) {
	for (j = 0; j < NVARS; j++) {
	    x = rand() % 1000 / 1000.0;
	    if (x < PMUTATION) {
		/* Find the bounds on the variable to be mutated */

		population[i].gene[j] =
		    (rand() % 1000 / 1000.0) * (population[i].upper[j] -
						population[i].lower[j]) +
		    population[i].lower[j];
	    }
	}
    }
}

/**************************************************************/
/* Report function: reports progress of the simulation. Data  */
/* dumped into the output file are separated by commas        */

/**************************************************************/

void report(struct genotype *population, int generation)
{
    int i;

    double best_val;		/* best population fitness */

    double avg;			/* avg population fitness */

    double stddev;		/* std. deviation of population fitness */

    double sum_square;		/* sum of square for std. calc */

    double square_sum;		/* square of sum for std. calc */

    double sum;			/* total population fitness */

    sum = 0.0;
    sum_square = 0.0;

    for (i = 0; i < POPSIZE; i++) {
	sum += population[i].fitness;
	sum_square += population[i].fitness * population[i].fitness;
    }

    avg = sum / (double)POPSIZE;
    square_sum = avg * avg * (double)POPSIZE;
    stddev = sqrt((sum_square - square_sum) / (POPSIZE - 1));
    FECd = day;
    FECm = month;

    best_val = population[POPSIZE].fitness;

    fprintf(galog, "%5d\t	%6.3f\t %6.3f\t %6.3f \n", generation,
	    best_val, avg, stddev);
}

/**************************************************************/
/* MakeGrassCell function: output final result to a file that */
/* will be used by the GRASS module to give values to cell    */

/**************************************************************/

//void makegrasscell(struct genotype *population)
//{
//      FILE *gc;
//      int temp_doy;

//      if((gc=fopen("grass_cell.txt","w"))==NULL)
//      {
//              exit(1);
//      }


	/* Date of Emergence of Crop */
	//date2doy(&population[POPSIZE].gene[0], &population[POPSIZE].gene[1]);

	//temp_doy = doy;
	//grass_cell[0]=doy;

	//fprintf(gc,"%i\n",doy);

	/* Irrigation Scheduling Start */
	//date2doy(&population[POPSIZE].gene[2], &population[POPSIZE].gene[3]);

	//grass_cell[1]=doy;
	//fprintf(gc,"%i\n",doy);

	/* Date of Emergence of Crop + Time Extent of Cropping */
	//doy = temp_doy + population[POPSIZE].gene[4];

	//grass_cell[2]=doy;
	//fprintf(gc,"%i\n",doy);

	/* GW Level 1st Jan */

	//grass_cell[3]=population[POPSIZE].gene[5];
	//fprintf(gc,"%i\n",population[POPSIZE].gene[5]);

	/* GW Level 31st Dec */
	//grass_cell[4]=population[POPSIZE].gene[6];
	//fprintf(gc,"%i\n",population[POPSIZE].gene[6]);

	/* fitness of the best member */

	//grass_cell[5]=population[POPSIZE].fitness;
	//fprintf(gc,"%5.3f\n",population[POPSIZE].fitness);
	//fclose(gc);

//}


/*************************************************************/

/*******************************************************/
/*                                                     */
/* SWAP forward with best fitness individual values    */

/*******************************************************/
/*
   void swap(void)
   {
   int i;
   FILE *f;

   if((f=fopen("ET.csv","w"))==NULL)
   {
   exit(1);
   }

   DECdoy =(int) (population[POPSIZE].gene[0]);
   STSdoy =(int) (population[POPSIZE].gene[1]);
   TECdoy =(int) (population[POPSIZE].gene[2]);
   GWJan =(int) (population[POPSIZE].gene[3]);
   GWDec =(int) (population[POPSIZE].gene[4]);  

   doy2date(&DECdoy,&DECy);
   DECd=day;
   DECm=month;
   day=0;
   month=0;

   doy2date(&STSdoy,&STSy);
   STSd=day;
   STSm=month;
   day=0;
   month=0;     

   printf("Making the SWAP_ET data\n");


   finput2();
   system("./swap");
   foutput();

   fprintf(f,"satETa,swapETa\n");       
   for(i=0;i<NSATEL;i++) {
   fprintf(f,"%2.3f,%2.3f\n",satETA[i],swapETA[i]);
   }
   fclose(f);
   }

 */

/*******************************************************/
/*                                                     */
/* Getting ETa from SWAP INC.file => swap.eta          */
/*         and merging it with satellite.eta file      */
/*         Resulting file => eval.eta                  */
/*         Format of eval.eta: ETaRS ETaSWAP\n         */

/*******************************************************/


/********************************************************/

int foutput(void)
{
    satellite_dates();
    return 1;
}

/********************************************************/


/********************************************************/

int get_eta(char *dateName, char *dateNameValue, int dateCounter)
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
			swapETA[dateCounter] = (TRA + EVS);
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
/* Thanks Dr Honda!                                    */
/*                                                     */
/* Limited to 99 images so far...                      */

/*******************************************************/

int satellite_dates()
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

    int dateCounter = 0;

    char buf[BUFLEN];

    //fp=fopen("satellite.dates","rt");
    //if (!fp)
    //    return 1;

    //iline = 1;
    //i = 1;

    // while (fgets( buf, BUFLEN, fp) != NULL) {
    for (i = 1; i <= NSATEL; i++) {
	if (sscanf(satDATE[i], "%d/%d/%d", &t.tm_mday, &t.tm_mon, &t.tm_year)
	    != 3) {
	    fprintf(stderr, "reading problem; line : %d: %s\n", iline, buf);
	    //fclose(fp);
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
	get_eta(dateName, dateNameValue, dateCounter);	/* send the sat.date to get_eta() */
	dateCounter++;
	//iline++;
    }
    //(void)fclose(fp);
    return 1;
}



/*************************************************************/


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

void finput1(void)
{
    swapkey();
    calfil();
    capfil();
    swafil();
    bbcfil();
    crpfil();
    sol1fil();
    sol2fil();
    sol3fil();
    sol4fil();
    sol5fil();
}

void finput2(void)
{
    calfil();
    bbcfil();
    crpfil();
}

/********************************************************/
/* FILE *swapkey; an input to SWAP                      */

/********************************************************/

void swapkey(void)
{
    FILE *swapkey;		/* SWAP.KEY file-variable */

    swapkey = fopen("SWAP.KEY", "w");

    fputs(" Project = 'Rood'\n", swapkey);
    fputs(" Path = ''\n", swapkey);
    fputs(" CType = 1\n", swapkey);
    fputs(" SWSCRE = 0\n\n", swapkey);

    fprintf(swapkey, " SSRUN = 01 01 %d\n", SSRUN);
    //fputs(" SSRUN = 01 01 1991\n", swapkey); /*variable only year*/
    fprintf(swapkey, " ESRUN = 31 12 %d\n", ESRUN);
    //fputs(" ESRUN = 31 12 1991\n", swapkey); /*variable only year*/
    fputs(" FMAY = 1\n", swapkey);
    fputs(" Period = 1\n", swapkey);
    fputs(" SWRES = 1\n\n", swapkey);

    fputs(" SWODAT = 0\n", swapkey);
    fputs("*\n", swapkey);
    fputs("* DD MM YYYY\n", swapkey);
    fputs("* End_of_table\n\n", swapkey);

    fprintf(swapkey, " METFIL = \'%s\'\n", METFIL);
    //fputs(" METFIL = 'ESF'\n", swapkey); /*variable*/
    fprintf(swapkey, " LAT = %lf\n", LAT);
    //fputs(" LAT = 32.4\n", swapkey);   /* variable*/
    fprintf(swapkey, " ALT = %lf\n", ALT);
    //fputs(" ALT = 1600.0\n", swapkey); /*variable*/
    fputs(" SWETR = 0\n", swapkey);
    fputs(" SWRAI = 0\n\n", swapkey);

    fputs("* IRGFIL CALFIL   DRFIL   BBCFIL  OUTFIL\n", swapkey);
    fputs("  ''     'RoodC'  'none'  'Rood'  'out'\n", swapkey);
    fputs("* End_of_table\n\n", swapkey);

    fputs(" SWDRA = 0\n\n", swapkey);

    fputs(" SWSOLU = 0\n\n", swapkey);

    fputs(" SWHEA = 0\n\n", swapkey);

    fputs(" SWVAP = 0\n\n", swapkey);

    fputs(" SWDRF = 0\n\n", swapkey);

    fputs(" SWSWB = 0\n\n", swapkey);

    fputs(" SWAFO = 0\n", swapkey);
    fputs(" AFONAM = 'testA'\n\n", swapkey);

    fputs(" SWAUN = 0\n", swapkey);
    fputs(" AUNNAM = 'testA'\n\n", swapkey);

    fputs(" SWATE = 0\n", swapkey);
    fputs(" ATENAM = 'testA'\n\n", swapkey);

    fputs(" SWAIR = 0\n", swapkey);
    fputs(" AIRNAM = 'testA'\n\n", swapkey);

    (void)fclose(swapkey);
    return;
}

/********************************************************/
/* CAL-file                                             */

/********************************************************/

void calfil(void)
{
    FILE *calfil;		/* RoodC.CAL file_variable */

    calfil = fopen("RoodC.CAL", "w");

    fputs("* CRPFIL Type CAPFIL  EMERGENCE END_crop START_sch\n", calfil);
    fputs("*                     d1 m1     d2 m2    d3 m3\n", calfil);
    fprintf(calfil, " 'Crop'  1    'RoodC' %i %i     %i %i    %i %i\n", DECd,
	    DECm, FECd, FECm, STSd, STSm);
    fputs("* End_of_table\n\n", calfil);

    (void)fclose(calfil);
    return;
}

/*******************************************************/
/* CAP-file                                            */

/*******************************************************/

void capfil(void)
{
    FILE *capfil;		/* RoodC.CAP file_variable */

    capfil = fopen("RoodC.CAP", "w");

    fputs(" ISUAS = 1\n\n", capfil);
    fputs(" CIRRS = 2.56\n\n", capfil);

    fputs(" TCS1 = 0\n", capfil);
    fputs("* DVS  Ta/Tp\n", capfil);
    fputs("0.0 0.75\n", capfil);
    fputs("2.0 0.75\n", capfil);
    fputs("* End of table\n\n", capfil);

    fputs("TCS2 = 0\n", capfil);
    fputs("* DVS  RAW\n", capfil);
    fputs("  0.0  0.95\n", capfil);
    fputs("  2.0  0.95\n", capfil);
    fputs("* End of table\n\n", capfil);

    fputs("TCS3 = 0\n", capfil);
    fputs("* DVS  TAW\n", capfil);
    fputs("  0.0  0.50\n", capfil);
    fputs("  2.0  0.50\n", capfil);
    fputs("* End of table\n\n", capfil);

    fputs("TCS4 = 0\n", capfil);
    fputs("* DVS  DWA\n", capfil);
    fputs("  0.0  40.0\n", capfil);
    fputs("  2.0  40.0\n", capfil);
    fputs("* End of table\n\n", capfil);

    fputs(" TCS5 = 1\n", capfil);
    fputs(" PHORMC = 0\n", capfil);
    fputs(" DCRIT = 0.0\n", capfil);
    fputs("* DVS  VALUE\n", capfil);
    fputs("  0.0  1.0\n", capfil);
    fputs("  2.0  1.0\n", capfil);
    fputs("* End of table\n\n", capfil);

    fputs(" DCS1 = 0\n", capfil);
    fputs("* DVS  dI\n", capfil);
    fputs("  0.0  0.0\n", capfil);
    fputs("  2.0  0.0\n", capfil);
    fputs("* End of table\n\n", capfil);

    fputs(" DCS2 = 1\n", capfil);
    fputs("* DVS  FID\n", capfil);
    fputs("  0.0  100.0\n", capfil);
    fputs("  2.0  100.0\n", capfil);
    fputs("* End of table\n\n", capfil);

    (void)fclose(capfil);
    return;
}

/*******************************************************/
/* SWA-file                                            */

/*******************************************************/

void swafil(void)
{
    FILE *swafil;		/* Rood.SWA file_variable */

    //double  tex[4];

    /* Get soil texture percentages */
    /*      if ((soil = fopen("soil.txt","r")) == NULL)
       {
       printf("Cannot open soil texture data file!\n");
       exit(1);
       }

       for (i=0;i<4;i++)
       {
       fscanf(soil, "%lf", &texture);
       tex[i]=texture;
       }
       /
       fclose(soil);

	 *//********************************/

    swafil = fopen("Rood.SWA", "w");

    fputs
	("*******************************************************************************\n",
	 swafil);
    fputs(" PONDMX = 10.0\n\n", swafil);
    fputs
	("*******************************************************************************\n\n",
	 swafil);

    fputs
	("*******************************************************************************\n",
	 swafil);
    fputs(" SWCFBS = 0\n", swafil);
    fputs(" CFBS = 0.9\n", swafil);
    fputs(" SWREDU = 2\n", swafil);
    fputs(" COFRED = 0.35\n", swafil);
    fputs(" RSIGNI = 0.5\n\n", swafil);
    fputs
	("*******************************************************************************\n\n",
	 swafil);

    fputs
	("*******************************************************************************\n",
	 swafil);
    fputs(" DTMIN = 1.0E-4\n", swafil);
    fputs(" DTMAX = 0.1\n", swafil);
    fputs(" SWNUMS = 2\n", swafil);
    fputs(" THETOL = 0.01\n\n", swafil);
    fputs
	("*******************************************************************************\n\n",
	 swafil);

    fputs
	("*******************************************************************************\n",
	 swafil);
    fputs(" NUMLAY = 5\n", swafil);
    fputs(" NUMNOD = 50\n\n", swafil);

    fputs(" BOTCOM = 14 19 22 26 50\n", swafil);
    fputs("*\n", swafil);
    fputs("* thickness of soil compartments [cm]:\n", swafil);
    fputs("* total 500 cm\n", swafil);
    fputs("*\n", swafil);
    fputs(" DZ =\n", swafil);
    fputs
	("     1.0     1.0     1.0     1.0     1.0     1.0     1.0     1.0     1.0     1.0\n",
	 swafil);
    fputs
	("     5.0     5.0     5.0     5.0     5.0     5.0     5.0     5.0     5.0     5.0\n",
	 swafil);
    fputs
	("    10.0    10.0    10.0    10.0    10.0    10.0    10.0    10.0    10.0    10.0\n",
	 swafil);
    fputs
	("    10.0    10.0    10.0    10.0    10.0    10.0    10.0    10.0    10.0    10.0\n",
	 swafil);
    fputs
	("    20.0    20.0    20.0    20.0    20.0    20.0    20.0    20.0    40.0    40.0\n",
	 swafil);
    fputs
	("*******************************************************************************\n\n",
	 swafil);

    fputs
	("*******************************************************************************\n",
	 swafil);
    fputs(" SOLFIL = 'Rood_1' 'Rood_2' 'Rood_3' 'Rood_4' 'Rood_5'\n\n",
	  swafil);
    fputs("* PSAND  PSILT  PCLAY  ORGMAT\n", swafil);
    //fputs("  0.21   0.44   0.34   0.0051\n",swafil);
    //fputs("  0.10   0.26   0.64   0.0039\n",swafil);
    //fputs("  0.04   0.28   0.68   0.0031\n",swafil);
    //fputs("  0.02   0.50   0.48   0.0023\n",swafil);
    //fputs("  0.08   0.60   0.32   0.0020\n",swafil);

    fprintf(swafil, "  %lf   %lf   %lf   %lf\n", tex[0], tex[1], tex[2],
	    tex[3]);
    fprintf(swafil, "  %lf   %lf   %lf   %lf\n", tex[0], tex[1], tex[2],
	    tex[3]);
    fprintf(swafil, "  %lf   %lf   %lf   %lf\n", tex[0], tex[1], tex[2],
	    tex[3]);
    fprintf(swafil, "  %lf   %lf   %lf   %lf\n", tex[0], tex[1], tex[2],
	    tex[3]);
    fprintf(swafil, "  %lf   %lf   %lf   %lf\n\n", tex[0], tex[1], tex[2],
	    tex[3]);

    fputs
	("*******************************************************************************\n\n",
	 swafil);

    fputs(" RDS = 300.0\n\n", swafil);

    fputs(" SWHYST = 0\n", swafil);
    fputs(" TAU = 0.2\n\n", swafil);

    fputs(" SWSCAL = 0\n", swafil);
    fputs(" NSCALE = 0\n", swafil);
    fputs(" ISCLAY = 0\n", swafil);
    /*      fputs(" FSCALE =\n", swafil);
       fputs("   0.00   0.00   0.00   0.00   0.00   0.00   0.00   0.00   0.00   0.00\n", swafil);
       fputs("   0.00   0.00   0.00   0.00   0.00   0.00   0.00   0.00   0.00   0.00\n", swafil);
       fputs("   0.00   0.00   0.00   0.00   0.00   0.00   0.00   0.00   0.00   0.00\n\n", swafil); */

    fputs(" SWMOBI = 0\n", swafil);
    fputs("* PF1  FM1  PF2  FM2  THETIM\n", swafil);
    fputs("  0.0  0.0  0.0  0.0  0.0\n", swafil);
    fputs("  0.0  0.0  0.0  0.0  0.0\n", swafil);
    fputs("* End_of_table\n\n", swafil);

    fputs(" SWCRACK = 0\n", swafil);
    fputs(" SHRINA = 0.53\n", swafil);
    fputs(" MOISR1 = 1.0\n", swafil);
    fputs(" MOISRD = 0.05\n", swafil);
    fputs(" ZNCRACK = -5.0\n", swafil);
    fputs(" GEOMF = 3.0\n", swafil);
    fputs(" DIAMPOL = 40.0\n", swafil);
    fputs(" RAPCOEF = 0.0\n", swafil);
    fputs(" DIFDES = 0.2\n", swafil);
    fputs(" THETCR = 0.50  0.50  0.50  0.50  0.50\n\n", swafil);

    fputs(" SWDIVD = 0\n", swafil);
    fputs(" COFANI =    1.0    1.0    1.0    1.0    1.0\n\n", swafil);

    fputs(" SWINCO = 2\n", swafil);
    /*      fputs(" HI =\n", swafil);
       fputs("    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0\n", swafil);
       fputs("    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0\n", swafil);
       fputs("    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0\n", swafil);
       fputs("    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0\n", swafil); */
    fputs(" GWLI = -200.0\n", swafil);
    fputs(" OSGWLM = 30.0\n\n", swafil);

    (void)fclose(swafil);
    return;
}

/*******************************************************/
/* BBC-file                                            */

/*******************************************************/

void bbcfil(void)
{
    FILE *bbcfil;		/* Rood.BBC file_variable */

    bbcfil = fopen("Rood.BBC", "w");

    fputs(" SWOPT1 = 1\n", bbcfil);
    fputs("* d1 m1 GWlevel\n", bbcfil);
    fprintf(bbcfil, "  1  1 -%i.0\n", GWJan);
    fprintf(bbcfil, " 31 12 -%i.0\n", GWDec);
    /*      fputs("   1  1 -150.0\n", bbcfil);
       fputs("  31 12 -150.0\n", bbcfil);
     */ fputs("* End of table\n\n", bbcfil);

    fputs(" SWOPT2 = 0\n", bbcfil);
    fputs(" SWC2 = 2\n", bbcfil);
    fputs(" C2AVE = 0.1\n", bbcfil);
    fputs(" C2AMP = 0.05\n", bbcfil);
    fputs(" C2STA = 91\n", bbcfil);
    fputs("* d2 m2 Qbot\n", bbcfil);
    fputs("   1  1 0.10\n", bbcfil);
    fputs("   5  6 0.20\n", bbcfil);
    fputs("  31 12 0.10\n", bbcfil);
    fputs("* End of table\n\n", bbcfil);

    fputs(" SWOPT3 = 0\n", bbcfil);
    fputs(" SHAPE = 0.79\n", bbcfil);
    fputs(" RIMLAY = 500\n", bbcfil);
    fputs(" AQAVE = 50.0\n", bbcfil);
    fputs(" AQAMP = 20.0\n", bbcfil);
    fputs(" AQTAMX = 120\n", bbcfil);
    fputs(" AQPER = 365\n\n", bbcfil);

    fputs(" SWOPT4 = 0\n", bbcfil);
    fputs(" COFQHA = -0.3\n", bbcfil);
    fputs(" COFQHB = -0.01\n\n", bbcfil);

    fputs(" SWOPT5 = 0\n", bbcfil);
    fputs("* d5 m5 GWlevel\n", bbcfil);
    fputs("   1  1  50.0\n", bbcfil);
    fputs("  31 12  20.0\n", bbcfil);
    fputs("* End of table\n\n", bbcfil);

    fputs(" SWOPT6 = 0\n", bbcfil);
    fputs(" SWOPT7 = 0\n", bbcfil);
    fputs(" SWOPT8 = 0\n", bbcfil);


    (void)fclose(bbcfil);
    return;
}

/********************************************************/
/* CRP-file                                             */

/********************************************************/

void crpfil(void)
{
    FILE *crpfil;		/* Crop.CRP file_variable */

    crpfil = fopen("Crop.CRP", "w");

    fputs(" IDEV = 1\n", crpfil);
    //      fputs(" LCC = 180\n", crpfil);
    fprintf(crpfil, "LCC = %i\n", TECdoy);
    fputs(" TSUMEA = 1050.0\n", crpfil);
    fputs(" TSUMAM = 1000.0\n", crpfil);
    fputs(" TBASE = 0.0\n\n", crpfil);

    fputs(" KDIF = 0.6\n", crpfil);
    fputs(" KDIR = 0.75\n\n", crpfil);

    fputs(" SWGC = 1\n", crpfil);
    fputs("*    DVS   LAI or SCF\n", crpfil);
    fputs(" GCTB =\n", crpfil);
    fputs("     0.0    0.00\n", crpfil);
    fputs("     0.2    0.07\n", crpfil);
    fputs("     0.4    0.16\n", crpfil);
    fputs("     0.6    0.61\n", crpfil);
    fputs("     0.8    1.25\n", crpfil);
    fputs("     1.0    1.73\n", crpfil);
    fputs("     1.2    1.75\n", crpfil);
    fputs("     1.4    1.73\n", crpfil);
    fputs("     1.6    1.71\n", crpfil);
    fputs("     1.8    1.04\n", crpfil);
    fputs("     2.0    0.58\n", crpfil);
    fputs("**************\n\n", crpfil);

    fputs(" SWCF = 2\n", crpfil);
    fputs("*        DVS   CF or CH\n", crpfil);
    fputs(" CFTB = 0.00   0.0\n", crpfil);
    fputs("        1.00  70.0\n", crpfil);
    fputs("        2.00  70.0\n\n", crpfil);

    fputs("*         DVS   RD\n", crpfil);
    fputs(" RDTB = 0.00   0.0\n", crpfil);
    fputs("        1.00 100.0\n", crpfil);
    fputs("        2.00 100.0\n\n", crpfil);

    fputs("*        DVS   KY\n", crpfil);
    fputs(" KYTB = 0.0   0.2\n", crpfil);
    fputs("        0.4   0.2\n", crpfil);
    fputs("        0.9   0.5\n", crpfil);
    fputs("        1.5   0.5\n", crpfil);
    fputs("        2.0   0.3\n\n", crpfil);
    fputs("**************\n\n", crpfil);

    fputs(" HLIM1 = -0.1\n", crpfil);
    fputs(" HLIM2U = -30.0\n", crpfil);
    fputs(" HLIM2L = -30.0\n", crpfil);
    fputs(" HLIM3H = -100.0\n", crpfil);
    fputs(" HLIM3L = -200.0\n", crpfil);
    fputs(" HLIM4 = -16000.0\n", crpfil);
    fputs(" RSC = 70.0\n", crpfil);
    fputs(" ADCRH = 0.5\n", crpfil);
    fputs(" ADCRL = 0.1\n\n", crpfil);

    fputs(" ECMAX = 7.7\n", crpfil);
    fputs(" ECSLOP = 5.0\n\n", crpfil);

    fputs(" COFAB = 0.25\n\n", crpfil);

    fputs("*        Rdepth Rdensity\n", crpfil);
    fputs(" RDCTB = 0.0    1.0\n", crpfil);
    fputs("         1.0    0.0\n", crpfil);
    fputs("**************\n", crpfil);

    (void)fclose(crpfil);
    return;
}

/*******************************************************/
/* SOL-file number 1                                   */

/*******************************************************/

void sol1fil(void)
{

    FILE *sol1fil;		/* Rood_1.SOL file_variable */

    sol1fil = fopen("Rood_1.SOL", "w");

    fputs(" SWPHYS = 1\n\n", sol1fil);

    fputs(" COFGEN1 = 0.000\n", sol1fil);
    fputs(" COFGEN2 = 0.492\n", sol1fil);
    fputs(" COFGEN3 = 0.500\n", sol1fil);
    fputs(" COFGEN4 = 0.02638\n", sol1fil);
    fputs(" COFGEN5 = -2.196\n", sol1fil);
    fputs(" COFGEN6 = 1.1775\n", sol1fil);
    fputs(" COFGEN8 = 0.029\n", sol1fil);
    fputs("* End of file\n", sol1fil);

    (void)fclose(sol1fil);
    return;
}

/*******************************************************/
/* SOL-file number 2                                   */

/*******************************************************/

void sol2fil(void)
{

    FILE *sol2fil;		/* Rood_2.SOL file_variable */

    sol2fil = fopen("Rood_2.SOL", "w");

    fputs(" SWPHYS = 1\n\n", sol2fil);

    fputs(" COFGEN1 = 0.000\n", sol2fil);
    fputs(" COFGEN2 = 0.516\n", sol2fil);
    fputs(" COFGEN3 = 30.206\n", sol2fil);
    fputs(" COFGEN4 = 0.01216\n", sol2fil);
    fputs(" COFGEN5 = 0.046\n", sol2fil);
    fputs(" COFGEN6 = 1.1471\n", sol2fil);
    fputs(" COFGEN8 = 0.013\n", sol2fil);
    fputs("* End of file\n", sol2fil);

    (void)fclose(sol2fil);
    return;
}

/*******************************************************/
/* SOL-file number 3                                   */

/******************************10194*************************/

void sol3fil(void)
{

    FILE *sol3fil;		/* Rood_3.SOL file_variable */

    sol3fil = fopen("Rood_3.SOL", "w");

    fputs(" SWPHYS = 1\n\n", sol3fil);

    fputs(" COFGEN1 = 0.000\n", sol3fil);
    fputs(" COFGEN2 = 0.501\n", sol3fil);
    fputs(" COFGEN3 = 2.295\n", sol3fil);
    fputs(" COFGEN4 = 0.00778\n", sol3fil);
    fputs(" COFGEN5 = 0.251\n", sol3fil);
    fputs(" COFGEN6 = 1.0829\n", sol3fil);
    fputs(" COFGEN8 = 0.009\n", sol3fil);
    fputs("* End of file\n", sol3fil);

    (void)fclose(sol3fil);
    return;
}

/*******************************************************/
/* SOL-file number 4                                   */

/*******************************************************/

void sol4fil(void)
{

    FILE *sol4fil;		/* Rood_4.SOL file_variable */

    sol4fil = fopen("Rood_4.SOL", "w");

    fputs(" SWPHYS = 1\n\n", sol4fil);

    fputs(" COFGEN1 = 0.000\n", sol4fil);
    fputs(" COFGEN2 = 0.431\n", sol4fil);
    fputs(" COFGEN3 = 4.331\n", sol4fil);
    fputs(" COFGEN4 = 0.01379\n", sol4fil);
    fputs(" COFGEN5 = -2.743\n", sol4fil);
    fputs(" COFGEN6 = 1.0818\n", sol4fil);
    fputs(" COFGEN8 = 0.015\n", sol4fil);
    fputs("* End of file\n", sol4fil);

    (void)fclose(sol4fil);
    return;
}

/*******************************************************/
/* SOL-file number 5                                   */

/*******************************************************/

void sol5fil(void)
{

    FILE *sol5fil;		/* Rood_5.SOL file_variable */

    sol5fil = fopen("Rood_5.SOL", "w");

    fputs(" SWPHYS = 1\n\n", sol5fil);

    fputs(" COFGEN1 = 0.000\n", sol5fil);
    fputs(" COFGEN2 = 0.424\n", sol5fil);
    fputs(" COFGEN3 = 9.843\n", sol5fil);
    fputs(" COFGEN4 = 0.01667\n", sol5fil);
    fputs(" COFGEN5 = -1.982\n", sol5fil);
    fputs(" COFGEN6 = 1.1307\n", sol5fil);
    fputs(" COFGEN8 = 0.018\n", sol5fil);
    fputs("* End of file\n", sol5fil);

    (void)fclose(sol5fil);
    return;
}

/********************************************************/
