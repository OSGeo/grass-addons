
float velocita_breccia(int i,double h);

/*Funzione per risolvere le shallow water equations
originariamente sviluppata per r.damflood (GRASS command)
nel caso generico dare una matrice con 2 raster di 0 **m_DAMBREAK & **m_lake
e method=3

returns void
*/
/* Function to solve Shallow Water Equations
Originally developed for r.damflood (GRASS module)
In the generic case give a matrix with 2 rasters of 0 **m_DAMBREAK & **m_lake
and method=3

returns void
*/

void shallow_water(double **m_h1,double **m_u1, double **m_v1,		/* water depth and velocities of the i step*/
		     	float **m_z,						/* DTM */
		     	float **m_DAMBREAK,	 				/* DTM changes (e.g. DTM) */
		     	float **m_m,						/* manning coefficient */		
			int **m_lake,						/* lake filter, default>0, if equal to 0 --> do not apply swe!!!*/	     	
			double **m_h2, double **m_u2, double **m_v2,		/* water depth and velocities of the i+1 step*/
			int row, int col, int nrows, int ncols,			/* matrix size*/
			float timestep,						/* timestep (normally optimized with another function)  */
			float res_ew, float res_ns,				/* grid resolutions*/
			int method, 						/* default = 3, various hypothesis*/
			int num_cell,int num_break,				/* number of cell of lake only in case of method 1 or 2, elsewhere 0*/
			double t);						/* computational instant */
