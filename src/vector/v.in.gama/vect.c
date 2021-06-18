#include "global.h"

int create_map(struct Map_info *Map, xmlDoc * doc, int dotable)
{
    struct list_points *vpoints;

    list_init((void **)&vpoints);

    create_points(Map, doc, dotable, &vpoints);

    create_obs(Map, doc, options.dotable, vpoints);

    list_points_free(&vpoints);

    return 0;
}

int create_points(struct Map_info *Map, xmlDoc * doc, int dotable,
		  struct list_points **vpoints)
{

    unsigned int i;

    xmlNode *root_element = NULL;

    xmlNode *points;
    struct list_nodes *point;
    xmlNode *id, *coor_x, *coor_y, *coor_z;

    Point *vpoint;

    const char *coor_type[] = { "fixed", "adjusted", "approximate" };

    dbString sid;

    db_init_string(&sid);

    list_init((void **)&point);

    root_element = xmlDocGetRootElement(doc);

    if (root_element == NULL) {
	G_fatal_error(_("Unable to get the root element"));
    }

    for (i = 0; i < sizeof(coor_type) / sizeof(char *); i++) {
	find_node(root_element, coor_type[i], &points);
	if (points) {
	    find_nodes(points, "point", &point);

	    if (point) {
		struct list_nodes *tp = point;

		while (tp) {
		    find_node(tp->node, "id", &id);
		    find_node(tp->node, "x", &coor_x);
		    find_node(tp->node, "y", &coor_y);
		    find_node(tp->node, "z", &coor_z);

		    if ((node_get_value_string(id, NULL, &sid)) &&
			(vpoint = find_point(*vpoints, &sid))) {
			point_update(vpoint, i, coor_x, coor_y, coor_z);
		    }
		    else {
			/* G_free () in function list_points_free () */
			vpoint = (Point *)
			    G_malloc((unsigned int)sizeof(Point));

			point_init(vpoint);

			point_set(vpoint, id, i, coor_x, coor_y, coor_z);

			list_points_push_back(vpoints, vpoint);
		    }
		    tp = tp->next;
		}
	    }
	}
    }

    /* write new vector element && insert records into table */
    write_points(Map, root_element, *vpoints, dotable);

    list_nodes_free(&point);

    return 0;
}

void point_init(Point * point)
{
    int i, j;

    point->cat = -1;

    db_init_string(&(point->id));

    for (i = 0; i < DIM; i++) {	/* x | y | z */
	for (j = 0; j < DIM; j++) {	/* fix | adj | app */
	    point->xyz[i].is_null[j] = 1;
	}
	point->xyz[i].is_constrained = 0;
    }

    return;
}
void point_set(Point * point, xmlNode * id, int type,
	       xmlNode * x, xmlNode * y, xmlNode * z)
{

    unsigned int i;
    dbString idvalue;
    double dvalue;
    const char *XYZ[] = { "X", "Y", "Z" };

    xmlNode *nodes[] = { x, y, z };

    db_init_string(&idvalue);

    if (id && node_get_value_string(id, NULL, &idvalue)) {
	db_copy_string(&(point->id), &idvalue);
    }
    else {
	G_warning("Missing point id");
    }

    for (i = 0; i < sizeof(nodes) / sizeof(struct list_nodes *); i++) {
	if (nodes[i]) {
	    if (node_get_value_double(nodes[i], &dvalue)) {

		point->xyz[i].val[type] = dvalue;
		point->xyz[i].is_null[type] = 0;

		if (!strcmp((char *)nodes[i]->name, XYZ[i])) {	/* cannot be G_strcasecmp */
		    point->xyz[i].is_constrained = 1;
		}
	    }
	}
    }

    return;
}

void write_points(struct Map_info *Map, xmlNode * root,
		  struct list_points *points, int dotable)
{
    int i, j, cat;
    double xyz[DIM];
    short xyz_null[DIM];

    struct list_points *lp;
    Point *p;

    struct line_pnts *ps;
    struct line_cats *cs;

    struct field_info *fi;

    dbDriver *driver;
    dbTable *table;
    dbString axes_xy, table_name;

    struct list_nodes *network_param;

    enum axes_xy_type
    {
	NE, SW, ES, WN,		/* right-handed */
	EN, WS, SE, NW		/* left-handed */
    };

