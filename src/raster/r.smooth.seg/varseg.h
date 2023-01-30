/** MS_N --- MUMFORD-SHAH (Gauss-Seidel method) **/
void ms_n(double *, double *, double *, double, double, double, double *, int,
          int);

/** MSK_N --- MUMFORD-SHAH with CURVATURE term (Gauss-Seidel method) **/
void msk_n(double *, double *, double *, double, double, double, double,
           double *, int, int);

/** MS_O --- MUMFORD-SHAH (Jacobi method) **/
void ms_o(double *, double *, double *, double, double, double, double *, int,
          int);

/** MSK_O --- MUMFORD-SHAH with CURVATURE term (Jacobi method) **/
void msk_o(double *, double *, double *, double, double, double, double,
           double *, int, int);

/** MS_T --- TEST --- MUMFORD-SHAH (Gauss-Seidel method) - (Different
 * approximation of "u" wrt MS_N) **/
void ms_t(double *, double *, double *, double, double, double, double *, int,
          int);

/** MSK_T --- TEST --- MUMFORD-SHAH with CURVATURE term (Gauss-Seidel method) -
 * (Different approximation of "u" wrt MSK_N) **/
void msk_t(double *, double *, double *, double, double, double, double,
           double *, int, int);
