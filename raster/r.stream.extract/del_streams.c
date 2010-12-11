#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "local_proto.h"

/* delete short stream segments according to threshold */
int del_streams(int min_length)
{
    int i;
    int n_deleted = 0;
    unsigned int thisindex, next_stream_pos = -1;
    int curr_stream, stream_id, other_trib, tmp_trib;
    int slength;

    G_message(_("Delete stream segments shorter than %d cells..."), min_length);

    /* go through all nodes */
    for (i = 1; i <= n_stream_nodes; i++) {
	G_percent(i, n_stream_nodes, 2);

	/* not a stream head */
	if (stream_node[i].n_trib > 0)
	    continue;

	/* already deleted */
	thisindex = INDEX(stream_node[i].r, stream_node[i].c);
	if (stream[thisindex] == 0)
	    continue;

	/* get length counted as n cells */
	if ((slength = seg_length(i, &next_stream_pos)) >= min_length)
	    continue;

	stream_id = i;

	/* check n sibling tributaries */
	if ((curr_stream = stream[next_stream_pos]) != stream_id) {
	    /* only one sibling tributary */
	    if (stream_node[curr_stream].n_trib == 2) {
		if (stream_node[curr_stream].trib[0] != stream_id)
		    other_trib = stream_node[curr_stream].trib[0];
		else
		    other_trib = stream_node[curr_stream].trib[1];

		/* other trib is also stream head */
		if (stream_node[other_trib].n_trib == 0) {
		    /* use shorter one */
		    if (seg_length(other_trib, NULL) < slength) {
			tmp_trib = stream_id;
			stream_id = other_trib;
			other_trib = tmp_trib;
		    }
		}
		del_stream_seg(stream_id);
		n_deleted++;
		
		/* update downstream IDs */
		update_stream_id(curr_stream, other_trib);
	    }
	    /* more than one other tributary */
	    else {
		del_stream_seg(stream_id);
		n_deleted++;
	    }
	}
	/* stream head is also outlet */
	else {
	    del_stream_seg(stream_id);
	    n_deleted++;
	}
    }

    G_verbose_message(_("%d stream segments deleted"), n_deleted);

    return n_deleted;
}

/* get stream segment length */
int seg_length(int stream_id, unsigned int *new_stream_pos)
{
    int r, c, r_nbr, c_nbr;
    int slength = 1;
    struct ddir draindir, *founddir;
    int curr_stream;
    int asp_r[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int asp_c[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };

    r = stream_node[stream_id].r;
    c = stream_node[stream_id].c;

    /* get next downstream point */
    draindir.pos = INDEX(r, c);
    if (new_stream_pos)
	*new_stream_pos = draindir.pos;
    while ((founddir = rbtree_find(draintree, &draindir)) != NULL) {
	r_nbr = r + asp_r[(int)founddir->dir];
	c_nbr = c + asp_c[(int)founddir->dir];

	/* user-defined depression */
	if (r_nbr == r && c_nbr == c)
	    break;
	/* outside region */
	if (r_nbr < 0 || r_nbr >= nrows || c_nbr < 0 || c_nbr >= ncols)
	    break;
	/* next stream */
	if ((curr_stream = stream[INDEX(r_nbr, c_nbr)]) != stream_id) {
	    if (new_stream_pos)
		*new_stream_pos = INDEX(r_nbr, c_nbr);
	    break;
	}
	slength++;
	r = r_nbr;
	c = c_nbr;
	if (new_stream_pos)
	    *new_stream_pos = draindir.pos;
	draindir.pos = INDEX(r, c);
    }

    return slength;
}

/* delete stream segment */
int del_stream_seg(int stream_id)
{
    int i, r, c, r_nbr, c_nbr;
    unsigned int this_index;
    struct ddir draindir, *founddir;
    int curr_stream;
    int asp_r[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int asp_c[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };

    r = stream_node[stream_id].r;
    c = stream_node[stream_id].c;
    this_index = INDEX(r, c);
    stream[this_index] = 0;
    curr_stream = stream_id;

    /* get next downstream point */
    draindir.pos = this_index;
    while ((founddir = rbtree_find(draintree, &draindir)) != NULL) {
	r_nbr = r + asp_r[(int)founddir->dir];
	c_nbr = c + asp_c[(int)founddir->dir];

	/* user-defined depression */
	if (r_nbr == r && c_nbr == c)
	    break;
	/* outside region */
	if (r_nbr < 0 || r_nbr >= nrows || c_nbr < 0 || c_nbr >= ncols)
	    break;
	/* next stream */
	if ((curr_stream = stream[INDEX(r_nbr, c_nbr)]) != stream_id)
	    break;
	r = r_nbr;
	c = c_nbr;
	this_index = INDEX(r, c);
	stream[this_index] = 0;
	rbtree_remove(draintree, &draindir);
	draindir.pos = this_index;
    }

    /* update tributaries */
    if (curr_stream != stream_id) {
	for (i = 0; i < stream_node[curr_stream].n_trib; i++) {
	    if (stream_node[curr_stream].trib[i] == stream_id) {
		stream_node[curr_stream].trib[i] = stream_node[curr_stream].trib[stream_node[curr_stream].n_trib - 1];
		stream_node[curr_stream].n_trib--;
		break;
	    }
	}
    }

    return 1;
}

/* update downstream id */
int update_stream_id(int stream_id, int new_stream_id)
{
    int i, r, c, r_nbr, c_nbr;
    unsigned int this_index;
    struct ddir draindir, *founddir;
    int curr_stream;
    int asp_r[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int asp_c[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };

    r = stream_node[stream_id].r;
    c = stream_node[stream_id].c;
    this_index = INDEX(r, c);
    stream[this_index] = new_stream_id;
    curr_stream = stream_id;

    /* get next downstream point */
    draindir.pos = this_index;
    while ((founddir = rbtree_find(draintree, &draindir)) != NULL) {
	r_nbr = r + asp_r[(int)founddir->dir];
	c_nbr = c + asp_c[(int)founddir->dir];

	/* user-defined depression */
	if (r_nbr == r && c_nbr == c)
	    break;
	/* outside region */
	if (r_nbr < 0 || r_nbr >= nrows || c_nbr < 0 || c_nbr >= ncols)
	    break;
	/* next stream */
	if ((curr_stream = stream[INDEX(r_nbr, c_nbr)]) != stream_id)
	    break;
	r = r_nbr;
	c = c_nbr;
	this_index = INDEX(r, c);
	stream[this_index] = new_stream_id;
	draindir.pos = this_index;
    }

    /* update tributaries */
    if (curr_stream != stream_id) {
	for (i = 0; i < stream_node[curr_stream].n_trib; i++) {
	    if (stream_node[curr_stream].trib[i] == stream_id) {
		stream_node[curr_stream].trib[i] = new_stream_id;
		break;
	    }
	}
    }

    return curr_stream;
}
