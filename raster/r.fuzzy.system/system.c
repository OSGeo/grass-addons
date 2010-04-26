#include "local_proto.h"

float implicate(void)
{

    int i, j;
    float *agregate = NULL;
    int set_index;
    float consequent;
    float max_antecedent = 0;
    float result;

    agregate = (float *)G_calloc(resolution, sizeof(float));

    if (coor_proc) /* this is allocated only once */
	visual_output = (float **)G_malloc(resolution * sizeof(float *));

    for (j = 0; j < nrules; ++j) {
	antecedents[j] = parse_expression(j);
	max_antecedent =
	    (max_antecedent >
	     antecedents[j]) ? max_antecedent : antecedents[j];
    }

    if (max_antecedent == 0.)
	return -9999;		/* for all rules value is 0 */

    if (coor_proc)
	for (i = 0; i < resolution; ++i) {
	    visual_output[i] = (float *)G_calloc(nrules + 2, sizeof(float));
	    visual_output[i][0] = universe[i];
	}

    for (j = 0; j < nrules; ++j) {

	if (defuzzyfication > d_BISECTOR && antecedents[j] < max_antecedent)
	    continue;
	    
	    set_index = s_rules[j].output_set_index;

	for (i = 0; i < resolution; ++i) {
	    
	    consequent = fuzzy(universe[i],
			       &s_maps[output_index].sets[set_index]);
	    
	    consequent = (!implication) ? MIN(antecedents[j], consequent) :
		antecedents[j] * consequent;
	    agregate[i] = MAX(agregate[i], consequent);

	    if (coor_proc)
		visual_output[i][j + 1] = consequent;
	}
    }
    if (coor_proc)
	for (i = 0; i < resolution; ++i)
	    visual_output[i][j + 1] = agregate[i];

     result=defuzzify(agregate, defuzzyfication, max_antecedent);
     G_free(agregate);
     return result;
}

float parse_expression(int n)
{

    /*  tokens and actions must heve the same order */
    actions parse_tab[t_size][t_size] = {
	/* stk -----------INPUT------------------ */
	/*  		{   &  | ~   =  (  )  }   */
	/*      --  -- -- -- -- -- -- -- */
	/* { */ {E, S, S, E, E, S, E, A},
	/* & */ {E, R, R, E, E, S, R, R},
	/* | */ {E, R, R, E, E, S, R, R},
	/* ~ */ {E, E, E, E, E, E, E, E},
	/* = */ {E, E, E, E, E, E, E, E},
	/* ( */ {E, S, S, E, E, S, S, E},
	/* ) */ {E, R, R, E, E, E, R, R},
	/* } */ {E, E, E, E, E, E, E, E}
    };

    tokens operator_stack[STACKMAX];
    float values_stack[STACKMAX];

    int i = 0, k = 0;
    int opr_top = 0;
    int val_top = 0;
    int set_index;
    float f_value;

    do {
	if (s_rules[n].work_stack[i] == t_START) {	/* first token */
	    if (i > 0)
		G_fatal_error("operator stack error, contact author");
	    operator_stack[opr_top] = t_START;
	    continue;
	}

	if (s_rules[n].work_stack[i] == t_VAL) {
	    f_value =
		fuzzy(*s_rules[n].value_stack[i].value,
		      s_rules[n].value_stack[i].set);
	    values_stack[++val_top] =
		(s_rules[n].value_stack[i].oper == '~') ? 
			f_not(f_value, family) :	f_value;
	    continue;
	}

	if (s_rules[n].work_stack[i] < t_size) {
	    switch (parse_tab[operator_stack[opr_top]]
		    [s_rules[n].work_stack[i]]) {

	    case E:		/* error */
		G_fatal_error("Stack error, contact author");
		break;

	    case S:		/* shift */
		operator_stack[++opr_top] = s_rules[n].work_stack[i];
		break;

	    case R:		/* reduce */

		switch (operator_stack[opr_top]) {

		case t_AND:
		    values_stack[val_top - 1] =
			f_and(values_stack[val_top],
			      values_stack[val_top - 1], family);
		    val_top--;
		    break;

		case t_OR:
		    values_stack[val_top - 1] =
			f_or(values_stack[val_top], values_stack[val_top - 1],
			     family);
		    val_top--;
		    break;

		case t_RBRC:
		    opr_top--;
		    break;
		}

		opr_top--;
		i--;
		break;

	    case A:		/* accept */
	
		if (!val_top)
		    G_fatal_error("Last Stack error, contact autor");
		return values_stack[val_top];
	
	    }
	}

    } while (s_rules[n].work_stack[i++] != t_STOP);
    
    G_fatal_error("Parse Stack empty, contact autor");
}




float defuzzify(float *agregate, int defuzzification, float max_antecedent)
{
    int i;
    float d_value = 0;
    float sum_agregate = 0;
    float tmp;

    for (i = 0; i < resolution; sum_agregate += agregate[i++]) ;

    switch (defuzzification) {

    case d_CENTEROID:
	for (i = 0; i < resolution; ++i)
	    d_value += (universe[i] * agregate[i]);
	return d_value / sum_agregate;

    case d_BISECTOR:
	for (i = 0, tmp = 0; (tmp += agregate[i]) < sum_agregate / 2; ++i) ;
	return universe[i];

    case d_MINOFHIGHEST:
	for (i = 0; agregate[i++] < max_antecedent;) ;
	return universe[i];

    case d_MAXOFHIGHEST:
	for (i = resolution; agregate[i--] < max_antecedent;) ;
	return universe[i];

    case d_MEANOFHIGHEST:
	sum_agregate = 0;
	for (i = 0; i < resolution; ++i) {
	    if (agregate[i] < max_antecedent)
		continue;
	    d_value += (universe[i] * agregate[i]);
	    sum_agregate += agregate[i];
	}
	return d_value / sum_agregate;
    }

    return -9999;
}
