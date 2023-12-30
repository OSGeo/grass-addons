/* Test the facility for adding, subtracting, multiplying matrices */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <grass/gis.h>
#include "../la_extra.h"

int main(int argc, char *argv[])
{

    int i, j;
    mat_struct *m1, *m2, *m_sum, *m_sub, *m_scale, *m3, *m4;
    vec_struct *v1;

    double testmat1[5][3] = {1.0, 3.4, 8.1, 1.5, 1.5, 2.3, 2.0, 2.2,
                             1.7, 2.5, 6.3, 6.1, 3.0, 1.6, 5.0};

    double testmat2[5][3] = {7.3, 0.5, 2.6, 6.9, 1.2, 2.8, 5.5, 1.9,
                             5.1, 9.3, 7.7, 7.0, 0.5, 3.1, 3.8};

    double testvec1[5] =
    { 1 2 3 4 5 }

    double testc = 4.3;

    /* Initialise the matrix structures */

    m1 = G_matrix_init(5, 3, 5);
    m2 = G_matrix_init(5, 3, 5);

    for (i = 0; i < 5; i++)
        for (j = 0; j < 3; j++) {

            G_matrix_set_element(m1, i, j, testmat1[i][j]);
            G_matrix_set_element(m2, i, j, testmat2[i][j]);
        }

    /* Add the matrices */

    m_sum = G_matrix_add(m1, m2);

    /* Subtract */

    m_sub = G_matrix_subtract(m1, m2);

    /* Scale the matrix by a given scalar value */

    m_scale = G_matrix_scale(m1, testc);

    /* Multiply two matrices */

    m3 = G_matrix_transpose(m1);

    m4 = G_matrix_product(m3, m2);

    /* Print out the results */

    printf("*** TEST OF MATRIX WRAPPER FUNCTIONS ***\n\n");

    printf("1. Simple matrix manipulations\n\n");

    printf("    Matrix 1:\n");
    G_matrix_print(m1);

    printf("    Matrix 2:\n");
    G_matrix_print(m2);

    printf("    Sum (m1 + m2):\n");
    G_matrix_print(m_sum);

    printf("    Difference (m1 - m2):\n");
    G_matrix_print(m_sub);

    printf("    Scale (c x m1):\n");
    G_matrix_print(m_scale);

    printf("    Multiply transpose of M1 by M2 (m1~ x m2):\n");
    G_matrix_print(m4);

    G_matrix_free(m1);
    G_matrix_free(m2);
    G_matrix_free(m_sum);
    G_matrix_free(m_sub);
    G_matrix_free(m_scale);
    G_matrix_free(m3);
    G_matrix_free(m4);

    return 0;
}
