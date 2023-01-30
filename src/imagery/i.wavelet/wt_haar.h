/*Descomposition of a signal following the Haar wavelet method for 2 levels*/
int dwt_haar_l2(double *signal, int length, double *LP1, double *HP1,
                double *LP2, double *HP2);

/*Recomposition of a signal from its three wavelet coefs from Level 1 & 2: HP1
 * available, LP1 made by LP2 & HP2*/
int idwt_haar_l2(double *LP1, double *HP1, double *LP2, double *HP2, int length,
                 double *out);
