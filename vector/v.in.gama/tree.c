#include "global.h"

int find_node(xmlNode * root, const char *name, xmlNode ** fnode)
{
    int found = 0;
    struct list_nodes *fnodes;

    list_init((void **)&fnodes);

    found = find_nodes(root, name, &fnodes);

    if (fnodes) {
	*fnode = fnodes->node;
    }
    else {
	*fnode = NULL;
    }

    list_nodes_free(&fnodes);

    return found;
}

int find_nodes(xmlNode * root, const char *name, struct list_nodes **fnodes)
{
    int fcount, stop;
    xmlNode *last;

    fcount = stop = 0;

    if (root->next) {
	last = root->next;
    }
    else {			/* root element */

	last = root->last;
    }

    list_nodes_free(fnodes);

    find__nodes(root, last, name, fnodes, &fcount, &stop);

    return fcount;
}

void find__nodes(xmlNode * root, xmlNode * last, const char *name,
		 struct list_nodes **fnodes, int *fcount, int *stop)
{

    xmlNode *node = NULL;

    for (node = root; node && !(*stop); node = node->next) {
	if (node == last) {
	    *stop = 1;
	    break;
	}

	if (node->type == XML_ELEMENT_NODE &&
	    !G_strcasecmp((char *)node->name, name)) {
	    list_nodes_push_back(fnodes, node);
	    (*fcount)++;
	}

	find__nodes(node->children, last, name, fnodes, fcount, stop);
    }

    return;
}

void list_init(void **lnodes)
{
    *lnodes = NULL;

    return;
}

void list_nodes_free(struct list_nodes **lnodes)
{
    struct list_nodes *tmp, *next;

    tmp = *lnodes;

    while (tmp) {
	next = tmp->next;
	G_free((struct list_nodes *)tmp);
	tmp = next;
    }

    if (*lnodes)
	*lnodes = NULL;

    return;
}

void list_nodes_push_back(struct list_nodes **lnodes, xmlNode * node)
{

    struct list_nodes *ln, *tmp;

    tmp = *lnodes;
    ln = (struct list_nodes *)G_malloc((unsigned int)
				       sizeof(struct list_nodes));

    ln->node = node;
    ln->next = NULL;

    if (tmp) {
	while (tmp->next)
	    tmp = tmp->next;

	tmp->next = ln;
    }
    else {
	*lnodes = ln;
    }

    return;
}

int is_3d_map(xmlDoc * doc)
{

    int count;

    xmlNode *root;
    struct list_nodes *summary, *count_xyz, *count_z;

    list_init((void **)&summary);
    list_init((void **)&count_xyz);
    list_init((void **)&count_z);

    root = xmlDocGetRootElement(doc);
    if (!root) {
	G_fatal_error(_("Unable to get the root element"));
    }

    find_nodes(root, "coordinates-summary", &summary);

    if (summary) {
	struct list_nodes *tmp;

	find_nodes(summary->node, "count-xyz", &count_xyz);
	if (count_xyz) {
	    for (tmp = count_xyz; tmp; tmp = tmp->next) {
		if (node_get_value_int(tmp->node, &count))
		    if (count > 0)
			return WITH_Z;
	    }
	}
	find_nodes(summary->node, "count-z", &count_z);
	if (count_z) {
	    for (tmp = count_z; tmp; tmp = tmp->next) {
		if (node_get_value_int(tmp->node, &count))
		    if (count > 0)
			return WITH_Z;
	    }
	}
    }

    list_nodes_free(&summary);
    list_nodes_free(&count_xyz);
    list_nodes_free(&count_z);

    return WITHOUT_Z;
}

int node_get_value_int(xmlNode * node, int *value)
{

    xmlNode *node_value;

    if (node) {
	node_value = node->children;
	if (node_value && node_value->type == XML_TEXT_NODE) {
	    *value = (long)atoi((char *)node_value->content);
	    return 1;
	}
    }

    return 0;
}

int node_get_value_double(xmlNode * node, double *value)
{

    xmlNode *node_value;

    if (node) {
	node_value = node->children;
	if (node_value && node_value->type == XML_TEXT_NODE) {
	    *value = (double)atof((char *)node_value->content);
	    return 1;
	}
    }

    return 0;
}

int node_get_value_string(xmlNode * node, char *attr, dbString * value)
{
    if (node) {
	if (!attr) {
	    xmlNode *node_value;

	    node_value = node->children;
	    if (node_value && node_value->type == XML_TEXT_NODE) {
		db_set_string(value, (char *)node_value->content);
		return 1;
	    }
	}
	else {			/* attribute */

	    xmlAttr *attr_value;

	    attr_value = node->properties;
	    while (attr_value) {
		if (attr_value->type == XML_ATTRIBUTE_NODE &&
		    !G_strcasecmp((char *)attr_value->name, attr)) {
		    if (attr_value->children) {
			db_set_string(value,
				      (char *)attr_value->children->content);
			if (db_sizeof_string(value) > 0) {
			    return 1;
			}
		    }
		}
		attr_value = attr_value->next;
	    }
	}
    }

    return 0;
}

int axes_xy_str2type(char *attr)
{
    if (attr) {
	/* right-handed */
	if (!G_strcasecmp(attr, "ne"))
	    return 0;
	if (!G_strcasecmp(attr, "sw"))
	    return 1;
	if (!G_strcasecmp(attr, "es"))
	    return 2;
	if (!G_strcasecmp(attr, "wn"))
	    return 3;
	/* left-handed */
	if (!G_strcasecmp(attr, "en"))
	    return 4;
	if (!G_strcasecmp(attr, "ws"))
	    return 5;
	if (!G_strcasecmp(attr, "se"))
	    return 6;
	if (!G_strcasecmp(attr, "nw"))
	    return 7;
    }

    return -1;
}
