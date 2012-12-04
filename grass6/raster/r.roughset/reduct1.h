
/****************************************************************************
 *
 * MODULE:       r.roughset
 * AUTHOR(S):    GRASS module authors ad Rough Set Library (RSL) maintain:
 *					G.Massei (g_massa@libero.it)-A.Boggia (boggia@unipg.it)		
 *				 Rough Set Library (RSL) ver. 2 original develop:
 *		         	M.Gawrys - J.Sienkiewicz 
 *
 * PURPOSE:      Geographics rough set analisys and knowledge discovery 
 *
 * COPYRIGHT:    (C) GRASS Development Team (2008)
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/

/***                                                                       ***/

/***               SOME MORE QUERIES FOR SYSTEM                            ***/

/***                   ( FINDING REDUCTS )                                 ***/

/***                                                                       ***/

/*** part of the RSL system written by M.Gawrys J.Sienkiewicz              ***/

/***                                                                       ***/

/*****************************************************************************/



int Red(setA * red, int matrix);

     /* finds all reducts for information system,      */
     /* sets red to yhe allocated reducts table        */
     /* function returns number of reducts             */


int RedRel(setA * red, setA P, setA Q, int matrix_type);

      /* like Red, but reducts are Q-relative and      */
      /* computed from set of attributes P             */

int RedLess(setA * red, int N, int matrix_type);

      /* finds all reducts which contain less than     */
      /* N attributes, other parameters and result     */
      /* like Red                                      */

int RedRelLess(setA * red, setA P, setA Q, int N, int matrix_type);

      /* like RedLess, but reducts are Q-relative of P */


int RedSetA(setA * red, setA quasicore, int matrix_type);

      /* finds only reducts including quasicore ,      */
      /* some reducts can be not minimal ( formally    */
      /* they are not reducts ) , other parameters and */
      /* result like Red                               */

int RedRelSetA(setA * red, setA quasicore, setA P, setA Q, int matrix_type);

      /* like RedSetA, but reducts are Q-relative of P  */


int RedFirst(setA * red, int N, int matrix_type);

      /* finds first N reducts ( only quasi-reduct ),  */
      /* other parameters and result like Red          */

int RedRelFirst(setA * red, setA P, setA Q, int N, int matrix_type);

      /* like RedFirst, but reducts are Q-relative of P */
