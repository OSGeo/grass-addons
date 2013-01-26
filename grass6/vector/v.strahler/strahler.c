#include "strahler.h"

/* Find Leaves of tree and distinguish outlet from sources */
int StrahFindLeaves(struct Map_info *In, DBBUF * dbbuf, NODEV * nodev,
		    int ntrees, int fdrast)
{
    int nnodes, degr, aline, node, unode, dnode, tree, outlet;
    double x, y, z, z_init;

    int n;

    struct Cell_head window;
    INTERP_TYPE method = NEAREST;

    OUTLETS *outlets;

    nnodes = Vect_get_num_nodes(In);

    z = z_init = 27000000.0;	/* is it safe to initialize lowest z with the height of Olympus Mons above Martian Datum in millimeters? */

    outlets = (OUTLETS *) G_malloc((ntrees + 1) * ((int)sizeof(OUTLETS)));

    /* initialize outlet table properly */
    for (n = 1; n <= ntrees; n++) {
	outlets[n].z = z_init;
	outlets[n].leaf = 0;
    }

    G_debug(1, "Reached StrahFindLeaves with %d trees", ntrees);

    G_get_window(&window);
    G_debug(2, "window: N %f S %f W %f E %f", window.north, window.south,
	    window.west, window.east);

    G_debug(2, "%d nodes in map", nnodes);
    for (node = 1; node <= nnodes; node++) {
	/*degr = Vect_get_node_n_lines( In, node ); */
	degr = StrahGetDegr(In, node);
	nodev[node].node = node;
	nodev[node].degree = degr;

	G_debug(4, "node %d: degr=%d", node, degr);

	if (degr == 1) {
	    unode = node;
	    nodev[node].visited = 1;	/*set the "visited" parameter to 1... can't be less */
	    /*aline = abs( Vect_get_node_line( In, unode, 0 ) ); */
	    aline = abs(StrahGetNodeLine(In, unode, 0));
	    /*Vect_get_line_nodes( In, aline, &unode, &dnode); */
	    /* these are not necessarily up-node and down-node but we need not distinguish here... */
	    dbbuf[aline].sorder = 1;
	    /* no, do not visit yet 
	       nodev[node].visited += 1;
	     */
	    /*
	       nodev[unode].visited += 1;
	       nodev[dnode].visited += 1;
	     */
	    /* get z value or DEM value under node here, remember lowest */
	    if (Vect_is_3d(In)) {
		Vect_get_node_coor(In, node, &x, &y, &z);
	    }
	    else {
		Vect_get_node_coor(In, node, &x, &y, NULL);
		z = (double)G_get_raster_sample(fdrast, &window, NULL, y, x,
						0, method);
	    }

	    G_debug(5, "fdrast=%d node=%d y=%f x=%f z=%f", fdrast, node, y,
		    x, z);

	    tree = dbbuf[aline].bsnid;
	    if (z < outlets[tree].z) {
		outlets[tree].z = z;
		outlets[tree].leaf = aline;
	    }
	}
    }
    /* reset outlets to 0 */
    for (n = 1; n <= ntrees; n++) {
	G_debug(2, "outlet tree %d: line %d with %f", n, outlets[n].leaf,
		outlets[n].z);
	outlet = outlets[n].leaf;
	dbbuf[outlet].sorder = 0;
	/*
	   Vect_get_line_nodes( In, outlet, &unode, &dnode);
	   nodev[unode].visited = 0;
	   nodev[dnode].visited = 0;
	 */
    }
    return 1;
}

