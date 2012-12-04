#include "local_proto.h"

/*
 * global function declaration
 */

void build_weight_vect(int nrows, int ncols, int ncriteria,
                       struct Option *weight, double *weight_vect);

void build_regime_matrix(int nrows, int ncols, int ncriteria,
                         double *weight_vect, double ***decision_vol);


/*
 * function definitions
 */

void build_weight_vect(int nrows, int ncols, int ncriteria,
                       struct Option *weight, double *weight_vect)
{

    int i, nweight = 0;
    double weight_sum = 0;

    while (weight->answers[nweight] != NULL)
    {
        nweight++;
    }

    if (nweight != ncriteria)
        G_fatal_error(_("criteria number  and weight number are different"));


    for (i = 0; i < nweight; i++)
    {
        weight_vect[i] = (atof(weight->answers[i]));	/*transfer  weight value  in double  array */
        weight_sum = weight_sum + weight_vect[i];	/*calculate sum weight */
    }

    for (i = 0; i < nweight; i++)
    {
        weight_vect[i] = weight_vect[i] / weight_sum;	/*normalize vector weight */

    }

}


void build_regime_matrix(int nrows, int ncols, int ncriteria,
                         double *weight_vect, double ***decision_vol)
{
    int row1, col1, row2, col2;
    int i, j, k, cont;
    double *row_sum_regime;
    
    row_sum_regime=G_malloc(ncriteria * nrows * ncols * sizeof(double*));

    j = 0;			/* make pairwise comparation and built regime matrix */
    for (row1 = 0; row1 < nrows; row1++)
    {
        for (col1 = 0; col1 < ncols; col1++)
        {
            for (row2 = 0; row2 < nrows; row2++)
            {
                for (col2 = 0; col2 < ncols; col2++)
                {
                    double reg = 0;

                    for (i = 0; i < ncriteria; i++)
                    {
                        double d = decision_vol[row1][col1][i]-decision_vol[row2][col2][i];
                        if (d > 0)
                            reg += (1 * weight_vect[i]);
                        else if (d < 0)
                            reg += (-1 * weight_vect[i]);
                        else
                            reg += 0;
                    }
                    row_sum_regime[j] += reg;
                }
            }
	    G_percent(j, nrows*ncols, 2);
            j++;		/* increase rows index up to nrows*ncols */
        }
    }

    /*calculate concordance and discordance index and storage in decision_vol */
    cont = 0;
    for (row1 = 0; row1 < nrows; row1++)
    {
        for (col1 = 0; col1 < ncols; col1++)
        {
            decision_vol[row1][col1][ncriteria] = row_sum_regime[cont] / (nrows * ncols - 1);	/*fill matrix with regime index for each DCELL */
            cont++;
        }
        G_percent(row1, nrows, 2);
    }
}
