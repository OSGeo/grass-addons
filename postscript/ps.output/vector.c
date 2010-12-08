
#include <string.h>
#include <grass/Vect.h>
#include "vector.h"
#include "ps_info.h"
#include "local_proto.h"


/* allocate memory space for a new vector */
int vector_new(void)
{
    int i = PS.vct_files;

    ++PS.vct_files;
    PS.vct = (VECTOR *) G_realloc(PS.vct, PS.vct_files * sizeof(VECTOR));

    PS.vct[i].type = NONE;
    PS.vct[i].n_item = 0;
    PS.vct[i].item = NULL;

    return i;
}

/* default values for a vector */
int default_vector(int i)
{
    PS.vct[i].id = i;

    PS.vct[i].layer = 1;
    PS.vct[i].cats = NULL;
    PS.vct[i].where = NULL;
    PS.vct[i].masked = 0;
    PS.vct[i].label = NULL;

    PS.vct[i].lpos = 0;
    PS.vct[i].cols = 1;
    PS.vct[i].yspan = -1;

    PS.vct[i].n_item = 0;
    PS.vct[i].item = NULL;
    PS.vct[i].n_rule = 0;
    PS.vct[i].rule = NULL;
}

/* find the rule by value */
int vector_rule_find(VECTOR * vct, double value)
{
    int i, j;

    for (i = 0; i < vct->n_rule; i++) {
	for (j = 0; j < vct->rule[i].count; j++) {
	    if (value >= vct->rule[i].val_list[j] &&
		value <= vct->rule[i].val_list[j + 1]) {
		return i;
	    }
	}
    }
    return -1;
}

/* allocate memory space for a new legend item */
int vector_item_new(VECTOR * vct, double value, long data)
{
    int i, k, rule;

    rule = vector_rule_find(vct, value);

    /* Check if already exist */
    for (k = 0; k < vct->n_item; k++) {
	if (vct->item[k].rule == -1) {
	    if (vct->item[k].data == data)
		return k;
	}
	else {
	    if (vct->item[k].rule == rule)
		return k;
	}
    }

    i = vct->n_item;

    ++(vct->n_item);
    vct->item = (ITEMS *) G_realloc(vct->item, vct->n_item * sizeof(ITEMS));
    vct->item[i].rule = rule;
    vct->item[i].data = data;

    return i;
}

/* allocate memory space for a new vector rule */
int vector_rule_new(VECTOR * vct, char *catsbuf, char *label, double value)
{
    int k, i = vct->n_rule;

    ++(vct->n_rule);
    vct->rule = (RULES *) G_realloc(vct->rule, vct->n_rule * sizeof(RULES));
    vct->rule[i].id = i;
    vct->rule[i].value = value;
    vct->rule[i].label = (label == NULL) ? NULL : G_store(label);
    vct->rule[i].count = parse_val_list(catsbuf, &(vct->rule[i].val_list));

    return i;
}