    int xy_type;

    cat = 1;
    lp = points;
    list_init((void **)&network_param);
    db_init_string(&axes_xy);

    ps = Vect_new_line_struct();
    cs = Vect_new_cats_struct();

    if (dotable) {
	fi = Vect_get_dblink(Map, FIELD_POINT - 1);

	if (!fi) {
	    G_fatal_error(_("Database connection not defined for layer %d"), FIELD_POINT - 1);
	}

	driver = db_start_driver_open_database(fi->driver, fi->database);

	if (!driver) {
	    G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
			  fi->database, fi->driver);
	}

	db_init_string(&table_name);
	db_set_string(&table_name, fi->table);

	if (db_describe_table(driver, &table_name, &table) != DB_OK) {
	    G_fatal_error(_("Unable to describe table <%s>"), fi->table);
	}

	db_begin_transaction(driver);
    }

    xy_type = -1;
    find_nodes(root, "network-general-parameters", &network_param);
    if (network_param) {
	if (node_get_value_string(network_param->node, "axes-xy", &axes_xy)) {
	    if (db_sizeof_string(&axes_xy) > 0) {
		xy_type = axes_xy_str2type(db_get_string(&axes_xy));
	    }
	}
    }

    if (xy_type == -1) {
	G_warning("Unable to recognize 'axes-xy' attribute, "
		  "switching to the default value 'en'");
	xy_type = NE;
    }

    while (lp) {
	p = lp->point;		/* should not be NULL */
	if (p) {
	    for (i = 0; i < DIM; i++) {
		xyz_null[i] = 1;
	    }

	    for (i = 0; i < DIM; i++) {	/* x | y | z */
		for (j = 0; j < DIM; j++) {	/* fix | adj | app */
		    if (xyz_null[i] && !(p->xyz[i].is_null[j])) {
			xyz[i] = p->xyz[i].val[j];
			xyz_null[i] = 0;
		    }
		}
	    }

	    if (xyz_null[2] && Vect_is_3d(Map)) {
		G_warning(_("Point id '%s': cannot set coordinate z"),
			  db_get_string(&(p->id)));
		xyz[2] = 0.0;
	    }

	    if (xyz_null[0] || xyz_null[1]) {
		G_warning(_("Point id '%s': missing coordinate x|y!"),
			  db_get_string(&(p->id)));
	    }
	    else {
		/* acceptable values
		   right-handed:
		   * ne
		   * sw
		   * es
		   * wn
		   left-handed:
		   * en
		   * ws
		   * se
		   * nw
		   ---
		 */

		switch (xy_type) {
		case NE:
		    {
			Vect_append_point(ps, xyz[1], xyz[0], xyz[2]);
			break;
		    }
		case SW:
		    {
			Vect_append_point(ps, -1.0 * xyz[1], -1.0 * xyz[0],
					  xyz[2]);
			break;
		    }
		case ES:
		    {
			Vect_append_point(ps, xyz[0], -1.0 * xyz[1], xyz[2]);
			break;
		    }
		case WN:
		    {
			Vect_append_point(ps, -1.0 * xyz[0], xyz[1], xyz[2]);
			break;
		    }
		case EN:
		    {
			Vect_append_point(ps, xyz[0], xyz[1], xyz[2]);
			break;
		    }
		case WS:
		    {
			Vect_append_point(ps, -1.0 * xyz[0], -1.0 * xyz[1],
					  xyz[2]);
			break;
		    }
		case SE:
		    {
			Vect_append_point(ps, xyz[1], -1.0 * xyz[0], xyz[2]);
			break;
		    }
		case NW:
		    {
			Vect_append_point(ps, -1.0 * xyz[1], xyz[0], xyz[2]);
			break;
		    }
		default:
		    break;
		}

		Vect_cat_set(cs, FIELD_POINT, cat);

		Vect_write_line(Map, GV_POINT, ps, cs);

		p->cat = cat;
	    }

	    if (dotable) {
		/* insert record into table */
		insert_point(fi, driver, table, p, cat);
	    }
	    cat++;
	}
	lp = lp->next;
	Vect_reset_line(ps);
	Vect_reset_cats(cs);
    }

    if (dotable && driver) {
	db_commit_transaction(driver);
	db_close_database_shutdown_driver(driver);
    }


    Vect_destroy_line_struct(ps);
    Vect_destroy_cats_struct(cs);

    list_nodes_free(&network_param);

    return;
}

