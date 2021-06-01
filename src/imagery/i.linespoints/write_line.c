#include "defs.h"
#define POINT_FILE "POINTS"

int read_control_points (
    FILE *fd,
    struct Control_Points *cp)
{
    char buf[100];
    double e1,e2,n1,n2;
    int status;

    cp->count = 0;

/* read the control point lines. format is:
   image_east image_north  target_east target_north  status
*/
    cp->e1 = NULL;
    cp->e2 = NULL;
    cp->n1 = NULL;
    cp->n2 = NULL;
    cp->status = NULL;

    while (G_getl (buf, sizeof buf, fd))
    {
	G_strip(buf);
	if (*buf == '#' || *buf == 0) continue;
	if (sscanf (buf, "%lf%lf%lf%lf%d", &e1, &n1, &e2, &n2, &status) == 5)
	    new_control_point (cp, e1, n1, e2, n2, status);
	else
	    return -4;
    }

    return 1;
}

int new_control_point (struct Control_Points *cp,
    double e1,double n1,double e2,double n2, int status)
{
    int i;
    unsigned int size;

    if (status ==-1) return 1;
    i = (cp->count)++ ;
    size =  cp->count * sizeof(double) ;
    cp->e1 = (double *) G_realloc (cp->e1, size);
    cp->e2 = (double *) G_realloc (cp->e2, size);
    cp->n1 = (double *) G_realloc (cp->n1, size);
    cp->n2 = (double *) G_realloc (cp->n2, size);
    size =  cp->count * sizeof(int) ;
    cp->status = (int *) G_realloc (cp->status, size);

    cp->e1[i] = e1;
    cp->e2[i] = e2;
    cp->n1[i] = n1;
    cp->n2[i] = n2;
    cp->status[i] = status;

    return 0;
}

int put_control_points (
    char *group,
    struct Control_Points *cp)
{
    FILE *fd;
    char msg[100];

    fd = I_fopen_group_file_new (group, POINT_FILE);
    if (fd == NULL)
    {
	sprintf (msg, "unable to create control point file for group [%s in %s]",
		group, G_mapset());
	G_warning (msg);
	return 0;
    }

    write_control_points (fd, cp);
    fclose (fd);
    return 1;
}



 int write_control_points(FILE *fd, struct Control_Points *cp)
{
    int i;

    fprintf (fd,"# %7s %15s %15s %15s %9s status\n","","image","","target","");
    fprintf (fd,"# %15s %15s %15s %15s   (1=ok)\n","east","north","east","north");
    fprintf (fd,"#\n");
    for (i = 0; i < cp->count; i++)
	if (cp->status[i] != -1)
	    fprintf (fd, "  %15f %15f %15f %15f %4d\n",
		cp->e1[i], cp->n1[i], cp->e2[i], cp->n2[i], cp->status[i]);

    return 0;
}

int get_control_points (
    char *group,
    struct Control_Points *cp)
{
    FILE *fd;
    char msg[100];
    int stat;

    fd = I_fopen_group_file_old (group, POINT_FILE);
    if (fd == NULL)
    {
	sprintf (msg, "unable to open control point file for group [%s in %s]",
		group, G_mapset());
	G_warning (msg);
	return 0;
    }

    stat = read_control_points (fd, cp);
    fclose (fd);
    if (stat < 0)
    {
	sprintf (msg, "bad format in control point file for group [%s in %s]",
		group, G_mapset());
	G_warning (msg);
	return 0;
    }
    return 1;
}