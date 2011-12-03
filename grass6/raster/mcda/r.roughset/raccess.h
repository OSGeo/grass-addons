
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

/***             FUNCTIONS OF ACCESS TO SYSTEM TABLES                      ***/

/***                                                                       ***/

/***  part of the RSL system written by M.Gawrys J. Sienkiewicz            ***/

/***                                                                       ***/

/*****************************************************************************/


#define START_OF_D 	_table_element=_mainsys->matD,_table_end=_table_element+Dsize(_mainsys)
#define START_OF_X 	_table_element=_mainsys->matX,_table_end=_table_element+_mainsys->matXsize
#define START_OF_MAT(set,num) _table_element=(set),_table_end=_table_element+(num)*_mainsys->setAsize
#define END_OF_MAT     (_table_element<_table_end)
#define NEXT_OF_MAT    _table_element+=_mainsys->setAsize
#define ELEM_OF_MAT    _table_element
#define ElemOfRule(rules,num,attr) (rules)[(num)*(_mainsys->attributes_num)+(attr)]

extern setA _table_element;
extern setA _table_end;
extern int _table_row;
extern int _table_column;
extern int _table_no;


int start_of_tab(int matrix_type);
void next_of_tab(void);
int end_of_tab(void);


int CompareA(int ob1, int ob2, setA P);
int CompareD(int ob1, int ob2, setA P);

	/* compares two objects, returns 1 if all attributes from */
	/* the set P are identical, otherwise returns 0 */

int SingCompA(int ob1, int ob2, int atr);
int SingCompD(int ob1, int ob2, int atr);

	/* compares two objects on the sigle attribute atr */
	/* returns 1 if identical, otherwise returns 0 */

setA GetD(int ob1, int ob2);

	/* returns a single element of matrix D, if this set */
	/* is going to be changed, it has to be first copied */

value_type GetA(int obj, int atr);

	/* returns value of attribute atr of object obj */
	/* from matrix A */

int GetDfromA(setA elem, int ob1, int ob2);

	/* generate a single element of matrix D into elem */
