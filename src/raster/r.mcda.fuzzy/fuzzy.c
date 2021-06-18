#include "local_proto.h"

/*
 * global function declaration
 */

void build_weight_vect(int nrows, int ncols, int ncriteria,
                       struct Option *weight, double *weight_vect);

void build_fuzzy_matrix(int nrows, int ncols, int ncriteria,
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


void build_fuzzy_matrix(int nrows, int ncols, int ncriteria,
                        double *weight_vect, double ***decision_vol)
{
    int row1, col1, row2, col2;
    int i, j, k, cont;
    double row_sum_conc, col_sum_conc, row_sum_disc, col_sum_disc;
    double value;

    /* apply linguistic modifier - */
    for (row1 = 0; row1 < nrows; row1++)
    {
        G_percent(row1, nrows, 2);
        for (col1 = 0; col1 < ncols; col1++)
        {
            for (i = 0; i < ncriteria; i++)
            {
                decision_vol[row1][col1][i] =
                    pow(decision_vol[row1][col1][i], weight_vect[i]);
            }
        }
    }

    /* operate intersection - AND logic (find min value -) */
    for (row1 = 0; row1 < nrows; row1++)
    {
        G_percent(row1, nrows, 2);
        for (col1 = 0; col1 < ncols; col1++)
        {
            value = decision_vol[row1][col1][0];	/* set value to firsth matrix i-value */
            for (i = 0; i < ncriteria; i++)
            {
                if (decision_vol[row1][col1][i] >= value)
                {
                    value = value;
                }
                else
                {
                    value = decision_vol[row1][col1][i];
                }
            }
            decision_vol[row1][col1][ncriteria] = value;
        }
    }

    /* operate union - OR logic (find max value -) */
    for (row1 = 0; row1 < nrows; row1++)
    {
        G_percent(row1, nrows, 2);
        for (col1 = 0; col1 < ncols; col1++)
        {
            value = decision_vol[row1][col1][0];	/* set value to firsth matrix i-value */
            for (i = 0; i < ncriteria; i++)
            {
                if (decision_vol[row1][col1][i] <= value)
                {
                    value = value;
                }
                else
                {
                    value = decision_vol[row1][col1][i];
                }
            }
            decision_vol[row1][col1][ncriteria + 1] = value;
        }
    }

    /* operate OWA (find average value -) */
    for (row1 = 0; row1 < nrows; row1++)
    {
        G_percent(row1, nrows, 2);
        for (col1 = 0; col1 < ncols; col1++)
        {
            /*value = decision_vol[row1][col1][0];*/	
	    value=0;  					/* set value to firsth matrix i-value */
            for (i = 0; i < ncriteria; i++)
            {
                value = value + decision_vol[row1][col1][i];
            }
            decision_vol[row1][col1][ncriteria + 2] = value / ncriteria;
        }
    }

}