void list_points_free(struct list_points **lpoints)
{
    struct list_points *tmp, *next;

    tmp = *lpoints;

    while (tmp) {
	next = tmp->next;
	G_free((Point *) tmp->point);
	G_free((struct list_point *)tmp);
	tmp = next;
    }

    if (*lpoints)
	*lpoints = NULL;

    return;
}

int list_points_push_back(struct list_points **lpoints, Point * np)
{

    struct list_points *lp, *tmp;

    tmp = *lpoints;
    lp = (struct list_points *)G_malloc((unsigned int)
					sizeof(struct list_points));

    lp->point = np;
    lp->next = NULL;

    if (tmp) {
	while (tmp->next)
	    tmp = tmp->next;

	tmp->next = lp;
    }
    else {
	*lpoints = lp;
    }

    return 1;
}

Point *find_point(struct list_points * lp, dbString * id)
{
    struct list_points *tmp;

    for (tmp = lp; tmp; tmp = tmp->next) {
	if (!G_strcasecmp
	    (db_get_string(&(tmp->point->id)), db_get_string(id))) {
	    return tmp->point;
	}
    }

    return NULL;
}

void point_update(Point * point, int type,
		  xmlNode * x, xmlNode * y, xmlNode * z)
{
    int i;
    double val;

    xmlNode *xyz[] = { x, y, z };

    for (i = 0; i < DIM; i++) {	/* x | y | z */
	if (xyz[i]) {
	    if (node_get_value_double(xyz[i], &val)) {
		point->xyz[i].val[type] = val;
		point->xyz[i].is_null[type] = 0;
	    }
	}
    }

    return;
}

/*
   0 ... error
   1 ... coordinate
   2 ... is constrained ?
 */
int point_get_xyz(Point * point, char *name, double *val)
{

    int index_xyz, index_type;
    char *typesubstr;

    index_xyz = index_type = -1;

    /* name -> x_fix */
    typesubstr = &name[2];

    switch (name[0]) {
    case 'x':
	{
	    index_xyz = 0;
	    break;
	}
    case 'y':
	{
	    index_xyz = 1;
	    break;
	}
    case 'z':
	{
	    index_xyz = 2;
	    break;
	}
    default:
	{
	    G_fatal_error(_("Unable to determine coordinate x|y|z!"));
	    break;
	}
    }

    if (!G_strcasecmp(typesubstr, "fix")) {
	index_type = FIX;
    }
    else {
	if (!G_strcasecmp(typesubstr, "adj")) {
	    index_type = ADJ;
	}
	else {
	    if (!G_strcasecmp(typesubstr, "app")) {
		index_type = APP;
	    }
	    else {
		if (!G_strcasecmp(typesubstr, "con")) {
		    *val = point->xyz[index_xyz].is_constrained;
		    return 2;
		}
		else {
		    G_fatal_error(_("Unable to determine coordinate x|y|z!"));
		}
	    }
	}
    }

    if (index_type == -1 || index_xyz == -1 ||
	point->xyz[index_xyz].is_null[index_type]) {
	return 0;
    }

    *val = point->xyz[index_xyz].val[index_type];

    return 1;
}

int create_obs(struct Map_info *Map, xmlDoc * doc, int dotable,
	       struct list_points *vpoints)
{
    unsigned int i;
    int write;
    int cat, cat1, cat2, cat3;
    struct field_info *fi;
    const int field = 1;	/* layer 2 */

    dbDriver *driver;
    dbTable *table;
    dbString table_name, id1, id2, id3;

    xmlNode *root, *obss, *obs_id;
    struct list_nodes *obs, *tmp;

    struct line_pnts *ps;
    struct line_cats *cs;

    /* should be determined from DTD ... */
    const char *obs_tag[] = {
	"distance", "direction", "angle",
	"height-diff", "slope-distance", "zenith-angle",
	"dx", "dy", "dz",
	"coordinate-x", "coordinate-y", "coordinate-z"
    };

