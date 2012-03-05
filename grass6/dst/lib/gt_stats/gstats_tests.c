#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include <gsl/gsl_types.h>>
#include <gsl/gsl_integration.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_cdf.h>

#include <grass/gis.h>

#include "gt/gstats_error.h"



/* Purpose: chi square test for differences in frequencies between sample and 
            population
   Parameters:	*observed = array of ints with event counts for each category
   				in the sample
   		*expected = array of ints with event counts for each category 
				as expected from the known population
   		k = number of categories
		df = degrees of freedom (e.g. k-1)
   Returns:	Probability of making an error when rejecting the NULL hypothesis
   		-1 if data does not support Chi^2 test
*/	    
double gstats_test_XF (int *observed, int *expected, int k, int df) {
	double chi;
	int i;
	long sum, sum2;
	double checksum;
	int lessThanFive;

	if ( df < 1 ) {
		gstats_error ("Chi^2 test: need at least one category with expected frequency > 0.");
		return (-1);
	}
		
	if ( k < 2 ) {
		gstats_error ("Chi^2 test: number of categories must be > 1.");
		return (-1);
	}
			
	lessThanFive = 0; /* keeps count of categories with < 1 expected frequency */
	
	/* check if parameters given make sense */	
	sum = 0;
	sum2 = 0;
	for (i = 0; i < k; i++) {
		sum = sum + observed [i];
		sum2 = sum2 + expected [i];
	}

	if ( sum < 2 ) {
		gstats_error ("Chi^2 test: sum of observed frequencies over all categories must be > 2.");
		return (-1);
	}
	
	if ( sum2 < 2 ) {
		gstats_error ("Chi^2 test: sum of expected frequencies over all categories must be > 2.");
		return (-1);
	}
		
	/* finally, calculate Chi! */
	chi = 0;
	for (i = 0; i < k; i++) {
		if (expected[i] > 0) {
			chi = chi + ( ((float) ((observed[i]-expected[i])*(observed[i]-expected[i])) / expected[i]) );				
			if (expected[i] < 5) {
				lessThanFive ++;
			}
		}
		else {
			gstats_error ("Chi^2 test: expected frequency for category < 1.");
			return (-1);			
		}
	}

	/* check if more than 20% of categories have less than 5 observations */
	checksum = lessThanFive / ((double) (k)/100.0);
	if (checksum > 20) {
		gstats_error ("Chi^2 test: more than 20% of categories have an expected frequency < 5.");
		return (-1);
	}
	
	return (gsl_ran_chisq_pdf (chi, (double) df));
}



/* Purpose: Relaxed chi square test for differences in frequencies between observed and 
            expected frequencies. This version keeps going, even if expected frequencies (E) are < 5 in
	    more than 20% of the categories. This also excludes skips categories that
	    have E = 0, reducing degrees of freedom accordingly.	    
   Parameters:	*observed = array of ints with event counts for each category
   				in the sample
   		*expected = array of ints with event counts for each category 
				as expected from the known population
   		k = number of categories
		df = degrees of freedom (e.g. k-1)		
   Returns:	Probability of making an error when rejecting the NULL hypothesis
   		-1 if data does not support Chi^2 test
*/	    
double gstats_rtest_XF (int *observed, int *expected, int k, int df) {
	double chi;
	int i;
	long sum, sum2;

	if ( df < 1 ) {
		gstats_error ("Chi^2 test: need at least one category with expected frequency > 0.");
		return (-1);
	}
		
	if ( k < 2 ) {
		gstats_error ("Chi^2 test: number of categories must be > 1.");
		return (-1);
	}
			
	/* check if parameters given make sense */	
	sum = 0;
	sum2 = 0;
	for (i = 0; i < k; i++) {
		sum = sum + observed [i];
		sum2 = sum2 + expected [i];
	}

	if ( sum < 2 ) {
		gstats_error ("Chi^2 test: sum of observed frequencies over all categories must be > 2.");
		return (-1);
	}
	
	if ( sum2 < 2 ) {
		gstats_error ("Chi^2 test: sum of expected frequencies over all categories must be > 2.");
		return (-1);
	}
		
	/* finally, calculate Chi! */
	chi = 0;
	for (i = 0; i < k; i++) {
		if (expected[i] > 0) {
			chi = chi + ( ((float) ((observed[i]-expected[i])*(observed[i]-expected[i])) / expected[i]) );
		}
		else {
			df --;
			if ( df < 1 ) {
				gstats_error ("Chi^2 test: need at least one category with expected frequency > 0.");
				return (-1);
			}
		}
	}
		
	return (gsl_ran_chisq_pdf (chi, (double) df));
}


