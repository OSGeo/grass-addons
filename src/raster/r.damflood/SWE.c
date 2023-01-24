#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <float.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/gmath.h>
#include <grass/dbmi.h>
#include <grass/linkm.h>
#include <grass/bitmap.h>

#include "SWE.h" /* specifical dependency to the header file */

#define min(A, B)        ((A) < (B) ? (A) : (B))
#define max(A, B)        ((A) > (B) ? (A) : (B))
#define min4(A, B, C, D) min(min(A, B), min(C, D))
#define max4(A, B, C, D) max(max(A, B), max(C, D))

#define ALLOC_DIM        10000
#define PI               3.14159265
#define g                9.81

float velocita_breccia(int i, double h)
{
    // double h;
    // int i;
    // float g=9.81;
    float v;

    if (i == 1) {
        v = 0.93 * sqrt(h);
    }
    else if (i == 2) {
        v = 0.4 * sqrt(2 * g * h);
    }
    return v;
}

void shallow_water(double **m_h1, double **m_u1, double **m_v1, float **m_z,
                   float **m_DAMBREAK, float **m_m, int **m_lake, double **m_h2,
                   double **m_u2, double **m_v2, int row, int col, int nrows,
                   int ncols, float timestep, float res_ew, float res_ns,
                   int method, int num_cell, int num_break, double t)
{

    /*FUNCTION VARIABLES*/
    double h_dx, h_sx, h_up, h_dw, Fup, Fdw, Fdx, Fsx, Gup, Gdw, Gdx, Gsx;
    double u_sx, u_dx, v_dx, v_sx, v_up, v_dw, u_up, u_dw;

    /***************************************************/
    /* DA METTERE IN UNA ULTERIORE FUNZIONE fall.c     */
    /* chiamato sia qua che nel main                   */
    /* controlla Q=0.0 & volume=0.0                    */
    float Q, vol_res, fall, volume;
    /***************************************************/
    int test;
    double F, G, S;
    double dZ_dx_down, dZ_dx_up, dZ_dx, dZ_dy_down, dZ_dy_up, dZ_dy;
    double cr_down, cr_up, Z_piu, Z_meno;
    double u, v, V;
    double hmin = 0.1;
    float R_i;

    // DESCRIPTION OF METHOD (italian --> TRASLATE)
    // primo ciclo: calcolo nuove altezze dell'acqua al tempo t+1:
    //                 - a valle della diga applico l'equazione di continuita'
    //                 delle shallow
    // water                   in pratica la nuova altezza e' valutata
    // attraverso un bilancio dei
    //                   flussi in ingresso e in uscita nelle due direzioni
    //                   principali
    //                 - a monte delle diga:
    //                      - nel metodo 1 e 2 :l'equazione di continuita' e'
    //              applicata al volume del lago
    //                          fisicamente questo porta a una minore
    //                          realisticita' ma evita le
    // oscillazioni che
    //                           sono causa di instabilita' numerica
    //                        - nel caso piu' generale si applicano le equazioni
    //                        a tutto il
    // lago

    for (row = 1; row < nrows - 1; row++) {
        for (col = 1; col < ncols - 1; col++) {
            if (m_lake[row][col] == 0 && m_DAMBREAK[row][col] <= 0) {

                //*******************************************/
                /* CONTINUITY EQUATION --> h(t+1)           */
                //*******************************************/
                // x direction
                // right intercell
                if (m_u1[row][col] > 0 && m_u1[row][col + 1] > 0) {
                    Fdx = m_u1[row][col] * m_h1[row][col];
                }
                else if (m_u1[row][col] < 0 && m_u1[row][col + 1] < 0) {
                    Fdx = m_u1[row][col + 1] * m_h1[row][col + 1];
                }
                else {
                    u_dx = (m_u1[row][col] + m_u1[row][col + 1]) / 2.0;
                    if ((u_dx < 0 && m_u1[row][col + 1] == 0) ||
                        (u_dx > 0 && m_u1[row][col] == 0))
                        u_dx = 0;
                    if (u_dx >= 0) {
                        h_dx = max(m_h1[row][col] + m_z[row][col] -
                                       m_z[row][col + 1],
                                   0);
                    }
                    else {
                        h_dx = max(m_h1[row][col + 1] + m_z[row][col + 1] -
                                       m_z[row][col],
                                   0);
                    }
                    Fdx = h_dx * u_dx;
                }

                // left intercell
                if (m_u1[row][col - 1] > 0 && m_u1[row][col] > 0) {
                    Fsx = m_u1[row][col - 1] * m_h1[row][col - 1];
                }
                else if (m_u1[row][col - 1] < 0 && m_u1[row][col] < 0) {
                    Fsx = m_u1[row][col] * m_h1[row][col];
                }
                else {
                    u_sx = (m_u1[row][col - 1] + m_u1[row][col]) / 2.0;
                    if ((u_sx < 0 && m_u1[row][col] == 0) ||
                        (u_sx > 0 && m_u1[row][col - 1] == 0))
                        u_sx = 0;
                    if (u_sx >= 0) {
                        h_sx = max(m_h1[row][col - 1] + m_z[row][col - 1] -
                                       m_z[row][col],
                                   0);
                    }
                    else {
                        h_sx = max(m_h1[row][col] + m_z[row][col] -
                                       m_z[row][col - 1],
                                   0);
                    }
                    Fsx = h_sx * u_sx;
                }

                if (m_DAMBREAK[row][col + 1] > 0 &&
                    ((m_h1[row][col] + m_z[row][col]) <
                     (m_h1[row][col + 1] + m_z[row][col + 1]))) {
                    Fdx = -m_h1[row][col + 1] *
                          velocita_breccia(method, m_h2[row][col + 1]);
                    if (m_h1[row][col + 1] == 0)
                        Fdx = 0.0;
                }
                if (m_DAMBREAK[row][col - 1] > 0 &&
                    ((m_h1[row][col] + m_z[row][col]) <
                     (m_h1[row][col - 1] + m_z[row][col - 1]))) {
                    Fsx = m_h1[row][col - 1] *
                          velocita_breccia(method, m_h2[row][col - 1]);
                    if (m_h1[row][col - 1] == 0)
                        Fsx = 0.0;
                }
                F = Fdx - Fsx;

                // dGup =m_v1[row][col] * m_h1[row][col] ;irezione y
                // intercella up
                if (m_v1[row][col] > 0 && m_v1[row - 1][col] > 0) {
                    Gup = m_v1[row][col] * m_h1[row][col];
                }
                else if (m_v1[row][col] < 0 && m_v1[row - 1][col] < 0) {
                    Gup = m_v1[row - 1][col] * m_h1[row - 1][col];
                }
                else {
                    v_up = (m_v1[row][col] + m_v1[row - 1][col]) / 2.0;
                    if ((v_up < 0 && m_v1[row - 1][col] == 0) ||
                        (v_up > 0 && m_v1[row][col] == 0))
                        v_up = 0;
                    if (v_up >= 0) {
                        h_up = max(m_h1[row][col] + m_z[row][col] -
                                       m_z[row - 1][col],
                                   0);
                    }
                    else {
                        h_up = max(m_h1[row - 1][col] + m_z[row - 1][col] -
                                       m_z[row][col],
                                   0);
                    }
                    Gup = h_up * v_up;
                }

                // intercella down
                if (m_v1[row + 1][col] > 0 && m_v1[row][col] > 0) {
                    Gdw = m_v1[row + 1][col] * m_h1[row + 1][col];
                }
                else if (m_v1[row + 1][col] < 0 && m_v1[row][col] < 0) {
                    Gdw = m_v1[row][col] * m_h1[row][col];
                }
                else {
                    v_dw = (m_v1[row][col] + m_v1[row + 1][col]) / 2.0;
                    if ((v_dw < 0 && m_v1[row][col] == 0) ||
                        (v_dw > 0 && m_v1[row + 1][col] == 0))
                        v_dw = 0;
                    if (v_dw >= 0) {
                        h_dw = max(m_h1[row + 1][col] + m_z[row + 1][col] -
                                       m_z[row][col],
                                   0);
                    }
                    else {
                        h_dw = max(m_h1[row][col] + m_z[row][col] -
                                       m_z[row + 1][col],
                                   0);
                    }

                    Gdw = h_dw * v_dw;
                }

                if (m_DAMBREAK[row - 1][col] > 0 &&
                    ((m_h1[row][col] + m_z[row][col]) <
                     (m_h1[row - 1][col] + m_z[row - 1][col]))) {
                    Gup = -m_h1[row - 1][col] *
                          velocita_breccia(method, m_h1[row - 1][col]);
                    if (m_h1[row - 1][col] == 0)
                        Gup = 0.0;
                }
                if (m_DAMBREAK[row + 1][col] > 0 &&
                    ((m_h1[row][col] + m_z[row][col]) <
                     (m_h1[row + 1][col] + m_z[row + 1][col]))) {
                    Gup = m_h1[row - 1][col] *
                          velocita_breccia(method, m_h1[row + 1][col]);
                    if (m_h1[row + 1][col] == 0)
                        Gdw = 0.0;
                }
                G = Gup - Gdw;

                // equazione
                m_h2[row][col] = m_h1[row][col] - timestep / res_ew * F -
                                 timestep / res_ns * G;

                /*if ((row==20||row==21||row==22||row==23)&&(col==18||col==19)){
                        printf("EQ. CONTINUITA' --> row:%d, col:%d\n)",row,
                col);
                        printf("m_h1[row][col]:%f,m_u1[row][col]:%f,m_v1[row][col]:%f",m_h1[row][col],m_u1[row][col],m_v1[row][col]);
                        printf("m_h1[row][col+1]:%f,m_h1[row][col-1]:%f,m_h1[row+1][col]:%f,
                m_h1[row-1][col]:%f\n",m_h1[row][col+1],m_h1[row][col-1],m_h1[row+1][col],
                m_h1[row-1][col]); printf("h_dx:%f, h_sx:%f, h_up%f,
                h_dw:%f\n",h_dx, h_sx, h_up, h_dw);
                        printf("m_u1[row][col+1]:%f,m_u1[row][col-1]:%f,m_v1[row+1][col]:%f,
                m_v1[row-1][col]:%f\n",m_u1[row][col+1],m_u1[row][col-1],m_v1[row+1][col],
                m_v1[row-1][col]); printf("v_up: %f,v_dw:%f,u_dx:%f,u_sx:%f
                \n",v_up, v_dw, u_dx, u_sx); printf("Fdx: %f,Fsx: %f, F: %f,
                Gup:%f, Gdw:%f, G: %f\n",Fdx, Fsx, F,Gup, Gdw, G);
                        printf("m_h2(row,col): %f\n \n", m_h2[row][col]);
                }*/

                /*if( (row==1 || row==(nrows-2) || col==1 || col==(ncols-2)) &&
  (m_v2[1][col]>0 || m_v2[nrows-2][col]<0 || m_u1[row][1]<0 ||
  m_u1[row][ncols-2]>0 )){ if (warn==0){ G_warning("At the time %.3f the
  computational region is smaller than inundation",t); warn=1;
                G_message("warn=%d",warn);
        }
  }*/

                if (m_h2[row][col] < 0) {
                    /*G_warning("At the time %f h is lesser than 0
               h(%d,%d)=%f",t, row,col,m_h2[row][col]); printf("row:%d, col:%d,
               H minore di zero: %.30lf)",row, col, m_h2[row][col]);
               printf("DATI:\n");
                    printf("row:%d,col%d,hmin:%g,h2:%.30lf \n
               ",row,col,hmin,m_h2[row][col]); printf("m_z[row][col]:%f\n",
               m_z[row][col]); printf("m_h1[row][col]:%.30lf\n",m_h1[row][col]);
                    printf("m_u1[row][col]:%.30lf,m_v1[row][col]:%.30lf\n",m_u1[row][col],
               m_v1[row][col]);
                    printf("m_z[row][col+1]:%f,m_z[row][col-1]:%f,m_z[row+1][col]:%f,
               m_z[row-1][col]:%f\n",m_z[row][col+1],m_z[row][col-1],m_z[row+1][col],
               m_z[row-1][col]);
                    printf("m_h1[row][col+1]:%.30lf,m_h1[row][col-1]:%.30lf,m_h1[row+1][col]:%.30lf,
               m_h1[row-1][col]:%.30lf\n",m_h1[row][col+1],m_h1[row][col-1],m_h1[row+1][col],
               m_h1[row-1][col]); printf("h_dx:%f, h_sx:%f, h_up%f,
               h_dw:%f\n",h_dx, h_sx, h_up, h_dw);
                    printf("m_u1[row][col+1]:%.30lf,m_u1[row][col-1]:%.30lf,m_v1[row+1][col]:%.30lf,
               m_v1[row-1][col]:%.30lf\n",m_u1[row][col+1],m_u1[row][col-1],m_v1[row+1][col],
               m_v1[row-1][col]); printf("timestep: %.30lf, res_ew: %.30lf,
               res_ns:%.30lf\n",timestep, res_ew, res_ns); printf("v_up:
               %f,v_dw:%f,u_dx:%f,u_sx:%f \n",v_up, v_dw, u_dx, u_sx);
                    printf("Fdx: %.30lf,Fsx: %.30lf, F: %.30lf, Gup:%.30lf,
               Gdw:%.30lf, G: %.30lf\n",Fdx, Fsx, F,Gup, Gdw, G); printf("row:
               %d, col %d, m_h1(row,col): %.30lf, m_h2(row,col): %.30lf \n",row,
               col,m_h1[row][col], m_h2[row][col]);
                    printf("m_DAMBREAk(ROW,COL):%f \n",m_DAMBREAK[row][col]);
                    while(!getchar()){ }*/
                    m_h2[row][col] = 0;
                }

            } // fine continuita' a valle (IF check)

            if (method == 1 || method == 2) {
                //*******************************************************************
                // calcolo portata Q uscente dal lago solo nel caso di Hp
                // stramazzo
                /* HP: method 1 or 2   */
                if (m_DAMBREAK[row][col] > 0) {
                    if ((m_z[row][col] + m_h1[row][col]) >
                        (m_z[row][col + 1] + m_h1[row][col + 1])) {
                        if (t == timestep)
                            Q = Q +
                                m_h1[row][col] *
                                    velocita_breccia(method, m_h1[row][col]) *
                                    res_ns;
                        m_u1[row][col] =
                            velocita_breccia(method, m_h1[row][col]);
                    }
                    else if ((m_z[row][col] + m_h1[row][col]) >
                             (m_z[row][col - 1] + m_h1[row][col - 1])) {
                        Q = Q + m_h1[row][col] *
                                    velocita_breccia(method, m_h1[row][col]) *
                                    res_ns;
                        m_u1[row][col] =
                            -velocita_breccia(method, m_h1[row][col]);
                    }
                    if ((m_z[row][col] + m_h1[row][col]) >
                        (m_z[row + 1][col] + m_h1[row + 1][col])) {
                        Q = Q + m_h1[row][col] *
                                    velocita_breccia(method, m_h1[row][col]) *
                                    res_ew;
                        m_v1[row][col] =
                            velocita_breccia(method, m_h1[row][col]);
                    }
                    else if ((m_z[row][col] + m_h1[row][col]) >
                             (m_z[row - 1][col] + m_h1[row - 1][col])) {
                        Q = Q + m_h1[row][col] *
                                    velocita_breccia(method, m_h1[row][col]) *
                                    res_ew;
                        m_v1[row][col] =
                            -velocita_breccia(method, m_h1[row][col]);
                    }
                }
            }
        }
    } // end two for cicles (continuity equation)

    //*****************************************************************************
    // abbassamento lago (siccome c'e due volte fare poi una function)
    //*****************************************************************************
    if (method == 1 || method == 2) {

        /* calcolo l'abbassamento sul lago*/
        if (num_cell != 0) {
            fall = (Q * timestep - vol_res) / (num_cell * res_ew * res_ns);
        }
        else {
            // if (warn1==0){
            G_warning("At the time %.0fs no water go out from lake", t);
            //        warn1=1;
            //}
        }
        vol_res = 0.0;
        Q = 0.0;

        for (row = 1; row < nrows - 1; row++) {
            for (col = 1; col < ncols - 1; col++) {
                if (m_DAMBREAK[row][col] > 0) {
                    m_h2[row][col] = m_h1[row][col] - fall;
                    if (m_h2[row][col] <= 0) {
                        m_h2[row][col] = 0.0;
                        if (m_h1[row][col] > 0) {
                            num_break--;
                            /*if (num_break==0){
                                    G_warning("At the time %.0fs no water go out
                            from lake",t);
                            }*/
                        }
                    }
                }
                if (m_lake[row][col] == 1) {
                    m_h2[row][col] = m_h1[row][col] - fall;
                    if (m_h2[row][col] <= 0) {
                        vol_res = vol_res - m_h2[row][col] * res_ew * res_ns;
                        m_lake[row][col] = -1;
                        m_h2[row][col] = 0.0;
                        num_cell--;
                    }
                }

            } // end for col
        }     // end for row
    }         // end if method

    // DESCRIPTION OF METHOD (italian --> TRASLATE)
    //**********************************************************************************
    // terzo ciclo completo sulla matrice: applico le  -->
    // EQUAZIONI DEL MOTO IN DIREZIONE X e Y
    // e quindi calcolo u(t+1) e v(t+1)
    //
    // NOTA:
    // u(i,j) e v (i,j) sono le velocita' medie della cella i,j
    /*******************************************************************/
    for (row = 1; row < nrows - 1; row++) {
        for (col = 1; col < ncols - 1; col++) {
            if (m_lake[row][col] == 0 && m_h2[row][col] >= hmin) {

                /**********************************************************************************************************************/
                /* EQUAZIONE DEL MOTO IN DIREZIONE X */
                // right intercell
                if (m_u1[row][col] > 0 && m_u1[row][col + 1] > 0) {
                    Fdx = m_u1[row][col] * m_u1[row][col] * m_h1[row][col];
                }
                else if (m_u1[row][col] < 0 && m_u1[row][col + 1] < 0) {
                    Fdx = m_u1[row][col + 1] * m_u1[row][col + 1] *
                          m_h1[row][col + 1];
                }
                else {
                    u_dx = (m_u1[row][col] + m_u1[row][col + 1]) / 2.0;
                    if ((u_dx < 0 && m_u1[row][col + 1] == 0) ||
                        (u_dx > 0 && m_u1[row][col] == 0))
                        u_dx = 0;
                    if (u_dx >= 0) {
                        h_dx = max(m_h1[row][col] + m_z[row][col] -
                                       m_z[row][col + 1],
                                   0);
                    }
                    else {
                        h_dx = max(m_h1[row][col + 1] + m_z[row][col + 1] -
                                       m_z[row][col],
                                   0);
                    }
                    Fdx = h_dx * u_dx * u_dx;
                }

                // left intercell
                if (m_u1[row][col - 1] > 0 && m_u1[row][col] > 0) {
                    Fsx = m_u1[row][col - 1] * m_u1[row][col - 1] *
                          m_h1[row][col - 1];
                }
                else if (m_u1[row][col - 1] < 0 && m_u1[row][col] < 0) {
                    Fsx = m_u1[row][col] * m_u1[row][col] * m_h1[row][col];
                }
                else {
                    u_sx = (m_u1[row][col - 1] + m_u1[row][col]) / 2.0;
                    if ((u_sx < 0 && m_u1[row][col] == 0) ||
                        (u_sx > 0 && m_u1[row][col - 1] == 0))
                        u_sx = 0;
                    if (u_sx >= 0) {
                        h_sx = max(m_h1[row][col - 1] + m_z[row][col - 1] -
                                       m_z[row][col],
                                   0);
                    }
                    else {
                        h_sx = max(m_h1[row][col] + m_z[row][col] -
                                       m_z[row][col - 1],
                                   0);
                    }
                    Fsx = h_sx * u_sx * u_sx;
                }

                if (m_DAMBREAK[row][col + 1] > 0 &&
                    ((m_h2[row][col] + m_z[row][col]) <
                     (m_h2[row][col + 1] + m_z[row][col + 1]))) {
                    Fdx = m_h1[row][col + 1] *
                          pow(-velocita_breccia(method, m_h1[row][col + 1]),
                              2.0); // -vel al quadrato perde il segno meno
                    if (m_h2[row][col + 1] == 0)
                        Fdx = 0.0;
                }
                if (m_DAMBREAK[row][col - 1] > 0 &&
                    ((m_h2[row][col] + m_z[row][col]) <
                     (m_h2[row][col - 1] + m_z[row][col - 1]))) {
                    Fsx =
                        m_h1[row][col - 1] *
                        pow(velocita_breccia(method, m_h1[row][col - 1]), 2.0);
                    if (m_h2[row][col - 1] == 0)
                        Fsx = 0.0;
                }
                F = Fdx - Fsx;

                // y
                //  intercella up
                if (m_v1[row][col] > 0 && m_v1[row - 1][col] > 0) {
                    Gup = m_v1[row][col] * m_u1[row][col] * m_h1[row][col];
                }
                else if (m_v1[row][col] < 0 && m_v1[row - 1][col] < 0) {
                    Gup = m_v1[row - 1][col] * m_u1[row - 1][col] *
                          m_h1[row - 1][col];
                }
                else {
                    v_up = (m_v1[row][col] + m_v1[row - 1][col]) / 2.0;
                    if ((v_up < 0 && m_v1[row - 1][col] == 0) ||
                        (v_up > 0 && m_v1[row][col] == 0))
                        v_up = 0;
                    u_up = (m_u1[row][col] + m_u1[row - 1][col]) / 2.0;
                    if (v_up >= 0) {
                        h_up = max(m_h1[row][col] + m_z[row][col] -
                                       m_z[row - 1][col],
                                   0);
                    }
                    else {
                        h_up = max(m_h1[row - 1][col] + m_z[row - 1][col] -
                                       m_z[row][col],
                                   0);
                    }
                    Gup = h_up * v_up * u_up;
                }

                // intercella down
                if (m_v1[row + 1][col] > 0 && m_v1[row][col] > 0) {
                    Gdw = m_v1[row + 1][col] * m_u1[row + 1][col] *
                          m_h1[row + 1][col];
                }
                else if (m_v1[row + 1][col] < 0 && m_v1[row][col] < 0) {
                    Gdw = m_v1[row][col] * m_u1[row][col] * m_h1[row][col];
                }
                else {
                    v_dw = (m_v1[row][col] + m_v1[row + 1][col]) / 2.0;
                    if ((v_dw < 0 && m_v1[row][col] == 0) ||
                        (v_dw > 0 && m_v1[row + 1][col] == 0))
                        v_dw = 0;
                    u_dw = (m_u1[row][col] + m_u1[row + 1][col]) / 2.0;
                    if (v_dw >= 0) {
                        h_dw = max(m_h1[row + 1][col] + m_z[row + 1][col] -
                                       m_z[row][col],
                                   0);
                    }
                    else {
                        h_dw = max(m_h1[row][col] + m_z[row][col] -
                                       m_z[row + 1][col],
                                   0);
                    }
                    Gdw = h_dw * u_dw * v_dw;
                }

                if (m_DAMBREAK[row - 1][col] > 0 &&
                    ((m_h2[row][col] + m_z[row][col]) <
                     (m_h2[row - 1][col] + m_z[row - 1][col]))) {
                    Gup = m_h1[row - 1][col] *
                          (-velocita_breccia(method, m_h1[row - 1][col]) *
                           m_u1[row - 1][col]);
                    if (m_h2[row - 1][col] == 0)
                        Gup = 0.0;
                }
                if (m_DAMBREAK[row + 1][col] > 0 &&
                    ((m_h2[row][col] + m_z[row][col]) <
                     (m_h2[row + 1][col] + m_z[row + 1][col]))) {
                    Gdw = m_h1[row + 1][col] *
                          (velocita_breccia(method, m_h1[row + 1][col]) *
                           m_u1[row + 1][col]);
                    if (m_h2[row + 1][col] == 0)
                        Gdw = 0.0;
                }
                G = Gup - Gdw;

                // courant number  --> UPWIND METHOD
                if (m_u1[row][col] > 0 && m_u1[row][col + 1] > 0 &&
                    m_u1[row][col - 1] > 0) {
                    test = 1;
                    dZ_dx_down = ((m_h2[row][col + 1] + m_z[row][col + 1]) -
                                  (m_h2[row][col] + m_z[row][col])) /
                                 res_ew;
                    if (m_h2[row][col - 1] == 0 &&
                        m_z[row][col - 1] > (m_h2[row][col] + m_z[row][col])) {
                        dZ_dx_up = 0;
                    }
                    else {
                        dZ_dx_up = ((m_h2[row][col] + m_z[row][col]) -
                                    (m_h2[row][col - 1] + m_z[row][col - 1])) /
                                   res_ew;
                    }
                    cr_down =
                        (timestep / res_ew) *
                        (fabs(m_u1[row][col + 1]) + fabs(m_u1[row][col])) / 2.0;
                    cr_up = (timestep / res_ew) *
                            (fabs(m_u1[row][col]) + fabs(m_u1[row][col - 1])) /
                            2.0;
                    Z_piu = 0.0;
                    Z_meno = 0.0;
                }
                else if (m_u1[row][col] < 0 && m_u1[row][col - 1] < 0 &&
                         m_u1[row][col + 1] < 0) {
                    test = 2;
                    dZ_dx_down = ((m_h2[row][col] + m_z[row][col]) -
                                  (m_h2[row][col - 1] + m_z[row][col - 1])) /
                                 res_ew;
                    if (m_h2[row][col + 1] == 0 &&
                        m_z[row][col + 1] > (m_h2[row][col] + m_z[row][col])) {
                        dZ_dx_up = 0;
                    }
                    else {
                        dZ_dx_up = ((m_h2[row][col + 1] + m_z[row][col + 1]) -
                                    (m_h2[row][col] + m_z[row][col])) /
                                   res_ew;
                    }
                    cr_down =
                        (timestep / res_ew) *
                        (fabs(m_u1[row][col]) + fabs(m_u1[row][col - 1])) / 2.0;
                    cr_up = (timestep / res_ew) *
                            (fabs(m_u1[row][col + 1]) + fabs(m_u1[row][col])) /
                            2.0;
                    Z_piu = 0.0;
                    Z_meno = 0.0;
                }
                else {
                    test = 3;
                    if (m_h2[row][col + 1] == 0 &&
                        m_z[row][col + 1] > (m_h2[row][col] + m_z[row][col])) {
                        Z_piu = (m_h2[row][col] + m_z[row][col]);
                    }
                    else {
                        Z_piu = ((m_h2[row][col + 1] + m_z[row][col + 1]) +
                                 (m_h2[row][col] + m_z[row][col])) /
                                2;
                    }
                    if (m_h2[row][col - 1] == 0 &&
                        m_z[row][col - 1] > (m_h2[row][col] + m_z[row][col])) {
                        Z_meno = (m_h2[row][col] + m_z[row][col]);
                    }
                    else {
                        Z_meno = ((m_h2[row][col - 1] + m_z[row][col - 1]) +
                                  (m_h2[row][col] + m_z[row][col])) /
                                 2;
                    }
                    dZ_dx_down = (Z_piu - Z_meno) / res_ew;
                    dZ_dx_up = (Z_piu - Z_meno) / res_ew;
                    cr_down =
                        (timestep / res_ew) *
                        (fabs(m_u1[row][col + 1]) + 2 * fabs(m_u1[row][col]) +
                         fabs(m_u1[row][col - 1])) /
                        4.0;
                    cr_up =
                        (timestep / res_ew) *
                        (fabs(m_u1[row][col + 1]) + 2 * fabs(m_u1[row][col]) +
                         fabs(m_u1[row][col - 1])) /
                        4.0;
                }

                if (m_DAMBREAK[row][col + 1] > 0 && m_h2[row][col + 1] == 0) {
                    test = 4;
                    dZ_dx_up = 0.0;
                    dZ_dx_down = ((m_h2[row][col] + m_z[row][col]) -
                                  (m_h2[row][col - 1] + m_z[row][col - 1])) /
                                 res_ew;
                }
                if (m_DAMBREAK[row][col - 1] > 0 && m_h2[row][col - 1] == 0) {
                    test = 5;
                    dZ_dx_up = 0.0;
                    dZ_dx_down = ((m_h2[row][col + 1] + m_z[row][col + 1]) -
                                  (m_h2[row][col] + m_z[row][col])) /
                                 res_ew;
                }
                dZ_dx =
                    (1 - sqrt(cr_down)) * dZ_dx_down + sqrt(cr_up) * dZ_dx_up;
                // dZ_dx = 0.5 * dZ_dx_down + 0.5 * dZ_dx_up;

                if (m_h1[row][col] < hmin)
                    R_i = hmin;
                else
                    R_i = m_h1[row][col];

                u = m_u1[row][col];
                v = m_v1[row][col];
                V = sqrt(pow(u, 2.0) + pow(v, 2.0));
                S = (-g * m_h2[row][col] * dZ_dx) -
                    g * (pow(m_m[row][col], 2.0) * u * V /
                         pow(R_i, (1.0 / 3.0)));

                if (m_DAMBREAK[row][col] > 0) {
                    if ((m_z[row][col] + m_h2[row][col]) >
                        (m_z[row][col + 1] + m_h2[row][col + 1]))
                        m_u2[row][col] = velocita_breccia(
                            method,
                            m_h2[row][col]); // velocita' sullo stramazzo
                    else if ((m_z[row][col] + m_h2[row][col]) >
                             (m_z[row][col - 1] + m_h2[row][col - 1]))
                        m_u2[row][col] = -velocita_breccia(
                            method,
                            m_h2[row][col]); // velocita' sullo stramazzo
                    else
                        m_u2[row][col] = 0.0;
                }
                else {
                    m_u2[row][col] = 1.0 / m_h2[row][col] *
                                     (m_h1[row][col] * m_u1[row][col] -
                                      timestep / res_ew * F -
                                      timestep / res_ns * G + timestep * S);
                }
                // no velocita' contro la diga
                /*if (m_z[row][col+1]> water_elevation && m_u2[row][col]>0)
                m_u2[row][col]=0.0;
                if (m_z[row][col-1] > water_elevation && m_u2[row][col]<0)
                m_u2[row][col]=0.0;*/

                if ((timestep / res_ew *
                     (fabs(m_u2[row][col]) + sqrt(g * m_h2[row][col]))) > 1.0) {
                    G_warning("At time %f the Courant-Friedrich-Lewy stability "
                              "condition isn't respected",
                              t);
                    /*G_message("velocita' lungo x\n");
                    G_message("row:%d, col%d \n",row,col);
                    G_message("dZ_dx_down:%f, dZ_dx_up:%f,cr_up:%f,
                    cr_down:%f\n" , dZ_dx_down,dZ_dx_up, cr_up, cr_down);
                    G_message("Z_piu:%f,Z_meno:%f\n", Z_piu, Z_meno);
                    G_message("dZ_dx:%f\n",dZ_dx);
                    G_message("m_h1[row][col]:%f, m_h2[row][col]:%f,
                    m_z[row][col]:%f\n",m_h1[row][col], m_h2[row][col],
                    m_z[row][col]); G_message("m_h2[row][col+1]:%f,
                    m_z[row][col+1]:%f,m_h2[row][col-1]:%f, m_z[row][col-1]:%f
                    \n",m_h2[row][col+1],
                    m_z[row][col+1],m_h2[row][col-1],m_z[row][col-1]);
                    G_message("m_h2[row][col+1]:%f,m_h2[row][col-1]:%f,\n",m_h2[row][col+1],m_h2[row][col-1]);
                    G_message("h_up: %f,h_dw:%f,h_dx:%f,h_sx:%f \n",h_up, h_dw,
                    h_dx, h_sx); G_message("Fdx: %f,Fsx: %f, F: %f, Gup:%f,
                    Gdw:%f, G: %.60lf,  S: %.60lf \n",Fdx, Fsx, F,Gup, Gdw, G,
                    S); G_message("m_u1[row][col-1]:%f, m_h1[row][col-1]:%f,
                    m_u1[row][col+1]:%f,
                    m_h1[row][col+1]:%f\n",m_u1[row][col-1], m_h1[row][col-1],
                    m_u1[row][col+1], m_h1[row][col+1]); G_message("timestep:%f,
                    res_ew:%f\n",timestep,res_ew);
                    G_message("m_u2[row][col]:%f,m_u1[row][col]:%f\n\n",
                    m_u2[row][col],m_u1[row][col]); G_warning("   ");*/
                }

                if (fabs(m_u2[row][col] >= 1000)) {
                    G_warning("At the time %f u(%d,%d)=%f", t, row, col,
                              m_u2[row][col]);
                }
                /******************************************************************************************************************************/

                /******************************************************************************************************************************/
                /* EQUAZIONE DEL MOTO IN DIREZIONE Y */
                // right intercell
                if (m_u1[row][col] > 0 && m_u1[row][col + 1] > 0) {
                    Fdx = m_u1[row][col] * m_v1[row][col] * m_h1[row][col];
                }
                else if (m_u1[row][col] < 0 && m_u1[row][col + 1] < 0) {
                    Fdx = m_u1[row][col + 1] * m_v1[row][col + 1] *
                          m_h1[row][col + 1];
                }
                else {
                    u_dx = (m_u1[row][col] + m_u1[row][col + 1]) / 2.0;
                    if ((u_dx < 0 && m_u1[row][col + 1] == 0) ||
                        (u_dx > 0 && m_u1[row][col] == 0))
                        u_dx = 0;
                    v_dx = (m_v1[row][col] + m_v1[row][col + 1]) / 2.0;
                    if (u_dx >= 0) {
                        h_dx = max(m_h1[row][col] + m_z[row][col] -
                                       m_z[row][col + 1],
                                   0);
                    }
                    else {
                        h_dx = max(m_h1[row][col + 1] + m_z[row][col + 1] -
                                       m_z[row][col],
                                   0);
                    }
                    Fdx = h_dx * u_dx * v_dx;
                }

                // left intercell
                if (m_u1[row][col - 1] > 0 && m_u1[row][col] > 0) {
                    Fsx = m_u1[row][col - 1] * m_v1[row][col - 1] *
                          m_h1[row][col - 1];
                }
                else if (m_u1[row][col - 1] < 0 && m_u1[row][col] < 0) {
                    Fsx = m_u1[row][col] * m_v1[row][col] * m_h1[row][col];
                }
                else {
                    u_sx = (m_u1[row][col - 1] + m_u1[row][col]) / 2.0;
                    if ((u_sx < 0 && m_u1[row][col] == 0) ||
                        (u_sx > 0 && m_u1[row][col - 1] == 0))
                        u_sx = 0;
                    v_sx = (m_v1[row][col - 1] + m_v1[row][col]) / 2.0;
                    if (u_sx >= 0) {
                        h_sx = max(m_h1[row][col - 1] + m_z[row][col - 1] -
                                       m_z[row][col],
                                   0);
                    }
                    else {
                        h_sx = max(m_h1[row][col] + m_z[row][col] -
                                       m_z[row][col - 1],
                                   0);
                    }
                    Fsx = h_sx * u_sx * v_sx;
                }

                if (m_DAMBREAK[row][col + 1] > 0.0 &&
                    ((m_h2[row][col] + m_z[row][col]) <
                     (m_h2[row][col + 1] + m_z[row][col + 1]))) {
                    Fdx = m_h1[row][col + 1] *
                          (-velocita_breccia(method, m_h1[row][col + 1])) *
                          m_v1[row][col + 1];
                    if (m_h2[row][col + 1] == 0)
                        Fdx = 0.0;
                }
                if (m_DAMBREAK[row][col - 1] > 0.0 &&
                    ((m_h2[row][col] + m_z[row][col]) <
                     (m_h2[row][col - 1] + m_z[row][col - 1]))) {
                    Fsx = m_h1[row][col - 1] *
                          velocita_breccia(method, m_h1[row][col - 1]) *
                          m_v1[row][col - 1];
                    if (m_h2[row][col - 1] == 0)
                        Fsx = 0.0;
                }
                F = Fdx - Fsx;

                // y
                //  intercella up
                if (m_v1[row][col] > 0 && m_v1[row - 1][col] > 0) {
                    Gup = m_v1[row][col] * m_v1[row][col] * m_h1[row][col];
                }
                else if (m_v1[row][col] < 0 && m_v1[row - 1][col] < 0) {
                    Gup = m_v1[row - 1][col] * m_v1[row - 1][col] *
                          m_h1[row - 1][col];
                }
                else {
                    v_up = (m_v1[row][col] + m_v1[row - 1][col]) / 2.0;
                    if ((v_up < 0 && m_v1[row - 1][col] == 0) ||
                        (v_up > 0 && m_v1[row][col] == 0))
                        v_up = 0;
                    if (v_up >= 0) {
                        h_up = max(m_h1[row][col] + m_z[row][col] -
                                       m_z[row - 1][col],
                                   0);
                    }
                    else {
                        h_up = max(m_h1[row - 1][col] + m_z[row - 1][col] -
                                       m_z[row][col],
                                   0);
                    }
                    Gup = h_up * v_up * v_up;
                }

                // intercella down
                if (m_v1[row + 1][col] > 0 && m_v1[row][col] > 0) {
                    Gdw = m_v1[row + 1][col] * m_v1[row + 1][col] *
                          m_h1[row + 1][col];
                }
                else if (m_v1[row + 1][col] < 0 && m_v1[row][col] < 0) {
                    Gdw = m_v1[row][col] * m_v1[row][col] * m_h1[row][col];
                }
                else {
                    v_dw = (m_v1[row][col] + m_v1[row + 1][col]) / 2.0;
                    if ((v_dw < 0 && m_v1[row][col] == 0) ||
                        (v_dw > 0 && m_v1[row + 1][col] == 0))
                        v_dw = 0;
                    if (v_dw >= 0) {
                        h_dw = max(m_h1[row + 1][col] + m_z[row + 1][col] -
                                       m_z[row][col],
                                   0);
                    }
                    else {
                        h_dw = max(m_h1[row][col] + m_z[row][col] -
                                       m_z[row + 1][col],
                                   0);
                    }
                    Gdw = h_dw * v_dw * v_dw;
                }

                if (m_DAMBREAK[row - 1][col] > 0.0 &&
                    ((m_h2[row][col] + m_z[row][col]) <
                     (m_h2[row - 1][col] + m_z[row - 1][col]))) {
                    Gup = m_h1[row - 1][col] *
                          pow((-velocita_breccia(method, m_h1[row - 1][col])),
                              2.0); // -0.4 al quadrato perde il segno meno
                    if (m_h2[row - 1][col] == 0)
                        Gup = 0.0;
                }
                if (m_DAMBREAK[row + 1][col] > 0.0 &&
                    ((m_h2[row][col] + m_z[row][col]) <
                     (m_h2[row + 1][col] + m_z[row + 1][col]))) {
                    Gdw = m_h1[row + 1][col] *
                          pow((velocita_breccia(method, m_h1[row + 1][col])),
                              2.0);
                    if (m_h2[row + 1][col] == 0)
                        Gdw = 0.0;
                }
                G = Gup - Gdw;

                // courant number  --> UPWIND METHOD
                if (m_v1[row][col] > 0 && m_v1[row - 1][col] > 0 &&
                    m_v1[row + 1][col] > 0) {
                    dZ_dy_down = ((m_h2[row - 1][col] + m_z[row - 1][col]) -
                                  (m_h2[row][col] + m_z[row][col])) /
                                 res_ns;
                    if (m_h2[row + 1][col] == 0 &&
                        m_z[row + 1][col] > (m_h2[row][col] + m_z[row][col])) {
                        dZ_dy_up = 0;
                    }
                    else {
                        dZ_dy_up = ((m_h2[row][col] + m_z[row][col]) -
                                    (m_h2[row + 1][col] + m_z[row + 1][col])) /
                                   res_ns;
                    }
                    cr_down = (timestep / res_ns) *
                              fabs(m_v1[row - 1][col] + m_v1[row][col]) / 2.0;
                    cr_up = (timestep / res_ns) *
                            (fabs(m_v1[row][col]) + fabs(m_v1[row + 1][col])) /
                            2.0;
                    Z_piu = 0.0;
                    Z_meno = 0.0;
                }
                else if (m_v1[row][col] < 0 && m_v1[row + 1][col] < 0 &&
                         m_v1[row - 1][col] < 0) {
                    dZ_dy_down = ((m_h2[row][col] + m_z[row][col]) -
                                  (m_h2[row + 1][col] + m_z[row + 1][col])) /
                                 res_ns;
                    if (m_h2[row - 1][col] == 0 &&
                        m_z[row - 1][col] > (m_h2[row][col] + m_z[row][col])) {
                        dZ_dy_up = 0;
                    }
                    else {
                        dZ_dy_up = ((m_h2[row - 1][col] + m_z[row - 1][col]) -
                                    (m_h2[row][col] + m_z[row][col])) /
                                   res_ns;
                    }
                    cr_down = (timestep / res_ns) *
                              fabs(m_v1[row][col] + m_v1[row + 1][col]) / 2.0;
                    cr_up = (timestep / res_ns) *
                            fabs(m_v1[row - 1][col] + m_v1[row][col]) / 2.0;
                    Z_piu = 0.0;
                    Z_meno = 0.0;
                }
                else {
                    if (m_h2[row - 1][col] == 0 &&
                        m_z[row - 1][col] > (m_h2[row][col] + m_z[row][col])) {
                        Z_piu = (m_h2[row][col] + m_z[row][col]);
                    }
                    else {
                        Z_piu = ((m_h2[row - 1][col] + m_z[row - 1][col]) +
                                 (m_h2[row][col] + m_z[row][col])) /
                                2.0;
                    }
                    if (m_h2[row + 1][col] == 0 &&
                        m_z[row + 1][col] > (m_h2[row][col] + m_z[row][col])) {
                        Z_meno = (m_h2[row][col] + m_z[row][col]);
                    }
                    else {
                        Z_meno = ((m_h2[row][col] + m_z[row][col]) +
                                  (m_h2[row + 1][col] + m_z[row + 1][col])) /
                                 2.0;
                    }
                    dZ_dy_down = (Z_piu - Z_meno) / res_ns;
                    dZ_dy_up = (Z_piu - Z_meno) / res_ns;
                    cr_down =
                        (timestep / res_ns) *
                        (fabs(m_u1[row + 1][col]) + 2 * fabs(m_u1[row][col]) +
                         fabs(m_u1[row - 1][col])) /
                        4;
                    cr_up =
                        (timestep / res_ns) *
                        (fabs(m_u1[row + 1][col]) + 2 * fabs(m_u1[row][col]) +
                         fabs(m_u1[row - 1][col])) /
                        4;
                }
                if (m_DAMBREAK[row - 1][col] > 0.0 &&
                    m_h2[row - 1][col] == 0.0) {
                    dZ_dy_up = 0.0;
                    dZ_dy_down = ((m_h2[row][col] + m_z[row][col]) -
                                  (m_h2[row + 1][col] + m_z[row + 1][col])) /
                                 res_ns;
                }
                if (m_DAMBREAK[row + 1][col] > 0.0 &&
                    m_h2[row + 1][col] == 0.0) {
                    dZ_dy_up = 0.0;
                    dZ_dy_down = ((m_h2[row - 1][col] + m_z[row - 1][col]) -
                                  (m_h2[row][col] + m_z[row][col])) /
                                 res_ns;
                }
                dZ_dy =
                    (1 - sqrt(cr_down)) * dZ_dy_down + sqrt(cr_up) * dZ_dy_up;
                // dZ_dy = 0.5 * dZ_dy_down + 0.5 * dZ_dy_up;

                if (m_h1[row][col] < hmin)
                    R_i = hmin;
                else
                    R_i = m_h1[row][col];

                u = m_u1[row][col];
                v = m_v1[row][col];
                V = sqrt(pow(u, 2.0) + pow(v, 2.0));
                S = (-g * m_h2[row][col] * dZ_dy) -
                    g * (pow(m_m[row][col], 2.0) * v * V /
                         pow(R_i, (1.0 / 3.0)));

                if (m_DAMBREAK[row][col] > 0.0) {
                    if ((m_z[row][col] + m_h2[row][col]) >
                        (m_z[row - 1][col] + m_h2[row - 1][col]))
                        m_v2[row][col] = velocita_breccia(
                            method, m_h2[row][col]); // velocita sullo stramazzo
                    else if ((m_z[row][col] + m_h2[row][col]) >
                             (m_z[row + 1][col] + m_h2[row + 1][col]))
                        m_v2[row][col] = -velocita_breccia(
                            method, m_h2[row][col]); // velocita sullo stramazzo
                    else
                        m_v2[row][col] = 0.0;
                }
                else {
                    m_v2[row][col] = 1.0 / m_h2[row][col] *
                                     (m_h1[row][col] * m_v1[row][col] -
                                      timestep / res_ew * F -
                                      timestep / res_ns * G + timestep * S);
                }

                // no velocita' contro la diga
                /*if (m_z[row-1][col] > water_elevation && m_v2[row][col] >0)
                        m_v2[row][col]=0.0;
                if (m_z[row+1][col] > water_elevation && m_v2[row][col] < 0 )
                        m_v2[row][col]=0.0;*/

                if ((timestep / res_ns *
                     (abs(abs(m_v2[row][col]) + sqrt(g * m_h2[row][col])))) >
                    1) {
                    G_warning("At time: %f the Courant-Friedrich-Lewy "
                              "stability condition isn't respected",
                              t);
                    /*G_message("EQ. MOTO DIR Y' --> row:%d, col:%d\n)",row,
                    col);
                    G_message("m_h1[row][col]:%f,m_u1[row][col]:%f,m_v1[row][col]:%f",m_h1[row][col],m_u1[row][col],m_v1[row][col]);
                    G_message("m_h1[row][col+1]:%f,m_h1[row][col-1]:%f,m_h1[row+1][col]:%f,
                    m_h1[row-1][col]:%f\n",m_h1[row][col+1],m_h1[row][col-1],m_h1[row+1][col],
                    m_h1[row-1][col]); G_message("h_dx:%f, h_sx:%f, h_up%f,
                    h_dw:%f\n",h_dx, h_sx, h_up, h_dw);
                    G_message("m_u1[row][col+1]:%f,m_u1[row][col-1]:%f,m_v1[row+1][col]:%f,
                    m_v1[row-1][col]:%f\n",m_u1[row][col+1],m_u1[row][col-1],m_v1[row+1][col],
                    m_v1[row-1][col]); G_message("v_up:
                    %f,v_dw:%f,u_dx:%f,u_sx:%f \n",v_up, v_dw, u_dx, u_sx);
                    G_message("Fdx: %f,Fsx: %f, F: %f, Gup:%f, Gdw:%f, G:
                    %f\n",Fdx, Fsx, F,Gup, Gdw, G);
                    G_message("m_h2[row][col+1]:%f,m_h2[row][col-1]:%f,m_h2[row+1][col]:%f,
                    m_h2[row-1][col]:%f\n",m_h1[row][col+1],m_h1[row][col-1],m_h1[row+1][col],
                    m_h1[row-1][col]); G_message("dZ_dy_down:%f,
                    dZ_dy_up:%f,cr_up:%f, cr_down:%f\n" , dZ_dy_down,dZ_dy_up,
                    cr_up, cr_down); G_message("Z_piu:%f,Z_meno:%f\n", Z_piu,
                    Z_meno); G_message("dZ_dy:%f,\n",dZ_dy);
                    G_message("u:%f,v:%f,V:%f\n", u,v,V);
                    G_message("R_i:%f,manning[row][col]:%f\n", R_i,
                    m_m[row][col]); G_message("S=%f\n",S);
                    G_message("m_v2(row,col): %f\n \n", m_v2[row][col]);
                    G_warning("   ");*/
                }

                //************** stampa
                //******************************************************** if
                // ((t>6.8 && m_v2[row][col]!=m_v1[row][col]) && (row==87) &&
                // (col == 193)) {
                /*if (fabs(m_v2[row][col])>=1000.0){
                        G_warning("At the time %f v(%d,%d)=%f", t,
                row,col,m_v2[row][col]);
                }*/
            }
            else {
                // tolgo h<hmin quando si svuota
                m_u2[row][col] = 0.0;
                m_v2[row][col] = 0.0;
            } // ciclo if (h>hmin)
        }
    }

} /* end function*/
