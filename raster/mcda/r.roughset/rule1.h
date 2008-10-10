/*******************************************************************/
/*******************************************************************/
/***                                                             ***/
/***               SOME MORE QUERIES FOR SYSTEM                  ***/
/***                   ( MENAGING RULES )                         ***/
/***                                                             ***/
/***  part of the RSL system written by M.Gawrys J.Sienkiewicz   ***/
/***                                                             ***/
/*******************************************************************/
/*******************************************************************/

#define MINUS ((value_type)-1)

void RuleCopy( value_type *dest,value_type *source);
	/* copies a rule from source to dest */
	
int RuleEQ( value_type *first,value_type *second);
	/* returns 1 if first rule is equal to second */

void AddRule( value_type *rules,int *size,value_type *rule);
	/* adds new rule to array of rules */
	/* if the rule is unique size is incremented */
