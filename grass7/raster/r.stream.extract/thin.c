#include <stdlib.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "local_proto.h"

int thin_seg(int stream_id)
{
    int thinned = 0;
    int r, c, r_nbr, c_nbr, last_r, last_c;
    unsigned int thisindex, lastindex;
    struct ddir draindir, *founddir;
    int curr_stream;
    int asp_r[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int asp_c[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };

    r = stream_node[stream_id].r;
    c = stream_node[stream_id].c;

    thisindex = INDEX(r, c);

    curr_stream = stream[thisindex];
    if (curr_stream != stream_id)
	G_fatal_error(_("BUG: stream node and stream not identical: stream id %d, stream node id %d, stream %d"),
		      stream_id, stream_node[stream_id].id, curr_stream);

    draindir.pos = thisindex;
    if ((founddir = rbtree_find(draintree, &draindir)) != NULL) {
	/* get downstream point */
	last_r = r + asp_r[(int)founddir->dir];
	last_c = c + asp_c[(int)founddir->dir];
	curr_stream = stream[INDEX(last_r, last_c)];

	if (curr_stream != stream_id)
	    return thinned;

	/* get next downstream point */
	draindir.pos = INDEX(last_r, last_c);
	while ((founddir = rbtree_find(draintree, &draindir)) != NULL) {
	    r_nbr = last_r + asp_r[(int)founddir->dir];
	    c_nbr = last_c + asp_c[(int)founddir->dir];

	    if (r_nbr == last_r && c_nbr == last_c)
		return thinned;
	    if (r_nbr < 0 || r_nbr >= nrows || c_nbr < 0 || c_nbr >= ncols)
		return thinned;
	    if ((curr_stream = stream[INDEX(r_nbr, c_nbr)]) != stream_id)
		return thinned;
	    if (abs(r_nbr - r) < 2 && abs(c_nbr - c) < 2) {
		/* eliminate last point */
		lastindex = INDEX(last_r, last_c);
		stream[lastindex] = 0;
		draindir.pos = lastindex;
		rbtree_remove(draintree, &draindir);
		/* update start point */
		draindir.pos = thisindex;
		founddir = rbtree_find(draintree, &draindir);
		founddir->dir = drain[r - r_nbr + 1][c - c_nbr + 1];
		asp[draindir.pos] = founddir->dir;
		last_r = r_nbr;
		last_c = c_nbr;
		draindir.pos = INDEX(last_r, last_c);

		thinned = 1;
	    }
	    else {
		/* nothing to eliminate, continue from last point */
		r = last_r;
		c = last_c;
		last_r = r_nbr;
		last_c = c_nbr;
		thisindex = INDEX(r, c);
		draindir.pos = INDEX(last_r, last_c);
	    }
	}
    }

    return thinned;
}

int thin_streams(void)
{
    int i, j, r, c, done;
    int stream_id, next_node;
    unsigned int thisindex;
    struct sstack
    {
	int stream_id;
	int next_trib;
    } *nodestack;
    int top = 0, stack_step = 1000;
    int n_trib_total;

    G_message(_("Thin stream segments..."));

    nodestack = (struct sstack *)G_malloc(stack_step * sizeof(struct sstack));

    for (i = 0; i < n_outlets; i++) {
	G_percent(i, n_outlets, 2);
	r = outlets[i].r;
	c = outlets[i].c;
	thisindex = INDEX(r, c);
	stream_id = stream[thisindex];

	if (stream_id == 0)
	    continue;

	/* add root node to stack */
	G_debug(2, "add root node");
	top = 0;
	nodestack[top].stream_id = stream_id;
	nodestack[top].next_trib = 0;

	/* depth first post order traversal */
	G_debug(2, "traverse");
	while (top >= 0) {

	    done = 1;
	    stream_id = nodestack[top].stream_id;
	    G_debug(3, "stream_id %d, top %d", stream_id, top);
	    if (nodestack[top].next_trib < stream_node[stream_id].n_trib) {
		/* add to stack */
		G_debug(3, "get next node");
		next_node =
		    stream_node[stream_id].trib[nodestack[top].next_trib];
		G_debug(3, "add to stack: next %d, trib %d, n trib %d",
			next_node, nodestack[top].next_trib,
			stream_node[stream_id].n_trib);
		nodestack[top].next_trib++;
		top++;
		if (top >= stack_step) {
		    /* need more space */
		    stack_step += 1000;
		    nodestack =
			(struct sstack *)G_realloc(nodestack,
						   stack_step *
						   sizeof(struct sstack));
		}

		nodestack[top].next_trib = 0;
		nodestack[top].stream_id = next_node;
		done = 0;
		G_debug(3, "go further down");
	    }
	    if (done) {
		/* thin stream segment */
		G_debug(3, "thin stream segment %d", stream_id);

		if (thin_seg(stream_id) == 0)
		    G_debug(3, "segment %d not thinned", stream_id);
		else
		    G_debug(3, "segment %d thinned", stream_id);

		top--;
		/* count tributaries */
		if (top >= 0) {
		    n_trib_total = 0;
		    stream_id = nodestack[top].stream_id;
		    for (j = 0; j < stream_node[stream_id].n_trib; j++) {
			/* intermediate */
			if (stream_node[stream_node[stream_id].trib[j]].
			    n_trib > 0)
			    n_trib_total +=
				stream_node[stream_node[stream_id].trib[j]].
				n_trib_total;
			/* start */
			else
			    n_trib_total++;
		    }
		    stream_node[stream_id].n_trib_total = n_trib_total;
		}
	    }
	}
    }
    G_percent(n_outlets, n_outlets, 1);	/* finish it */

    G_free(nodestack);

    return 1;
}
