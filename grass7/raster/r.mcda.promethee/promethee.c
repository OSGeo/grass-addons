#include "local_proto.h"

/*
 * global function declaration
 */

void build_weight_vect(int ncriteria, struct Option *weight,
						double *weight_vect);

void build_flow_matrix(int nrows, int ncols, int ncriteria,
                            double *weight_vect, double ***decision_vol,
                            double ***positive_flow_vol, double ***negative_flow_vol);


/*
 * function definitions
 */

void build_weight_vect(int ncriteria,struct Option *weight, 
						double *weight_vect)
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


void build_flow_matrix(int nrows, int ncols, int ncriteria,
                            double *weight_vect, double ***decision_vol,
                            double ***positive_flow_vol, double ***negative_flow_vol)
{
    int row1, col1, row2, col2;
    int i;
	double threshold;

/* make pairwise comparation and build positive flow matrix */
	for (i = 0; i < ncriteria; i++)
	{
		G_percent(i, (nrows*ncriteria), 2);
		for (row1 = 0; row1 < nrows; row1++)
		{
			for (col1 = 0; col1 < ncols; col1++)
			{
				for (row2 = 0; row2 < nrows; row2++)
				{
					for (col2 = 0; col2 < ncols; col2++)
					{
						threshold = (decision_vol[row1][col1][i] - decision_vol[row2][col2][i]);
						if (threshold>0)
							{
							positive_flow_vol[row1][col1][i]=threshold*weight_vect[i];
							negative_flow_vol[row1][col1][i]=0;
							}
						else
							{
							positive_flow_vol[row1][col1][i]=0;
							negative_flow_vol[row1][col1][i]=threshold*weight_vect[i];
							}
					}
				}
			}
		}
	}

    /*storage preference value in decision_vol */
    for (row1 = 0; row1 < nrows; row1++)
    {
        G_percent(row1, nrows, 2);
        for (col1 = 0; col1 < ncols; col1++)
        {
			for ( i=0; i<ncriteria;i++)
			{
            /*fill matrix with performance  for each DCELL */
            positive_flow_vol[row1][col1][ncriteria] = positive_flow_vol[row1][col1][ncriteria]+positive_flow_vol[row1][col1][i];
            negative_flow_vol[row1][col1][ncriteria] = negative_flow_vol[row1][col1][ncriteria]+negative_flow_vol[row1][col1][i];
			}
        }
    }
}
