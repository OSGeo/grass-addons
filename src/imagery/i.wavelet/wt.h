int dwt_l2(double *signal, int length, double *LP1, double *HP1, double *HP2,
           double *LP2, double *h, double *g, int l);

/** REVERSE MODE FUNCTION **/
int idwt_l2(double *LP1, double *HP1, double *LP2, double *HP2, int length,
            double *out, double *h, double *g, int l);
