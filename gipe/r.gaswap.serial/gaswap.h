
void gaswap(double texture[], double sat[], double satDOY[], int NVAR,
	    int NSAT, int year, int pop, int maxgen, double pmute,
	    double pxover, double target_fitness, int syear, int eyear,
	    char *METRO, double Lati, double Alt, double *grass_c);

struct genotype			/* genotype (GT), a member of the population */
{
    int *gene;
    double fitness;		/* GT's fitness */
    double *upper;		/* GT's variables upper bound */
    double *lower;		/* GT's variables lower bound */
    double rfitness;		/* relative fitness */
    double cfitness;		/* cumulative fitness */
};