/* assign strahler order */
int StrahOrder(struct Map_info *In, DBBUF * dbbuf, NODEV * nodev)
{
    int nlines, line;
    int fnode, tnode, unode, dnode;	/* from-, to-, up-, down- node */
    int degr, d, aline, aorder;	/* find adjacent lines */
    int corder, norder, dorder, dline;	/* assign order */
    int cline, rfinish;		/* follow one line until this stop-condition is 1 */

    struct dbbuf;
    struct nodev;

    nlines = Vect_get_num_lines(In);

    G_debug(1, "reached StrahOrder");

    for (line = 1; line <= nlines; line++) {
	if (dbbuf[line].sorder == 1) {	/* get lines of order 1 */

	    cline = line;	/* and start run downwards */
	    rfinish = 0;
	    while (rfinish == 0) {
		G_debug(3, "reached line %d", cline);

		Vect_get_line_nodes(In, cline, &fnode, &tnode);	/* and their nodes */

		/**** BAUSTELLE ****/
		/* check nodes - we do not rely on flow direction */
		if (nodev[fnode].visited == 1) {
		    unode = fnode;
		    dnode = tnode;
		}
		else {
		    unode = tnode;
		    dnode = fnode;
		}

		/*
		   if (nodev[fnode].visited == nodev[tnode].visited) {
		   printf("Line %d: both nodes are visited or not - what now?\n", line);
		   } else if (nodev[fnode].visited == 0) {
		   node = fnode;
		   } else {
		   node = tnode;
		   }
		 */

		/* 
		   if ( (nodev[fnode].degree - nodev[fnode].visited) < (nodev[tnode].degree - nodev[tnode].visited) ) {
		   unode = fnode;
		   dnode = tnode;
		   } else if ( (nodev[fnode].degree - nodev[fnode].visited) > (nodev[tnode].degree - nodev[tnode].visited) ) {
		   unode = tnode;
		   dnode = fnode;
		   } else {
		   G_message("Line %d: nodes have same diff(degree,visited) - what now?\n", cline);
		 */
		/* ok, what now?
		   - occurs when leaf meets node with norder==0 -> visit nodes and continue
		   - or: is outlet -> assign order
		 */
		/* continue? */
		/*
		   printf("visiting tnode %d and fnode %d for line %d and break\n\n", tnode, fnode, cline);
		   nodev[tnode].visited += 1;
		   nodev[fnode].visited += 1;
		   break;
		   }
		 */

		G_debug(3, "unode is %d and dnode is %d", unode, dnode);

		/*degr = Vect_get_node_n_lines ( In, dnode );            use downward node */
		degr = StrahGetDegr(In, dnode);

		G_debug(4, "deg for dnode %d is %d", dnode, degr);

		corder = dbbuf[cline].sorder;	/* current order - result won't be less than that */
		norder = dorder = 0;	/* no order - how many lines have none?, highest order of others */
		for (d = 0; d < degr; d++) {
		    /*aline = abs( Vect_get_node_line ( In, dnode, d ) ); */
		    aline = abs(StrahGetNodeLine(In, dnode, d));
		    G_debug(4, "line %d at dnode %d is %d", d, dnode, aline);
		    if (aline != cline) {	/* we don't need the line we come from */
			aorder = dbbuf[aline].sorder;
			if (aorder == 0) {
			    norder++;
			    dline = aline;	/* downward line */
			}
			else if (aorder > dorder) {
			    dorder = aorder;	/* find highest order */
			}
		    }
		}

		if (norder > 1 || norder == 0) {	/* if (norder > 1: node indeterminate OR norder == 0 : subtree finished) */
		    G_debug(3, "Finished run at line %d because norder=%d",
			    cline, norder);
		    G_debug(4, "visiting unode %d for line %d", unode, cline);
		    nodev[unode].visited += 1;	/* visit unode, for the sake of completeness */
		    rfinish = 1;	/* finish this run */

		}
		else {		/* or */
		    if (dorder > corder) {
			;	/* assign highest order of alines */
		    }
		    else if (dorder < corder) {
			dorder = corder;	/* or keep order of cline */
		    }
		    else {
			dorder++;	/* or raise order by one */
		    }

		    dbbuf[dline].sorder = dorder;	/* assign order */

		    G_debug(4, "visiting dnode %d and unode %d for line %d",
			    dnode, unode, cline);
		    nodev[dnode].visited += 1;	/* visit dnode */
		    nodev[unode].visited += 1;	/* visit unode, for the sake of completeness */

		    cline = dline;	/* and continue with this line */

		    G_debug(3, "StrahOrder for dline %d: %d", dline, dorder);
		}
	    }			/* while */
	}
    }
    return 1;
}
