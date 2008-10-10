/*******************************************************************/
/*******************************************************************/
/***                                                             ***/
/***              SOME MORE QUERIES FOR SYSTEM                   ***/
/***              (AUXILIARY REDUCTS ROUTINES)                   ***/
/***                                                             ***/
/*** part of the RSL system written by M.Gawrys J.Sienkiewicz    ***/
/***                                                             ***/
/*******************************************************************/
/*******************************************************************/

int RedSingle( setA red, int matrix_type);
	/* heuristicly searches for a single reduct and stores it in red */

int RedRelSingle( setA red, setA P, setA Q, int matrix_type);
	/* heuristicly searches for a single Q-relative reduct of P */
	/* and stores it in red */

int RedOptim( setA red, int matrix_type);
	/* heuristicly searches for a single reduct and stores it in red */
	/* dependency coefficient is used to select */
	/* attributes for search optimization */
		
int RedRelOptim( setA red, setA P, setA Q, int matrix_type);
	/* heuristicly searches for a single Q-relative reduct of P */
	/* and stores it in red; dependency coefficient is used to select */
	/* attributes for search optimization */

int RedFew( setA *reds, int matrix_type);
	/* finds all reducts shortesest or equal in size to the first */
	/* reduct found by the heuristic algorithm */

int RedRelFew( setA *reds, setA P, setA Q, int matrix_type);
	/* finds all Q-relative P-reducts shortesest or equal in size */
	/* to the first reduct found by the heuristic algorithm */

int SelectOneShort( setA reds, int num );
	/* returns index of the single shortest reduct */
	/* from the table of num reducts pointed by reds */
	 
int SelectAllShort( setA *newreds, setA reds, int num);
	/* copies all the shortest reducts */
	/* from the table of num reducts pointed by reds */


