#include "strahler.h"

/* helper functions for ForestToTrees:
   push_line: push number of adjacent line on stack
   pop_line: return number of top line on stack
   we could do this with some Vect_list but we don't need 
   to handle entire lines, only their identifiers */

#define STACK_SIZE 65535
int sp = 0;			/* stack position */
int stack[STACK_SIZE];		/* generous stack size */

void push_line(int line)
{
    if (sp < STACK_SIZE) {
	stack[sp++] = line;
    }
    else {
	G_fatal_error("ForestToTrees: stack full");
    }
}

int pop_line(void)
{
    if (sp > 0) {
	return stack[--sp];
    }
    else {
	G_debug(3, "ForestToTrees: stack empty, tree finished");
	return 0;
    }
}


/* or write our own lfind: nexttree() */
/* start at offset, walk array up until bsnid == 0 and return that offset */

int nexttree(DBBUF * dbbuf, int offset, int upper)
{
    while ((dbbuf[offset].bsnid != 0) && (offset < upper)) {
	++offset;
	G_debug(4, "bsnid[%d] is %d", offset, dbbuf[offset].bsnid);
    }
    return offset;
}

/* Find trees, assign basinID */
int StrahForestToTrees(struct Map_info *In, struct Map_info *Out,
		       DBBUF * dbbuf)
{
    int tree, tree_finished, forest_done;	/* ID of tree (basin), processing status */
    int l, n, d, degr, node;	/* iterators */
    int nlines, offset;		/* number of lines, position in dbbuf */
    int cline, aline;		/* currently harvested line, adjacent line */
    int lnodes[2];		/* nodes of cline */


    G_debug(1, "reached StrahForestToTrees");

    nlines = Vect_get_num_lines(In);

    forest_done = 0;
    tree = 1;			/* we start with tree no. 1 */
    offset = cline = 1;		/* we start at line 1 */

    while (forest_done == 0) {
	G_debug(3, "\nProcessing Tree %d", tree);
	tree_finished = 0;	/* initialize status indicator for this tree */
	while (tree_finished == 0) {
	    /* procedure to get adjacent lines and push them on the stack */
	    Vect_get_line_nodes(In, cline, &lnodes[0], &lnodes[1]);
	    G_debug(4, "nodes for line %d: %d %d", cline, lnodes[0],
		    lnodes[1]);

	    for (n = 0; n <= 1; n++) {	/* loop through array[2] of fnode and tnode */
		node = lnodes[n];
		/*degr = Vect_get_node_n_lines( In, node ); */
		degr = StrahGetDegr(In, node);
		G_debug(4, "degr %d for node %d", degr, node);
		for (d = 0; d < degr; d++) {
		    /*aline = abs( Vect_get_node_line( In, node, d ) ); */
		    aline = abs(StrahGetNodeLine(In, node, d));
		    if (dbbuf[aline].bsnid == 0) {	/* push line on stack only if not done yet */
			G_debug(4, "pushing line %d on sp %d", aline, sp);
			push_line(aline);
			G_debug(4, "pushed, sp is now %d", sp);
			dbbuf[aline].bsnid = tree;	/* line is done when pushed on stack */
			dbbuf[aline].line = aline;
		    }
		}
	    }

	    /* pop a line from stack */
	    cline = (int)pop_line();
	    G_debug(4, "popped line %d", cline);
	    /* tree is finished when pop_line returned 0 */
	    if (cline == 0) {
		tree_finished = 1;
	    }
	}

	/* get first cline of next tree */
	offset = cline = nexttree(dbbuf, ++offset, nlines);
	G_debug(3, "cline/offset for tree %d is %d", tree, cline);
	if (offset == nlines) {
	    forest_done = 1;	/* what if last line still is 0 - it is a tree consisting of this line only - it shall keep bsnid 0 */
	}
	else {
	    tree++;		/* continue with next tree */
	}
    }

    return tree;
}