    cat = 1;
    db_init_string(&table_name);
    db_init_string(&id1);
    db_init_string(&id2);
    db_init_string(&id3);

    ps = Vect_new_line_struct();
    cs = Vect_new_cats_struct();

    list_init((void **)&obs);

    if (dotable) {
	fi = Vect_get_dblink(Map, field);

	if (!fi) {
	    G_fatal_error(_("Database connection not defined for layer %d"), field);
	}

	driver = db_start_driver_open_database(fi->driver, fi->database);

	if (!driver) {
	    G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
			  fi->database, fi->driver);
	}

	db_init_string(&table_name);
	db_set_string(&table_name, fi->table);

	if (db_describe_table(driver, &table_name, &table) != DB_OK) {
	    G_fatal_error(_("Unable to describe table <%s>"), fi->table);
	}

	db_begin_transaction(driver);
    }

    root = xmlDocGetRootElement(doc);

    if (!root) {
	G_fatal_error(_("Unable to get the root element"));
    }

    find_node(root, "observations", &obss);

    if (!obss) {
	G_warning(_("No observations found"));
    }
    else {
	for (i = 0; i < sizeof(obs_tag) / sizeof(char *); i++) {
	    if (find_nodes(obss, obs_tag[i], &obs)) {
		tmp = obs;
		while (tmp) {
		    write = 0;

		    if (dotable) {
			insert_obs(fi, driver, table, tmp->node, cat);
		    }

		    if (!G_strcasecmp(obs_tag[i], "coordinate-x") ||
			!G_strcasecmp(obs_tag[i], "coordinate-y") ||
			!G_strcasecmp(obs_tag[i], "coordinate-z")) {
			if (find_node(tmp->node, "id", &obs_id)) {
			    node_get_value_string(obs_id, NULL, &id1);
			}
			cat1 = point_exists(vpoints, &id1);
			cat2 = cat3 = -1;
			if (cat1 != -1) {
			    write = 1;
			}
		    }
		    else {
			if (!G_strcasecmp(obs_tag[i], "angle")) {
			    if (find_node(tmp->node, "from", &obs_id)) {
				node_get_value_string(obs_id, NULL, &id1);
			    }
			    if (find_node(tmp->node, "left", &obs_id)) {
				node_get_value_string(obs_id, NULL, &id2);
			    }
			    if (find_node(tmp->node, "right", &obs_id)) {
				node_get_value_string(obs_id, NULL, &id3);
			    }

			    cat1 = point_exists(vpoints, &id1);
			    cat2 = point_exists(vpoints, &id2);
			    cat3 = point_exists(vpoints, &id3);
			    if (cat1 != -1 && cat2 != -1 && cat3 != -1) {
				write = 1;
			    }
			}
			else {
			    if (find_node(tmp->node, "from", &obs_id)) {
				node_get_value_string(obs_id, NULL, &id1);
			    }
			    if (find_node(tmp->node, "to", &obs_id)) {
				node_get_value_string(obs_id, NULL, &id2);
			    }

			    cat1 = point_exists(vpoints, &id1);
			    cat2 = point_exists(vpoints, &id2);
			    cat3 = -1;
			    if (cat1 != -1 && cat2 != -1) {
				write = 1;
			    }
			}
		    }
		    if (write) {
			write_line(Map, cat1, cat2, cat3, cat++);
		    }
		    else {
			char buf[1024];
			dbString err;

			db_init_string(&err);

			sprintf(buf,
				"Line number %d: unable write vector line, "
				" missing point id ", tmp->node->line);
			db_set_string(&err, buf);

			if (db_sizeof_string(&id1) > 0) {
			    sprintf(buf, "[%s]", db_get_string(&id1));
			    db_append_string(&err, buf);
			}
			if (db_sizeof_string(&id2) > 0) {
			    sprintf(buf, " or [%s]", db_get_string(&id2));
			    db_append_string(&err, buf);
			}

			if (db_sizeof_string(&id3) > 0) {
			    sprintf(buf, " or [%s]", db_get_string(&id3));
			    db_append_string(&err, buf);
			}

			db_append_string(&err, ".");
			G_warning(_(db_get_string(&err)));

		    }
		    tmp = tmp->next;
		}
	    }
	}
    }

    if (dotable && driver) {
	db_commit_transaction(driver);
	db_close_database_shutdown_driver(driver);
    }

    list_nodes_free(&obs);

    Vect_destroy_line_struct(ps);
    Vect_destroy_cats_struct(cs);

    return 0;
}

