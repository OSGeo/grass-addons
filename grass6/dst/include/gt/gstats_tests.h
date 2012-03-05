/* Some high-level statistical tests */

#ifndef __GSTATS_TESTS_H__
#define __GSTATS_TESTS_H__

double gstats_test_XF (int *observed, int *expected, int k, int df);
double gstats_rtest_XF (int *observed, int *expected, int k, int df);
double gstats_test_ZP2 (double p_sample, double p_population, int n);
double gstats_test_ZPL (double p_sample, double p_population, int n);
double gstats_test_ZPU (double p_sample, double p_population, int n);


#endif /* __GSTATS_TESTS_H__ */