/* Purpose: calculate z test for proportions, two-tailed for two-sided hypothesis H1 != H0
   Parameters:  p_sample = proportion of events in sample [0..1] 
	 	p_population  = proportion of events in population [0..1] 
 		n  = sample size 
   Returns: Probability of making an error when rejecting the NULL hypothesis 
*/
double gstats_test_ZP2 (double p_sample, double p_population, int n) {
	double z;
	double result = 0.0;
	
	
	if ((p_sample < 0.0) || (p_sample > 1.0)) {
		gstats_error ("z-stat: sample proportion must be given as 0.0 - 1.0.");
	}
	
	if ((p_population < 0.0) || (p_population > 1.0)) {
		gstats_error ("z-stat: population proportion must be given as 0.0 - 1.0.");
	}
	
	if (n < 2) {
		gstats_error ("z-stat: size of population must be a positive integer > 0.");
	}
	
	z = (p_sample - p_population) / 
	    (sqrt ( (p_population * (1-p_population)) / n) );
	
	/* determine direction of numeric integration */
	if ( p_sample > p_population ) {		
		/* we use a normal distribution, if n is at least 30, */
		/* t-distribution with n - 1 degress of freedom, otherwise */
		if (n >= 30) {
			result = gsl_cdf_ugaussian_Q (z);
		} else {
			result = gsl_cdf_tdist_Q (z, (double) n-1);
		}
	}
	if ( p_sample < p_population ) {
		/* we use a normal distribution, if n is at least 30, */
		/* t-distribution with n - 1 degress of freedom, otherwise */
		if (n >= 30) {
			result = gsl_cdf_ugaussian_P (z);
		} else {
			result = gsl_cdf_tdist_P (z, (double) n-1);
		}
	}
	if ( p_sample == p_population ) {
		result = 0.5;
	}
	
	return (result * 2);	
}


/* Purpose: calculate z test for proportions, lower tail for one-sided hypothesis H1 < H0 
   Parameters:  p_sample = proportion of events in sample [0..1] 
	 	p_population  = proportion of events in population [0..1] 
 		n  = sample size 
   Returns: Probability of making an error when rejecting the NULL hypothesis 
*/
double gstats_test_ZPL (double p_sample, double p_population, int n) {
	double z;
	double result = 0.0;
	
	
	if ((p_sample < 0.0) || (p_sample > 1.0)) {
		gstats_error ("z-stat: sample proportion must be given as 0.0 - 1.0.");
	}
	
	if ((p_population < 0.0) || (p_population > 1.0)) {
		gstats_error ("z-stat: population proportion must be given as 0.0 - 1.0.");
	}
	
	if (n < 2) {
		gstats_error ("z-stat: size of population must be a positive integer > 0.");
	}
	
	if (p_sample > p_population) {
		gstats_error ("z-stat: sample prop. > population prop., cannot calculate lower tail of distribution."); 
	}
	
	z = (p_sample - p_population) / 
	    (sqrt ( (p_population * (1-p_population)) / n) );
	
	/* determine direction of numeric integration */
	if ( p_sample < p_population ) {
		/* we use a normal distribution, if n is at least 30, */
		/* t-distribution with n - 1 degress of freedom, otherwise */
		if (n >= 30) {
			result = gsl_cdf_ugaussian_P (z);
		} else {
			result = gsl_cdf_tdist_P (z, (double) n-1);
		}
	}
	if ( p_sample == p_population ) {
		result = 0.5;
	}
	
	return (result);	
}


/* Purpose: calculate z test for proportions, upper tail for one-sided hypothesis H1 > H0
   Parameters:  p_sample = proportion of events in sample [0..1] 
	 	p_population  = proportion of events in population [0..1] 
 		n  = sample size 
   Returns: Probability of making an error when rejecting the NULL hypothesis 
*/
double gstats_test_ZPU (double p_sample, double p_population, int n) {
	double z;
	double result = 0.0; 
	
	
	if ((p_sample < 0.0) || (p_sample > 1.0)) {
		gstats_error ("z-stat: sample proportion must be given as 0.0 - 1.0.");
	}
	
	if ((p_population < 0.0) || (p_population > 1.0)) {
		gstats_error ("z-stat: population proportion must be given as 0.0 - 1.0.");
	}
	
	if (n < 2) {
		gstats_error ("z-stat: size of population must be a positive integer > 0.");
	}
	
	if (p_sample < p_population) {
		gstats_error ("z-stat: sample prop. < population prop., cannot calculate upper tail of distribution."); 
	}
	
	z = (p_sample - p_population) / 
	    (sqrt ( (p_population * (1-p_population)) / n) );
	
	/* determine direction of numeric integration */
	if ( p_sample > p_population ) {
		/* we use a normal distribution, if n is at least 30, */
		/* t-distribution with n - 1 degress of freedom, otherwise */
		if (n >= 30) {
			result = gsl_cdf_ugaussian_Q (z);
		} else {
			result = gsl_cdf_tdist_Q (z, (double) n-1);
		}
	}
	if ( p_sample == p_population ) {
		result = 0.5;
	}
	
	return (result);	
}