int point_exists(struct list_points *vpoints, dbString * from_id)
{

    Point *fp;

    fp = find_point(vpoints, from_id);
    if (fp) {
	return fp->cat;
    }

    return -1;
}

int write_line(struct Map_info *Map, int cat_id1, int cat_id2, int cat_id3,
	       int cat)
{

    int line, nlines, i, j, k;
    int pcat, cat_line, fcat;
    int points[3];

    struct line_pnts *ps_line, *ps[3];
    struct line_cats *cs_line, *cs[3];

    int cats[] = { cat_id1, cat_id2, cat_id3 };
    const short dim = sizeof(cats) / sizeof(int);

    for (i = 0; i < dim; i++) {
	points[i] = 0;
	ps[i] = Vect_new_line_struct();
	cs[i] = Vect_new_cats_struct();
    }

    ps_line = Vect_new_line_struct();
    cs_line = Vect_new_cats_struct();

    Vect_build_partial(Map, GV_BUILD_BASE);

    nlines = Vect_get_num_lines(Map);

    for (line = 1; line <= nlines; line++) {
	if (!Vect_line_alive(Map, line) ||
	    Vect_read_line(Map, ps_line, cs_line, line) != GV_POINT)
	    continue;

	pcat = Vect_get_line_cat(Map, line, FIELD_POINT);

	for (i = 0; i < dim; i++) {
	    if (cats[i] != -1 && pcat == cats[i]) {
		points[i] = line;
	    }
	}
    }

    for (i = 0; i < dim; i++) {
	if (points[i] > 0) {
	    /* add category number to the point */
	    Vect_read_line(Map, ps[i], cs[i], points[i]);
	    Vect_cat_set(cs[i], FIELD_OBS, cat);
	    Vect_rewrite_line(Map, points[i], GV_POINT, ps[i], cs[i]);
	}
    }

    if (cats[0] != -1) {
	for (i = 1; cats[i] != -1 && i < dim; i++) {
	    cat_line = -1;
	    Vect_reset_line(ps_line);
	    Vect_reset_cats(cs_line);
	    for (j = 0; cat_line == -1 && j < cs[0]->n_cats; j++) {
		if (cs[0]->field[j] != FIELD_OBS)
		    continue;

		for (k = 0; cat_line == -1 && k < cs[i]->n_cats; k++) {
		    if (cs[i]->field[k] == FIELD_OBS &&
			cs[i]->cat[k] != cat &&
			cs[0]->cat[j] == cs[i]->cat[k]) {
			cat_line = cs[i]->cat[k];
		    }
		}
	    }

	    if (cat_line == -1) {
		/* write new line with category number 'cat' */
		Vect_cat_set(cs_line, FIELD_OBS, cat);
		Vect_append_points(ps_line, ps[0], GV_FORWARD);
		Vect_append_points(ps_line, ps[i], GV_FORWARD);
		Vect_write_line(Map, GV_LINE, ps_line, cs_line);
	    }
	    else {
		Vect_build_partial(Map, GV_BUILD_BASE);
		nlines = Vect_get_num_lines(Map);

		/* add category number to the existing vector line */
		for (line = 1; line <= nlines; line++) {
		    if (!Vect_line_alive(Map, line) ||
			Vect_read_line(Map, ps_line, cs_line,
				       line) != GV_LINE)
			continue;

		    Vect_cat_get(cs_line, FIELD_OBS, &fcat);
		    if (fcat == cat_line) {
			/* works only if fcat is the first category number in given field 
			   -> it should be (?)
			 */

			Vect_cat_set(cs_line, FIELD_OBS, cat);
			Vect_rewrite_line(Map, line, GV_LINE, ps_line,
					  cs_line);
			break;
		    }
		}
	    }
	}
    }

    Vect_destroy_line_struct(ps_line);
    Vect_destroy_cats_struct(cs_line);

    for (i = 0; i < dim; i++) {
	Vect_destroy_line_struct(ps[i]);
	Vect_destroy_cats_struct(cs[i]);
    }



    return 0;
}
